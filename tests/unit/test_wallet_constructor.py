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
           When: Query storage for default label and basket
           Then: Default label and basket exist

        Reference: wallet-toolbox/test/wallet/construct/Wallet.constructor.test.ts
                   test('0')

        Note: TypeScript test uses TestSetup1 which seeds test data (transactions/outputs).
              Python test verifies that constructor creates default label/basket.
        """
        # Given
        engine = create_engine_from_url("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        storage = StorageProvider(engine=engine, chain="test", storage_identity_key="test_wallet")
        root_key = PrivateKey(bytes.fromhex("2" * 64))
        key_deriver = KeyDeriver(root_key)
        
        # When - Create wallet (should auto-create defaults)
        wallet = Wallet(chain="test", storage_provider=storage, key_deriver=key_deriver)
        user_id = 1  # Default user ID

        # Then - Default label exists
        labels = storage.find_tx_labels({"userId": user_id})
        assert len(labels) > 0, "Expected at least one label to be created"
        assert any(label["label"] == "default" for label in labels), "Expected default label to exist"

        # Then - Default basket exists
        baskets = storage.find_output_baskets({"userId": user_id})
        assert len(baskets) > 0, "Expected at least one basket to be created"
        assert any(basket["name"] == "default" for basket in baskets), "Expected default basket to exist"
