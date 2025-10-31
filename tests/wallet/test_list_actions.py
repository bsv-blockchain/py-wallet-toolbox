"""Unit tests for Wallet.list_actions method.

Reference: wallet-toolbox/test/wallet/list/listActions.test.ts
"""

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError


class TestWalletListActions:
    """Test suite for Wallet.list_actions method."""

    @pytest.mark.skip(reason="Waiting for list_actions implementation")
    def test_invalid_params_label_too_long(self, wallet: Wallet) -> None:
        """Given: ListActionsArgs with label exceeding 300 characters
           When: Call list_actions
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/list/listActions.test.ts
                   test('0 invalid params')
        """
        # Given
        invalid_args = {"labels": ["toolong890" * 31]}  # Exceeds 300 character limit

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet.list_actions(invalid_args)

    @pytest.mark.skip(reason="Waiting for list_actions implementation with test database")
    def test_all_actions(self, wallet: Wallet) -> None:
        """Given: Wallet with existing actions
           When: Call list_actions with includeLabels=True
           Then: Returns paginated list of actions with labels

        Reference: wallet-toolbox/test/wallet/list/listActions.test.ts
                   test('1 all actions')

        Note: This test requires a populated test database.
        """
        # Given
        args = {"includeLabels": True, "labels": []}

        # When
        result = wallet.list_actions(args)

        # Then
        assert "totalActions" in result
        assert "actions" in result
        assert isinstance(result["actions"], list)

        for action in result["actions"]:
            assert "inputs" not in action or action["inputs"] is None
            assert "outputs" not in action or action["outputs"] is None
            assert isinstance(action.get("labels"), list)

    @pytest.mark.skip(reason="Waiting for list_actions implementation with test database")
    def test_non_existing_label_with_any(self, wallet: Wallet) -> None:
        """Given: Wallet and non-existing label
           When: Call list_actions with labelQueryMode='any'
           Then: Returns empty result

        Reference: wallet-toolbox/test/wallet/list/listActions.test.ts
                   test('2 non-existing label with any')

        Note: This test requires a populated test database.
        """
        # Given
        args = {"includeLabels": True, "labels": ["xyzzy"], "labelQueryMode": "any"}  # Non-existing label

        # When
        result = wallet.list_actions(args)

        # Then
        assert result["totalActions"] == 0
        assert len(result["actions"]) == 0

    @pytest.mark.skip(reason="Waiting for list_actions implementation with test database")
    def test_specific_label_filter(self, wallet: Wallet) -> None:
        """Given: Wallet with actions having specific label
           When: Call list_actions with label filter
           Then: Returns only actions with that label

        Reference: wallet-toolbox/test/wallet/list/listActions.test.ts
                   test('3_label babbage_protocol_perm')

        Note: This test requires a populated test database with labeled actions.
        """
        # Given
        args = {"includeLabels": True, "labels": ["test_label"]}

        # When
        result = wallet.list_actions(args)

        # Then
        assert result["totalActions"] >= len(result["actions"])
        assert len(result["actions"]) == args.get("limit", 10)

        for action in result["actions"]:
            assert "labels" in action
            assert "test_label" in action["labels"]
