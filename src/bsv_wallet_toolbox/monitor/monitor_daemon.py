"""MonitorDaemon implementation."""

import logging
import threading
import time

from .monitor import Monitor

logger = logging.getLogger(__name__)


class MonitorDaemon:
    """Daemon manager for running Monitor in a background thread.

    Handles the lifecycle of the monitor thread, including starting,
    stopping, and exception handling during loop execution.
    """

    monitor: Monitor
    _thread: threading.Thread | None
    _running: bool

    def __init__(self, monitor: Monitor) -> None:
        """Initialize the daemon with a monitor instance."""
        self.monitor = monitor
        self._thread = None
        self._running = False

    def start(self) -> None:
        """Start the monitor loop in a background daemon thread.

        Raises:
            RuntimeError: If the daemon is already running.
        """
        if self._running:
            raise RuntimeError("Monitor daemon is already running")

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="WalletMonitorThread")
        self._thread.start()

    def stop(self) -> None:
        """Stop the monitor loop.

        Signals the thread to stop. The thread will exit after completing
        the current iteration or wait period.
        """
        self._running = False
        if self._thread:
            self._thread.join(timeout=self.monitor.options.task_run_wait_msecs / 1000.0 * 2)
            self._thread = None

    def _loop(self) -> None:
        """Internal run loop executed by the background thread."""
        while self._running:
            try:
                self.monitor.run_once()
            except Exception as e:
                logger.error("MonitorDaemon loop error: %s", e)
                # Prevent tight loop on persistent error
                time.sleep(1)

            # Wait for next cycle
            # Splitting sleep to allow faster shutdown response
            wait_msecs = self.monitor.options.task_run_wait_msecs
            step_msecs = 100
            waited = 0
            while self._running and waited < wait_msecs:
                time.sleep(step_msecs / 1000.0)
                waited += step_msecs
