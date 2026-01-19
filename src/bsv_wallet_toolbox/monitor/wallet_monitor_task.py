"""WalletMonitorTask base class."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .monitor import Monitor


class WalletMonitorTask(ABC):
    """Abstract base class for wallet monitor tasks.

    Reference: ts-wallet-toolbox/src/monitor/tasks/WalletMonitorTask.ts
    """

    monitor: "Monitor"
    name: str
    last_run_msecs_since_epoch: int

    def __init__(self, monitor: "Monitor", name: str) -> None:
        """Initialize the task with a monitor instance and name."""
        self.monitor = monitor
        self.name = name
        self.last_run_msecs_since_epoch = 0

    @abstractmethod
    def run_task(self) -> str:
        """Run the monitor task.

        Returns:
            str: A log message describing the result of the task execution.
        """

    def setup(self) -> None:
        """Perform synchronous setup for the task.

        Equivalent to asyncSetup() in TS, but synchronous for Python implementation.
        Override this method to perform initialization before task execution.
        """

    def trigger(self, now: int) -> dict[str, bool]:
        """Determine if the task should run based on current time.

        Args:
            now: Current timestamp in milliseconds.

        Returns:
            dict: {'run': bool} indicating if task should run.
        """
        return {"run": True}
