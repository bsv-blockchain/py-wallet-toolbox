"""WalletSettingsManager - Wallet settings and preferences management.

Manages wallet configuration including trust settings, theme, and other preferences.
Settings are stored in a dedicated "wallet settings" basket using LocalKVStore.

Reference: toolbox/ts-wallet-toolbox/src/WalletSettingsManager.ts
"""

from __future__ import annotations

import json
from typing import Any, TypedDict

from bsv_wallet_toolbox.local_kv_store import LocalKVStore


class Certifier(TypedDict, total=False):
    """Certifier information for trust settings."""

    name: str
    description: str
    identityKey: str
    trust: int
    iconUrl: str
    baseURL: str


class TrustSettings(TypedDict):
    """Trust settings configuration."""

    trustLevel: int
    trustedCertifiers: list[Certifier]


class WalletTheme(TypedDict, total=False):
    """Wallet theme configuration."""

    mode: str


class WalletSettings(TypedDict, total=False):
    """Complete wallet settings."""

    trustSettings: TrustSettings
    theme: WalletTheme
    currency: str


class WalletSettingsManagerConfig(TypedDict, total=False):
    """WalletSettingsManager configuration."""

    defaultSettings: WalletSettings


# Constants
SETTINGS_BASKET = "wallet settings"

# Default trust settings
DEFAULT_SETTINGS: WalletSettings = {
    "trustSettings": {
        "trustLevel": 2,
        "trustedCertifiers": [
            {
                "name": "Metanet Trust Services",
                "description": "Registry for protocols, baskets, and certificates types",
                "iconUrl": "https://bsvblockchain.org/favicon.ico",
                "identityKey": "03daf815fe38f83da0ad83b5bedc520aa488aef5cbc93a93c67a7fe60406cbffe8",
                "trust": 4,
            },
            {
                "name": "SocialCert",
                "description": "Certifies social media handles, phone numbers and emails",
                "iconUrl": "https://socialcert.net/favicon.ico",
                "trust": 3,
                "identityKey": "02cf6cdf466951d8dfc9e7c9367511d0007ed6fba35ed42d425cc412fd6cfd4a17",
            },
        ],
    },
    "theme": {"mode": "dark"},
}

# Testnet identity keys mapping
TESTNET_IDENTITY_KEYS = {
    "Babbage Trust Services": "03d0b36b5c98b000ec9ffed9a2cf005e279244edf6a19cf90545cdebe873162761",
    "IdentiCert": "036dc48522aba1705afbb43df3c04dbd1da373b6154341a875bceaa2a3e7f21528",
    "SocialCert": "02cf6cdf466951d8dfc9e7c9367511d0007ed6fba35ed42d425cc412fd6cfd4a17",
}

# Testnet default settings
TESTNET_DEFAULT_SETTINGS: WalletSettings = {
    "trustSettings": {
        "trustLevel": DEFAULT_SETTINGS["trustSettings"]["trustLevel"],
        "trustedCertifiers": [
            {
                **certifier,
                "identityKey": TESTNET_IDENTITY_KEYS.get(certifier["name"], certifier["identityKey"]),
            }
            for certifier in DEFAULT_SETTINGS["trustSettings"]["trustedCertifiers"]
        ],
    },
    "theme": DEFAULT_SETTINGS.get("theme", {"mode": "dark"}),
}


class WalletSettingsManager:
    """Manages wallet settings and preferences.

    Stores wallet configuration including trust settings, theme preferences,
    and other user-specific settings in a local key-value store.

    Reference: toolbox/ts-wallet-toolbox/src/WalletSettingsManager.ts
    """

    def __init__(
        self,
        wallet: Any,
        config: WalletSettingsManagerConfig | None = None,
        kv_store: LocalKVStore | None = None,
    ) -> None:
        """Initialize WalletSettingsManager.

        Args:
            wallet: The underlying WalletInterface instance
            config: Configuration with default settings

        Reference: toolbox/ts-wallet-toolbox/src/WalletSettingsManager.ts
        """
        self._wallet: Any = wallet

        # Initialize config with defaults
        if config is None:
            config = {"defaultSettings": DEFAULT_SETTINGS}
        self._config: WalletSettingsManagerConfig = config

        self._kv_store: LocalKVStore | None = kv_store or self._create_default_kv_store(wallet)
        self._settings_store: dict[str, str] = {}

    def get(self) -> WalletSettings:
        """Get user's wallet settings.

        Returns stored settings or default settings if not found.

        Returns:
            WalletSettings object with current configuration

        Reference: toolbox/ts-wallet-toolbox/src/WalletSettingsManager.ts
        """
        default_json = json.dumps(self._config.get("defaultSettings", DEFAULT_SETTINGS))

        if self._kv_store is not None:
            settings_json = self._kv_store.get_value("settings")
            if settings_json is None:
                self._kv_store.set_value("settings", default_json)
                settings_json = default_json
            return json.loads(settings_json)

        settings_json = self._settings_store.get("settings", default_json)
        return json.loads(settings_json)

    def set(self, settings: WalletSettings) -> None:
        """Store or update user's wallet settings.

        Args:
            settings: WalletSettings object to store

        Reference: toolbox/ts-wallet-toolbox/src/WalletSettingsManager.ts
        """
        serialized = json.dumps(settings)
        if self._kv_store is not None:
            self._kv_store.set_value("settings", serialized)
        else:
            self._settings_store["settings"] = serialized

    def delete(self) -> None:
        """Delete user's stored settings.

        Resets to default settings on next retrieval.

        Reference: toolbox/ts-wallet-toolbox/src/WalletSettingsManager.ts
        """
        if self._kv_store is not None:
            self._kv_store.remove_value("settings")
        else:
            self._settings_store.pop("settings", None)

    def _create_default_kv_store(self, wallet: Any) -> LocalKVStore | None:
        try:
            return LocalKVStore(wallet, SETTINGS_BASKET, True)
        except Exception:
            return None
