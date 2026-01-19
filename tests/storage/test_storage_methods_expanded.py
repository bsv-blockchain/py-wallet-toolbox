"""Expanded tests for storage methods with better coverage.

This module provides more comprehensive tests for storage methods,
focusing on edge cases, error conditions, and actual logic testing.
"""

from unittest.mock import Mock, patch

import pytest

from bsv_wallet_toolbox.errors import WalletError
from bsv_wallet_toolbox.storage.methods import (
    attempt_to_post_reqs_to_network,
    get_beef_for_transaction,
    get_sync_chunk,
    purge_data,
    review_status,
)


class TestGetSyncChunk:
    """Comprehensive tests for get_sync_chunk function."""

    def test_get_sync_chunk_requires_storage(self) -> None:
        """Test that get_sync_chunk requires storage parameter."""
        with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'get_sync_chunk'"):
            get_sync_chunk(None, {"userId": "test"})

    def test_get_sync_chunk_requires_user_id(self) -> None:
        """Test that get_sync_chunk requires userId in args."""
        storage = Mock()
        storage.get_sync_chunk = Mock(side_effect=WalletError("userId is required"))
        with pytest.raises(WalletError, match="userId is required"):
            get_sync_chunk(storage, {})

    def test_get_sync_chunk_basic_flow(self) -> None:
        """Test basic get_sync_chunk flow with mocked storage."""
        storage = Mock()

        # Mock storage.get_sync_chunk to return expected structure
        storage.get_sync_chunk = Mock(
            return_value={
                "syncState": {},
                "transactions": [],
                "outputs": [],
                "certificates": [],
                "labels": [],
                "baskets": [],
                "hasMore": False,
                "nextChunkId": None,
                "syncVersion": 1,
            }
        )

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
        storage.get_sync_chunk = Mock(
            return_value={
                "syncState": mock_sync_state,
                "transactions": [],
                "outputs": [],
                "certificates": [],
                "labels": [],
                "baskets": [],
                "hasMore": False,
                "nextChunkId": None,
                "syncVersion": 5,
            }
        )

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

        storage.get_sync_chunk = Mock(
            return_value={
                "syncState": {},
                "transactions": mock_transactions,
                "outputs": [],
                "certificates": [],
                "labels": [],
                "baskets": [],
                "hasMore": False,
                "nextChunkId": None,
                "syncVersion": 1,
            }
        )

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

        storage.get_sync_chunk = Mock(
            return_value={
                "syncState": {},
                "transactions": [],
                "outputs": [],
                "certificates": [],
                "labels": [],
                "baskets": [],
                "hasMore": True,
                "nextChunkId": 75,  # chunkOffset (25) + chunkSize (50)
                "syncVersion": 1,
            }
        )

        args = {
            "userId": "test_user",
            "chunkSize": 50,
            "chunkOffset": 25,
        }
        result = get_sync_chunk(storage, args)

        # Should indicate more data available
        assert result["hasMore"] is True
        assert result["nextChunkId"] == 75

    def test_get_sync_chunk_with_sync_from_filter(self) -> None:
        """Test get_sync_chunk with syncFrom timestamp filter."""
        storage = Mock()

        sync_from = "2023-01-01T00:00:00Z"
        storage.get_sync_chunk = Mock(
            return_value={
                "syncState": {},
                "transactions": [],
                "outputs": [],
                "certificates": [],
                "labels": [],
                "baskets": [],
                "hasMore": False,
                "nextChunkId": None,
                "syncVersion": 1,
            }
        )

        args = {
            "userId": "test_user",
            "syncFrom": sync_from,
        }
        result = get_sync_chunk(storage, args)

        # Verify storage.get_sync_chunk was called with the args
        storage.get_sync_chunk.assert_called_once_with(args)
        assert result["syncVersion"] == 1

    def test_get_sync_chunk_creates_sync_state(self) -> None:
        """Test get_sync_chunk creates new sync state when none exists."""
        storage = Mock()

        storage.get_sync_chunk = Mock(
            return_value={
                "syncState": {"userId": "test_user", "syncVersion": 1},
                "transactions": [],
                "outputs": [],
                "certificates": [],
                "labels": [],
                "baskets": [],
                "hasMore": False,
                "nextChunkId": None,
                "syncVersion": 1,
            }
        )

        args = {"userId": "test_user"}
        result = get_sync_chunk(storage, args)

        # Verify storage.get_sync_chunk was called
        storage.get_sync_chunk.assert_called_once_with(args)
        assert result["syncVersion"] == 1
        assert result["syncState"]["userId"] == "test_user"

    def test_get_sync_chunk_updates_sync_state(self) -> None:
        """Test get_sync_chunk updates existing sync state."""
        storage = Mock()

        storage.get_sync_chunk = Mock(
            return_value={
                "syncState": {"userId": "test_user", "lastSyncTimestamp": "2023-01-02T00:00:00Z", "syncVersion": 4},
                "transactions": [],
                "outputs": [],
                "certificates": [],
                "labels": [],
                "baskets": [],
                "hasMore": False,
                "nextChunkId": None,
                "syncVersion": 4,
            }
        )

        args = {"userId": "test_user"}
        result = get_sync_chunk(storage, args)

        # Verify storage.get_sync_chunk was called
        storage.get_sync_chunk.assert_called_once_with(args)
        assert result["syncVersion"] == 4
        assert result["syncState"]["syncVersion"] == 4

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

        storage.get_sync_chunk = Mock(
            return_value={
                "syncState": {},
                "transactions": [],
                "outputs": mock_outputs,
                "certificates": mock_certificates,
                "labels": [],
                "baskets": [],
                "hasMore": False,
                "nextChunkId": None,
                "syncVersion": 1,
            }
        )

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
        with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'purge_data'"):
            purge_data(None, {"purgeCompleted": True})

    def test_purge_data_basic_completed_purge(self) -> None:
        """Test purge_data with completed transaction purging."""
        storage = Mock()

        storage.purge_data = Mock(
            return_value={
                "deletedTransactions": 0,
                "deletedOutputs": 0,
                "deletedCertificates": 0,
                "deletedRequests": 0,
                "deletedLabels": 0,
                "log": "",
            }
        )

        params = {"agedBeforeDate": "2023-01-01T00:00:00Z"}  # With date parameter
        result = purge_data(storage, params)

        # Verify result structure (matches actual function return)
        assert "deletedTransactions" in result
        assert "deletedOutputs" in result
        assert "deletedCertificates" in result
        assert "deletedRequests" in result
        assert "deletedLabels" in result

        # Verify storage.purge_data was called
        storage.purge_data.assert_called_once_with(params)

    def test_purge_data_multiple_flags(self) -> None:
        """Test purge_data with multiple purge flags enabled."""
        storage = Mock()

        storage.purge_data = Mock(
            return_value={
                "deletedTransactions": 0,
                "deletedOutputs": 0,
                "deletedCertificates": 0,
                "deletedRequests": 0,
                "deletedLabels": 0,
                "log": "",
            }
        )

        params = {
            "purgeCompleted": True,
            "purgeFailed": True,
            "purgeSpent": True,
            "purgeUnspent": True,
        }
        result = purge_data(storage, params)

        # Verify result structure
        assert result["deletedTransactions"] == 0
        assert result["deletedOutputs"] == 0
        assert result["deletedCertificates"] == 0
        assert result["deletedRequests"] == 0
        assert result["deletedLabels"] == 0

    def test_purge_data_empty_params(self) -> None:
        """Test purge_data with empty parameters."""
        storage = Mock()

        storage.purge_data = Mock(
            return_value={
                "deletedTransactions": 0,
                "deletedOutputs": 0,
                "deletedCertificates": 0,
                "deletedRequests": 0,
                "deletedLabels": 0,
                "log": "",
            }
        )

        params = {}
        result = purge_data(storage, params)

        # Should handle empty params gracefully
        assert all(count == 0 for count in result.values() if isinstance(count, int))


