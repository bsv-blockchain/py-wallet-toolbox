"""Chaintracks configuration options.

Provides factory functions for creating Chaintracks configurations.

Reference: wallet-toolbox/src/services/chaintracker/chaintracks/options.ts
"""

from typing import Any


def create_default_no_db_chaintracks_options(chain: str = "main") -> dict[str, Any]:
    """Create default Chaintracks options without database storage.

    Args:
        chain: The blockchain network ("main" or "test")

    Returns:
        Configuration dictionary for Chaintracks

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/options.ts
               createDefaultNoDbChaintracksOptions()
    """
    return {
        "chain": chain,
        "useStorage": False,
        "storageEngine": None,
        "network": "mainnet" if chain == "main" else "testnet",
        "maxCachedHeaders": 10000,
        "useRemoteHeaders": True,
    }


def create_default_chaintracks_options(chain: str = "main", storage_path: str | None = None) -> dict[str, Any]:
    """Create default Chaintracks options with database storage.

    Args:
        chain: The blockchain network ("main" or "test")
        storage_path: Optional path to database file

    Returns:
        Configuration dictionary for Chaintracks

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/options.ts
               createDefaultChaintracksOptions()
    """
    return {
        "chain": chain,
        "useStorage": True,
        "storagePath": storage_path or f"./chaintracks_{chain}.db",
        "network": "mainnet" if chain == "main" else "testnet",
        "maxCachedHeaders": 10000,
        "useRemoteHeaders": True,
    }
