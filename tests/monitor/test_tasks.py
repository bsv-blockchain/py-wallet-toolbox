"""Unit tests for Monitor Task classes.

These tests verify the logic of individual monitor tasks in isolation,
mocking the Monitor dependency to focus on task behavior.
"""

import pytest
from unittest.mock import MagicMock, patch
import time

from bsv_wallet_toolbox.monitor.tasks import (
    TaskClock,
    TaskNewHeader,
    TaskSendWaiting,
    TaskCheckForProofs,
    TaskReviewStatus,
    TaskPurge,
    TaskFailAbandoned,
    TaskMonitorCallHistory,
    TaskReorg,
    TaskSyncWhenIdle,
    TaskUnFail,
)


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
        mock_monitor.storage.find_transactions.assert_called_once_with({"tx_status": "signed"})

    def test_task_send_waiting_run_task_with_transactions(self) -> None:
        """Test TaskSendWaiting with signed transactions."""
        mock_monitor = MagicMock()
        mock_storage = MagicMock()
        mock_services = MagicMock()

        # Mock transaction data
        txs = [
            {"txid": "tx1", "transaction_id": 123},
            {"txid": "tx2", "transaction_id": 456},
        ]
        mock_storage.find_transactions.return_value = txs
        mock_storage.get_beef_for_transaction.return_value = bytes([1, 2, 3])
        mock_services.post_beef.return_value = {"accepted": True}

        mock_monitor.storage = mock_storage
        mock_monitor.services = mock_services

        task = TaskSendWaiting(mock_monitor)
        result = task.run_task()

        assert "Broadcasted tx1: Success" in result
        assert "Broadcasted tx2: Success" in result

        # Verify calls
        assert mock_storage.update_transaction.call_count == 2
        assert mock_services.post_beef.call_count == 2

    def test_task_send_waiting_run_task_broadcast_failure(self) -> None:
        """Test TaskSendWaiting handles broadcast failure."""
        mock_monitor = MagicMock()
        mock_storage = MagicMock()
        mock_services = MagicMock()

        txs = [{"txid": "tx1", "transaction_id": 123}]
        mock_storage.find_transactions.return_value = txs
        mock_storage.get_beef_for_transaction.return_value = bytes([1, 2, 3])
        mock_services.post_beef.return_value = {"accepted": False, "message": "Network error"}

        mock_monitor.storage = mock_storage
        mock_monitor.services = mock_services

        task = TaskSendWaiting(mock_monitor)
        result = task.run_task()

        assert "Broadcast failed tx1: Network error" in result
        # Should not update transaction status on failure
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

    def test_task_fail_abandoned_run_task(self) -> None:
        """Test TaskFailAbandoned run_task execution."""
        mock_monitor = MagicMock()

        task = TaskFailAbandoned(mock_monitor)
        result = task.run_task()

        assert isinstance(result, str)


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

    def test_task_reorg_run_task(self) -> None:
        """Test TaskReorg run_task execution."""
        mock_monitor = MagicMock()

        task = TaskReorg(mock_monitor)
        result = task.run_task()

        assert isinstance(result, str)


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

    def test_task_un_fail_run_task(self) -> None:
        """Test TaskUnFail run_task execution."""
        mock_monitor = MagicMock()

        task = TaskUnFail(mock_monitor)
        result = task.run_task()

        assert isinstance(result, str)
