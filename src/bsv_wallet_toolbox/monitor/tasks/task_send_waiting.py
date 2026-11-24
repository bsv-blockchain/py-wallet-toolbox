"""TaskSendWaiting implementation."""

import time
from typing import TYPE_CHECKING

from ..wallet_monitor_task import WalletMonitorTask

if TYPE_CHECKING:
    from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..monitor import Monitor


class TaskSendWaiting(WalletMonitorTask):
    """Broadcasts transactions that are in 'signed' status.

    Reference: ts-wallet-toolbox/src/monitor/tasks/TaskSendWaiting.ts
    """

    check_period_msecs: int
    min_age_msecs: int

    def __init__(
        self,
        monitor: "Monitor",
        check_period_msecs: int = 8000,
        min_age_msecs: int = 7000,
    ) -> None:
        """Initialize TaskSendWaiting.

        Args:
            monitor: "Monitor" instance.
            check_period_msecs: Interval between checks (default 8s).
            min_age_msecs: Minimum age of transaction before broadcasting (default 7s).
                           Used to prevent race conditions with immediate broadcast.
        """
        super().__init__(monitor, "SendWaiting")
        self.check_period_msecs = check_period_msecs
        self.min_age_msecs = min_age_msecs

    def trigger(self, now: int) -> dict[str, bool]:
        """Run if enough time has passed since last run."""
        if now - self.last_run_msecs_since_epoch > self.check_period_msecs:
            return {"run": True}
        return {"run": False}

    def run_task(self) -> str:
        """Find and broadcast signed transactions.

        Returns:
            str: Log message summarizing actions.
        """
        # Find unsent ProvenTxReqs
        reqs = self.monitor.storage.find_proven_tx_reqs({"partial": {}, "status": ["unsent", "sending"]})
        if not reqs:
            return ""

        # Filter reqs by minimum age
        current_time = int(time.time() * 1000)
        filtered_reqs = []
        for req in reqs:
            updated_at = req.get("updatedAt")
            if updated_at is not None:
                # Convert updated_at to milliseconds since epoch
                if hasattr(updated_at, "timestamp"):  # datetime object
                    updated_at_ms = int(updated_at.timestamp() * 1000)
                elif isinstance(updated_at, str):
                    # Assume ISO format, convert to timestamp
                    continue  # Skip for now
                elif updated_at < 1e10:  # Likely in seconds
                    updated_at_ms = updated_at * 1000
                else:
                    updated_at_ms = updated_at

                if current_time - updated_at_ms >= self.min_age_msecs:
                    filtered_reqs.append(req)
            else:
                # If no updated_at, assume it's old enough to process
                filtered_reqs.append(req)

        if not filtered_reqs:
            return ""

        # Same send path as an immediate processAction: AtomicBEEF of each tx, statuses updated by storage.
        result = self.monitor.storage.attempt_to_post_reqs_to_network(filtered_reqs, self.monitor.services)
        log_messages: list[str] = []
        for d in result["details"]:
            txid = d["txid"]
            if d["status"] == "success":
                log_messages.append(f"Broadcasted {txid}: Success")
                self.monitor.call_on_broadcasted_transaction({"status": "success", "txid": txid})
            else:
                log_messages.append(f"Broadcast failed {txid}: {d['status']} {d.get('message')}")

        return "\n".join(log_messages)