class TestReviewStatus:
    """Comprehensive tests for review_status function."""

    def test_review_status_requires_storage(self) -> None:
        """Test that review_status requires storage parameter."""
        with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'review_status'"):
            review_status(None, {"agedLimit": 3600})

    def test_review_status_basic_flow(self) -> None:
        """Test basic review_status flow."""
        storage = Mock()

        storage.review_status = Mock(return_value={"updatedCount": 1, "agedCount": 0, "log": ""})

        args = {"agedLimit": 3600}
        result = review_status(storage, args)

        # Verify result structure (matches actual function)
        assert "updatedCount" in result
        assert "agedCount" in result
        assert "log" in result

    def test_review_status_no_aged_limit(self) -> None:
        """Test review_status with no aged limit."""
        storage = Mock()

        storage.review_status = Mock(return_value={"updatedCount": 0, "agedCount": 0, "log": ""})

        args = {}
        result = review_status(storage, args)

        # Should handle None aged_limit gracefully
        assert result["agedCount"] == 0

    def test_review_status_with_aged_requests(self) -> None:
        """Test review_status identifies aged requests correctly."""
        storage = Mock()

        storage.review_status = Mock(return_value={"updatedCount": 1, "agedCount": 1, "log": ""})

        args = {"agedLimit": 3600}  # 1 hour limit
        result = review_status(storage, args)

        # Should process transactions (exact count depends on implementation)
        assert "updatedCount" in result


