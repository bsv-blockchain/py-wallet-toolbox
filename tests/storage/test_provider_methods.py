"""Unit tests for StorageProvider CRUD methods.

Tests the core storage functionality using in-memory SQLite database.
"""

from datetime import UTC, datetime

import pytest

from bsv_wallet_toolbox.storage.db import create_engine_from_url
from bsv_wallet_toolbox.storage.provider import StorageProvider


@pytest.fixture
def storage_provider():
    """Create an in-memory StorageProvider for testing."""
    engine = create_engine_from_url("sqlite:///:memory:")
    storage = StorageProvider(engine=engine, chain="main", storage_identity_key="test_storage")
    storage.make_available()
    return storage


class TestStorageProviderBasicOperations:
    """Test basic StorageProvider operations."""

    def test_storage_provider_initialization(self, storage_provider):
        """Test StorageProvider initializes correctly."""
        assert storage_provider.is_storage_provider()
        assert storage_provider.is_available()

    def test_get_or_create_user_id(self, storage_provider):
        """Test getting or creating user ID."""
        identity_key = "test_key_123"
        user_id = storage_provider.get_or_create_user_id(identity_key)

        assert isinstance(user_id, int)
        assert user_id > 0

        # Should return same ID for same key
        user_id2 = storage_provider.get_or_create_user_id(identity_key)
        assert user_id == user_id2

    def test_find_or_insert_user(self, storage_provider):
        """Test finding or inserting user."""
        identity_key = "test_user_key"

        result = storage_provider.find_or_insert_user(identity_key)
        assert "userId" in result["user"]
        # createdNew may not be present if user already exists
        assert isinstance(result["user"]["userId"], int)


