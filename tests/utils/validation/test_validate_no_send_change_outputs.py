"""Tests for validate_no_send_change_outputs utility function.

Reference: go-wallet-toolbox/pkg/internal/validate/validate_no_send_change_outputs_test.go
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.utils.validation import validate_no_send_change_outputs


class TestValidateNoSendChangeOutputs:
    """Test suite for validate_no_send_change_outputs function.

    This validates that outputs (for noSend change) meet specific criteria:
    - providedBy: must match "storage"
    - purpose: must match "change"
    - basketName: must not be None and must match "change basket"
    """

    def test_validate_no_send_change_outputs_single_valid_output(self) -> None:
        """Given: Single valid output with correct fields
           When: Call validate_no_send_change_outputs
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_no_send_change_outputs_test.go
                   TestNoSendChangeOutputs_Success - single valid output
        """
        # Given

        valid_outputs = [{"id": 1, "providedBy": "storage", "purpose": "change", "basketName": "change basket"}]

        # When / Then
        validate_no_send_change_outputs(valid_outputs)  # Should not raise

    def test_validate_no_send_change_outputs_multiple_valid_outputs(self) -> None:
        """Given: Multiple valid outputs with correct fields
           When: Call validate_no_send_change_outputs
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_no_send_change_outputs_test.go
                   TestNoSendChangeOutputs_Success - multiple valid outputs
        """
        # Given

        valid_outputs = [
            {"id": 1, "providedBy": "storage", "purpose": "change", "basketName": "change basket"},
            {"id": 2, "providedBy": "storage", "purpose": "change", "basketName": "change basket"},
        ]

        # When / Then
        validate_no_send_change_outputs(valid_outputs)  # Should not raise

    def test_validate_no_send_change_outputs_empty_outputs(self) -> None:
        """Given: Empty outputs list
           When: Call validate_no_send_change_outputs
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_no_send_change_outputs_test.go
                   TestNoSendChangeOutputs_Success - empty outputs
        """
        # Given

        # When / Then
        validate_no_send_change_outputs([])  # Should not raise

    def test_validate_no_send_change_outputs_provided_by_mismatch(self) -> None:
        """Given: Output with providedBy not matching 'storage'
           When: Call validate_no_send_change_outputs
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_no_send_change_outputs_test.go
                   TestNoSendChangeOutputs_Error - ProvidedBy field value doesn't match
        """
        # Given

        invalid_outputs = [
            {"id": 4, "providedBy": "you", "purpose": "change", "basketName": "change basket"}  # Should be "storage"
        ]

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_no_send_change_outputs(invalid_outputs)
        assert "provided" in str(exc_info.value).lower() or "match" in str(exc_info.value).lower()

    def test_validate_no_send_change_outputs_purpose_mismatch(self) -> None:
        """Given: Output with purpose not matching 'change'
           When: Call validate_no_send_change_outputs
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_no_send_change_outputs_test.go
                   TestNoSendChangeOutputs_Error - Purpose field value doesn't match
        """
        # Given

        invalid_outputs = [
            {
                "id": 5,
                "providedBy": "storage",
                "purpose": "bad-purpose",  # Should be "change"
                "basketName": "change basket",
            }
        ]

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_no_send_change_outputs(invalid_outputs)
        assert "purpose" in str(exc_info.value).lower() or "match" in str(exc_info.value).lower()

    def test_validate_no_send_change_outputs_basket_name_none(self) -> None:
        """Given: Output with basketName set to None
           When: Call validate_no_send_change_outputs
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_no_send_change_outputs_test.go
                   TestNoSendChangeOutputs_Error - BasketName field value is nil
        """
        # Given

        invalid_outputs = [
            {"id": 5, "providedBy": "storage", "purpose": "change", "basketName": None}  # Should not be None
        ]

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_no_send_change_outputs(invalid_outputs)
        assert "basket" in str(exc_info.value).lower() or "nil" in str(exc_info.value).lower()

    def test_validate_no_send_change_outputs_basket_name_mismatch(self) -> None:
        """Given: Output with basketName not matching 'change basket'
           When: Call validate_no_send_change_outputs
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_no_send_change_outputs_test.go
                   TestNoSendChangeOutputs_Error - BasketName field value doesn't match
        """
        # Given

        invalid_outputs = [
            {
                "id": 5,
                "providedBy": "storage",
                "purpose": "change",
                "basketName": "bad-basket-name",  # Should be "change basket"
            }
        ]

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_no_send_change_outputs(invalid_outputs)
        assert "basket" in str(exc_info.value).lower() or "match" in str(exc_info.value).lower()
