"""Live ingestor that polls WhatsOnChain for block headers.

Provides functionality for polling block header data from WhatsOnChain API
with caching and background polling capabilities.

Reference: go-wallet-toolbox/pkg/services/chaintracks/ingest/live_ingestor_woc_poll.go
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from ...wallet_services import Chain
from .live_ingestor_interface import LiveIngestor
from .woc_client import WOCClient

logger = logging.getLogger(__name__)


class LiveIngestorWocPoll(LiveIngestor):
    """Live ingestor that polls block headers from WhatsOnChain.

    Polls WhatsOnChain API for new block headers at regular intervals,
    caches seen headers, and notifies subscribers of new blocks.

    Reference: go-wallet-toolbox/pkg/services/chaintracks/ingest/live_ingestor_woc_poll.go
    """

    def __init__(self, chain: Chain, sync_period: float = 60.0, api_key: str | None = None, cache_size: int = 500):
        """Initialize WOC polling ingestor.

        Args:
            chain: Blockchain network ("main" or "test")
            sync_period: Polling interval in seconds (default 60)
            api_key: Optional WhatsOnChain API key
            cache_size: Size of LRU cache for seen headers (default 500)
        """
        self.chain = chain
        self.sync_period = sync_period
        self.api_key = api_key
        self.cache_size = cache_size

        self.woc_client = WOCClient(chain, api_key)

        # Background polling state
        self._polling_task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._callbacks: list[Callable] = []

        # LRU cache for seen header hashes
        self._seen_headers: set[str] = set()

        logger.info(f"LiveIngestorWocPoll initialized for {chain} chain with {sync_period}s sync period")

    def start_listening(self, callback: Callable) -> None:
        """Start listening for new block headers.

        Args:
            callback: Function to call when new headers are received.
                     Should accept a list of block header dicts.
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

        if self._polling_task is None or self._polling_task.done():
            self._stop_event.clear()
            self._polling_task = asyncio.create_task(self._poll_loop())
            logger.info("LiveIngestorWocPoll started listening")

    def stop_listening(self) -> None:
        """Stop listening for new block headers."""
        if self._polling_task and not self._polling_task.done():
            self._stop_event.set()
            logger.info("LiveIngestorWocPoll stopping listening")

    def get_header_by_hash(self, block_hash: str) -> dict[str, Any] | None:
        """Get block header by hash.

        Args:
            block_hash: Block hash

        Returns:
            Block header dict or None if not found
        """
        try:
            dto = self.woc_client.get_header_by_hash(block_hash)
            return dto.to_block_header() if dto else None
        except Exception as e:
            logger.error(f"Failed to get header by hash {block_hash}: {e}")
            return None

    def get_present_height(self) -> int:
        """Get current blockchain height.

        Returns:
            Current block height
        """
        try:
            return self.woc_client.get_present_height()
        except Exception as e:
            logger.error(f"Failed to get present height: {e}")
            return 0

    async def _poll_loop(self) -> None:
        """Main polling loop."""
        logger.info("LiveIngestorWocPoll polling loop started")

        # Initial poll
        await self._process_new_headers()

        while not self._stop_event.is_set():
            try:
                # Wait for sync period or stop event
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.sync_period)
                if self._stop_event.is_set():
                    break

                await self._process_new_headers()

            except TimeoutError:
                # Normal timeout, continue polling
                continue
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(5)

        logger.info("LiveIngestorWocPoll polling loop stopped")

    async def _process_new_headers(self) -> None:
        """Fetch and process new headers."""
        try:
            # Get last 10 headers (should include any new ones)
            dtos = self.woc_client.get_last_headers(10)

            # Convert to block headers
            headers = []
            for dto in dtos:
                header = dto.to_block_header()
                header_hash = header["hash"]

                # Check if we've seen this header before
                if header_hash not in self._seen_headers:
                    self._seen_headers.add(header_hash)
                    headers.append(header)

                    # Limit cache size
                    if len(self._seen_headers) > self.cache_size:
                        # Remove oldest entries (simple FIFO)
                        oldest_to_remove = len(self._seen_headers) - self.cache_size
                        self._seen_headers = set(list(self._seen_headers)[oldest_to_remove:])

            # Notify callbacks if we have new headers
            if headers and self._callbacks:
                # Sort by height (oldest first)
                headers.sort(key=lambda h: h["height"])

                logger.info(f"LiveIngestorWocPoll found {len(headers)} new headers")

                # Call all callbacks
                for callback in self._callbacks:
                    try:
                        callback(headers)
                    except Exception as e:
                        logger.error(f"Error in header callback: {e}")

        except Exception as e:
            logger.error(f"Failed to process new headers: {e}")
