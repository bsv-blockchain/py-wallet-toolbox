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
        """Fail unprocessed/unsigned transactions not updated for abandoned_msecs, a page at a time (TS)."""
        log_lines: list[str] = []
        abandoned_time = datetime.now(UTC) - timedelta(milliseconds=self.abandoned_msecs)
        limit, offset = 100, 0
        while True:
            txs = self.monitor.storage.find_transactions(
                {"partial": {}, "status": ["unprocessed", "unsigned"], "paged": {"limit": limit, "offset": offset}}
            )
            retained = len(txs)
            for tx in txs:
                tx_id = tx.get("transactionId")
                if tx_id and self._is_abandoned(tx.get("updatedAt"), abandoned_time):
                    try:
                        self.monitor.storage.update_transaction_status("failed", tx_id)
                        log_lines.append(f"updated tx {tx_id} status to 'failed'")
                        retained -= 1
                    except Exception as e:
                        log_lines.append(f"failed to update tx {tx_id}: {e!s}")
            if len(txs) < limit:
                break
            offset += retained  # failed rows drop out of the status filter

        return "\n".join(log_lines)

    @staticmethod
    def _is_abandoned(updated_at: object, abandoned_time: datetime) -> bool:
        # updated_at might be datetime or string (depending on storage implementation)
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            except ValueError:
                return False
        if not isinstance(updated_at, datetime):
            return False
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=UTC)
        return updated_at < abandoned_time
