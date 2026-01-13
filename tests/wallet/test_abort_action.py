"""Unit tests for Wallet.abort_action method.

Reference: wallet-toolbox/test/wallet/action/abortAction.test.ts
"""

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError
from tests.fixtures.transaction_fixtures import create_abortable_transaction, seed_transaction


@pytest.fixture
def valid_abort_args():
    """Fixture providing valid abort action arguments."""
    return {"reference": "Sfh42EBViQ=="}


@pytest.fixture
def invalid_abort_args():
    """Fixture providing various invalid abort action arguments."""
    return [
        {"reference": ""},  # Empty reference
        {"reference": "===="},  # Invalid base64
        {"reference": "a" * 301},  # Too long
        {"reference": "a" * 300},  # Exactly at limit (should fail)
        {},  # Missing reference
        {"reference": None},  # None reference
        {"reference": 123},  # Wrong type
        {"reference": []},  # Wrong type
        {"reference": "invalid base64!@#$"},  # Invalid characters
        {"reference": "short"},  # Too short for valid base64
    ]


class TestWalletAbortAction:
    """Test suite for Wallet.abort_action method."""

    def test_invalid_params_empty_reference(self, wallet_with_storage: Wallet) -> None:
        """Given: AbortActionArgs with empty reference
           When: Call abort_action
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/action/abortAction.test.ts
                   test('0 invalid params')
        """
        # Given
        invalid_args = {"reference": ""}  # Empty reference

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.abort_action(invalid_args)

    def test_invalid_params_invalid_base64(self, wallet_with_storage: Wallet) -> None:
        """Given: AbortActionArgs with invalid base64 reference
           When: Call abort_action
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/action/abortAction.test.ts
                   test('0 invalid params')
        """
        # Given
        invalid_args = {"reference": "===="}  # Invalid base64

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.abort_action(invalid_args)

    def test_invalid_params_reference_too_long(self, wallet_with_storage: Wallet) -> None:
        """Given: AbortActionArgs with reference exceeding 300 characters
           When: Call abort_action
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/action/abortAction.test.ts
                   test('0 invalid params')
        """
        # Given
        invalid_args = {"reference": "a" * 301}  # Exceeds 300 character limit

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.abort_action(invalid_args)

    def test_abort_specific_reference(self, wallet_with_storage: Wallet) -> None:
        """Given: Valid AbortActionArgs with existing action reference
           When: Call abort_action
           Then: Action is successfully aborted

        Reference: wallet-toolbox/test/wallet/action/abortAction.test.ts
                   test('1_abort reference 49f878d8405589')
        """
        # Given - Seed an abortable transaction
        reference = "Sfh42EBViQ=="
        tx_data = create_abortable_transaction(
            user_id=1,
            reference=reference,
        )
        seed_transaction(wallet_with_storage.storage, tx_data)

        valid_args = {"reference": reference}

        # When
        wallet_with_storage.abort_action(valid_args)

        # Then
        # No exception raised = success

    def test_invalid_params_none_reference_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: AbortActionArgs with None reference
        When: Call abort_action
        Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"reference": None}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_storage.abort_action(invalid_args)

    def test_invalid_params_wrong_type_reference_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: AbortActionArgs with non-string reference
        When: Call abort_action
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various wrong types
        invalid_types = [123, [], {}, True, 45.67]

        for invalid_ref in invalid_types:
            invalid_args = {"reference": invalid_ref}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_storage.abort_action(invalid_args)

    def test_invalid_params_whitespace_only_reference_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: AbortActionArgs with whitespace-only reference
        When: Call abort_action
        Then: Raises InvalidParameterError
        """
        # Given - Various whitespace references
        whitespace_refs = ["   ", "\t", "\n", " \t \n "]

        for ref in whitespace_refs:
            invalid_args = {"reference": ref}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError)):
                wallet_with_storage.abort_action(invalid_args)

    def test_invalid_params_reference_with_invalid_chars_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: AbortActionArgs with reference containing invalid base64 characters
        When: Call abort_action
        Then: Raises InvalidParameterError
        """
        # Given - References with invalid base64 chars
        invalid_refs = [
            "invalid@chars!",
            "contains#symbols",
            "with$dollar$signs",
            "percent%encoded",
            "caret^here",
            "ampersand&here",
            "asterisk*here",
            "plus+but+invalid",
            "slash/invalid",
            "backslash\\invalid",
        ]

        for ref in invalid_refs:
            invalid_args = {"reference": ref}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError)):
                wallet_with_storage.abort_action(invalid_args)

    def test_invalid_params_reference_too_short_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: AbortActionArgs with very short reference
        When: Call abort_action
        Then: Raises InvalidParameterError
        """
        # Given - Very short references
        short_refs = ["a", "ab", "abc", "1", "12"]

        for ref in short_refs:
            invalid_args = {"reference": ref}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError)):
                wallet_with_storage.abort_action(invalid_args)

    def test_invalid_params_missing_reference_key_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: AbortActionArgs missing reference key
        When: Call abort_action
        Then: Raises InvalidParameterError, KeyError or TypeError
        """
        # Given
        invalid_args = {}  # Missing reference key

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError)):
            wallet_with_storage.abort_action(invalid_args)

    def test_invalid_params_extra_keys_ignored(self, wallet_with_storage: Wallet) -> None:
        """Given: AbortActionArgs with extra keys beyond reference
        When: Call abort_action
        Then: Extra keys are ignored, processes normally or fails on reference
        """
        # Given - Extra keys that should be ignored
        invalid_args = {
            "reference": "",  # Invalid reference
            "extraKey": "ignored",
            "anotherKey": 123,
            "nested": {"key": "value"},
        }

        # When/Then - Should fail on the invalid reference, not the extra keys
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.abort_action(invalid_args)

    def test_abort_nonexistent_reference_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: Valid format reference that doesn't exist
        When: Call abort_action
        Then: Raises appropriate error (transaction not found)
        """
        # Given - Valid base64 format but nonexistent reference
        nonexistent_ref = "nonexistent123"
        valid_format_args = {"reference": nonexistent_ref}

        # When/Then - Should raise error for nonexistent transaction
        # The exact error type depends on implementation
        with pytest.raises((InvalidParameterError, ValueError, RuntimeError)):
            wallet_with_storage.abort_action(valid_format_args)

    def test_abort_already_aborted_reference_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: Reference that was already aborted
        When: Call abort_action again
        Then: Raises appropriate error
        """
        # Given - First abort succeeds
        reference = "Sfh42EBViQ=="
        tx_data = create_abortable_transaction(user_id=1, reference=reference)
        seed_transaction(wallet_with_storage.storage, tx_data)

        valid_args = {"reference": reference}

        # First abort succeeds
        wallet_with_storage.abort_action(valid_args)

        # When/Then - Second abort should fail
        with pytest.raises((InvalidParameterError, ValueError, RuntimeError)):
            wallet_with_storage.abort_action(valid_args)
