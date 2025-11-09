"""Binary data reader for byte arrays.

Provides utilities for reading structured data from byte arrays with position tracking.

Reference: toolbox/ts-wallet-toolbox/src/utility/ReaderUint8Array.ts
"""

from __future__ import annotations


class ReaderUint8Array:
    """Reader for binary data in byte array format.

    Maintains position and provides methods to read various data types.

    Reference: toolbox/ts-wallet-toolbox/src/utility/ReaderUint8Array.ts:4+
    """

    def __init__(self, data: list[int] | bytes) -> None:
        """Initialize reader with data.

        Args:
            data: Byte array as list[int] or bytes
        """
        if isinstance(data, bytes):
            self.data = list(data)
        else:
            self.data = data
        self.position = 0

    def read_uint8(self) -> int:
        """Read single byte (uint8).

        Returns:
            Value (0-255)

        Raises:
            IndexError: If position is at end of data
        """
        if self.position >= len(self.data):
            raise IndexError("Attempt to read past end of data")
        value = self.data[self.position]
        self.position += 1
        return value

    def read_uint16_le(self) -> int:
        """Read little-endian uint16.

        Returns:
            Value (0-65535)
        """
        if self.position + 1 >= len(self.data):
            raise IndexError("Attempt to read past end of data")
        value = self.data[self.position] | (self.data[self.position + 1] << 8)
        self.position += 2
        return value

    def read_uint32_le(self) -> int:
        """Read little-endian uint32.

        Returns:
            Value
        """
        if self.position + 3 >= len(self.data):
            raise IndexError("Attempt to read past end of data")
        value = (
            self.data[self.position]
            | (self.data[self.position + 1] << 8)
            | (self.data[self.position + 2] << 16)
            | (self.data[self.position + 3] << 24)
        )
        self.position += 4
        return value

    def read_uint64_le(self) -> int:
        """Read little-endian uint64.

        Returns:
            Value
        """
        if self.position + 7 >= len(self.data):
            raise IndexError("Attempt to read past end of data")
        value = (
            self.data[self.position]
            | (self.data[self.position + 1] << 8)
            | (self.data[self.position + 2] << 16)
            | (self.data[self.position + 3] << 24)
            | (self.data[self.position + 4] << 32)
            | (self.data[self.position + 5] << 40)
            | (self.data[self.position + 6] << 48)
            | (self.data[self.position + 7] << 56)
        )
        self.position += 8
        return value

    def read_bytes(self, count: int) -> list[int]:
        """Read specified number of bytes.

        Args:
            count: Number of bytes to read

        Returns:
            List of bytes read
        """
        if self.position + count > len(self.data):
            raise IndexError("Attempt to read past end of data")
        value = self.data[self.position : self.position + count]
        self.position += count
        return value

    def skip(self, count: int) -> None:
        """Skip specified number of bytes.

        Args:
            count: Number of bytes to skip
        """
        self.position += count

    def is_at_end(self) -> bool:
        """Check if at end of data.

        Returns:
            True if position is at or past end of data
        """
        return self.position >= len(self.data)

    def get_position(self) -> int:
        """Get current read position.

        Returns:
            Current position in data
        """
        return self.position

    def set_position(self, position: int) -> None:
        """Set read position.

        Args:
            position: New position
        """
        self.position = position

    def get_remaining(self) -> int:
        """Get number of bytes remaining.

        Returns:
            Number of bytes from current position to end
        """
        return max(0, len(self.data) - self.position)
