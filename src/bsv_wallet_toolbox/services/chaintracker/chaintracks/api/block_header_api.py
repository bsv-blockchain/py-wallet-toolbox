"""Block header types and interfaces.

This module defines types for block headers used by ChaintracksClientApi.

Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Api/BlockHeaderApi.ts
"""

from typing import TypedDict


class BaseBlockHeader(TypedDict):
    """Base block header structure (80 bytes when serialized).

    This is the Python equivalent of TypeScript's BaseBlockHeader.
    Contains the essential fields of a Bitcoin block header.

    Note: BaseBlockHeader is re-exported from WalletServices.interfaces in TypeScript.

    Reference:
        - toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Api/BlockHeaderApi.ts
        - toolbox/ts-wallet-toolbox/src/sdk/WalletServices.interfaces.ts
    """

    version: int  # Block version number. Serialized length is 4 bytes.
    previousHash: str  # Hash of the previous block. Serialized length is 32 bytes.
    merkleRoot: str  # Merkle root of the block's transactions. Serialized length is 32 bytes.
    time: int  # Block timestamp (Unix epoch time). Serialized length is 4 bytes.
    bits: int  # Difficulty target in compact format. Serialized length is 4 bytes.
    nonce: int  # Block header nonce value. Serialized length is 4 bytes.


class BlockHeader(BaseBlockHeader):
    """Block header extended with computed hash and height.

    This is the Python equivalent of TypeScript's BlockHeader.
    Extends BaseBlockHeader with additional computed fields.

    Note: BlockHeader is re-exported from WalletServices.interfaces in TypeScript.

    Reference:
        - toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Api/BlockHeaderApi.ts
        - toolbox/ts-wallet-toolbox/src/sdk/WalletServices.interfaces.ts
    """

    height: int  # Height of the header, starting from zero.
    hash: str  # The double sha256 hash of the serialized BaseBlockHeader fields.


class LiveBlockHeader(BlockHeader):
    """Live block header with additional chain tracking fields.

    The "live" portion of the blockchain is recent history that can conceivably
    be subject to reorganizations. The additional fields support tracking orphan
    blocks, chain forks, and chain reorgs.

    Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Api/BlockHeaderApi.ts
    """

    chainWork: str  # Cumulative chainwork achieved by this block. Only matters for active chain selection.
    isChainTip: bool  # True only if this header is currently a chain tip (no header follows it).
    isActive: bool  # True only if this header is currently on the active chain.
    headerId: int  # Unique ID while part of "live" portion of blockchain.
    previousHeaderId: int | None  # Links to ancestor header. Due to forks, multiple headers may share this.


class ChaintracksPackageInfo(TypedDict):
    """Information about a chaintracks package.

    Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Api/ChaintracksClientApi.ts
    """

    name: str
    version: str


class ChaintracksInfo(TypedDict):
    """Summary of chaintracks configuration and state.

    Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Api/ChaintracksClientApi.ts
    """

    chain: str  # 'main' or 'test'
    heightBulk: int
    heightLive: int
    storage: str
    bulkIngestors: list[str]
    liveIngestors: list[str]
    packages: list[ChaintracksPackageInfo]


# Type aliases for type guard functions
BlockHeaderTypes = BaseBlockHeader | BlockHeader | LiveBlockHeader


def is_live(header: BlockHeader | LiveBlockHeader) -> bool:
    """Type guard function to check if header is LiveBlockHeader.

    Args:
        header: BlockHeader or LiveBlockHeader to check

    Returns:
        True if header is LiveBlockHeader (has headerId field)

    Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Api/BlockHeaderApi.ts
    """
    return "headerId" in header


def is_base_block_header(header: BlockHeaderTypes) -> bool:
    """Type guard function to check if header is BaseBlockHeader.

    Args:
        header: Any block header type to check

    Returns:
        True if header has previousHash field (basic indicator)

    Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Api/BlockHeaderApi.ts
    """
    return isinstance(header.get("previousHash"), str)


def is_block_header(header: BlockHeaderTypes) -> bool:
    """Type guard function to check if header is BlockHeader.

    Args:
        header: Any block header type to check

    Returns:
        True if header has height field and previousHash

    Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Api/BlockHeaderApi.ts
    """
    return "height" in header and isinstance(header.get("previousHash"), str)


def is_live_block_header(header: BlockHeaderTypes) -> bool:
    """Type guard function to check if header is LiveBlockHeader.

    Args:
        header: Any block header type to check

    Returns:
        True if header has chainWork field and previousHash

    Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Api/BlockHeaderApi.ts
    """
    return "chainWork" in header and isinstance(header.get("previousHash"), str)
