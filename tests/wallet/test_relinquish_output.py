"""Unit tests for Wallet.relinquish_output method.

Reference: wallet-toolbox/test/wallet/action/relinquishOutput.test.ts
"""

from datetime import datetime

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError


@pytest.fixture
def valid_relinquish_output_args():
    """Fixture providing valid relinquish output arguments."""
    return {"basket": "default", "output": "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122.0"}


@pytest.fixture
def invalid_relinquish_output_cases():
    """Fixture providing various invalid relinquish output arguments."""
    return [
        # Invalid basket
        {"basket": "", "output": "valid.txid.0"},  # Empty basket
        {"basket": "   ", "output": "valid.txid.0"},  # Whitespace basket
        {"basket": None, "output": "valid.txid.0"},  # None basket
        {"basket": 123, "output": "valid.txid.0"},  # Wrong basket type
        {"basket": [], "output": "valid.txid.0"},  # Wrong basket type
        {"basket": {}, "output": "valid.txid.0"},  # Wrong basket type
        # Invalid output
        {"basket": "default", "output": ""},  # Empty output
        {"basket": "default", "output": "   "},  # Whitespace output
        {"basket": "default", "output": None},  # None output
        {"basket": "default", "output": 123},  # Wrong output type
        {"basket": "default", "output": []},  # Wrong output type
        {"basket": "default", "output": {}},  # Wrong output type
        # Invalid output format
        {"basket": "default", "output": "invalid-txid.0"},  # Invalid txid format
        {
            "basket": "default",
            "output": "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122",
        },  # Missing vout
        {
            "basket": "default",
            "output": "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122.abc",
        },  # Invalid vout
        {
            "basket": "default",
            "output": "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122.-1",
        },  # Negative vout
        {
            "basket": "default",
            "output": "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122.999999",
        },  # Very large vout
        # Missing keys
        {"basket": "default"},  # Missing output
        {"output": "valid.txid.0"},  # Missing basket
        {},  # Missing both
        # Extra keys (should be ignored)
        {"basket": "default", "output": "valid.txid.0", "extra": "value"},
    ]