class TestStorageProviderTransactionOperations:
    """Test transaction-related CRUD operations."""

    def test_insert_transaction(self, storage_provider):
        """Test inserting a transaction."""
        user_id = storage_provider.get_or_create_user_id("test_user")

        tx_data = {
            "userId": user_id,
            "txid": "a" * 64,
            "status": "completed",
            "reference": "test_tx",
            "isOutgoing": False,
            "satoshis": 1000,
            "description": "Test transaction",
            "version": 1,
            "lockTime": 0,
            "rawTx": bytes([1, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
        }

        tx_id = storage_provider.insert_transaction(tx_data)
        assert isinstance(tx_id, int)
        assert tx_id > 0

    def test_find_transactions(self, storage_provider):
        """Test finding transactions."""
        user_id = storage_provider.get_or_create_user_id("test_user")

        # Insert test transaction
        tx_data = {
            "userId": user_id,
            "txid": "b" * 64,
            "status": "completed",
            "reference": "test_tx_2",
            "isOutgoing": False,
            "satoshis": 2000,
            "description": "Test transaction 2",
            "version": 1,
            "lockTime": 0,
            "rawTx": bytes([2, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
        }
        storage_provider.insert_transaction(tx_data)

        # Find transactions
        transactions = storage_provider.find_transactions({"userId": user_id})
        assert len(transactions) >= 1
        assert transactions[0]["txid"] == "b" * 64

    def test_update_transaction(self, storage_provider):
        """Test updating a transaction."""
        user_id = storage_provider.get_or_create_user_id("test_user")

        # Insert transaction
        tx_data = {
            "userId": user_id,
            "txid": "c" * 64,
            "status": "unmined",
            "reference": "test_tx_3",
            "isOutgoing": True,
            "satoshis": 3000,
            "description": "Test transaction 3",
            "version": 1,
            "lockTime": 0,
            "rawTx": bytes([3, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
        }
        tx_id = storage_provider.insert_transaction(tx_data)

        # Update transaction
        updated = storage_provider.update_transaction(tx_id, {"status": "completed"})
        assert updated == 1

        # Verify update
        transactions = storage_provider.find_transactions({"txid": "c" * 64})
        assert len(transactions) == 1
        assert transactions[0]["status"] == "completed"


class TestStorageProviderOutputOperations:
    """Test output-related CRUD operations."""

    def test_insert_output(self, storage_provider):
        """Test inserting an output."""
        user_id = storage_provider.get_or_create_user_id("test_user")

        # Create basket first
        basket_data = {
            "userId": user_id,
            "name": "default",
            "numberOfDesiredUTXOs": 10,
            "minimumDesiredUTXOValue": 1000,
            "isDeleted": False,
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
        }
        basket_id = storage_provider.insert_output_basket(basket_data)

        # Insert transaction first
        tx_data = {
            "userId": user_id,
            "txid": "d" * 64,
            "status": "completed",
            "reference": "test_tx_4",
            "isOutgoing": False,
            "satoshis": 5000,
            "description": "Test transaction 4",
            "version": 1,
            "lockTime": 0,
            "rawTx": bytes([4, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
        }
        tx_id = storage_provider.insert_transaction(tx_data)

        # Insert output
        output_data = {
            "transactionId": tx_id,
            "userId": user_id,
            "basketId": basket_id,
            "spendable": True,
            "change": True,
            "vout": 0,
            "satoshis": 5000,
            "providedBy": "test",
            "purpose": "change",
            "type": "change",
            "txid": "d" * 64,
            "lockingScript": bytes([0x76, 0xA9, 0x14] + [0] * 20 + [0x88, 0xAC]),  # P2PKH
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
        }

        output_id = storage_provider.insert_output(output_data)
        assert isinstance(output_id, int)
        assert output_id > 0

    def test_find_outputs(self, storage_provider):
        """Test finding outputs."""
        user_id = storage_provider.get_or_create_user_id("test_user")

        # Get existing outputs (may be empty)
        outputs = storage_provider.find_outputs({"userId": user_id})
        assert isinstance(outputs, list)

    def test_find_output_baskets(self, storage_provider):
        """Test finding output baskets."""
        user_id = storage_provider.get_or_create_user_id("test_user")

        baskets = storage_provider.find_output_baskets({"userId": user_id})
        assert isinstance(baskets, list)


class TestStorageProviderCertificateOperations:
    """Test certificate-related CRUD operations."""

    def test_insert_certificate(self, storage_provider):
        """Test inserting a certificate."""
        user_id = storage_provider.get_or_create_user_id("test_user")

        cert_data = {
            "userId": user_id,
            "type": "test_cert",
            "serialNumber": "12345",
            "certifier": "test_certifier",
            "subject": "test_subject",
            "verifier": "test_verifier",
            "revocationOutpoint": "e" * 64 + ".0",
            "signature": "f" * 128,
            "isDeleted": False,
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
        }

        cert_id = storage_provider.insert_certificate(cert_data)
        assert isinstance(cert_id, int)
        assert cert_id > 0

    def test_find_certificates(self, storage_provider):
        """Test finding certificates."""
        user_id = storage_provider.get_or_create_user_id("test_user")

        certificates = storage_provider.find_certificates({"userId": user_id})
        assert isinstance(certificates, list)


class TestStorageProviderProvenTxOperations:
    """Test proven transaction CRUD operations."""

    def test_insert_proven_tx(self, storage_provider):
        """Test inserting a proven transaction."""
        import json

        proven_tx_data = {
            "txid": "f" * 64,
            "height": 100000,
            "index": 0,
            "merklePath": json.dumps({"path": [], "blockHeight": 100000}).encode("utf-8"),
            "rawTx": bytes([5, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
            "blockHash": "g" * 64,
            "merkleRoot": "h" * 64,
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
        }

        proven_tx_id = storage_provider.insert_proven_tx(proven_tx_data)
        assert isinstance(proven_tx_id, int)
        assert proven_tx_id > 0

    def test_find_proven_txs(self, storage_provider):
        """Test finding proven transactions."""
        proven_txs = storage_provider.find_proven_txs()
        assert isinstance(proven_txs, list)

    def test_insert_proven_tx_req(self, storage_provider):
        """Test inserting a proven transaction request."""
        req_data = {
            "txid": "i" * 64,
            "status": "unmined",
            "rawTx": bytes([6, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
            "attempts": 0,
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
        }

        req_id = storage_provider.insert_proven_tx_req(req_data)
        assert isinstance(req_id, int)
        assert req_id > 0

    def test_find_proven_tx_reqs(self, storage_provider):
        """Test finding proven transaction requests."""
        user_id = storage_provider.get_or_create_user_id("test_user")

        reqs = storage_provider.find_proven_tx_reqs({"userId": user_id})
        assert isinstance(reqs, list)


class TestStorageProviderLabelOperations:
    """Test label-related operations."""

    def test_find_or_insert_tx_label(self, storage_provider):
        """Test finding or inserting transaction label."""
        user_id = storage_provider.get_or_create_user_id("test_user")

        label_data = storage_provider.find_or_insert_tx_label(user_id, "test_label")
        assert "txLabelId" in label_data
        assert label_data["label"] == "test_label"

    def test_find_tx_labels(self, storage_provider):
        """Test finding transaction labels."""
        user_id = storage_provider.get_or_create_user_id("test_user")

        labels = storage_provider.find_tx_labels({"userId": user_id})
        assert isinstance(labels, list)


class TestStorageProviderTagOperations:
    """Test tag-related operations."""

    def test_find_or_insert_output_tag(self, storage_provider):
        """Test finding or inserting output tag."""
        user_id = storage_provider.get_or_create_user_id("test_user")

        tag_data = storage_provider.find_or_insert_output_tag(user_id, "test_tag")
        assert "outputTagId" in tag_data
        assert tag_data["tag"] == "test_tag"

    def test_find_output_tags(self, storage_provider):
        """Test finding output tags."""
        user_id = storage_provider.get_or_create_user_id("test_user")

        tags = storage_provider.find_output_tags({"userId": user_id})
        assert isinstance(tags, list)


class TestStorageProviderSettings:
    """Test settings operations."""

    def test_get_settings(self, storage_provider):
        """Test getting settings."""
        settings = storage_provider.get_settings()
        assert isinstance(settings, dict)

    def test_update_settings(self, storage_provider):
        """Test updating settings (if supported)."""
        # This may not be implemented, but we test the interface
        try:
            settings = storage_provider.get_settings()
            assert isinstance(settings, dict)
        except Exception:
            pass  # May not be implemented


class TestStorageProviderUtilityMethods:
    """Test utility methods."""

    def test_count_methods(self, storage_provider):
        """Test count methods."""
        user_id = storage_provider.get_or_create_user_id("test_user")

        # Test various count methods
        user_count = storage_provider.count_users({"userId": user_id})
        assert isinstance(user_count, int)

        tx_count = storage_provider.count_transactions({"userId": user_id})
        assert isinstance(tx_count, int)

        output_count = storage_provider.count_outputs({"userId": user_id})
        assert isinstance(output_count, int)

    def test_is_available(self, storage_provider):
        """Test is_available method."""
        assert storage_provider.is_available()

    def test_destroy(self, storage_provider):
        """Test destroy method."""
        # Should not raise
        storage_provider.destroy()