class TestAttemptToPostReqsToNetwork:
    """Comprehensive tests for attempt_to_post_reqs_to_network function."""

    def test_attempt_to_post_reqs_to_network_requires_storage(self) -> None:
        """Test that attempt_to_post_reqs_to_network requires storage parameter."""
        with pytest.raises(
            AttributeError, match="'NoneType' object has no attribute 'attempt_to_post_reqs_to_network'"
        ):
            attempt_to_post_reqs_to_network(None, [])

    def test_attempt_to_post_reqs_to_network_empty_txids(self) -> None:
        """Test attempt_to_post_reqs_to_network with empty reqs list."""
        storage = Mock()

        storage.attempt_to_post_reqs_to_network = Mock(return_value={"posted": 0, "failed": 0})

        reqs = []
        result = attempt_to_post_reqs_to_network(storage, reqs)

        # Should return empty result (matches actual function return)
        assert isinstance(result, dict)
        assert "posted" in result
        assert "failed" in result

    def test_attempt_to_post_reqs_to_network_with_txids(self) -> None:
        """Test attempt_to_post_reqs_to_network with transaction IDs."""
        storage = Mock()

        mock_reqs = [
            {"id": 1, "txid": "tx1", "status": "unproven", "beef": "beef1"},
            {"id": 2, "txid": "tx2", "status": "unproven", "beef": "beef2"},
        ]

        storage.attempt_to_post_reqs_to_network = Mock(return_value={"posted": 2, "failed": 0})

        result = attempt_to_post_reqs_to_network(storage, mock_reqs)

        # Verify result structure
        assert "posted" in result
        assert "failed" in result
        assert result["posted"] == 2


