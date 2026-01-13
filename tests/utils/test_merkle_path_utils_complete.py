"""Complete coverage tests for merkle_path_utils.

This module provides comprehensive tests for Merkle path conversion utilities.
"""

try:
    from bsv_wallet_toolbox.utils.merkle_path_utils import convert_proof_to_merkle_path

    IMPORT_SUCCESS = True
except ImportError:
    IMPORT_SUCCESS = False


class TestConvertProofBasic:
    """Test basic convert_proof_to_merkle_path functionality."""

    def test_convert_single_level_proof(self) -> None:
        """Test converting proof with single level."""
        txid = "a" * 64
        proof = {"height": 100, "index": 0, "nodes": ["b" * 64]}

        result = convert_proof_to_merkle_path(txid, proof)

        assert "blockHeight" in result
        assert result["blockHeight"] == 100
        assert "path" in result
        assert len(result["path"]) == 1

    def test_convert_multi_level_proof(self) -> None:
        """Test converting proof with multiple levels."""
        txid = "tx" * 32
        proof = {"height": 200, "index": 5, "nodes": ["node1" * 8, "node2" * 8, "node3" * 8]}

        result = convert_proof_to_merkle_path(txid, proof)

        assert result["blockHeight"] == 200
        assert len(result["path"]) == 3

    def test_convert_even_index(self) -> None:
        """Test converting proof with even index."""
        txid = "even" * 16
        proof = {"height": 150, "index": 2, "nodes": ["sibling" * 8]}  # Even

        result = convert_proof_to_merkle_path(txid, proof)

        # Even index: txid is inserted at position 0, sibling at position 1
        assert result["path"][0][0]["hash_str"] == txid
        assert result["path"][0][0]["txid"] is True
        assert result["path"][0][0]["offset"] == 2
        # Sibling at position 1 with offset index+1
        assert result["path"][0][1]["offset"] == 3

    def test_convert_odd_index(self) -> None:
        """Test converting proof with odd index."""
        txid = "odd_" * 16
        proof = {"height": 175, "index": 3, "nodes": ["sibling" * 8]}  # Odd

        result = convert_proof_to_merkle_path(txid, proof)

        assert result["path"][0][0]["offset"] == 2  # Sibling at index-1
        # Txid should be second (odd index)
        assert result["path"][0][1]["hash_str"] == txid
        assert result["path"][0][1]["txid"] is True


class TestConvertProofDuplicates:
    """Test handling of duplicate nodes."""

    def test_convert_duplicate_marker(self) -> None:
        """Test converting proof with duplicate marker (*)."""
        txid = "dup_" * 16
        proof = {"height": 100, "index": 0, "nodes": ["*"]}  # Duplicate marker

        result = convert_proof_to_merkle_path(txid, proof)

        # With even index (0), txid is at position 0, sibling at position 1
        # Sibling (position 1) should be marked as duplicate
        sibling = result["path"][0][1]
        assert sibling.get("duplicate") is True
        assert "hash" not in sibling

    def test_convert_txid_as_node_at_level_0(self) -> None:
        """Test when node at level 0 equals txid (indicates duplicate)."""
        txid = "same" * 16
        proof = {"height": 100, "index": 0, "nodes": [txid]}  # Node is same as txid at level 0

        result = convert_proof_to_merkle_path(txid, proof)

        # Should be marked as duplicate (sibling at position 1)
        sibling = result["path"][0][1]
        assert sibling.get("duplicate") is True

    def test_convert_non_duplicate_different_hash(self) -> None:
        """Test non-duplicate when hash is different."""
        txid = "txid" * 16
        proof = {"height": 100, "index": 0, "nodes": ["diff" * 16]}  # Different from txid

        result = convert_proof_to_merkle_path(txid, proof)

        # Txid at position 0 (even index), sibling at position 1
        # Sibling should not be marked as duplicate
        sibling = result["path"][0][1]
        assert sibling.get("duplicate") is not True
        assert sibling["hash_str"] == "diff" * 16


