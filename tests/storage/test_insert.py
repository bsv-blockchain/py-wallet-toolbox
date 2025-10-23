"""Unit tests for storage INSERT operations.

Reference: wallet-toolbox/test/storage/insert.test.ts
"""


import pytest


class Testinsert:
    """Test suite for database INSERT operations."""

    @pytest.mark.skip(reason="Storage implementation not implemented yet")
    @pytest.mark.asyncio
    async def test_insert_proventx(self) -> None:
        """Given: Mock storage with test ProvenTx data
           When: Insert ProvenTx, then attempt duplicate insert
           Then: First insert succeeds, duplicate throws error

        Reference: test/storage/insert.test.ts
                  test('0 insert ProvenTx')
        """
        # Given

        mock_storage = type("MockStorage", (), {"insert_proven_tx": lambda self, ptx: None})()

        ptx = {"provenTxId": 0, "txid": "1" * 64, "height": 100, "index": 0, "merklePath": [], "rawTx": b"test"}

        # When
        ptx_id = await mock_storage.insert_proven_tx(ptx)

        # Then
        assert ptx_id == 1

        # Duplicate must throw
        ptx["provenTxId"] = 0
        with pytest.raises(Exception):
            await mock_storage.insert_proven_tx(ptx)

    @pytest.mark.skip(reason="Storage implementation not implemented yet")
    @pytest.mark.asyncio
    async def test_insert_proventxreq(self) -> None:
        """Given: Mock storage with test ProvenTxReq data
           When: Insert ProvenTxReq, then attempt duplicate and invalid foreign key
           Then: First insert succeeds, duplicate throws, invalid FK throws

        Reference: test/storage/insert.test.ts
                  test('1 insert ProvenTxReq')
        """
        # Given

        mock_storage = type("MockStorage", (), {"insert_proven_tx_req": lambda self, ptxreq: None})()

        ptxreq = {"provenTxReqId": 0, "txid": "2" * 64, "status": "unsent", "attempts": 0}

        # When
        ptxreq_id = await mock_storage.insert_proven_tx_req(ptxreq)

        # Then
        assert ptxreq_id == 1

        # Duplicate must throw
        ptxreq["provenTxReqId"] = 0
        with pytest.raises(Exception):
            await mock_storage.insert_proven_tx_req(ptxreq)

    @pytest.mark.skip(reason="Storage implementation not implemented yet")
    @pytest.mark.asyncio
    async def test_insert_user(self) -> None:
        """Given: Mock storage with test User data
           When: Insert User, then attempt duplicate
           Then: First insert succeeds, duplicate throws error

        Reference: test/storage/insert.test.ts
                  test('2 insert User')
        """
        # Given

        mock_storage = type("MockStorage", (), {"insert_user": lambda self, user: None})()

        user = {"userId": 0, "identityKey": "03" + "0" * 64, "created_at": None, "updated_at": None}

        # When
        user_id = await mock_storage.insert_user(user)

        # Then
        assert user_id > 0

        # Duplicate must throw
        user["userId"] = 0
        with pytest.raises(Exception):
            await mock_storage.insert_user(user)

    @pytest.mark.skip(reason="Storage implementation not implemented yet")
    @pytest.mark.asyncio
    async def test_insert_certificate(self) -> None:
        """Given: Mock storage with test Certificate data
           When: Insert Certificate, then attempt duplicate
           Then: First insert succeeds, duplicate throws error

        Reference: test/storage/insert.test.ts
                  test('3 insert Certificate')
        """
        # Given

        mock_storage = type("MockStorage", (), {"insert_certificate": lambda self, cert: None})()

        cert = {
            "certificateId": 0,
            "userId": 1,
            "type": "test_type",
            "serialNumber": "serial123",
            "subject": "test_subject",
            "certifier": "03" + "0" * 64,
            "created_at": None,
            "updated_at": None,
        }

        # When
        cert_id = await mock_storage.insert_certificate(cert)

        # Then
        assert cert_id > 0

        # Duplicate must throw
        cert["certificateId"] = 0
        with pytest.raises(Exception):
            await mock_storage.insert_certificate(cert)

    @pytest.mark.skip(reason="Storage implementation not implemented yet")
    @pytest.mark.asyncio
    async def test_insert_certificatefield(self) -> None:
        """Given: Mock storage with test CertificateField data
           When: Insert CertificateField, then attempt duplicate
           Then: First insert succeeds, duplicate throws error

        Reference: test/storage/insert.test.ts
                  test('4 insert CertificateField')
        """
        # Given

        mock_storage = type("MockStorage", (), {"insert_certificate_field": lambda self, field: None})()

        field = {
            "certificateId": 1,
            "userId": 1,
            "fieldName": "prize",
            "fieldValue": "starship",
            "masterKey": "master123",
            "created_at": None,
            "updated_at": None,
        }

        # When
        await mock_storage.insert_certificate_field(field)

        # Then
        assert field["certificateId"] == 1
        assert field["fieldName"] == "prize"

        # Duplicate must throw
        with pytest.raises(Exception):
            await mock_storage.insert_certificate_field(field)

    @pytest.mark.skip(reason="Storage implementation not implemented yet")
    @pytest.mark.asyncio
    async def test_insert_outputbasket(self) -> None:
        """Given: Mock storage with test OutputBasket data
           When: Insert OutputBasket, then attempt duplicate
           Then: First insert succeeds, duplicate throws error

        Reference: test/storage/insert.test.ts
                  test('5 insert OutputBasket')
        """
        # Given

        mock_storage = type("MockStorage", (), {"insert_output_basket": lambda self, basket: None})()

        basket = {
            "basketId": 0,
            "userId": 1,
            "name": "test_basket",
            "numberOfDesiredUTXOs": 10,
            "minimumDesiredUTXOValue": 1000,
            "isDeleted": False,
            "created_at": None,
            "updated_at": None,
        }

        # When
        basket_id = await mock_storage.insert_output_basket(basket)

        # Then
        assert basket_id > 0

        # Duplicate must throw
        basket["basketId"] = 0
        with pytest.raises(Exception):
            await mock_storage.insert_output_basket(basket)

    @pytest.mark.skip(reason="Storage implementation not implemented yet")
    @pytest.mark.asyncio
    async def test_insert_transaction(self) -> None:
        """Given: Mock storage with test Transaction data
           When: Insert Transaction, then attempt duplicate
           Then: First insert succeeds, duplicate throws error

        Reference: test/storage/insert.test.ts
                  test('6 insert Transaction')
        """
        # Given

        mock_storage = type("MockStorage", (), {"insert_transaction": lambda self, tx: None})()

        tx = {
            "transactionId": 0,
            "userId": 1,
            "txid": "5" * 64,
            "status": "sending",
            "reference": "ref123",
            "isOutgoing": True,
            "satoshis": 5000,
            "description": "Test transaction",
            "created_at": None,
            "updated_at": None,
        }

        # When
        tx_id = await mock_storage.insert_transaction(tx)

        # Then
        assert tx_id > 0

        # Duplicate must throw
        tx["transactionId"] = 0
        with pytest.raises(Exception):
            await mock_storage.insert_transaction(tx)

    @pytest.mark.skip(reason="Storage implementation not implemented yet")
    @pytest.mark.asyncio
    async def test_insert_commission(self) -> None:
        """Given: Mock storage with test Commission data
           When: Insert Commission, then attempt duplicate
           Then: First insert succeeds, duplicate throws error

        Reference: test/storage/insert.test.ts
                  test('7 insert Commission')
        """
        # Given

        mock_storage = type("MockStorage", (), {"insert_commission": lambda self, comm: None})()

        commission = {
            "commissionId": 0,
            "transactionId": 1,
            "userId": 1,
            "isRedeemed": False,
            "keyOffset": "offset123",
            "lockingScript": [1, 2, 3],
            "satoshis": 500,
            "created_at": None,
            "updated_at": None,
        }

        # When
        comm_id = await mock_storage.insert_commission(commission)

        # Then
        assert comm_id > 0

        # Duplicate must throw
        commission["commissionId"] = 0
        with pytest.raises(Exception):
            await mock_storage.insert_commission(commission)

    @pytest.mark.skip(reason="Storage implementation not implemented yet")
    @pytest.mark.asyncio
    async def test_insert_output(self) -> None:
        """Given: Mock storage with test Output data
           When: Insert Output, then attempt duplicate
           Then: First insert succeeds, duplicate throws error

        Reference: test/storage/insert.test.ts
                  test('8 insert Output')
        """
        # Given

        mock_storage = type("MockStorage", (), {"insert_output": lambda self, output: None})()

        output = {
            "outputId": 0,
            "transactionId": 1,
            "userId": 1,
            "vout": 0,
            "satoshis": 101,
            "lockingScript": [1, 2, 3],
            "spendable": True,
            "created_at": None,
            "updated_at": None,
        }

        # When
        output_id = await mock_storage.insert_output(output)

        # Then
        assert output_id > 0
        assert output["userId"] == 1
        assert output["vout"] == 0

        # Duplicate must throw
        output["outputId"] = 0
        with pytest.raises(Exception):
            await mock_storage.insert_output(output)

    @pytest.mark.skip(reason="Storage implementation not implemented yet")
    @pytest.mark.asyncio
    async def test_insert_outputtag(self) -> None:
        """Given: Mock storage with test OutputTag data
           When: Insert OutputTag, then attempt duplicate
           Then: First insert succeeds, duplicate throws error

        Reference: test/storage/insert.test.ts
                  test('9 insert OutputTag')
        """
        # Given

        mock_storage = type("MockStorage", (), {"insert_output_tag": lambda self, tag: None})()

        tag = {
            "outputTagId": 0,
            "userId": 1,
            "tag": "test_tag",
            "isDeleted": False,
            "created_at": None,
            "updated_at": None,
        }

        # When
        tag_id = await mock_storage.insert_output_tag(tag)

        # Then
        assert tag_id > 0
        assert tag["userId"] == 1

        # Duplicate must throw
        tag["outputTagId"] = 0
        with pytest.raises(Exception):
            await mock_storage.insert_output_tag(tag)

    @pytest.mark.skip(reason="Storage implementation not implemented yet")
    @pytest.mark.asyncio
    async def test_insert_outputtagmap(self) -> None:
        """Given: Mock storage with test OutputTagMap data
           When: Insert OutputTagMap, then attempt duplicate
           Then: First insert succeeds, duplicate throws error

        Reference: test/storage/insert.test.ts
                  test('10 insert OutputTagMap')
        """
        # Given

        mock_storage = type("MockStorage", (), {"insert_output_tag_map": lambda self, tagmap: None})()

        tagmap = {"outputId": 1, "outputTagId": 1, "isDeleted": False, "created_at": None, "updated_at": None}

        # When
        await mock_storage.insert_output_tag_map(tagmap)

        # Then
        assert tagmap["outputId"] == 1
        assert tagmap["outputTagId"] == 1

        # Duplicate must throw
        with pytest.raises(Exception):
            await mock_storage.insert_output_tag_map(tagmap)

    @pytest.mark.skip(reason="Storage implementation not implemented yet")
    @pytest.mark.asyncio
    async def test_insert_txlabel(self) -> None:
        """Given: Mock storage with test TxLabel data
           When: Insert TxLabel, then attempt duplicate
           Then: First insert succeeds, duplicate throws error

        Reference: test/storage/insert.test.ts
                  test('11 insert TxLabel')
        """
        # Given

        mock_storage = type("MockStorage", (), {"insert_tx_label": lambda self, label: None})()

        label = {
            "txLabelId": 0,
            "userId": 1,
            "label": "test_label",
            "isDeleted": False,
            "created_at": None,
            "updated_at": None,
        }

        # When
        label_id = await mock_storage.insert_tx_label(label)

        # Then
        assert label_id > 0
        assert label["userId"] == 1

        # Duplicate must throw
        label["txLabelId"] = 0
        with pytest.raises(Exception):
            await mock_storage.insert_tx_label(label)

    @pytest.mark.skip(reason="Storage implementation not implemented yet")
    @pytest.mark.asyncio
    async def test_insert_txlabelmap(self) -> None:
        """Given: Mock storage with test TxLabelMap data
           When: Insert TxLabelMap, then attempt duplicate
           Then: First insert succeeds, duplicate throws error

        Reference: test/storage/insert.test.ts
                  test('12 insert TxLabelMap')
        """
        # Given

        mock_storage = type("MockStorage", (), {"insert_tx_label_map": lambda self, labelmap: None})()

        labelmap = {"transactionId": 1, "txLabelId": 1, "isDeleted": False, "created_at": None, "updated_at": None}

        # When
        await mock_storage.insert_tx_label_map(labelmap)

        # Then
        assert labelmap["transactionId"] == 1
        assert labelmap["txLabelId"] == 1

        # Duplicate must throw
        with pytest.raises(Exception):
            await mock_storage.insert_tx_label_map(labelmap)

    @pytest.mark.skip(reason="Storage implementation not implemented yet")
    @pytest.mark.asyncio
    async def test_insert_monitorevent(self) -> None:
        """Given: Mock storage with test MonitorEvent data
           When: Insert MonitorEvent
           Then: Insert succeeds with valid ID

        Reference: test/storage/insert.test.ts
                  test('13 insert MonitorEvent')
        """
        # Given

        mock_storage = type("MockStorage", (), {"insert_monitor_event": lambda self, event: None})()

        event = {"id": 0, "created_at": None, "event": "test_event", "data": {}}

        # When
        event_id = await mock_storage.insert_monitor_event(event)

        # Then
        assert event_id > 0

    @pytest.mark.skip(reason="Storage implementation not implemented yet")
    @pytest.mark.asyncio
    async def test_insert_syncstate(self) -> None:
        """Given: Mock storage with test SyncState data
           When: Insert SyncState
           Then: Insert succeeds with valid ID

        Reference: test/storage/insert.test.ts
                  test('14 insert SyncState')
        """
        # Given

        mock_storage = type("MockStorage", (), {"insert_sync_state": lambda self, state: None})()

        state = {
            "syncStateId": 0,
            "userId": 1,
            "storageIdentityKey": "03" + "0" * 64,
            "created_at": None,
            "updated_at": None,
        }

        # When
        state_id = await mock_storage.insert_sync_state(state)

        # Then
        assert state_id > 0
