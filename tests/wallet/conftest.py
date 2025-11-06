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
