"""Unit tests for Output entity.

Reference: wallet-toolbox/src/storage/schema/entities/__tests/OutputTests.test.ts
"""

from datetime import datetime
from typing import Any

from bsv_wallet_toolbox.storage.entities import Output


class TestOutputEntity:
    """Test suite for Output entity."""

    def test_equals_identifies_matching_entities_with_and_without_syncmap(self) -> None:
        """Given: Two Output entities with same data
           When: Call equals with and without SyncMap
           Then: Returns True in both cases

        Reference: src/storage/schema/entities/__tests/OutputTests.test.ts
                  test('0_equals identifies matching entities with and without SyncMap')
        """
        # Given

        initial_data = {
            "outputId": 601,
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "userId": 1,
            "transactionId": 100,
            "basketId": 1,
            "spendable": True,
            "change": False,
            "satoshis": 1000,
            "outputDescription": "Test Output",
            "vout": 40,
            "type": "p2pkh",
            "providedBy": "you",
            "purpose": "testing",
            "txid": "txid123",
            "spendingDescription": "Test Spending",
            "derivationPrefix": "m/44",
            "derivationSuffix": "/0/0",
            "senderIdentityKey": "key123",
            "customInstructions": "none",
            "lockingScript": [1, 2, 3],
            "scriptLength": 10,
            "scriptOffset": 0,
        }

        entity1 = Output(initial_data)
        entity2 = Output(initial_data)

        sync_map = {"transaction": {"idMap": {100: 100}}, "outputBasket": {"idMap": {1: 1}}}

        # When/Then
        assert entity1.equals(entity2.to_api()) is True
        assert entity1.equals(entity2.to_api(), sync_map) is True

    def test_equals_identifies_non_matching_entities(self) -> None:
        """Given: Two Output entities with different satoshis
           When: Call equals method
           Then: Returns False

        Reference: src/storage/schema/entities/__tests/OutputTests.test.ts
                  test('1_equals identifies non-matching entities')
        """
        # Given

        initial_data = {
            "outputId": 602,
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "userId": 1,
            "transactionId": 101,
            "basketId": 2,
            "spendable": True,
            "change": False,
            "satoshis": 1000,
            "outputDescription": "Test Output",
            "vout": 41,
            "type": "p2pkh",
            "providedBy": "you",
            "purpose": "testing",
            "txid": "txid124",
            "spendingDescription": "Test Spending",
            "derivationPrefix": "m/44",
            "derivationSuffix": "/0/0",
            "senderIdentityKey": "key124",
            "customInstructions": "none",
            "lockingScript": [1, 2, 3],
            "scriptLength": 10,
            "scriptOffset": 0,
        }

        entity1 = Output(initial_data)
        entity2_data = {**initial_data, "satoshis": 2000}
        entity2 = Output(entity2_data)

        # When/Then
        assert entity1.equals(entity2.to_api()) is False

    def test_equals_handles_optional_fields_and_arrays(self) -> None:
        """Given: Two Output entities with different lockingScript arrays
           When: Call equals method
           Then: Returns False for different arrays

        Reference: src/storage/schema/entities/__tests/OutputTests.test.ts
                  test('2_equals handles optional fields and arrays')
        """
        # Given

        initial_data = {
            "outputId": 603,
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "userId": 1,
            "transactionId": 102,
            "basketId": 3,
            "spendable": True,
            "change": False,
            "satoshis": 1000,
            "outputDescription": "Test Output",
            "vout": 42,
            "type": "p2pkh",
            "providedBy": "you",
            "purpose": "testing",
            "txid": "txid125",
            "spendingDescription": "Test Spending",
            "derivationPrefix": "m/44",
            "derivationSuffix": "/0/0",
            "senderIdentityKey": "key125",
            "customInstructions": "none",
            "lockingScript": [1, 2, 3],
            "scriptLength": 10,
            "scriptOffset": 0,
        }

        entity1 = Output(initial_data)
        entity2_data = {**initial_data, "lockingScript": [1, 2, 4]}
        entity2 = Output(entity2_data)

        # When/Then
        assert entity1.equals(entity2.to_api()) is False

    def test_mergeexisting_updates_entity_and_database_when_ei_updated_at_greater_than_this_updated_at(
        self,
    ) -> None:
        """Given: Existing Output with old updated_at
           When: Call merge_existing with newer updated_at
           Then: Output is updated and returns True

        Reference: src/storage/schema/entities/__tests/OutputTests.test.ts
                  test('3_mergeExisting updates entity and database when ei.updated_at > this.updated_at')
        """
        # Given

        initial_data = {
            "outputId": 701,
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "userId": 1,
            "transactionId": 103,
            "basketId": 1,
            "spendable": True,
            "change": False,
            "satoshis": 1000,
            "outputDescription": "Initial Output",
            "vout": 50,
            "type": "p2pkh",
            "providedBy": "you",
            "purpose": "initial",
            "txid": "txid201",
            "spendingDescription": "Initial Spending",
            "derivationPrefix": "m/44",
            "derivationSuffix": "/0/0",
            "senderIdentityKey": "key201",
            "customInstructions": "none",
            "lockingScript": [1, 2, 3],
            "scriptLength": 10,
            "scriptOffset": 0,
            "spentBy": None,
        }

        entity = Output(initial_data)

        updated_data = {
            **initial_data,
            "updatedAt": datetime(2023, 1, 3),  # Newer
            "spendable": False,
            "change": True,
            "type": "p2sh",
            "providedBy": "storage",
            "purpose": "updated",
            "outputDescription": "Updated Output",
            "spendingDescription": "Updated Spending",
            "senderIdentityKey": "key202",
            "customInstructions": "new instructions",
            "scriptLength": 15,
            "scriptOffset": 5,
            "lockingScript": [4, 5, 6],
            "spentBy": 105,
        }

        sync_map = {"transaction": {"idMap": {103: 103, 105: 105}}, "outputBasket": {"idMap": {1: 1}}}

        # Mock storage
        updated_records: list[dict[str, Any]] = []

        def mock_update_output(output_id: int, data: dict[str, Any]) -> None:
            updated_records.append({"outputId": output_id, **data})

        def mock_find_outputs(query: dict[str, Any]) -> list[dict[str, Any]]:
            if updated_records:
                return updated_records
            return []

        mock_storage = type("MockStorage", (), {"updateOutput": mock_update_output, "findOutputs": mock_find_outputs})()

        # When
        was_merged = entity.merge_existing(mock_storage, None, updated_data, sync_map, None)

        # Then
        assert was_merged is True
        assert entity.spent_by == 105
        assert entity.spendable is False
        assert entity.change is True
        assert entity.type == "p2sh"

    def test_mergeexisting_does_not_update_when_ei_updated_at_less_than_or_equal_this_updated_at(self) -> None:
        """Given: Existing Output with new updated_at
           When: Call merge_existing with older updated_at
           Then: Output is not updated and returns False

        Reference: src/storage/schema/entities/__tests/OutputTests.test.ts
                  test('4_mergeExisting does not update when ei.updated_at <= this.updated_at')
        """
        # Given

        initial_data = {
            "outputId": 702,
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "userId": 1,
            "transactionId": 104,
            "basketId": 1,
            "spendable": True,
            "change": False,
            "satoshis": 1000,
            "outputDescription": "Initial Output",
            "vout": 50,
            "type": "p2pkh",
            "providedBy": "you",
            "purpose": "initial",
            "txid": "txid202",
            "spendingDescription": "Initial Spending",
            "derivationPrefix": "m/44",
            "derivationSuffix": "/0/0",
            "senderIdentityKey": "key202",
            "customInstructions": "none",
            "lockingScript": [1, 2, 3],
            "scriptLength": 10,
            "scriptOffset": 0,
            "spentBy": None,
        }

        entity = Output(initial_data)

        earlier_data = {**initial_data, "updatedAt": datetime(2023, 1, 1), "spendable": False}  # Earlier

        sync_map = {"transaction": {"idMap": {104: 104}}, "outputBasket": {"idMap": {1: 1}}}

        # Mock storage that should not be called
        def mock_update_output(output_id: int, data: dict[str, Any]) -> None:
            raise AssertionError("This should not be called")

        mock_storage = type("MockStorage", (), {"updateOutput": mock_update_output})()

        # When
        was_merged = entity.merge_existing(mock_storage, None, earlier_data, sync_map, None)

        # Then
        assert was_merged is False
        assert entity.spendable is True

    def test_output_entity_getters_and_setters(self) -> None:
        """Given: Output instance
           When: Set and get all properties
           Then: Getters and setters work correctly

        Reference: src/storage/schema/entities/__tests/OutputTests.test.ts
                  test('Output entity getters and setters')
        """
        # Given

        now = datetime.now()
        initial_data = {
            "outputId": 701,
            "createdAt": now,
            "updatedAt": now,
            "userId": 1,
            "transactionId": 103,
            "basketId": 1,
            "spendable": True,
            "change": False,
            "satoshis": 1000,
            "outputDescription": "Initial Output",
            "vout": 50,
            "type": "p2pkh",
            "providedBy": "you",
            "purpose": "initial",
            "txid": "txid201",
            "spendingDescription": "Initial Spending",
            "derivationPrefix": "m/44",
            "derivationSuffix": "/0/0",
            "senderIdentityKey": "key201",
            "customInstructions": "none",
            "lockingScript": [1, 2, 3],
            "scriptLength": 10,
            "scriptOffset": 0,
            "spentBy": 200,
        }

        entity = Output(initial_data)

        # Validate getters
        assert entity.output_id == 701
        assert entity.user_id == 1
        assert entity.transaction_id == 103
        assert entity.basket_id == 1
        assert entity.spent_by == 200
        assert entity.vout == 50
        assert entity.satoshis == 1000
        assert entity.spendable is True
        assert entity.change is False

        # Validate setters
        entity.output_id = 800
        entity.created_at = datetime(2024, 1, 1)
        entity.updated_at = datetime(2024, 1, 2)
        entity.user_id = 2
        entity.transaction_id = 104
        entity.basket_id = 2
        entity.spent_by = 300
        entity.vout = 60
        entity.satoshis = 2000
        entity.output_description = "Updated Output"
        entity.spendable = False
        entity.change = True
        entity.txid = "txid202"
        entity.type = "p2sh"
        entity.provided_by = "storage"
        entity.purpose = "updated"
        entity.spending_description = "Updated Spending"
        entity.derivation_prefix = "m/45"
        entity.derivation_suffix = "/1/0"
        entity.sender_identity_key = "key202"
        entity.custom_instructions = "new instructions"
        entity.locking_script = [4, 5, 6]
        entity.script_length = 15
        entity.script_offset = 5

        assert entity.output_id == 800
        assert entity.satoshis == 2000
        assert entity.spendable is False

        # Validate id setter and getter
        entity.id = 900
        assert entity.id == 900
        assert entity.output_id == 900

        # Validate entity_name and entity_table
        assert entity.entity_name == "output"
        assert entity.entity_table == "outputs"
