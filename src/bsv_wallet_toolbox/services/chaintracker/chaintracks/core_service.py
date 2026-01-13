"""Core Chaintracks service implementation.

Provides the main service that orchestrates live ingestors, bulk managers,
header processing, and reorg detection.

Reference: go-wallet-toolbox/pkg/services/chaintracks/chaintracks_service.go
"""

import asyncio
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ...wallet_services import Chain
from ..chaintracks_storage import ChaintracksStorageMemory
from .bulk_ingestor_factory import create_bulk_ingestors
from .bulk_manager import BulkManager
from .chain_work import ChainWork
from .live_ingestor_factory import create_live_ingestors
from .live_ingestor_interface import NamedLiveIngestor
from .models import BlockHeader, HeightRanges, InfoResponse, LiveBlockHeader

logger = logging.getLogger(__name__)


@dataclass
class ChaintracksServiceConfig:
    """Configuration for Chaintracks core service."""

    chain: Chain
    live_ingestors: list[str] = None  # List of ingestor types
    bulk_ingestors: list[dict[str, Any]] = None  # List of ingestor configs
    add_live_recursion_limit: int = 10
    live_height_threshold: int = 2000

    def __post_init__(self):
        if self.live_ingestors is None:
            self.live_ingestors = ["woc_poll"]
        if self.bulk_ingestors is None:
            self.bulk_ingestors = [
                {"type": "chaintracks_cdn", "cdnConfig": {"sourceUrl": "https://cdn.projectbabbage.com/blockheaders"}},
                {"type": "whats_on_chain_cdn"},
            ]


class PubSubEvents:
    """Simple pub/sub event system for headers and reorgs."""

    def __init__(self):
        self._subscribers: list[Callable] = []
        self._lock = threading.Lock()

    def subscribe(self) -> tuple[Callable[[Any], None], Callable[[], None]]:
        """Subscribe to events.

        Returns:
            Tuple of (send_function, unsubscribe_function)
        """

        def send_callback(data: Any) -> None:
            callback(data)

        def unsubscribe() -> None:
            with self._lock:
                if callback in self._subscribers:
                    self._subscribers.remove(callback)

        callback = None

        def create_callback() -> Callable:
            def cb(data: Any) -> None:
                with self._lock:
                    for subscriber in self._subscribers[:]:
                        try:
                            subscriber(data)
                        except Exception as e:
                            logger.error(f"Error in event subscriber: {e}")

            return cb

        callback = create_callback()

        with self._lock:
            self._subscribers.append(callback)

        return send_callback, unsubscribe

    def publish(self, data: Any) -> None:
        """Publish event to all subscribers."""
        with self._lock:
            for subscriber in self._subscribers[:]:
                try:
                    subscriber(data)
                except Exception as e:
                    logger.error(f"Error publishing event: {e}")


class CacheableWithTTL:
    """Simple TTL cache for expensive operations."""

    def __init__(self, ttl_seconds: float, fetch_func: Callable[[], Any]):
        self.ttl_seconds = ttl_seconds
        self.fetch_func = fetch_func
        self._cached_value: Any | None = None
        self._cache_time: float = 0
        self._lock = threading.Lock()

    def get(self) -> Any:
        """Get cached value or fetch new one if expired."""
        now = time.time()

        with self._lock:
            if self._cached_value is None or (now - self._cache_time) > self.ttl_seconds:
                self._cached_value = self.fetch_func()
                self._cache_time = now

            return self._cached_value

    def invalidate(self) -> None:
        """Invalidate the cache."""
        with self._lock:
            self._cached_value = None
            self._cache_time = 0


