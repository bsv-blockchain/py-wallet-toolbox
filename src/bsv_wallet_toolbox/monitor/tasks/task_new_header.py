"""TaskNewHeader implementation."""

from typing import TYPE_CHECKING, Any

from ..wallet_monitor_task import WalletMonitorTask
from .task_check_for_proofs import TaskCheckForProofs

if TYPE_CHECKING:
    from ..monitor import Monitor


class TaskNewHeader(WalletMonitorTask):
    """Process new header events.

    Reference: ts-wallet-toolbox/src/monitor/tasks/TaskNewHeader.ts
    """

    check_now: bool = False
    header: dict[str, Any] | None = None

    def __init__(self, monitor: "Monitor") -> None:
        """Initialize TaskNewHeader."""
        super().__init__(monitor, "NewHeader")
        self.header = None

    def trigger(self, now: int) -> dict[str, bool]:
        """Run when triggered by event."""
        return {"run": self.check_now}

    def run_task(self) -> str:
        """Process new header."""
        self.check_now = False
        log = ""

        if self.monitor.last_new_header:
            self.header = self.monitor.last_new_header
            h = self.header
            log += f"Processing new header {h.get('height')} {h.get('hash')}\n"

            # Trigger proof checks
            # In Python implementation, we might need a way to signal TaskCheckForProofs
            # directly or rely on its next scheduled run.
            # TS sets TaskCheckForProofs.checkNow = true.
            # Here we can find the task instance and set a flag.

            for task in self.monitor._tasks:
                if isinstance(task, TaskCheckForProofs):
                    task.check_now = True
                    log += "Triggered TaskCheckForProofs\n"

        return log
