"""Tests for sync chunk processor."""

from unittest.mock import Mock

import pytest

from bsv_wallet_toolbox.storage.sync_processor import SyncChunkProcessor


class TestSyncChunkProcessor:
    """Test SyncChunkProcessor functionality."""

    def test_empty_chunk_detection(self):
        """Test that empty chunks are properly detected."""
        provider = Mock()
        chunk = {
            "fromStorageIdentityKey": "remote_key",
            "toStorageIdentityKey": "local_key",
            "userIdentityKey": "user123",
            # Empty entity arrays
            "outputBaskets": [],
            "transactions": [],
            "outputs": [],
        }
        args = {"fromStorageIdentityKey": "remote_key", "identityKey": "user123"}

        processor = SyncChunkProcessor(provider, chunk, args)
        result = processor.process_chunk()

        assert result["done"] is True
        assert result["processed"] is True
        assert result["updated"] == 0

    def test_chunk_validation(self):
        """Test chunk validation."""
        provider = Mock()
        chunk = {
            "toStorageIdentityKey": "local_key",
            "userIdentityKey": "user123",
            # Missing fromStorageIdentityKey
        }
        args = {"fromStorageIdentityKey": "remote_key"}

        with pytest.raises(ValueError, match="Missing required field"):
            SyncChunkProcessor(provider, chunk, args)

    def test_storage_key_validation(self):
        """Test storage identity key validation."""
        provider = Mock()
        provider.storage_identity_key = "local_key"
        chunk = {
            "fromStorageIdentityKey": "wrong_key",
            "toStorageIdentityKey": "local_key",
            "userIdentityKey": "user123",
        }
        args = {"fromStorageIdentityKey": "remote_key"}

        with pytest.raises(ValueError, match="Storage key mismatch"):
            SyncChunkProcessor(provider, chunk, args)

    def test_transaction_processing(self):
        """Test transaction processing in sync chunks."""
        provider = Mock()
        provider.insert_transaction = Mock()
        provider.get_or_create_user_id = Mock(return_value=1)

        chunk = {
            "fromStorageIdentityKey": "remote_key",
            "toStorageIdentityKey": "local_key",
            "userIdentityKey": "user123",
            "transactions": [{"txid": "abc123", "status": "confirmed"}, {"txid": "def456", "status": "pending"}],
        }
        args = {"fromStorageIdentityKey": "remote_key", "identityKey": "user123"}

        processor = SyncChunkProcessor(provider, chunk, args)
        result = processor.process_chunk()

        assert result["processed"] is True
        assert result["updated"] == 2  # 2 transactions
        assert provider.insert_transaction.call_count == 2

    def test_basket_processing(self):
        """Test output basket processing."""
        provider = Mock()
        provider.configure_basket = Mock()
        provider.get_or_create_user_id = Mock(return_value=1)

        chunk = {
            "fromStorageIdentityKey": "remote_key",
            "toStorageIdentityKey": "local_key",
            "userIdentityKey": "user123",
            "outputBaskets": [{"name": "basket1", "numberOfDesiredUTXOs": 5}],
        }
        args = {"fromStorageIdentityKey": "remote_key", "identityKey": "user123"}

        processor = SyncChunkProcessor(provider, chunk, args)
        result = processor.process_chunk()

        assert result["processed"] is True
        assert result["updated"] == 1
        provider.configure_basket.assert_called_once()

    def test_error_handling(self):
        """Test error handling during processing."""
        provider = Mock()
        provider.insert_transaction = Mock(side_effect=Exception("DB error"))
        provider.get_or_create_user_id = Mock(return_value=1)

        chunk = {
            "fromStorageIdentityKey": "remote_key",
            "toStorageIdentityKey": "local_key",
            "userIdentityKey": "user123",
            "transactions": [{"txid": "abc123"}],
        }
        args = {"fromStorageIdentityKey": "remote_key", "identityKey": "user123"}

        processor = SyncChunkProcessor(provider, chunk, args)
        result = processor.process_chunk()

        assert result["processed"] is True
        assert len(result["errors"]) == 1
        assert "DB error" in result["errors"][0]

    def test_mixed_entity_processing(self):
        """Test processing multiple entity types."""
        provider = Mock()
        provider.configure_basket = Mock()
        provider.insert_transaction = Mock()
        provider.insert_output = Mock()
        provider.get_or_create_user_id = Mock(return_value=1)

        chunk = {
            "fromStorageIdentityKey": "remote_key",
            "toStorageIdentityKey": "local_key",
            "userIdentityKey": "user123",
            "outputBaskets": [{"name": "basket1"}],
            "transactions": [{"txid": "tx1"}],
            "outputs": [{"txid": "tx1", "vout": 0}],
        }
        args = {"fromStorageIdentityKey": "remote_key", "identityKey": "user123"}

        processor = SyncChunkProcessor(provider, chunk, args)
        result = processor.process_chunk()

        assert result["processed"] is True
        assert result["updated"] == 3  # basket + transaction + output
        provider.configure_basket.assert_called_once()
        provider.insert_transaction.assert_called_once()
        provider.insert_output.assert_called_once()
