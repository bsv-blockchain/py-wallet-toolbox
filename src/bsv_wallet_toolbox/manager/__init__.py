"""Manager layer implementations for BSV Wallet Toolbox.

This module contains wallet manager implementations that handle authentication,
key management, and delegation to underlying wallet instances.

Reference: toolbox/ts-wallet-toolbox/src/{SimpleWalletManager,CWIStyleWalletManager,WalletPermissionsManager}.ts
"""

from bsv_wallet_toolbox.manager.cwi_style_wallet_manager import (
    CWIStyleWalletManager,
)
from bsv_wallet_toolbox.manager.simple_wallet_manager import SimpleWalletManager
from bsv_wallet_toolbox.manager.wallet_permissions_manager import (
    WalletPermissionsManager,
)

__all__ = [
    "CWIStyleWalletManager",
    "SimpleWalletManager",
    "WalletPermissionsManager",
]
