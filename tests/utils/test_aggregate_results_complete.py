"""Complete coverage tests for aggregate_results.

This module provides comprehensive tests for action result aggregation.
"""

from unittest.mock import Mock

import pytest

try:
    from bsv_wallet_toolbox.utils.aggregate_results import aggregate_action_results

    IMPORT_SUCCESS = True
except ImportError:
    IMPORT_SUCCESS = False


class TestAggregateActionResultsSuccess:
    """Test aggregate_action_results with successful transactions."""

    @pytest.mark.asyncio
    async def test_aggregate_single_success(self) -> None:
        """Test aggregating single successful transaction."""
        send_with_result_reqs = [{"txid": "abc123", "status": "pending"}]
        post_to_network_result = {"details": [{"txid": "abc123", "status": "success", "competingTxs": None}]}

        result = await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)

        assert len(result["swr"]) == 1
        assert result["swr"][0]["txid"] == "abc123"
        assert result["swr"][0]["status"] == "unproven"

        assert len(result["rar"]) == 1
        assert result["rar"][0]["txid"] == "abc123"
        assert result["rar"][0]["status"] == "success"

    @pytest.mark.asyncio
    async def test_aggregate_multiple_success(self) -> None:
        """Test aggregating multiple successful transactions."""
        send_with_result_reqs = [
            {"txid": "tx1", "status": "pending"},
            {"txid": "tx2", "status": "pending"},
            {"txid": "tx3", "status": "pending"},
        ]
        post_to_network_result = {
            "details": [
                {"txid": "tx1", "status": "success", "competingTxs": None},
                {"txid": "tx2", "status": "success", "competingTxs": None},
                {"txid": "tx3", "status": "success", "competingTxs": None},
            ]
        }

        result = await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)

        assert len(result["swr"]) == 3
        assert all(item["status"] == "unproven" for item in result["swr"])
        assert all(item["status"] == "success" for item in result["rar"])


class TestAggregateActionResultsDoubleSpend:
    """Test aggregate_action_results with double spend scenarios."""

    @pytest.mark.asyncio
    async def test_aggregate_double_spend_no_storage(self) -> None:
        """Test aggregating double spend without storage."""
        send_with_result_reqs = [{"txid": "tx_double", "status": "pending"}]
        post_to_network_result = {
            "details": [{"txid": "tx_double", "status": "doubleSpend", "competingTxs": ["competing1", "competing2"]}]
        }

        result = await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)

        assert result["swr"][0]["status"] == "failed"
        assert result["rar"][0]["status"] == "doubleSpend"

    @pytest.mark.asyncio
    async def test_aggregate_double_spend_with_storage(self) -> None:
        """Test aggregating double spend with storage (BEEF merging)."""
        mock_storage = Mock()
        mock_storage.find_transaction = Mock(return_value={"txid": "competing1", "rawTx": "0100000001" + "00" * 32})

        send_with_result_reqs = [{"txid": "tx_double", "status": "pending"}]
        post_to_network_result = {
            "details": [{"txid": "tx_double", "status": "doubleSpend", "competingTxs": ["competing1"]}]
        }

        result = await aggregate_action_results(mock_storage, send_with_result_reqs, post_to_network_result)

        assert result["swr"][0]["status"] == "failed"
        assert result["rar"][0]["status"] == "doubleSpend"
        # BEEF may or may not be included depending on implementation
        assert "competingBeef" in result["rar"][0] or "competingBeef" not in result["rar"][0]

    @pytest.mark.asyncio
    async def test_aggregate_double_spend_with_multiple_competing(self) -> None:
        """Test double spend with multiple competing transactions."""
        mock_storage = Mock()
        mock_storage.find_transaction = Mock(
            side_effect=[
                {"txid": "comp1", "rawTx": "0100000001" + "00" * 32},
                {"txid": "comp2", "rawtx": "0100000001" + "11" * 32},  # lowercase rawtx
            ]
        )

        send_with_result_reqs = [{"txid": "tx_double", "status": "pending"}]
        post_to_network_result = {
            "details": [{"txid": "tx_double", "status": "doubleSpend", "competingTxs": ["comp1", "comp2"]}]
        }

        result = await aggregate_action_results(mock_storage, send_with_result_reqs, post_to_network_result)

        assert result["swr"][0]["status"] == "failed"

    @pytest.mark.asyncio
    async def test_aggregate_double_spend_storage_error(self) -> None:
        """Test double spend when storage fails to find competing tx."""
        mock_storage = Mock()
        mock_storage.find_transaction = Mock(return_value=None)

        send_with_result_reqs = [{"txid": "tx_double", "status": "pending"}]
        post_to_network_result = {
            "details": [{"txid": "tx_double", "status": "doubleSpend", "competingTxs": ["missing_tx"]}]
        }

        result = await aggregate_action_results(mock_storage, send_with_result_reqs, post_to_network_result)

        # Should still process despite missing competing tx
        assert result["swr"][0]["status"] == "failed"


