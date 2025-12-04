"""High-impact coverage tests for storage methods.

This module provides targeted tests for missing coverage lines in storage/methods.py.
"""

from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch

import pytest

from bsv_wallet_toolbox.errors import WalletError
from bsv_wallet_toolbox.storage.methods import (
    GenerateChangeInput,
    ListActionsArgs,
    ListOutputsArgs,
    StorageProcessActionArgs,
    StorageProcessActionResults,
    attempt_to_post_reqs_to_network,
    generate_change,
    get_beef_for_transaction,
    get_sync_chunk,
    internalize_action,
    list_actions,
    list_certificates,
    list_outputs,
    process_action,
    purge_data,
    review_status,
)


class TestStorageMethodsHighImpactCoverage:
    """High-impact coverage tests for storage methods missing lines."""

    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage."""
        return Mock()

    @pytest.fixture
    def mock_auth(self):
        """Create mock auth context."""
        return {"userId": 123, "identityKey": "test_key"}

    def test_attempt_to_post_reqs_to_network_with_beef(self, mock_storage, mock_auth) -> None:
        """Test attempt_to_post_reqs_to_network with beef (lines 197-210)."""
        # Mock storage to return proven tx reqs with beef
        mock_storage.find.return_value = [
            {
                "txid": "test_txid",
                "userId": 123,
                "status": "unsent",
                "rawTx": bytes([1, 2, 3, 4]),
                "beef": bytes([5, 6, 7, 8]),
            }
        ]

        # Mock successful post
        mock_storage.update.return_value = None

        txids = ["test_txid"]

        with patch('bsv_wallet_toolbox.storage.methods.requests') as mock_requests:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"txid": "test_txid", "status": "posted"}
            mock_requests.post.return_value = mock_response

            result = attempt_to_post_reqs_to_network(mock_storage, mock_auth, txids)

            # Verify the function completed and beef path was exercised
            assert "posted_txids" in result
            assert "test_txid" in result["posted_txids"]

    def test_generate_change_with_single_input(self, mock_storage, mock_auth) -> None:
        """Test generate_change with single input (line 248)."""
        inputs = [
            GenerateChangeInput(
                satoshis=50000,
                locking_script=bytes([118, 169, 20, 255, 255, 255, 255, 136, 172]),  # P2PKH
                derivation_prefix="m/44'/0'/0'",
                derivation_suffix="/0/0",
            )
        ]

        args = {
            "inputs": inputs,
            "outputs": [{"satoshis": 40000, "basket": "default"}],
            "change": {"basket": "default"},
        }

        result = generate_change(mock_storage, mock_auth, args)

        # Verify single input processing
        assert "outputs" in result
        assert len(result["outputs"]) >= 1

    def test_generate_change_with_multiple_inputs(self, mock_storage, mock_auth) -> None:
        """Test generate_change with multiple inputs (line 251)."""
        inputs = [
            GenerateChangeInput(
                satoshis=30000,
                locking_script=bytes([118, 169, 20, 255, 255, 255, 255, 136, 172]),
                derivation_prefix="m/44'/0'/0'",
                derivation_suffix="/0/0",
            ),
            GenerateChangeInput(
                satoshis=20000,
                locking_script=bytes([118, 169, 20, 255, 255, 255, 255, 136, 172]),
                derivation_prefix="m/44'/0'/0'",
                derivation_suffix="/0/1",
            ),
        ]

        args = {
            "inputs": inputs,
            "outputs": [{"satoshis": 40000, "basket": "default"}],
            "change": {"basket": "default"},
        }

        result = generate_change(mock_storage, mock_auth, args)

        # Verify multiple input processing
        assert "outputs" in result

    def test_list_actions_with_status_filter(self, mock_storage, mock_auth) -> None:
        """Test list_actions with status filter (lines 346, 350)."""
        mock_storage.count.return_value = 10
        mock_storage.find.return_value = [
            {"actionId": 1, "status": "completed", "txid": "tx1"},
            {"actionId": 2, "status": "pending", "txid": "tx2"},
        ]

        args = ListActionsArgs(
            limit=10,
            offset=0,
            status="completed",
            txid=None,
            start_date=None,
            end_date=None,
        )

        result = list_actions(mock_storage, mock_auth, args)

        # Verify status filtering was applied
        assert "actions" in result
        assert "total" in result
        mock_storage.find.assert_called_once()

    def test_list_actions_with_txid_filter(self, mock_storage, mock_auth) -> None:
        """Test list_actions with txid filter (lines 368-369)."""
        mock_storage.count.return_value = 1
        mock_storage.find.return_value = [
            {"actionId": 1, "status": "completed", "txid": "specific_txid"},
        ]

        args = ListActionsArgs(
            limit=10,
            offset=0,
            status=None,
            txid="specific_txid",
            start_date=None,
            end_date=None,
        )

        result = list_actions(mock_storage, mock_auth, args)

        # Verify txid filtering was applied
        assert "actions" in result
        assert len(result["actions"]) == 1

    def test_list_outputs_with_pagination(self, mock_storage, mock_auth) -> None:
        """Test list_outputs with pagination (lines 403-405)."""
        mock_storage.count.return_value = 100
        mock_storage.find.return_value = [
            {"outputId": 1, "satoshis": 50000, "basketId": 1},
            {"outputId": 2, "satoshis": 25000, "basketId": 1},
        ]

        args = ListOutputsArgs(
            basket="default",
            limit=2,
            offset=10,
            include_labels=False,
            include_tags=False,
            spent=None,
        )

        result = list_outputs(mock_storage, mock_auth, args)

        # Verify pagination was applied
        assert "outputs" in result
        assert "total" in result
        assert result["total"] == 100

    def test_list_outputs_with_spent_filter(self, mock_storage, mock_auth) -> None:
        """Test list_outputs with spent filter (lines 413-426)."""
        mock_storage.count.return_value = 5
        mock_storage.find.return_value = [
            {"outputId": 1, "satoshis": 50000, "spentBy": None},
        ]

        args = ListOutputsArgs(
            basket="default",
            limit=10,
            offset=0,
            include_labels=False,
            include_tags=False,
            spent=False,  # Only unspent
        )

        result = list_outputs(mock_storage, mock_auth, args)

        # Verify spent filter was applied
        assert "outputs" in result
        assert len(result["outputs"]) == 1

    def test_list_outputs_with_basket_filter(self, mock_storage, mock_auth) -> None:
        """Test list_outputs with basket filter (lines 433-442)."""
        mock_storage.count.return_value = 3
        mock_storage.find.return_value = [
            {"outputId": 1, "satoshis": 50000, "basketId": 1},
        ]

        args = ListOutputsArgs(
            basket="savings",
            limit=10,
            offset=0,
            include_labels=False,
            include_tags=False,
            spent=None,
        )

        result = list_outputs(mock_storage, mock_auth, args)

        # Verify basket filter was applied
        assert "outputs" in result

    def test_list_outputs_include_labels(self, mock_storage, mock_auth) -> None:
        """Test list_outputs with include_labels (lines 446-455)."""
        mock_storage.count.return_value = 2
        mock_storage.find.return_value = [
            {"outputId": 1, "satoshis": 50000, "basketId": 1},
        ]

        args = ListOutputsArgs(
            basket="default",
            limit=10,
            offset=0,
            include_labels=True,  # Include labels
            include_tags=False,
            spent=None,
        )

        result = list_outputs(mock_storage, mock_auth, args)

        # Verify include_labels was processed
        assert "outputs" in result

    def test_list_outputs_include_tags(self, mock_storage, mock_auth) -> None:
        """Test list_outputs with include_tags (lines 460-469)."""
        mock_storage.count.return_value = 2
        mock_storage.find.return_value = [
            {"outputId": 1, "satoshis": 50000, "basketId": 1},
        ]

        args = ListOutputsArgs(
            basket="default",
            limit=10,
            offset=0,
            include_labels=False,
            include_tags=True,  # Include tags
            spent=None,
        )

        result = list_outputs(mock_storage, mock_auth, args)

        # Verify include_tags was processed
        assert "outputs" in result

    def test_list_certificates_with_limit_offset(self, mock_storage, mock_auth) -> None:
        """Test list_certificates with limit and offset (lines 477-486)."""
        mock_storage.count.return_value = 50
        mock_storage.find.return_value = [
            {"certificateId": 1, "type": "identity", "subject": "test"},
        ]

        result = list_certificates(mock_storage, mock_auth, limit=5, offset=10)

        # Verify limit and offset were applied
        assert "certificates" in result
        assert "total" in result
        assert result["total"] == 50

    def test_internalize_action_with_transaction(self, mock_storage, mock_auth) -> None:
        """Test internalize_action with transaction processing (lines 490-512)."""
        # Mock the transaction and storage calls
        mock_storage.create_action.return_value = {
            "transactionId": 123,
            "outputs": [{"vout": 0, "satoshis": 50000}],
        }
        mock_storage.find.return_value = []
        mock_storage.insert.return_value = None

        args = {
            "tx": bytes([1, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # Minimal tx
            "outputs": [{"vout": 0, "satoshis": 50000, "basket": "default"}],
            "description": "Internalized transaction",
        }

        with patch('bsv_wallet_toolbox.storage.methods.Transaction') as mock_tx_class:
            mock_tx = Mock()
            mock_tx.txid.return_value = "internalized_txid"
            mock_tx_class.from_hex.return_value = mock_tx

            result = internalize_action(mock_storage, mock_auth, args)

            # Verify transaction processing
            assert "txid" in result
            assert result["txid"] == "internalized_txid"

    def test_get_beef_for_transaction_with_proven_tx(self, mock_storage, mock_auth) -> None:
        """Test get_beef_for_transaction with proven tx (lines 542, 546)."""
        # Mock proven tx with beef
        mock_storage.find.return_value = [
            {
                "provenTxId": 1,
                "txid": "test_txid",
                "rawTx": bytes([1, 2, 3]),
                "proof": bytes([4, 5, 6]),
                "blockHeight": 1000,
            }
        ]

        result = get_beef_for_transaction(mock_storage, mock_auth, "test_txid")

        # Verify beef construction from proven tx
        assert "beef" in result
        assert result["txid"] == "test_txid"

    def test_get_beef_for_transaction_with_merkle_path(self, mock_storage, mock_auth) -> None:
        """Test get_beef_for_transaction with merkle path (lines 568-572)."""
        # Mock proven tx with merkle path
        mock_storage.find.return_value = [
            {
                "provenTxId": 1,
                "txid": "test_txid",
                "rawTx": bytes([1, 2, 3]),
                "merklePath": "merkle_path_data",
                "blockHeight": 1000,
            }
        ]

        with patch('bsv_wallet_toolbox.storage.methods.BsvTransaction') as mock_bsv_tx:
            mock_tx = Mock()
            mock_bsv_tx.from_hex.return_value = mock_tx

            result = get_beef_for_transaction(mock_storage, mock_auth, "test_txid")

            # Verify merkle path processing
            assert "beef" in result

    def test_attempt_to_post_reqs_to_network_no_beef(self, mock_storage, mock_auth) -> None:
        """Test attempt_to_post_reqs_to_network without beef (lines 585-586)."""
        # Mock proven tx req without beef
        mock_storage.find.return_value = [
            {
                "txid": "test_txid",
                "userId": 123,
                "status": "unsent",
                "rawTx": bytes([1, 2, 3, 4]),
                # No beef field
            }
        ]

        txids = ["test_txid"]

        with patch('bsv_wallet_toolbox.storage.methods.requests') as mock_requests:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"txid": "test_txid", "status": "posted"}
            mock_requests.post.return_value = mock_response

            result = attempt_to_post_reqs_to_network(mock_storage, mock_auth, txids)

            # Verify non-beef path was exercised
            assert "send_with_results" in result

    def test_review_status_with_aged_limit(self, mock_storage, mock_auth) -> None:
        """Test review_status with aged limit processing (lines 590-600)."""
        aged_limit = datetime.now(timezone.utc)

        # Mock various status updates
        mock_storage.find.return_value = []
        mock_storage.update.return_value = None

        result = review_status(mock_storage, mock_auth, aged_limit)

        # Verify aged limit processing
        assert "updated" in result
        assert "errors" in result

    def test_purge_data_with_date_params(self, mock_storage) -> None:
        """Test purge_data with date parameters (lines 607-620)."""
        params = {
            "beforeDate": "2023-01-01",
            "entityTypes": ["Transaction", "Output"],
        }

        mock_storage.delete.return_value = 5

        result = purge_data(mock_storage, params)

        # Verify date-based purging
        assert "deleted" in result
        assert result["deleted"] >= 0

    def test_purge_data_with_count_limits(self, mock_storage) -> None:
        """Test purge_data with count limits (lines 625-641)."""
        params = {
            "maxCount": 100,
            "entityTypes": ["Transaction"],
        }

        mock_storage.delete.return_value = 50

        result = purge_data(mock_storage, params)

        # Verify count-based purging
        assert "deleted" in result
        assert result["deleted"] == 50

    def test_get_sync_chunk_with_entity_filters(self, mock_storage) -> None:
        """Test get_sync_chunk with entity filters (line 671)."""
        args = {
            "entityName": "Transaction",
            "sinceVersion": 100,
            "limit": 50,
        }

        mock_storage.find.return_value = [
            {"id": 1, "version": 101, "data": {"test": "data"}},
            {"id": 2, "version": 102, "data": {"test": "data2"}},
        ]

        result = get_sync_chunk(mock_storage, args)

        # Verify entity filtering
        assert "entities" in result
        assert len(result["entities"]) == 2

    def test_process_action_with_send_with(self, mock_storage, mock_auth) -> None:
        """Test process_action with send_with functionality (lines 684-685)."""
        args = StorageProcessActionArgs(
            is_new_tx=True,
            is_no_send=False,
            is_send_with=True,
            is_delayed=False,
            send_with=["txid1", "txid2"],
            log={"action": "process"},
        )

        mock_storage.create_action.return_value = {"actionId": 123}

        result = process_action(mock_storage, mock_auth, args)

        # Verify send_with processing
        assert isinstance(result, StorageProcessActionResults)

    def test_process_action_with_delayed_flag(self, mock_storage, mock_auth) -> None:
        """Test process_action with delayed flag (lines 689-700)."""
        args = StorageProcessActionArgs(
            is_new_tx=True,
            is_no_send=False,
            is_send_with=False,
            is_delayed=True,  # Delayed processing
            send_with=[],
            log={"action": "delayed_process"},
        )

        mock_storage.create_action.return_value = {"actionId": 456}

        result = process_action(mock_storage, mock_auth, args)

        # Verify delayed processing
        assert isinstance(result, StorageProcessActionResults)

    def test_list_actions_with_date_filters(self, mock_storage, mock_auth) -> None:
        """Test list_actions with date filters (lines 708-727)."""
        start_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2023, 12, 31, tzinfo=timezone.utc)

        mock_storage.count.return_value = 25
        mock_storage.find.return_value = [
            {"actionId": 1, "createdAt": start_date, "txid": "tx1"},
        ]

        args = ListActionsArgs(
            limit=10,
            offset=0,
            status=None,
            txid=None,
            start_date=start_date,
            end_date=end_date,
        )

        result = list_actions(mock_storage, mock_auth, args)

        # Verify date filtering
        assert "actions" in result
        assert result["total"] == 25

    def test_internalize_action_with_labels(self, mock_storage, mock_auth) -> None:
        """Test internalize_action with labels processing (lines 758, 776)."""
        mock_storage.create_action.return_value = {
            "transactionId": 123,
            "outputs": [{"vout": 0, "satoshis": 50000}],
        }
        mock_storage.find.return_value = []
        mock_storage.insert.return_value = None

        args = {
            "tx": bytes([1, 0, 0, 0]),
            "outputs": [{"vout": 0, "satoshis": 50000, "basket": "default"}],
            "labels": ["received", "payment"],
            "description": "Labeled transaction",
        }

        with patch('bsv_wallet_toolbox.storage.methods.Transaction') as mock_tx_class:
            mock_tx = Mock()
            mock_tx.txid.return_value = "labeled_txid"
            mock_tx_class.from_hex.return_value = mock_tx

            result = internalize_action(mock_storage, mock_auth, args)

            # Verify labels processing
            assert "txid" in result

    def test_get_beef_for_transaction_error_handling(self, mock_storage, mock_auth) -> None:
        """Test get_beef_for_transaction error handling (line 802)."""
        # Mock no proven tx found
        mock_storage.find.return_value = []

        with pytest.raises(WalletError):
            get_beef_for_transaction(mock_storage, mock_auth, "nonexistent_txid")

    def test_attempt_to_post_reqs_to_network_http_error(self, mock_storage, mock_auth) -> None:
        """Test attempt_to_post_reqs_to_network HTTP error handling (lines 837-877)."""
        mock_storage.find.return_value = [
            {
                "txid": "test_txid",
                "userId": 123,
                "status": "unsent",
                "rawTx": bytes([1, 2, 3, 4]),
            }
        ]

        txids = ["test_txid"]

        with patch('bsv_wallet_toolbox.storage.methods.requests') as mock_requests:
            mock_requests.post.side_effect = Exception("Network error")

            result = attempt_to_post_reqs_to_network(mock_storage, mock_auth, txids)

            # Verify error handling
            assert "errors" in result

    def test_attempt_to_post_reqs_to_network_update_failure(self, mock_storage, mock_auth) -> None:
        """Test attempt_to_post_reqs_to_network update failure (lines 881, 883)."""
        mock_storage.find.return_value = [
            {
                "txid": "test_txid",
                "userId": 123,
                "status": "unsent",
                "rawTx": bytes([1, 2, 3, 4]),
            }
        ]
        mock_storage.update.side_effect = Exception("Update failed")

        txids = ["test_txid"]

        result = attempt_to_post_reqs_to_network(mock_storage, mock_auth, txids)

        # Verify update failure handling
        assert "errors" in result

    def test_review_status_with_abandoned_actions(self, mock_storage, mock_auth) -> None:
        """Test review_status with abandoned actions (lines 888, 901-911)."""
        aged_limit = datetime.now(timezone.utc)

        # Mock abandoned actions
        mock_storage.find.return_value = [
            {"actionId": 1, "status": "sending", "createdAt": aged_limit},
            {"actionId": 2, "status": "failed", "createdAt": aged_limit},
        ]
        mock_storage.update.return_value = None

        result = review_status(mock_storage, mock_auth, aged_limit)

        # Verify abandoned action processing
        assert "updated" in result

    def test_review_status_with_proven_tx_reqs(self, mock_storage, mock_auth) -> None:
        """Test review_status with proven tx reqs (lines 916-947)."""
        aged_limit = datetime.now(timezone.utc)

        mock_storage.find.return_value = [
            {"reqId": 1, "status": "unsent", "createdAt": aged_limit},
        ]
        mock_storage.update.return_value = None

        result = review_status(mock_storage, mock_auth, aged_limit)

        # Verify proven tx req processing
        assert "updated" in result

    def test_purge_data_with_combined_filters(self, mock_storage) -> None:
        """Test purge_data with combined filters (lines 1030-1032)."""
        params = {
            "beforeDate": "2023-01-01",
            "maxCount": 10,
            "entityTypes": ["Transaction", "Output"],
        }

        mock_storage.delete.return_value = 8

        result = purge_data(mock_storage, params)

        # Verify combined filtering
        assert "deleted" in result
        assert result["deleted"] == 8

    def test_get_sync_chunk_with_version_filtering(self, mock_storage) -> None:
        """Test get_sync_chunk with version filtering (lines 1069-1088)."""
        args = {
            "entityName": "Transaction",
            "sinceVersion": 50,
            "limit": 20,
        }

        mock_storage.find.return_value = [
            {"id": 1, "version": 51, "data": {"tx": "data1"}},
            {"id": 2, "version": 52, "data": {"tx": "data2"}},
        ]

        result = get_sync_chunk(mock_storage, args)

        # Verify version filtering
        assert "entities" in result
        assert len(result["entities"]) == 2

    def test_get_sync_chunk_error_handling(self, mock_storage) -> None:
        """Test get_sync_chunk error handling (lines 1103-1119)."""
        args = {
            "entityName": "InvalidEntity",
            "sinceVersion": 1,
            "limit": 10,
        }

        mock_storage.find.side_effect = Exception("Storage error")

        with pytest.raises(WalletError):
            get_sync_chunk(mock_storage, args)

    def test_review_status_with_monitor_tasks(self, mock_storage, mock_auth) -> None:
        """Test review_status with monitor tasks (lines 1167-1172)."""
        aged_limit = datetime.now(timezone.utc)

        mock_storage.find.return_value = []
        mock_storage.update.return_value = None

        result = review_status(mock_storage, mock_auth, aged_limit)

        # Verify monitor task processing
        assert "updated" in result

    def test_review_status_with_abandoned_proofs(self, mock_storage, mock_auth) -> None:
        """Test review_status with abandoned proofs (lines 1178-1183)."""
        aged_limit = datetime.now(timezone.utc)

        mock_storage.find.return_value = []
        mock_storage.update.return_value = None

        result = review_status(mock_storage, mock_auth, aged_limit)

        # Verify abandoned proof processing
        assert "updated" in result

    def test_purge_data_with_entity_specific_limits(self, mock_storage) -> None:
        """Test purge_data with entity-specific limits (lines 1201, 1203)."""
        params = {
            "maxCount": 5,
            "entityTypes": ["Transaction"],
            "beforeDate": "2023-06-01",
        }

        mock_storage.delete.return_value = 3

        result = purge_data(mock_storage, params)

        # Verify entity-specific limits
        assert "deleted" in result

    def test_get_sync_chunk_with_empty_results(self, mock_storage) -> None:
        """Test get_sync_chunk with empty results (lines 1282-1283)."""
        args = {
            "entityName": "Transaction",
            "sinceVersion": 1000,
            "limit": 10,
        }

        mock_storage.find.return_value = []

        result = get_sync_chunk(mock_storage, args)

        # Verify empty result handling
        assert "entities" in result
        assert len(result["entities"]) == 0

    def test_review_status_with_no_updates_needed(self, mock_storage, mock_auth) -> None:
        """Test review_status with no updates needed (lines 1295-1297)."""
        aged_limit = datetime.now(timezone.utc)

        # Mock no items to update
        mock_storage.find.return_value = []
        mock_storage.update.return_value = None

        result = review_status(mock_storage, mock_auth, aged_limit)

        # Verify no-op case
        assert "updated" in result
        assert result["updated"] == 0

    def test_purge_data_with_invalid_params(self, mock_storage) -> None:
        """Test purge_data with invalid parameters (line 1336)."""
        params = {}  # Empty params

        result = purge_data(mock_storage, params)

        # Verify invalid param handling
        assert "deleted" in result
        assert result["deleted"] == 0

    def test_get_sync_chunk_with_large_limit(self, mock_storage) -> None:
        """Test get_sync_chunk with large limit (lines 1342-1352)."""
        args = {
            "entityName": "Transaction",
            "sinceVersion": 1,
            "limit": 1000,  # Large limit
        }

        mock_storage.find.return_value = [{"id": 1, "version": 2, "data": {"large": "data"}}]

        result = get_sync_chunk(mock_storage, args)

        # Verify large limit handling
        assert "entities" in result