class TestConvertProofIndexCalculation:
    """Test index calculation across levels."""

    def test_convert_index_progression(self) -> None:
        """Test that index is divided by 2 at each level."""
        txid = "idx_" * 16
        proof = {"height": 100, "index": 8, "nodes": ["n1" * 32, "n2" * 32, "n3" * 32, "n4" * 32]}  # Binary: 1000

        result = convert_proof_to_merkle_path(txid, proof)

        # At level 0: index=8 (even), txid at pos 0 with offset=8, sibling at pos 1 with offset=9
        # At level 1: index=4 (even), sibling has offset=5
        # At level 2: index=2 (even), sibling has offset=3
        # At level 3: index=1 (odd), sibling has offset=0

        # Check txid offset at level 0
        assert result["path"][0][0]["offset"] == 8
        assert result["path"][0][0]["txid"] is True
        # Check sibling offsets
        assert result["path"][0][1]["offset"] == 9
        assert result["path"][1][0]["offset"] == 5
        assert result["path"][2][0]["offset"] == 3
        assert result["path"][3][0]["offset"] == 0

    def test_convert_odd_index_progression(self) -> None:
        """Test index progression starting with odd number."""
        txid = "odd_" * 16
        proof = {"height": 100, "index": 7, "nodes": ["n1" * 32, "n2" * 32, "n3" * 32]}  # Binary: 0111

        result = convert_proof_to_merkle_path(txid, proof)

        # At level 0: index=7 (odd), offset should be 6 (7-1)
        # At level 1: index=3 (odd), offset should be 2 (3-1)
        # At level 2: index=1 (odd), offset should be 0 (1-1)

        assert result["path"][0][0]["offset"] == 6
        assert result["path"][1][0]["offset"] == 2
        assert result["path"][2][0]["offset"] == 0


class TestConvertProofTxidLeaf:
    """Test txid leaf placement."""

    def test_convert_txid_leaf_even_index(self) -> None:
        """Test txid leaf placement when index is even."""
        txid = "txid" * 16
        proof = {"height": 100, "index": 4, "nodes": ["sibling" * 8]}  # Even

        result = convert_proof_to_merkle_path(txid, proof)

        # With even index, txid should be first
        path_level_0 = result["path"][0]
        assert path_level_0[0]["hash_str"] == txid
        assert path_level_0[0]["txid"] is True
        assert path_level_0[0]["offset"] == 4

    def test_convert_txid_leaf_odd_index(self) -> None:
        """Test txid leaf placement when index is odd."""
        txid = "txid" * 16
        proof = {"height": 100, "index": 5, "nodes": ["sibling" * 8]}  # Odd

        result = convert_proof_to_merkle_path(txid, proof)

        # With odd index, txid should be second
        path_level_0 = result["path"][0]
        assert path_level_0[1]["hash_str"] == txid
        assert path_level_0[1]["txid"] is True
        assert path_level_0[1]["offset"] == 5

    def test_convert_txid_leaf_index_zero(self) -> None:
        """Test txid leaf when index is zero."""
        txid = "zero" * 16
        proof = {"height": 100, "index": 0, "nodes": ["sibling" * 8]}

        result = convert_proof_to_merkle_path(txid, proof)

        # Index 0 is even, txid should be first
        path_level_0 = result["path"][0]
        assert path_level_0[0]["hash_str"] == txid
        assert path_level_0[0]["offset"] == 0


class TestConvertProofPathStructure:
    """Test overall path structure."""

    def test_convert_path_levels_match_nodes(self) -> None:
        """Test that path has as many levels as nodes."""
        txid = "test" * 16
        node_count = 5
        proof = {"height": 100, "index": 10, "nodes": [f"node{i}" * 8 for i in range(node_count)]}

        result = convert_proof_to_merkle_path(txid, proof)

        assert len(result["path"]) == node_count

    def test_convert_each_level_has_leaves(self) -> None:
        """Test that each level has leaf entries."""
        txid = "leaf" * 16
        proof = {"height": 100, "index": 3, "nodes": ["n1" * 32, "n2" * 32]}

        result = convert_proof_to_merkle_path(txid, proof)

        # Each level should have at least one leaf (the sibling)
        for level in result["path"]:
            assert len(level) >= 1

    def test_convert_level_0_has_txid(self) -> None:
        """Test that level 0 always includes txid leaf."""
        txid = "check" * 16
        proof = {"height": 100, "index": 7, "nodes": ["node" * 16]}

        result = convert_proof_to_merkle_path(txid, proof)

        # Level 0 should have txid leaf
        level_0 = result["path"][0]
        txid_leaves = [leaf for leaf in level_0 if leaf.get("txid")]
        assert len(txid_leaves) == 1
        assert txid_leaves[0]["hash_str"] == txid