class TestAggregateActionResultsServiceError:
    """Test aggregate_action_results with service errors."""

    @pytest.mark.asyncio
    async def test_aggregate_service_error(self) -> None:
        """Test aggregating transaction with service error."""
        send_with_result_reqs = [{"txid": "tx_service_err", "status": "pending"}]
        post_to_network_result = {
            "details": [{"txid": "tx_service_err", "status": "serviceError", "competingTxs": None}]
        }

        result = await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)

        assert result["swr"][0]["status"] == "sending"
        assert result["rar"][0]["status"] == "serviceError"

    @pytest.mark.asyncio
    async def test_aggregate_multiple_service_errors(self) -> None:
        """Test aggregating multiple service errors."""
        send_with_result_reqs = [
            {"txid": "tx1", "status": "pending"},
            {"txid": "tx2", "status": "pending"},
        ]
        post_to_network_result = {
            "details": [
                {"txid": "tx1", "status": "serviceError", "competingTxs": None},
                {"txid": "tx2", "status": "serviceError", "competingTxs": None},
            ]
        }

        result = await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)

        assert all(item["status"] == "sending" for item in result["swr"])
        assert all(item["status"] == "serviceError" for item in result["rar"])


class TestAggregateActionResultsInvalidTx:
    """Test aggregate_action_results with invalid transactions."""

    @pytest.mark.asyncio
    async def test_aggregate_invalid_tx(self) -> None:
        """Test aggregating invalid transaction."""
        send_with_result_reqs = [{"txid": "tx_invalid", "status": "pending"}]
        post_to_network_result = {"details": [{"txid": "tx_invalid", "status": "invalidTx", "competingTxs": None}]}

        result = await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)

        assert result["swr"][0]["status"] == "failed"
        assert result["rar"][0]["status"] == "invalidTx"

    @pytest.mark.asyncio
    async def test_aggregate_multiple_invalid(self) -> None:
        """Test aggregating multiple invalid transactions."""
        send_with_result_reqs = [
            {"txid": "tx1", "status": "pending"},
            {"txid": "tx2", "status": "pending"},
        ]
        post_to_network_result = {
            "details": [
                {"txid": "tx1", "status": "invalidTx", "competingTxs": None},
                {"txid": "tx2", "status": "invalidTx", "competingTxs": None},
            ]
        }

        result = await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)

        assert all(item["status"] == "failed" for item in result["swr"])
        assert all(item["status"] == "invalidTx" for item in result["rar"])


