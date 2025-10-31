"""Unit tests for Wallet.list_outputs method.

Reference: wallet-toolbox/test/wallet/list/listOutputs.test.ts
"""

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError


class TestWalletListOutputs:
    """Test suite for Wallet.list_outputs method."""

    @pytest.mark.skip(reason="Waiting for list_outputs implementation")
    def test_invalid_params_empty_basket(self, wallet: Wallet) -> None:
        """Given: ListOutputsArgs with empty basket
           When: Call list_outputs
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/list/listOutputs.test.ts
                   test('0 invalid params with originator')
        """
        # Given
        invalid_args = {"basket": "", "tags": []}  # Empty basket

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet.list_outputs(invalid_args)

    @pytest.mark.skip(reason="Waiting for list_outputs implementation")
    def test_invalid_params_empty_tag(self, wallet: Wallet) -> None:
        """Given: ListOutputsArgs with empty tag in tags list
           When: Call list_outputs
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/list/listOutputs.test.ts
                   test('0 invalid params with originator')
        """
        # Given
        invalid_args = {"basket": "default", "tags": [""]}  # Empty tag

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet.list_outputs(invalid_args)

    @pytest.mark.skip(reason="Waiting for list_outputs implementation")
    def test_invalid_params_limit_zero(self, wallet: Wallet) -> None:
        """Given: ListOutputsArgs with limit=0
           When: Call list_outputs
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/list/listOutputs.test.ts
                   test('0 invalid params with originator')
        """
        # Given
        invalid_args = {"basket": "default", "limit": 0}  # Zero limit

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet.list_outputs(invalid_args)

    @pytest.mark.skip(reason="Waiting for list_outputs implementation")
    def test_invalid_params_limit_exceeds_max(self, wallet: Wallet) -> None:
        """Given: ListOutputsArgs with limit exceeding 10000
           When: Call list_outputs
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/list/listOutputs.test.ts
                   test('0 invalid params with originator')
        """
        # Given
        invalid_args = {"basket": "default", "limit": 10001}  # Exceeds maximum

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet.list_outputs(invalid_args)

    @pytest.mark.skip(reason="Waiting for list_outputs implementation")
    def test_invalid_params_negative_offset(self, wallet: Wallet) -> None:
        """Given: ListOutputsArgs with negative offset
           When: Call list_outputs
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/list/listOutputs.test.ts
                   test('0 invalid params with originator')
        """
        # Given
        invalid_args = {"basket": "default", "offset": -1}  # Negative offset

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet.list_outputs(invalid_args)

    @pytest.mark.skip(reason="Waiting for list_outputs implementation")
    def test_invalid_originator_too_long(self, wallet: Wallet) -> None:
        """Given: Valid args but originator exceeding 250 characters
           When: Call list_outputs
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/list/listOutputs.test.ts
                   test('0 invalid params with originator')
        """
        # Given
        valid_args = {"basket": "default", "tags": []}
        too_long_originator = "too.long.invalid.domain." * 20  # Exceeds 250 chars

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet.list_outputs(valid_args, originator=too_long_originator)

    @pytest.mark.skip(reason="Waiting for list_outputs implementation with test database")
    def test_valid_params_with_originator(self, wallet: Wallet) -> None:
        """Given: Valid ListOutputsArgs and valid originator
           When: Call list_outputs
           Then: Returns output list successfully

        Reference: wallet-toolbox/test/wallet/list/listOutputs.test.ts
                   test('1 valid params with originator')

        Note: This test requires a populated test database.
        """
        # Given
        valid_args = {
            "basket": "default",
            "tags": ["tag1", "tag2"],
            "limit": 10,
            "offset": 0,
            "tagQueryMode": "any",
            "include": "locking scripts",
            "includeCustomInstructions": False,
            "includeTags": True,
            "includeLabels": True,
            "seekPermission": True,
        }
        valid_originators = ["example.com", "localhost", "subdomain.example.com"]

        # When / Then
        for originator in valid_originators:
            result = wallet.list_outputs(valid_args, originator=originator)
            assert "totalOutputs" in result
            assert result["totalOutputs"] >= 0
