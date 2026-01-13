"""Unit tests for CertificateField entity.

Reference: wallet-toolbox/src/storage/schema/entities/__tests/CertificateFieldTests.test.ts
"""

from datetime import datetime

import pytest

from bsv_wallet_toolbox.storage.entities import CertificateField


class TestCertificateFieldEntity:
    """Test suite for CertificateField entity."""

    def test_equals_identifies_matching_certificatefield_entities(self) -> None:
        """Given: Two CertificateField entities with identical data
           When: Call equals method with and without syncMap
           Then: Returns True in both cases

        Reference: src/storage/schema/entities/__tests/CertificateFieldTests.test.ts
                  test('0_equals identifies matching CertificateField entities')
        """
        # Given

        now = datetime.now()
        certificate_id = 300
        initial_data = {
            "certificateId": certificate_id,
            "createdAt": now,
            "updatedAt": now,
            "userId": 1,
            "fieldName": "field1",
            "fieldValue": "value1",
            "masterKey": "masterKey1",
        }

        entity1 = CertificateField(initial_data)
        entity2 = CertificateField(initial_data)

        sync_map = {"certificate": {"idMap": {certificate_id: certificate_id}}}

        # When/Then
        assert entity1.equals(entity2.to_api()) is True
        assert entity1.equals(entity2.to_api(), sync_map) is True

    def test_equals_identifies_non_matching_certificatefield_entities(self) -> None:
        """Given: Two CertificateField entities with different data
           When: Call equals method with and without syncMap
           Then: Returns False for mismatched fields

        Reference: src/storage/schema/entities/__tests/CertificateFieldTests.test.ts
                  test('1_equals identifies non-matching CertificateField entities')
        """
        # Given

        now = datetime.now()
        certificate_id1 = 301
        certificate_id2 = 302

        initial_data = {
            "certificateId": certificate_id1,
            "createdAt": now,
            "updatedAt": now,
            "userId": 1,
            "fieldName": "field1",
            "fieldValue": "value1",
            "masterKey": "masterKey1",
        }

        entity1 = CertificateField(initial_data)

        # Test each mismatched field
        mismatched_entities = [
            {"certificateId": certificate_id2},
            {"fieldName": "field2"},
            {"fieldValue": "value2"},
            {"masterKey": "masterKey2"},
        ]

        for mismatch in mismatched_entities:
            mismatched_entity = CertificateField({**initial_data, **mismatch})

            # When/Then
            assert entity1.equals(mismatched_entity.to_api()) is False

            # Test with SyncMap
            sync_map = {"certificate": {"idMap": {certificate_id1: certificate_id1, certificate_id2: certificate_id2}}}
            assert entity1.equals(mismatched_entity.to_api(), sync_map) is False

    def test_mergeexisting_updates_entity_and_database_when_ei_updated_at_greater_than_this_updated_at(
        self,
    ) -> None:
        """Given: CertificateField entity with older updated_at
           When: Call merge_existing with newer updated_at
           Then: Entity and database are updated

        Reference: src/storage/schema/entities/__tests/CertificateFieldTests.test.ts
                  test('mergeExisting updates entity and database when ei.updated_at > this.updated_at')
        """
        # Given

        now = datetime.now()
        certificate_id = 400
        initial_data = {
            "certificateId": certificate_id,
            "createdAt": now,
            "updatedAt": now,
            "userId": 1,
            "fieldName": "field1",
            "fieldValue": "value1",
            "masterKey": "masterKey1",
        }

        entity = CertificateField(initial_data)

        # Updated data with later timestamp
        updated_data = {
            **initial_data,
            "updatedAt": datetime.fromtimestamp(now.timestamp() + 1),
            "fieldValue": "updatedValue",
            "masterKey": "updatedMasterKey",
        }

        sync_map = {"certificate": {"idMap": {certificate_id: certificate_id}}}
        mock_storage = type("MockStorage", (), {})()

        # When
        was_merged = entity.merge_existing(mock_storage, None, updated_data, sync_map, None)

        # Then
        assert was_merged is True
        assert entity.field_value == "updatedValue"
        assert entity.master_key == "updatedMasterKey"

    def test_mergeexisting_does_not_update_entity_when_ei_updated_at_less_than_or_equal_this_updated_at(
        self,
    ) -> None:
        """Given: CertificateField entity with same or newer updated_at
           When: Call merge_existing with same or older updated_at
           Then: Entity is not updated

        Reference: src/storage/schema/entities/__tests/CertificateFieldTests.test.ts
                  test('mergeExisting does not update entity when ei.updated_at <= this.updated_at')
        """
        # Given

        now = datetime.now()
        certificate_id = 401
        initial_data = {
            "certificateId": certificate_id,
            "createdAt": now,
            "updatedAt": now,
            "userId": 1,
            "fieldName": "field1",
            "fieldValue": "value1",
            "masterKey": "masterKey1",
        }

        entity = CertificateField(initial_data)

        # Same updated_at
        same_updated_data = {
            **initial_data,
            "updatedAt": now,
            "fieldValue": "unchangedValue",
            "masterKey": "unchangedMasterKey",
        }

        sync_map = {"certificate": {"idMap": {certificate_id: certificate_id}}}
        mock_storage = type("MockStorage", (), {})()

        # When
        was_merged = entity.merge_existing(mock_storage, None, same_updated_data, sync_map, None)

        # Then
        assert was_merged is False
        assert entity.field_value == "value1"
        assert entity.master_key == "masterKey1"

    def test_certificatefield_getters_and_setters(self) -> None:
        """Given: CertificateField entity with initial data
           When: Get and set all properties
           Then: Getters and setters work correctly

        Reference: src/storage/schema/entities/__tests/CertificateFieldTests.test.ts
                  test('CertificateField getters and setters')
        """
        # Given

        now = datetime.now()
        initial_data = {
            "userId": 1,
            "certificateId": 500,
            "createdAt": now,
            "updatedAt": now,
            "fieldName": "fieldName1",
            "fieldValue": "fieldValue1",
            "masterKey": "masterKey1",
        }

        entity = CertificateField(initial_data)

        # Validate getters
        assert entity.user_id == 1
        assert entity.certificate_id == 500
        assert entity.created_at == now
        assert entity.updated_at == now
        assert entity.field_name == "fieldName1"
        assert entity.field_value == "fieldValue1"
        assert entity.master_key == "masterKey1"

        # Validate overridden properties
        with pytest.raises(Exception, match='entity has no "id" value'):
            _ = entity.id
        assert entity.entity_name == "certificateField"
        assert entity.entity_table == "certificate_fields"

        # Validate setters
        new_date = datetime.fromtimestamp(now.timestamp() + 1)
        entity.user_id = 2
        entity.certificate_id = 600
        entity.created_at = datetime(2025, 1, 1)
        entity.updated_at = new_date
        entity.field_name = "updatedFieldName"
        entity.field_value = "updatedFieldValue"
        entity.master_key = "updatedMasterKey"

        # Validate updated values
        assert entity.user_id == 2
        assert entity.certificate_id == 600
        assert entity.created_at == datetime(2025, 1, 1)
        assert entity.updated_at == new_date
        assert entity.field_name == "updatedFieldName"
        assert entity.field_value == "updatedFieldValue"
        assert entity.master_key == "updatedMasterKey"
