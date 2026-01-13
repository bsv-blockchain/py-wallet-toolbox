"""TaskFailAbandoned implementation."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..monitor import Monitor
from ..wallet_monitor_task import WalletMonitorTask


class TaskFailAbandoned(WalletMonitorTask):
    """Handles transactions which have not been updated for an extended time period.

    Calls `updateTransactionStatus` to set `status` to `failed`.

    Reference: ts-wallet-toolbox/src/monitor/tasks/TaskFailAbandoned.ts
    """

    trigger_msecs: int
    abandoned_msecs: int

    def __init__(self, monitor: "Monitor", trigger_msecs: int = 5 * 60 * 1000) -> None:
        """Initialize TaskFailAbandoned."""
        super().__init__(monitor, "FailAbandoned")
        self.trigger_msecs = trigger_msecs
        # Default abandoned time: 5 minutes (MonitorOptions default in TS)
        self.abandoned_msecs = 5 * 60 * 1000

    def trigger(self, now: int) -> dict[str, bool]:
        """Run periodically."""
        should_run = now - self.last_run_msecs_since_epoch > self.trigger_msecs
        return {"run": should_run}

    def run_task(self) -> str:
        """Fail abandoned transactions."""
        log_lines: list[str] = []
        now = datetime.now(UTC)
        abandoned_time = now - timedelta(milliseconds=self.abandoned_msecs)

        # Find transactions with statuses that can be abandoned
        # TS uses: ['unprocessed', 'unsigned']
        # We need to check Python's transaction status flow.
        # Assuming similar statuses for now.
        txs = self.monitor.storage.find_transactions({"txStatus": ["unprocessed", "unsigned"]})

        if not txs:
            return ""

        count = 0
        for tx in txs:
            updated_at = tx.get("updatedAt")
            if not updated_at:
                continue

            # updated_at might be datetime or string (depending on storage implementation)
            if isinstance(updated_at, str):
                try:
                    # Handle potential Z suffix
                    updated_at_dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                except ValueError:
                    continue
            elif isinstance(updated_at, datetime):
                updated_at_dt = updated_at
            else:
                continue

            # Ensure timezone awareness for comparison
            if updated_at_dt.tzinfo is None:
                updated_at_dt = updated_at_dt.replace(tzinfo=UTC)

            if updated_at_dt < abandoned_time:
                tx_id = tx.get("transactionId")
                if tx_id:
                    try:
                        self.monitor.storage.update_transaction_status("failed", tx_id)
                        log_lines.append(f"updated tx {tx_id} status to 'failed'")
                        count += 1
                    except Exception as e:
                        log_lines.append(f"failed to update tx {tx_id}: {e!s}")

        if log_lines:
            return "\n".join(log_lines)
        return ""
