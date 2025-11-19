"""Tests for validate_request_sync_chunk_args utility function.

Reference: go-wallet-toolbox/pkg/internal/validate/validate_request_sync_chunk_args_test.go
"""

from datetime import datetime

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.utils.validation import validate_request_sync_chunk_args


class TestValidateRequestSyncChunkArgs:
    """Test suite for validate_request_sync_chunk_args function.

    This validates RequestSyncChunkArgs according to BRC-100 specifications.
    RequestSyncChunkArgs must include:
    - fromStorageIdentityKey: non-empty string
    - toStorageIdentityKey: non-empty string
    - identityKey: non-empty string
    - maxRoughSize: must be greater than 0
    - maxItems: must be greater than 0
    - since: optional datetime
    - offsets: optional list of sync offsets
    """

    def test_validate_request_sync_chunk_args_valid_all_fields(self) -> None:
        """Given: Valid RequestSyncChunkArgs with all fields
           When: Call validate_request_sync_chunk_args
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_request_sync_chunk_args_test.go
                   TestValidRequestSyncChunkArgs_Success - all valid fields
        """
        # Given

        valid_args = {
            "fromStorageIdentityKey": "from_key",
            "toStorageIdentityKey": "to_key",
            "identityKey": "identity",
            "since": datetime.now(),
            "maxRoughSize": 100,
            "maxItems": 10,
            "offsets": [{"name": "entity", "offset": 5}],
        }

        # When / Then
        validate_request_sync_chunk_args(valid_args)  # Should not raise

    def test_validate_request_sync_chunk_args_valid_minimal_fields(self) -> None:
        """Given: Valid RequestSyncChunkArgs with minimal required fields
           When: Call validate_request_sync_chunk_args
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_request_sync_chunk_args_test.go
                   TestValidRequestSyncChunkArgs_Success - minimal valid fields
        """
        # Given

        valid_args = {
            "fromStorageIdentityKey": "from_key",
            "toStorageIdentityKey": "to_key",
            "identityKey": "identity",
            "maxRoughSize": 1,
            "maxItems": 1,
        }

        # When / Then
        validate_request_sync_chunk_args(valid_args)  # Should not raise

    def test_validate_request_sync_chunk_args_missing_to_storage_identity_key(self) -> None:
        """Given: RequestSyncChunkArgs with missing toStorageIdentityKey
           When: Call validate_request_sync_chunk_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_request_sync_chunk_args_test.go
                   TestValidRequestSyncChunkArgs_MissingRequiredFields - missing toStorageIdentityKey
        """
        # Given

        invalid_args = {
            "fromStorageIdentityKey": "from_key",
            "toStorageIdentityKey": "",  # Empty
            "identityKey": "identity",
            "maxRoughSize": 100,
            "maxItems": 10,
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_request_sync_chunk_args(invalid_args)
        assert "tostorageidentitykey" in str(exc_info.value).lower()

    def test_validate_request_sync_chunk_args_missing_from_storage_identity_key(self) -> None:
        """Given: RequestSyncChunkArgs with missing fromStorageIdentityKey
           When: Call validate_request_sync_chunk_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_request_sync_chunk_args_test.go
                   TestValidRequestSyncChunkArgs_MissingRequiredFields - missing fromStorageIdentityKey
        """
        # Given

        invalid_args = {
            "fromStorageIdentityKey": "",  # Empty
            "toStorageIdentityKey": "to_key",
            "identityKey": "identity",
            "maxRoughSize": 100,
            "maxItems": 10,
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_request_sync_chunk_args(invalid_args)
        assert "fromstorageidentitykey" in str(exc_info.value).lower()

    def test_validate_request_sync_chunk_args_missing_identity_key(self) -> None:
        """Given: RequestSyncChunkArgs with missing identityKey
           When: Call validate_request_sync_chunk_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_request_sync_chunk_args_test.go
                   TestValidRequestSyncChunkArgs_MissingRequiredFields - missing user identityKey
        """
        # Given

        invalid_args = {
            "fromStorageIdentityKey": "from_key",
            "toStorageIdentityKey": "to_key",
            "identityKey": "",  # Empty
            "maxRoughSize": 100,
            "maxItems": 10,
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_request_sync_chunk_args(invalid_args)
        assert "identitykey" in str(exc_info.value).lower()

    def test_validate_request_sync_chunk_args_max_items_zero(self) -> None:
        """Given: RequestSyncChunkArgs with maxItems=0
           When: Call validate_request_sync_chunk_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_request_sync_chunk_args_test.go
                   TestValidRequestSyncChunkArgs_MissingRequiredFields - maxItems is zero
        """
        # Given

        invalid_args = {
            "fromStorageIdentityKey": "from_key",
            "toStorageIdentityKey": "to_key",
            "identityKey": "identity",
            "maxRoughSize": 100,
            "maxItems": 0,  # Zero (invalid)
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_request_sync_chunk_args(invalid_args)
        assert "maxitems" in str(exc_info.value).lower() or "greater than 0" in str(exc_info.value).lower()

    def test_validate_request_sync_chunk_args_max_rough_size_zero(self) -> None:
        """Given: RequestSyncChunkArgs with maxRoughSize=0
           When: Call validate_request_sync_chunk_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_request_sync_chunk_args_test.go
                   TestValidRequestSyncChunkArgs_MissingRequiredFields - maxRoughSize is zero
        """
        # Given

        invalid_args = {
            "fromStorageIdentityKey": "from_key",
            "toStorageIdentityKey": "to_key",
            "identityKey": "identity",
            "maxRoughSize": 0,  # Zero (invalid)
            "maxItems": 10,
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_request_sync_chunk_args(invalid_args)
        assert "maxroughsize" in str(exc_info.value).lower() or "greater than 0" in str(exc_info.value).lower()
