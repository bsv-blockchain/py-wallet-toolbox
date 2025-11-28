"""TaskSendWaiting implementation."""

from typing import TYPE_CHECKING, Any

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
        # 1. Find 'signed' transactions
        # Note: min_age filtering would ideally happen in DB query,
        # but we'll filter in memory for now if query doesn't support complex where.
        txs = self.monitor.storage.find_transactions({"tx_status": "signed"})
        if not txs:
            return ""

        log_messages: list[str] = []
        # TODO: Implement min_age filtering logic using created_at

        for tx in txs:
            txid = tx.get("txid")
            tx_id = tx.get("transaction_id")

            if not txid or not tx_id:
                continue

            # 2. Get BEEF (BUMP Extended Format)
            # In TS implementation, we get the full BEEF to broadcast.
            beef_bytes = self.monitor.storage.get_beef_for_transaction(txid)
            if not beef_bytes:
                log_messages.append(f"Skipped {txid}: No BEEF data found")
                continue

            # 3. Broadcast via Services
            # post_beef accepts hex string
            beef_hex = beef_bytes.hex()
            result = self.monitor.services.post_beef(beef_hex)

            if result.get("accepted"):
                # 4. Update status on success
                self.monitor.storage.update_transaction(tx_id, {"tx_status": "broadcasted"})
                log_messages.append(f"Broadcasted {txid}: Success")

                # Trigger hook if available (TS parity)
                self.monitor.call_on_broadcasted_transaction(result)
            else:
                # Log failure but keep as 'signed' to retry later
                # TODO: Implement retry count and eventual failure
                msg = result.get("message", "unknown error")
                log_messages.append(f"Broadcast failed {txid}: {msg}")

        return "\n".join(log_messages) if log_messages else ""

