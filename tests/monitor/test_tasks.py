"""Unit tests for Monitor Task classes.

These tests verify the logic of individual monitor tasks in isolation,
mocking the Monitor dependency to focus on task behavior.
"""

import time
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from bsv_wallet_toolbox.monitor.tasks import (
    TaskCheckForProofs,
    TaskClock,
    TaskFailAbandoned,
    TaskMonitorCallHistory,
    TaskNewHeader,
    TaskPurge,
    TaskReorg,
    TaskReviewStatus,
    TaskSendWaiting,
    TaskSyncWhenIdle,
    TaskUnFail,
)
from bsv_wallet_toolbox.monitor.tasks.task_check_no_sends import TaskCheckNoSends


class TestTaskClock:
    """Test TaskClock functionality."""

    def test_task_clock_initialization(self) -> None:
        """Test TaskClock initializes correctly."""
        mock_monitor = MagicMock()
        task = TaskClock(mock_monitor)

        assert task.name == "Clock"
        assert task.monitor == mock_monitor

    def test_task_clock_trigger_every_minute(self) -> None:
        """Test TaskClock triggers every 60 seconds based on next_minute logic."""
        mock_monitor = MagicMock()
        task = TaskClock(mock_monitor)

        # TaskClock uses next_minute logic, not last_run_msecs_since_epoch
        # next_minute is initialized to the next minute boundary

        # Trigger before next_minute should not run
        current_time = int(time.time() * 1000)
        next_minute = task.next_minute
        if current_time < next_minute:
            result = task.trigger(current_time)
            assert result["run"] is False

        # Trigger after next_minute should run
        result = task.trigger(next_minute + 1000)  # 1 second after next_minute
        assert result["run"] is True

        # After run_task updates next_minute, trigger should not run until next boundary
        task.run_task()  # This updates next_minute to next boundary
        result = task.trigger(task.next_minute - 1000)  # Before new next_minute
        assert result["run"] is False

    def test_task_clock_run_task(self) -> None:
        """Test TaskClock run_task returns ISO timestamp string."""
        mock_monitor = MagicMock()
        task = TaskClock(mock_monitor)

        result = task.run_task()
        # Should return ISO timestamp format like "2025-12-02T08:51:00"
        assert "T" in result  # ISO format has T separator
        assert ":" in result  # Time has colons
        assert "-" in result  # Date has dashes
        assert isinstance(result, str)


class TestTaskNewHeader:
    """Test TaskNewHeader functionality."""

    def test_task_new_header_initialization(self) -> None:
        """Test TaskNewHeader initializes correctly."""
        mock_monitor = MagicMock()
        task = TaskNewHeader(mock_monitor)

        assert task.name == "NewHeader"
        assert task.monitor == mock_monitor
        assert task.check_now is False

    def test_task_new_header_trigger(self) -> None:
        """Test TaskNewHeader trigger logic."""
        mock_monitor = MagicMock()
        task = TaskNewHeader(mock_monitor)

        # Initially should not run
        result = task.trigger(0)
        assert result["run"] is False

        # When check_now is set, should run
        task.check_now = True
        result = task.trigger(0)
        assert result["run"] is True

    def test_task_new_header_run_task_no_header(self) -> None:
        """Test TaskNewHeader run_task with no header."""
        mock_monitor = MagicMock()
        mock_monitor.last_new_header = None
        mock_monitor._tasks = []

        task = TaskNewHeader(mock_monitor)
        result = task.run_task()

        assert result == ""
        assert task.check_now is False

    def test_task_new_header_run_task_with_header(self) -> None:
        """Test TaskNewHeader run_task with header."""
        mock_monitor = MagicMock()
        mock_monitor.last_new_header = {"height": 100, "hash": "abc123"}
        mock_monitor._tasks = []

        task = TaskNewHeader(mock_monitor)
        result = task.run_task()

        assert "Processing new header 100 abc123" in result
        assert task.check_now is False

    def test_task_new_header_run_task_triggers_proof_check(self) -> None:
        """Test TaskNewHeader triggers TaskCheckForProofs."""
        from bsv_wallet_toolbox.monitor.tasks.task_check_for_proofs import TaskCheckForProofs

        mock_monitor = MagicMock()
        mock_monitor.last_new_header = {"height": 100, "hash": "abc123"}

        # Create mock proof check task
        proof_task = MagicMock(spec=TaskCheckForProofs)
        proof_task.check_now = False

        mock_monitor._tasks = [proof_task]

        task = TaskNewHeader(mock_monitor)
        result = task.run_task()

        assert "Triggered TaskCheckForProofs" in result
        assert proof_task.check_now is True


