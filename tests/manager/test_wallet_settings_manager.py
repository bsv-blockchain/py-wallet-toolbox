import json

from bsv_wallet_toolbox.manager.wallet_settings_manager import (
    DEFAULT_SETTINGS,
    WalletSettings,
    WalletSettingsManager,
)


class FakeKVStore:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def get_value(self, key: str) -> str | None:
        return self._store.get(key)

    def set_value(self, key: str, value: str) -> None:
        self._store[key] = value

    def remove_value(self, key: str) -> None:
        self._store.pop(key, None)


def test_get_writes_default_settings_when_absent() -> None:
    kv_store = FakeKVStore()
    manager = WalletSettingsManager(wallet=None, kv_store=kv_store)  # type: ignore[arg-type]

    settings = manager.get()

    assert settings == DEFAULT_SETTINGS
    assert json.loads(kv_store._store["settings"]) == DEFAULT_SETTINGS  # type: ignore[attr-defined]


def test_set_updates_underlying_kv_store() -> None:
    kv_store = FakeKVStore()
    manager = WalletSettingsManager(wallet=None, kv_store=kv_store)  # type: ignore[arg-type]

    new_settings: WalletSettings = {
        "trustSettings": {
            "trustLevel": 1,
            "trustedCertifiers": [],
        },
        "theme": {"mode": "light"},
    }

    manager.set(new_settings)

    assert json.loads(kv_store._store["settings"]) == new_settings  # type: ignore[attr-defined]


def test_delete_removes_persisted_settings() -> None:
    kv_store = FakeKVStore()
    manager = WalletSettingsManager(wallet=None, kv_store=kv_store)  # type: ignore[arg-type]

    manager.set(DEFAULT_SETTINGS)
    manager.delete()

    assert "settings" not in kv_store._store  # type: ignore[attr-defined]
    assert manager.get() == DEFAULT_SETTINGS
