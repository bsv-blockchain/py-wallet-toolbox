"""Unit tests for Wallet.internalize_action method.

Reference: wallet-toolbox/test/wallet/action/internalizeAction.test.ts
"""

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError


class TestWalletInternalizeAction:
    """Test suite for Wallet.internalize_action method."""

    def test_invalid_params_empty_tx(self, wallet_with_storage: Wallet) -> None:
        """Given: InternalizeActionArgs with empty tx
           When: Call internalize_action
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/action/internalizeAction.test.ts
                   test('0 invalid params')
        """
        # Given
        invalid_args = {"tx": b"", "outputs": [], "description": ""}  # Empty tx

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.internalize_action(invalid_args)

    def test_invalid_params_empty_description(self, wallet_with_storage: Wallet) -> None:
        """Given: InternalizeActionArgs with empty description
           When: Call internalize_action
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/action/internalizeAction.test.ts
                   test('0 invalid params')
        """
        # Given
        invalid_args = {
            "tx": b"\x01\x00\x00\x00",  # Non-empty tx
            "outputs": [],
            "description": "",  # Empty description
        }

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.internalize_action(invalid_args)

    def test_invalid_params_empty_outputs(self, wallet_with_storage: Wallet) -> None:
        """Given: InternalizeActionArgs with valid tx but empty outputs
           When: Call internalize_action
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/action/internalizeAction.test.ts
                   test('0 invalid params')
        """
        # Given
        invalid_args = {
            "tx": b"\x01\x00\x00\x00",  # Non-empty tx
            "outputs": [],  # Empty outputs list
            "description": "12345",
        }

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.internalize_action(invalid_args)

    @pytest.mark.skip(reason="Needs valid transaction bytes (not placeholder) and proper basket setup")
    def test_internalize_custom_output_basket_insertion(self, wallet_with_storage: Wallet) -> None:
        """Given: Valid InternalizeActionArgs with basket insertion protocol
           When: Call internalize_action
           Then: Output is added to specified basket with custom instructions and tags

        Reference: wallet-toolbox/test/wallet/action/internalizeAction.test.ts
                   test('1_internalize custom output in receiving wallet with checks')

        Note: This test requires:
        - A valid transaction (not placeholder b"...")
        - Pre-created "payments" basket in storage
        - Proper test data fixtures
        """
        # Given
        internalize_args = {
            "tx": b"...",  # Transaction bytes from createAction
            "outputs": [
                {
                    "outputIndex": 0,
                    "protocol": "basket insertion",
                    "insertionRemittance": {
                        "basket": "payments",
                        "customInstructions": '{"root": "02135476", "repeat": 8}',
                        "tags": ["test", "again"],
                    },
                }
            ],
            "description": "got paid!",
        }

        # When
        result = wallet_with_storage.internalize_action(internalize_args)

        # Then
        assert result["accepted"] is True
        # Additional checks would verify:
        # - Output is in correct basket (not default)
        # - Satoshi amount matches
        # - Custom instructions preserved
        # - Tags are correctly associated
