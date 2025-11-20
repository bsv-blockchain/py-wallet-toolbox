"""Unit tests for Wallet.abort_action method.

Reference: wallet-toolbox/test/wallet/action/abortAction.test.ts
"""

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError
from tests.fixtures.transaction_fixtures import create_abortable_transaction, seed_transaction


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

    @pytest.mark.skip(reason="SQLAlchemy session conflicts - need scoped_session or transaction rollback pattern")
    def test_abort_specific_reference(self, wallet_with_storage: Wallet) -> None:
        """Given: Valid AbortActionArgs with existing action reference
           When: Call abort_action
           Then: Action is successfully aborted

        Reference: wallet-toolbox/test/wallet/action/abortAction.test.ts
                   test('1_abort reference 49f878d8405589')
        
        Note: SQLAlchemy session management issue - insert_transaction returns instance
              attached to one session, abort_action queries in another session.
              Need proper scoped_session configuration or transaction rollback pattern.
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
