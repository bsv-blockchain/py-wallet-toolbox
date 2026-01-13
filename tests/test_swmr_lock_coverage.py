"""Coverage tests for SingleWriterMultiReaderLock.

This module tests the async reader-writer lock implementation to ensure
proper concurrent access control.
"""

import asyncio

import pytest

from bsv_wallet_toolbox.single_writer_multi_reader_lock import SingleWriterMultiReaderLock


class TestSingleWriterMultiReaderLock:
    """Test SingleWriterMultiReaderLock class."""

    @pytest.mark.asyncio
    async def test_single_reader(self) -> None:
        """Test single reader can acquire and release lock."""
        lock = SingleWriterMultiReaderLock()
        result = []

        async def read_fn():
            result.append("read")
            return "read_result"

        output = await lock.with_read_lock(read_fn)

        assert output == "read_result"
        assert result == ["read"]
        assert lock._readers == 0  # Should be released

    @pytest.mark.asyncio
    async def test_single_writer(self) -> None:
        """Test single writer can acquire and release lock."""
        lock = SingleWriterMultiReaderLock()
        result = []

        async def write_fn():
            result.append("write")
            return "write_result"

        output = await lock.with_write_lock(write_fn)

        assert output == "write_result"
        assert result == ["write"]
        assert not lock._writer  # Should be released

    @pytest.mark.asyncio
    async def test_multiple_concurrent_readers(self) -> None:
        """Test multiple readers can execute concurrently."""
        lock = SingleWriterMultiReaderLock()
        results = []

        async def read_fn(reader_id: int):
            results.append(f"start_{reader_id}")
            await asyncio.sleep(0.01)  # Simulate some work
            results.append(f"end_{reader_id}")
            return f"reader_{reader_id}"

        # Start multiple readers concurrently
        tasks = [lock.with_read_lock(lambda i=i: read_fn(i)) for i in range(3)]
        outputs = await asyncio.gather(*tasks)

        assert len(outputs) == 3
        assert all(f"reader_{i}" in outputs for i in range(3))
        # All readers should have started before any finished
        # (proving they ran concurrently)
        assert results.count("start_0") > 0
        assert lock._readers == 0  # All should be released

    @pytest.mark.asyncio
    async def test_writer_blocks_readers(self) -> None:
        """Test that writer blocks readers."""
        lock = SingleWriterMultiReaderLock()
        execution_order = []

        async def write_fn():
            execution_order.append("write_start")
            await asyncio.sleep(0.02)
            execution_order.append("write_end")

        async def read_fn():
            execution_order.append("read")

        # Start writer first
        write_task = asyncio.create_task(lock.with_write_lock(write_fn))
        await asyncio.sleep(0.001)  # Let writer acquire lock

        # Now try to read
        read_task = asyncio.create_task(lock.with_read_lock(read_fn))

        await asyncio.gather(write_task, read_task)

        # Reader should only execute after writer finishes
        write_end_idx = execution_order.index("write_end")
        read_idx = execution_order.index("read")
        assert read_idx > write_end_idx

    @pytest.mark.asyncio
    async def test_readers_block_writer(self) -> None:
        """Test that readers block writer."""
        lock = SingleWriterMultiReaderLock()
        execution_order = []

        async def read_fn(reader_id: int):
            execution_order.append(f"read_start_{reader_id}")
            await asyncio.sleep(0.02)
            execution_order.append(f"read_end_{reader_id}")

        async def write_fn():
            execution_order.append("write")

        # Start readers first
        read_tasks = [asyncio.create_task(lock.with_read_lock(lambda i=i: read_fn(i))) for i in range(2)]
        await asyncio.sleep(0.001)  # Let readers acquire locks

        # Now try to write
        write_task = asyncio.create_task(lock.with_write_lock(write_fn))

        await asyncio.gather(*read_tasks, write_task)

        # Writer should only execute after all readers finish
        read_end_indices = [i for i, x in enumerate(execution_order) if x.startswith("read_end")]
        write_idx = execution_order.index("write")
        assert write_idx > max(read_end_indices)

    @pytest.mark.asyncio
    async def test_writer_priority_over_readers(self) -> None:
        """Test that waiting writers block new readers (writer priority)."""
        lock = SingleWriterMultiReaderLock()
        execution_order = []

        async def read_fn(reader_id: int):
            execution_order.append(f"read_{reader_id}")
            await asyncio.sleep(0.01)

        async def write_fn():
            execution_order.append("write")
            await asyncio.sleep(0.01)

        # Start first reader
        read1_task = asyncio.create_task(lock.with_read_lock(lambda: read_fn(1)))
        await asyncio.sleep(0.001)

        # Queue a writer (should increment pending_writers)
        write_task = asyncio.create_task(lock.with_write_lock(write_fn))
        await asyncio.sleep(0.001)

        # Try to start another reader (should be blocked by pending writer)
        read2_task = asyncio.create_task(lock.with_read_lock(lambda: read_fn(2)))

        await asyncio.gather(read1_task, write_task, read2_task)

        # Order should be: read_1, write, read_2
        assert execution_order.index("read_1") < execution_order.index("write")
        assert execution_order.index("write") < execution_order.index("read_2")

    @pytest.mark.asyncio
    async def test_exception_in_read_fn_releases_lock(self) -> None:
        """Test that lock is released even if read function raises exception."""
        lock = SingleWriterMultiReaderLock()

        async def failing_read_fn():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            await lock.with_read_lock(failing_read_fn)

        # Lock should be released
        assert lock._readers == 0

        # Should be able to acquire lock again
        async def normal_read_fn():
            return "success"

        result = await lock.with_read_lock(normal_read_fn)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_exception_in_write_fn_releases_lock(self) -> None:
        """Test that lock is released even if write function raises exception."""
        lock = SingleWriterMultiReaderLock()

        async def failing_write_fn():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            await lock.with_write_lock(failing_write_fn)

        # Lock should be released
        assert not lock._writer

        # Should be able to acquire lock again
        async def normal_write_fn():
            return "success"

        result = await lock.with_write_lock(normal_write_fn)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_lock_state_initialization(self) -> None:
        """Test initial lock state."""
        lock = SingleWriterMultiReaderLock()

        assert lock._readers == 0
        assert lock._writer is False
        assert lock._pending_writers == 0
        assert isinstance(lock._read_ready, asyncio.Condition)
        assert isinstance(lock._write_ready, asyncio.Condition)

    @pytest.mark.asyncio
    async def test_multiple_sequential_operations(self) -> None:
        """Test multiple sequential read/write operations."""
        lock = SingleWriterMultiReaderLock()
        results = []

        async def read_fn(i: int):
            results.append(f"R{i}")

        async def write_fn(i: int):
            results.append(f"W{i}")

        # Execute sequence: R-R-W-R-W-R
        await lock.with_read_lock(lambda: read_fn(1))
        await lock.with_read_lock(lambda: read_fn(2))
        await lock.with_write_lock(lambda: write_fn(1))
        await lock.with_read_lock(lambda: read_fn(3))
        await lock.with_write_lock(lambda: write_fn(2))
        await lock.with_read_lock(lambda: read_fn(4))

        assert results == ["R1", "R2", "W1", "R3", "W2", "R4"]
        assert lock._readers == 0
        assert not lock._writer

    @pytest.mark.asyncio
    async def test_readers_notified_after_writer_releases(self) -> None:
        """Test that waiting readers are notified when writer releases."""
        lock = SingleWriterMultiReaderLock()
        execution_order = []

        async def write_fn():
            execution_order.append("write_start")
            await asyncio.sleep(0.02)
            execution_order.append("write_end")

        async def read_fn(i: int):
            execution_order.append(f"read_{i}")

        # Start writer
        write_task = asyncio.create_task(lock.with_write_lock(write_fn))
        await asyncio.sleep(0.001)

        # Queue multiple readers while writer is active
        read_tasks = [asyncio.create_task(lock.with_read_lock(lambda i=i: read_fn(i))) for i in range(3)]

        await asyncio.gather(write_task, *read_tasks)

        # All readers should execute after writer finishes
        write_end_idx = execution_order.index("write_end")
        for i in range(3):
            read_idx = execution_order.index(f"read_{i}")
            assert read_idx > write_end_idx
