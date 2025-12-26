"""Unit tests for proof_for_merkle_path (GO port).

This module tests TSC proof to MerklePath conversion logic.

Reference: go-wallet-toolbox/pkg/internal/txutils/proof_for_merkle_path_test.go
"""

import pytest

try:
    from bsv_wallet_toolbox.utils.proof_for_merkle_path import convert_tsc_proof_to_merkle_path

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class TestProofForMerklePath:
    """Test suite for proof_for_merkle_path (GO port).

    Reference: go-wallet-toolbox/pkg/internal/txutils/proof_for_merkle_path_test.go
                func TestConvertTscProofToMerklePath(t *testing.T)
    """

    def test_convert_tsc_proof_to_merkle_path_with_various_inputs(self) -> None:
        """Given: TSC proof data (txid, index, nodes, blockHeight)
           When: Convert TSC proof to MerklePath
           Then: Returns MerklePath or raises error for invalid inputs

        Reference: go-wallet-toolbox/pkg/internal/txutils/proof_for_merkle_path_test.go
                   TestConvertTscProofToMerklePath
        """
        test_cases = [
            {
                "name": "success - even index",
                "txid": "4d5e6f7a8b9c0d1e2f30415263748596a7b8c9d0e1f2a3b4c5d6e7f8091a2b3c",
                "index": 0,
                "nodes": ["a" * 64, "b" * 64, "c" * 64],
                "blockHeight": 100,
                "wantErr": False,
            },
            {
                "name": "success - odd index",
                "txid": "5e4d3c2b1a0f9e8d7c6b5a4938271615141312110f0e0d0c0b0a090807060504",
                "index": 1,
                "nodes": ["d" * 64, "e" * 64, "f" * 64],
                "blockHeight": 200,
                "wantErr": False,
            },
            {
                "name": "success - duplicate node marker",
                "txid": "11f20e0d0c0b0a090807060504030201ffeeddccbbaa99887766554433221100",
                "index": 1,
                "nodes": ["*", "b" * 64],
                "blockHeight": 300,
                "wantErr": False,
                "checkDuplicate": True,
            },
            {
                "name": "error - empty nodes list",
                "txid": "4d5e6f7a8b9c0d1e2f30415263748596a7b8c9d0e1f2a3b4c5d6e7f8091a2b3c",
                "index": 0,
                "nodes": [],
                "blockHeight": 100,
                "wantErr": True,
            },
            {
                "name": "error - invalid txid",
                "txid": "invalid-txid",
                "index": 0,
                "nodes": ["a" * 64],
                "blockHeight": 100,
                "wantErr": True,
            },
            {
                "name": "error - invalid node hash at level 0",
                "txid": "4d5e6f7a8b9c0d1e2f30415263748596a7b8c9d0e1f2a3b4c5d6e7f8091a2b3c",
                "index": 0,
                "nodes": ["invalid-node-hash"],
                "blockHeight": 100,
                "wantErr": True,
            },
        ]

        for tc in test_cases:
            # When
            if tc["wantErr"]:
                with pytest.raises(Exception):
                    convert_tsc_proof_to_merkle_path(tc["txid"], tc["index"], tc["nodes"], tc["blockHeight"])
            else:
                mp = convert_tsc_proof_to_merkle_path(tc["txid"], tc["index"], tc["nodes"], tc["blockHeight"])

                # Then
                assert mp is not None, f"Test '{tc['name']}' failed"
                assert mp["blockHeight"] == tc["blockHeight"]

                if tc.get("checkDuplicate"):
                    assert (
                        mp["path"][0][0].get("duplicate") is not None
                    ), "first level sibling should be marked duplicate"
