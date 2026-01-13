"""TaskClock implementation."""

import math
import time
from typing import TYPE_CHECKING

from ..wallet_monitor_task import WalletMonitorTask

if TYPE_CHECKING:
    from ..monitor import Monitor
else:
    # Import Monitor at runtime to avoid circular import
    Monitor = None  # Will be set when needed


class TaskClock(WalletMonitorTask):
    """Simple clock task to verify monitor is running and log heartbeats.

    Reference: ts-wallet-toolbox/src/monitor/tasks/TaskClock.ts
    """

    def __init__(self, monitor: "Monitor", trigger_msecs: int | None = None) -> None:
        """Initialize TaskClock.

        Args:
            monitor: Monitor instance
            trigger_msecs: Optional trigger interval in milliseconds (defaults to 1 second)
        """
        super().__init__(monitor, "Clock")
        # Import Monitor here to avoid circular import
        from ..monitor import Monitor as MonitorClass

        if trigger_msecs is None:
            trigger_msecs = 1 * MonitorClass.ONE_SECOND
        self.trigger_msecs = trigger_msecs
        self.next_minute = self.get_next_minute()

    def get_next_minute(self) -> int:
        """Calculate next minute timestamp.

        Returns:
            int: Next minute timestamp in milliseconds (rounded up)
        """
        # Import Monitor here to avoid circular import
        from ..monitor import Monitor as MonitorClass

        return math.ceil(time.time() * 1000 / MonitorClass.ONE_MINUTE) * MonitorClass.ONE_MINUTE

    def trigger(self, now: int) -> dict[str, bool]:
        """Trigger every minute.

        Args:
            now: Current timestamp in milliseconds.

        Returns:
            dict: {'run': bool}
        """
        # Run when current time exceeds next_minute
        return {"run": now > self.next_minute}

    def run_task(self) -> str:
        """Log current time and update next_minute.

        Returns:
            str: Log message with current time.
        """
        log = f"{time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(self.next_minute / 1000))}"
        self.next_minute = self.get_next_minute()
        return log