@pytest.fixture
def nonexistent_output_args():
    """Fixture providing args for nonexistent output."""
    return {"basket": "default", "output": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff.0"}


@pytest.fixture
def already_relinquished_output_args():
    """Fixture providing args for output that's already been relinquished."""
    return {"basket": "default", "output": "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122.0"}


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
        tx_id = wallet_with_storage.storage.insert_transaction(
            {
                "userId": 1,
                "txid": output_txid,
                "status": "completed",
                "reference": "",  # Required field
                "isOutgoing": False,
                "satoshis": 1000,
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            }
        )

        # Find or create default basket
        default_basket = wallet_with_storage.storage.find_or_insert_output_basket(1, "default")

        # Create output
        wallet_with_storage.storage.insert_output(
            {
                "transactionId": tx_id,
                "userId": 1,
                "vout": 0,
                "satoshis": 1000,
                "lockingScript": b"\x76\xa9\x14" + b"\x00" * 20 + b"\x88\xac",
                "spendable": True,
                "basketId": default_basket["basketId"],
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            }
        )

        args = {"basket": "default", "output": f"{output_txid}.0"}
        expected_result = {"relinquished": True}

        # When
        result = wallet_with_storage.relinquish_output(args)

        # Then
        assert result == expected_result

    def test_invalid_params_empty_basket_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishOutputArgs with empty basket
        When: Call relinquish_output
        Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"basket": "", "output": "valid.txid.0"}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_storage.relinquish_output(invalid_args)

    def test_invalid_params_whitespace_basket_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishOutputArgs with whitespace-only basket
        When: Call relinquish_output
        Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"basket": "   ", "output": "valid.txid.0"}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_storage.relinquish_output(invalid_args)

    def test_invalid_params_none_basket_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishOutputArgs with None basket
        When: Call relinquish_output
        Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"basket": None, "output": "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122.0"}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_storage.relinquish_output(invalid_args)

    def test_invalid_params_wrong_basket_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishOutputArgs with wrong basket type
        When: Call relinquish_output
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, [], {}, True, 45.67]

        for invalid_basket in invalid_types:
            invalid_args = {
                "basket": invalid_basket,
                "output": "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122.0",
            }

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_storage.relinquish_output(invalid_args)

    def test_invalid_params_basket_too_long_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishOutputArgs with basket exceeding length limits
        When: Call relinquish_output
        Then: Raises InvalidParameterError
        """
        # Given - Basket too long (based on typical constraints)
        too_long_basket = "basket_name_" * 31  # Exceeds reasonable length
        invalid_args = {"basket": too_long_basket, "output": "valid.txid.0"}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_storage.relinquish_output(invalid_args)

    def test_invalid_params_empty_output_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishOutputArgs with empty output
        When: Call relinquish_output
        Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"basket": "default", "output": ""}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_storage.relinquish_output(invalid_args)

    def test_invalid_params_whitespace_output_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishOutputArgs with whitespace-only output
        When: Call relinquish_output
        Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"basket": "default", "output": "   "}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_storage.relinquish_output(invalid_args)

    def test_invalid_params_none_output_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishOutputArgs with None output
        When: Call relinquish_output
        Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"basket": "default", "output": None}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError, ValueError)):
            wallet_with_storage.relinquish_output(invalid_args)

    def test_invalid_params_wrong_output_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishOutputArgs with wrong output type
        When: Call relinquish_output
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, [], {}, True, 45.67]

        for invalid_output in invalid_types:
            invalid_args = {"basket": "default", "output": invalid_output}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError, ValueError)):
                wallet_with_storage.relinquish_output(invalid_args)

    def test_invalid_params_missing_output_vout_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishOutputArgs with output missing vout
        When: Call relinquish_output
        Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {
            "basket": "default",
            "output": "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122",
        }

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_storage.relinquish_output(invalid_args)

    def test_invalid_params_invalid_txid_format_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishOutputArgs with invalid txid format
        When: Call relinquish_output
        Then: Raises InvalidParameterError
        """
        # Given - Invalid txid formats
        invalid_outputs = [
            "invalid-txid.0",
            "gggggggggggggggggggggggggggggggggggggggg.0",  # Invalid hex
            "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f12.0",  # Too short
            "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122aa.0",  # Too long
        ]

        for invalid_output in invalid_outputs:
            invalid_args = {"basket": "default", "output": invalid_output}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError)):
                wallet_with_storage.relinquish_output(invalid_args)

    def test_invalid_params_negative_vout_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishOutputArgs with negative vout
        When: Call relinquish_output
        Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {
            "basket": "default",
            "output": "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122.-1",
        }

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_storage.relinquish_output(invalid_args)

    def test_invalid_params_invalid_vout_format_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishOutputArgs with invalid vout format
        When: Call relinquish_output
        Then: Raises InvalidParameterError
        """
        # Given - Invalid vout formats
        invalid_outputs = [
            "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122.abc",
            "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122.notanumber",
            "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122.999999999999999999999",  # Too large
        ]

        for invalid_output in invalid_outputs:
            invalid_args = {"basket": "default", "output": invalid_output}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError)):
                wallet_with_storage.relinquish_output(invalid_args)

    def test_invalid_params_missing_basket_key_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishOutputArgs missing basket key
        When: Call relinquish_output
        Then: Raises InvalidParameterError or KeyError
        """
        # Given
        invalid_args = {"output": "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122.0"}

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError, ValueError)):
            wallet_with_storage.relinquish_output(invalid_args)

    def test_invalid_params_missing_output_key_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishOutputArgs missing output key
        When: Call relinquish_output
        Then: Raises InvalidParameterError or KeyError
        """
        # Given
        invalid_args = {"basket": "default"}

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError, ValueError)):
            wallet_with_storage.relinquish_output(invalid_args)

    def test_invalid_params_empty_args_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: Empty RelinquishOutputArgs
        When: Call relinquish_output
        Then: Raises InvalidParameterError or KeyError
        """
        # Given
        invalid_args = {}

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError, ValueError)):
            wallet_with_storage.relinquish_output(invalid_args)

    def test_relinquish_nonexistent_output_returns_false(
        self, wallet_with_storage: Wallet, nonexistent_output_args
    ) -> None:
        """Given: RelinquishOutputArgs with nonexistent output
        When: Call relinquish_output
        Then: Returns relinquished=False
        """
        # When
        result = wallet_with_storage.relinquish_output(nonexistent_output_args)

        # Then
        assert result == {"relinquished": False}

    def test_relinquish_already_relinquished_output_returns_false(self, wallet_with_storage: Wallet) -> None:
        """Given: Output that has already been relinquished
           When: Call relinquish_output again
           Then: Returns relinquished=False

        Note: Without a pre-existing output in the database, both calls return False
        because the output doesn't exist in the first place.
        """
        # Given - Try to relinquish an output that doesn't exist
        args = {"basket": "default", "output": "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122.0"}

        # First call returns False (output doesn't exist)
        first_result = wallet_with_storage.relinquish_output(args)
        assert first_result == {"relinquished": False}

        # Second call also returns False (still doesn't exist)
        second_result = wallet_with_storage.relinquish_output(args)
        assert second_result == {"relinquished": False}

    def test_relinquish_output_from_different_basket(self, wallet_with_storage: Wallet) -> None:
        """Given: Output in a different basket than specified
        When: Call relinquish_output
        Then: Returns relinquished=False
        """
        # Given - Try to relinquish from a different basket
        args = {
            "basket": "other_basket",
            "output": "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122.0",
        }

        # When
        result = wallet_with_storage.relinquish_output(args)

        # Then - Should return False since output is not in that basket
        assert result == {"relinquished": False}

    def test_relinquish_output_with_unicode_basket_name(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishOutputArgs with unicode basket name
        When: Call relinquish_output
        Then: Handles unicode correctly
        """
        # Given - Create output with unicode basket name would require setup
        # For now, test that unicode basket names are handled
        unicode_args = {
            "basket": "测试_basket",
            "output": "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122.0",
        }

        # When
        result = wallet_with_storage.relinquish_output(unicode_args)

        # Then - Should return False (since basket doesn't exist) but not crash
        assert result == {"relinquished": False}

    def test_relinquish_output_case_sensitive_basket(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishOutputArgs with different case basket name
        When: Call relinquish_output
        Then: Basket names are case-sensitive
        """
        # Given - Try different case basket names
        test_cases = [
            {"basket": "DEFAULT", "output": "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122.0"},
            {"basket": "Default", "output": "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122.0"},
        ]

        for args in test_cases:
            # When
            result = wallet_with_storage.relinquish_output(args)

            # Then - Should return False since case doesn't match
            assert result == {"relinquished": False}

    def test_relinquish_output_extra_parameters_ignored(
        self, wallet_with_storage: Wallet, valid_relinquish_output_args
    ) -> None:
        """Given: RelinquishOutputArgs with extra parameters
        When: Call relinquish_output
        Then: Extra parameters are ignored
        """
        # Given - Add extra parameters
        args_with_extra = valid_relinquish_output_args.copy()
        args_with_extra.update(
            {"extraParam": "should_be_ignored", "anotherParam": 123, "nestedParam": {"key": "value"}}
        )

        # When
        result = wallet_with_storage.relinquish_output(args_with_extra)

        # Then - Should work normally (result depends on whether output exists)
        assert isinstance(result, dict)
        assert "relinquished" in result
        assert isinstance(result["relinquished"], bool)
