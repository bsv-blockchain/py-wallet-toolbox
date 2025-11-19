"""Unit tests for Wallet constructor.

This module tests wallet initialization and basic functionality.

Reference: wallet-toolbox/test/wallet/construct/Wallet.constructor.test.ts
"""

import pytest

try:
    from bsv_wallet_toolbox.storage import WalletStorageManager
    from bsv_wallet_toolbox.wallet import Wallet

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class TestWalletConstructor:
    """Test suite for Wallet constructor.

    Reference: wallet-toolbox/test/wallet/construct/Wallet.constructor.test.ts
                describe('Wallet constructor tests')
    """

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for Wallet implementation")
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
        storage = WalletStorageManager(chain="test")
        wallet = Wallet(chain="test", storage=storage, root_key_hex="2" * 64)
        user_id = 1  # Default user ID

        # When - Find default label and list actions
        labels = storage.find_tx_labels({"partial": {"user_id": user_id}})
        label = labels[0]["label"]
        r_actions = wallet.list_actions({"labels": [label]})

        # Then
        assert r_actions["totalActions"] == 1

        # When - Find default basket and list outputs
        baskets = storage.find_output_baskets({"partial": {"user_id": user_id}})
        basket = baskets[0]["name"]
        r_outputs = wallet.list_outputs({"basket": basket})

        # Then
        assert r_outputs["totalOutputs"] == 1
