"""Unit tests for ProvenTx entity.

Reference: wallet-toolbox/src/storage/schema/entities/__tests/ProvenTxTests.test.ts
"""

from datetime import datetime
from typing import Any

from bsv_wallet_toolbox.storage.entities import ProvenTx


class TestProvenTxEntity:
    """Test suite for ProvenTx entity."""

    def test_fromtxid_valid_txid_with_rawtx_and_merkle_proof_real_database(self) -> None:
        """Given: Valid txid with rawTx and Merkle proof in database
           When: Call from_txid with services
           Then: Returns ProvenTx with valid data

        Reference: src/storage/schema/entities/__tests/ProvenTxTests.test.ts
                  test('0_fromTxid: valid txid with rawTx and Merkle proof (real database)')
        """
        # Given

        txid = "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122"
        height = 123
        block_hash = "mock-block-hash"
        merkle_root = "mock-merkle-root"
        merkle_path_binary = [0x01, 0x02, 0x03]
        raw_tx = [0x04, 0x05, 0x06]

        # Mock services
        def mock_get_raw_tx(requested_txid: str) -> dict[str, Any]:
            if requested_txid == txid:
                return {"txid": requested_txid, "rawTx": raw_tx}
            raise Exception("Unexpected txid")

        def mock_get_merkle_path(requested_txid: str) -> dict[str, Any]:
            if requested_txid == txid:
                return {
                    "merklePath": {
                        "path": [[{"hash": txid, "offset": 0}]],
                        "blockHeight": height,
                        "toBinary": lambda: merkle_path_binary,
                    },
                    "header": {"height": height, "hash": block_hash, "merkleRoot": merkle_root},
                }
            raise Exception("Unexpected txid")

        mock_services = type(
            "MockServices",
            (),
            {
                "getRawTx": staticmethod(mock_get_raw_tx),
                "getMerklePath": staticmethod(mock_get_merkle_path),
            },
        )()

        # When
        result = ProvenTx.from_txid(txid, mock_services)

        # Then
        assert result["proven"] is not None
        assert result["proven"].txid == txid
        assert result["proven"].height == height
        assert result["proven"].block_hash == block_hash
        assert result["proven"].merkle_root == merkle_root
        assert result["rawTx"] == raw_tx

    def test_fromtxid_txid_with_no_rawtx_available(self) -> None:
        """Given: Txid with no rawTx available
           When: Call from_txid
           Then: Returns result with undefined proven and rawTx

        Reference: src/storage/schema/entities/__tests/ProvenTxTests.test.ts
                  test('1_fromTxid: txid with no rawTx available')
        """
        # Given

        txid = "missing-txid"

        # Mock services that return nothing
        def mock_get_raw_tx(requested_txid: str) -> None:
            return None

        mock_services = type("MockServices", (), {"getRawTx": mock_get_raw_tx})()

        # When
        result = ProvenTx.from_txid(txid, mock_services)

        # Then
        assert result["proven"] is None
        assert result["rawTx"] is None

    def test_fromtxid_txid_with_no_merkle_proof_available(self) -> None:
        """Given: Txid with rawTx but no Merkle proof
           When: Call from_txid
           Then: Returns result with rawTx but undefined proven

        Reference: src/storage/schema/entities/__tests/ProvenTxTests.test.ts
                  test('2_fromTxid: txid with no Merkle proof available')
        """
        # Given

        txid = "no-merkle-proof-txid"
        raw_tx = [0x01, 0x02, 0x03]

        # Mock services
        def mock_get_raw_tx(requested_txid: str) -> dict[str, Any]:
            return {"txid": requested_txid, "rawTx": raw_tx}

        def mock_get_merkle_path(requested_txid: str) -> None:
            return None

        mock_services = type(
            "MockServices",
            (),
            {
                "getRawTx": staticmethod(mock_get_raw_tx),
                "getMerklePath": staticmethod(mock_get_merkle_path),
            },
        )()

        # When
        result = ProvenTx.from_txid(txid, mock_services)

        # Then
        assert result["proven"] is None
        assert result["rawTx"] == raw_tx

    def test_proventx_getters_and_setters(self) -> None:
        """Given: ProvenTx instance with mock data
           When: Set and get all properties
           Then: Getters and setters work correctly

        Reference: src/storage/schema/entities/__tests/ProvenTxTests.test.ts
                  test('3_ProvenTx getters and setters')
        """
        # Given

        mock_data = {
            "provenTxId": 1,
            "createdAt": datetime(2025, 1, 1),
            "updatedAt": datetime(2025, 1, 2),
            "txid": "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122",
            "height": 123,
            "index": 0,
            "merklePath": [0x04, 0x05, 0x06],
            "rawTx": [0x01, 0x02, 0x03],
            "blockHash": "mock-block-hash",
            "merkleRoot": "mock-merkle-root",
        }

        proven_tx = ProvenTx(mock_data)

        # Validate getters
        assert proven_tx.proven_tx_id == 1
        assert proven_tx.txid == "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122"
        assert proven_tx.height == 123
        assert proven_tx.index == 0
        assert proven_tx.merkle_path == [0x04, 0x05, 0x06]
        assert proven_tx.raw_tx == [0x01, 0x02, 0x03]
        assert proven_tx.block_hash == "mock-block-hash"
        assert proven_tx.merkle_root == "mock-merkle-root"

        # Validate setters
        proven_tx.proven_tx_id = 2
        proven_tx.created_at = datetime(2025, 2, 1)
        proven_tx.updated_at = datetime(2025, 2, 2)
        proven_tx.txid = "a3b2f0935c7b5bb7a841a09e535c13be86f4df0e7a91cebdc33812bfcc0eb9d7"
        proven_tx.height = 456
        proven_tx.index = 1
        proven_tx.merkle_path = [0x07, 0x08, 0x09]
        proven_tx.raw_tx = [0x0A, 0x0B, 0x0C]
        proven_tx.block_hash = "new-block-hash"
        proven_tx.merkle_root = "new-merkle-root"

        # Validate updated values
        assert proven_tx.proven_tx_id == 2
        assert proven_tx.txid == "a3b2f0935c7b5bb7a841a09e535c13be86f4df0e7a91cebdc33812bfcc0eb9d7"
        assert proven_tx.height == 456

        # Validate overridden methods
        assert proven_tx.id == 2
        assert proven_tx.entity_name == "provenTx"
        assert proven_tx.entity_table == "proven_txs"

        # Update id via overridden setter
        proven_tx.id = 3
        assert proven_tx.proven_tx_id == 3

    def test_equals_identifies_matching_proventx_entities(self) -> None:
        """Given: Two ProvenTx entities with matching data
           When: Call equals method with syncMap
           Then: Returns True

        Reference: src/storage/schema/entities/__tests/ProvenTxTests.test.ts
                  test('4_equals: identifies matching ProvenTx entities')
        """
        # Given

        proven_tx1 = ProvenTx(
            {
                "provenTxId": 401,
                "txid": "valid-txid",
                "createdAt": datetime(2023, 1, 1),
                "updatedAt": datetime(2023, 1, 2),
                "height": 1588740,
                "index": 0,
                "merklePath": [1, 2, 3],
                "rawTx": [4, 5, 6],
                "blockHash": "block-hash",
                "merkleRoot": "merkle-root",
            }
        )

        proven_tx2_api = {
            "provenTxId": 401,
            "txid": "valid-txid",
            "createdAt": datetime(2023, 1, 1),
            "updatedAt": datetime(2023, 1, 2),
            "height": 1588740,
            "index": 0,
            "merklePath": [1, 2, 3],
            "rawTx": [4, 5, 6],
            "blockHash": "block-hash",
            "merkleRoot": "merkle-root",
        }

        sync_map = {"provenTx": {"idMap": {401: 401}}}

        # When/Then
        assert proven_tx1.equals(proven_tx2_api, sync_map) is True

    def test_equals_identifies_non_matching_txid(self) -> None:
        """Given: Two ProvenTx entities with different txids
           When: Call equals method
           Then: Returns False

        Reference: src/storage/schema/entities/__tests/ProvenTxTests.test.ts
                  test('5_equals: identifies non-matching txid')
        """
        # Given

        proven_tx1 = ProvenTx({"provenTxId": 102, "txid": "txid1", "height": 1588740, "merklePath": [1, 2, 3]})

        proven_tx2_api = {"provenTxId": 103, "txid": "txid2", "height": 1588740, "merklePath": [1, 2, 3]}

        # When/Then
        assert proven_tx1.equals(proven_tx2_api) is False

    def test_equals_identifies_non_matching_height(self) -> None:
        """Given: Two ProvenTx entities with different heights
           When: Call equals method
           Then: Returns False

        Reference: src/storage/schema/entities/__tests/ProvenTxTests.test.ts
                  test('6_equals: identifies non-matching height')
        """
        # Given

        proven_tx1 = ProvenTx({"provenTxId": 104, "txid": "valid-txid", "height": 1588740, "merklePath": [1, 2, 3]})

        proven_tx2_api = {
            "provenTxId": 105,
            "txid": "valid-txid",
            "height": 1588741,  # Different height
            "merklePath": [1, 2, 3],
        }

        # When/Then
        assert proven_tx1.equals(proven_tx2_api) is False

    def test_equals_identifies_non_matching_merklepath(self) -> None:
        """Given: Two ProvenTx entities with different merklePaths
           When: Call equals method
           Then: Returns False

        Reference: src/storage/schema/entities/__tests/ProvenTxTests.test.ts
                  test('7_equals: identifies non-matching merklePath')
        """
        # Given

        proven_tx1 = ProvenTx({"provenTxId": 106, "txid": "valid-txid", "height": 1588740, "merklePath": [1, 2, 3]})

        proven_tx2_api = {
            "provenTxId": 107,
            "txid": "valid-txid",
            "height": 1588740,
            "merklePath": [1, 2, 4],  # Different merklePath
        }

        # When/Then
        assert proven_tx1.equals(proven_tx2_api) is False

    def test_equals_identifies_non_matching_syncmap(self) -> None:
        """Given: Two ProvenTx entities with mismatched syncMap
           When: Call equals method with syncMap
           Then: Returns False

        Reference: src/storage/schema/entities/__tests/ProvenTxTests.test.ts
                  test('8_equals: identifies non-matching syncMap')
        """
        # Given

        proven_tx1 = ProvenTx({"provenTxId": 108, "txid": "valid-txid", "height": 1588740, "merklePath": [1, 2, 3]})

        proven_tx2_api = {"provenTxId": 109, "txid": "valid-txid", "height": 1588740, "merklePath": [1, 2, 3]}

        sync_map = {"provenTx": {"idMap": {108: 999}}}  # Mismatched mapping

        # When/Then
        assert proven_tx1.equals(proven_tx2_api, sync_map) is False

    def test_equals_proventxid_mismatch_without_syncmap(self) -> None:
        """Given: Two ProvenTx entities with different provenTxIds, no syncMap
           When: Call equals method
           Then: Returns False

        Reference: src/storage/schema/entities/__tests/ProvenTxTests.test.ts
                  test('9_equals: provenTxId mismatch without syncMap')
        """
        # Given

        tx1 = ProvenTx(
            {
                "provenTxId": 405,
                "txid": "txid1",
                "height": 100,
                "index": 1,
                "merklePath": [1, 2, 3],
                "rawTx": [4, 5, 6],
                "blockHash": "block-hash-1",
                "merkleRoot": "merkle-root-1",
            }
        )

        tx2_api = {
            "provenTxId": 406,  # Different ID
            "txid": "txid1",
            "height": 100,
            "index": 1,
            "merklePath": [1, 2, 3],
            "rawTx": [4, 5, 6],
            "blockHash": "block-hash-1",
            "merkleRoot": "merkle-root-1",
        }

        # When/Then
        assert tx1.equals(tx2_api) is False

    def test_mergeexisting_always_returns_false(self) -> None:
        """Given: ProvenTx entity
           When: Call merge_existing
           Then: Always returns False

        Reference: src/storage/schema/entities/__tests/ProvenTxTests.test.ts
                  test('10_mergeExisting: always returns false')
        """
        # Given

        proven_tx = ProvenTx(
            {
                "provenTxId": 101,
                "txid": "txid1",
                "createdAt": datetime(2023, 1, 1),
                "updatedAt": datetime(2023, 1, 2),
                "height": 100,
                "index": 1,
                "merklePath": [1, 2, 3],
                "rawTx": [4, 5, 6],
                "blockHash": "block-hash-1",
                "merkleRoot": "merkle-root-1",
            }
        )

        sync_map = {"provenTx": {"idMap": {101: 101}}}

        mock_storage = type("MockStorage", (), {})()
        mock_trx = {}

        # When
        result = proven_tx.merge_existing(mock_storage, datetime.now(), proven_tx.to_api(), sync_map, mock_trx)

        # Then
        assert result is False
