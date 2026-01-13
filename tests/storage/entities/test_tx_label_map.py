"""Unit tests for TxLabelMap entity.

Reference: wallet-toolbox/src/storage/schema/entities/__tests/TxLabelMapTests.test.ts
"""

from datetime import datetime
from typing import Any

import pytest

from bsv_wallet_toolbox.storage.entities import TxLabelMap


class TestTxLabelMapEntity:
    """Test suite for TxLabelMap entity."""

    def test_creates_instance_with_default_values(self) -> None:
        """Given: No arguments
           When: Create TxLabelMap with default constructor
           Then: Entity has correct default values

        Reference: src/storage/schema/entities/__tests/TxLabelMapTests.test.ts
                  test('1_creates_instance_with_default_values')
        """
        # Given/When

        tx_label_map = TxLabelMap()
        now = datetime.now()

        # Then
        assert tx_label_map.transaction_id == 0
        assert tx_label_map.tx_label_id == 0
        assert tx_label_map.is_deleted is False
        assert isinstance(tx_label_map.created_at, datetime)
        assert isinstance(tx_label_map.updated_at, datetime)
        assert tx_label_map.created_at.timestamp() <= now.timestamp()
        assert tx_label_map.updated_at.timestamp() <= now.timestamp()

    def test_creates_instance_with_provided_api_object(self) -> None:
        """Given: API object with all properties
           When: Create TxLabelMap with API object
           Then: Entity properties match API object

        Reference: src/storage/schema/entities/__tests/TxLabelMapTests.test.ts
                  test('2_creates_instance_with_provided_api_object')
        """
        # Given

        now = datetime.now()
        api_object = {"transactionId": 123, "txLabelId": 456, "createdAt": now, "updatedAt": now, "isDeleted": True}

        # When
        tx_label_map = TxLabelMap(api_object)

        # Then
        assert tx_label_map.transaction_id == 123
        assert tx_label_map.tx_label_id == 456
        assert tx_label_map.is_deleted is True
        assert tx_label_map.created_at == now
        assert tx_label_map.updated_at == now

    def test_getters_and_setters_work_correctly_correctly(self) -> None:
        """Given: TxLabelMap entity
           When: Set and get all properties
           Then: Getters and setters work correctly

        Reference: src/storage/schema/entities/__tests/TxLabelMapTests.test.ts
                  test('3_getters_and_setters_work_correctly')
        """
        # Given

        tx_label_map = TxLabelMap()

        # When
        now = datetime.now()
        tx_label_map.transaction_id = 1001
        tx_label_map.tx_label_id = 2002
        tx_label_map.is_deleted = True
        tx_label_map.created_at = now
        tx_label_map.updated_at = now

        # Then
        assert tx_label_map.transaction_id == 1001
        assert tx_label_map.tx_label_id == 2002
        assert tx_label_map.is_deleted is True
        assert tx_label_map.created_at == now
        assert tx_label_map.updated_at == now

    def test_updateapi_does_nothing(self) -> None:
        """Given: TxLabelMap entity
           When: Call update_api
           Then: No exception is raised

        Reference: src/storage/schema/entities/__tests/TxLabelMapTests.test.ts
                  test('4_updateApi_does_nothing')
        """
        # Given

        tx_label_map = TxLabelMap()

        # When/Then
        tx_label_map.update_api()  # Should not throw

    def test_get_id_throws_error(self) -> None:
        """Given: TxLabelMap entity
           When: Access id property
           Then: Raises exception

        Reference: src/storage/schema/entities/__tests/TxLabelMapTests.test.ts
                  test('5_get_id_throws_error')
        """
        # Given

        tx_label_map = TxLabelMap()

        # When/Then
        with pytest.raises(Exception):
            _ = tx_label_map.id

    def test_equals_checks_equality_correctly(self) -> None:
        """Given: Two TxLabelMap entities with matching data and syncMap
           When: Call equals method
           Then: Returns True

        Reference: src/storage/schema/entities/__tests/TxLabelMapTests.test.ts
                  test('6_equals_checks_equality_correctly')
        """
        # Given

        sync_map: dict[str, Any] = {"transaction": {"idMap": {123: 123}}, "txLabel": {"idMap": {456: 456}}}

        tx_label_map = TxLabelMap(
            {
                "transactionId": 123,
                "txLabelId": 456,
                "isDeleted": False,
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            }
        )

        other = {"transactionId": 123, "txLabelId": 456, "isDeleted": False}

        # When
        result = tx_label_map.equals(other, sync_map)

        # Then
        assert result is True

    def test_mergefind_finds_or_creates_entity(self) -> None:
        """Given: Storage with existing TxLabelMap and syncMap
           When: Call merge_find
           Then: Finds existing entity and returns it

        Reference: src/storage/schema/entities/__tests/TxLabelMapTests.test.ts
                  test('7_mergeFind_finds_or_creates_entity')
        """
        # Given

        def mock_find_tx_label_maps(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
            return [{"transactionId": 999, "txLabelId": 888}]

        mock_storage = type("MockStorage", (), {"findTxLabelMaps": mock_find_tx_label_maps})()

        sync_map = {"transaction": {"idMap": {123: 999}}, "txLabel": {"idMap": {456: 888}}}

        ei = {"transactionId": 123, "txLabelId": 456}

        # When
        result = TxLabelMap.merge_find(mock_storage, 1, ei, sync_map)

        # Then
        assert result["found"] is True
        assert result["eo"].transaction_id == 999
        assert result["eo"].tx_label_id == 888

    def test_mergenew_inserts_entity(self) -> None:
        """Given: TxLabelMap entity and storage with syncMap
           When: Call merge_new
           Then: Inserts entity with mapped IDs

        Reference: src/storage/schema/entities/__tests/TxLabelMapTests.test.ts
                  test('8_mergeNew_inserts_entity')
        """
        # Given

        inserted_data = None

        def mock_insert(data: dict[str, Any], trx: Any = None) -> None:
            nonlocal inserted_data
            inserted_data = data

        mock_storage = type("MockStorage", (), {"insertTxLabelMap": staticmethod(mock_insert)})()

        sync_map = {"transaction": {"idMap": {123: 999}}, "txLabel": {"idMap": {456: 888}}}

        tx_label_map = TxLabelMap(
            {
                "transactionId": 123,
                "txLabelId": 456,
                "createdAt": datetime(2022, 2, 1),
                "updatedAt": datetime(2022, 2, 1),
                "isDeleted": False,
            }
        )

        # When
        tx_label_map.merge_new(mock_storage, 1, sync_map)

        # Then
        assert inserted_data is not None
        assert inserted_data["transactionId"] == 999
        assert inserted_data["txLabelId"] == 888

    def test_mergeexisting_updates_entity(self) -> None:
        """Given: TxLabelMap entity with older data
           When: Call merge_existing with newer data
           Then: Updates entity and database

        Reference: src/storage/schema/entities/__tests/TxLabelMapTests.test.ts
                  test('9_mergeExisting_updates_entity')
        """
        # Given

        updated_data = None

        def mock_update(transaction_id: int, tx_label_id: int, data: dict[str, Any], trx: Any = None) -> None:
            nonlocal updated_data
            updated_data = data

        mock_storage = type("MockStorage", (), {"updateTxLabelMap": staticmethod(mock_update)})()

        tx_label_map = TxLabelMap(
            {
                "transactionId": 123,
                "txLabelId": 456,
                "createdAt": datetime(2022, 2, 1),
                "updatedAt": datetime(2022, 2, 1),
                "isDeleted": False,
            }
        )

        ei = {
            "transactionId": 123,
            "txLabelId": 456,
            "isDeleted": True,
            "createdAt": datetime.now(),
            "updatedAt": datetime(2023, 2, 1),
        }

        sync_map = {"transaction": {"idMap": {123: 999}}, "txLabel": {"idMap": {456: 888}}}

        # When
        result = tx_label_map.merge_existing(mock_storage, datetime.now(), ei, sync_map)

        # Then
        assert result is True
        assert updated_data is not None
        assert updated_data["isDeleted"] is True

    def test_entityname_returns_correct_value(self) -> None:
        """Given: TxLabelMap entity
           When: Access entity_name property
           Then: Returns 'txLabelMap'

        Reference: src/storage/schema/entities/__tests/TxLabelMapTests.test.ts
                  test('10_entityName_returns_correct_value')
        """
        # Given

        tx_label_map = TxLabelMap()

        # When/Then
        assert tx_label_map.entity_name == "txLabelMap"

    def test_entitytable_returns_correct_value(self) -> None:
        """Given: TxLabelMap entity
           When: Access entity_table property
           Then: Returns 'tx_labels_map'

        Reference: src/storage/schema/entities/__tests/TxLabelMapTests.test.ts
                  test('11_entityTable_returns_correct_value')
        """
        # Given

        tx_label_map = TxLabelMap()

        # When/Then
        assert tx_label_map.entity_table == "tx_labels_map"

    def test_equals_identifies_matching_entities_entities(self) -> None:
        """Given: Two TxLabelMap entities with matching data and syncMap
           When: Call equals method
           Then: Returns True

        Reference: src/storage/schema/entities/__tests/TxLabelMapTests.test.ts
                  test('12_equals_identifies_matching_entities')
        """
        # Given

        tx_label_map1 = TxLabelMap(
            {
                "transactionId": 405,
                "txLabelId": 306,
                "isDeleted": False,
                "createdAt": datetime(2023, 1, 1),
                "updatedAt": datetime(2023, 1, 2),
            }
        )

        tx_label_map2 = TxLabelMap(
            {
                "transactionId": 406,
                "txLabelId": 307,
                "isDeleted": False,
                "createdAt": datetime(2023, 1, 1),
                "updatedAt": datetime(2023, 1, 2),
            }
        )

        sync_map = {"transaction": {"idMap": {406: 405}, "count": 1}, "txLabel": {"idMap": {307: 306}, "count": 1}}

        # When/Then
        assert tx_label_map1.equals(tx_label_map2.to_api(), sync_map) is True

    def test_equals_identifies_non_matching_entities_entities(self) -> None:
        """Given: Two TxLabelMap entities with different data
           When: Call equals method with syncMap
           Then: Returns False

        Reference: src/storage/schema/entities/__tests/TxLabelMapTests.test.ts
                  test('13_equals_identifies_non_matching_entities')
        """
        # Given

        tx_label_map1 = TxLabelMap(
            {
                "transactionId": 103,
                "txLabelId": 1,
                "isDeleted": False,
                "createdAt": datetime(2023, 1, 1),
                "updatedAt": datetime(2023, 1, 2),
            }
        )

        tx_label_map2 = TxLabelMap(
            {
                "transactionId": 104,
                "txLabelId": 1,
                "isDeleted": True,
                "createdAt": datetime(2023, 1, 1),
                "updatedAt": datetime(2023, 1, 2),
            }
        )

        sync_map = {
            "transaction": {"idMap": {tx_label_map1.transaction_id: tx_label_map2.transaction_id}, "count": 1},
            "txLabel": {"idMap": {tx_label_map1.tx_label_id: tx_label_map2.tx_label_id}, "count": 1},
        }

        # When/Then
        assert tx_label_map1.equals(tx_label_map2.to_api(), sync_map) is False
