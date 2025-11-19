"""Tests for validate_list_actions_args utility function.

Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_actions_args_test.go
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.utils.validation import validate_list_actions_args


class TestValidateListActionsArgs:
    """Test suite for validate_list_actions_args function.

    This validates ListActionsArgs according to BRC-100 specifications.
    ListActionsArgs must include:
    - limit: must not exceed MaxPaginationLimit (typically 10000)
    - offset: must not exceed MaxPaginationOffset (typically 1000000)
    - labelQueryMode: must be valid query mode (any, all, or empty string)
    - seekPermission: must be True (default True)
    - labels: each label must be non-empty and under 300 characters
    """

    def test_validate_list_actions_args_valid(self) -> None:
        """Given: Valid ListActionsArgs
           When: Call validate_list_actions_args
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_actions_args_test.go
                   TestListActionsArgs - valid args
        """
        # Given

        valid_args = {
            "limit": 100,
            "offset": 0,
            "labelQueryMode": "any",
            "labels": ["valid-label"],
            "seekPermission": True,
        }

        # When / Then
        validate_list_actions_args(valid_args)  # Should not raise

    def test_validate_list_actions_args_nil(self) -> None:
        """Given: None as arguments
           When: Call validate_list_actions_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_actions_args_test.go
                   TestWrongListActionsArgs - nil args
        """
        # Given

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_list_actions_args(None)
        assert "args" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()

    def test_validate_list_actions_args_limit_exceeds_max(self) -> None:
        """Given: ListActionsArgs with limit exceeding maximum
           When: Call validate_list_actions_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_actions_args_test.go
                   TestWrongListActionsArgs - limit exceeds max
        """
        # Given

        invalid_args = {"limit": 10001}  # Exceeds typical MaxPaginationLimit of 10000

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_list_actions_args(invalid_args)
        assert "limit" in str(exc_info.value).lower()

    def test_validate_list_actions_args_offset_exceeds_max(self) -> None:
        """Given: ListActionsArgs with offset exceeding maximum
           When: Call validate_list_actions_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_actions_args_test.go
                   TestWrongListActionsArgs - offset exceeds max
        """
        # Given

        invalid_args = {"offset": 1000001}  # Exceeds typical MaxPaginationOffset of 1000000

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_list_actions_args(invalid_args)
        assert "offset" in str(exc_info.value).lower()

    def test_validate_list_actions_args_invalid_label_query_mode(self) -> None:
        """Given: ListActionsArgs with invalid labelQueryMode
           When: Call validate_list_actions_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_actions_args_test.go
                   TestWrongListActionsArgs - invalid labelQueryMode
        """
        # Given

        invalid_args = {"labelQueryMode": "unknown"}  # Invalid mode (must be "any", "all", or empty)

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_list_actions_args(invalid_args)
        assert "labelquerymode" in str(exc_info.value).lower() or "query" in str(exc_info.value).lower()

    def test_validate_list_actions_args_seek_permission_false(self) -> None:
        """Given: ListActionsArgs with seekPermission=False
           When: Call validate_list_actions_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_actions_args_test.go
                   TestWrongListActionsArgs - seekPermission set to false
        """
        # Given

        invalid_args = {"seekPermission": False}  # Must be True

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_list_actions_args(invalid_args)
        assert "permission" in str(exc_info.value).lower()

    def test_validate_list_actions_args_label_too_long(self) -> None:
        """Given: ListActionsArgs with label exceeding 300 characters
           When: Call validate_list_actions_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_actions_args_test.go
                   TestWrongListActionsArgs - invalid label - too long
        """
        # Given

        invalid_args = {"labels": ["x" * 301]}  # 301 characters (exceeds 300 limit)

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_list_actions_args(invalid_args)
        assert "label" in str(exc_info.value).lower()

    def test_validate_list_actions_args_label_empty(self) -> None:
        """Given: ListActionsArgs with empty label
           When: Call validate_list_actions_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_actions_args_test.go
                   TestWrongListActionsArgs - invalid label - empty
        """
        # Given

        invalid_args = {"labels": [""]}  # Empty label

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_list_actions_args(invalid_args)
        assert "label" in str(exc_info.value).lower()
