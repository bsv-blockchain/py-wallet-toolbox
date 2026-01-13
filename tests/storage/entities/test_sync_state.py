"""Unit tests for SyncState entity.

Reference: toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntitySyncState.ts
"""

from datetime import datetime

from bsv_wallet_toolbox.storage.entities import SyncState


class TestSyncState:
    """Test suite for SyncState entity."""

    def test_sync_state_init_default(self) -> None:
        """Test SyncState initialization with default values."""
        entity = SyncState()

        assert entity.sync_state_id == 0
        assert entity.user_id == 0
        assert entity.storage_identity_key == ""
        assert entity.storage_name == ""
        assert entity.status == ""
        assert entity.init is False
        assert entity.ref_num == 0
        assert entity.sync_map == ""
        assert isinstance(entity.created_at, datetime)
        assert isinstance(entity.updated_at, datetime)

    def test_sync_state_init_with_api_object(self) -> None:
        """Test SyncState initialization with API object."""
        api_obj = {
            "syncStateId": 123,
            "userId": 456,
            "storageIdentityKey": "test_key",
            "storageName": "test_storage",
            "status": "active",
            "init": True,
            "refNum": 789,
            "syncMap": "test_map",
            "createdAt": datetime(2023, 1, 1, 12, 0, 0),
            "updatedAt": datetime(2023, 1, 2, 12, 0, 0),
        }

        entity = SyncState(api_obj)

        assert entity.sync_state_id == 123
        assert entity.user_id == 456
        assert entity.storage_identity_key == "test_key"
        assert entity.storage_name == "test_storage"
        assert entity.status == "active"
        assert entity.init is True
        assert entity.ref_num == 789
        assert entity.sync_map == "test_map"
        assert entity.created_at == datetime(2023, 1, 1, 12, 0, 0)
        assert entity.updated_at == datetime(2023, 1, 2, 12, 0, 0)

    def test_sync_state_init_with_empty_api_object(self) -> None:
        """Test SyncState initialization with empty API object."""
        entity = SyncState({})

        assert entity.sync_state_id == 0
        assert entity.user_id == 0
        assert entity.storage_identity_key == ""
        assert entity.storage_name == ""
        assert entity.status == ""
        assert entity.init is False
        assert entity.ref_num == 0
        assert entity.sync_map == ""

    def test_sync_state_entity_properties(self) -> None:
        """Test SyncState entity properties."""
        entity = SyncState()

        assert entity.entity_name == "syncState"
        assert entity.entity_table == "sync_states"

    def test_sync_state_to_api(self) -> None:
        """Test SyncState to_api conversion."""
        entity = SyncState()
        entity.sync_state_id = 123
        entity.user_id = 456
        entity.storage_identity_key = "test_key"
        entity.storage_name = "test_storage"
        entity.status = "active"
        entity.init = True
        entity.ref_num = 789
        entity.sync_map = "test_map"
        entity.created_at = datetime(2023, 1, 1, 12, 0, 0)
        entity.updated_at = datetime(2023, 1, 2, 12, 0, 0)

        api_result = entity.to_api()

        expected = {
            "syncStateId": 123,
            "userId": 456,
            "storageIdentityKey": "test_key",
            "storageName": "test_storage",
            "status": "active",
            "init": True,
            "refNum": 789,
            "syncMap": "test_map",
            "createdAt": datetime(2023, 1, 1, 12, 0, 0),
            "updatedAt": datetime(2023, 1, 2, 12, 0, 0),
        }

        assert api_result == expected

    def test_sync_state_equals_true(self) -> None:
        """Test SyncState equals returns True for identical entities."""
        entity = SyncState()
        entity.status = "active"
        entity.ref_num = 123

        other = {"status": "active", "refNum": 123}

        assert entity.equals(other) is True

    def test_sync_state_equals_false(self) -> None:
        """Test SyncState equals returns False for different entities."""
        entity = SyncState()
        entity.status = "active"
        entity.ref_num = 123

        other = {"status": "inactive", "refNum": 456}

        assert entity.equals(other) is False

    def test_sync_state_merge_existing_updates(self) -> None:
        """Test SyncState merge_existing updates fields when remote is newer."""
        entity = SyncState()
        entity.status = "old_status"
        entity.ref_num = 100
        entity.updated_at = datetime(2023, 1, 1, 10, 0, 0)

        ei = {
            "status": "new_status",
            "refNum": 200,
            "syncMap": "new_map",
            "updatedAt": datetime(2023, 1, 1, 12, 0, 0),  # newer
        }

        result = entity.merge_existing(None, None, ei)

        assert result is True
        assert entity.status == "new_status"
        assert entity.ref_num == 200
        assert entity.sync_map == "new_map"

    def test_sync_state_merge_existing_no_update(self) -> None:
        """Test SyncState merge_existing doesn't update when remote is older."""
        entity = SyncState()
        entity.status = "current_status"
        entity.updated_at = datetime(2023, 1, 1, 12, 0, 0)

        ei = {
            "status": "old_status",
            "updatedAt": datetime(2023, 1, 1, 10, 0, 0),  # older
        }

        result = entity.merge_existing(None, None, ei)

        assert result is False
        assert entity.status == "current_status"  # unchanged

    def test_sync_state_merge_new(self) -> None:
        """Test SyncState merge_new resets sync_state_id."""
        entity = SyncState()
        entity.sync_state_id = 123

        entity.merge_new(None, 456)

        assert entity.sync_state_id == 0
