"""TaskArcadeSSE implementation."""

import threading
from typing import TYPE_CHECKING, Any

from ...services.providers.arcade import is_fee_policy_rejection
from ...services.providers.arcade_sse import ArcadeSSEClient
from ..wallet_monitor_task import WalletMonitorTask

if TYPE_CHECKING:
    from ..monitor import Monitor

# ProvenTxReq statuses that can never change again (TS: ProvenTxReqTerminalStatus).
PROVEN_TX_REQ_TERMINAL_STATUSES = frozenset({"completed", "invalid", "doubleSpend"})

# Attempts per SSE event before it is dropped (~5 minutes at the default 5 s monitor cycle).
MAX_EVENT_ATTEMPTS = 60

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
      here the existing proof machinery is reused, so TaskCheckForProofs and
      TaskNewHeader must be installed.)
    - DOUBLE_SPEND_ATTEMPTED: req => doubleSpend, transactions => failed
      (their allocated inputs are released). Current Arcade reports double
      spends as REJECTED; this branch is defensive.
    - REJECTED: req => invalid, transactions => failed. Not applied when the
      reason (GET /tx/{txid} extraInfo) is Arcade's own minimum-fee policy:
      Services.post_beef fell through to the other broadcasters on that
      rejection, so the broadcast result decides the outcome.

    Transactions are resolved by txid (every user's transaction row for it).
    They are updated before the req so a failure part-way leaves the req
    non-terminal; a failed event is retried on the next run (the SSE cursor
    has already moved past it) up to MAX_EVENT_ATTEMPTS.

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
        retry: list[dict[str, Any]] = []
        for event in events:
            try:
                self._process_status_event(event, log_lines)
            except Exception as e:
                attempts = event.get("_attempts", 0) + 1
                if attempts < MAX_EVENT_ATTEMPTS:
                    retry.append({**event, "_attempts": attempts})
                    log_lines.append(
                        f"SSE: failed to process {event.get('txid')} (attempt {attempts}), will retry: {e!s}"
                    )
                else:
                    log_lines.append(f"SSE: giving up on {event.get('txid')} after {attempts} attempts: {e!s}")
        if retry:
            with self._pending_lock:
                # Ahead of newer events, keeping arrival order.
                self._pending_events[:0] = retry
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
                self._update_transactions(req, "unproven")
                self.monitor.storage.update_proven_tx_req(req_id, {"status": "unmined"})
                log_lines.append(f"  req {req_id} => unmined")
        elif tx_status in ("MINED", "IMMUTABLE"):
            self._request_proof_check()
            log_lines.append(f"  req {req_id} MINED/IMMUTABLE — proof check requested")
        elif tx_status == "DOUBLE_SPEND_ATTEMPTED":
            self._update_transactions(req, "failed")
            self.monitor.storage.update_proven_tx_req(req_id, {"status": "doubleSpend"})
            log_lines.append(f"  req {req_id} => doubleSpend")
        elif tx_status == "REJECTED":
            if self._rejected_for_fee_policy(req.get("txid")):
                log_lines.append(f"  req {req_id} REJECTED by Arcade's fee policy; left to the other broadcasters")
                return
            self._update_transactions(req, "failed")
            self.monitor.storage.update_proven_tx_req(req_id, {"status": "invalid"})
            log_lines.append(f"  req {req_id} => invalid")
        else:
            log_lines.append(f"  req {req_id} unhandled status: {tx_status}")

    def _rejected_for_fee_policy(self, txid: Any) -> bool:
        """True when Arcade rejected the tx for its own minimum-fee policy.

        The SSE event carries no reason, so it is read from GET /tx/{txid}.
        Raises when the reason cannot be read so the event is retried.
        """
        arcade = getattr(self.monitor.services, "arcade", None)
        if arcade is None:
            return False
        data = arcade.get_tx_data(txid)
        if data is None:
            raise RuntimeError(f"could not read Arcade's rejection reason for {txid}")
        return is_fee_policy_rejection(data.extra_info)

    def _update_transactions(self, req: dict[str, Any], new_status: str) -> None:
        """Update the status of the transactions for the req's txid.

        Resolved by txid because ProvenTxReq.notify.transactionIds is not
        populated by this storage. update_transactions_status releases the
        inputs of transactions marked 'failed'.
        """
        txs = self.monitor.storage.find_transactions({"partial": {"txid": req.get("txid")}})
        ids = [t["transactionId"] for t in txs if t.get("transactionId") is not None]
        self.monitor.storage.update_transactions_status(ids, new_status)

    def _request_proof_check(self) -> None:
        """Flag TaskCheckForProofs to run on its next trigger evaluation."""
        for task in self.monitor._tasks:
            if task.name == "CheckForProofs" and hasattr(task, "check_now"):
                task.check_now = True
                return
