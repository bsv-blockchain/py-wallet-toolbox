"""BSV Wallet Toolbox - BRC-100 compliant wallet implementation.

This package provides a production-ready implementation of the BRC-100
WalletInterface, compatible with TypeScript and Go implementations.
"""

from .errors import InvalidParameterError
from .services import MockWalletServices, WalletServices
from .wallet import Wallet

__version__ = "0.5.0"
__all__ = [
    "InvalidParameterError",
    "MockWalletServices",
    "Wallet",
    "WalletServices",
]
