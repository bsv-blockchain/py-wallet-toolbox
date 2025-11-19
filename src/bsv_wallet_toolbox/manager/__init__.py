"""Manager layer implementations for BSV Wallet Toolbox.

This module contains wallet manager implementations that handle authentication,
key management, and delegation to underlying wallet instances.

Reference: toolbox/ts-wallet-toolbox/src/{SimpleWalletManager,CWIStyleWalletManager,WalletPermissionsManager}.ts
"""

# Phase 3 Implementation Status:
# ✅ SimpleWalletManager: 100% complete
# ✅ CWIStyleWalletManager: 100% complete
# ✅ WalletSettingsManager: 100% complete
# ⚠️ WalletPermissionsManager: 79% (38/48 methods)
#
# Phase 4 TODO:
# TODO: Phase 4 - Implement WalletPermissionsManager remaining 10 methods
# TODO: Phase 4 - Add UI callback integration for permission requests
# TODO: Phase 4 - Implement permission storage persistence
# TODO: Phase 4 - Add advanced permission grouping support
# TODO: Phase 4 - Integrate with Chaintracks layer

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
