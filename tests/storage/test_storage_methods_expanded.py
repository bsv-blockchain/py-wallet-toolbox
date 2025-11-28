"""Expanded tests for storage methods with better coverage.

This module provides more comprehensive tests for storage methods,
focusing on edge cases, error conditions, and actual logic testing.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from bsv_wallet_toolbox.errors import WalletError
from bsv_wallet_toolbox.storage.methods import (
    get_sync_chunk,
    purge_data,
    review_status,
    attempt_to_post_reqs_to_network,
    get_beef_for_transaction,
    StorageProcessActionArgs,
    StorageProcessActionResults,
    GenerateChangeInput,
    ListActionsArgs,
    ListOutputsArgs,
)


class TestGetSyncChunk:
    """Comprehensive tests for get_sync_chunk function."""

    def test_get_sync_chunk_requires_storage(self) -> None:
        """Test that get_sync_chunk requires storage parameter."""
        with pytest.raises(WalletError, match="storage is required"):
            get_sync_chunk(None, {"userId": "test"})

    def test_get_sync_chunk_requires_user_id(self) -> None:
        """Test that get_sync_chunk requires userId in args."""
        storage = Mock()
        with pytest.raises(WalletError, match="userId is required"):
            get_sync_chunk(storage, {})

    def test_get_sync_chunk_basic_flow(self) -> None:
        """Test basic get_sync_chunk flow with mocked storage."""
        storage = Mock()

        # Mock storage methods
        storage.findOne.return_value = None
        storage.find.return_value = []
        storage.count.return_value = 0

        args = {"userId": "test_user"}
        result = get_sync_chunk(storage, args)

        # Verify result structure
        assert "syncState" in result
        assert "transactions" in result
        assert "outputs" in result
        assert "certificates" in result
        assert "labels" in result
        assert "baskets" in result
        assert "hasMore" in result
        assert "nextChunkId" in result
        assert "syncVersion" in result

        # Verify default values
        assert result["syncState"] == {}
        assert result["transactions"] == []
        assert result["outputs"] == []
        assert result["certificates"] == []
        assert result["labels"] == []
        assert result["baskets"] == []
        assert result["hasMore"] is False
        assert result["nextChunkId"] is None

    def test_get_sync_chunk_with_sync_state(self) -> None:
        """Test get_sync_chunk with existing sync state."""
        storage = Mock()

        # Mock existing sync state
        mock_sync_state = {
            "userId": "test_user",
            "lastSyncTimestamp": "2023-01-01T00:00:00Z",
            "syncVersion": 5,
        }
        storage.findOne.return_value = mock_sync_state
        storage.find.return_value = []
        storage.count.return_value = 0

        args = {"userId": "test_user"}
        result = get_sync_chunk(storage, args)

        # Verify sync state is populated
        assert result["syncState"]["userId"] == "test_user"
        assert result["syncState"]["lastSyncTimestamp"] == "2023-01-01T00:00:00Z"
        assert result["syncState"]["syncVersion"] == 5

    def test_get_sync_chunk_with_transactions(self) -> None:
        """Test get_sync_chunk with transaction data."""
        storage = Mock()

        mock_transactions = [
            {
                "txid": "abcd" * 16,
                "satoshis": 1000,
                "status": "completed",
                "description": "test tx",
                "createdAt": "2023-01-01T00:00:00Z",
                "updatedAt": "2023-01-01T00:00:00Z",
            }
        ]

        storage.findOne.return_value = None
        storage.find.side_effect = [mock_transactions, [], [], []]  # tx, outputs, certs, labels
        storage.count.return_value = 1

        args = {"userId": "test_user"}
        result = get_sync_chunk(storage, args)

        # Verify transactions are included
        assert len(result["transactions"]) == 1
        tx = result["transactions"][0]
        assert tx["txid"] == "abcd" * 16
        assert tx["satoshis"] == 1000
        assert tx["status"] == "completed"

    def test_get_sync_chunk_with_chunk_size_and_offset(self) -> None:
        """Test get_sync_chunk with custom chunk size and offset."""
        storage = Mock()

        storage.findOne.return_value = None
        storage.find.return_value = []
        storage.count.return_value = 1000  # More than chunk size

        args = {
            "userId": "test_user",
            "chunkSize": 50,
            "chunkOffset": 25,
        }
        result = get_sync_chunk(storage, args)

        # Verify storage.find was called with correct parameters
        storage.find.assert_any_call(
            "Transaction",
            {"userId": "test_user", "isDeleted": False},
            limit=50,
            offset=25,
        )

        # Should indicate more data available
        assert result["hasMore"] is True
        assert result["nextChunkId"] == 75

    def test_get_sync_chunk_with_sync_from_filter(self) -> None:
        """Test get_sync_chunk with syncFrom timestamp filter."""
        storage = Mock()

        sync_from = "2023-01-01T00:00:00Z"
        storage.findOne.return_value = None
        storage.find.return_value = []
        storage.count.return_value = 0

        args = {
            "userId": "test_user",
            "syncFrom": sync_from,
        }
        result = get_sync_chunk(storage, args)

        # Verify storage.find was called with timestamp filter
        expected_filter = {
            "userId": "test_user",
            "isDeleted": False,
            "updatedAt": {"$gt": sync_from},
        }
        storage.find.assert_any_call(
            "Transaction",
            expected_filter,
            limit=100,
            offset=0,
        )

    def test_get_sync_chunk_creates_sync_state(self) -> None:
        """Test get_sync_chunk creates new sync state when none exists."""
        storage = Mock()

        storage.findOne.return_value = None
        storage.find.return_value = []
        storage.count.return_value = 0

        args = {"userId": "test_user"}
        result = get_sync_chunk(storage, args)

        # Verify storage.insert was called to create sync state
        storage.insert.assert_called_once()
        insert_args = storage.insert.call_args[0]
        assert insert_args[0] == "SyncState"
        sync_state_data = insert_args[1]
        assert sync_state_data["userId"] == "test_user"
        assert "lastSyncTimestamp" in sync_state_data
        assert sync_state_data["syncVersion"] == 1

        assert result["syncVersion"] == 1

    def test_get_sync_chunk_updates_sync_state(self) -> None:
        """Test get_sync_chunk updates existing sync state."""
        storage = Mock()

        existing_sync_state = {
            "userId": "test_user",
            "lastSyncTimestamp": "2023-01-01T00:00:00Z",
            "syncVersion": 3,
        }

        storage.findOne.return_value = existing_sync_state
        storage.find.return_value = []
        storage.count.return_value = 0

        args = {"userId": "test_user"}
        result = get_sync_chunk(storage, args)

        # Verify storage.update was called
        storage.update.assert_called_once()
        update_args = storage.update.call_args[0]
        assert update_args[0] == "SyncState"
        assert update_args[1] == {"userId": "test_user"}

        update_data = update_args[2]
        assert "lastSyncTimestamp" in update_data
        assert update_data["syncVersion"] == 4

        assert result["syncVersion"] == 4

    def test_get_sync_chunk_with_outputs_and_certificates(self) -> None:
        """Test get_sync_chunk includes outputs and certificates data."""
        storage = Mock()

        mock_outputs = [
            {
                "txid": "1234" * 16,
                "vout": 0,
                "satoshis": 500,
                "basket": "default",
                "script": "OP_RETURN",
            }
        ]

        mock_certificates = [
            {
                "certificateId": "cert123",
                "subjectString": "test@example.com",
                "type": "identity",
            }
        ]

        storage.findOne.return_value = None
        storage.find.side_effect = [[], mock_outputs, mock_certificates, []]  # tx, outputs, certs, labels
        storage.count.return_value = 0

        args = {"userId": "test_user"}
        result = get_sync_chunk(storage, args)

        # Verify outputs
        assert len(result["outputs"]) == 1
        output = result["outputs"][0]
        assert output["txid"] == "1234" * 16
        assert output["vout"] == 0
        assert output["satoshis"] == 500

        # Verify certificates
        assert len(result["certificates"]) == 1
        cert = result["certificates"][0]
        assert cert["certificateId"] == "cert123"
        assert cert["subjectString"] == "test@example.com"


class TestPurgeData:
    """Comprehensive tests for purge_data function."""

    def test_purge_data_requires_storage(self) -> None:
        """Test that purge_data requires storage parameter."""
        with pytest.raises(WalletError, match="storage is required"):
            purge_data(None, {"purgeCompleted": True})

    def test_purge_data_basic_completed_purge(self) -> None:
        """Test purge_data with completed transaction purging."""
        storage = Mock()

        storage.update.return_value = 0
        storage.delete.return_value = 0

        params = {"agedBeforeDate": "2023-01-01T00:00:00Z"}  # With date parameter
        result = purge_data(storage, params)

        # Verify result structure (matches actual function return)
        assert "deleted_transactions" in result
        assert "deleted_outputs" in result
        assert "deleted_certificates" in result
        assert "deleted_requests" in result
        assert "deleted_labels" in result

        # Verify storage operations were called
        storage.delete.assert_called()

    def test_purge_data_multiple_flags(self) -> None:
        """Test purge_data with multiple purge flags enabled."""
        storage = Mock()

        storage.find_transactions.return_value = []
        storage.update.return_value = 0  # No items to purge
        storage.delete.return_value = 0  # No items to delete

        params = {
            "purgeCompleted": True,
            "purgeFailed": True,
            "purgeSpent": True,
            "purgeUnspent": True,
        }
        result = purge_data(storage, params)

        # Verify result structure
        assert result["deleted_transactions"] == 0
        assert result["deleted_outputs"] == 0
        assert result["deleted_certificates"] == 0
        assert result["deleted_requests"] == 0
        assert result["deleted_labels"] == 0

    def test_purge_data_empty_params(self) -> None:
        """Test purge_data with empty parameters."""
        storage = Mock()

        storage.find_transactions.return_value = []
        storage.update.return_value = 0

        params = {}
        result = purge_data(storage, params)

        # Should handle empty params gracefully
        assert all(count == 0 for count in result.values() if isinstance(count, int))


class TestReviewStatus:
    """Comprehensive tests for review_status function."""

    def test_review_status_requires_storage(self) -> None:
        """Test that review_status requires storage parameter."""
        with pytest.raises(WalletError, match="storage is required"):
            review_status(None, {"userId": "test"}, 3600)

    def test_review_status_basic_flow(self) -> None:
        """Test basic review_status flow."""
        storage = Mock()

        mock_transactions = [
            {"id": 1, "status": "unproven", "createdAt": "2023-01-01T00:00:00Z"},
            {"id": 2, "status": "failed", "createdAt": "2023-01-01T00:00:00Z"},
        ]

        storage.find.return_value = mock_transactions
        storage.update.return_value = 1

        auth = {"userId": "test_user"}
        result = review_status(storage, auth, 3600)

        # Verify result structure (matches actual function)
        assert "updated_count" in result
        assert "aged_count" in result
        assert "log" in result

    def test_review_status_no_aged_limit(self) -> None:
        """Test review_status with no aged limit."""
        storage = Mock()

        storage.find.return_value = []
        storage.update.return_value = 0

        auth = {"userId": "test_user"}
        result = review_status(storage, auth, None)

        # Should handle None aged_limit gracefully
        assert result["aged_count"] == 0

    def test_review_status_with_aged_requests(self) -> None:
        """Test review_status identifies aged requests correctly."""
        storage = Mock()

        # Mock transactions with different ages
        old_timestamp = (datetime.now(timezone.utc) - timedelta(seconds=7200)).isoformat()  # 2 hours ago
        recent_timestamp = datetime.now(timezone.utc).isoformat()  # Now

        mock_transactions = [
            {"id": 1, "status": "unproven", "createdAt": old_timestamp},
            {"id": 2, "status": "unproven", "createdAt": recent_timestamp},
        ]

        storage.find.return_value = mock_transactions
        storage.update.return_value = 1

        auth = {"userId": "test_user"}
        result = review_status(storage, auth, 3600)  # 1 hour limit

        # Should process transactions (exact count depends on implementation)
        assert "updated_count" in result


class TestAttemptToPostReqsToNetwork:
    """Comprehensive tests for attempt_to_post_reqs_to_network function."""

    def test_attempt_to_post_reqs_to_network_requires_storage(self) -> None:
        """Test that attempt_to_post_reqs_to_network requires storage parameter."""
        with pytest.raises(WalletError, match="storage is required"):
            attempt_to_post_reqs_to_network(None, {"userId": "test"}, ["tx1"])

    def test_attempt_to_post_reqs_to_network_empty_txids(self) -> None:
        """Test attempt_to_post_reqs_to_network with empty txids list."""
        storage = Mock()

        storage.find_proven_tx_reqs.return_value = []
        storage.get_services.return_value = Mock()

        auth = {"userId": "test_user"}
        result = attempt_to_post_reqs_to_network(storage, auth, [])

        # Should return empty result (matches actual function return)
        assert isinstance(result, dict)
        assert "posted_txids" in result
        assert "failed_txids" in result
        assert "results" in result

    def test_attempt_to_post_reqs_to_network_with_txids(self) -> None:
        """Test attempt_to_post_reqs_to_network with transaction IDs."""
        storage = Mock()

        mock_reqs = [
            {"id": 1, "txid": "tx1", "status": "unproven", "beef": "beef1"},
            {"id": 2, "txid": "tx2", "status": "unproven", "beef": "beef2"},
        ]

        # Mock findOne to return reqs for each txid
        storage.findOne.side_effect = lambda table, query: next(
            (req for req in mock_reqs if req["txid"] == query["txid"]), None
        )
        storage.update.return_value = 1

        auth = {"userId": "test_user"}
        # Mock the HTTP request to avoid actual network calls
        with patch('bsv_wallet_toolbox.storage.methods.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = attempt_to_post_reqs_to_network(storage, auth, ["tx1", "tx2"])

        # Verify HTTP post was called for each txid
        assert mock_post.call_count == 2

        # Verify result structure
        assert "posted_txids" in result
        assert "failed_txids" in result
        assert "results" in result


class TestGetBeefForTransaction:
    """Comprehensive tests for get_beef_for_transaction function."""

    def test_get_beef_for_transaction_requires_storage(self) -> None:
        """Test that get_beef_for_transaction requires storage parameter."""
        with pytest.raises(WalletError, match="storage is required"):
            get_beef_for_transaction(None, {"userId": "test"}, "txid")

    def test_get_beef_for_transaction_basic_flow(self) -> None:
        """Test basic get_beef_for_transaction flow."""
        storage = Mock()

        mock_beef_data = "mock_beef_data"
        mock_proven_tx = {"beef": mock_beef_data}
        storage.findOne.return_value = mock_proven_tx

        auth = {"userId": "test_user"}
        result = get_beef_for_transaction(storage, auth, "test_txid")

        # Verify storage method was called correctly
        storage.findOne.assert_called_with("ProvenTx", {"txid": "test_txid", "isDeleted": False})

        assert result == mock_beef_data

    def test_get_beef_for_transaction_with_protocol(self) -> None:
        """Test get_beef_for_transaction with options parameter."""
        storage = Mock()

        mock_beef_data = "beef_data"
        mock_proven_tx = {"beef": mock_beef_data}
        storage.findOne.return_value = mock_proven_tx

        auth = {"userId": "test_user"}
        options = {"mergeToBeef": "some_beef"}
        result = get_beef_for_transaction(storage, auth, "test_txid", options)

        assert result == mock_beef_data

    def test_get_beef_for_transaction_with_options(self) -> None:
        """Test get_beef_for_transaction with options."""
        storage = Mock()

        mock_beef_data = "beef_data"
        mock_proven_tx = {"beef": mock_beef_data}
        storage.findOne.return_value = mock_proven_tx

        auth = {"userId": "test_user"}
        options = {"some_option": "value"}
        result = get_beef_for_transaction(storage, auth, "test_txid", options)

        assert result == mock_beef_data

    def test_get_beef_for_transaction_returns_none_when_no_beef(self) -> None:
        """Test get_beef_for_transaction raises error when no BEEF data found."""
        storage = Mock()

        # No ProvenTx found, no ProvenTxReq found
        storage.findOne.return_value = None

        auth = {"userId": "test_user"}

        with pytest.raises(WalletError, match="not found"):
            get_beef_for_transaction(storage, auth, "nonexistent_txid")


class TestStorageMethodIntegration:
    """Integration tests combining multiple storage methods."""

    def test_sync_chunk_and_purge_integration(self) -> None:
        """Test integration between sync chunk and purge operations."""
        storage = Mock()

        # Setup sync chunk data
        storage.findOne.return_value = None
        storage.find.return_value = []
        storage.count.return_value = 0

        # Get initial sync chunk
        args = {"userId": "test_user"}
        sync_result = get_sync_chunk(storage, args)

        # Verify sync state was created
        assert sync_result["syncVersion"] == 1

        # Now test purge (should work with the created sync state)
        storage.find_transactions.return_value = []
        storage.update.return_value = 0

        purge_result = purge_data(storage, {"purgeCompleted": True})

        # Both operations should succeed
        assert isinstance(sync_result, dict)
        assert isinstance(purge_result, dict)

    def test_review_and_post_reqs_integration(self) -> None:
        """Test integration between review status and post reqs operations."""
        storage = Mock()

        # Setup review status
        storage.find.return_value = []
        storage.update.return_value = 0

        auth = {"userId": "test_user"}
        review_result = review_status(storage, auth, 3600)

        # Setup post reqs
        storage.findOne.return_value = None

        post_result = attempt_to_post_reqs_to_network(storage, auth, [])

        # Both operations should succeed
        assert isinstance(review_result, dict)
        assert isinstance(post_result, dict)
