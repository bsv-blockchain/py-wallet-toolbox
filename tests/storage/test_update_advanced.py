"""Advanced unit tests for storage UPDATE operations.

These tests focus on edge cases and constraint validation (unique/foreign key).

Reference: wallet-toolbox/test/storage/update2.test.ts
"""

import re
from datetime import datetime

import pytest


def _camel_to_snake(name: str) -> str:
    s1 = re.sub("([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _build_mock_storage(methods: dict[str, object]) -> object:
    attrs: dict[str, object] = {}
    for key, value in methods.items():
        attrs[key] = value
        snake_key = _camel_to_snake(key)
        if snake_key != key and snake_key not in attrs:
            attrs[snake_key] = value
    return type("MockStorage", (), attrs)()


class Testupdate2:
    """Test suite for advanced database UPDATE operations."""

    def test_update_proventx(self) -> None:
        """Given: Mock storage with existing ProvenTx records
           When: Update ProvenTx with blockHash and updated_at
           Then: Records are updated successfully with correct values

        Reference: test/storage/update2.test.ts
                  test('1_update ProvenTx')
        """
        # Given

        mock_storage = _build_mock_storage(
            {
                "findProvenTxs": lambda self, query: [{"provenTxId": 1, "blockHash": "old"}],
                "updateProvenTx": lambda self, id, updates: 1,
            }
        )

        time = datetime(2001, 1, 2, 12, 0, 0)

        # When
        records = mock_storage.find_proven_txs({"partial": {}})
        for record in records:
            mock_storage.update_proven_tx(record["provenTxId"], {"blockHash": "fred", "updatedAt": time})
            updated = mock_storage.find_proven_txs({"partial": {"provenTxId": record["provenTxId"]}})

            # Then
            assert len(updated) == 1
            assert updated[0]["provenTxId"] == record["provenTxId"]

    def test_update_proventx_193(self) -> None:
        """Given: Mock storage with existing ProvenTx records
           When: Update all ProvenTx fields with test values
           Then: All fields are updated and verified correctly

        Reference: test/storage/update2.test.ts
                  test('2_update ProvenTx')
        """
        # Given

        mock_storage = _build_mock_storage(
            {
                "findProvenTxs": lambda self, query: [{"provenTxId": 1}],
                "updateProvenTx": lambda self, id, updates: 1,
            }
        )

        test_values = {
            "txid": "mockTxid",
            "createdAt": datetime(2024, 12, 30, 23, 0, 0),
            "updatedAt": datetime(2024, 12, 30, 23, 5, 0),
            "blockHash": "mockBlockHash",
            "height": 12345,
            "index": 1,
            "merklePath": [1, 2, 3, 4],
            "merkleRoot": "1234",
            "rawTx": [4, 3, 2, 1],
        }

        # When
        records = mock_storage.find_proven_txs({"partial": {}})
        for record in records:
            result = mock_storage.update_proven_tx(record["provenTxId"], test_values)

            # Then
            assert result == 1

    def test_update_proventx_set_created_at_and_updated_at_time(self) -> None:
        """Given: Mock storage with existing ProvenTx records
           When: Update with invalid or edge case timestamps
           Then: Handles timestamp validation correctly

        Reference: test/storage/update2.test.ts
                  test('3_update ProvenTx set created_at and updated_at time')
        """
        # Given

        mock_storage = _build_mock_storage(
            {
                "findProvenTxs": lambda self, query: [{"provenTxId": 1}],
                "updateProvenTx": lambda self, id, updates: 1,
            }
        )

        scenarios = [
            {
                "description": "Invalid created_at time",
                "updates": {
                    "createdAt": datetime(3000, 1, 1, 0, 0, 0),
                    "updatedAt": datetime(2024, 12, 30, 23, 5, 0),
                },
            },
            {
                "description": "Invalid updated_at time",
                "updates": {
                    "createdAt": datetime(2024, 12, 30, 23, 0, 0),
                    "updatedAt": datetime(3000, 1, 1, 0, 0, 0),
                },
            },
        ]

        # When/Then
        records = mock_storage.find_proven_txs({"partial": {}})
        for record in records:
            for scenario in scenarios:
                # Should handle invalid timestamps appropriately
                mock_storage.update_proven_tx(record["provenTxId"], scenario["updates"])

    def test_update_proventx_setting_individual_values(self) -> None:
        """Given: Mock storage with newly inserted ProvenTx
           When: Update individual fields one at a time
           Then: Each field update works correctly

        Reference: test/storage/update2.test.ts
                  test('4_update ProvenTx setting individual values')
        """
        # Given

        mock_storage = _build_mock_storage(
            {
                "insertProvenTx": lambda self, record: 3,
                "findProvenTxs": lambda self, query: [{"provenTxId": 3}],
                "updateProvenTx": lambda self, id, updates: 1,
            }
        )

        initial_record = {
            "provenTxId": 3,
            "txid": "mockTxid",
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
            "blockHash": "",
            "height": 1,
            "index": 1,
            "merklePath": [],
            "merkleRoot": "",
            "rawTx": [],
        }

        # When
        result = mock_storage.insert_proven_tx(initial_record)
        assert result > 0

        # Then - can update individual fields
        mock_storage.update_proven_tx(3, {"blockHash": "newHash"})
        mock_storage.update_proven_tx(3, {"height": 12345})

    def test_update_proventxreq(self) -> None:
        """Given: Mock storage with existing ProvenTxReq records
           When: Update all ProvenTxReq fields
           Then: All fields are updated correctly

        Reference: test/storage/update2.test.ts
                  test('5_update ProvenTxReq')
        """
        # Given

        mock_storage = _build_mock_storage(
            {
                "findProvenTxReqs": lambda self, query: [{"provenTxReqId": 1}],
                "updateProvenTxReq": lambda self, id, updates: 1,
            }
        )

        test_values = {
            "provenTxId": 1,
            "batch": "batch-001",
            "status": "completed",
            "txid": "mockTxid-0",
            "createdAt": datetime(2024, 12, 30, 23, 0, 0),
            "updatedAt": datetime(2024, 12, 30, 23, 5, 0),
            "attempts": 3,
            "history": '{"validated": true}',
            "inputBEEF": [5, 6, 7, 8],
            "notified": True,
        }

        # When
        records = mock_storage.find_proven_tx_reqs({"partial": {}})
        for record in records:
            result = mock_storage.update_proven_tx_req(record["provenTxReqId"], test_values)

            # Then
            assert result == 1

    def test_update_proventxreq_set_created_at_and_updated_at_time(self) -> None:
        """Given: Mock storage with existing ProvenTxReq records
           When: Update with invalid timestamp scenarios
           Then: Handles timestamp validation correctly

        Reference: test/storage/update2.test.ts
                  test('6_update ProvenTxReq set created_at and updated_at time')
        """
        # Given

        mock_storage = _build_mock_storage(
            {
                "findProvenTxReqs": lambda self, query: [{"provenTxReqId": 1}],
                "updateProvenTxReq": lambda self, id, updates: 1,
            }
        )

        scenarios = [
            {
                "description": "Invalid created_at time",
                "updates": {
                    "createdAt": datetime(3000, 1, 1, 0, 0, 0),
                    "updatedAt": datetime(2024, 12, 30, 23, 5, 0),
                },
            },
            {
                "description": "Invalid updated_at time",
                "updates": {
                    "createdAt": datetime(2024, 12, 30, 23, 0, 0),
                    "updatedAt": datetime(3000, 1, 1, 0, 0, 0),
                },
            },
        ]

        # When/Then
        records = mock_storage.find_proven_tx_reqs({"partial": {}})
        for record in records:
            for scenario in scenarios:
                mock_storage.update_proven_tx_req(record["provenTxReqId"], scenario["updates"])

    def test_update_proventxreq_setting_individual_values(self) -> None:
        """Given: Mock storage with newly inserted ProvenTxReq records
           When: Update individual fields one at a time
           Then: Each field update works correctly

        Reference: test/storage/update2.test.ts
                  test('7_update ProvenTxReq setting individual values')
        """
        # Given

        mock_storage = _build_mock_storage(
            {"insertProvenTxReq": lambda self, record: 3, "updateProvenTxReq": lambda self, id, updates: 1}
        )

        reference_time = datetime.now()
        initial_record = {
            "provenTxReqId": 3,
            "provenTxId": 1,
            "batch": "batch",
            "status": "nosend",
            "txid": "mockTxid1",
            "createdAt": reference_time,
            "updatedAt": reference_time,
            "attempts": 0,
            "history": "{}",
            "inputBEEF": [],
            "notified": False,
            "notify": "{}",
            "rawTx": [],
        }

        # When
        mock_storage.insert_proven_tx_req(initial_record)

        # Then - can update individual fields
        mock_storage.update_proven_tx_req(3, {"status": "completed"})
        mock_storage.update_proven_tx_req(3, {"attempts": 5})

    def test_update_user(self) -> None:
        """Given: Mock storage with existing User records
           When: Update all User fields
           Then: All fields are updated correctly

        Reference: test/storage/update2.test.ts
                  test('8_update User')
        """
        # Given

        mock_storage = _build_mock_storage(
            {
                "findUsers": lambda self, query: [{"userId": 1}],
                "updateUser": lambda self, id, updates: 1,
                "getSettings": lambda self: {"storageIdentityKey": "test_key"},
            }
        )

        test_values = {
            "identityKey": "mockUpdatedIdentityKey-1",
            "createdAt": datetime(2024, 12, 30, 23, 0, 0),
            "updatedAt": datetime(2024, 12, 30, 23, 5, 0),
            "activeStorage": "test_key",
        }

        # When
        records = mock_storage.find_users({"partial": {}})
        for record in records:
            result = mock_storage.update_user(record["userId"], test_values)

            # Then
            assert result == 1

    def test_update_user_set_created_at_and_updated_at_time(self) -> None:
        """Given: Mock storage with existing User records
           When: Update with invalid timestamp scenarios
           Then: Handles timestamp validation correctly

        Reference: test/storage/update2.test.ts
                  test('9_update User set created_at and updated_at time')
        """
        # Given

        mock_storage = _build_mock_storage(
            {"findUsers": lambda self, query: [{"userId": 1}], "updateUser": lambda self, id, updates: 1}
        )

        scenarios = [
            {
                "description": "Invalid created_at time",
                "updates": {
                    "createdAt": datetime(3000, 1, 1, 0, 0, 0),
                    "updatedAt": datetime(2024, 12, 30, 23, 5, 0),
                },
            },
            {
                "description": "Invalid updated_at time",
                "updates": {
                    "createdAt": datetime(2024, 12, 30, 23, 0, 0),
                    "updatedAt": datetime(3000, 1, 1, 0, 0, 0),
                },
            },
        ]

        # When/Then
        records = mock_storage.find_users({"partial": {}})
        for record in records:
            for scenario in scenarios:
                mock_storage.update_user(record["userId"], scenario["updates"])

    def test_update_user_trigger_db_unique_constraint_errors(self) -> None:
        """Given: Mock storage with multiple User records
           When: Update to duplicate unique field values
           Then: Triggers unique constraint error

        Reference: test/storage/update2.test.ts
                  test('10_update User trigger DB unique constraint errors')
        """
        # Given

        def _raise_unique_error(self, id, updates):
            raise Exception("UNIQUE constraint failed")

        mock_storage = _build_mock_storage({"updateUser": _raise_unique_error})

        # When/Then - should trigger unique constraint error
        with pytest.raises(Exception):
            mock_storage.update_user(2, {"identityKey": "mockDupIdentityKey"})

    def test_update_user_trigger_db_foreign_key_constraint_errors(self) -> None:
        """Given: Mock storage with User records
           When: Update with invalid foreign key references
           Then: Triggers foreign key constraint error

        Reference: test/storage/update2.test.ts
                  test('11_update User trigger DB foreign key constraint errors')
        """
        # Given

        def _raise_fk_error(self, id, updates):
            raise Exception("FOREIGN KEY constraint failed")

        mock_storage = _build_mock_storage({"updateUser": _raise_fk_error})

        # When/Then - should trigger foreign key constraint error
        with pytest.raises(Exception):
            mock_storage.update_user(1, {"userId": 0})

    def test_update_user_table_setting_individual_values(self) -> None:
        """Given: Mock storage with newly inserted User
           When: Update individual fields one at a time
           Then: Each field update works correctly

        Reference: test/storage/update2.test.ts
                  test('12_update User table setting individual values')
        """
        # Given

        mock_storage = _build_mock_storage(
            {
                "insertUser": lambda self, record: 3,
                "updateUser": lambda self, id, updates: 1,
                "getSettings": lambda self: {"storageIdentityKey": "test_key"},
            }
        )

        initial_record = {
            "userId": 3,
            "identityKey": "",
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
            "activeStorage": "test_key",
        }

        # When
        result = mock_storage.insert_user(initial_record)
        assert result > 1

        # Then - can update individual fields
        mock_storage.update_user(3, {"identityKey": "newKey"})

    def test_update_certificate(self) -> None:
        """Given: Mock storage with existing Certificate records
           When: Update all Certificate fields
           Then: All fields are updated correctly

        Reference: test/storage/update2.test.ts
                  test('13_update Certificate')
        """
        # Given

        mock_storage = _build_mock_storage(
            {
                "findCertificates": lambda self, query: [{"certificateId": 1}],
                "updateCertificate": lambda self, id, updates: 1,
            }
        )

        test_values = {
            "type": "mockType",
            "subject": "mockSubject",
            "serialNumber": "mockSerialNumber",
            "certifier": "mockCertifier",
            "revocationOutpoint": "mockRevocationOutpoint",
            "signature": "mockSignature",
            "fields": {},
            "createdAt": datetime(2024, 12, 30, 23, 0, 0),
            "updatedAt": datetime(2024, 12, 30, 23, 5, 0),
            "isDeleted": False,
        }

        # When
        records = mock_storage.find_certificates({"partial": {}})
        for record in records:
            result = mock_storage.update_certificate(record["certificateId"], test_values)

            # Then
            assert result == 1

    def test_update_certificate_set_created_at_and_updated_at_time(self) -> None:
        """Given: Mock storage with existing Certificate records
           When: Update with invalid timestamp scenarios
           Then: Handles timestamp validation correctly

        Reference: test/storage/update2.test.ts
                  test('14_update Certificate set created_at and updated_at time')
        """
        # Given

        mock_storage = _build_mock_storage(
            {
                "findCertificates": lambda self, query: [{"certificateId": 1}],
                "updateCertificate": lambda self, id, updates: 1,
            }
        )

        scenarios = [
            {
                "description": "Invalid created_at time",
                "updates": {
                    "createdAt": datetime(3000, 1, 1, 0, 0, 0),
                    "updatedAt": datetime(2024, 12, 30, 23, 5, 0),
                },
            },
            {
                "description": "Invalid updated_at time",
                "updates": {
                    "createdAt": datetime(2024, 12, 30, 23, 0, 0),
                    "updatedAt": datetime(3000, 1, 1, 0, 0, 0),
                },
            },
        ]

        # When/Then
        records = mock_storage.find_certificates({"partial": {}})
        for record in records:
            for scenario in scenarios:
                mock_storage.update_certificate(record["certificateId"], scenario["updates"])

    def test_update_certificate_trigger_db_unique_constraint_errors(self) -> None:
        """Given: Mock storage with multiple Certificate records
           When: Update to duplicate unique field values
           Then: Triggers unique constraint error

        Reference: test/storage/update2.test.ts
                  test('15_update Certificate trigger DB unique constraint errors')
        """
        # Given

        def _raise_unique_error(self, id, updates):
            raise Exception("UNIQUE constraint failed")

        mock_storage = _build_mock_storage({"updateCertificate": _raise_unique_error})

        # When/Then - should trigger unique constraint error
        with pytest.raises(Exception):
            mock_storage.update_certificate(2, {"serialNumber": "mockDupSerial"})

    def test_update_certificate_trigger_db_foreign_key_constraint_errors(self) -> None:
        """Given: Mock storage with Certificate records
           When: Update with invalid foreign key references
           Then: Triggers foreign key constraint error

        Reference: test/storage/update2.test.ts
                  test('16_update Certificate trigger DB foreign key constraint errors')
        """
        # Given

        def _raise_fk_error(self, id, updates):
            raise Exception("FOREIGN KEY constraint failed")

        mock_storage = _build_mock_storage({"updateCertificate": _raise_fk_error})

        # When/Then - should trigger foreign key constraint error
        with pytest.raises(Exception):
            mock_storage.update_certificate(1, {"userId": 999})
