"""TaskClock implementation."""

import time
from typing import TYPE_CHECKING, Any

from ..wallet_monitor_task import WalletMonitorTask

if TYPE_CHECKING:
    from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..monitor import Monitor


class TaskClock(WalletMonitorTask):
    """Simple clock task to verify monitor is running and log heartbeats.

    Reference: ts-wallet-toolbox/src/monitor/tasks/TaskClock.ts
    """

    def __init__(self, monitor: "Monitor") -> None:
        """Initialize TaskClock."""
        super().__init__(monitor, "Clock")

    def trigger(self, now: int) -> dict[str, bool]:
        """Trigger every minute.

        Args:
            now: Current timestamp in milliseconds.

        Returns:
            dict: {'run': bool}
        """
        # Run every 60 seconds
        if now - self.last_run_msecs_since_epoch > 60000:
            return {"run": True}
        return {"run": False}

    def run_task(self) -> str:
        """Log current time.

        Returns:
            str: Log message with current time.
        """
        return f"Tick: {time.ctime()}"

