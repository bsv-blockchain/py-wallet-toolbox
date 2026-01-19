"""Background transaction broadcaster.

Provides asynchronous background broadcasting of transactions with retry logic
and proper resource cleanup.

Reference: go-wallet-toolbox/pkg/storage/internal/service/background_broadcaster.go
"""

import asyncio
import logging
from asyncio import Queue
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class BroadcasterProtocol(Protocol):
    """Protocol for transaction broadcasters."""

    async def background_broadcast(self, beef: bytes, txids: list[str]) -> dict[str, Any]:
        """Broadcast BEEF transaction in background.

        Args:
            beef: BEEF data to broadcast
            txids: Transaction IDs being broadcast

        Returns:
            Dict with broadcast results
        """
        ...


class BackgroundBroadcaster:
    """Asynchronous background transaction broadcaster.

    Manages a queue of broadcast requests and processes them asynchronously
    with proper error handling and cleanup.

    Reference: go-wallet-toolbox/pkg/storage/internal/service/background_broadcaster.go
    """

    def __init__(self, broadcaster: BroadcasterProtocol, max_queue_size: int = 100):
        """Initialize background broadcaster.

        Args:
            broadcaster: Object implementing the broadcast protocol
            max_queue_size: Maximum queue size before blocking
        """
        self.broadcaster = broadcaster
        self.queue: Queue[dict[str, Any]] = Queue(maxsize=max_queue_size)
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._shutdown_event = asyncio.Event()

    def start(self) -> None:
        """Start the background broadcaster task."""
        if self._running:
            logger.warning("Background broadcaster already running")
            return

        self._running = True
        self._shutdown_event.clear()
        self._task = asyncio.create_task(self._process_queue())
        logger.info("Background broadcaster started")

    async def stop(self) -> None:
        """Stop the background broadcaster and cleanup resources."""
        if not self._running:
            return

        logger.info("Stopping background broadcaster...")
        self._running = False
        self._shutdown_event.set()

        # Wait for current broadcast to complete
        if self._task and not self._task.done():
            try:
                await asyncio.wait_for(self._task, timeout=30.0)
            except TimeoutError:
                logger.warning("Background broadcaster task did not complete within timeout")
                self._task.cancel()

        logger.info("Background broadcaster stopped")

    async def enqueue(self, beef: bytes, txids: list[str]) -> None:
        """Enqueue a broadcast request.

        Args:
            beef: BEEF data to broadcast
            txids: Transaction IDs being broadcast

        Raises:
            RuntimeError: If broadcaster is not running
        """
        if not self._running:
            raise RuntimeError("Background broadcaster is not running")

        try:
            await self.queue.put({"beef": beef, "txids": txids, "timestamp": asyncio.get_event_loop().time()})
        except asyncio.QueueFull:
            logger.error("Broadcast queue is full, dropping request for txids: %s", txids)

    async def _process_queue(self) -> None:
        """Process broadcast requests from the queue."""
        while self._running or not self.queue.empty():
            try:
                # Wait for either a shutdown signal or a queue item
                shutdown_task = asyncio.create_task(self._shutdown_event.wait())
                queue_task = asyncio.create_task(self.queue.get())

                done, pending = await asyncio.wait([shutdown_task, queue_task], return_when=asyncio.FIRST_COMPLETED)

                # Cancel pending tasks
                for task in pending:
                    task.cancel()

                if shutdown_task in done and self._shutdown_event.is_set():
                    # Shutdown requested
                    break

                if queue_task in done:
                    # Process the broadcast request
                    request = queue_task.result()
                    await self._handle_broadcast(request)

            except Exception as e:
                logger.error("Error processing broadcast queue: %s", e)
                await asyncio.sleep(1)  # Brief pause before retrying

    async def _handle_broadcast(self, request: dict[str, Any]) -> None:
        """Handle a single broadcast request.

        Args:
            request: Broadcast request with beef and txids
        """
        beef = request["beef"]
        txids = request["txids"]

        try:
            logger.debug("Broadcasting transactions: %s", txids)
            result = await self.broadcaster.background_broadcast(beef, txids)

            if result.get("success"):
                logger.info("Successfully broadcast transactions: %s", txids)
            else:
                logger.error("Failed to broadcast transactions %s: %s", txids, result.get("error", "Unknown error"))

        except Exception as e:
            logger.error("Exception during broadcast of %s: %s", txids, e)

    def is_running(self) -> bool:
        """Check if the broadcaster is currently running."""
        return self._running

    def queue_size(self) -> int:
        """Get current queue size."""
        return self.queue.qsize()
