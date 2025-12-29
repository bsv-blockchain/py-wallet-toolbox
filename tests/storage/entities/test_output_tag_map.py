"""Unit tests for OutputTagMap entity.

Reference: wallet-toolbox/src/storage/schema/entities/__tests/OutputTagMapTests.test.ts
"""

from datetime import datetime

import pytest

from bsv_wallet_toolbox.storage.entities import OutputTagMap


class TestOutputTagMapEntity:
    """Test suite for OutputTagMap entity."""

    def test_outputtagmap_getters_and_setters(self) -> None:
        """Given: OutputTagMap entity
           When: Set and get all properties
           Then: Getters and setters work correctly, id throws error

        Reference: src/storage/schema/entities/__tests/OutputTagMapTests.test.ts
                  test('0_OutputTagMap getters and setters')
        """
        # Given

        now = datetime.now()
        initial_data = {"createdAt": now, "updatedAt": now, "outputId": 1, "outputTagId": 2, "isDeleted": False}

        output_tag_map = OutputTagMap(initial_data)

        # Test getters
        assert output_tag_map.output_tag_id == 2
        assert output_tag_map.output_id == 1
        assert output_tag_map.created_at == now
        assert output_tag_map.updated_at == now
        assert output_tag_map.is_deleted is False
        assert output_tag_map.entity_name == "outputTagMap"
        assert output_tag_map.entity_table == "output_tags_map"

        # Test setters
        new_date = datetime.now()
        output_tag_map.output_tag_id = 3
        output_tag_map.output_id = 4
        output_tag_map.created_at = new_date
        output_tag_map.updated_at = new_date
        output_tag_map.is_deleted = True

        assert output_tag_map.output_tag_id == 3
        assert output_tag_map.output_id == 4
        assert output_tag_map.created_at == new_date
        assert output_tag_map.updated_at == new_date
        assert output_tag_map.is_deleted is True

        # Test id throws an error
        with pytest.raises(Exception):
            _ = output_tag_map.id

    def test_equals_returns_true_for_matching_entities(self) -> None:
        """Given: Two OutputTagMap entities with matching data
           When: Call equals method with syncMap
           Then: Returns True

        Reference: src/storage/schema/entities/__tests/OutputTagMapTests.test.ts
                  test('1_equals returns true for matching entities')
        """
        # Given

        output_tag_map_data = {
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "outputId": 1,
            "outputTagId": 8,
            "isDeleted": False,
        }

        entity1 = OutputTagMap(output_tag_map_data)
        entity2 = OutputTagMap(output_tag_map_data)

        sync_map = {"output": {"idMap": {1: 1}}, "outputTag": {"idMap": {8: 8}}}

        # When/Then
        assert entity1.equals(entity2.to_api(), sync_map) is True

    def test_equals_returns_false_for_non_matching_entities(self) -> None:
        """Given: Two OutputTagMap entities with different data
           When: Call equals method with and without syncMap
           Then: Returns False in both cases

        Reference: src/storage/schema/entities/__tests/OutputTagMapTests.test.ts
                  test('2_equals returns false for non-matching entities')
        """
        # Given

        output_tag_map_data1 = {
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "outputId": 1,
            "outputTagId": 9,
            "isDeleted": False,
        }

        output_tag_map_data2 = {
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "outputId": 1,
            "outputTagId": 21,
            "isDeleted": True,
        }

        entity1 = OutputTagMap(output_tag_map_data1)
        entity2 = OutputTagMap(output_tag_map_data2)

        sync_map = {"output": {"idMap": {101: 101}}}

        # When/Then
        assert entity1.equals(entity2.to_api(), sync_map) is False
        assert entity1.equals(entity2.to_api()) is False

    def test_mergeexisting_merges_and_updates_entity_when_ei_updated_at_greater_than_this_updated_at_at(
        self,
    ) -> None:
        """Given: OutputTagMap entity with older updated_at
           When: Call merge_existing with newer updated_at
           Then: Entity and database are updated

        Reference: src/storage/schema/entities/__tests/OutputTagMapTests.test.ts
                  test('3_mergeExisting merges and updates entity when ei.updated_at > this.updated_at')
        """
        # Given

        initial_data = {
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "outputId": 2,
            "outputTagId": 8,
            "isDeleted": False,
        }

        entity = OutputTagMap(initial_data)

        # Updated data with later timestamp
        updated_data = {**initial_data, "updatedAt": datetime(2023, 1, 3), "isDeleted": True}

        sync_map = {"output": {"idMap": {1: 1}}}
        mock_storage = type("MockStorage", (), {})()

        # When
        was_merged = entity.merge_existing(mock_storage, None, updated_data, sync_map)

        # Then
        assert was_merged is True
        assert entity.is_deleted == 1

    def test_mergeexisting_does_not_merge_when_ei_updated_at_less_than_or_equal_this_updated_at_at(self) -> None:
        """Given: OutputTagMap entity with same or newer updated_at
           When: Call merge_existing with same or older updated_at
           Then: Entity is not updated

        Reference: src/storage/schema/entities/__tests/OutputTagMapTests.test.ts
                  test('4_mergeExisting does not merge when ei.updated_at <= this.updated_at')
        """
        # Given

        initial_data = {
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "outputId": 2,
            "outputTagId": 11,
            "isDeleted": False,
        }

        entity = OutputTagMap(initial_data)

        # Earlier data
        earlier_data = {**initial_data, "updatedAt": datetime(2023, 1, 1), "isDeleted": True}

        sync_map = {"output": {"idMap": {101: 101}}}
        mock_storage = type("MockStorage", (), {})()

        # When
        was_merged = entity.merge_existing(mock_storage, None, earlier_data, sync_map)

        # Then
        assert was_merged is False
        assert entity.is_deleted == 0
