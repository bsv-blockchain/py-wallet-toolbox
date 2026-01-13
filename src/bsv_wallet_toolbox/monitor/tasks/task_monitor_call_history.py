"""TaskMonitorCallHistory implementation."""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..monitor import Monitor
from ..wallet_monitor_task import WalletMonitorTask


class TaskMonitorCallHistory(WalletMonitorTask):
    """Logs service call history.

    Reference: ts-wallet-toolbox/src/monitor/tasks/TaskMonitorCallHistory.ts
    """

    trigger_msecs: int

    def __init__(self, monitor: "Monitor", trigger_msecs: int = 12 * 60 * 1000) -> None:
        """Initialize TaskMonitorCallHistory."""
        super().__init__(monitor, "MonitorCallHistory")
        self.trigger_msecs = trigger_msecs

    def trigger(self, now: int) -> dict[str, bool]:
        """Run periodically."""
        should_run = now - self.last_run_msecs_since_epoch > self.trigger_msecs
        return {"run": should_run}

    def run_task(self) -> str:
        """Get and log service call history."""
        # Pass reset=True as in TS implementation (TaskMonitorCallHistory.ts calls getServicesCallHistory(true))
        history = self.monitor.services.get_services_call_history(reset=True)
        return json.dumps(history)
