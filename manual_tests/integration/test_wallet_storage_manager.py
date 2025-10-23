"""Unit tests for WalletStorageManager.

These tests verify the reader/writer/sync interlocking mechanisms
for concurrent storage access.

Reference: wallet-toolbox/src/storage/__test/WalletStorageManager.test.ts
"""

import asyncio
import time
from typing import Literal, Never

import pytest


class TestWalletStorageManager:
    """Test suite for WalletStorageManager.

    Reference: wallet-toolbox/src/storage/__test/WalletStorageManager.test.ts
    """

    @pytest.mark.skip(reason="WalletStorageManager implementation not ready yet")
    @pytest.mark.asyncio
    async def test_runasreader_runaswriter_runassync_interlock_correctly(self) -> None:
        """Given: Storage manager with concurrent reader, writer, and sync operations
           When: Execute multiple readers, writers, and syncs with varying durations
           Then: No time overlaps occur between non-reader operations (writer/sync must be exclusive)

        Reference: wallet-toolbox/src/storage/__test/WalletStorageManager.test.ts
                   test('1_runAsReader runAsWriter runAsSync interlock correctly')
        """
        # Given
        storage = await create_sqlite_test_storage("syncTest1")

        class Result:
            def __init__(self, i: int, t: Literal["reader", "writer", "sync"], start: float, end: float):
                self.i = i
                self.t = t
                self.start = start
                self.end = end

        result: list[Result] = []
        promises: list = []

        now = time.time() * 1000  # milliseconds

        async def make_reader(i: int, duration: int) -> Result:
            async def reader_func(reader):
                start = time.time() * 1000 - now
                await asyncio.sleep(duration / 1000)
                end = time.time() * 1000 - now
                r = Result(i=i, t="reader", start=start, end=end)
                result.append(r)
                return r

            return await storage.run_as_reader(reader_func)

        async def make_writer(i: int, duration: int) -> Result:
            async def writer_func(writer):
                start = time.time() * 1000 - now
                await asyncio.sleep(duration / 1000)
                end = time.time() * 1000 - now
                r = Result(i=i, t="writer", start=start, end=end)
                result.append(r)
                return r

            return await storage.run_as_writer(writer_func)

        async def make_sync(i: int, duration: int) -> Result:
            async def sync_func(sync):
                start = time.time() * 1000 - now
                await asyncio.sleep(duration / 1000)
                end = time.time() * 1000 - now
                r = Result(i=i, t="sync", start=start, end=end)
                result.append(r)
                return r

            return await storage.run_as_sync(sync_func)

        # When
        i = 0
        # First batch: 5 readers
        for j in range(5):
            promises.append(make_reader(i, 10 + j * 10))
            i += 1

        # One sync operation
        promises.append(make_sync(i, 5000))
        i += 1

        # Second batch: alternating readers and writers
        for j in range(5):
            promises.append(make_reader(i, 10 + j * 10))
            i += 1
            promises.append(make_writer(i, 30 + j * 500))
            i += 1

        # Another sync operation
        promises.append(make_sync(i, 5000))
        i += 1

        # Third batch: 5 more readers
        for j in range(5):
            promises.append(make_reader(i, 10 + j * 10))
            i += 1

        await asyncio.gather(*promises)

        # Then
        assert result is not None

        # Check for overlaps (non-reader operations should not overlap)
        log = ""
        for r in result:
            overlaps = [
                r2
                for r2 in result
                if r2.i != r.i and (r2.t != "reader" or r.t != "reader") and r.start > r2.start and r.start < r2.end
            ]
            if len(overlaps) > 0:
                log += f"{r.i} {r.t} {r.start} overlaps:\n"
                for o in overlaps:
                    log += f"  {o.i} {o.t} {o.start} {o.end}\n"

        if len(log) > 0:
            print(log)
            assert len(log) == 0, "Time overlaps detected between non-reader operations"

        await storage.destroy()

    @pytest.mark.skip(reason="WalletStorageManager implementation not ready yet")
    @pytest.mark.asyncio
    async def test_runasreader_runaswriter_runassync_interlock_correctly_with_low_durations(self) -> None:
        """Given: Storage manager with concurrent operations using very short durations
           When: Execute multiple readers, writers, and syncs with minimal wait times
           Then: No time overlaps occur between non-reader operations (stress test)

        Reference: wallet-toolbox/src/storage/__test/WalletStorageManager.test.ts
                   test('1a_runAsReader runAsWriter runAsSync interlock correctly with low durations')
        """
        # Given
        storage = await create_sqlite_test_storage("syncTest1a")

        class Result:
            def __init__(self, i: int, t: Literal["reader", "writer", "sync"], start: float, end: float):
                self.i = i
                self.t = t
                self.start = start
                self.end = end

        result: list[Result] = []
        promises: list = []

        now = time.time() * 1000  # milliseconds

        async def make_reader(i: int, duration: int) -> Result:
            async def reader_func(reader):
                start = time.time() * 1000 - now
                await asyncio.sleep(duration / 1000)
                end = time.time() * 1000 - now
                r = Result(i=i, t="reader", start=start, end=end)
                result.append(r)
                return r

            return await storage.run_as_reader(reader_func)

        async def make_writer(i: int, duration: int) -> Result:
            async def writer_func(writer):
                start = time.time() * 1000 - now
                await asyncio.sleep(duration / 1000)
                end = time.time() * 1000 - now
                r = Result(i=i, t="writer", start=start, end=end)
                result.append(r)
                return r

            return await storage.run_as_writer(writer_func)

        async def make_sync(i: int, duration: int) -> Result:
            async def sync_func(sync):
                start = time.time() * 1000 - now
                await asyncio.sleep(duration / 1000)
                end = time.time() * 1000 - now
                r = Result(i=i, t="sync", start=start, end=end)
                result.append(r)
                return r

            return await storage.run_as_sync(sync_func)

        # When - Using very low durations (j milliseconds)
        i = 0
        # First batch: 5 readers with minimal duration
        for j in range(5):
            promises.append(make_reader(i, j))
            i += 1

        # One sync operation
        promises.append(make_sync(i, 5000))
        i += 1

        # Second batch: alternating readers and writers with minimal duration
        for j in range(5):
            promises.append(make_reader(i, j))
            i += 1
            promises.append(make_writer(i, j))
            i += 1

        # Another sync operation
        promises.append(make_sync(i, 5000))
        i += 1

        # Third batch: 5 more readers with minimal duration
        for j in range(5):
            promises.append(make_reader(i, j))
            i += 1

        await asyncio.gather(*promises)

        # Then
        assert result is not None

        # Check for overlaps (non-reader operations should not overlap)
        log = ""
        for r in result:
            overlaps = [
                r2
                for r2 in result
                if r2.i != r.i and (r2.t != "reader" or r.t != "reader") and r.start > r2.start and r.start < r2.end
            ]
            if len(overlaps) > 0:
                log += f"{r.i} {r.t} {r.start} overlaps:\n"
                for o in overlaps:
                    log += f"  {o.i} {o.t} {o.start} {o.end}\n"

        if len(log) > 0:
            print(log)
            assert len(log) == 0, "Time overlaps detected between non-reader operations (low duration stress test)"

        await storage.destroy()


async def create_sqlite_test_storage(database_name: str) -> Never:
    """Create SQLite test storage instance.

    Args:
        database_name: Name of the test database

    Returns:
        WalletStorageManager instance
    """
    raise NotImplementedError("create_sqlite_test_storage not implemented yet")