class TestTaskSendWaiting:
    """Test TaskSendWaiting functionality."""

    def test_task_send_waiting_initialization(self) -> None:
        """Test TaskSendWaiting initializes correctly."""
        mock_monitor = MagicMock()
        task = TaskSendWaiting(mock_monitor)

        assert task.name == "SendWaiting"
        assert task.monitor == mock_monitor
        assert task.check_period_msecs == 8000
        assert task.min_age_msecs == 7000

    def test_task_send_waiting_custom_params(self) -> None:
        """Test TaskSendWaiting with custom parameters."""
        mock_monitor = MagicMock()
        task = TaskSendWaiting(mock_monitor, check_period_msecs=5000, min_age_msecs=4000)

        assert task.check_period_msecs == 5000
        assert task.min_age_msecs == 4000

    def test_task_send_waiting_trigger_timing(self) -> None:
        """Test TaskSendWaiting trigger timing."""
        mock_monitor = MagicMock()
        task = TaskSendWaiting(mock_monitor, check_period_msecs=5000)

        # First trigger should run (last_run is 0, so difference is now - 0)
        result = task.trigger(5001)  # More than 5 seconds from epoch
        assert result["run"] is True

        # Should not run again within period
        task.last_run_msecs_since_epoch = 5001
        result = task.trigger(9000)  # Only 4 seconds later
        assert result["run"] is False

        # Should run after period
        result = task.trigger(10002)  # More than 5 seconds later
        assert result["run"] is True

    def test_task_send_waiting_run_task_no_transactions(self) -> None:
        """Test TaskSendWaiting with no signed transactions."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_transactions.return_value = []

        task = TaskSendWaiting(mock_monitor)
        result = task.run_task()

        assert result == ""
        mock_monitor.storage.find_proven_tx_reqs.assert_called_once_with(
            {"partial": {}, "status": ["unsent", "sending"]}
        )

    def test_task_send_waiting_run_task_with_transactions(self) -> None:
        """Test TaskSendWaiting with unsent ProvenTxReqs."""
        mock_monitor = MagicMock()
        mock_storage = MagicMock()
        mock_services = MagicMock()

        # Mock ProvenTxReq data
        reqs = [
            {
                "txid": "tx1",
                "provenTxReqId": 123,
                "rawTx": bytes([1, 2, 3]),
                "status": "unsent",
                "notify": '{"transactionIds": [1]}',
            },
            {
                "txid": "tx2",
                "provenTxReqId": 456,
                "rawTx": bytes([4, 5, 6]),
                "status": "unsent",
                "notify": '{"transactionIds": [2]}',
            },
        ]
        mock_storage.find_proven_tx_reqs.return_value = reqs
        mock_services.post_beef.return_value = {"accepted": True}

        mock_monitor.storage = mock_storage
        mock_monitor.services = mock_services

        task = TaskSendWaiting(mock_monitor)
        result = task.run_task()

        assert "Broadcasted tx1: Success" in result
        assert "Broadcasted tx2: Success" in result

        # Verify calls
        assert mock_storage.update_proven_tx_req.call_count == 2
        assert mock_storage.update_transaction.call_count == 2
        assert mock_services.post_beef.call_count == 2

    def test_task_send_waiting_run_task_broadcast_failure(self) -> None:
        """Test TaskSendWaiting handles broadcast failure."""
        mock_monitor = MagicMock()
        mock_storage = MagicMock()
        mock_services = MagicMock()

        reqs = [
            {
                "txid": "tx1",
                "provenTxReqId": 123,
                "rawTx": bytes([1, 2, 3]),
                "status": "unsent",
                "notify": '{"transactionIds": [1]}',
            }
        ]
        mock_storage.find_proven_tx_reqs.return_value = reqs
        mock_services.post_beef.return_value = {"accepted": False, "message": "Network error"}

        mock_monitor.storage = mock_storage
        mock_monitor.services = mock_services

        task = TaskSendWaiting(mock_monitor)
        result = task.run_task()

        assert "Broadcast failed tx1: Network error" in result
        # Should not update req or transaction status on failure
        mock_storage.update_proven_tx_req.assert_not_called()
        mock_storage.update_transaction.assert_not_called()


class TestTaskCheckForProofs:
    """Test TaskCheckForProofs functionality."""

    def test_task_check_for_proofs_initialization(self) -> None:
        """Test TaskCheckForProofs initializes correctly."""
        mock_monitor = MagicMock()
        task = TaskCheckForProofs(mock_monitor)

        assert task.name == "CheckForProofs"
        assert task.monitor == mock_monitor
        assert task.check_now is False

    def test_task_check_for_proofs_trigger(self) -> None:
        """Test TaskCheckForProofs trigger logic."""
        mock_monitor = MagicMock()
        task = TaskCheckForProofs(mock_monitor)

        # Should run when check_now is set
        task.check_now = True
        result = task.trigger(0)
        assert result["run"] is True

        # Should not run when check_now is False and no time has passed
        task.check_now = False
        task.last_run_msecs_since_epoch = 0
        result = task.trigger(0)
        assert result["run"] is False

    def test_task_check_for_proofs_run_task(self) -> None:
        """Test TaskCheckForProofs run_task basic execution."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_proven_tx_reqs.return_value = []
        mock_monitor.services.get_merkle_path_for_transaction = MagicMock()

        task = TaskCheckForProofs(mock_monitor)
        result = task.run_task()

        # Should return empty string when no proven tx reqs
        assert result == ""
        mock_monitor.storage.find_proven_tx_reqs.assert_called()


