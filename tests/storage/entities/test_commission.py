"""Unit tests for Commission entity.

Reference: wallet-toolbox/src/storage/schema/entities/__tests/CommissionTests.test.ts
"""

from datetime import datetime

from bsv_wallet_toolbox.storage.entities import Commission


class TestCommissionEntity:
    """Test suite for Commission entity."""

    def test_equals_identifies_matching_commission_entities(self) -> None:
        """Given: Two Commission entities with identical data
           When: Call equals method with and without syncMap
           Then: Returns True in both cases

        Reference: src/storage/schema/entities/__tests/CommissionTests.test.ts
                  test('0_equals identifies matching Commission entities')
        """
        # Given

        now = datetime.now()
        initial_data = {
            "commissionId": 801,
            "createdAt": now,
            "updatedAt": now,
            "transactionId": 192,
            "userId": 1,
            "isRedeemed": False,
            "keyOffset": "offset123",
            "lockingScript": [1, 2, 3],
            "satoshis": 500,
        }

        entity1 = Commission(initial_data)
        entity2 = Commission(initial_data)

        sync_map = {"transaction": {"idMap": {192: 192}}}

        # When/Then
        assert entity1.equals(entity2.to_api()) is True
        assert entity1.equals(entity2.to_api(), sync_map) is True

    def test_equals_identifies_non_matching_commission_entities(self) -> None:
        """Given: Two Commission entities with different data
           When: Call equals method for each mismatched property
           Then: Returns False for all mismatches

        Reference: src/storage/schema/entities/__tests/CommissionTests.test.ts
                  test('1_equals identifies non-matching Commission entities')
        """
        # Given

        now = datetime.now()
        initial_data = {
            "commissionId": 802,
            "createdAt": now,
            "updatedAt": now,
            "transactionId": 200,
            "userId": 1,
            "isRedeemed": False,
            "keyOffset": "offset123",
            "lockingScript": [1, 2, 3],
            "satoshis": 500,
        }

        entity1 = Commission(initial_data)

        sync_map = {"transaction": {"idMap": {200: 200, 201: 201}}}

        # Test each mismatched property
        mismatched_entities = [
            {"isRedeemed": True},
            {"transactionId": 201},
            {"keyOffset": "offset456"},
            {"lockingScript": [4, 5, 6]},
            {"satoshis": 1000},
        ]

        # When/Then
        for mismatch in mismatched_entities:
            mismatched_entity = Commission({**initial_data, **mismatch})
            assert entity1.equals(mismatched_entity.to_api()) is False
            assert entity1.equals(mismatched_entity.to_api(), sync_map) is False

    def test_mergeexisting_updates_entity_and_database_when_ei_updated_at_greater_than_this_updated_at(
        self,
    ) -> None:
        """Given: Commission entity with older updated_at
           When: Call merge_existing with newer updated_at
           Then: Entity and database are updated, returns True

        Reference: src/storage/schema/entities/__tests/CommissionTests.test.ts
                  test('2_mergeExisting updates entity and database when ei.updated_at > this.updated_at')
        """
        # Given

        now = datetime.now()
        initial_data = {
            "commissionId": 803,
            "createdAt": now,
            "updatedAt": now,
            "transactionId": 203,
            "userId": 1,
            "isRedeemed": False,
            "keyOffset": "offset123",
            "lockingScript": [1, 2, 3],
            "satoshis": 500,
        }

        entity = Commission(initial_data)

        # Updated data with later timestamp
        updated_data = {**initial_data, "updatedAt": datetime.fromtimestamp(now.timestamp() + 1), "isRedeemed": True}

        sync_map = {"transaction": {"idMap": {203: 203}}}

        mock_storage = type("MockStorage", (), {})()

        # When
        was_merged = entity.merge_existing(mock_storage, None, updated_data, sync_map, None)

        # Then
        assert was_merged is True
        assert entity.is_redeemed is True

    def test_mergeexisting_does_not_update_when_ei_updated_at_less_than_or_equal_this_updated_at(self) -> None:
        """Given: Commission entity with same or newer updated_at
           When: Call merge_existing with same or older updated_at
           Then: Entity is not updated, returns False

        Reference: src/storage/schema/entities/__tests/CommissionTests.test.ts
                  test('3_mergeExisting does not update when ei.updated_at <= this.updated_at')
        """
        # Given

        now = datetime.now()
        initial_data = {
            "commissionId": 804,
            "createdAt": now,
            "updatedAt": now,
            "transactionId": 193,
            "userId": 1,
            "isRedeemed": False,
            "keyOffset": "offset123",
            "lockingScript": [1, 2, 3],
            "satoshis": 500,
        }

        entity = Commission(initial_data)

        # Same timestamp
        older_or_equal_data = {**initial_data, "updatedAt": now, "isRedeemed": True}

        sync_map = {"transaction": {"idMap": {193: 193}}}

        mock_storage = type("MockStorage", (), {})()

        # When
        was_merged = entity.merge_existing(mock_storage, None, older_or_equal_data, sync_map, None)

        # Then
        assert was_merged is False
        assert entity.is_redeemed is False

    def test_commission_entity_getters_and_setters(self) -> None:
        """Given: Commission entity with initial data
           When: Get and set all properties
           Then: Getters and setters work correctly

        Reference: src/storage/schema/entities/__tests/CommissionTests.test.ts
                  test('4_Commission entity getters and setters')
        """
        # Given

        now = datetime.now()
        initial_data = {
            "commissionId": 801,
            "createdAt": now,
            "updatedAt": now,
            "transactionId": 101,
            "userId": 1,
            "isRedeemed": False,
            "keyOffset": "offset123",
            "lockingScript": [1, 2, 3],
            "satoshis": 500,
        }

        entity = Commission(initial_data)

        # Validate getters
        assert entity.commission_id == 801
        assert entity.created_at == now
        assert entity.updated_at == now
        assert entity.transaction_id == 101
        assert entity.user_id == 1
        assert entity.is_redeemed is False
        assert entity.key_offset == "offset123"
        assert entity.locking_script == [1, 2, 3]
        assert entity.satoshis == 500
        assert entity.id == 801
        assert entity.entity_name == "commission"
        assert entity.entity_table == "commissions"

        # Validate setters
        entity.commission_id = 900
        entity.created_at = datetime(2024, 1, 1)
        entity.updated_at = datetime(2024, 1, 2)
        entity.transaction_id = 202
        entity.user_id = 2
        entity.is_redeemed = True
        entity.key_offset = "offset456"
        entity.locking_script = [4, 5, 6]
        entity.satoshis = 1000
        entity.id = 900

        assert entity.commission_id == 900
        assert entity.created_at == datetime(2024, 1, 1)
        assert entity.updated_at == datetime(2024, 1, 2)
        assert entity.transaction_id == 202
        assert entity.user_id == 2
        assert entity.is_redeemed is True
        assert entity.key_offset == "offset456"
        assert entity.locking_script == [4, 5, 6]
        assert entity.satoshis == 1000
        assert entity.id == 900
