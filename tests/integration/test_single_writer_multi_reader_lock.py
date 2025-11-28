"""Unit tests for SingleWriterMultiReaderLock.

This module tests the single writer/multi-reader lock utility for safe concurrent access.

Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/SingleWriterMultiReaderLock.test.ts
"""

import asyncio

import pytest

try:
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.util import SingleWriterMultiReaderLock

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class LockHelper:
    """Helper class for testing lock behavior.

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/SingleWriterMultiReaderLock.test.ts
               class TestLock
    """

    def __init__(self):
        self.lock = SingleWriterMultiReaderLock() if IMPORTS_AVAILABLE else None
        self.value = 0

    async def read_value(self) -> int:
        """Read the current value with a read lock.

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/SingleWriterMultiReaderLock.test.ts
                   async readValue()
        """

        async def read_fn():
            # Simulate some read delay
            await asyncio.sleep(0.01)
            return self.value

        return await self.lock.with_read_lock(read_fn)

    async def write_value(self, new_value: int) -> int:
        """Write a new value with a write lock.

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/SingleWriterMultiReaderLock.test.ts
                   async writeValue(newValue: number)
        """

        async def write_fn():
            # Simulate some write delay
            await asyncio.sleep(0.05)
            self.value = new_value
            return self.value

        return await self.lock.with_write_lock(write_fn)

    async def run_concurrent_read_write_test(self) -> list:
        """Test concurrent reads and writes.

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/SingleWriterMultiReaderLock.test.ts
                   async test()
        """
        promises = []
        read_count = 3

        # First batch of reads
        for _ in range(read_count):
            promises.append(self.read_value())

        # First batch of writes
        promises.append(self.write_value(42))
        promises.append(self.write_value(43))
        promises.append(self.write_value(47))

        # Second batch of reads
        for _ in range(read_count):
            promises.append(self.read_value())

        # Second batch of writes
        promises.append(self.write_value(44))
        promises.append(self.write_value(45))
        promises.append(self.write_value(46))

        # Third batch of reads
        for _ in range(read_count):
            promises.append(self.read_value())

        # Wait for all operations to complete
        results = await asyncio.gather(*promises)
        return results


class TestSingleWriterMultiReaderLock:
    """Test suite for SingleWriterMultiReaderLock.

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/SingleWriterMultiReaderLock.test.ts
               describe('SingleWriterMultiReaderLock tests')
    """

    @pytest.mark.asyncio
    async def test_concurrent_reads_and_writes_execute_in_correct_order(self) -> None:
        """Given: LockHelper instance with concurrent read/write operations
           When: Execute run_concurrent_read_write_test() which runs multiple concurrent reads and writes
           Then: Results should match expected sequence [0, 0, 0, 42, 43, 47, 46, 46, 46, 44, 45, 46, 46, 46, 46]

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/SingleWriterMultiReaderLock.test.ts
                   test('0_')
        """
        # Given
        t = LockHelper()

        # When
        r = await t.run_concurrent_read_write_test()

        # Then
        assert r == [0, 0, 0, 42, 43, 47, 46, 46, 46, 44, 45, 46, 46, 46, 46]
