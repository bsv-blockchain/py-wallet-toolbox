"""Coverage tests for storage entities.

This module provides comprehensive coverage for entity classes,
focusing on missing lines and edge cases.
"""

import json
from datetime import datetime
from typing import Any

import pytest

from bsv_wallet_toolbox.storage.entities import (
    Certificate,
    CertificateField,
    Commission,
    Output,
    OutputBasket,
    OutputTag,
    OutputTagMap,
    ProvenTx,
    ProvenTxReq,
    SyncState,
    Transaction,
    TxLabel,
    TxLabelMap,
    User,
)


class TestEntityCoverage:
    """Comprehensive coverage tests for all entity classes."""

    @pytest.fixture
    def sample_api_objects(self) -> dict[str, dict[str, Any]]:
        """Provide sample API objects for various entities."""
        return {
            "user": {
                "userId": 123,
                "identityKey": "test_identity_key",
                "activeStorage": "storage_key",
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            },
            "certificate": {
                "certificateId": 456,
                "userId": 123,
                "type": "identity",
                "serialNumber": "12345",
                "certifier": "test_certifier",
                "subject": "test_subject",
                "verifier": "test_verifier",
                "revocationOutpoint": "",
                "signature": "test_signature",
                "isDeleted": False,
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            },
            "certificate_field": {
                "certificateFieldId": 789,
                "certificateId": 456,
                "userId": 123,
                "fieldName": "test_field",
                "fieldValue": "test_value",
                "masterKey": "test_master_key",
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            },
            "commission": {
                "commissionId": 101,
                "transactionId": 202,
                "userId": 123,
                "satoshis": 50000,
                "isRedeemed": False,
                "keyOffset": "m/44'/0'/0'/0/1",
                "lockingScript": [118, 169, 20],  # P2PKH script bytes
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            },
            "output": {
                "outputId": 303,
                "transactionId": 202,
                "vout": 0,
                "satoshis": 100000,
                "lockingScript": [118, 169, 20, 255, 255, 255, 255, 136, 172],  # Full P2PKH
                "spentBy": None,
                "spentAt": None,
                "basketId": 404,
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            },
            "output_basket": {
                "basketId": 404,
                "userId": 123,
                "name": "default",
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            },
            "output_tag": {
                "tagId": 505,
                "userId": 123,
                "tag": "test_tag",
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            },
            "output_tag_map": {
                "mapId": 606,
                "outputId": 303,
                "tagId": 505,
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            },
            "proven_tx": {
                "provenTxId": 707,
                "txid": "a" * 64,
                "userId": 123,
                "rawTx": bytes([1, 2, 3, 4]),
                "proof": bytes([5, 6, 7, 8]),
                "blockHeight": 12345,
                "merkleRoot": "b" * 64,
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            },
            "proven_tx_req": {
                "reqId": 808,
                "userId": 123,
                "txid": "c" * 64,
                "callback": "test_callback",
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            },
            "sync_state": {
                "stateId": 1010,
                "userId": 123,
                "entityName": "Output",
                "entityId": 303,
                "version": 1,
                "data": json.dumps({"test": "data"}),
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            },
            "transaction": {
                "transactionId": 202,
                "userId": 123,
                "txid": "d" * 64,
                "rawTx": bytes([9, 10, 11, 12]),
                "description": "test transaction",
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            },
            "tx_label": {
                "labelId": 1111,
                "userId": 123,
                "label": "test_label",
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            },
            "tx_label_map": {
                "mapId": 1212,
                "transactionId": 202,
                "labelId": 1111,
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            },
        }

    def test_user_to_api_default_values(self, sample_api_objects) -> None:
        """Test User.to_api() with default values (line 99)."""
        user = User()
        api_result = user.to_api()

        # Verify all expected keys are present with default values
        assert "userId" in api_result
        assert "identityKey" in api_result
        assert "activeStorage" in api_result
        assert "createdAt" in api_result
        assert "updatedAt" in api_result
        assert api_result["userId"] == 0
        assert api_result["identityKey"] == ""

    def test_commission_constructor_defaults(self) -> None:
        """Test Commission constructor default initialization (lines 191-200)."""
        commission = Commission()

        # Verify default values are set correctly
        assert commission.commission_id == 0
        assert commission.transaction_id == 0
        assert commission.user_id == 0
        assert commission.satoshis == 0
        assert commission.is_redeemed is False
        assert commission.key_offset == ""
        assert commission.locking_script is None
        assert isinstance(commission.created_at, datetime)
        assert isinstance(commission.updated_at, datetime)

    def test_certificate_constructor_with_api_object(self, sample_api_objects) -> None:
        """Test Certificate constructor with API object (lines 308-332)."""
        cert = Certificate(sample_api_objects["certificate"])

        assert cert.certificate_id == 456
        assert cert.user_id == 123
        assert cert.type == "identity"
        assert cert.serial_number == "12345"
        assert cert.certifier == "test_certifier"
        assert cert.subject == "test_subject"
        assert cert.verifier == "test_verifier"
        assert cert.signature == "test_signature"
        assert cert.is_deleted is False
        assert isinstance(cert.created_at, datetime)
        assert isinstance(cert.updated_at, datetime)

    def test_certificate_to_api_method(self, sample_api_objects) -> None:
        """Test Certificate.to_api() method (line 404)."""
        cert = Certificate(sample_api_objects["certificate"])
        api_result = cert.to_api()

        assert "certificateId" in api_result
        assert "userId" in api_result
        assert "type" in api_result
        assert "subject" in api_result
        assert "fields" in api_result
        assert "signature" in api_result
        assert "verifier" in api_result
        assert "revokedAt" in api_result
        assert "createdAt" in api_result
        assert "updatedAt" in api_result

    def test_certificate_field_constructor_defaults(self) -> None:
        """Test CertificateField constructor defaults (lines 465-473)."""
        field = CertificateField()

        assert field.field_id == 0
        assert field.certificate_id == 0
        assert field.field_name == ""
        assert field.field_value == ""
        assert isinstance(field.created_at, datetime)
        assert isinstance(field.updated_at, datetime)

    def test_output_constructor_with_api_object(self, sample_api_objects) -> None:
        """Test Output constructor with API object (line 605)."""
        output = Output(sample_api_objects["output"])

        assert output.output_id == 303
        assert output.transaction_id == 202
        assert output.vout == 0
        assert output.satoshis == 100000
        assert output.locking_script == [118, 169, 20, 255, 255, 255, 255, 136, 172]
        assert output.spent_by is None
        assert output.spent_at is None
        assert output.basket_id == 404

    def test_output_basket_merge_new_raises_error(self) -> None:
        """Test OutputBasket.merge_new() raises error (line 719)."""
        basket = OutputBasket()

        with pytest.raises(NotImplementedError):
            basket.merge_new({})

    def test_output_tag_to_api_method(self) -> None:
        """Test OutputTag.to_api() method (line 738)."""
        tag = OutputTag()
        api_result = tag.to_api()

        assert "tagId" in api_result
        assert "userId" in api_result
        assert "tag" in api_result
        assert "createdAt" in api_result
        assert "updatedAt" in api_result

    def test_output_tag_constructor_defaults(self) -> None:
        """Test OutputTag constructor defaults (lines 741, 746)."""
        tag = OutputTag()

        assert tag.tag_id == 0
        assert tag.user_id == 0
        assert tag.tag == ""
        assert isinstance(tag.created_at, datetime)
        assert isinstance(tag.updated_at, datetime)

    def test_output_tag_map_to_api_method(self) -> None:
        """Test OutputTagMap.to_api() method (line 763)."""
        tag_map = OutputTagMap()
        api_result = tag_map.to_api()

        assert "mapId" in api_result
        assert "outputId" in api_result
        assert "tagId" in api_result
        assert "createdAt" in api_result
        assert "updatedAt" in api_result

    def test_proven_tx_constructor_with_api_object(self, sample_api_objects) -> None:
        """Test ProvenTx constructor with API object (line 788)."""
        proven_tx = ProvenTx(sample_api_objects["proven_tx"])

        assert proven_tx.proven_tx_id == 707
        assert proven_tx.txid == "a" * 64
        assert proven_tx.user_id == 123
        assert proven_tx.raw_tx == bytes([1, 2, 3, 4])
        assert proven_tx.proof == bytes([5, 6, 7, 8])
        assert proven_tx.block_height == 12345
        assert proven_tx.merkle_root == "b" * 64

    def test_proven_tx_req_constructor_with_api_object(self, sample_api_objects) -> None:
        """Test ProvenTxReq constructor with API object (lines 819-829)."""
        req = ProvenTxReq(sample_api_objects["proven_tx_req"])

        assert req.req_id == 808
        assert req.user_id == 123
        assert req.txid == "c" * 64
        assert req.callback == "test_callback"
        assert isinstance(req.created_at, datetime)
        assert isinstance(req.updated_at, datetime)


    def test_sync_state_constructor_with_api_object(self, sample_api_objects) -> None:
        """Test SyncState constructor with API object (line 897)."""
        state = SyncState(sample_api_objects["sync_state"])

        assert state.state_id == 1010
        assert state.user_id == 123
        assert state.entity_name == "Output"
        assert state.entity_id == 303
        assert state.version == 1
        assert state.data == json.dumps({"test": "data"})

    def test_transaction_constructor_with_api_object(self, sample_api_objects) -> None:
        """Test Transaction constructor with API object (line 913)."""
        tx = Transaction(sample_api_objects["transaction"])

        assert tx.transaction_id == 202
        assert tx.user_id == 123
        assert tx.txid == "d" * 64
        assert tx.raw_tx == bytes([9, 10, 11, 12])
        assert tx.description == "test transaction"

    def test_transaction_to_api_method(self) -> None:
        """Test Transaction.to_api() method (line 920)."""
        tx = Transaction()
        api_result = tx.to_api()

        assert "transactionId" in api_result
        assert "userId" in api_result
        assert "txid" in api_result
        assert "rawTx" in api_result
        assert "description" in api_result
        assert "createdAt" in api_result
        assert "updatedAt" in api_result

    def test_tx_label_constructor_with_api_object(self, sample_api_objects) -> None:
        """Test TxLabel constructor with API object (line 928)."""
        label = TxLabel(sample_api_objects["tx_label"])

        assert label.label_id == 1111
        assert label.user_id == 123
        assert label.label == "test_label"
        assert isinstance(label.created_at, datetime)
        assert isinstance(label.updated_at, datetime)

    def test_tx_label_map_constructor_with_api_object(self, sample_api_objects) -> None:
        """Test TxLabelMap constructor with API object (line 939)."""
        label_map = TxLabelMap(sample_api_objects["tx_label_map"])

        assert label_map.map_id == 1212
        assert label_map.transaction_id == 202
        assert label_map.label_id == 1111
        assert isinstance(label_map.created_at, datetime)
        assert isinstance(label_map.updated_at, datetime)

    def test_certificate_merge_existing_method(self) -> None:
        """Test Certificate.merge_existing() method (lines 1017-1031)."""
        cert = Certificate()
        existing_data = {"type": "updated_type", "subject": "updated_subject"}

        # merge_existing should update the certificate
        cert.merge_existing(existing_data)

        assert cert.type == "updated_type"
        assert cert.subject == "updated_subject"

    def test_certificate_merge_new_raises_error(self) -> None:
        """Test Certificate.merge_new() raises error (lines 1046-1047)."""
        cert = Certificate()

        with pytest.raises(NotImplementedError):
            cert.merge_new({})

    def test_output_merge_existing_method(self) -> None:
        """Test Output.merge_existing() method (line 1070)."""
        output = Output()
        existing_data = {"satoshis": 200000, "spentBy": 12345}

        output.merge_existing(existing_data)

        assert output.satoshis == 200000
        assert output.spent_by == 12345

    def test_output_basket_constructor_defaults(self) -> None:
        """Test OutputBasket constructor defaults (lines 1074, 1078)."""
        basket = OutputBasket()

        assert basket.basket_id == 0
        assert basket.user_id == 0
        assert basket.name == ""
        assert isinstance(basket.created_at, datetime)
        assert isinstance(basket.updated_at, datetime)

    def test_proven_tx_to_api_method(self) -> None:
        """Test ProvenTx.to_api() method (line 1107)."""
        proven_tx = ProvenTx()
        api_result = proven_tx.to_api()

        assert "provenTxId" in api_result
        assert "txid" in api_result
        assert "userId" in api_result
        assert "rawTx" in api_result
        assert "proof" in api_result
        assert "blockHeight" in api_result
        assert "merkleRoot" in api_result
        assert "createdAt" in api_result
        assert "updatedAt" in api_result

    def test_proven_tx_req_to_api_method(self) -> None:
        """Test ProvenTxReq.to_api() method (lines 1127-1130)."""
        req = ProvenTxReq()
        api_result = req.to_api()

        assert "reqId" in api_result
        assert "userId" in api_result
        assert "txid" in api_result
        assert "callback" in api_result
        assert "createdAt" in api_result
        assert "updatedAt" in api_result

    def test_proven_tx_req_constructor_defaults(self) -> None:
        """Test ProvenTxReq constructor defaults (lines 1134, 1140, 1143-1144)."""
        req = ProvenTxReq()

        assert req.req_id == 0
        assert req.user_id == 0
        assert req.txid == ""
        assert req.callback == ""
        assert isinstance(req.created_at, datetime)
        assert isinstance(req.updated_at, datetime)


    def test_sync_state_to_api_method(self) -> None:
        """Test SyncState.to_api() method (line 1165)."""
        state = SyncState()
        api_result = state.to_api()

        assert "stateId" in api_result
        assert "userId" in api_result
        assert "entityName" in api_result
        assert "entityId" in api_result
        assert "version" in api_result
        assert "data" in api_result
        assert "createdAt" in api_result
        assert "updatedAt" in api_result

    def test_sync_state_constructor_defaults(self) -> None:
        """Test SyncState constructor defaults (lines 1168-1170, 1177)."""
        state = SyncState()

        assert state.state_id == 0
        assert state.user_id == 0
        assert state.entity_name == ""
        assert state.entity_id == 0
        assert state.version == 0
        assert state.data == ""
        assert isinstance(state.created_at, datetime)
        assert isinstance(state.updated_at, datetime)

    def test_transaction_merge_existing_method(self) -> None:
        """Test Transaction.merge_existing() method (lines 1186-1200)."""
        tx = Transaction()
        existing_data = {"description": "updated description", "rawTx": bytes([1, 2, 3])}

        tx.merge_existing(existing_data)

        assert tx.description == "updated description"
        assert tx.raw_tx == bytes([1, 2, 3])

    def test_tx_label_to_api_method(self) -> None:
        """Test TxLabel.to_api() method (lines 1234-1246)."""
        label = TxLabel()
        api_result = label.to_api()

        assert "labelId" in api_result
        assert "userId" in api_result
        assert "label" in api_result
        assert "createdAt" in api_result
        assert "updatedAt" in api_result

    def test_tx_label_constructor_defaults(self) -> None:
        """Test TxLabel constructor defaults (line 1294)."""
        label = TxLabel()

        assert label.label_id == 0
        assert label.user_id == 0
        assert label.label == ""
        assert isinstance(label.created_at, datetime)
        assert isinstance(label.updated_at, datetime)

    def test_tx_label_map_to_api_method(self) -> None:
        """Test TxLabelMap.to_api() method (line 1327)."""
        label_map = TxLabelMap()
        api_result = label_map.to_api()

        assert "mapId" in api_result
        assert "transactionId" in api_result
        assert "labelId" in api_result
        assert "createdAt" in api_result
        assert "updatedAt" in api_result

    def test_certificate_field_merge_existing_method(self) -> None:
        """Test CertificateField.merge_existing() method (lines 1350-1358)."""
        field = CertificateField()
        existing_data = {"fieldName": "updated_name", "fieldValue": "updated_value"}

        field.merge_existing(existing_data)

        assert field.field_name == "updated_name"
        assert field.field_value == "updated_value"

    def test_certificate_field_to_api_method(self) -> None:
        """Test CertificateField.to_api() method (line 1375)."""
        field = CertificateField()
        api_result = field.to_api()

        assert "fieldId" in api_result
        assert "certificateId" in api_result
        assert "fieldName" in api_result
        assert "fieldValue" in api_result
        assert "createdAt" in api_result
        assert "updatedAt" in api_result

    def test_commission_merge_existing_method(self) -> None:
        """Test Commission.merge_existing() method (line 1398)."""
        commission = Commission()
        existing_data = {"satoshis": 75000, "isRedeemed": True}

        commission.merge_existing(existing_data)

        assert commission.satoshis == 75000
        assert commission.is_redeemed is True

    def test_output_to_api_method(self) -> None:
        """Test Output.to_api() method (line 1422)."""
        output = Output()
        api_result = output.to_api()

        assert "outputId" in api_result
        assert "transactionId" in api_result
        assert "vout" in api_result
        assert "satoshis" in api_result
        assert "lockingScript" in api_result
        assert "spentBy" in api_result
        assert "spentAt" in api_result
        assert "basketId" in api_result
        assert "createdAt" in api_result
        assert "updatedAt" in api_result

    def test_output_tag_map_constructor_defaults(self) -> None:
        """Test OutputTagMap constructor defaults (lines 1445-1450)."""
        tag_map = OutputTagMap()

        assert tag_map.map_id == 0
        assert tag_map.output_id == 0
        assert tag_map.tag_id == 0
        assert isinstance(tag_map.created_at, datetime)
        assert isinstance(tag_map.updated_at, datetime)

    def test_tx_label_map_constructor_defaults(self) -> None:
        """Test TxLabelMap constructor defaults (line 1466)."""
        label_map = TxLabelMap()

        assert label_map.map_id == 0
        assert label_map.transaction_id == 0
        assert label_map.label_id == 0
        assert isinstance(label_map.created_at, datetime)
        assert isinstance(label_map.updated_at, datetime)


    def test_proven_tx_merge_existing_method(self) -> None:
        """Test ProvenTx.merge_existing() method (line 1558)."""
        proven_tx = ProvenTx()
        existing_data = {"blockHeight": 67890, "merkleRoot": "e" * 64}

        proven_tx.merge_existing(existing_data)

        assert proven_tx.block_height == 67890
        assert proven_tx.merkle_root == "e" * 64

    def test_proven_tx_req_merge_existing_method(self) -> None:
        """Test ProvenTxReq.merge_existing() method (line 1562)."""
        req = ProvenTxReq()
        existing_data = {"callback": "updated_callback"}

        req.merge_existing(existing_data)

        assert req.callback == "updated_callback"

    def test_sync_state_merge_existing_method(self) -> None:
        """Test SyncState.merge_existing() method (line 1587)."""
        state = SyncState()
        existing_data = {"version": 2, "data": json.dumps({"updated": "data"})}

        state.merge_existing(existing_data)

        assert state.version == 2
        assert state.data == json.dumps({"updated": "data"})

    def test_certificate_field_merge_new_raises_error(self) -> None:
        """Test CertificateField.merge_new() raises error (line 1671)."""
        field = CertificateField()

        with pytest.raises(NotImplementedError):
            field.merge_new({})

    def test_commission_to_api_method(self) -> None:
        """Test Commission.to_api() method (lines 1682-1684)."""
        commission = Commission()
        api_result = commission.to_api()

        assert "commissionId" in api_result
        assert "transactionId" in api_result
        assert "userId" in api_result
        assert "satoshis" in api_result
        assert "isRedeemed" in api_result
        assert "keyOffset" in api_result
        assert "lockingScript" in api_result
        assert "createdAt" in api_result
        assert "updatedAt" in api_result

    def test_tx_label_merge_existing_method(self) -> None:
        """Test TxLabel.merge_existing() method (line 1689)."""
        label = TxLabel()
        existing_data = {"label": "updated_label"}

        label.merge_existing(existing_data)

        assert label.label == "updated_label"

    def test_tx_label_map_merge_existing_method(self) -> None:
        """Test TxLabelMap.merge_existing() method (line 1733)."""
        label_map = TxLabelMap()
        existing_data = {"transactionId": 999, "labelId": 888}

        label_map.merge_existing(existing_data)

        assert label_map.transaction_id == 999
        assert label_map.label_id == 888

    def test_output_tag_merge_existing_method(self) -> None:
        """Test OutputTag.merge_existing() method (line 1794)."""
        tag = OutputTag()
        existing_data = {"tag": "updated_tag"}

        tag.merge_existing(existing_data)

        assert tag.tag == "updated_tag"

    def test_output_tag_map_merge_existing_method(self) -> None:
        """Test OutputTagMap.merge_existing() method (line 1826)."""
        tag_map = OutputTagMap()
        existing_data = {"outputId": 777, "tagId": 666}

        tag_map.merge_existing(existing_data)

        assert tag_map.output_id == 777
        assert tag_map.tag_id == 666
