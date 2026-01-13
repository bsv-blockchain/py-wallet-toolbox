"""Block header utilities.

Provides functions for serializing, deserializing, and hashing block headers.

Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/blockHeaderUtilities.ts
"""

import hashlib

from bsv_wallet_toolbox.services.chaintracker.chaintracks.api import BaseBlockHeader
from bsv_wallet_toolbox.services.wallet_services import Chain


def block_hash(buffer: bytes) -> str:
    """Compute double SHA256 hash of buffer.

    Args:
        buffer: Bytes to hash

    Returns:
        Hex string of the hash

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/blockHeaderUtilities.ts
               blockHash()
    """
    # Double SHA256
    first_hash = hashlib.sha256(buffer).digest()
    second_hash = hashlib.sha256(first_hash).digest()
    return second_hash[::-1].hex()  # Reverse byte order


def deserialize_base_block_headers(buffer: bytes, offset: int = 0, count: int | None = None) -> list[BaseBlockHeader]:
    """Deserialize base block headers from buffer.

    Args:
        buffer: Binary data containing headers
        offset: Starting offset in buffer
        count: Number of headers to deserialize (None for all remaining)

    Returns:
        List of deserialized base block headers

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/blockHeaderUtilities.ts
               deserializeBaseBlockHeaders()
    """
    headers = []
    header_size = 80
    buffer_len = len(buffer)

    if count is None:
        count = (buffer_len - offset) // header_size

    for i in range(count):
        if offset + (i + 1) * header_size > buffer_len:
            break

        header_buffer = buffer[offset + i * header_size : offset + (i + 1) * header_size]
        header = deserialize_base_block_header(header_buffer, 0)
        headers.append(header)

    return headers


def serialize_base_block_header(header: BaseBlockHeader) -> bytes:
    """Serialize base block header to bytes.

    Args:
        header: Block header to serialize

    Returns:
        Serialized header bytes (80 bytes)

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/blockHeaderUtilities.ts
               serializeBaseBlockHeader()
    """
    buffer = bytearray(80)

    # Version (4 bytes, little endian)
    buffer[0:4] = int(header["version"]).to_bytes(4, "little")

    # Previous hash (32 bytes, reversed)
    prev_hash_bytes = bytes.fromhex(header["previousHash"])[::-1]
    buffer[4:36] = prev_hash_bytes

    # Merkle root (32 bytes, reversed)
    merkle_root_bytes = bytes.fromhex(header["merkleRoot"])[::-1]
    buffer[36:68] = merkle_root_bytes

    # Time (4 bytes, little endian)
    buffer[68:72] = int(header["time"]).to_bytes(4, "little")

    # Bits (4 bytes, little endian)
    buffer[72:76] = int(header["bits"]).to_bytes(4, "little")

    # Nonce (4 bytes, little endian)
    buffer[76:80] = int(header["nonce"]).to_bytes(4, "little")

    return bytes(buffer)


def deserialize_base_block_header(buffer: bytes, offset: int = 0) -> BaseBlockHeader:
    """Deserialize base block header from buffer.

    Args:
        buffer: Binary data containing header
        offset: Starting offset in buffer

    Returns:
        Deserialized base block header

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/blockHeaderUtilities.ts
               deserializeBaseBlockHeader()
    """
    if len(buffer) - offset < 80:
        raise ValueError("Buffer too small for block header")

    # Version (4 bytes, little endian)
    version = int.from_bytes(buffer[offset : offset + 4], "little")

    # Previous hash (32 bytes, reversed)
    prev_hash = buffer[offset + 4 : offset + 36][::-1].hex()

    # Merkle root (32 bytes, reversed)
    merkle_root = buffer[offset + 36 : offset + 68][::-1].hex()

    # Time (4 bytes, little endian)
    time_val = int.from_bytes(buffer[offset + 68 : offset + 72], "little")

    # Bits (4 bytes, little endian)
    bits = int.from_bytes(buffer[offset + 72 : offset + 76], "little")

    # Nonce (4 bytes, little endian)
    nonce = int.from_bytes(buffer[offset + 76 : offset + 80], "little")

    return {
        "version": version,
        "previousHash": prev_hash,
        "merkleRoot": merkle_root,
        "time": time_val,
        "bits": bits,
        "nonce": nonce,
    }


def genesis_buffer(chain: Chain) -> bytes:
    """Get genesis block header buffer for chain.

    Args:
        chain: Blockchain network ("main" or "test")

    Returns:
        Serialized genesis block header

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/blockHeaderUtilities.ts
               genesisBuffer()
    """
    header = genesis_header(chain)
    return serialize_base_block_header(header)


def genesis_header(chain: Chain) -> BaseBlockHeader:
    """Get genesis block header for chain.

    Args:
        chain: Blockchain network ("main" or "test")

    Returns:
        Genesis block header

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/blockHeaderUtilities.ts
               genesisHeader()
    """
    if chain == "main":
        return {
            "version": 1,
            "previousHash": "0000000000000000000000000000000000000000000000000000000000000000",
            "merkleRoot": "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b",
            "time": 1231006505,
            "bits": 486604799,
            "nonce": 2083236893,
        }
    elif chain == "test":
        return {
            "version": 1,
            "previousHash": "0000000000000000000000000000000000000000000000000000000000000000",
            "merkleRoot": "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b",
            "time": 1296688602,
            "bits": 486604799,
            "nonce": 414098458,
        }
    else:
        raise ValueError(f"Unknown chain: {chain}")
