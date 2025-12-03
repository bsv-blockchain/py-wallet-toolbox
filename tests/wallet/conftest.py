from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.storage.db import create_engine_from_url
from bsv_wallet_toolbox.storage.models import Base
from bsv_wallet_toolbox.storage.provider import StorageProvider


@pytest.fixture
def wallet_with_mocked_create_action(test_key_deriver) -> tuple[Wallet, StorageProvider, dict[str, Any], int]:
    """Wallet fixture that records create_action invocations.

    The underlying storage provider's ``create_action`` method is monkeypatched
    to capture invocation details and return deterministic results for both
    ``signAndProcess`` and ``signable`` flows.  This enables tests to focus on
    Wallet-level argument handling without depending on the (still evolving)
    storage pipeline implementation.
    """

    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    storage = StorageProvider(engine=engine, chain="main", storage_identity_key="wallet-create-action")
    storage.make_available()

    wallet = Wallet(chain="main", key_deriver=test_key_deriver, storage_provider=storage)

    # Ensure a user record exists so auth userId is stable across calls.
    seed_auth = wallet._make_auth()
    seed_user_id = seed_auth["userId"]

    call_log: dict[str, Any] = {}

    def stub_create_action(auth: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
        call_log.clear()
        call_log["auth"] = auth
        call_log["args"] = args

        outputs = args.get("outputs", [])
        first_output = outputs[0] if outputs else {"satoshis": 0}

        if args.get("options", {}).get("signAndProcess"):
            return {
                "txid": "mock-deterministic-txid",
                "reference": "ref-123",
                "version": 2,
                "lockTime": 0,
                "inputs": [
                    {
                        "vin": 0,
                        "sourceTxid": "aa" * 32,
                        "sourceVout": 0,
                        "sourceSatoshis": 5000,
                        "sourceLockingScript": "51",
                        "unlockingScriptLength": 107,
                        "providedBy": "you",
                        "type": "custom",
                    }
                ],
                "outputs": [
                    {
                        "vout": 0,
                        "satoshis": first_output.get("satoshis", 0),
                        "providedBy": "you",
                        "purpose": "payment",
                        "tags": [],
                    }
                ],
                "derivationPrefix": "m/44'",
                "inputBeef": [0x00],
                "noSendChangeOutputVouts": [1, 2],
            }

        return {
            "reference": "ref-456",
            "version": 2,
            "lockTime": 0,
            "inputs": [],
            "outputs": [],
            "derivationPrefix": "m/44'",
            "inputBeef": [],
            "signableTransaction": {
                "reference": "ref-456",
                "tx": [0xDE, 0xAD],
            },
            "noSendChange": ["mock.txid.0"],
        }

    storage.create_action = MagicMock(side_effect=stub_create_action)

    return wallet, storage, call_log, seed_user_id


@pytest.fixture
def _wallet(test_key_deriver) -> Wallet:
    """Wallet fixture with populated data for sync tests.

    Creates a wallet with storage provider and some seeded data for testing
    sync operations.
    """
    # Create in-memory SQLite database
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    # Create storage provider
    storage = StorageProvider(engine=engine, chain="main", storage_identity_key="sync-test-wallet")
    storage.make_available()

    # Create wallet with storage
    wallet = Wallet(chain="main", key_deriver=test_key_deriver, storage_provider=storage)

    # Seed some data (similar to wallet_with_services but minimal)
    from datetime import datetime, timezone
    try:
        user_id = storage.insert_user({
            "identityKey": test_key_deriver._root_private_key.public_key().hex(),
            "activeStorage": "test",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })
    except Exception:
        # User might already exist, get the existing user
        user_id = storage.get_or_create_user_id(test_key_deriver._root_private_key.public_key().hex())

    # Create default basket
    try:
        storage.insert_output_basket({
            "userId": user_id,
            "name": "default",
            "numberOfDesiredUTXOs": 10,
            "minimumDesiredUTXOValue": 1000,
            "isDeleted": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })
    except Exception:
        # Basket might already exist
        pass

    return wallet


@pytest.fixture
def destination_storage() -> StorageProvider:
    """Empty destination storage for sync_to_writer tests."""
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    storage = StorageProvider(engine=engine, chain="main", storage_identity_key="destination-storage")
    storage.make_available()

    return storage


@pytest.fixture
def backup_storage() -> StorageProvider:
    """Empty backup storage for set_active tests."""
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    storage = StorageProvider(engine=engine, chain="main", storage_identity_key="backup-storage")
    storage.make_available()

    return storage


@pytest.fixture
def original_storage() -> StorageProvider:
    """Original storage with data for set_active tests."""
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    storage = StorageProvider(engine=engine, chain="main", storage_identity_key="original-storage")
    storage.make_available()

    # For set_active tests, we need a wallet with storage that has data
    # The test will set this as the active storage
    return storage