class TestConvertProofEdgeCases:
    """Test edge cases in proof conversion."""

    def test_convert_single_transaction_tree(self) -> None:
        """Test proof for single transaction in block (index 0, one level)."""
        txid = "single" * 10
        proof = {"height": 100, "index": 0, "nodes": ["*"]}  # Duplicate (tree has only one tx)

        result = convert_proof_to_merkle_path(txid, proof)

        assert result["blockHeight"] == 100
        assert len(result["path"]) == 1
        # Index 0 is even, so txid at position 0, sibling at position 1
        assert result["path"][0][1].get("duplicate") is True

    def test_convert_large_index(self) -> None:
        """Test proof with large index."""
        txid = "large" * 13
        proof = {"height": 100, "index": 1023, "nodes": [f"n{i}" * 8 for i in range(10)]}  # Large index

        result = convert_proof_to_merkle_path(txid, proof)

        assert len(result["path"]) == 10

    def test_convert_empty_nodes_list(self) -> None:
        """Test proof with empty nodes list."""
        txid = "empty" * 13
        proof = {"height": 100, "index": 0, "nodes": []}

        result = convert_proof_to_merkle_path(txid, proof)

        assert result["blockHeight"] == 100
        assert len(result["path"]) == 0

    def test_convert_high_block_height(self) -> None:
        """Test proof with high block height."""
        txid = "high" * 16
        proof = {"height": 999999, "index": 0, "nodes": ["node" * 16]}

        result = convert_proof_to_merkle_path(txid, proof)

        assert result["blockHeight"] == 999999

    def test_convert_zero_block_height(self) -> None:
        """Test proof with zero block height (genesis)."""
        txid = "genesis" * 8
        proof = {"height": 0, "index": 0, "nodes": ["*"]}

        result = convert_proof_to_merkle_path(txid, proof)

        assert result["blockHeight"] == 0


class TestConvertProofRealWorld:
    """Test with realistic proof scenarios."""

    def test_convert_typical_proof(self) -> None:
        """Test with typical proof (2048 transactions, index 100)."""
        txid = "real" * 16
        # 2048 transactions = 11 levels (2^11 = 2048)
        proof = {
            "height": 700000,
            "index": 100,
            "nodes": [
                "a1" * 32,
                "a2" * 32,
                "a3" * 32,
                "a4" * 32,
                "a5" * 32,
                "a6" * 32,
                "a7" * 32,
                "a8" * 32,
                "a9" * 32,
                "aa" * 32,
                "ab" * 32,
            ],
        }

        result = convert_proof_to_merkle_path(txid, proof)

        assert result["blockHeight"] == 700000
        assert len(result["path"]) == 11
        # Verify level 0 has txid
        assert any(leaf.get("txid") for leaf in result["path"][0])

    def test_convert_full_block_proof(self) -> None:
        """Test with proof for transaction in full block."""
        txid = "full" * 16
        # Simulating 4096 transactions (12 levels)
        proof = {"height": 650000, "index": 2048, "nodes": [f"node{i:02x}" * 8 for i in range(12)]}

        result = convert_proof_to_merkle_path(txid, proof)

        assert len(result["path"]) == 12

    def test_convert_first_transaction(self) -> None:
        """Test proof for first transaction in block (coinbase)."""
        txid = "coinbase" * 7
        proof = {"height": 100000, "index": 0, "nodes": ["next" * 16, "level2" * 12, "level3" * 12]}

        result = convert_proof_to_merkle_path(txid, proof)

        # Index 0 is always even
        level_0 = result["path"][0]
        # Txid should be first
        assert level_0[0]["hash_str"] == txid
        assert level_0[0]["offset"] == 0

    def test_convert_last_transaction_odd(self) -> None:
        """Test proof for last transaction (odd index)."""
        txid = "last" * 16
        # Last tx in block of 15 (index 14, which is even actually)
        # Let's use 15 (odd)
        proof = {"height": 100000, "index": 15, "nodes": ["prev" * 16, "l2" * 16, "l3" * 16, "l4" * 16]}

        result = convert_proof_to_merkle_path(txid, proof)

        # Index 15 is odd
        level_0 = result["path"][0]
        # Txid should be second
        assert level_0[1]["hash_str"] == txid


