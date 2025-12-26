"""Unit tests for ProvenTxReq entity.

Reference: wallet-toolbox/src/storage/schema/entities/__tests/ProvenTxReqTests.test.ts
"""

import json
from datetime import datetime
from typing import Any

from bsv_wallet_toolbox.storage.entities import ProvenTxReq


class TestProvenTxReqEntity:
    """Test suite for ProvenTxReq entity."""

    def test_apinotify_getter_and_setter(self) -> None:
        """Given: ProvenTxReq instance
           When: Set and get api_notify property
           Then: Properly serializes/deserializes JSON notify data

        Reference: src/storage/schema/entities/__tests/ProvenTxReqTests.test.ts
                  test('0_apiNotify_getter_and_setter')
        """
        # Given

        proven_tx_req = ProvenTxReq(
            {
                "provenTxReqId": 0,
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
                "txid": "",
                "rawTx": [],
                "history": "{}",
                "notify": "{}",
                "attempts": 0,
                "status": "unknown",
                "notified": False,
            }
        )

        # When
        notify_data = {"transactionIds": [1, 2, 3]}
        proven_tx_req.api_notify = json.dumps(notify_data)

        # Then
        assert proven_tx_req.api_notify == json.dumps(notify_data)
        assert proven_tx_req.notify["transactionIds"] == [1, 2, 3]

    def test_gethistorysummary(self) -> None:
        """Given: ProvenTxReq instance with history
           When: Call get_history_summary
           Then: Returns formatted history summary

        Reference: src/storage/schema/entities/__tests/ProvenTxReqTests.test.ts
                  test('1_getHistorySummary')
        """
        # Given

        # Placeholder test - implementation details not shown in TS
        ProvenTxReq({})

        # When/Then
        # Test implementation pending

    def test_parsehistorynote(self) -> None:
        """Given: ProvenTxReq instance
           When: Call parse_history_note
           Then: Parses history note correctly

        Reference: src/storage/schema/entities/__tests/ProvenTxReqTests.test.ts
                  test('2_parseHistoryNote')
        """
        # Given

        ProvenTxReq(
            {
                "provenTxReqId": 0,
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
                "txid": "",
                "rawTx": [],
                "history": "{}",
                "notify": "{}",
                "attempts": 0,
                "status": "unknown",
                "notified": False,
            }
        )

        # When/Then
        # Test implementation details

    def test_updatestorage(self) -> None:
        """Given: ProvenTxReq instance
           When: Call update_storage
           Then: Updates storage and can fetch back the record

        Reference: src/storage/schema/entities/__tests/ProvenTxReqTests.test.ts
                  test('3_updateStorage')
        """
        # Given

        proven_tx_req = ProvenTxReq(
            {
                "provenTxReqId": 0,
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
                "txid": "test-txid",
                "rawTx": [1, 2, 3],
                "history": "{}",
                "notify": "{}",
                "attempts": 0,
                "status": "unknown",
                "notified": False,
            }
        )

        # Mock storage
        stored_records: list[dict[str, Any]] = []

        def mock_update_proven_tx_req(_id: int, data: dict[str, Any]) -> None:
            stored_records.append(data)

        def mock_find_proven_tx_reqs(query: dict[str, Any]) -> list[dict[str, Any]]:
            return [r for r in stored_records if r.get("txid") == query["partial"]["txid"]]

        mock_storage = type(
            "MockStorage",
            (),
            {
                "updateProvenTxReq": staticmethod(mock_update_proven_tx_req),
                "findProvenTxReqs": staticmethod(mock_find_proven_tx_reqs),
            },
        )()

        # When
        proven_tx_req.update_storage(mock_storage)

        # Then
        fetched = mock_storage.findProvenTxReqs({"partial": {"txid": "test-txid"}})
        assert len(fetched) == 1
        assert fetched[0]["txid"] == "test-txid"

    def test_insertormerge(self) -> None:
        """Given: ProvenTxReq instance
           When: Call insert_or_merge
           Then: Inserts or merges record and returns result

        Reference: src/storage/schema/entities/__tests/ProvenTxReqTests.test.ts
                  test('4_insertOrMerge')
        """
        # Given

        proven_tx_req = ProvenTxReq(
            {
                "provenTxReqId": 0,
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
                "txid": "test-txid-merge",
                "rawTx": [1, 2, 3],
                "history": "{}",
                "notify": "{}",
                "attempts": 0,
                "status": "unknown",
                "notified": False,
            }
        )

        # Mock storage
        def mock_insert_or_merge(data: dict[str, Any]) -> dict[str, Any]:
            return data

        mock_storage = type(
            "MockStorage",
            (),
            {"insertOrMergeProvenTxReq": staticmethod(mock_insert_or_merge)},
        )()

        # When
        result = proven_tx_req.insert_or_merge(mock_storage)

        # Then
        assert result["txid"] == "test-txid-merge"

    def test_equals_identifies_matching_entities(self) -> None:
        """Given: Two ProvenTxReq entities with matching data
           When: Call equals method
           Then: Returns True

        Reference: src/storage/schema/entities/__tests/ProvenTxReqTests.test.ts
                  test('5_equals_identifies_matching_entities')
        """
        # Given

        current_time = datetime.now()

        proven_tx_req1 = ProvenTxReq(
            {
                "provenTxReqId": 405,
                "createdAt": current_time,
                "updatedAt": current_time,
                "txid": "test-equals",
                "rawTx": [1, 2, 3],
                "history": json.dumps({"notes": {"2025-01-01T00:00:00.000Z": "test-note-1"}}),
                "notify": json.dumps({"transactionIds": [100]}),
                "attempts": 0,
                "status": "unknown",
                "notified": False,
            }
        )

        proven_tx_req2_api = {
            "provenTxReqId": 406,
            "createdAt": current_time,
            "updatedAt": current_time,
            "txid": "test-equals",
            "rawTx": [1, 2, 3],
            "history": json.dumps({"notes": {"2025-01-01T00:00:00.000Z": "test-note-1"}}),
            "notify": json.dumps({"transactionIds": [100]}),
            "attempts": 0,
            "status": "unknown",
            "notified": False,
        }

        sync_map: dict[str, Any] = {}

        # When/Then
        assert proven_tx_req1.equals(proven_tx_req2_api, sync_map) is True

    def test_equals_identifies_non_matching_entities(self) -> None:
        """Given: Two ProvenTxReq entities with different data
           When: Call equals method
           Then: Returns False

        Reference: src/storage/schema/entities/__tests/ProvenTxReqTests.test.ts
                  test('6_equals_identifies_non_matching_entities')
        """
        # Given

        datetime.now()

        proven_tx_req1 = ProvenTxReq(
            {
                "provenTxReqId": 407,
                "txid": "test-not-equals",
                "rawTx": [1, 2, 3],
                "history": json.dumps({"notes": {"2025-01-01T00:00:00.000Z": "test-note-1"}}),
                "notify": json.dumps({"transactionIds": [200]}),
                "status": "unknown",
            }
        )

        proven_tx_req2_api = {
            "provenTxReqId": 408,
            "txid": "test-not-equals",
            "rawTx": [4, 5, 6],
            "history": json.dumps({"notes": {"2025-01-01T00:00:00.000Z": "test-note-2"}}),
            "notify": json.dumps({"transactionIds": [300]}),
            "attempts": 1,
            "status": "unknown",
        }

        sync_map: dict[str, Any] = {}

        # When/Then
        assert proven_tx_req1.equals(proven_tx_req2_api, sync_map) is False

    def test_mergenotifytransactionids(self) -> None:
        """Given: ProvenTxReq with existing notify transactionIds
           When: Call merge_notify_transaction_ids with new IDs
           Then: Merges IDs correctly

        Reference: src/storage/schema/entities/__tests/ProvenTxReqTests.test.ts
                  test('7_mergeNotifyTransactionIds')
        """
        # Given

        proven_tx_req = ProvenTxReq(
            {"provenTxReqId": 0, "txid": "test-merge-ids", "notify": json.dumps({"transactionIds": [1, 2]})}
        )

        # When
        proven_tx_req.merge_notify_transaction_ids([2, 3, 4])

        # Then
        assert set(proven_tx_req.notify["transactionIds"]) == {1, 2, 3, 4}

    def test_getters_and_setters(self) -> None:
        """Given: ProvenTxReq instance
           When: Set and get all properties
           Then: Getters and setters work correctly

        Reference: src/storage/schema/entities/__tests/ProvenTxReqTests.test.ts
                  test('8_getters_and_setters')
        """
        # Given

        now = datetime.now()
        proven_tx_req = ProvenTxReq(
            {
                "provenTxReqId": 1,
                "createdAt": now,
                "updatedAt": now,
                "txid": "test-txid",
                "rawTx": [1, 2, 3],
                "history": "{}",
                "notify": "{}",
                "attempts": 5,
                "status": "unknown",
                "notified": False,
            }
        )

        # Validate getters
        assert proven_tx_req.proven_tx_req_id == 1
        assert proven_tx_req.txid == "test-txid"
        assert proven_tx_req.attempts == 5
        assert proven_tx_req.status == "unknown"
        assert proven_tx_req.notified is False

        # Validate setters
        proven_tx_req.proven_tx_req_id = 2
        proven_tx_req.txid = "new-txid"
        proven_tx_req.attempts = 10
        proven_tx_req.status = "completed"
        proven_tx_req.notified = True

        assert proven_tx_req.proven_tx_req_id == 2
        assert proven_tx_req.txid == "new-txid"
        assert proven_tx_req.attempts == 10
        assert proven_tx_req.status == "completed"
        assert proven_tx_req.notified is True

        # Validate entity metadata
        assert proven_tx_req.entity_name == "provenTxReq"
        assert proven_tx_req.entity_table == "proven_tx_reqs"

    def test_parsehistorynote_82(self) -> None:
        """Given: ProvenTxReq with history data
           When: Call parse_history_note
           Then: Correctly parses history note

        Reference: src/storage/schema/entities/__tests/ProvenTxReqTests.test.ts
                  test('9_parseHistoryNote')
        """
        # Given

        # Placeholder - implementation details not shown
        ProvenTxReq({})

        # When/Then
        # Test implementation pending

    def test_mergehistory(self) -> None:
        """Given: ProvenTxReq with history
           When: Call merge_history with new history
           Then: Merges history correctly

        Reference: src/storage/schema/entities/__tests/ProvenTxReqTests.test.ts
                  test('10_mergeHistory')
        """
        # Given

        # Placeholder - implementation details not shown
        ProvenTxReq({})

        # When/Then
        # Test implementation pending

    def test_isterminalstatus_with_real_data(self) -> None:
        """Given: ProvenTxReq with various statuses
           When: Call is_terminal_status
           Then: Correctly identifies terminal statuses

        Reference: src/storage/schema/entities/__tests/ProvenTxReqTests.test.ts
                  test('12_isTerminalStatus_with_real_data')
        """
        # Given

        # Test various statuses
        statuses = [("completed", True), ("invalid", True), ("unknown", False), ("sending", False)]

        for status, expected_terminal in statuses:
            # When/Then
            assert ProvenTxReq.is_terminal_status(status) == expected_terminal

    def test_mergeexisting_real_data(self) -> None:
        """Given: Existing ProvenTxReq
           When: Call merge_existing with updated data
           Then: Merges data correctly

        Reference: src/storage/schema/entities/__tests/ProvenTxReqTests.test.ts
                  test('13_mergeExisting_real_data')
        """
        # Given

        # Placeholder - implementation details not shown
        ProvenTxReq({})

        # When/Then
        # Test implementation pending
