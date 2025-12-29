"""Unit tests for OutputBasket entity.

Reference: wallet-toolbox/src/storage/schema/entities/__tests/OutputBasketTests.test.ts
"""

from datetime import datetime

from bsv_wallet_toolbox.storage.entities import OutputBasket


class TestOutputBasketEntity:
    """Test suite for OutputBasket entity."""

    def test_mergeexisting_merges_and_updates_entity_when_ei_updated_at_greater_than_this_updated_at(
        self,
    ) -> None:
        """Given: OutputBasket entity with older updated_at
           When: Call merge_existing with newer updated_at
           Then: Entity and database are updated

        Reference: src/storage/schema/entities/__tests/OutputBasketTests.test.ts
                  test('1_mergeExisting merges and updates entity when ei.updated_at > this.updated_at')
        """
        # Given

        initial_data = {
            "basketId": 100,
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "userId": 1,
            "name": "Basket1",
            "numberOfDesiredUTXOs": 10,
            "minimumDesiredUTXOValue": 5000,
            "isDeleted": False,
        }

        entity = OutputBasket(initial_data)

        # Updated data with later timestamp
        updated_data = {
            **initial_data,
            "updatedAt": datetime(2023, 1, 3),
            "numberOfDesiredUTXOs": 20,
            "minimumDesiredUTXOValue": 10000,
            "isDeleted": True,
        }

        sync_map = {"outputBasket": {"idMap": {100: 100}}}
        mock_storage = type("MockStorage", (), {})()

        # When
        was_merged = entity.merge_existing(mock_storage, None, updated_data, sync_map, None)

        # Then
        assert was_merged is True
        assert entity.number_of_desired_utxos == 20
        assert entity.minimum_desired_utxo_value == 10000
        assert entity.is_deleted == 1

    def test_mergeexisting_does_not_merge_when_ei_updated_at_less_than_or_equal_this_updated_at(self) -> None:
        """Given: OutputBasket entity with same or newer updated_at
           When: Call merge_existing with same or older updated_at
           Then: Entity is not updated

        Reference: src/storage/schema/entities/__tests/OutputBasketTests.test.ts
                  test('2_mergeExisting does not merge when ei.updated_at <= this.updated_at')
        """
        # Given

        initial_data = {
            "basketId": 200,
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "userId": 1,
            "name": "Basket2",
            "numberOfDesiredUTXOs": 10,
            "minimumDesiredUTXOValue": 5000,
            "isDeleted": False,
        }

        entity = OutputBasket(initial_data)

        # Earlier data
        earlier_data = {
            **initial_data,
            "updatedAt": datetime(2023, 1, 1),
            "numberOfDesiredUTXOs": 20,
            "minimumDesiredUTXOValue": 10000,
            "isDeleted": True,
        }

        sync_map = {"outputBasket": {"idMap": {200: 200}}}
        mock_storage = type("MockStorage", (), {})()

        # When
        was_merged = entity.merge_existing(mock_storage, None, earlier_data, sync_map, None)

        # Then
        assert was_merged is False
        assert entity.number_of_desired_utxos == 10
        assert entity.minimum_desired_utxo_value == 5000
        assert entity.is_deleted == 0

    def test_equals_identifies_matching_entities_with_and_without_syncmap(self) -> None:
        """Given: Two OutputBasket entities with identical data
           When: Call equals method with and without syncMap
           Then: Returns True in both cases

        Reference: src/storage/schema/entities/__tests/OutputBasketTests.test.ts
                  test('equals identifies matching entities with and without SyncMap')
        """
        # Given

        basket_data = {
            "basketId": 401,
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "userId": 1,
            "name": "Test Basket",
            "numberOfDesiredUTXOs": 10,
            "minimumDesiredUTXOValue": 1000,
            "isDeleted": False,
        }

        entity1 = OutputBasket(basket_data)
        entity2 = OutputBasket(basket_data)

        sync_map = {"outputBasket": {"idMap": {401: 401}}}

        # When/Then
        assert entity1.equals(entity2.to_api()) is True
        assert entity1.equals(entity2.to_api(), sync_map) is True

    def test_equals_identifies_non_matching_entities(self) -> None:
        """Given: Two OutputBasket entities with different data
           When: Call equals method with and without syncMap
           Then: Returns False in both cases

        Reference: src/storage/schema/entities/__tests/OutputBasketTests.test.ts
                  test('equals identifies non-matching entities')
        """
        # Given

        basket_data1 = {
            "basketId": 402,
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "userId": 1,
            "name": "Test Basket 1",
            "numberOfDesiredUTXOs": 10,
            "minimumDesiredUTXOValue": 1000,
            "isDeleted": False,
        }

        basket_data2 = {
            "basketId": 403,
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "userId": 1,
            "name": "Test Basket 2",
            "numberOfDesiredUTXOs": 5,
            "minimumDesiredUTXOValue": 500,
            "isDeleted": True,
        }

        entity1 = OutputBasket(basket_data1)
        entity2 = OutputBasket(basket_data2)

        sync_map = {"outputBasket": {"idMap": {1: 2}}}

        # When/Then
        assert entity1.equals(entity2.to_api()) is False
        assert entity1.equals(entity2.to_api(), sync_map) is False

    def test_outputbasket_getters_setters_and_updateapi(self) -> None:
        """Given: OutputBasket entity with initial data
           When: Get and set all properties
           Then: Getters and setters work correctly

        Reference: src/storage/schema/entities/__tests/OutputBasketTests.test.ts
                  test('OutputBasket getters, setters, and updateApi')
        """
        # Given

        initial_data = {
            "basketId": 123,
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "userId": 1,
            "name": "Test Basket",
            "numberOfDesiredUTXOs": 10,
            "minimumDesiredUTXOValue": 1000,
            "isDeleted": False,
        }

        entity = OutputBasket(initial_data)

        # Validate getters
        assert entity.basket_id == 123
        assert entity.created_at == datetime(2023, 1, 1)
        assert entity.updated_at == datetime(2023, 1, 2)
        assert entity.user_id == 1
        assert entity.name == "Test Basket"
        assert entity.number_of_desired_utxos == 10
        assert entity.minimum_desired_utxo_value == 1000
        assert entity.is_deleted is False
        assert entity.id == 123
        assert entity.entity_name == "outputBasket"
        assert entity.entity_table == "output_baskets"

        # Validate setters
        entity.basket_id = 456
        entity.created_at = datetime(2023, 2, 1)
        entity.updated_at = datetime(2023, 2, 2)
        entity.user_id = 2
        entity.name = "Updated Basket"
        entity.number_of_desired_utxos = 20
        entity.minimum_desired_utxo_value = 2000
        entity.is_deleted = True
        entity.id = 456

        assert entity.basket_id == 456
        assert entity.created_at == datetime(2023, 2, 1)
        assert entity.updated_at == datetime(2023, 2, 2)
        assert entity.user_id == 2
        assert entity.name == "Updated Basket"
        assert entity.number_of_desired_utxos == 20
        assert entity.minimum_desired_utxo_value == 2000
        assert entity.is_deleted is True
        assert entity.id == 456

        # Test update_api (even though it does nothing)
        entity.update_api()  # Should not raise