class TestConvertProofLeafAttributes:
    """Test individual leaf attributes."""

    def test_convert_leaf_has_offset(self) -> None:
        """Test that all leaves have offset attribute."""
        txid = "attr" * 16
        proof = {"height": 100, "index": 5, "nodes": ["n1" * 32, "n2" * 32]}

        result = convert_proof_to_merkle_path(txid, proof)

        for level in result["path"]:
            for leaf in level:
                assert "offset" in leaf
                assert isinstance(leaf["offset"], int)

    def test_convert_txid_leaf_attributes(self) -> None:
        """Test txid leaf has correct attributes."""
        txid = "txleaf" * 10
        proof = {"height": 100, "index": 0, "nodes": ["sibling" * 8]}

        result = convert_proof_to_merkle_path(txid, proof)

        txid_leaf = result["path"][0][0]  # First leaf (even index)
        assert txid_leaf["hash_str"] == txid
        assert txid_leaf["txid"] is True
        assert txid_leaf["offset"] == 0

    def test_convert_sibling_leaf_attributes(self) -> None:
        """Test sibling leaf has correct attributes."""
        txid = "sib" * 21
        node_hash = "sibhash" * 8
        proof = {"height": 100, "index": 0, "nodes": [node_hash]}

        result = convert_proof_to_merkle_path(txid, proof)

        sibling_leaf = result["path"][0][1]  # Second leaf
        assert sibling_leaf["hash_str"] == node_hash
        assert sibling_leaf.get("txid") is not True
        assert sibling_leaf["offset"] == 1


class TestConvertProofIntegration:
    """Integration tests for proof conversion."""

    def test_convert_multiple_proofs(self) -> None:
        """Test converting multiple different proofs."""
        proofs_and_txids = [
            ("tx1" * 32, {"height": 100, "index": 0, "nodes": ["n1" * 32]}),
            ("tx2" * 32, {"height": 200, "index": 5, "nodes": ["n2" * 32, "n3" * 32]}),
            ("tx3" * 32, {"height": 300, "index": 10, "nodes": ["n4" * 32, "n5" * 32, "n6" * 32]}),
        ]

        results = []
        for txid, proof in proofs_and_txids:
            result = convert_proof_to_merkle_path(txid, proof)
            results.append(result)

        # All should have valid structure
        for i, result in enumerate(results):
            assert result["blockHeight"] == proofs_and_txids[i][1]["height"]
            assert len(result["path"]) == len(proofs_and_txids[i][1]["nodes"])

    def test_convert_consistency(self) -> None:
        """Test that same proof produces same result."""
        txid = "consistent" * 5
        proof = {"height": 100, "index": 7, "nodes": ["node" * 16, "node2" * 12]}

        result1 = convert_proof_to_merkle_path(txid, proof)
        result2 = convert_proof_to_merkle_path(txid, proof)

        assert result1 == result2

    def test_convert_path_completeness(self) -> None:
        """Test that converted path has all required elements."""
        txid = "complete" * 7
        proof = {"height": 500, "index": 42, "nodes": ["n1" * 32, "n2" * 32, "n3" * 32]}

        result = convert_proof_to_merkle_path(txid, proof)

        # Check structure
        assert "blockHeight" in result
        assert "path" in result
        assert isinstance(result["path"], list)

        # Check each level
        for level in result["path"]:
            assert isinstance(level, list)
            assert len(level) > 0
            for leaf in level:
                assert isinstance(leaf, dict)
                assert "offset" in leaf
