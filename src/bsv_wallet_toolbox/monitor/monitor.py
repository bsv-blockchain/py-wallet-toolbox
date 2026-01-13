"""Monitor implementation."""

import logging
import time
from collections.abc import Callable
from datetime import UTC
from typing import Any, ClassVar

from ..services.chaintracker.chaintracks.api import ChaintracksClientApi
from ..services.services import Services
from ..services.wallet_services import Chain
from ..storage.provider import StorageProvider
from .tasks import (
    TaskCheckForProofs,
    TaskCheckNoSends,
    TaskClock,
    TaskFailAbandoned,
    TaskMonitorCallHistory,
    TaskNewHeader,
    TaskPurge,
    TaskReorg,
    TaskReviewStatus,
    TaskSendWaiting,
    TaskSyncWhenIdle,
    TaskUnFail,
)
from .wallet_monitor_task import WalletMonitorTask

logger = logging.getLogger(__name__)


class MonitorOptions:
    """Configuration options for Monitor."""

    chain: Chain
    services: Services
    storage: StorageProvider
    chaintracks: ChaintracksClientApi | None
    task_run_wait_msecs: int
    msecs_wait_per_merkle_proof_service_req: int
    abandoned_msecs: int
    unproven_attempts_limit_test: int
    unproven_attempts_limit_main: int
    on_transaction_broadcasted: Callable[[dict[str, Any]], Any] | None
    on_transaction_proven: Callable[[dict[str, Any]], Any] | None

    def __init__(
        self,
        chain: Chain,
        storage: StorageProvider,
        services: Services | None = None,
        chaintracks: ChaintracksClientApi | None = None,
        task_run_wait_msecs: int = 5000,
        msecs_wait_per_merkle_proof_service_req: int = 500,
        abandoned_msecs: int = 1000 * 60 * 5,  # 5 minutes
        unproven_attempts_limit_test: int = 10,
        unproven_attempts_limit_main: int = 144,
        on_transaction_broadcasted: Callable[[dict[str, Any]], Any] | None = None,
        on_transaction_proven: Callable[[dict[str, Any]], Any] | None = None,
    ) -> None:
        """Initialize monitor options."""
        self.chain = chain
        self.storage = storage
        self.services = services or Services(chain)
        self.chaintracks = chaintracks
        self.task_run_wait_msecs = task_run_wait_msecs
        self.msecs_wait_per_merkle_proof_service_req = msecs_wait_per_merkle_proof_service_req
        self.abandoned_msecs = abandoned_msecs
        self.unproven_attempts_limit_test = unproven_attempts_limit_test
        self.unproven_attempts_limit_main = unproven_attempts_limit_main
        self.on_transaction_broadcasted = on_transaction_broadcasted
        self.on_transaction_proven = on_transaction_proven


