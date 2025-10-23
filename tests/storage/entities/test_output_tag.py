"""Unit tests for OutputTag entity.

Reference: src/storage/schema/entities/__tests/OutputTagTests.test.ts
"""

import pytest
from datetime import datetime
from typing import Any


class TestOutputTagEntity:
    """Test suite for OutputTag entity."""

    @pytest.mark.skip(reason="OutputTag entity not implemented yet")
    @pytest.mark.asyncio
    async def test_mergeexisting_merges_and_updates_entity_when_ei_updated_at_greater_than_this_updated_at(
        self
    ) -> None:
        """Given: OutputTag entity with older updated_at
           When: Call merge_existing with newer updated_at
           Then: Entity and database are updated
           
        Reference: src/storage/schema/entities/__tests/OutputTagTests.test.ts
                  test('0_mergeExisting merges and updates entity when ei.updated_at > this.updated_at')
        """
        # Given
        from bsv_wallet_toolbox.storage.entities import OutputTag
        
        initial_data = {
            "outputTagId": 401,
            "created_at": datetime(2023, 1, 1),
            "updated_at": datetime(2023, 1, 2),
            "tag": "tag1",
            "userId": 1,
            "isDeleted": False
        }
        
        entity = OutputTag(initial_data)
        
        # Updated data with later timestamp
        updated_data = {
            **initial_data,
            "updated_at": datetime(2023, 1, 3),
            "isDeleted": True
        }
        
        sync_map = {"outputTag": {"idMap": {401: 401}}}
        mock_storage = type("MockStorage", (), {})()
        
        # When
        was_merged = await entity.merge_existing(
            mock_storage, None, updated_data, sync_map, None
        )
        
        # Then
        assert was_merged is True
        assert entity.is_deleted == 1

    @pytest.mark.skip(reason="OutputTag entity not implemented yet")
    @pytest.mark.asyncio
    async def test_mergeexisting_does_not_merge_when_ei_updated_at_less_than_or_equal_this_updated_at(
        self
    ) -> None:
        """Given: OutputTag entity with same or newer updated_at
           When: Call merge_existing with same or older updated_at
           Then: Entity is not updated
           
        Reference: src/storage/schema/entities/__tests/OutputTagTests.test.ts
                  test('1_mergeExisting does not merge when ei.updated_at <= this.updated_at')
        """
        # Given
        from bsv_wallet_toolbox.storage.entities import OutputTag
        
        initial_data = {
            "outputTagId": 402,
            "created_at": datetime(2023, 1, 1),
            "updated_at": datetime(2023, 1, 2),
            "tag": "tag2",
            "userId": 1,
            "isDeleted": False
        }
        
        entity = OutputTag(initial_data)
        
        # Earlier data
        earlier_data = {
            **initial_data,
            "updated_at": datetime(2023, 1, 1),
            "isDeleted": True
        }
        
        sync_map = {"outputTag": {"idMap": {1: 1}}}
        mock_storage = type("MockStorage", (), {})()
        
        # When
        was_merged = await entity.merge_existing(
            mock_storage, None, earlier_data, sync_map, None
        )
        
        # Then
        assert was_merged is False
        assert entity.is_deleted == 0

    @pytest.mark.skip(reason="OutputTag entity not implemented yet")
    @pytest.mark.asyncio
    async def test_equals_identifies_matching_entities_without_syncmap(self) -> None:
        """Given: Two OutputTag entities with identical data
           When: Call equals method without syncMap
           Then: Returns True
           
        Reference: src/storage/schema/entities/__tests/OutputTagTests.test.ts
                  test('2_equals identifies matching entities without syncMap')
        """
        # Given
        from bsv_wallet_toolbox.storage.entities import OutputTag
        
        data = {
            "outputTagId": 403,
            "created_at": datetime(2023, 1, 1),
            "updated_at": datetime(2023, 1, 2),
            "tag": "tag3",
            "userId": 1,
            "isDeleted": False
        }
        
        entity1 = OutputTag(data)
        entity2 = OutputTag(data)
        
        # When/Then
        assert entity1.equals(entity2.to_api()) is True

    @pytest.mark.skip(reason="OutputTag entity not implemented yet")
    @pytest.mark.asyncio
    async def test_equals_identifies_non_matching_entities_when_tags_differ(self) -> None:
        """Given: Two OutputTag entities with different tags
           When: Call equals method
           Then: Returns False
           
        Reference: src/storage/schema/entities/__tests/OutputTagTests.test.ts
                  test('3_equals identifies non-matching entities when tags differ')
        """
        # Given
        from bsv_wallet_toolbox.storage.entities import OutputTag
        
        data1 = {
            "outputTagId": 404,
            "created_at": datetime(2023, 1, 1),
            "updated_at": datetime(2023, 1, 2),
            "tag": "tag4",
            "userId": 1,
            "isDeleted": False
        }
        data2 = {**data1, "tag": "tag2"}
        
        entity1 = OutputTag(data1)
        entity2 = OutputTag(data2)
        
        # When/Then
        assert entity1.equals(entity2.to_api()) is False

    @pytest.mark.skip(reason="OutputTag entity not implemented yet")
    @pytest.mark.asyncio
    async def test_equals_identifies_non_matching_entities_when_isdeleted_differs(self) -> None:
        """Given: Two OutputTag entities with different isDeleted
           When: Call equals method
           Then: Returns False
           
        Reference: src/storage/schema/entities/__tests/OutputTagTests.test.ts
                  test('4_equals identifies non-matching entities when isDeleted differs')
        """
        # Given
        from bsv_wallet_toolbox.storage.entities import OutputTag
        
        data1 = {
            "outputTagId": 405,
            "created_at": datetime(2023, 1, 1),
            "updated_at": datetime(2023, 1, 2),
            "tag": "tag5",
            "userId": 1,
            "isDeleted": False
        }
        data2 = {**data1, "isDeleted": True}
        
        entity1 = OutputTag(data1)
        entity2 = OutputTag(data2)
        
        # When/Then
        assert entity1.equals(entity2.to_api()) is False

    @pytest.mark.skip(reason="OutputTag entity not implemented yet")
    @pytest.mark.asyncio
    async def test_equals_identifies_matching_entities_with_syncmap(self) -> None:
        """Given: Two OutputTag entities with identical data
           When: Call equals method with syncMap
           Then: Returns True
           
        Reference: src/storage/schema/entities/__tests/OutputTagTests.test.ts
                  test('5_equals identifies matching entities with syncMap')
        """
        # Given
        from bsv_wallet_toolbox.storage.entities import OutputTag
        
        data = {
            "outputTagId": 406,
            "created_at": datetime(2023, 1, 1),
            "updated_at": datetime(2023, 1, 2),
            "tag": "tag6",
            "userId": 1,
            "isDeleted": False
        }
        
        entity1 = OutputTag(data)
        entity2 = OutputTag(data)
        
        sync_map = {"outputTag": {"idMap": {1: 1}}}
        
        # When/Then
        assert entity1.equals(entity2.to_api(), sync_map) is True

    @pytest.mark.skip(reason="OutputTag entity not implemented yet")
    @pytest.mark.asyncio
    async def test_equals_identifies_non_matching_entities_when_userids_differ_and_no_syncmap_is_provided(
        self
    ) -> None:
        """Given: Two OutputTag entities with different userIds
           When: Call equals method without syncMap
           Then: Returns False
           
        Reference: src/storage/schema/entities/__tests/OutputTagTests.test.ts
                  test('6_equals identifies non-matching entities when userIds differ and no syncMap is provided')
        """
        # Given
        from bsv_wallet_toolbox.storage.entities import OutputTag
        
        data1 = {
            "outputTagId": 407,
            "created_at": datetime(2023, 1, 1),
            "updated_at": datetime(2023, 1, 2),
            "tag": "tag7",
            "userId": 1,
            "isDeleted": False
        }
        data2 = {**data1, "userId": 2}
        
        entity1 = OutputTag(data1)
        entity2 = OutputTag(data2)
        
        # When/Then
        assert entity1.equals(entity2.to_api()) is False

    @pytest.mark.skip(reason="OutputTag entity not implemented yet")
    def test_getters_and_setters_work_as_expected_for_outputtag(self) -> None:
        """Given: OutputTag entity
           When: Set and get all properties
           Then: Getters and setters work correctly
           
        Reference: src/storage/schema/entities/__tests/OutputTagTests.test.ts
                  test('7_getters and setters work as expected for OutputTag')
        """
        # Given
        from bsv_wallet_toolbox.storage.entities import OutputTag
        
        now = datetime.now()
        later = datetime.fromtimestamp(now.timestamp() + 1)
        
        output_tag = OutputTag()
        
        # Set values using setters
        output_tag.output_tag_id = 123
        output_tag.created_at = now
        output_tag.updated_at = later
        output_tag.tag = "Test Tag"
        output_tag.user_id = 456
        output_tag.is_deleted = True
        
        # Validate values using getters
        assert output_tag.output_tag_id == 123
        assert output_tag.created_at == now
        assert output_tag.updated_at == later
        assert output_tag.tag == "Test Tag"
        assert output_tag.user_id == 456
        assert output_tag.is_deleted is True
        
        # Validate id, entity_name, and entity_table
        assert output_tag.id == 123
        assert output_tag.entity_name == "outputTag"
        assert output_tag.entity_table == "output_tags"
        
        # Update id using override setter
        output_tag.id = 789
        
        # Validate id again
        assert output_tag.id == 789

