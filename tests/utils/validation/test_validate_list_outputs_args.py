"""Tests for validate_list_outputs_args utility function.

Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_outputs_args_test.go
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.utils.validation import validate_list_outputs_args


class TestValidateListOutputsArgs:
    """Test suite for validate_list_outputs_args function.

    This validates ListOutputsArgs according to BRC-100 specifications.
    ListOutputsArgs must include:
    - limit: must be greater than 0
    - knownTxids: must be valid hexadecimal transaction IDs
    - tagQueryMode: must be valid query mode (any, all)
    """

    def test_validate_list_outputs_args_valid_paging_only(self) -> None:
        """Given: Valid ListOutputsArgs with only paging parameters
           When: Call validate_list_outputs_args
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_outputs_args_test.go
                   TestListOutputsArgs_Success - valid args only paging
        """
        # Given

        valid_args = {"limit": 10}

        # When / Then
        validate_list_outputs_args(valid_args)  # Should not raise

    def test_validate_list_outputs_args_valid_with_tag_query_all(self) -> None:
        """Given: Valid ListOutputsArgs with tagQueryMode='all'
           When: Call validate_list_outputs_args
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_outputs_args_test.go
                   TestListOutputsArgs_Success - valid args with tag query mode: all
        """
        # Given

        valid_args = {"limit": 100, "tagQueryMode": "all"}

        # When / Then
        validate_list_outputs_args(valid_args)  # Should not raise

    def test_validate_list_outputs_args_valid_with_tag_query_any(self) -> None:
        """Given: Valid ListOutputsArgs with tagQueryMode='any'
           When: Call validate_list_outputs_args
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_outputs_args_test.go
                   TestListOutputsArgs_Success - valid args with tag query mode: any
        """
        # Given

        valid_args = {"limit": 100, "tagQueryMode": "any"}

        # When / Then
        validate_list_outputs_args(valid_args)  # Should not raise

    def test_validate_list_outputs_args_invalid_txid(self) -> None:
        """Given: ListOutputsArgs with invalid txid in knownTxids
           When: Call validate_list_outputs_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_outputs_args_test.go
                   TestListOutputsArgs_Error - invalid txid
        """
        # Given

        invalid_args = {"limit": 10, "knownTxids": ["invalidhex"]}  # Not valid hex

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_list_outputs_args(invalid_args)
        assert "txid" in str(exc_info.value).lower() or "hex" in str(exc_info.value).lower()

    def test_validate_list_outputs_args_zero_limit(self) -> None:
        """Given: ListOutputsArgs with zero limit
           When: Call validate_list_outputs_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_outputs_args_test.go
                   TestListOutputsArgs_Error - zero limit
        """
        # Given

        invalid_args = {"limit": 0}  # Must be greater than 0

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_list_outputs_args(invalid_args)
        assert "limit" in str(exc_info.value).lower()

    def test_validate_list_outputs_args_wrong_tag_query(self) -> None:
        """Given: ListOutputsArgs with invalid tagQueryMode
           When: Call validate_list_outputs_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_outputs_args_test.go
                   TestListOutputsArgs_Error - wrong tag query
        """
        # Given

        invalid_args = {"limit": 10, "tagQueryMode": "invalid"}  # Invalid query mode

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_list_outputs_args(invalid_args)
        assert "tagquerymode" in str(exc_info.value).lower() or "query" in str(exc_info.value).lower()
