"""Unit tests for storage INSERT operations.

Reference: wallet-toolbox/test/storage/insert.test.ts
"""

from datetime import datetime

import pytest

from bsv_wallet_toolbox.storage.db import create_engine_from_url
from bsv_wallet_toolbox.storage.models import Base
from bsv_wallet_toolbox.storage.provider import StorageProvider


@pytest.fixture
def storage():
    """Create in-memory SQLite storage for testing."""
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return StorageProvider(engine=engine, chain="main", storage_identity_key="test")


@pytest.fixture
def user(storage):
    """Create test user in storage."""
    user_data = {"identityKey": "03" + "0" * 64, "activeStorage": ""}
    user_id = storage.insert_user(user_data)
    return user_id


class Testinsert:
    """Test suite for database INSERT operations."""

    def test_insert_proventx(self, storage) -> None:
        """Given: Storage provider with test ProvenTx data
           When: Insert ProvenTx, then attempt duplicate insert
           Then: First insert succeeds with auto-incremented ID, duplicate throws error

        Reference: test/storage/insert.test.ts
                  test('0 insert ProvenTx')
        """
        ptx = {
            "txid": "1" * 64,
            "height": 100,
            "index": 0,
            "merklePath": b"",  # Empty bytes, not empty list
            "rawTx": b"test",
            "blockHash": "block",
            "merkleRoot": "root",
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }

        ptx_id = storage.insert_proven_tx(ptx)
        assert ptx_id == 1

        with pytest.raises(Exception):
            storage.insert_proven_tx(ptx)

    def test_insert_proventxreq(self, storage) -> None:
        """Given: Storage provider with test ProvenTxReq data
           When: Insert ProvenTxReq, then attempt duplicate
           Then: First insert succeeds, duplicate throws error

        Reference: test/storage/insert.test.ts
                  test('1 insert ProvenTxReq')
        """
        ptxreq = {
            "txid": "2" * 64,
            "status": "unsent",
            "attempts": 0,
            "rawTx": b"test",  # Required field
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }

        ptxreq_id = storage.insert_proven_tx_req(ptxreq)
        assert ptxreq_id == 1

        with pytest.raises(Exception):
            storage.insert_proven_tx_req(ptxreq)

    def test_insert_user(self, storage) -> None:
        """Given: Storage provider with test User data
           When: Insert User
           Then: Insert succeeds with auto-incremented ID

        Reference: test/storage/insert.test.ts
                  test('2 insert User')
        """
        user = {"identityKey": "03" + "1" * 64, "activeStorage": "test"}

        user_id = storage.insert_user(user)
        assert user_id > 0

    def test_insert_certificate(self, storage, user) -> None:
        """Given: Storage provider with test Certificate data
           When: Insert Certificate
           Then: Insert succeeds with auto-incremented ID

        Reference: test/storage/insert.test.ts
                  test('3 insert Certificate')
        """
        cert = {
            "userId": user,
            "type": "test_type",
            "serialNumber": "serial123",
            "subject": "test_subject",
            "certifier": "03" + "0" * 64,
            "signature": "",
            "verifier": None,
            "revocationOutpoint": "0000000000000000000000000000000000000000000000000000000000000000.0",  # Required field
            "isDeleted": False,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }

        cert_id = storage.insert_certificate(cert)
        assert cert_id > 0

    def test_insert_certificatefield(self, storage, user) -> None:
        """Given: Storage provider with test CertificateField data
           When: Insert CertificateField
           Then: Insert succeeds

        Reference: test/storage/insert.test.ts
                  test('4 insert CertificateField')
        """
        cert = {
            "userId": user,
            "type": "test_type",
            "serialNumber": "serial123",
            "subject": "test_subject",
            "certifier": "03" + "0" * 64,
            "signature": "",
            "verifier": None,
            "revocationOutpoint": "0000000000000000000000000000000000000000000000000000000000000000.0",  # Required field
            "isDeleted": False,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }
        cert_id = storage.insert_certificate(cert)

        field = {
            "certificateId": cert_id,
            "userId": user,
            "fieldName": "prize",
            "fieldValue": "starship",
            "masterKey": "master123",
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }

        field_id = storage.insert_certificate_field(field)
        assert field_id is not None

    def test_insert_outputbasket(self, storage, user) -> None:
        """Given: Storage provider with test OutputBasket data
           When: Insert OutputBasket
           Then: Insert succeeds with auto-incremented ID

        Reference: test/storage/insert.test.ts
                  test('5 insert OutputBasket')
        """
        basket = {
            "userId": user,
            "name": "test_basket",
            "numberOfDesiredUTXOs": 10,
            "minimumDesiredUTXOValue": 1000,
            "isDeleted": False,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }

        basket_id = storage.insert_output_basket(basket)
        assert basket_id > 0

    def test_insert_transaction(self, storage, user) -> None:
        """Given: Storage provider with test Transaction data
           When: Insert Transaction
           Then: Insert succeeds with auto-incremented ID

        Reference: test/storage/insert.test.ts
                  test('6 insert Transaction')
        """
        tx = {
            "userId": user,
            "txid": "5" * 64,
            "status": "sending",
            "reference": "ref123",
            "isOutgoing": True,
            "satoshis": 5000,
            "description": "Test transaction",
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }

        tx_id = storage.insert_transaction(tx)
        assert tx_id > 0

    def test_insert_commission(self, storage, user) -> None:
        """Given: Storage provider with test Commission data
           When: Insert Commission
           Then: Insert succeeds with auto-incremented ID

        Reference: test/storage/insert.test.ts
                  test('7 insert Commission')
        """
        tx = {
            "userId": user,
            "txid": "6" * 64,
            "status": "sending",
            "reference": "",
            "isOutgoing": True,
            "satoshis": 5000,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }
        tx_id = storage.insert_transaction(tx)

        commission = {
            "transactionId": tx_id,
            "userId": user,
            "isRedeemed": False,
            "keyOffset": "offset123",
            "lockingScript": b"\x01\x02\x03",  # Should be bytes, not list
            "satoshis": 500,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }

        comm_id = storage.insert_commission(commission)
        assert comm_id > 0

    def test_insert_output(self, storage, user) -> None:
        """Given: Storage provider with test Output data
           When: Insert Output
           Then: Insert succeeds with auto-incremented ID

        Reference: test/storage/insert.test.ts
                  test('8 insert Output')
        """
        tx = {
            "userId": user,
            "txid": "7" * 64,
            "status": "sending",
            "reference": "",
            "isOutgoing": True,
            "satoshis": 5000,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }
        tx_id = storage.insert_transaction(tx)

        output = {
            "transactionId": tx_id,
            "userId": user,
            "vout": 0,
            "satoshis": 101,
            "lockingScript": b"\x01\x02\x03",  # Should be bytes, not list
            "spendable": True,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }

        output_id = storage.insert_output(output)
        assert output_id > 0

    def test_insert_outputtag(self, storage, user) -> None:
        """Given: Storage provider with test OutputTag data
           When: Insert OutputTag
           Then: Insert succeeds with auto-incremented ID

        Reference: test/storage/insert.test.ts
                  test('9 insert OutputTag')
        """
        tag = {
            "userId": user,
            "tag": "test_tag",
            "isDeleted": False,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }

        tag_id = storage.insert_output_tag(tag)
        assert tag_id > 0

    def test_insert_outputtagmap(self, storage, user) -> None:
        """Given: Storage provider with test OutputTagMap data
           When: Insert OutputTagMap
           Then: Insert succeeds

        Reference: test/storage/insert.test.ts
                  test('10 insert OutputTagMap')
        """
        tx = {
            "userId": user,
            "txid": "8" * 64,
            "status": "sending",
            "reference": "",
            "isOutgoing": True,
            "satoshis": 5000,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }
        tx_id = storage.insert_transaction(tx)

        output = {
            "transactionId": tx_id,
            "userId": user,
            "vout": 0,
            "satoshis": 101,
            "lockingScript": b"\x01\x02\x03",  # Should be bytes, not list
            "spendable": True,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }
        output_id = storage.insert_output(output)

        tag = {
            "userId": user,
            "tag": "test_tag",
            "isDeleted": False,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }
        tag_id = storage.insert_output_tag(tag)

        tagmap = {
            "outputId": output_id,
            "outputTagId": tag_id,
            "isDeleted": False,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }

        storage.insert_output_tag_map(tagmap)

    def test_insert_txlabel(self, storage, user) -> None:
        """Given: Storage provider with test TxLabel data
           When: Insert TxLabel
           Then: Insert succeeds with auto-incremented ID

        Reference: test/storage/insert.test.ts
                  test('11 insert TxLabel')
        """
        label = {
            "userId": user,
            "label": "test_label",
            "isDeleted": False,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }

        label_id = storage.insert_tx_label(label)
        assert label_id > 0

    def test_insert_txlabelmap(self, storage, user) -> None:
        """Given: Storage provider with test TxLabelMap data
           When: Insert TxLabelMap
           Then: Insert succeeds

        Reference: test/storage/insert.test.ts
                  test('12 insert TxLabelMap')
        """
        tx = {
            "userId": user,
            "txid": "9" * 64,
            "status": "sending",
            "reference": "",
            "isOutgoing": True,
            "satoshis": 5000,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }
        tx_id = storage.insert_transaction(tx)

        label = {
            "userId": user,
            "label": "test_label",
            "isDeleted": False,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }
        label_id = storage.insert_tx_label(label)

        labelmap = {
            "transactionId": tx_id,
            "txLabelId": label_id,
            "isDeleted": False,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }

        storage.insert_tx_label_map(labelmap)

    def test_insert_monitorevent(self, storage) -> None:
        """Given: Storage provider with test MonitorEvent data
           When: Insert MonitorEvent
           Then: Insert succeeds with valid ID

        Reference: test/storage/insert.test.ts
                  test('13 insert MonitorEvent')
        """
        event = {
            "createdAt": datetime.now(),
            "event": "test_event",
            "details": "{}",  # Correct field name is 'details', not 'data'
        }

        event_id = storage.insert_monitor_event(event)
        assert event_id > 0

    def test_insert_syncstate(self, storage, user) -> None:
        """Given: Storage provider with test SyncState data
           When: Insert SyncState
           Then: Insert succeeds with valid ID

        Reference: test/storage/insert.test.ts
                  test('14 insert SyncState')
        """
        state = {
            "userId": user,
            "storageIdentityKey": "03" + "0" * 64,
            "storageName": "test_storage",  # Required field
            "status": "unknown",  # Correct field name (not sync_status)
            "refNum": "0",  # Correct field name (not sync_ref_num), and should be string
            "syncMap": "{}",  # Required field
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }

        state_id = storage.insert_sync_state(state)
        assert state_id > 0
