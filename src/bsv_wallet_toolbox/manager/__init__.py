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
from bsv_wallet_toolbox.manager.wallet_settings_manager import (
    DEFAULT_SETTINGS,
    TESTNET_DEFAULT_SETTINGS,
    WalletSettings,
    WalletSettingsManager,
)

__all__ = [
    "DEFAULT_SETTINGS",
    "TESTNET_DEFAULT_SETTINGS",
    "CWIStyleWalletManager",
    "SimpleWalletManager",
    "WalletPermissionsManager",
    "WalletSettings",
    "WalletSettingsManager",
]