class TestTaskReviewStatus:
    """Test TaskReviewStatus functionality."""

    def test_task_review_status_initialization(self) -> None:
        """Test TaskReviewStatus initializes correctly."""
        mock_monitor = MagicMock()
        task = TaskReviewStatus(mock_monitor)

        assert task.name == "ReviewStatus"
        assert task.monitor == mock_monitor

    def test_task_review_status_run_task(self) -> None:
        """Test TaskReviewStatus run_task execution."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_proven_tx_reqs.return_value = []
        mock_monitor.storage.find_transactions.return_value = []
        mock_monitor.storage.review_status.return_value = {"log": "Review completed"}

        task = TaskReviewStatus(mock_monitor)
        result = task.run_task()

        assert isinstance(result, str)
        assert "Review completed" in result


class TestTaskPurge:
    """Test TaskPurge functionality."""

    def test_task_purge_initialization(self) -> None:
        """Test TaskPurge initializes correctly."""
        mock_monitor = MagicMock()
        mock_params = {"purgeSpent": True, "purgeFailed": True}
        task = TaskPurge(mock_monitor, mock_params)

        assert task.name == "Purge"
        assert task.monitor == mock_monitor
        assert task.params == mock_params

    def test_task_purge_run_task(self) -> None:
        """Test TaskPurge run_task execution."""
        mock_monitor = MagicMock()
        mock_params = {"purgeSpent": True, "purgeFailed": True}

        task = TaskPurge(mock_monitor, mock_params)
        result = task.run_task()

        assert isinstance(result, str)


class TestTaskFailAbandoned:
    """Test TaskFailAbandoned functionality."""

    def test_task_fail_abandoned_initialization(self) -> None:
        """Test TaskFailAbandoned initializes correctly."""
        mock_monitor = MagicMock()
        task = TaskFailAbandoned(mock_monitor)

        assert task.name == "FailAbandoned"
        assert task.monitor == mock_monitor

    def test_task_fail_abandoned_initialization_custom_trigger(self) -> None:
        """Test TaskFailAbandoned initializes with custom trigger time."""
        mock_monitor = MagicMock()
        task = TaskFailAbandoned(mock_monitor, trigger_msecs=10000)

        assert task.trigger_msecs == 10000
        assert task.abandoned_msecs == 5 * 60 * 1000  # Default 5 minutes

    def test_task_fail_abandoned_trigger_should_run(self) -> None:
        """Test trigger returns run=true when enough time has passed."""
        mock_monitor = MagicMock()
        task = TaskFailAbandoned(mock_monitor, trigger_msecs=1000)

        # Set last run to 2 seconds ago
        task.last_run_msecs_since_epoch = 1000
        result = task.trigger(3000)  # 3 seconds later

        assert result == {"run": True}

    def test_task_fail_abandoned_trigger_should_not_run(self) -> None:
        """Test trigger returns run=false when not enough time has passed."""
        mock_monitor = MagicMock()
        task = TaskFailAbandoned(mock_monitor, trigger_msecs=10000)

        # Set last run to 1 second ago
        task.last_run_msecs_since_epoch = 9000
        result = task.trigger(9500)  # Only 500ms later

        assert result == {"run": False}

    def test_task_fail_abandoned_run_task_no_transactions(self) -> None:
        """Test run_task when no transactions are found."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_transactions.return_value = []

        task = TaskFailAbandoned(mock_monitor)
        result = task.run_task()

        assert result == ""

    def test_task_fail_abandoned_run_task_transaction_not_abandoned(self) -> None:
        """Test run_task with transaction that hasn't been abandoned yet."""
        mock_monitor = MagicMock()
        # Transaction updated 1 minute ago, abandoned threshold is 5 minutes
        recent_time = datetime.now(UTC) - timedelta(minutes=1)
        mock_monitor.storage.find_transactions.return_value = [{"transactionId": 1, "updatedAt": recent_time}]

        task = TaskFailAbandoned(mock_monitor)
        result = task.run_task()

        # Should not update anything
        mock_monitor.storage.update_transaction_status.assert_not_called()
        assert result == ""

    def test_task_fail_abandoned_run_task_transaction_abandoned(self) -> None:
        """Test run_task with transaction that should be failed."""
        mock_monitor = MagicMock()
        # Transaction updated 10 minutes ago (past the 5 minute threshold)
        old_time = datetime.now(UTC) - timedelta(minutes=10)
        mock_monitor.storage.find_transactions.return_value = [{"transactionId": 123, "updatedAt": old_time}]

        task = TaskFailAbandoned(mock_monitor)
        result = task.run_task()

        # Should update status to failed
        mock_monitor.storage.update_transaction_status.assert_called_once_with("failed", 123)
        assert "updated tx 123 status to 'failed'" in result

    def test_task_fail_abandoned_run_task_multiple_transactions(self) -> None:
        """Test run_task with multiple transactions."""
        mock_monitor = MagicMock()
        old_time = datetime.now(UTC) - timedelta(minutes=10)
        recent_time = datetime.now(UTC) - timedelta(minutes=1)

        mock_monitor.storage.find_transactions.return_value = [
            {"transactionId": 1, "updatedAt": old_time},  # Should be failed
            {"transactionId": 2, "updatedAt": recent_time},  # Should not be failed
            {"transactionId": 3, "updatedAt": old_time},  # Should be failed
        ]

        task = TaskFailAbandoned(mock_monitor)
        result = task.run_task()

        # Should update only the old transactions
        assert mock_monitor.storage.update_transaction_status.call_count == 2
        mock_monitor.storage.update_transaction_status.assert_any_call("failed", 1)
        mock_monitor.storage.update_transaction_status.assert_any_call("failed", 3)

        assert "updated tx 1 status to 'failed'" in result
        assert "updated tx 3 status to 'failed'" in result

    def test_task_fail_abandoned_run_task_string_datetime(self) -> None:
        """Test run_task with string datetime format."""
        mock_monitor = MagicMock()
        # ISO format string from 10 minutes ago
        old_time_str = (datetime.now(UTC) - timedelta(minutes=10)).isoformat()
        mock_monitor.storage.find_transactions.return_value = [{"transactionId": 456, "updatedAt": old_time_str}]

        task = TaskFailAbandoned(mock_monitor)
        result = task.run_task()

        mock_monitor.storage.update_transaction_status.assert_called_once_with("failed", 456)
        assert "updated tx 456 status to 'failed'" in result

    def test_task_fail_abandoned_run_task_invalid_datetime_string(self) -> None:
        """Test run_task with invalid datetime string."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_transactions.return_value = [{"transactionId": 789, "updatedAt": "invalid-date"}]

        task = TaskFailAbandoned(mock_monitor)
        result = task.run_task()

        # Should skip invalid datetime
        mock_monitor.storage.update_transaction_status.assert_not_called()
        assert result == ""

    def test_task_fail_abandoned_run_task_no_updated_at(self) -> None:
        """Test run_task with transaction missing updated_at field."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_transactions.return_value = [{"transactionId": 999}]  # No updated_at field

        task = TaskFailAbandoned(mock_monitor)
        result = task.run_task()

        # Should skip transaction without updated_at
        mock_monitor.storage.update_transaction_status.assert_not_called()
        assert result == ""

    def test_task_fail_abandoned_run_task_naive_datetime(self) -> None:
        """Test run_task with naive datetime (no timezone)."""
        mock_monitor = MagicMock()
        # Naive datetime from 10 minutes ago (representing UTC time)
        old_time_naive = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=10)
        mock_monitor.storage.find_transactions.return_value = [{"transactionId": 111, "updatedAt": old_time_naive}]

        task = TaskFailAbandoned(mock_monitor)
        result = task.run_task()

        mock_monitor.storage.update_transaction_status.assert_called_once_with("failed", 111)
        assert "updated tx 111 status to 'failed'" in result

    def test_task_fail_abandoned_run_task_update_error(self) -> None:
        """Test run_task when transaction update fails."""
        mock_monitor = MagicMock()
        old_time = datetime.now(UTC) - timedelta(minutes=10)
        mock_monitor.storage.find_transactions.return_value = [{"transactionId": 222, "updatedAt": old_time}]
        mock_monitor.storage.update_transaction_status.side_effect = Exception("DB error")

        task = TaskFailAbandoned(mock_monitor)
        result = task.run_task()

        mock_monitor.storage.update_transaction_status.assert_called_once_with("failed", 222)
        assert "failed to update tx 222: DB error" in result

    def test_task_fail_abandoned_run_task_no_transaction_id(self) -> None:
        """Test run_task with transaction missing transaction_id."""
        mock_monitor = MagicMock()
        old_time = datetime.now(UTC) - timedelta(minutes=10)
        mock_monitor.storage.find_transactions.return_value = [{"updatedAt": old_time}]  # No transaction_id field

        task = TaskFailAbandoned(mock_monitor)
        result = task.run_task()

        # Should skip transaction without transaction_id
        mock_monitor.storage.update_transaction_status.assert_not_called()
        assert result == ""


