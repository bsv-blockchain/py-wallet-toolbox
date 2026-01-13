"""Unit tests for Wallet.get_known_txids method.

Ported from TypeScript implementation to ensure compatibility.

Reference: wallet-toolbox/test/Wallet/get/getKnownTxids.test.ts

Note: All tests are currently skipped as the get_known_txids API is not yet implemented.
"""

from bsv_wallet_toolbox import Wallet


class TestGetKnownTxids:
    """Test suite for Wallet.get_known_txids method.

    Reference: wallet-toolbox/test/Wallet/get/getKnownTxids.test.ts
               getKnownTxids Tests
    """

    def test_returns_empty_array_when_no_txids_provided(self, test_key_deriver) -> None:
        """Given: Wallet with no txids registered
           When: Call get_known_txids with no arguments
           Then: Returns empty list

        Reference: wallet-toolbox/test/Wallet/get/getKnownTxids.test.ts
                   test('0 should return an empty array when no txids are provided')
        """
        # Given
        wallet = Wallet(chain="test", key_deriver=test_key_deriver)

        # When
        result = wallet.get_known_txids()

        # Then
        assert result == []

    def test_adds_new_known_txids(self, test_key_deriver) -> None:
        """Given: Wallet with no txids registered
           When: Add txids and retrieve them
           Then: Returns the added txids

        Reference: wallet-toolbox/test/Wallet/get/getKnownTxids.test.ts
                   test('1 should add new known txids')
        """
        # Given
        wallet = Wallet(chain="test", key_deriver=test_key_deriver)
        # Force fallback to _known_txids by disabling beef
        wallet.beef = None
        txids = ["txid1"]

        # When
        result_before = wallet.get_known_txids()
        assert result_before == []

        wallet.get_known_txids(txids)
        result_after = wallet.get_known_txids()

        # Then
        assert result_after == txids

    def test_avoids_duplicating_txids(self, test_key_deriver) -> None:
        """Given: Wallet with some txids already registered
           When: Add a duplicate txid
           Then: Txid list remains unique (no duplicates)

        Reference: wallet-toolbox/test/Wallet/get/getKnownTxids.test.ts
                   test('2 should avoid duplicating txids')

        Note: TypeScript comment indicates "Duplicate txids are not being handled correctly"
              Python implementation should handle this correctly.
        """
        # Given
        wallet = Wallet(chain="test", key_deriver=test_key_deriver)
        # Force fallback to _known_txids by disabling beef
        wallet.beef = None
        txids = ["txid1", "txid2"]
        wallet.get_known_txids(txids)

        result_before = wallet.get_known_txids()
        assert result_before == txids

        # When - Add duplicate txid
        wallet.get_known_txids(["txid2"])
        result_after = wallet.get_known_txids()

        # Then - Ensure no duplicates are added
        assert result_after == txids

    def test_returns_sorted_txids(self, test_key_deriver) -> None:
        """Given: Wallet with unsorted txids added
           When: Retrieve known txids
           Then: Returns txids in sorted order

        Reference: wallet-toolbox/test/Wallet/get/getKnownTxids.test.ts
                   test('3 should return sorted txids')

        Note: TypeScript comment indicates "Duplicate txids are not being handled correctly"
              but sorting is expected to work.
        """
        # Given
        wallet = Wallet(chain="test", key_deriver=test_key_deriver)
        # Force fallback to _known_txids by disabling beef
        wallet.beef = None
        unsorted_txids = ["txid3", "txid1", "txid2"]
        wallet.get_known_txids(unsorted_txids)

        # When
        result = wallet.get_known_txids()

        # Then - Ensure txids are sorted
        assert result == ["txid1", "txid2", "txid3"]

    def test_handles_invalid_txids_gracefully(self, test_key_deriver) -> None:
        """Given: Mix of valid and invalid txids
           When: Add them to wallet
           Then: All txids are stored (validation is permissive)

        Reference: wallet-toolbox/test/Wallet/get/getKnownTxids.test.ts
                   test('4 should handle invalid txids gracefully')

        Note: TypeScript allows invalid txids to be stored.
              Python implementation should follow the same permissive behavior.
        """
        # Given
        wallet = Wallet(chain="test", key_deriver=test_key_deriver)
        # Force fallback to _known_txids by disabling beef
        wallet.beef = None
        invalid_txids = ["invalid_txid"]
        valid_txids = ["txid1", "txid2", "txid3"]
        input_txids = valid_txids + invalid_txids

        # When - Call the method with both valid and invalid txids
        result = wallet.get_known_txids(input_txids)

        # Then - Validate the result includes all txids
        assert isinstance(result, list)
        assert set(result) == set(input_txids)
