"""TaskArcadeSSE implementation."""

import json
import threading
from typing import TYPE_CHECKING, Any

from ...services.providers.arcade_sse import ArcadeSSEClient
from ..wallet_monitor_task import WalletMonitorTask

if TYPE_CHECKING:
    from ..monitor import Monitor

# ProvenTxReq statuses that can never change again (TS: ProvenTxReqTerminalStatus).
PROVEN_TX_REQ_TERMINAL_STATUSES = frozenset({"completed", "invalid", "doubleSpend"})

# Arcade statuses confirming the broadcast reached the network.
_BROADCAST_CONFIRMED_STATUSES = frozenset(
    {"SENT_TO_NETWORK", "ACCEPTED_BY_NETWORK", "SEEN_ON_NETWORK", "SEEN_MULTIPLE_NODES"}
)


class TaskArcadeSSE(WalletMonitorTask):
    """Receives transaction status updates from Arcade via SSE and processes them.

    Requires ``arcadeUrl`` and ``arcadeCallbackToken`` in the Services options
    (the token must match the X-CallbackToken sent on broadcast). When either
    is missing the task stays idle.

    Status handling:

    - SENT_TO_NETWORK / ACCEPTED_BY_NETWORK / SEEN_ON_NETWORK /
      SEEN_MULTIPLE_NODES: broadcast confirmed — req => unmined,
      transactions => unproven.
    - MINED / IMMUTABLE: flags TaskCheckForProofs to run now, which fetches
      the proof via Services.get_merkle_path (Arcade is queried first when
      configured) and persists the ProvenTx. (TS fetches the proof inline;
      here the existing proof machinery is reused.)
    - DOUBLE_SPEND_ATTEMPTED: terminal in Arcade — req => doubleSpend,
      transactions => failed.
    - REJECTED: req => invalid, transactions => failed.

    Reference: ts-wallet-toolbox/src/monitor/tasks/TaskArcSSE.ts
    """

    def __init__(self, monitor: "Monitor") -> None:
        """Initialize TaskArcadeSSE."""
        super().__init__(monitor, "ArcadeSSE")
        self.sse_client: ArcadeSSEClient | None = None
        self._setup_attempted = False
        self._pending_events: list[dict[str, Any]] = []
        self._pending_lock = threading.Lock()

    def setup(self) -> None:
        """Create and connect the SSE client when Arcade is configured.

        Called lazily from the first trigger() evaluation because
        Monitor.run_once/start_tasks do not invoke setup().
        """
        if self._setup_attempted:
            return
        self._setup_attempted = True

        options = getattr(self.monitor.services, "options", None) or {}
        arcade_url = options.get("arcadeUrl")
        callback_token = options.get("arcadeCallbackToken")

        if not arcade_url:
            self.monitor.log_event(self.name, "no arcadeUrl configured; SSE disabled")
            return
        if not callback_token:
            self.monitor.log_event(self.name, "no arcadeCallbackToken configured; SSE disabled")
            return

        self.monitor.log_event(self.name, f"setting up SSE for arcadeUrl={arcade_url}")

        self.sse_client = ArcadeSSEClient(
            base_url=arcade_url,
            callback_token=callback_token,
            api_key=options.get("arcadeApiKey"),
            on_event=self._on_event,
            on_error=lambda e: self.monitor.log_event(self.name, f"SSE error: {e}"),
        )
        self.sse_client.connect()

    def _on_event(self, event: dict[str, Any]) -> None:
        """Queue an event from the SSE reader thread for run_task processing."""
        with self._pending_lock:
            self._pending_events.append(event)

    def trigger(self, now: int) -> dict[str, bool]:
        """Run whenever SSE events are pending (sets up the SSE client on first call)."""
        self.setup()
        with self._pending_lock:
            return {"run": bool(self._pending_events)}

    def run_task(self) -> str:
        """Process all pending SSE status events."""
        with self._pending_lock:
            events = self._pending_events[:]
            self._pending_events.clear()

        log_lines: list[str] = []
        for event in events:
            self._process_status_event(event, log_lines)
        return "\n".join(log_lines) if log_lines else ""

    def _process_status_event(self, event: dict[str, Any], log_lines: list[str]) -> None:
        txid = event.get("txid")
        tx_status = event.get("txStatus")
        if not txid or not tx_status:
            return
        log_lines.append(f"SSE: txid={txid} status={tx_status}")

        reqs = self.monitor.storage.find_proven_tx_reqs({"partial": {"txid": txid}})
        if not reqs:
            log_lines.append("  No matching ProvenTxReq")
            return

        for req in reqs:
            req_id = req.get("provenTxReqId")
            status = req.get("status")
            if req_id is None:
                continue
            if status in PROVEN_TX_REQ_TERMINAL_STATUSES:
                log_lines.append(f"  req {req_id} already terminal: {status}")
                continue
            self._apply_status_to_req(req, req_id, status, tx_status, log_lines)

    def _apply_status_to_req(
        self, req: dict[str, Any], req_id: Any, status: Any, tx_status: str, log_lines: list[str]
    ) -> None:
        if tx_status in _BROADCAST_CONFIRMED_STATUSES:
            if status in ("unsent", "sending", "callback"):
                self.monitor.storage.update_proven_tx_req(req_id, {"status": "unmined"})
                self._update_notify_transactions(req, "unproven")
                log_lines.append(f"  req {req_id} => unmined")
        elif tx_status in ("MINED", "IMMUTABLE"):
            self._request_proof_check()
            log_lines.append(f"  req {req_id} MINED/IMMUTABLE — proof check requested")
        elif tx_status == "DOUBLE_SPEND_ATTEMPTED":
            self.monitor.storage.update_proven_tx_req(req_id, {"status": "doubleSpend"})
            self._update_notify_transactions(req, "failed")
            log_lines.append(f"  req {req_id} => doubleSpend")
        elif tx_status == "REJECTED":
            self.monitor.storage.update_proven_tx_req(req_id, {"status": "invalid"})
            self._update_notify_transactions(req, "failed")
            log_lines.append(f"  req {req_id} => invalid")
        else:
            log_lines.append(f"  req {req_id} unhandled status: {tx_status}")

    def _update_notify_transactions(self, req: dict[str, Any], new_status: str) -> None:
        """Update the transactions recorded in the req's notify list."""
        notify = req.get("notify", {})
        if isinstance(notify, str):
            try:
                notify = json.loads(notify)
            except ValueError:
                return
        for tx_id in notify.get("transactionIds", []) if isinstance(notify, dict) else []:
            self.monitor.storage.update_transaction(tx_id, {"status": new_status})

    def _request_proof_check(self) -> None:
        """Flag TaskCheckForProofs to run on its next trigger evaluation."""
        for task in self.monitor._tasks:
            if task.name == "CheckForProofs" and hasattr(task, "check_now"):
                task.check_now = True
                return
