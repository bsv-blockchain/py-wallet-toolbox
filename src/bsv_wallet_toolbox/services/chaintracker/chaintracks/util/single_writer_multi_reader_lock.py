"""Single Writer Multi Reader Lock implementation.

Provides a fair reader-writer lock that allows multiple concurrent readers
or a single exclusive writer.

Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/SingleWriterMultiReaderLock.ts
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


class SingleWriterMultiReaderLock:
    """A fair reader-writer lock for async operations.

    Allows multiple concurrent readers or a single exclusive writer.
    Writers have priority to prevent starvation.

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/SingleWriterMultiReaderLock.ts
    """

    def __init__(self) -> None:
        """Initialize the lock."""
        self._readers = 0
        self._writer = False
        self._read_ready = asyncio.Condition()
        self._write_ready = asyncio.Condition()
        self._pending_writers = 0

    async def with_read_lock(self, fn: Callable[[], Awaitable[T]]) -> T:
        """Execute a function with a read lock.

        Multiple readers can execute concurrently.
        Blocks if a writer is active or waiting.

        Args:
            fn: Async function to execute with read lock

        Returns:
            Result from fn()
        """
        await self._acquire_read()
        try:
            return await fn()
        finally:
            await self._release_read()

    async def with_write_lock(self, fn: Callable[[], Awaitable[T]]) -> T:
        """Execute a function with a write lock.

        Only one writer can execute at a time.
        Blocks if any readers or writer is active.

        Args:
            fn: Async function to execute with write lock

        Returns:
            Result from fn()
        """
        await self._acquire_write()
        try:
            return await fn()
        finally:
            await self._release_write()

    async def _acquire_read(self) -> None:
        """Acquire a read lock."""
        async with self._read_ready:
            # Wait while writer is active or writers are pending
            while self._writer or self._pending_writers > 0:
                await self._read_ready.wait()
            self._readers += 1

    async def _release_read(self) -> None:
        """Release a read lock."""
        async with self._read_ready:
            self._readers -= 1
            if self._readers == 0:
                # Notify waiting writers
                async with self._write_ready:
                    self._write_ready.notify()

    async def _acquire_write(self) -> None:
        """Acquire a write lock."""
        async with self._write_ready:
            self._pending_writers += 1
            try:
                # Wait while readers are active or writer is active
                while self._readers > 0 or self._writer:
                    await self._write_ready.wait()
                self._writer = True
            finally:
                self._pending_writers -= 1

    async def _release_write(self) -> None:
        """Release a write lock."""
        async with self._write_ready:
            self._writer = False
            # Notify waiting readers first (fairness)
            async with self._read_ready:
                self._read_ready.notify_all()
            # Then notify waiting writers
            self._write_ready.notify()