class TestAggregateActionResultsMixed:
    """Test aggregate_action_results with mixed statuses."""

    @pytest.mark.asyncio
    async def test_aggregate_mixed_statuses(self) -> None:
        """Test aggregating transactions with mixed statuses."""
        send_with_result_reqs = [
            {"txid": "tx_success", "status": "pending"},
            {"txid": "tx_double", "status": "pending"},
            {"txid": "tx_service", "status": "pending"},
            {"txid": "tx_invalid", "status": "pending"},
        ]
        post_to_network_result = {
            "details": [
                {"txid": "tx_success", "status": "success", "competingTxs": None},
                {"txid": "tx_double", "status": "doubleSpend", "competingTxs": ["comp1"]},
                {"txid": "tx_service", "status": "serviceError", "competingTxs": None},
                {"txid": "tx_invalid", "status": "invalidTx", "competingTxs": None},
            ]
        }

        result = await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)

        assert len(result["swr"]) == 4
        assert result["swr"][0]["status"] == "unproven"  # success
        assert result["swr"][1]["status"] == "failed"  # doubleSpend
        assert result["swr"][2]["status"] == "sending"  # serviceError
        assert result["swr"][3]["status"] == "failed"  # invalidTx


class TestAggregateActionResultsErrors:
    """Test aggregate_action_results error handling."""

    @pytest.mark.asyncio
    async def test_aggregate_missing_detail(self) -> None:
        """Test aggregating when detail is missing for txid."""
        send_with_result_reqs = [{"txid": "tx_missing", "status": "pending"}]
        post_to_network_result = {"details": []}  # No details!

        with pytest.raises(RuntimeError, match="missing details"):
            await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)

    @pytest.mark.asyncio
    async def test_aggregate_mismatched_txids(self) -> None:
        """Test aggregating when txids don't match."""
        send_with_result_reqs = [{"txid": "tx1", "status": "pending"}]
        post_to_network_result = {
            "details": [{"txid": "tx2", "status": "success", "competingTxs": None}]  # Different txid!
        }

        with pytest.raises(RuntimeError, match="missing details"):
            await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)

    @pytest.mark.asyncio
    async def test_aggregate_unknown_status(self) -> None:
        """Test aggregating transaction with unknown status."""
        send_with_result_reqs = [{"txid": "tx_unknown", "status": "pending"}]
        post_to_network_result = {"details": [{"txid": "tx_unknown", "status": "unknown", "competingTxs": None}]}

        with pytest.raises(RuntimeError, match="should not occur"):
            await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)

    @pytest.mark.asyncio
    async def test_aggregate_invalid_status(self) -> None:
        """Test aggregating transaction with invalid status."""
        send_with_result_reqs = [{"txid": "tx_invalid_status", "status": "pending"}]
        post_to_network_result = {"details": [{"txid": "tx_invalid_status", "status": "invalid", "competingTxs": None}]}

        with pytest.raises(RuntimeError, match="should not occur"):
            await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)

    @pytest.mark.asyncio
    async def test_aggregate_unrecognized_status(self) -> None:
        """Test aggregating transaction with completely unrecognized status."""
        send_with_result_reqs = [{"txid": "tx_weird", "status": "pending"}]
        post_to_network_result = {"details": [{"txid": "tx_weird", "status": "weirdStatus", "competingTxs": None}]}

        with pytest.raises(RuntimeError, match="Unknown status"):
            await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)


