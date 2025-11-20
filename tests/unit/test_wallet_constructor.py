"""Unit tests for Wallet constructor.

This module tests wallet initialization and basic functionality.

Reference: wallet-toolbox/test/wallet/construct/Wallet.constructor.test.ts
"""

import pytest

try:
    from bsv.keys import PrivateKey
    from bsv.wallet import KeyDeriver
    from bsv_wallet_toolbox.storage import StorageProvider
    from bsv_wallet_toolbox.storage.db import create_engine_from_url
    from bsv_wallet_toolbox.storage.models import Base
    from bsv_wallet_toolbox.wallet import Wallet

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    StorageProvider = None
    Wallet = None
    KeyDeriver = None
    PrivateKey = None


class TestWalletConstructor:
    """Test suite for Wallet constructor.

    Reference: wallet-toolbox/test/wallet/construct/Wallet.constructor.test.ts
                describe('Wallet constructor tests')
    """

    def test_constructor_creates_wallet_with_default_labels_and_baskets(self) -> None:
        """Given: Wallet initialized with storage
           When: List actions by default label and list outputs by default basket
           Then: Returns 1 action and 1 output respectively

        Reference: wallet-toolbox/test/wallet/construct/Wallet.constructor.test.ts
                   test('0')

        Note: TypeScript initializes wallet with MySQL/SQLite storage and verifies
              that default labels and baskets are created.
        """
        # Given
        engine = create_engine_from_url("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        storage = StorageProvider(engine=engine, chain="test", storage_identity_key="test_wallet")
        root_key = PrivateKey(bytes.fromhex("2" * 64))
        key_deriver = KeyDeriver(root_key)
        wallet = Wallet(chain="test", storage_provider=storage, key_deriver=key_deriver)
        user_id = 1  # Default user ID

        # When - Find default label and list actions
        labels = storage.find_tx_labels({"partial": {"user_id": user_id}})
        label = labels[0]["label"]
        r_actions = wallet.list_actions({"labels": [label]}, originator=None)

        # Then
        assert r_actions["totalActions"] == 1

        # When - Find default basket and list outputs
        baskets = storage.find_output_baskets({"partial": {"user_id": user_id}})
        basket = baskets[0]["name"]
        r_outputs = wallet.list_outputs({"basket": basket}, originator=None)

        # Then
        assert r_outputs["totalOutputs"] == 1