class TestTaskMonitorCallHistory:
    """Test TaskMonitorCallHistory functionality."""

    def test_task_monitor_call_history_initialization(self) -> None:
        """Test TaskMonitorCallHistory initializes correctly."""
        mock_monitor = MagicMock()
        task = TaskMonitorCallHistory(mock_monitor)

        assert task.name == "MonitorCallHistory"
        assert task.monitor == mock_monitor

    def test_task_monitor_call_history_run_task(self) -> None:
        """Test TaskMonitorCallHistory run_task execution."""
        mock_monitor = MagicMock()
        mock_services = MagicMock()
        mock_services.get_services_call_history.return_value = {"calls": []}
        mock_monitor.services = mock_services

        task = TaskMonitorCallHistory(mock_monitor)
        result = task.run_task()

        assert isinstance(result, str)
        assert '"calls": []' in result


class TestTaskReorg:
    """Test TaskReorg functionality."""

    def test_task_reorg_initialization(self) -> None:
        """Test TaskReorg initializes correctly."""
        mock_monitor = MagicMock()
        task = TaskReorg(mock_monitor)

        assert task.name == "Reorg"
        assert task.monitor == mock_monitor

    def test_task_reorg_initialization_custom_params(self) -> None:
        """Test TaskReorg initializes with custom parameters."""
        mock_monitor = MagicMock()
        task = TaskReorg(mock_monitor, aged_msecs=5000, max_retries=5)

        assert task.aged_msecs == 5000
        assert task.max_retries == 5
        assert task.process_queue == []

    def test_task_reorg_trigger_no_headers(self) -> None:
        """Test trigger when no deactivated headers exist."""
        mock_monitor = MagicMock()
        mock_monitor.deactivated_headers = []

        task = TaskReorg(mock_monitor)
        result = task.trigger(1000000)

        assert result == {"run": False}
        assert task.process_queue == []

    def test_task_reorg_trigger_headers_too_new(self) -> None:
        """Test trigger when headers exist but are too new."""
        mock_monitor = MagicMock()
        # Header from 1 second ago, aged_msecs is 10 minutes
        mock_monitor.deactivated_headers = [{"whenMsecs": 999000}]

        task = TaskReorg(mock_monitor)
        result = task.trigger(1000000)

        assert result == {"run": False}
        assert task.process_queue == []

    def test_task_reorg_trigger_headers_old_enough(self) -> None:
        """Test trigger when headers are old enough to process."""
        mock_monitor = MagicMock()
        # Header from 11 minutes ago (aged_msecs is 10 minutes default = 600000 msecs)
        # 1000000 (now) - 660000 (11 minutes) = 340000
        header = {"whenMsecs": 340000, "header": {"hash": "abc123"}, "tries": 0}
        mock_monitor.deactivated_headers = [header]

        task = TaskReorg(mock_monitor)
        result = task.trigger(1000000)  # 1000 seconds = 1000000 msecs

        assert result == {"run": True}
        assert task.process_queue == [header]
        assert mock_monitor.deactivated_headers == []

    def test_task_reorg_trigger_multiple_headers(self) -> None:
        """Test trigger with multiple headers, some old some new."""
        mock_monitor = MagicMock()
        old_header = {"whenMsecs": 100000, "header": {"hash": "old"}, "tries": 0}
        new_header = {"whenMsecs": 999000, "header": {"hash": "new"}, "tries": 0}
        mock_monitor.deactivated_headers = [old_header, new_header]

        task = TaskReorg(mock_monitor)
        result = task.trigger(1000000)

        assert result == {"run": True}
        assert task.process_queue == [old_header]
        assert mock_monitor.deactivated_headers == [new_header]

    def test_task_reorg_run_task_no_queue(self) -> None:
        """Test run_task when process queue is empty."""
        mock_monitor = MagicMock()
        task = TaskReorg(mock_monitor)

        result = task.run_task()

        assert result == ""

    def test_task_reorg_run_task_with_ptxs(self) -> None:
        """Test run_task processing proven transactions."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_proven_txs.return_value = [
            {"txid": "tx1", "provenTxId": 1, "blockHash": "old_hash"},
            {"txid": "tx2", "provenTxId": 2, "blockHash": "old_hash"},
        ]

        # Mock successful merkle path
        mock_mp = MagicMock()
        mock_mp.blockHeight = 100
        mock_mp.to_binary.return_value = b"merkle_data"

        mock_header = {"merkleRoot": "root123", "hash": "new_hash"}

        mock_monitor.services.get_merkle_path.return_value = {"merklePath": mock_mp, "header": mock_header}

        task = TaskReorg(mock_monitor)
        task.process_queue = [{"header": {"hash": "old_hash"}, "tries": 0}]

        result = task.run_task()

        # Should have updated proven txs
        assert mock_monitor.storage.update_proven_tx.call_count == 2
        assert "block old_hash orphaned with 2 impacted transactions" in result
        assert "proof data updated" in result

    def test_task_reorg_run_task_merkle_path_error(self) -> None:
        """Test run_task when merkle path retrieval fails."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_proven_txs.return_value = [{"txid": "tx1"}]
        mock_monitor.services.get_merkle_path.side_effect = Exception("Network error")

        task = TaskReorg(mock_monitor)
        task.process_queue = [{"header": {"hash": "hash"}, "tries": 0}]

        result = task.run_task()

        assert "error processing: Network error" in result

    def test_task_reorg_run_task_same_block_hash(self) -> None:
        """Test run_task when new merkle path has same block hash."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_proven_txs.return_value = [{"txid": "tx1", "provenTxId": 1, "blockHash": "same_hash"}]

        mock_mp = MagicMock()
        mock_mp.blockHeight = 100

        mock_monitor.services.get_merkle_path.return_value = {
            "merklePath": mock_mp,
            "header": {"merkleRoot": "root", "hash": "same_hash"},  # Same hash
        }

        task = TaskReorg(mock_monitor)
        task.process_queue = [{"header": {"hash": "same_hash"}, "tries": 0}]

        result = task.run_task()

        # Should retry since block hash is same
        assert "still based on deactivated header same_hash" in result
        assert "retrying..." in result
        mock_monitor.deactivated_headers.append.assert_called_once()

    def test_task_reorg_run_task_max_retries_exceeded(self) -> None:
        """Test run_task when maximum retries are exceeded."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_proven_txs.return_value = [{"txid": "tx1", "provenTxId": 1, "blockHash": "same_hash"}]

        mock_mp = MagicMock()
        mock_mp.blockHeight = 100

        mock_monitor.services.get_merkle_path.return_value = {
            "merklePath": mock_mp,
            "header": {"merkleRoot": "root", "hash": "same_hash"},
        }

        task = TaskReorg(mock_monitor, max_retries=2)
        task.process_queue = [{"header": {"hash": "same_hash"}, "tries": 2}]  # Already at max

        result = task.run_task()

        assert "maximum retries 2 exceeded" in result
        # Should not add back to deactivated headers

    def test_task_reorg_run_task_no_merkle_path(self) -> None:
        """Test run_task when merkle path is unavailable."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_proven_txs.return_value = [{"txid": "tx1"}]
        mock_monitor.services.get_merkle_path.return_value = {"merklePath": None, "header": None}

        task = TaskReorg(mock_monitor)
        task.process_queue = [{"header": {"hash": "hash"}, "tries": 0}]

        result = task.run_task()

        assert "merkle path update unavailable" in result
        assert "retrying..." in result

    def test_task_reorg_run_task_find_ptxs_error(self) -> None:
        """Test run_task when finding proven txs fails."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_proven_txs.side_effect = Exception("DB error")

        task = TaskReorg(mock_monitor)
        task.process_queue = [{"header": {"hash": "hash"}, "tries": 0}]

        result = task.run_task()

        assert "Error finding proven txs: DB error" in result

    def test_task_reorg_run_task_empty_ptx_list(self) -> None:
        """Test run_task when no proven txs are found."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_proven_txs.return_value = []

        task = TaskReorg(mock_monitor)
        task.process_queue = [{"header": {"hash": "hash"}, "tries": 0}]

        result = task.run_task()

        assert "block hash orphaned with 0 impacted transactions" in result


class TestTaskSyncWhenIdle:
    """Test TaskSyncWhenIdle functionality."""

    def test_task_sync_when_idle_initialization(self) -> None:
        """Test TaskSyncWhenIdle initializes correctly."""
        mock_monitor = MagicMock()
        task = TaskSyncWhenIdle(mock_monitor)

        assert task.name == "SyncWhenIdle"
        assert task.monitor == mock_monitor

    def test_task_sync_when_idle_run_task(self) -> None:
        """Test TaskSyncWhenIdle run_task execution."""
        mock_monitor = MagicMock()

        task = TaskSyncWhenIdle(mock_monitor)
        result = task.run_task()

        assert isinstance(result, str)


class TestTaskUnFail:
    """Test TaskUnFail functionality."""

    def test_task_un_fail_initialization(self) -> None:
        """Test TaskUnFail initializes correctly."""
        mock_monitor = MagicMock()
        task = TaskUnFail(mock_monitor)

        assert task.name == "UnFail"
        assert task.monitor == mock_monitor

    def test_task_un_fail_initialization_custom_trigger(self) -> None:
        """Test TaskUnFail initializes with custom trigger time."""
        mock_monitor = MagicMock()
        task = TaskUnFail(mock_monitor, trigger_msecs=15000)

        assert task.trigger_msecs == 15000
        assert task.check_now is False

    def test_task_un_fail_trigger_check_now_true(self) -> None:
        """Test trigger returns run=true when check_now is True."""
        mock_monitor = MagicMock()
        task = TaskUnFail(mock_monitor)

        task.check_now = True
        result = task.trigger(1000)

        assert result == {"run": True}

    def test_task_un_fail_trigger_should_run_periodic(self) -> None:
        """Test trigger returns run=true when periodic time has passed."""
        mock_monitor = MagicMock()
        task = TaskUnFail(mock_monitor, trigger_msecs=2000)

        task.last_run_msecs_since_epoch = 1000
        result = task.trigger(3500)  # 2.5 seconds later

        assert result == {"run": True}

    def test_task_un_fail_trigger_should_not_run(self) -> None:
        """Test trigger returns run=false when not enough time has passed."""
        mock_monitor = MagicMock()
        task = TaskUnFail(mock_monitor, trigger_msecs=5000)

        task.last_run_msecs_since_epoch = 8000
        result = task.trigger(9000)  # Only 1 second later

        assert result == {"run": False}

    def test_task_un_fail_run_task_no_requests(self) -> None:
        """Test run_task when no unfail requests exist."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_proven_tx_reqs.return_value = []

        task = TaskUnFail(mock_monitor)
        result = task.run_task()

        assert result == ""
        assert task.check_now is False

    def test_task_un_fail_run_task_successful_unfail(self) -> None:
        """Test run_task with successful unfail operation."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_proven_tx_reqs.return_value = [
            {"provenTxReqId": 123, "txid": "tx123", "rawTx": b"deadbeef"}
        ]
        mock_monitor.services.get_merkle_path_for_transaction.return_value = {"merklePath": {"some": "path"}}
        mock_monitor.storage.find_transactions.return_value = [{"transactionId": 456, "userId": 789}]

        task = TaskUnFail(mock_monitor)
        result = task.run_task()

        # Should update request status
        mock_monitor.storage.update_proven_tx_req.assert_any_call(123, {"status": "unmined", "attempts": 0})
        # Should update transaction status
        mock_monitor.storage.update_transaction.assert_called_once_with(456, {"status": "unproven"})

        assert "Req 123: unfailed. status is now 'unmined'" in result
        assert "transaction tx123 status is now 'unproven'" in result
        assert task.check_now is False

    def test_task_un_fail_run_task_proof_not_found(self) -> None:
        """Test run_task when merkle proof is not found."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_proven_tx_reqs.return_value = [{"provenTxReqId": 456, "txid": "tx456"}]
        mock_monitor.services.get_merkle_path_for_transaction.return_value = {"merklePath": None}

        task = TaskUnFail(mock_monitor)
        result = task.run_task()

        # Should set status back to invalid
        mock_monitor.storage.update_proven_tx_req.assert_called_once_with(456, {"status": "invalid"})
        assert "Req 456: returned to status 'invalid'" in result

    def test_task_un_fail_run_task_merkle_path_error(self) -> None:
        """Test run_task when getting merkle path fails."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_proven_tx_reqs.return_value = [{"provenTxReqId": 789, "txid": "tx789"}]
        mock_monitor.services.get_merkle_path_for_transaction.side_effect = Exception("Network error")

        task = TaskUnFail(mock_monitor)
        result = task.run_task()

        assert "Error processing req 789: Network error" in result

    def test_task_un_fail_run_task_missing_txid_or_req_id(self) -> None:
        """Test run_task skips requests with missing txid or req_id."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_proven_tx_reqs.return_value = [
            {"txid": "tx1"},  # Missing req_id
            {"provenTxReqId": 2},  # Missing txid
            {"provenTxReqId": 3, "txid": "tx3"},  # Valid
        ]
        mock_monitor.services.get_merkle_path_for_transaction.return_value = {"merklePath": {"some": "path"}}

        task = TaskUnFail(mock_monitor)
        task.run_task()

        # Should only process the valid request
        assert mock_monitor.services.get_merkle_path_for_transaction.call_count == 1
        mock_monitor.services.get_merkle_path_for_transaction.assert_called_with("tx3")

    def test_task_un_fail_run_task_transaction_not_found(self) -> None:
        """Test run_task when transaction is not found in storage."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_proven_tx_reqs.return_value = [
            {"provenTxReqId": 111, "txid": "tx111", "rawTx": b"data"}
        ]
        mock_monitor.services.get_merkle_path_for_transaction.return_value = {"merklePath": {"some": "path"}}
        mock_monitor.storage.find_transactions.return_value = []  # Not found

        task = TaskUnFail(mock_monitor)
        result = task.run_task()

        assert "transaction tx111 was not found" in result
        # Should still update the request status
        mock_monitor.storage.update_proven_tx_req.assert_called_once_with(111, {"status": "unmined", "attempts": 0})

    def test_task_un_fail_run_task_unfail_req_error(self) -> None:
        """Test run_task when unfailing request details fails."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_proven_tx_reqs.return_value = [
            {"provenTxReqId": 222, "txid": "tx222", "rawTx": b"data"}
        ]
        mock_monitor.services.get_merkle_path_for_transaction.return_value = {"merklePath": {"some": "path"}}
        mock_monitor.storage.find_transactions.return_value = [{"transactionId": 333, "userId": 444}]
        mock_monitor.storage.update_transaction.side_effect = Exception("DB error")

        task = TaskUnFail(mock_monitor)
        result = task.run_task()

        assert "Error unfailing details for 222: DB error" in result
        # Should still have updated the request status
        mock_monitor.storage.update_proven_tx_req.assert_called_once_with(222, {"status": "unmined", "attempts": 0})

    def test_task_un_fail_run_task_pagination(self) -> None:
        """Test run_task with pagination (multiple batches)."""
        mock_monitor = MagicMock()
        # Create 150 requests (more than the limit of 100)
        requests = []
        for i in range(150):
            requests.append({"provenTxReqId": i + 1, "txid": f"tx{i+1}"})

        mock_monitor.storage.find_proven_tx_reqs.return_value = requests
        mock_monitor.services.get_merkle_path_for_transaction.return_value = {"merklePath": {"some": "path"}}

        task = TaskUnFail(mock_monitor)
        result = task.run_task()

        # Should process 100 requests in first batch
        assert "100 reqs with status 'unfail'" in result
        # Should process remaining 50 in second batch
        assert "50 reqs with status 'unfail'" in result

        # Should call get_merkle_path_for_transaction 150 times total
        assert mock_monitor.services.get_merkle_path_for_transaction.call_count == 150

    def test_task_un_fail_unfail_req_missing_txid(self) -> None:
        """Test _unfail_req when request is missing txid."""
        mock_monitor = MagicMock()

        task = TaskUnFail(mock_monitor)
        log_lines = []
        req = {}  # Missing txid

        task._unfail_req(req, b"data", log_lines)

        # Should return early without doing anything
        mock_monitor.storage.find_transactions.assert_not_called()
        assert log_lines == []

    def test_task_un_fail_unfail_req_missing_transaction_fields(self) -> None:
        """Test _unfail_req when transaction is missing required fields."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_transactions.return_value = [
            {"transactionId": None, "userId": 123}  # Missing transaction_id
        ]

        task = TaskUnFail(mock_monitor)
        log_lines = []
        req = {"txid": "tx999"}

        task._unfail_req(req, b"data", log_lines)

        # Should not update transaction
        mock_monitor.storage.update_transaction.assert_not_called()
        assert log_lines == []


class TestTaskCheckNoSends:
    """Test TaskCheckNoSends functionality."""

    def test_task_check_no_sends_initialization(self) -> None:
        """Test TaskCheckNoSends initializes correctly."""
        mock_monitor = MagicMock()
        task = TaskCheckNoSends(mock_monitor)

        assert task.name == "CheckNoSends"
        assert task.monitor == mock_monitor
        assert task.check_now is False

    def test_task_check_no_sends_initialization_custom_trigger(self) -> None:
        """Test TaskCheckNoSends initializes with custom trigger time."""
        mock_monitor = MagicMock()
        custom_trigger = 12 * 60 * 60 * 1000  # 12 hours
        task = TaskCheckNoSends(mock_monitor, custom_trigger)

        assert task.name == "CheckNoSends"
        assert task.monitor == mock_monitor
        assert task.trigger_msecs == custom_trigger

    def test_task_check_no_sends_run_task_no_reqs(self) -> None:
        """Test TaskCheckNoSends run_task when no nosend reqs exist."""
        mock_monitor = MagicMock()
        mock_monitor.storage.find_proven_tx_reqs.return_value = []

        task = TaskCheckNoSends(mock_monitor)
        result = task.run_task()

        # Should return empty string when no reqs
        assert result == ""
        mock_monitor.storage.find_proven_tx_reqs.assert_called_with({"status": ["nosend"]})

    def test_task_check_no_sends_run_task_with_reqs(self) -> None:
        """Test TaskCheckNoSends run_task when nosend reqs exist."""
        mock_monitor = MagicMock()
        mock_monitor.services.find_chain_tip_header.return_value = {"height": 1000}
        mock_monitor.storage.find_proven_tx_reqs.return_value = [{"id": 1, "txid": "tx1"}, {"id": 2, "txid": "tx2"}]

        task = TaskCheckNoSends(mock_monitor)

        # Mock the inherited _process_req method
        with patch.object(task, "_process_req") as mock_process_req:
            result = task.run_task()

            # Should process the reqs
            assert mock_process_req.call_count == 2
            assert "Processing 2 nosend reqs..." in result

    def test_task_check_no_sends_run_task_chain_tip_error(self) -> None:
        """Test TaskCheckNoSends run_task when chain tip retrieval fails."""
        mock_monitor = MagicMock()
        mock_monitor.services.find_chain_tip_header.side_effect = Exception("Network error")

        task = TaskCheckNoSends(mock_monitor)
        result = task.run_task()

        assert "Failed to get chain tip header: Network error" in result

    def test_task_check_no_sends_run_task_no_chain_height(self) -> None:
        """Test TaskCheckNoSends run_task when chain tip has no height."""
        mock_monitor = MagicMock()
        mock_monitor.services.find_chain_tip_header.return_value = {"hash": "some_hash"}

        task = TaskCheckNoSends(mock_monitor)
        result = task.run_task()

        assert result == "Chain tip height unavailable"

    def test_task_check_no_sends_inheritance(self) -> None:
        """Test TaskCheckNoSends properly inherits from TaskCheckForProofs."""
        mock_monitor = MagicMock()
        task = TaskCheckNoSends(mock_monitor)

        # Should have inherited methods from parent
        assert hasattr(task, "trigger")
        assert hasattr(task, "_process_req")
        assert hasattr(task, "run_task")

        # But should have its own name
        assert task.name == "CheckNoSends"
