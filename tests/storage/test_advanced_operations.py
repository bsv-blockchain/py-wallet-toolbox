"""Tests for advanced storage operations."""

from datetime import UTC
from unittest.mock import Mock, patch

from bsv_wallet_toolbox.storage.provider import StorageProvider


class TestAdvancedStorageOperations:
    """Test advanced storage operations."""

    def test_synchronize_transaction_statuses_with_services(self):
        """Test synchronize_transaction_statuses with available services."""
        provider = Mock()
        provider._services = Mock()

        # Mock pending transactions
        provider.find_transactions = Mock(return_value=[{"txid": "abc123", "transactionId": 1, "status": "pending"}])

        # Mock service response
        provider._services.get_transaction_status = Mock(return_value={"status": "confirmed"})

        # Import and call the actual method

        StorageProvider.synchronize_transaction_statuses(provider)

        # Should have checked status and updated transaction
        provider._services.get_transaction_status.assert_called_once_with("abc123")
        provider.update_transaction.assert_called_once_with(1, {"status": "confirmed"})

    def test_send_waiting_transactions(self):
        """Test send_waiting_transactions with age filtering."""
        provider = Mock()
        provider._services = Mock()

        # Mock waiting transactions with old datetime (older than cutoff)
        from datetime import datetime, timedelta

        old_time = datetime.now(UTC) - timedelta(seconds=10)  # 10 seconds ago
        provider.find_transactions = Mock(
            return_value=[{"txid": "abc123", "transactionId": 1, "status": "waiting", "createdAt": old_time}]
        )

        # Mock raw transaction
        provider.get_raw_tx_of_known_valid_transaction = Mock(return_value="raw_tx_hex")

        # Mock successful broadcast
        provider._services.post_beef = Mock(return_value={"success": True})

        # Import and call the actual method

        result = StorageProvider.send_waiting_transactions(provider, min_age_seconds=0)

        assert result["sent"] == 1
        assert result["failed"] == 0
        provider.update_transaction.assert_called_once_with(1, {"status": "sent"})

    def test_abort_abandoned(self):
        """Test abort_abandoned marks old transactions as failed."""
        provider = Mock()

        # Mock processing transactions with proper datetime objects
        from datetime import datetime

        old_time = datetime.now(UTC)
        provider.find_transactions = Mock(
            return_value=[{"transactionId": 1, "status": "processing", "createdAt": old_time}]
        )

        # Import and call the actual method

        result = StorageProvider.abort_abandoned(provider, min_age_seconds=0)

        assert result["abandoned"] == 1
        provider.update_transaction.assert_called_once_with(1, {"status": "failed"})

    def test_un_fail_success(self):
        """Test un_fail restores failed transactions that are now confirmed."""
        provider = Mock()
        provider._services = Mock()

        # Mock failed transactions
        provider.find_transactions = Mock(return_value=[{"txid": "abc123", "transactionId": 1, "status": "failed"}])

        # Mock service showing transaction is now confirmed
        provider._services.get_transaction_status = Mock(return_value={"status": "confirmed"})

        # Import and call the actual method

        result = StorageProvider.un_fail(provider)

        assert result["unfail"] == 1
        provider.update_transaction.assert_called_once_with(1, {"status": "confirmed"})

    def test_configure_basket(self):
        """Test basket configuration."""
        provider = Mock()

        # Mock the session and database operations
        with patch("bsv_wallet_toolbox.storage.provider.session_scope") as mock_session_scope:
            mock_session = Mock()
            mock_session_scope.return_value.__enter__.return_value = mock_session

            # Mock no existing basket found
            mock_session.execute.return_value.scalar_one_or_none.return_value = None

            # Import and call the actual method
            from bsv_wallet_toolbox.storage.provider import StorageProvider

            StorageProvider.configure_basket(
                provider, auth={"userId": 1}, basket_config={"name": "test_basket", "numberOfDesiredUTXOs": 5}
            )

            # Should have executed database operations
            assert mock_session.execute.called
