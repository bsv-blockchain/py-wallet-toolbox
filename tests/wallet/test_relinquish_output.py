"""Unit tests for Wallet.relinquish_output method.

Reference: wallet-toolbox/test/wallet/action/relinquishOutput.test.ts
"""

from bsv_wallet_toolbox import Wallet


class TestWalletRelinquishOutput:
    """Test suite for Wallet.relinquish_output method."""

    def test_relinquish_specific_output(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishOutputArgs with existing output
           When: Call relinquish_output
           Then: Returns relinquished=True

        Reference: wallet-toolbox/test/wallet/action/relinquishOutput.test.ts
                   test('1_default')

        Note: This test requires a populated test database with the specific output.
        """
        # Given
        output_txid = "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122"
        args = {"basket": "default", "output": f"{output_txid}.0"}
        expected_result = {"relinquished": True}

        # When
        result = wallet_with_storage.relinquish_output(args)

        # Then
        assert result == expected_result
