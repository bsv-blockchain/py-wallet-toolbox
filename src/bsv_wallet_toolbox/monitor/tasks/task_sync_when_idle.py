"""TaskSyncWhenIdle implementation (Placeholder)."""

from typing import TYPE_CHECKING

from ..wallet_monitor_task import WalletMonitorTask

if TYPE_CHECKING:
    from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..monitor import Monitor


class TaskSyncWhenIdle(WalletMonitorTask):
    """(Placeholder) Task to sync UTXOs when idle.

    NOTE: This task is defined in TypeScript wallet-toolbox but is NOT implemented there either.
    Reference: ts-wallet-toolbox/src/monitor/tasks/TaskSyncWhenIdle.ts
    The reference implementation contains an empty runTask method and trigger returns false.

    Desired Functionality (for future reference):
    To detect external deposits (e.g. from Faucet) automatically, this task would need to:
    1. Fetch current UTXOs from provider (e.g. WhatsOnChain).
    2. Compare with local UTXOs.
    3. Internalize any new transactions found using `wallet.internalize_action(txid)`.

    Since this is missing in the reference implementation (TS), it is omitted here to avoid
    Python-specific logic divergence.

    IMPLICATION:
    Users MUST manually internalize Faucet transactions using `wallet.internalize_action(txid)`
    until this feature is officially supported in the upstream design.
    """

    trigger_msecs: int

    def __init__(self, monitor: "Monitor", trigger_msecs: int = 60 * 1000) -> None:
        """Initialize TaskSyncWhenIdle."""
        super().__init__(monitor, "SyncWhenIdle")
        self.trigger_msecs = trigger_msecs

    def trigger(self, now: int) -> dict[str, bool]:
        """Determine if the task should run.

        Run periodically based on trigger_msecs interval.
        """
        if now - self.last_run_msecs_since_epoch > self.trigger_msecs:
            return {"run": True}
        return {"run": False}

    def run_task(self) -> str:
        """Run the monitor task."""
        return ""
