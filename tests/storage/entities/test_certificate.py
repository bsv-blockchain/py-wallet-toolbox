"""Unit tests for Certificate entity.

Reference: wallet-toolbox/src/storage/schema/entities/__tests/CertificateTests.test.ts
"""

from datetime import datetime

from bsv_wallet_toolbox.storage.entities import Certificate


class TestCertificateEntity:
    """Test suite for Certificate entity."""

    def test_equals_identifies_matching_certificate_entities(self) -> None:
        """Given: Two Certificate entities with identical data
           When: Call equals method
           Then: Returns True

        Reference: src/storage/schema/entities/__tests/CertificateTests.test.ts
                  test('0_equals identifies matching Certificate entities')
        """
        # Given

        now = datetime.now()
        certificate_id = 500
        certificate_data = {
            "certificateId": certificate_id,
            "createdAt": now,
            "updatedAt": now,
            "userId": 1,
            "type": "exampleType",
            "serialNumber": "serial123",
            "certifier": "02c123eabcdeff1234567890abcdef1234567890abcdef1234567890abcdef1234",
            "subject": "02c123eabcdeff1234567890abcdef1234567890abcdef1234567890abcdef5678",
            "revocationOutpoint": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890:0",
            "signature": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "isDeleted": False,
        }

        entity1 = Certificate(certificate_data)
        entity2 = Certificate(certificate_data)

        # When/Then
        assert entity1.equals(entity2.to_api()) is True

    def test_equals_identifies_non_matching_certificate_entities(self) -> None:
        """Given: Two Certificate entities with different data
           When: Call equals method
           Then: Returns False for each mismatched field

        Reference: src/storage/schema/entities/__tests/CertificateTests.test.ts
                  test('1_equals identifies non-matching Certificate entities')
        """
        # Given

        now = datetime.now()
        certificate_data1 = {
            "certificateId": 501,
            "createdAt": now,
            "updatedAt": now,
            "userId": 1,
            "type": "exampleType1",
            "serialNumber": "serial123-1",
            "certifier": "02c123eabcdeff1234567890abcdef1234567890abcdef1234567890abcdef1234",
            "subject": "02c123eabcdeff1234567890abcdef1234567890abcdef1234567890abcdef5678",
            "revocationOutpoint": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890:0",
            "signature": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "isDeleted": False,
        }

        entity1 = Certificate(certificate_data1)

        # Test each mismatched field
        mismatched_entities = [
            {"type": "differentType"},
            {"subject": "differentSubject"},
            {"serialNumber": "differentSerialNumber"},
            {"revocationOutpoint": "differentOutpoint:0"},
            {"signature": "differentSignature"},
            {"verifier": "differentVerifier"},
            {"isDeleted": not certificate_data1["isDeleted"]},
        ]

        for mismatch in mismatched_entities:
            mismatched_entity = Certificate({**certificate_data1, **mismatch})
            # When/Then
            assert entity1.equals(mismatched_entity.to_api()) is False

    def test_mergeexisting_updates_entity_and_database_when_ei_updated_at_greater_than_this_updated_at(
        self,
    ) -> None:
        """Given: Certificate entity with older updated_at
           When: Call merge_existing with newer updated_at
           Then: Entity and database are updated

        Reference: src/storage/schema/entities/__tests/CertificateTests.test.ts
                  test('2_mergeExisting updates entity and database when ei.updated_at > this.updated_at')
        """
        # Given

        now = datetime.now()
        certificate_id = 600
        certificate_data = {
            "certificateId": certificate_id,
            "createdAt": now,
            "updatedAt": now,
            "userId": 1,
            "type": "exampleTypeMerge",
            "serialNumber": "serialMerge123",
            "certifier": "02c123eabcdeff1234567890abcdef1234567890abcdef1234567890abcdef1234",
            "subject": "02c123eabcdeff1234567890abcdef1234567890abcdef1234567890abcdef5678",
            "revocationOutpoint": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890:0",
            "signature": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "isDeleted": False,
        }

        entity = Certificate(certificate_data)

        # Updated data with later timestamp
        updated_data = {
            **certificate_data,
            "updatedAt": datetime.fromtimestamp(now.timestamp() + 1),
            "type": "updatedType",
            "subject": "updatedSubject",
            "serialNumber": "updatedSerialNumber",
            "revocationOutpoint": "updatedOutpoint:1",
            "signature": "updatedSignature",
            "verifier": "updatedVerifier",
            "isDeleted": True,
        }

        sync_map = {"certificate": {"idMap": {certificate_id: certificate_id}}}
        mock_storage = type("MockStorage", (), {})()

        # When
        was_merged = entity.merge_existing(mock_storage, None, updated_data, sync_map, None)

        # Then
        assert was_merged is True
        assert entity.type == "updatedType"
        assert entity.subject == "updatedSubject"
        assert entity.serial_number == "updatedSerialNumber"
        assert entity.revocation_outpoint == "updatedOutpoint:1"
        assert entity.signature == "updatedSignature"
        assert entity.verifier == "updatedVerifier"
        assert entity.is_deleted == 1

    def test_mergeexisting_does_not_update_entity_when_ei_updated_at_less_than_or_equal_this_updated_at(
        self,
    ) -> None:
        """Given: Certificate entity with same or newer updated_at
           When: Call merge_existing with same or older updated_at
           Then: Entity is not updated

        Reference: src/storage/schema/entities/__tests/CertificateTests.test.ts
                  test('3_mergeExisting does not update entity when ei.updated_at <= this.updated_at')
        """
        # Given

        now = datetime.now()
        certificate_id = 601
        certificate_data = {
            "certificateId": certificate_id,
            "createdAt": now,
            "updatedAt": now,
            "userId": 1,
            "type": "exampleType",
            "serialNumber": "exampleSerialNumber",
            "certifier": "02c123eabcdeff1234567890abcdef1234567890abcdef1234567890abcdef1234",
            "subject": "02c123eabcdeff1234567890abcdef1234567890abcdef1234567890abcdef5678",
            "revocationOutpoint": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890:0",
            "signature": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "isDeleted": False,
        }

        entity = Certificate(certificate_data)

        # Same updated_at
        same_updated_data = {
            **certificate_data,
            "updatedAt": now,
            "type": "unchangedType",
            "subject": "unchangedSubject",
        }

        sync_map = {"certificate": {"idMap": {certificate_id: certificate_id}}}
        mock_storage = type("MockStorage", (), {})()

        # When
        was_merged = entity.merge_existing(mock_storage, None, same_updated_data, sync_map, None)

        # Then
        assert was_merged is False
        assert entity.type == "exampleType"
        assert entity.subject == "02c123eabcdeff1234567890abcdef1234567890abcdef1234567890abcdef5678"

    def test_certificate_class_getters_and_setters(self) -> None:
        """Given: Certificate entity with initial data
           When: Get and set all properties
           Then: Getters and setters work correctly

        Reference: src/storage/schema/entities/__tests/CertificateTests.test.ts
                  test('4_Certificate class getters and setters')
        """
        # Given

        now = datetime.now()
        initial_data = {
            "certificateId": 701,
            "createdAt": now,
            "updatedAt": now,
            "userId": 1,
            "type": "initialType",
            "subject": "initialSubject",
            "verifier": "initialVerifier",
            "serialNumber": "initialSerialNumber",
            "certifier": "initialCertifier",
            "revocationOutpoint": "initialOutpoint:0",
            "signature": "initialSignature",
            "isDeleted": False,
        }

        entity = Certificate(initial_data)

        # Validate getters
        assert entity.certificate_id == 701
        assert entity.created_at == now
        assert entity.updated_at == now
        assert entity.user_id == 1
        assert entity.type == "initialType"
        assert entity.subject == "initialSubject"
        assert entity.verifier == "initialVerifier"
        assert entity.serial_number == "initialSerialNumber"
        assert entity.certifier == "initialCertifier"
        assert entity.revocation_outpoint == "initialOutpoint:0"
        assert entity.signature == "initialSignature"
        assert not entity.is_deleted
        assert entity.id == 701
        assert entity.entity_name == "certificate"
        assert entity.entity_table == "certificates"

        # Validate setters
        entity.certificate_id = 800
        entity.created_at = datetime(2025, 1, 1)
        entity.updated_at = datetime(2025, 1, 2)
        entity.user_id = 2
        entity.type = "updatedType"
        entity.subject = "updatedSubject"
        entity.verifier = "updatedVerifier"
        entity.serial_number = "updatedSerialNumber"
        entity.certifier = "updatedCertifier"
        entity.revocation_outpoint = "updatedOutpoint:1"
        entity.signature = "updatedSignature"
        entity.is_deleted = True
        entity.id = 900

        # Validate updated values
        assert entity.certificate_id == 900
        assert entity.created_at == datetime(2025, 1, 1)
        assert entity.updated_at == datetime(2025, 1, 2)
        assert entity.user_id == 2
        assert entity.type == "updatedType"
        assert entity.subject == "updatedSubject"
        assert entity.verifier == "updatedVerifier"
        assert entity.serial_number == "updatedSerialNumber"
        assert entity.certifier == "updatedCertifier"
        assert entity.revocation_outpoint == "updatedOutpoint:1"
        assert entity.signature == "updatedSignature"
        assert entity.is_deleted is True
        assert entity.id == 900
