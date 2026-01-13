"""TaskPurge implementation."""

from typing import TYPE_CHECKING, Any

from ..wallet_monitor_task import WalletMonitorTask

if TYPE_CHECKING:
    from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..monitor import Monitor


class TaskPurge(WalletMonitorTask):
    """Purge transient data from storage.

    Reference: ts-wallet-toolbox/src/monitor/tasks/TaskPurge.ts
    """

    params: dict[str, Any]
    trigger_msecs: int
    check_now: bool = False

    def __init__(
        self,
        monitor: "Monitor",
        params: dict[str, Any],
        trigger_msecs: int = 0,
    ) -> None:
        """Initialize TaskPurge.

        Args:
            monitor: "Monitor" instance.
            params: Purge parameters (purgeSpent, purgeFailed, ages...).
            trigger_msecs: Trigger interval.
        """
        super().__init__(monitor, "Purge")
        self.params = params
        self.trigger_msecs = trigger_msecs

    def trigger(self, now: int) -> dict[str, bool]:
        """Run periodically or on demand."""
        should_run = self.check_now or (
            self.trigger_msecs > 0 and now - self.last_run_msecs_since_epoch > self.trigger_msecs
        )
        return {"run": should_run}

    def run_task(self) -> str:
        """Run purge."""
        self.check_now = False
        log = ""

        try:
            res = self.monitor.storage.purge_data(self.params)
            if res.get("count", 0) > 0:
                log = f"{res.get('count')} records updated or deleted.\n{res.get('log', '')}"
        except Exception as e:
            log = f"Error running purge_data: {e!s}"

        return log
