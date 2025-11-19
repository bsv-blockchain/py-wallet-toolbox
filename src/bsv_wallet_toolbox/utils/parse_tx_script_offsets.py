"""Parse transaction script offsets.

Extract input and output script offsets from raw transaction byte array.

Reference: toolbox/ts-wallet-toolbox/src/utility/parseTxScriptOffsets.ts
"""

from __future__ import annotations

from typing import TypedDict


class TxScriptOffsets(TypedDict, total=False):
    """Transaction script offset information."""

    inputs: list[int]
    outputs: list[int]


def parse_tx_script_offsets(raw_tx: list[int]) -> TxScriptOffsets:
    """Parse transaction to extract input and output script offsets.

    Analyzes raw transaction byte array to find where input and output
    locking scripts begin within the transaction structure.

    Args:
        raw_tx: Raw transaction bytes as list of integers (0-255)

    Returns:
        Dictionary with 'inputs' and 'outputs' keys containing offset lists

    Reference: toolbox/ts-wallet-toolbox/src/utility/parseTxScriptOffsets.ts:8+
    """
    inputs: list[int] = []
    outputs: list[int] = []

    if not raw_tx or len(raw_tx) < 10:
        # Transaction too short to parse
        return {"inputs": inputs, "outputs": outputs}

    offset = 0

    # Skip version (4 bytes)
    offset += 4

    # Read number of inputs (varint)
    input_count, bytes_read = _read_varint(raw_tx, offset)
    offset += bytes_read

    # Process inputs
    for _ in range(input_count):
        # Skip previous transaction hash (32 bytes)
        offset += 32

        # Skip previous transaction output index (4 bytes)
        offset += 4

        # Read script length (varint)
        script_length, bytes_read = _read_varint(raw_tx, offset)
        offset += bytes_read

        # Record script offset
        inputs.append(offset)

        # Skip script
        offset += script_length

        # Skip sequence (4 bytes)
        offset += 4

    # Read number of outputs (varint)
    output_count, bytes_read = _read_varint(raw_tx, offset)
    offset += bytes_read

    # Process outputs
    for _ in range(output_count):
        # Skip satoshis (8 bytes)
        offset += 8

        # Read script length (varint)
        script_length, bytes_read = _read_varint(raw_tx, offset)
        offset += bytes_read

        # Record script offset
        outputs.append(offset)

        # Skip script
        offset += script_length

    return {"inputs": inputs, "outputs": outputs}


def _read_varint(data: list[int], offset: int) -> tuple[int, int]:
    """Read varint (variable-length integer) from byte array.

    Args:
        data: Byte array to read from
        offset: Starting offset in array

    Returns:
        Tuple of (value, bytes_read)
    """
    if offset >= len(data):
        return 0, 0

    first_byte = data[offset]

    if first_byte < 0xFD:
        return first_byte, 1
    elif first_byte == 0xFD:
        if offset + 2 >= len(data):
            return 0, 1
        # Little-endian uint16
        value = data[offset + 1] | (data[offset + 2] << 8)
        return value, 3
    elif first_byte == 0xFE:
        if offset + 4 >= len(data):
            return 0, 1
        # Little-endian uint32
        value = data[offset + 1] | (data[offset + 2] << 8) | (data[offset + 3] << 16) | (data[offset + 4] << 24)
        return value, 5
    elif first_byte == 0xFF:
        if offset + 8 >= len(data):
            return 0, 1
        # Little-endian uint64
        value = (
            data[offset + 1]
            | (data[offset + 2] << 8)
            | (data[offset + 3] << 16)
            | (data[offset + 4] << 24)
            | (data[offset + 5] << 32)
            | (data[offset + 6] << 40)
            | (data[offset + 7] << 48)
            | (data[offset + 8] << 56)
        )
        return value, 9

    return 0, 1