class Monitor:
    """Synchronous Monitoring Service for Wallet Operations.

    Manages and runs background tasks for transaction monitoring, broadcasting,
    and proof verification.

    Reference: ts-wallet-toolbox/src/monitor/Monitor.ts
    """

    ONE_SECOND: ClassVar[int] = 1000
    ONE_MINUTE: ClassVar[int] = 60 * ONE_SECOND
    ONE_HOUR: ClassVar[int] = 60 * ONE_MINUTE
    ONE_DAY: ClassVar[int] = 24 * ONE_HOUR
    ONE_WEEK: ClassVar[int] = 7 * ONE_DAY

    options: MonitorOptions
    services: Services
    chain: Chain
    storage: StorageProvider
    _tasks: list[WalletMonitorTask]

    last_new_header: dict[str, Any] | None = None
    last_new_header_when: float | None = None
    deactivated_headers: list[dict[str, Any]] = []

    def __init__(self, options: MonitorOptions) -> None:
        """Initialize the Monitor with options."""
        self.options = options
        self.services = options.services
        self.chain = options.chain
        self.storage = options.storage
        self.chaintracks = options.chaintracks
        self._tasks = []
        self.deactivated_headers = []

    def add_task(self, task: WalletMonitorTask) -> None:
        """Add a task to the monitor.

        Args:
            task: The task instance to add.

        Raises:
            ValueError: If a task with the same name already exists.
        """
        if any(t.name == task.name for t in self._tasks):
            raise ValueError(f"Task {task.name} has already been added.")
        self._tasks.append(task)

    def add_default_tasks(self) -> None:
        """Add the standard set of monitoring tasks.

        Mirrors Monitor.addDefaultTasks() from TypeScript.
        """
        self.add_task(TaskClock(self))
        self.add_task(TaskCheckForProofs(self))
        self.add_task(TaskSendWaiting(self))
        self.add_task(TaskCheckNoSends(self))
        self.add_task(TaskFailAbandoned(self))
        self.add_task(TaskReviewStatus(self))
        self.add_task(TaskUnFail(self))
        self.add_task(TaskMonitorCallHistory(self))
        self.add_task(TaskSyncWhenIdle(self))
        self.add_task(TaskReorg(self))

        # TaskPurge requires parameters
        purge_params = {
            "purgeSpent": False,
            "purgeCompleted": False,
            "purgeFailed": True,
            "purgeSpentAge": 2 * self.ONE_WEEK,
            "purgeCompletedAge": 2 * self.ONE_WEEK,
            "purgeFailedAge": 5 * self.ONE_DAY,
        }
        self.add_task(TaskPurge(self, purge_params))
        self.add_task(TaskNewHeader(self))

    def run_task(self, name: str) -> str:
        """Run a specific task by name.

        Args:
            name: The name of the task to run.

        Returns:
            str: Log output from the task, or empty string if not found.
        """
        task = next((t for t in self._tasks if t.name == name), None)
        if task:
            task.setup()
            return task.run_task()
        return ""

    def run_once(self) -> None:
        """Run one cycle of all eligible tasks.

        Iterates through all registered tasks, checks their trigger conditions,
        and executes them sequentially if eligible.
        """
        now = int(time.time() * 1000)
        tasks_to_run: list[WalletMonitorTask] = []

        # Check triggers
        for t in self._tasks:
            try:
                trigger_result = t.trigger(now)
                if trigger_result.get("run"):
                    tasks_to_run.append(t)
            except Exception as e:
                logger.error("Monitor task %s trigger error: %s", t.name, e)
                self.log_event("error0", f"Monitor task {t.name} trigger error: {e!s}")

        # Run eligible tasks
        for ttr in tasks_to_run:
            try:
                log = ttr.run_task()
                if log:
                    logger.info("Task %s: %s", ttr.name, log[:256])
                    self.log_event(ttr.name, log)
            except Exception as e:
                logger.error("Monitor task %s runTask error: %s", ttr.name, e)
                self.log_event("error1", f"Monitor task {ttr.name} runTask error: {e!s}")
            finally:
                ttr.last_run_msecs_since_epoch = int(time.time() * 1000)

    _tasks_running: bool = False

    async def start_tasks(self) -> None:
        """Start running monitor tasks asynchronously.

        Runs tasks in a loop, checking triggers and executing eligible tasks,
        waiting between cycles according to task_run_wait_msecs.

        Reference: ts-wallet-toolbox/src/monitor/Monitor.ts (startTasks)
        """
        if self._tasks_running:
            raise ValueError("monitor tasks are already running")

        self._tasks_running = True
        import asyncio

        while self._tasks_running:
            self.run_once()
            # Wait before next cycle
            await asyncio.sleep(self.options.task_run_wait_msecs / 1000.0)

    def stop_tasks(self) -> None:
        """Stop running monitor tasks.

        Sets the running flag to False, which will cause start_tasks loop to exit.
        """
        self._tasks_running = False

    def log_event(self, event: str, details: str | None = None) -> None:
        """Log a monitor event to storage.

        Args:
            event: Event name/type.
            details: Optional details string.
        """
        if hasattr(self.storage, "insert_monitor_event"):
            from datetime import datetime

            now = datetime.now(UTC)
            try:
                self.storage.insert_monitor_event(
                    {
                        "event": event,
                        "details": details or "",
                        "createdAt": now,
                        "updatedAt": now,
                    }
                )
            except Exception as e:
                logger.error("Failed to log monitor event '%s': %s", event, e)
        else:
            # Fallback logging if storage doesn't support it (or during early initialization)
            logger.info("[Monitor Event] %s: %s", event, details)

    def process_new_block_header(self, header: dict[str, Any]) -> None:
        """Process new chain header event received from Chaintracks.

        Kicks processing 'unconfirmed' and 'unmined' request processing.

        Args:
            header: Block header data.
        """
        self.last_new_header = header
        self.last_new_header_when = time.time()
        # Nudge the proof checker to try again.
        for t in self._tasks:
            if hasattr(t, "check_now"):
                t.check_now = True

    def process_reorg(
        self,
        depth: int,
        old_tip: dict[str, Any],
        new_tip: dict[str, Any],
        deactivated_headers: list[dict[str, Any]] | None = None,
    ) -> None:
        """Process reorg event received from Chaintracks.

        Args:
            depth: Reorg depth.
            old_tip: Old chain tip header.
            new_tip: New chain tip header.
            deactivated_headers: List of headers that were deactivated.
        """
        if deactivated_headers:
            now = int(time.time() * 1000)
            for header in deactivated_headers:
                self.deactivated_headers.append(
                    {
                        "whenMsecs": now,
                        "tries": 0,
                        "header": header,
                    }
                )

    def call_on_broadcasted_transaction(self, broadcast_result: dict[str, Any]) -> None:
        """Hook for when a transaction is broadcasted.

        Args:
            broadcast_result: Result of the broadcast.
        """
        callback = self.on_transaction_broadcasted or self.options.on_transaction_broadcasted
        if callback:
            try:
                import inspect

                if inspect.iscoroutinefunction(callback):
                    # If callback is async, create a task to run it
                    import asyncio

                    asyncio.create_task(callback(broadcast_result))
                else:
                    callback(broadcast_result)
            except Exception as e:
                logger.error("Error in on_transaction_broadcasted hook: %s", e)

    def call_on_proven_transaction(self, tx_status: dict[str, Any]) -> None:
        """Hook for when a transaction is proven.

        Args:
            tx_status: Transaction status update.
        """
        callback = self.on_transaction_proven or self.options.on_transaction_proven
        if callback:
            try:
                import asyncio
                import inspect

                if inspect.iscoroutinefunction(callback):
                    # If callback is async, create a task to run it
                    asyncio.create_task(callback(tx_status))
                else:
                    callback(tx_status)
            except Exception as e:
                logger.error("Error in on_transaction_proven hook: %s", e)
