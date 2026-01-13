"""Tests for MonitorDaemon.

This module provides comprehensive test coverage for the MonitorDaemon class.
"""

from unittest.mock import Mock, patch

import pytest

from bsv_wallet_toolbox.monitor.monitor_daemon import MonitorDaemon


class TestMonitorDaemon:
    """Test MonitorDaemon functionality."""

    @pytest.fixture
    def mock_monitor(self) -> Mock:
        """Create a mock monitor."""
        monitor = Mock()
        monitor.options.task_run_wait_msecs = 1000  # 1 second
        return monitor

    @pytest.fixture
    def daemon(self, mock_monitor: Mock) -> MonitorDaemon:
        """Create a monitor daemon."""
        return MonitorDaemon(mock_monitor)

    def test_init(self, mock_monitor: Mock) -> None:
        """Test daemon initialization."""
        daemon = MonitorDaemon(mock_monitor)

        assert daemon.monitor == mock_monitor
        assert daemon._thread is None
        assert daemon._running is False

    def test_start_success(self, daemon: MonitorDaemon) -> None:
        """Test successful daemon start."""
        daemon.start()

        assert daemon._running is True
        assert daemon._thread is not None
        assert daemon._thread.daemon is True
        assert daemon._thread.name == "WalletMonitorThread"
        assert daemon._thread.is_alive()

        daemon.stop()

    def test_start_already_running_raises_error(self, daemon: MonitorDaemon) -> None:
        """Test starting daemon when already running raises error."""
        daemon.start()

        with pytest.raises(RuntimeError, match="Monitor daemon is already running"):
            daemon.start()

        daemon.stop()

    def test_stop_when_not_running(self, daemon: MonitorDaemon) -> None:
        """Test stopping daemon when not running."""
        assert daemon._running is False

        # Should not raise
        daemon.stop()

        assert daemon._running is False
        assert daemon._thread is None

    def test_stop_after_start(self, daemon: MonitorDaemon) -> None:
        """Test stopping daemon after starting."""
        daemon.start()
        assert daemon._running is True
        assert daemon._thread is not None

        daemon.stop()

        assert daemon._running is False
        assert daemon._thread is None

    @patch("time.sleep")
    def test_loop_calls_monitor_run_once(self, mock_sleep: Mock, daemon: MonitorDaemon) -> None:
        """Test that the loop calls monitor.run_once()."""
        daemon._running = True

        # Mock run_once to set _running to False after first call to exit loop
        def side_effect():
            daemon._running = False
            raise Exception("Exit loop")

        daemon.monitor.run_once.side_effect = side_effect

        try:
            daemon._loop()
        except Exception:
            pass  # Expected

        daemon.monitor.run_once.assert_called()

    @patch("time.sleep")
    def test_loop_handles_exceptions(self, mock_sleep: Mock, daemon: MonitorDaemon) -> None:
        """Test that the loop handles exceptions gracefully."""
        daemon._running = True

        # Make run_once raise an exception and then stop the loop
        call_count = 0

        def side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Test error")
            else:
                daemon._running = False

        daemon.monitor.run_once.side_effect = side_effect

        with patch("bsv_wallet_toolbox.monitor.monitor_daemon.logger") as mock_logger:
            daemon._loop()

            # Should have logged the error
            mock_logger.error.assert_called_once()
            args = mock_logger.error.call_args[0]
            assert args[0] == "MonitorDaemon loop error: %s"
            assert isinstance(args[1], ValueError)
            assert str(args[1]) == "Test error"

    @patch("time.sleep")
    def test_loop_respects_running_flag(self, mock_sleep: Mock, daemon: MonitorDaemon) -> None:
        """Test that the loop respects the running flag."""
        daemon._running = False

        # Should exit immediately
        daemon._loop()

        # run_once should not be called
        daemon.monitor.run_once.assert_not_called()

    @patch("time.sleep")
    def test_loop_wait_timing(self, mock_sleep: Mock, daemon: MonitorDaemon) -> None:
        """Test that the loop waits for the correct amount of time."""
        daemon._running = True
        daemon.monitor.options.task_run_wait_msecs = 500  # 0.5 seconds

        # Count calls to control when to stop
        call_count = 0

        def side_effect():
            nonlocal call_count
            call_count += 1
            if call_count >= 2:  # Let it run once and start waiting, then stop
                daemon._running = False

        daemon.monitor.run_once.side_effect = side_effect

        daemon._loop()

        # Should have called sleep multiple times to wait
        # Total calls should be wait_msecs / step_msecs = 500 / 100 = 5
        assert mock_sleep.call_count >= 4  # At least 4 calls for 500ms with 100ms steps

    def test_thread_cleanup_on_stop(self, daemon: MonitorDaemon) -> None:
        """Test that the thread is properly cleaned up on stop."""
        daemon.start()

        thread = daemon._thread
        assert thread is not None
        assert thread.is_alive()

        daemon.stop()

        assert daemon._thread is None
        # Thread should eventually stop (may take a moment)
        thread.join(timeout=2.0)

    @patch("threading.Thread.join")
    def test_stop_handles_join_timeout(self, mock_join: Mock, daemon: MonitorDaemon) -> None:
        """Test that stop handles thread join timeout gracefully."""
        daemon.start()
        assert daemon._thread is not None

        # Mock join to not complete
        mock_join.return_value = None

        daemon.stop()

        # Should still set _running to False and _thread to None
        assert daemon._running is False
        assert daemon._thread is None
