"""Unit tests for Wallet.abort_action method.

Reference: wallet-toolbox/test/wallet/action/abortAction.test.ts
"""

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError


class TestWalletAbortAction:
    """Test suite for Wallet.abort_action method."""

    @pytest.mark.skip(reason="Waiting for abort_action implementation")
    def test_invalid_params_empty_reference(self, wallet: Wallet) -> None:
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
            wallet.abort_action(invalid_args)

    @pytest.mark.skip(reason="Waiting for abort_action implementation")
    def test_invalid_params_invalid_base64(self, wallet: Wallet) -> None:
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
            wallet.abort_action(invalid_args)

    @pytest.mark.skip(reason="Waiting for abort_action implementation")
    def test_invalid_params_reference_too_long(self, wallet: Wallet) -> None:
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
            wallet.abort_action(invalid_args)

    @pytest.mark.skip(reason="Waiting for abort_action implementation with test database")
    def test_abort_specific_reference(self, wallet: Wallet) -> None:
        """Given: Valid AbortActionArgs with existing action reference
           When: Call abort_action
           Then: Action is successfully aborted

        Reference: wallet-toolbox/test/wallet/action/abortAction.test.ts
                   test('1_abort reference 49f878d8405589')

        Note: This test requires a populated test database with the specific action.
        """
        # Given
        valid_args = {"reference": "Sfh42EBViQ=="}  # Base64 reference from test data

        # When
        wallet.abort_action(valid_args)

        # Then
        # No exception raised = success
