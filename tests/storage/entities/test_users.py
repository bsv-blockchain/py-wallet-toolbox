"""Unit tests for User entity.

Reference: wallet-toolbox/src/storage/schema/entities/__tests/usersTests.test.ts
"""

import sys
from datetime import datetime
from typing import Any

import pytest

from bsv_wallet_toolbox.storage.entities import User


class TestUsersEntity:
    """Test suite for User entity."""

    def test_creates_user_with_default_values(self) -> None:
        """Given: Default User constructor
           When: Create User with no arguments
           Then: Returns User with correct default values

        Reference: src/storage/schema/entities/__tests/usersTests.test.ts
                  test('1_creates_user_with_default_values')
        """
        # Given/When

        user = User()

        # Then
        assert user.user_id == 0
        assert user.identity_key == ""
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        assert user.created_at <= user.updated_at

    def test_creates_user_with_provided_api_object(self) -> None:
        """Given: API object with user data
           When: Create User with provided API object
           Then: Returns User with values from API object

        Reference: src/storage/schema/entities/__tests/usersTests.test.ts
                  test('2_creates_user_with_provided_api_object')
        """
        # Given

        now = datetime.now()
        api_object = {
            "userId": 42,
            "createdAt": now,
            "updatedAt": now,
            "identityKey": "testIdentityKey",
            "activeStorage": "",
        }

        # When
        user = User(api_object)

        # Then
        assert user.user_id == 42
        assert user.identity_key == "testIdentityKey"
        assert user.created_at == now
        assert user.updated_at == now

    def test_getters_and_setters_work_correctly(self) -> None:
        """Given: User instance
           When: Set values using setters
           Then: Getters return the updated values

        Reference: src/storage/schema/entities/__tests/usersTests.test.ts
                  test('3_getters_and_setters_work_correctly')
        """
        # Given

        user = User()

        # When
        now = datetime.now()
        user.user_id = 1001
        user.identity_key = "newIdentityKey"
        user.created_at = now
        user.updated_at = now
        user.active_storage = "testActiveStorage"

        # Then
        assert user.user_id == 1001
        assert user.identity_key == "newIdentityKey"
        assert user.created_at == now
        assert user.updated_at == now
        assert user.active_storage == "testActiveStorage"

    def test_equals_identifies_matching_entities(self) -> None:
        """Given: Two User entities with same identityKey but different IDs
           When: Call equals method
           Then: Returns True (entities match by identityKey)

        Reference: src/storage/schema/entities/__tests/usersTests.test.ts
                  test('5_equals_identifies_matching_entities')
        """
        # Given

        user1 = User(
            {
                "userId": 2,
                "identityKey": "key1",
                "createdAt": datetime(2023, 1, 1),
                "updatedAt": datetime(2023, 1, 2),
                "activeStorage": "",
            }
        )

        user2_api = {
            "userId": 3,  # Different ID
            "identityKey": "key1",  # Same key
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "activeStorage": "",
        }

        sync_map: dict[str, Any] = {}

        # When/Then
        assert user1.equals(user2_api, sync_map) is True

    def test_equals_identifies_non_matching_entities(self) -> None:
        """Given: Two User entities with different identityKeys
           When: Call equals method
           Then: Returns False (entities do not match)

        Reference: src/storage/schema/entities/__tests/usersTests.test.ts
                  test('6_equals_identifies_non_matching_entities')
        """
        # Given

        user1 = User(
            {
                "userId": 4,
                "identityKey": "key2",
                "createdAt": datetime(2023, 1, 1),
                "updatedAt": datetime(2023, 1, 2),
                "activeStorage": "",
            }
        )

        user2_api = {
            "userId": 5,  # Different ID
            "identityKey": "key3",  # Different key
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "activeStorage": "",
        }

        sync_map: dict[str, Any] = {}

        # When/Then
        assert user1.equals(user2_api, sync_map) is False

    def test_handles_edge_cases_in_constructor(self) -> None:
        """Given: Partial API object with missing fields
           When: Create User with partial API object
           Then: Returns User with provided values and undefined for missing fields

        Reference: src/storage/schema/entities/__tests/usersTests.test.ts
                  test('7_handles_edge_cases_in_constructor')
        """
        # Given

        now = datetime.now()
        past_date = datetime.fromtimestamp(now.timestamp() - 1000000)

        partial_api_object = {"userId": 123, "createdAt": past_date}

        # When
        user = User(partial_api_object)

        # Then
        assert user.user_id == 123
        assert user.identity_key is None  # Default None for missing field
        assert user.created_at == past_date
        assert user.updated_at is None  # Default None for missing field

    def test_handles_large_input_values(self) -> None:
        """Given: API object with large values
           When: Create User with large userId and long identityKey
           Then: Returns User with correct large values

        Reference: src/storage/schema/entities/__tests/usersTests.test.ts
                  test('8_handles_large_input_values')
        """
        # Given

        now = datetime.now()
        large_user_id = sys.maxsize  # Python equivalent of MAX_SAFE_INTEGER
        long_identity_key = "x" * 1000

        api_object = {
            "userId": large_user_id,
            "createdAt": now,
            "updatedAt": now,
            "identityKey": long_identity_key,
            "activeStorage": "",
        }

        # When
        user = User(api_object)

        # Then
        assert user.user_id == large_user_id
        assert user.identity_key == long_identity_key

    def test_handles_empty_api_object(self) -> None:
        """Given: Empty API object
           When: Create User with empty dict
           Then: Returns User with all None/undefined values

        Reference: src/storage/schema/entities/__tests/usersTests.test.ts
                  test('10_handles_empty_api_object')
        """
        # Given

        empty_api_object: dict[str, Any] = {}

        # When
        user = User(empty_api_object)

        # Then
        assert user.user_id is None
        assert user.identity_key is None
        assert user.created_at is None
        assert user.updated_at is None

    def test_id_getter_and_setter_work_correctly(self) -> None:
        """Given: User instance
           When: Set id property
           Then: Getter returns the set value

        Reference: src/storage/schema/entities/__tests/usersTests.test.ts
                  test('11_id_getter_and_setter_work_correctly')
        """
        # Given

        user = User()

        # When
        user.id = 123

        # Then
        assert user.id == 123

    def test_entityname_returns_user(self) -> None:
        """Given: User instance
           When: Access entity_name property
           Then: Returns 'user'

        Reference: src/storage/schema/entities/__tests/usersTests.test.ts
                  test('12_entityName_returns_User')
        """
        # Given

        user = User()

        # When/Then
        assert user.entity_name == "user"

    def test_entitytable_returns_users(self) -> None:
        """Given: User instance
           When: Access entity_table property
           Then: Returns 'users'

        Reference: src/storage/schema/entities/__tests/usersTests.test.ts
                  test('13_entityTable_returns_users')
        """
        # Given

        user = User()

        # When/Then
        assert user.entity_table == "users"

    def test_mergeexisting_updates_user_when_ei_updated_at_is_newer(self) -> None:
        """Given: Existing User with old updated_at
           When: Call merge_existing with newer updated_at
           Then: User is updated and returns True

        Reference: src/storage/schema/entities/__tests/usersTests.test.ts
                  test('14_mergeExisting_updates_user_when_ei_updated_at_is_newer')
        """
        # Given

        user = User(
            {
                "userId": 1,
                "createdAt": datetime(2023, 1, 1),
                "updatedAt": datetime(2023, 1, 1),
                "identityKey": "oldKey",
                "activeStorage": "oldStorage",
            }
        )

        updated_ei = {
            "userId": 1,
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 2, 1),  # Newer updated_at
            "identityKey": "oldKey",
            "activeStorage": "newStorage",
        }

        # Mock storage
        update_called = False

        def mock_update_user(user_id: int, data: dict[str, Any]) -> None:
            nonlocal update_called
            update_called = True
            assert user_id == 1
            assert data["activeStorage"] == "newStorage"
            assert isinstance(data["updatedAt"], datetime)

        mock_storage = type("MockStorage", (), {"updateUser": mock_update_user})()

        # When
        result = user.merge_existing(mock_storage, None, updated_ei, None)

        # Then
        assert result is True
        assert user.active_storage == "newStorage"
        assert update_called

    def test_mergeexisting_does_not_update_user_when_ei_updated_at_is_older(self) -> None:
        """Given: Existing User with new updated_at
           When: Call merge_existing with older updated_at
           Then: User is not updated and returns False

        Reference: src/storage/schema/entities/__tests/usersTests.test.ts
                  test('15_mergeExisting_does_not_update_user_when_ei_updated_at_is_older')
        """
        # Given

        user = User(
            {
                "userId": 1,
                "createdAt": datetime(2023, 1, 1),
                "updatedAt": datetime(2023, 2, 1),
                "identityKey": "oldKey",
                "activeStorage": "oldStorage",
            }
        )

        older_ei = {
            "userId": 1,
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 1),  # Older updated_at
            "identityKey": "oldKey",
            "activeStorage": "newStorage",
        }

        # Mock storage that should not be called
        def mock_update_user(user_id: int, data: dict[str, Any]) -> None:
            raise AssertionError("This should not be called")

        mock_storage = type("MockStorage", (), {"updateUser": mock_update_user})()

        # When
        result = user.merge_existing(mock_storage, None, older_ei, None)

        # Then
        assert result is False
        assert user.active_storage == "oldStorage"

    def test_mergeexisting_updates_user_with_trx(self) -> None:
        """Given: Existing User and transaction token
           When: Call merge_existing with newer updated_at and trx
           Then: User is updated with trx and returns True

        Reference: src/storage/schema/entities/__tests/usersTests.test.ts
                  test('16_mergeExisting_updates_user_with_trx')
        """
        # Given

        user = User(
            {
                "userId": 1,
                "createdAt": datetime(2023, 1, 1),
                "updatedAt": datetime(2023, 1, 1),
                "identityKey": "oldKey",
                "activeStorage": "oldStorage",
            }
        )

        updated_ei = {
            "userId": 1,
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 2, 1),  # Newer updated_at
            "identityKey": "oldKey",
            "activeStorage": "newStorage",
        }

        mock_trx = {"transaction": "mock"}

        # Mock storage
        update_called = False

        def mock_update_user(user_id: int, data: dict[str, Any], trx: dict[str, Any] | None = None) -> None:
            nonlocal update_called
            update_called = True
            assert user_id == 1
            assert data["activeStorage"] == "newStorage"
            assert isinstance(data["updatedAt"], datetime)
            assert trx == mock_trx

        mock_storage = type("MockStorage", (), {"updateUser": mock_update_user})()

        # When
        result = user.merge_existing(mock_storage, None, updated_ei, None, mock_trx)

        # Then
        assert result is True
        assert user.active_storage == "newStorage"
        assert update_called

    def test_mergenew_always_throws_error(self) -> None:
        """Given: User instance
           When: Call merge_new
           Then: Raises error (sync chunk merge must never create new user)

        Reference: src/storage/schema/entities/__tests/usersTests.test.ts
                  test('17_mergeNew_always_throws_error')
        """
        # Given

        user = User()
        mock_storage = {}
        user_id = 123
        sync_map: dict[str, Any] = {}
        trx = None

        # When/Then
        with pytest.raises(Exception, match="a sync chunk merge must never create a new user"):
            user.merge_new(mock_storage, user_id, sync_map, trx)