class ChaintracksCoreService:
    """Core Chaintracks service managing ingestors and header processing.

    This is the main service that coordinates live ingestors, bulk managers,
    storage, and provides the Chaintracks API functionality.

    Reference: go-wallet-toolbox/pkg/services/chaintracks/chaintracks_service.go
    """

    def __init__(self, config: ChaintracksServiceConfig):
        """Initialize Chaintracks core service.

        Args:
            config: Service configuration
        """
        self.config = config
        self.chain = config.chain

        # Storage
        storage_opts = ChaintracksStorageMemory.create_memory_storage_options(self.chain)
        self.storage = ChaintracksStorageMemory(storage_opts)

        # Live ingestors
        self.live_ingestors: list[NamedLiveIngestor] = []

        # Bulk manager
        bulk_ingestors = create_bulk_ingestors(self.chain)
        self.bulk_mgr = BulkManager(self.chain, bulk_ingestors)

        # Channels and event handling
        self.live_headers_chan: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._header_callbacks = PubSubEvents()
        self._reorg_callbacks = PubSubEvents()

        # State
        self._available = False
        self._available_lock = threading.Lock()

        # Cached present height
        self.cached_present_height = CacheableWithTTL(60.0, self._fetch_latest_present_height)

        # Background tasks
        self._background_tasks: list[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()

        # Sync state
        self.last_sync_check = time.time()
        self.last_bulk_sync = time.time()

        logger.info(f"ChaintracksCoreService initialized for {self.chain} chain")

    async def make_available(self) -> None:
        """Initialize and make the service available.

        Sets up storage, starts ingestors, and begins background processing.
        """
        with self._available_lock:
            if self._available:
                return

            logger.info("Chaintracks service - making available")

            # Initialize storage
            self.storage.make_available()

            # Create and start live ingestors
            self.live_ingestors = create_live_ingestors(self.chain)

            # Create bulk ingestors
            create_bulk_ingestors(self.chain)

            # TODO: Initialize bulk manager
            # self.bulk_mgr = ...

            # Start live ingestors
            for ingestor in self.live_ingestors:
                logger.info(f"Chaintracks service - starting live ingestor {ingestor.name}")

                def create_callback(ingestor_name: str):
                    def callback(headers: list[dict[str, Any]]) -> None:
                        # Forward headers to processing channel
                        for header in headers:
                            try:
                                # Use asyncio.create_task if loop is running, otherwise just put directly
                                if asyncio.get_running_loop():
                                    asyncio.create_task(self.live_headers_chan.put(header))
                                else:
                                    # This shouldn't happen in normal operation
                                    logger.warning(f"No event loop running for {ingestor_name} callback")
                            except RuntimeError:
                                # No event loop running
                                logger.warning(f"No event loop running for {ingestor_name} callback")
                            except Exception as e:
                                logger.error(f"Failed to queue header from {ingestor_name}: {e}")

                    return callback

                try:
                    ingestor.ingestor.start_listening(create_callback(ingestor.name))
                except RuntimeError as e:
                    if "no running event loop" in str(e):
                        logger.warning(f"Cannot start {ingestor.name} ingestor - no event loop running")
                    else:
                        raise

            # Start background processing
            self._background_tasks.append(asyncio.create_task(self._shift_live_headers_worker()))

            self._available = True
            logger.info("Chaintracks service - now available")

    def destroy(self) -> None:
        """Shutdown the service and clean up resources."""
        logger.info("Chaintracks service - destroying")

        with self._available_lock:
            if not self._available:
                return

            # Stop shutdown event
            self._shutdown_event.set()

            # Stop live ingestors
            for ingestor in self.live_ingestors:
                logger.info(f"Chaintracks service - stopping live ingestor {ingestor.name}")
                ingestor.ingestor.stop_listening()

            # Cancel background tasks
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()

            # Wait for tasks to complete with timeout (in a fire-and-forget manner)
            # Since destroy() is synchronous, we can't await here
            # The tasks will be cancelled and should complete on their own

            self._available = False
            logger.info("Chaintracks service - destroyed")

    def is_available(self) -> bool:
        """Check if service is available."""
        with self._available_lock:
            return self._available

    def get_chain(self) -> Chain:
        """Get the blockchain network."""
        return self.chain

    async def get_present_height(self) -> int:
        """Get current blockchain height."""
        return self.cached_present_height.get()

    async def get_available_height_ranges(self) -> HeightRanges:
        """Get available height ranges from storage."""
        # TODO: Implement bulk manager height ranges
        live_range = await self._get_live_height_range()
        bulk_range = await self._get_bulk_height_range()

        return HeightRanges(bulk=bulk_range, live=live_range)

    async def get_info(self) -> InfoResponse:
        """Get service information."""
        height_ranges = await self.get_available_height_ranges()

        return InfoResponse(
            chain=self.chain,
            height_bulk=height_ranges.bulk.max_height if height_ranges.bulk else 0,
            height_live=height_ranges.live.max_height if height_ranges.live else 0,
            storage="memory",
            bulk_ingestors=[],  # TODO: Get from bulk manager
            live_ingestors=[ingestor.name for ingestor in self.live_ingestors],
        )

    async def find_chain_tip_header(self) -> BlockHeader | None:
        """Find the current chain tip header."""
        queries = self.storage.query()
        header, err = queries.get_active_tip_live_header()

        if err or header is None:
            return None

        return header.chain_block_header

    async def find_chain_tip_hash(self) -> str | None:
        """Find the current chain tip hash."""
        tip_header = await self.find_chain_tip_header()
        return tip_header.get("hash") if tip_header else None

    async def find_header_for_height(self, height: int) -> BlockHeader | None:
        """Find block header for specific height."""
        queries = self.storage.query()
        header, err = queries.get_live_header_by_height(height)

        if err or header is None:
            return None

        return header.chain_block_header

    def subscribe_headers(self) -> tuple[Callable[[dict[str, Any]], None], Callable[[], None]]:
        """Subscribe to new header events."""
        return self._header_callbacks.subscribe()

    def subscribe_reorgs(self) -> tuple[Callable[[dict[str, Any]], None], Callable[[], None]]:
        """Subscribe to reorg events."""
        return self._reorg_callbacks.subscribe()

    async def _shift_live_headers_worker(self) -> None:
        """Background worker for processing live headers."""
        while not self._shutdown_event.is_set():
            try:
                await self._shift_live_headers()
                await asyncio.sleep(1.0)  # Check interval
            except asyncio.CancelledError:
                logger.info("Background worker cancelled")
                break
            except Exception as e:
                logger.error(f"Error in shift live headers worker: {e}")
                await asyncio.sleep(5.0)  # Back off on error

    async def _shift_live_headers(self) -> None:
        """Process incoming live headers and manage synchronization."""
        try:
            # Get present height
            await self.get_present_height()

            # Get available ranges
            await self.get_available_height_ranges()

            # Process queued headers
            headers_processed = 0
            while not self.live_headers_chan.empty() and headers_processed < 100:
                try:
                    header = self.live_headers_chan.get_nowait()
                    await self._add_live_header(header)
                    headers_processed += 1
                except asyncio.QueueEmpty:
                    break

            # TODO: Bulk sync logic
            # TODO: Migrate live to bulk headers

        except Exception as e:
            logger.error(f"Error shifting live headers: {e}")

    async def _add_live_header(self, header: dict[str, Any]) -> None:
        """Add a live header to storage with chain work calculation."""
        try:
            # Calculate chain work
            bits = header.get("bits", 0)
            chain_work = ChainWork.from_bits(bits)

            # Get previous header for chain work accumulation
            prev_hash = header.get("previousHash", "")
            if prev_hash and prev_hash != "0" * 64:
                queries = self.storage.query()
                prev_header, _ = queries.get_live_header_by_hash(prev_hash)
                if prev_header:
                    prev_work = ChainWork.from_hex(prev_header.chain_work)
                    chain_work = prev_work.add_chain_work(chain_work)

            # Create LiveBlockHeader
            live_header = LiveBlockHeader(
                chain_block_header=header,
                chain_work=chain_work.to_64_pad_hex(),
                is_chain_tip=True,  # TODO: Proper chain tip detection
                is_active=True,
            )

            # Store header
            queries = self.storage.query()
            queries.begin()

            try:
                # Check if header already exists
                exists, _ = queries.live_header_exists(header["hash"])
                if exists:
                    queries.rollback()
                    return

                # Insert new header
                err = queries.insert_new_live_header(live_header)
                if err:
                    raise err

                queries.commit()

                # Publish header event
                self._header_callbacks.publish(header)

                logger.debug(f"Added live header {header['hash']} at height {header.get('height', 0)}")

            except Exception as e:
                queries.rollback()
                raise e

        except Exception as e:
            logger.error(f"Failed to add live header: {e}")

    async def _get_live_height_range(self) -> Any | None:
        """Get height range for live headers."""
        queries = self.storage.query()
        height_range, err = queries.find_live_height_range()

        if err:
            logger.error(f"Failed to get live height range: {err}")
            return None

        return height_range

    async def _get_bulk_height_range(self) -> Any | None:
        """Get height range for bulk headers."""
        # TODO: Implement bulk manager height range
        return None

    def _fetch_latest_present_height(self) -> int:
        """Fetch latest present height from ingestors."""
        max_height = 0

        for ingestor in self.live_ingestors:
            try:
                height = ingestor.ingestor.get_present_height()
                max_height = max(max_height, height)
            except Exception as e:
                logger.error(f"Failed to get present height from {ingestor.name}: {e}")

        return max_height if max_height > 0 else 800000  # Default fallback
