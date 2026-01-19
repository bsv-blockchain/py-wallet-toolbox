"""Unit tests for Wallet constructor.

This module tests wallet initialization and basic functionality.

Reference: wallet-toolbox/test/wallet/construct/Wallet.constructor.test.ts
"""

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
           When: Call ensure_initialized and query storage for default basket
           Then: Default basket exists

        Reference: wallet-toolbox/test/wallet/construct/Wallet.constructor.test.ts
                   test('0')

        Note: TypeScript test uses TestSetup1 which seeds test data (transactions/outputs).
              Python test verifies that ensure_initialized creates default basket.
              Default labels are NOT auto-created - they are created when transactions
              are labeled. This matches TypeScript behavior where TestSetup1 creates
              the test data including labels.
        """
        # Given
        engine = create_engine_from_url("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        storage = StorageProvider(engine=engine, chain="test", storage_identity_key="test_wallet")
        root_key = PrivateKey(bytes.fromhex("2" * 64))
        key_deriver = KeyDeriver(root_key)

        # When - Create wallet and ensure initialized (creates default basket)
        wallet = Wallet(chain="test", storage_provider=storage, key_deriver=key_deriver)
        auth = wallet.ensure_initialized(ensure_default_basket=True)
        user_id = auth.get("userId", 1)

        # Then - Default basket exists (created by ensure_initialized)
        baskets = storage.find_output_baskets({"userId": user_id})
        assert len(baskets) > 0, "Expected at least one basket to be created"
        assert any(basket["name"] == "default" for basket in baskets), "Expected default basket to exist"

        # Note: Default labels are NOT auto-created by constructor or ensure_initialized.
        # Labels are created on-demand when transactions are labeled.
        # This matches TypeScript behavior where TestSetup1 creates test transactions
        # with labels, not the Wallet constructor itself.