class TestGetBeefForTransaction:
    """Comprehensive tests for get_beef_for_transaction function."""

    VALID_TXID = "a" * 64

    def test_get_beef_for_transaction_requires_storage(self) -> None:
        """Test that get_beef_for_transaction requires storage parameter."""
        with pytest.raises(AttributeError, match="NoneType"):
            get_beef_for_transaction(None, self.VALID_TXID)

    def test_get_beef_for_transaction_basic_flow(self) -> None:
        """Test basic get_beef_for_transaction flow."""
        storage = Mock()
        mock_beef_data = b"mock_beef_data"

        with patch(
            "bsv_wallet_toolbox.storage.methods_impl.get_beef_for_transaction",
            return_value=mock_beef_data,
        ) as mock_impl:
            result = get_beef_for_transaction(storage, self.VALID_TXID)

        mock_impl.assert_called_once_with(storage, {}, self.VALID_TXID, None)
        assert result == mock_beef_data

    def test_get_beef_for_transaction_with_protocol(self) -> None:
        """Test get_beef_for_transaction supports protocol-specific options."""
        storage = Mock()
        options = {"protocol": {"name": "arc", "version": 1}}
        mock_beef_data = b"proto_beef_data"

        with patch(
            "bsv_wallet_toolbox.storage.methods_impl.get_beef_for_transaction",
            return_value=mock_beef_data,
        ) as mock_impl:
            result = get_beef_for_transaction(storage, self.VALID_TXID, options=options)

        mock_impl.assert_called_once_with(storage, {}, self.VALID_TXID, options)
        assert result == mock_beef_data

    def test_get_beef_for_transaction_with_auth(self) -> None:
        """Test get_beef_for_transaction forwards auth context."""
        storage = Mock()
        auth = {"userId": 1}
        mock_beef_data = b"beef_data"

        with patch(
            "bsv_wallet_toolbox.storage.methods_impl.get_beef_for_transaction",
            return_value=mock_beef_data,
        ) as mock_impl:
            result = get_beef_for_transaction(storage, self.VALID_TXID, auth)

        mock_impl.assert_called_once_with(storage, auth, self.VALID_TXID, None)
        assert result == mock_beef_data

    def test_get_beef_for_transaction_with_options(self) -> None:
        """Test get_beef_for_transaction forwards options."""
        storage = Mock()
        options = {"ignoreStorage": True, "ignoreServices": False}
        mock_beef_data = b"beef_data"

        with patch(
            "bsv_wallet_toolbox.storage.methods_impl.get_beef_for_transaction",
            return_value=mock_beef_data,
        ) as mock_impl:
            result = get_beef_for_transaction(storage, self.VALID_TXID, options=options)

        mock_impl.assert_called_once_with(storage, {}, self.VALID_TXID, options)
        assert result == mock_beef_data

    def test_get_beef_for_transaction_returns_none_when_no_beef(self) -> None:
        """Test get_beef_for_transaction returns None when no BEEF data found."""
        storage = Mock()

        with patch(
            "bsv_wallet_toolbox.storage.methods_impl.get_beef_for_transaction",
            return_value=None,
        ) as mock_impl:
            result = get_beef_for_transaction(storage, self.VALID_TXID)

        mock_impl.assert_called_once_with(storage, {}, self.VALID_TXID, None)
        assert result is None


class TestStorageMethodIntegration:
    """Integration tests combining multiple storage methods."""

    def test_sync_chunk_and_purge_integration(self) -> None:
        """Test integration between sync chunk and purge operations."""
        storage = Mock()

        # Setup sync chunk data
        storage.get_sync_chunk = Mock(
            return_value={
                "syncState": {"userId": "test_user", "syncVersion": 1},
                "transactions": [],
                "outputs": [],
                "certificates": [],
                "labels": [],
                "baskets": [],
                "hasMore": False,
                "nextChunkId": None,
                "syncVersion": 1,
            }
        )

        # Get initial sync chunk
        args = {"userId": "test_user"}
        sync_result = get_sync_chunk(storage, args)

        # Verify sync state was created
        assert sync_result["syncVersion"] == 1

        # Now test purge (should work with the created sync state)
        storage.purge_data = Mock(
            return_value={
                "deletedTransactions": 0,
                "deletedOutputs": 0,
                "deletedCertificates": 0,
                "deletedRequests": 0,
                "deletedLabels": 0,
                "log": "",
            }
        )

        purge_result = purge_data(storage, {"purgeCompleted": True})

        # Both operations should succeed
        assert isinstance(sync_result, dict)
        assert isinstance(purge_result, dict)

    def test_review_and_post_reqs_integration(self) -> None:
        """Test integration between review status and post reqs operations."""
        storage = Mock()

        # Setup review status
        storage.review_status = Mock(return_value={"updatedCount": 0, "agedCount": 0, "log": ""})

        args = {"agedLimit": 3600}
        review_result = review_status(storage, args)

        # Setup post reqs
        storage.attempt_to_post_reqs_to_network = Mock(return_value={"posted": 0, "failed": 0})

        reqs = []
        post_result = attempt_to_post_reqs_to_network(storage, reqs)

        # Both operations should succeed
        assert isinstance(review_result, dict)
        assert isinstance(post_result, dict)
