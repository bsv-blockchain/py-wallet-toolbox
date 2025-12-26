"""Unit tests for TxLabel entity.

Reference: wallet-toolbox/src/storage/schema/entities/__tests/TxLabelTests.test.ts
"""

from datetime import datetime
from typing import Any

from bsv_wallet_toolbox.storage.entities import TxLabel


class TestTxLabelEntity:
    """Test suite for TxLabel entity."""

    def test_creates_txlabel_with_default_values(self) -> None:
        """Given: No arguments
           When: Create TxLabel with default constructor
           Then: Entity has correct default values

        Reference: src/storage/schema/entities/__tests/TxLabelTests.test.ts
                  test('1_creates_txLabel_with_default_values')
        """
        # Given/When

        tx_label = TxLabel()

        # Then
        assert tx_label.tx_label_id == 0
        assert tx_label.label == ""
        assert tx_label.user_id == 0
        assert tx_label.is_deleted is False
        assert isinstance(tx_label.created_at, datetime)
        assert isinstance(tx_label.updated_at, datetime)
        assert tx_label.created_at <= tx_label.updated_at

    def test_creates_txlabel_with_provided_api_object(self) -> None:
        """Given: API object with all properties
           When: Create TxLabel with API object
           Then: Entity properties match API object

        Reference: src/storage/schema/entities/__tests/TxLabelTests.test.ts
                  test('2_creates_txLabel_with_provided_api_object')
        """
        # Given

        now = datetime.now()
        api_object = {
            "txLabelId": 42,
            "label": "Test Label",
            "userId": 101,
            "isDeleted": False,
            "createdAt": now,
            "updatedAt": now,
        }

        # When
        tx_label = TxLabel(api_object)

        # Then
        assert tx_label.tx_label_id == 42
        assert tx_label.label == "Test Label"
        assert tx_label.user_id == 101
        assert tx_label.is_deleted is False
        assert tx_label.created_at == now
        assert tx_label.updated_at == now

    def test_getters_and_setters_work_correctly(self) -> None:
        """Given: TxLabel entity
           When: Set and get all properties including id
           Then: Getters and setters work correctly

        Reference: src/storage/schema/entities/__tests/TxLabelTests.test.ts
                  test('3_getters_and_setters_work_correctly')
        """
        # Given

        tx_label = TxLabel()

        # When
        now = datetime.now()
        tx_label.tx_label_id = 1
        tx_label.label = "New Label"
        tx_label.user_id = 200
        tx_label.is_deleted = True
        tx_label.created_at = now
        tx_label.updated_at = now
        tx_label.id = 2

        # Then
        assert tx_label.id == 2
        assert tx_label.entity_name == "txLabel"
        assert tx_label.entity_table == "tx_labels"
        assert tx_label.tx_label_id == 2
        assert tx_label.label == "New Label"
        assert tx_label.user_id == 200
        assert tx_label.is_deleted is True
        assert tx_label.created_at == now
        assert tx_label.updated_at == now

    def test_mergeexisting_does_not_update_txlabel_when_ei_updated_at_is_older(self) -> None:
        """Given: TxLabel entity with newer updated_at in database
           When: Call merge_existing with older updated_at
           Then: Entity is not updated, returns False

        Reference: src/storage/schema/entities/__tests/TxLabelTests.test.ts
                  test('5_mergeExisting_does_not_update_txLabel_when_ei_updated_at_is_older')
        """
        # Given

        tx_label = TxLabel(
            {
                "txLabelId": 302,
                "label": "Original Label",
                "userId": 1,
                "isDeleted": False,
                "createdAt": datetime(2023, 1, 1),
                "updatedAt": datetime(2023, 2, 1),
            }
        )

        older_ei = {
            "txLabelId": 302,
            "label": "Outdated Label",
            "userId": 1,
            "isDeleted": True,
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 1),
        }

        mock_storage = type("MockStorage", (), {})()
        sync_map: dict[str, Any] = {}

        # When
        result = tx_label.merge_existing(mock_storage, None, older_ei, sync_map)

        # Then
        assert result is False
        assert tx_label.label == "Original Label"
        assert tx_label.is_deleted is False
        assert tx_label.updated_at == datetime(2023, 2, 1)

    def test_equals_identifies_matching_entities(self) -> None:
        """Given: Two TxLabel entities with matching properties using syncMap
           When: Call equals method with syncMap
           Then: Returns True

        Reference: src/storage/schema/entities/__tests/TxLabelTests.test.ts
                  test('6_equals_identifies_matching_entities')
        """
        # Given

        tx_label1 = TxLabel(
            {
                "txLabelId": 303,
                "userId": 1,
                "label": "Test Label",
                "isDeleted": False,
                "createdAt": datetime(2023, 1, 1),
                "updatedAt": datetime(2023, 1, 2),
            }
        )

        tx_label2 = TxLabel(
            {
                "txLabelId": 304,
                "userId": 1,
                "label": "Test Label",
                "isDeleted": False,
                "createdAt": datetime(2023, 1, 1),
                "updatedAt": datetime(2023, 1, 2),
            }
        )

        sync_map = {"txLabel": {"idMap": {tx_label2.user_id: tx_label1.user_id}, "count": 1}}

        # When/Then
        assert tx_label1.equals(tx_label2.to_api(), sync_map) is True

    def test_equals_identifies_non_matching_entities(self) -> None:
        """Given: Two TxLabel entities with different properties
           When: Call equals method with syncMap
           Then: Returns False

        Reference: src/storage/schema/entities/__tests/TxLabelTests.test.ts
                  test('7_equals_identifies_non_matching_entities')
        """
        # Given

        tx_label1 = TxLabel(
            {
                "txLabelId": 305,
                "userId": 1,
                "label": "Label A",
                "isDeleted": False,
                "createdAt": datetime(2023, 1, 1),
                "updatedAt": datetime(2023, 1, 2),
            }
        )

        tx_label2 = TxLabel(
            {
                "txLabelId": 306,
                "userId": 1,
                "label": "Label B",
                "isDeleted": True,
                "createdAt": datetime(2023, 1, 1),
                "updatedAt": datetime(2023, 1, 2),
            }
        )

        sync_map = {"txLabel": {"idMap": {tx_label2.user_id: tx_label1.user_id}, "count": 1}}

        # When/Then
        assert tx_label1.equals(tx_label2.to_api(), sync_map) is False
