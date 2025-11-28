"""Unit tests for Wallet.relinquish_output method.

Reference: wallet-toolbox/test/wallet/action/relinquishOutput.test.ts
"""

from datetime import datetime

import pytest

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
        # Given - Create the output in the database first
        output_txid = "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122"
        
        # Create transaction
        tx_id = wallet_with_storage.storage.insert_transaction({
            "userId": 1,
            "txid": output_txid,
            "status": "completed",
            "reference": "",  # Required field
            "isOutgoing": False,
            "satoshis": 1000,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        })
        
        # Find or create default basket
        default_basket = wallet_with_storage.storage.find_or_insert_output_basket(1, "default")
        
        # Create output
        wallet_with_storage.storage.insert_output({
            "transactionId": tx_id,
            "userId": 1,
            "vout": 0,
            "satoshis": 1000,
            "lockingScript": b"\x76\xa9\x14" + b"\x00" * 20 + b"\x88\xac",
            "spendable": True,
            "basketId": default_basket["basketId"],
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        })
        
        args = {"basket": "default", "output": f"{output_txid}.0"}
        expected_result = {"relinquished": True}

        # When
        result = wallet_with_storage.relinquish_output(args)

        # Then
        assert result == expected_result
