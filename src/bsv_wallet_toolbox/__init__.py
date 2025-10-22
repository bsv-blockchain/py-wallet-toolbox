"""BSV Wallet Toolbox - BRC-100 compliant wallet implementation.

This package provides a production-ready implementation of the BRC-100
WalletInterface, compatible with TypeScript and Go implementations.

Reference: toolbox/ts-wallet-toolbox/src/
"""

from .errors import InvalidParameterError
from .services import Services, WalletServices, WalletServicesOptions, create_default_options
from .services.chaintracker.chaintracks.api import (
    BaseBlockHeader,
    BlockHeader,
    BlockHeaderTypes,
    ChaintracksClientApi,
    ChaintracksInfo,
    ChaintracksPackageInfo,
    HeaderListener,
    LiveBlockHeader,
    ReorgListener,
    is_base_block_header,
    is_block_header,
    is_live,
    is_live_block_header,
)
from .services.providers import WhatsOnChain
from .wallet import Wallet

__version__ = "0.6.0"
__all__ = [
    "BaseBlockHeader",
    "BlockHeader",
    "BlockHeaderTypes",
    "ChaintracksClientApi",
    "ChaintracksInfo",
    "ChaintracksPackageInfo",
    "HeaderListener",
    "InvalidParameterError",
    "LiveBlockHeader",
    "ReorgListener",
    "Services",
    "Wallet",
    "WalletServices",
    "WalletServicesOptions",
    "WhatsOnChain",
    "create_default_options",
    "is_base_block_header",
    "is_block_header",
    "is_live",
    "is_live_block_header",
]