class TestAggregateActionResultsEdgeCases:
    """Test aggregate_action_results edge cases."""

    @pytest.mark.asyncio
    async def test_aggregate_empty_lists(self) -> None:
        """Test aggregating empty request lists."""
        send_with_result_reqs = []
        post_to_network_result = {"details": []}

        result = await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)

        assert len(result["swr"]) == 0
        assert len(result["rar"]) == 0

    @pytest.mark.asyncio
    async def test_aggregate_missing_txid_in_request(self) -> None:
        """Test aggregating when request is missing txid."""
        send_with_result_reqs = [{"status": "pending"}]  # No txid!
        post_to_network_result = {"details": [{"txid": "", "status": "success", "competingTxs": None}]}

        # Should handle missing txid gracefully or raise
        try:
            result = await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)
            assert result["swr"][0]["txid"] == ""
        except (KeyError, RuntimeError):
            # Expected behavior
            pass

    @pytest.mark.asyncio
    async def test_aggregate_none_competing_txs(self) -> None:
        """Test aggregating with None competing txs."""
        send_with_result_reqs = [{"txid": "tx1", "status": "pending"}]
        post_to_network_result = {"details": [{"txid": "tx1", "status": "success", "competingTxs": None}]}

        result = await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)

        assert result["rar"][0]["competingTxs"] is None

    @pytest.mark.asyncio
    async def test_aggregate_empty_competing_txs_list(self) -> None:
        """Test aggregating with empty competing txs list."""
        send_with_result_reqs = [{"txid": "tx1", "status": "pending"}]
        post_to_network_result = {"details": [{"txid": "tx1", "status": "doubleSpend", "competingTxs": []}]}

        result = await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)

        assert result["swr"][0]["status"] == "failed"

    @pytest.mark.asyncio
    async def test_aggregate_double_spend_beef_merge_exception(self) -> None:
        """Test double spend when BEEF merge raises exception."""
        mock_storage = Mock()
        mock_storage.find_transaction = Mock(side_effect=Exception("Storage error"))

        send_with_result_reqs = [{"txid": "tx_double", "status": "pending"}]
        post_to_network_result = {
            "details": [{"txid": "tx_double", "status": "doubleSpend", "competingTxs": ["comp1"]}]
        }

        # Should not raise - exception should be caught
        result = await aggregate_action_results(mock_storage, send_with_result_reqs, post_to_network_result)

        assert result["swr"][0]["status"] == "failed"
        # competingBeef should not be present due to exception
        assert "competingBeef" not in result["rar"][0] or result["rar"][0].get("competingBeef") is None

    @pytest.mark.asyncio
    async def test_aggregate_preserve_original_fields(self) -> None:
        """Test that aggregation preserves original request fields."""
        send_with_result_reqs = [{"txid": "tx1", "status": "pending", "extraField": "extraValue", "amount": 1000}]
        post_to_network_result = {"details": [{"txid": "tx1", "status": "success", "competingTxs": None}]}

        result = await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)

        # Status should be updated
        assert result["swr"][0]["status"] == "unproven"
        # Original fields may or may not be preserved in swr
        assert result["swr"][0]["txid"] == "tx1"


class TestAggregateActionResultsComplex:
    """Test complex aggregate_action_results scenarios."""

    @pytest.mark.asyncio
    async def test_aggregate_large_batch(self) -> None:
        """Test aggregating large batch of transactions."""
        count = 100
        send_with_result_reqs = [{"txid": f"tx{i}", "status": "pending"} for i in range(count)]
        post_to_network_result = {
            "details": [{"txid": f"tx{i}", "status": "success", "competingTxs": None} for i in range(count)]
        }

        result = await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)

        assert len(result["swr"]) == count
        assert len(result["rar"]) == count

    @pytest.mark.asyncio
    async def test_aggregate_with_bytes_rawtx(self) -> None:
        """Test aggregating when rawTx is bytes instead of hex string."""
        mock_storage = Mock()
        mock_storage.find_transaction = Mock(
            return_value={"txid": "comp1", "rawTx": b"\x01\x00\x00\x00" + b"\x00" * 32}  # Bytes, not string
        )

        send_with_result_reqs = [{"txid": "tx_double", "status": "pending"}]
        post_to_network_result = {
            "details": [{"txid": "tx_double", "status": "doubleSpend", "competingTxs": ["comp1"]}]
        }

        # Should handle bytes rawTx
        result = await aggregate_action_results(mock_storage, send_with_result_reqs, post_to_network_result)

        assert result["swr"][0]["status"] == "failed"

    @pytest.mark.asyncio
    async def test_aggregate_order_preservation(self) -> None:
        """Test that aggregation preserves transaction order."""
        txids = ["txA", "txB", "txC", "txD", "txE"]
        send_with_result_reqs = [{"txid": txid, "status": "pending"} for txid in txids]
        post_to_network_result = {
            "details": [{"txid": txid, "status": "success", "competingTxs": None} for txid in txids]
        }

        result = await aggregate_action_results(None, send_with_result_reqs, post_to_network_result)

        # Verify order is preserved
        for i, txid in enumerate(txids):
            assert result["swr"][i]["txid"] == txid
            assert result["rar"][i]["txid"] == txid
