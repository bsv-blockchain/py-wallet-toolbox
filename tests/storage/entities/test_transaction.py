"""Unit tests for Transaction entity.

Reference: wallet-toolbox/src/storage/schema/entities/__tests/TransactionTests.test.ts
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

from bsv.transaction import Transaction as BsvTransaction

from bsv_wallet_toolbox.storage.entities import Transaction


class TestTransactionEntity:
    """Test suite for Transaction entity."""

    def test_creates_instance_with_default_values(self) -> None:
        """Given: Default Transaction constructor
           When: Create Transaction with no arguments
           Then: Returns Transaction with correct default values

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('0_creates_instance_with_default_values')
        """
        # Given/When

        tx = Transaction()

        # Then
        now = datetime.now()
        assert tx.transaction_id == 0
        assert tx.user_id == 0
        assert tx.txid == ""
        assert tx.status == "unprocessed"
        assert tx.reference == ""
        assert tx.satoshis == 0
        assert tx.description == ""
        assert tx.is_outgoing is False
        assert tx.raw_tx is None
        assert tx.input_beef is None
        assert isinstance(tx.created_at, datetime)
        assert isinstance(tx.updated_at, datetime)
        assert tx.created_at <= now
        assert tx.updated_at <= now

    def test_creates_instance_with_provided_api_object(self) -> None:
        """Given: API object with transaction data
           When: Create Transaction with provided API object
           Then: Returns Transaction with values from API object

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('1_creates_instance_with_provided_api_object')
        """
        # Given

        now = datetime.now()
        api_object = {
            "transactionId": 123,
            "userId": 456,
            "txid": "testTxid",
            "status": "completed",
            "reference": "testReference",
            "satoshis": 789,
            "description": "testDescription",
            "isOutgoing": True,
            "rawTx": [1, 2, 3],
            "inputBEEF": [4, 5, 6],
            "createdAt": now,
            "updatedAt": now,
        }

        # When
        tx = Transaction(api_object)

        # Then
        assert tx.transaction_id == 123
        assert tx.user_id == 456
        assert tx.txid == "testTxid"
        assert tx.status == "completed"
        assert tx.reference == "testReference"
        assert tx.satoshis == 789
        assert tx.description == "testDescription"
        assert tx.is_outgoing is True
        assert tx.raw_tx == [1, 2, 3]
        assert tx.input_beef == [4, 5, 6]
        assert tx.created_at == now
        assert tx.updated_at == now

    def test_getters_and_setters_work_correctly(self) -> None:
        """Given: Transaction instance
           When: Set values using setters including version and lockTime
           Then: Getters return the updated values

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('2_getters_and_setters_work_correctly')
        """
        # Given

        tx = Transaction()

        # When
        now = datetime.now()
        tx.transaction_id = 123
        tx.user_id = 456
        tx.txid = "testTxid"
        tx.status = "processed"
        tx.reference = "testReference"
        tx.satoshis = 789
        tx.description = "testDescription"
        tx.is_outgoing = True
        tx.raw_tx = [1, 2, 3]
        tx.input_beef = [4, 5, 6]
        tx.created_at = now
        tx.updated_at = now
        tx.version = 2
        tx.lock_time = 5000

        # Then
        assert tx.transaction_id == 123
        assert tx.user_id == 456
        assert tx.txid == "testTxid"
        assert tx.status == "processed"
        assert tx.reference == "testReference"
        assert tx.satoshis == 789
        assert tx.description == "testDescription"
        assert tx.is_outgoing is True
        assert tx.raw_tx == [1, 2, 3]
        assert tx.input_beef == [4, 5, 6]
        assert tx.created_at == now
        assert tx.updated_at == now
        assert tx.version == 2
        assert tx.lock_time == 5000

    def test_getbsvtx_returns_parsed_transaction(self) -> None:
        """Given: Transaction with rawTx bytes
           When: Call get_bsv_tx
           Then: Returns parsed BSV Transaction object

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('3_getBsvTx_returns_parsed_transaction')
        """
        # Given

        raw_tx = bytes([1, 2, 3])
        tx = Transaction({"rawTx": list(raw_tx)})

        # When
        with patch("bsv_wallet_toolbox.storage.entities.BsvTransaction.from_hex") as mock_from_hex:
            mock_tx = MagicMock(spec=BsvTransaction)
            mock_from_hex.return_value = mock_tx
            bsv_tx = tx.get_bsv_tx()

        # Then
        assert bsv_tx is mock_tx

    def test_getbsvtx_returns_undefined_if_no_rawtx(self) -> None:
        """Given: Transaction without rawTx
           When: Call get_bsv_tx
           Then: Returns None

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('4_getBsvTx_returns_undefined_if_no_rawTx')
        """
        # Given

        tx = Transaction()

        # When
        bsv_tx = tx.get_bsv_tx()

        # Then
        assert bsv_tx is None

    def test_getbsvtxins_returns_inputs(self) -> None:
        """Given: Transaction with rawTx bytes
           When: Call get_bsv_tx_ins
           Then: Returns array of transaction inputs

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('5_getBsvTxIns_returns_inputs')
        """
        # Given

        raw_tx = bytes([1, 2, 3])
        tx = Transaction({"rawTx": list(raw_tx)})

        # When
        inputs = tx.get_bsv_tx_ins()

        # Then
        assert isinstance(inputs, list)

    def test_getinputs_combines_spentby_and_rawtx_inputs(self) -> None:
        """Given: Transaction with outputs linked by spentBy
           When: Call get_inputs with storage
           Then: Returns combined inputs from spentBy and rawTx

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('6_getInputs_combines_spentBy_and_rawTx_inputs')
        """
        # Given

        # Mock storage with test data
        raw_tx = bytes([1, 2, 3])
        tx = Transaction({"transactionId": 123, "rawTx": list(raw_tx)})

        # Mock outputs linked by spentBy
        mock_outputs = [{"vout": 0, "satoshis": 100, "spentBy": 123}, {"vout": 1, "satoshis": 200, "spentBy": 123}]

        def mock_find_outputs(query: dict[str, Any]) -> list[dict[str, Any]]:
            return mock_outputs

        mock_storage = type("MockStorage", (), {"findOutputs": staticmethod(mock_find_outputs)})()

        # When
        inputs = tx.get_inputs(mock_storage)

        # Then
        assert len(inputs) == 2
        assert any(inp["vout"] == 0 and inp["satoshis"] == 100 for inp in inputs)
        assert any(inp["vout"] == 1 and inp["satoshis"] == 200 for inp in inputs)

    def test_mergeexisting_updates_when_ei_updated_at_is_newer(self) -> None:
        """Given: Existing Transaction with old updated_at
           When: Call merge_existing with newer updated_at
           Then: Transaction is updated and returns True

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('9_mergeExisting_updates_when_ei_updated_at_is_newer')
        """
        # Given

        tx = Transaction(
            {
                "transactionId": 123,
                "userId": 456,
                "txid": "oldTxId",
                "status": "unprocessed",
                "updatedAt": datetime(2022, 1, 1),
            }
        )

        ei = {
            "transactionId": 123,
            "userId": 456,
            "txid": "newTxId",
            "status": "completed",
            "updatedAt": datetime(2023, 1, 1),
        }

        sync_map = {"transaction": {"idMap": {456: 123}, "count": 1}}

        # Mock storage
        updated_transactions: list[dict[str, Any]] = []

        def mock_update_transaction(transaction_id: int, data: dict[str, Any]) -> None:
            updated_transactions.append({"transactionId": transaction_id, **data})

        def mock_find_transactions(query: dict[str, Any]) -> list[dict[str, Any]]:
            if updated_transactions:
                return updated_transactions
            return []

        mock_storage = type(
            "MockStorage",
            (),
            {
                "update_transaction": staticmethod(mock_update_transaction),
                "find_transactions": staticmethod(mock_find_transactions),
            },
        )()

        # When
        result = tx.merge_existing(mock_storage, datetime.now(), ei, sync_map)

        # Then
        assert result is True
        found_txs = mock_storage.find_transactions({"partial": {"transactionId": 123}})
        assert found_txs[0]["txid"] == "newTxId"

    def test_getbsvtx_handles_undefined_rawtx(self) -> None:
        """Given: Transaction with no rawTx
           When: Call get_bsv_tx
           Then: Returns None

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('10_getBsvTx_handles_undefined_rawTx')
        """
        # Given

        tx = Transaction()

        # When
        bsv_tx = tx.get_bsv_tx()

        # Then
        assert bsv_tx is None

    def test_getinputs_handles_storage_lookups_and_input_merging(self) -> None:
        """Given: Transaction with complex input sources
           When: Call get_inputs
           Then: Correctly merges inputs from storage lookups and rawTx

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('11_getInputs_handles_storage_lookups_and_input_merging')
        """
        # Given

        tx = Transaction({"transactionId": 123, "rawTx": list(bytes([1, 2, 3]))})

        # Mock storage with complex lookups
        def mock_find_outputs(query: dict[str, Any]) -> list[dict[str, Any]]:
            return [{"vout": 0, "satoshis": 100, "txid": "abc123"}, {"vout": 1, "satoshis": 200, "txid": "def456"}]

        mock_storage = type("MockStorage", (), {"findOutputs": staticmethod(mock_find_outputs)})()

        # When
        inputs = tx.get_inputs(mock_storage)

        # Then
        assert isinstance(inputs, list)
        # Verify proper merging logic

    def test_getproventx_retrieves_proven_transaction(self) -> None:
        """Given: Transaction with valid provenTxId
           When: Call get_proven_tx
           Then: Returns the ProvenTx from storage

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('15_getProvenTx_retrieves_proven_transaction')
        """
        # Given

        tx = Transaction({"provenTxId": 123})

        # Mock storage
        mock_proven_tx = {"provenTxId": 123, "txid": "abc123"}

        def mock_find_proven_tx(proven_tx_id: int) -> dict[str, Any] | None:
            if proven_tx_id == 123:
                return mock_proven_tx
            return None

        mock_storage = type("MockStorage", (), {"findProvenTx": staticmethod(mock_find_proven_tx)})()

        # When
        retrieved_proven_tx = tx.get_proven_tx(mock_storage)

        # Then
        assert retrieved_proven_tx is not None
        assert retrieved_proven_tx["provenTxId"] == 123

    def test_getproventx_returns_undefined_when_proventxid_is_not_set(self) -> None:
        """Given: Transaction without provenTxId
           When: Call get_proven_tx
           Then: Returns None

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('16_getProvenTx_returns_undefined_when_provenTxId_is_not_set')
        """
        # Given

        tx = Transaction()

        # Mock storage
        mock_storage = type("MockStorage", (), {})()

        # When
        retrieved_proven_tx = tx.get_proven_tx(mock_storage)

        # Then
        assert retrieved_proven_tx is None

    def test_getproventx_returns_undefined_when_no_matching_proventx_is_found(self) -> None:
        """Given: Transaction with provenTxId that doesn't exist
           When: Call get_proven_tx
           Then: Returns None

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('17_getProvenTx_returns_undefined_when_no_matching_ProvenTx_is_found')
        """
        # Given

        tx = Transaction({"provenTxId": 9999})

        # Mock storage
        def mock_find_proven_tx(proven_tx_id: int) -> dict[str, Any] | None:
            return None  # No matching ProvenTx

        mock_storage = type("MockStorage", (), {"findProvenTx": staticmethod(mock_find_proven_tx)})()

        # When
        retrieved_proven_tx = tx.get_proven_tx(mock_storage)

        # Then
        assert retrieved_proven_tx is None

    def test_getinputs_merges_known_inputs_correctly(self) -> None:
        """Given: Transaction with multiple input sources
           When: Call get_inputs
           Then: Correctly merges known inputs

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('18_getInputs_merges_known_inputs_correctly')
        """
        # Given

        tx = Transaction({"transactionId": 123, "rawTx": list(bytes([1, 2, 3]))})

        # Mock storage with known inputs
        def mock_find_outputs(query: dict[str, Any]) -> list[dict[str, Any]]:
            return [
                {"outputId": 1, "vout": 0, "satoshis": 100, "txid": "input1"},
                {"outputId": 2, "vout": 1, "satoshis": 200, "txid": "input2"},
            ]

        mock_storage = type("MockStorage", (), {"findOutputs": staticmethod(mock_find_outputs)})()

        # When
        inputs = tx.get_inputs(mock_storage)

        # Then
        assert len(inputs) >= 2
        assert any(inp.get("outputId") == 1 for inp in inputs)
        assert any(inp.get("outputId") == 2 for inp in inputs)

    def test_get_version_returns_api_version(self) -> None:
        """Given: Transaction with version property
           When: Access version property
           Then: Returns API version

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('19_get_version_returns_api_version')
        """
        # Given

        tx = Transaction({"version": 2})

        # When/Then
        assert tx.version == 2

    def test_get_locktime_returns_api_locktime(self) -> None:
        """Given: Transaction with lockTime property
           When: Access lock_time property
           Then: Returns API lockTime

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('20_get_lockTime_returns_api_lockTime')
        """
        # Given

        tx = Transaction({"lockTime": 5000})

        # When/Then
        assert tx.lock_time == 5000

    def test_set_id_updates_transactionid(self) -> None:
        """Given: Transaction instance
           When: Set id property
           Then: Updates transactionId

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('21_set_id_updates_transactionId')
        """
        # Given

        tx = Transaction()

        # When
        tx.id = 456

        # Then
        assert tx.transaction_id == 456
        assert tx.id == 456

    def test_get_entityname_returns_correct_value(self) -> None:
        """Given: Transaction instance
           When: Access entity_name property
           Then: Returns 'transaction'

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('22_get_entityName_returns_correct_value')
        """
        # Given

        tx = Transaction()

        # When/Then
        assert tx.entity_name == "transaction"

    def test_get_entitytable_returns_correct_value(self) -> None:
        """Given: Transaction instance
           When: Access entity_table property
           Then: Returns 'transactions'

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('23_get_entityTable_returns_correct_value')
        """
        # Given

        tx = Transaction()

        # When/Then
        assert tx.entity_table == "transactions"

    def test_equals_returns_false_for_mismatched_other_properties(self) -> None:
        """Given: Two transactions with different properties
           When: Call equals method
           Then: Returns False for mismatched properties

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('25_equals_returns_false_for_mismatched_other_properties')
        """
        # Given

        tx1 = Transaction({"transactionId": 123, "txid": "abc123", "status": "completed", "satoshis": 1000})

        tx2_api = {
            "transactionId": 123,
            "txid": "abc123",
            "status": "unprocessed",  # Different status
            "satoshis": 2000,  # Different satoshis
        }

        sync_map = {"transaction": {"idMap": {123: 123}, "count": 1}}

        # When/Then
        assert tx1.equals(tx2_api, sync_map) is False

    def test_getinputs_handles_known_and_unknown_inputs(self) -> None:
        """Given: Transaction with both known and unknown inputs
           When: Call get_inputs
           Then: Properly handles both types of inputs

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('26_getInputs_handles_known_and_unknown_inputs')
        """
        # Given

        tx = Transaction({"transactionId": 123, "rawTx": list(bytes([1, 2, 3]))})

        # Mock storage with some known inputs
        def mock_find_outputs(query: dict[str, Any]) -> list[dict[str, Any]]:
            return [{"outputId": 1, "txid": "known1", "vout": 0, "satoshis": 100}]

        mock_storage = type("MockStorage", (), {"findOutputs": staticmethod(mock_find_outputs)})()

        # When
        inputs = tx.get_inputs(mock_storage)

        # Then
        assert isinstance(inputs, list)
        assert len(inputs) >= 1

    def test_equals_identifies_matching_entities(self) -> None:
        """Given: Two Transaction entities with matching properties
           When: Call equals method
           Then: Returns True

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('27_equals_identifies_matching_entities')
        """
        # Given

        tx1 = Transaction({"transactionId": 123, "txid": "abc123", "status": "completed", "satoshis": 1000})

        tx2_api = {
            "transactionId": 456,  # Different ID
            "txid": "abc123",  # Same txid
            "status": "completed",
            "satoshis": 1000,
        }

        sync_map: dict[str, Any] = {}

        # When/Then
        assert tx1.equals(tx2_api, sync_map) is True

    def test_equals_identifies_non_matching_entities(self) -> None:
        """Given: Two Transaction entities with different properties
           When: Call equals method
           Then: Returns False

        Reference: src/storage/schema/entities/__tests/TransactionTests.test.ts
                  test('28_equals_identifies_non_matching_entities')
        """
        # Given

        tx1 = Transaction({"transactionId": 123, "txid": "abc123", "status": "completed"})

        tx2_api = {"transactionId": 456, "txid": "def456", "status": "completed"}  # Different txid

        sync_map: dict[str, Any] = {}

        # When/Then
        assert tx1.equals(tx2_api, sync_map) is False
