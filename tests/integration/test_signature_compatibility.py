"""Signature compatibility tests for cross-implementation verification.

These tests verify that Python implementation produces identical signatures
to TypeScript/Go implementations when given the same inputs.

Reference: go-wallet-toolbox/pkg/internal/assembler/create_action_tx_assembler_test.go

The key test is TestTxAssemblerAlignsTsGenerated which:
1. Uses Alice's fixed private key
2. Loads TS-generated CreateActionResult
3. Assembles and signs the transaction
4. Compares the result with TS-generated SignedTransactionHex
"""

import json

import pytest

from tests.testabilities.testusers import ALICE
from tests.testabilities.tsgenerated import (
    SIGNED_TRANSACTION_HEX,
    create_action_result_json,
    load_create_action_result,
)


class TestTxAssemblerAlignsTsGenerated:
    """Test that transaction assembler produces identical results to TS/Go.

    Reference: go-wallet-toolbox/pkg/internal/assembler/create_action_tx_assembler_test.go
    TestTxAssemblerAlignsTsGenerated
    """

    def test_tx_assembler_aligns_ts_generated(self) -> None:
        """Given: Alice's key and TS-generated CreateActionResult
           When: Assemble and sign the transaction
           Then: Result matches TS-generated SignedTransactionHex exactly

        This is the core cross-implementation compatibility test.
        If this passes, Python signing is compatible with TS/Go.

        Reference: go-wallet-toolbox/pkg/internal/assembler/create_action_tx_assembler_test.go
        TestTxAssemblerAlignsTsGenerated
        """
        from bsv_wallet_toolbox.assembler import CreateActionTransactionAssembler

        # Given: Alice's key deriver
        key_deriver = ALICE.key_deriver()

        # And: TS-generated CreateActionResult
        create_action_result = load_create_action_result()

        # When: Assemble the transaction
        assembled = CreateActionTransactionAssembler(
            key_deriver=key_deriver,
            provided_inputs=None,
            create_action_result=create_action_result,
        ).assemble()

        # Then: No error during assembly
        assert assembled is not None

        # When: Sign the transaction
        assembled.sign()

        # Then: The signed transaction matches TS-generated exactly
        assert assembled.hex() == SIGNED_TRANSACTION_HEX, (
            f"Signature mismatch!\n"
            f"Expected: {SIGNED_TRANSACTION_HEX[:100]}...\n"
            f"Got:      {assembled.hex()[:100]}..."
        )

    def test_ts_generated_fixtures_load_correctly(self) -> None:
        """Given: TS-generated fixtures
        When: Load them
        Then: They contain expected data
        """
        # Load CreateActionResult
        result = load_create_action_result()

        # Verify structure
        assert "inputs" in result
        assert "outputs" in result
        assert "inputBeef" in result
        assert "reference" in result
        assert "version" in result
        assert "lockTime" in result

        # Verify specific values matching Go test expectations
        assert len(result["inputs"]) == 1
        assert result["inputs"][0]["sourceTxid"] == "756754d5ad8f00e05c36d89a852971c0a1dc0c10f20cd7840ead347aff475ef6"
        assert result["inputs"][0]["sourceVout"] == 0
        assert result["inputs"][0]["sourceSatoshis"] == 99904
        assert result["inputs"][0]["providedBy"] == "storage"
        assert result["inputs"][0]["type"] == "P2PKH"

        # Verify outputs
        assert len(result["outputs"]) == 32
        assert result["outputs"][0]["satoshis"] == 1000
        assert result["outputs"][0]["vout"] == 0

        # Verify derivation
        assert result["derivationPrefix"] == "Y2NjY2NjY2NjY2NjY2NjYw=="
        assert result["reference"] == "YmJiYmJiYmJiYmJi"

    def test_signed_transaction_hex_is_valid(self) -> None:
        """Given: TS-generated SignedTransactionHex
        When: Parse it
        Then: It's a valid transaction hex
        """
        # Verify it's valid hex
        try:
            tx_bytes = bytes.fromhex(SIGNED_TRANSACTION_HEX)
        except ValueError:
            pytest.fail("SIGNED_TRANSACTION_HEX is not valid hex")

        # Verify minimum transaction size (header + at least one input/output)
        assert len(tx_bytes) > 60, "Transaction too short"

        # Verify version (first 4 bytes, little-endian)
        version = int.from_bytes(tx_bytes[:4], "little")
        assert version == 1, f"Unexpected transaction version: {version}"

    def test_alice_key_deriver_works(self) -> None:
        """Given: Alice's fixed private key
        When: Create key deriver
        Then: It produces expected public key
        """
        # Get Alice's identity key (public key)
        identity_key = ALICE.identity_key()

        # Verify it's a valid compressed public key (33 bytes = 66 hex chars)
        assert len(identity_key) == 66, f"Expected 66 hex chars, got {len(identity_key)}"

        # Verify it starts with 02 or 03 (compressed public key prefix)
        assert identity_key.startswith(("02", "03")), "Invalid compressed public key prefix"

    def test_create_action_result_json_matches_dict(self) -> None:
        """Given: TS-generated CreateActionResult
        When: Load as JSON string and as dict
        Then: They match
        """
        json_str = create_action_result_json()
        result_dict = load_create_action_result()

        # Parse JSON string and compare
        parsed = json.loads(json_str)
        assert parsed == result_dict


class TestKeyDerivationCompatibility:
    """Test that key derivation matches Go/TS implementations."""

    def test_alice_private_key_matches_go(self) -> None:
        """Verify Alice's private key matches Go implementation.

        Reference: go-wallet-toolbox/pkg/internal/fixtures/testusers/test_users.go
        """
        expected_priv_key = "143ab18a84d3b25e1a13cefa90038411e5d2014590a2a4a57263d1593c8dee1c"
        assert ALICE.priv_key == expected_priv_key

    def test_bob_private_key_matches_go(self) -> None:
        """Verify Bob's private key matches Go implementation.

        Reference: go-wallet-toolbox/pkg/internal/fixtures/testusers/test_users.go
        """
        from tests.testabilities.testusers import BOB

        expected_priv_key = "0881208859876fc227d71bfb8b91814462c5164b6fee27e614798f6e85d2547d"
        assert BOB.priv_key == expected_priv_key

    def test_alice_user_id_matches_go(self) -> None:
        """Verify Alice's user ID matches Go implementation."""
        assert ALICE.id == 1

    def test_bob_user_id_matches_go(self) -> None:
        """Verify Bob's user ID matches Go implementation."""
        from tests.testabilities.testusers import BOB

        assert BOB.id == 2


class TestBeefToInternalizeCompatibility:
    """Test BEEF to internalize fixtures match Go implementation."""

    def test_parent_beef_txid_matches_go(self) -> None:
        """Verify parent BEEF txid matches Go implementation."""
        from tests.testabilities.tsgenerated import PARENT_BEEF_TXID

        expected = "756754d5ad8f00e05c36d89a852971c0a1dc0c10f20cd7840ead347aff475ef6"
        assert expected == PARENT_BEEF_TXID

    def test_beef_internalize_height_matches_go(self) -> None:
        """Verify BEEF internalize height matches Go implementation."""
        from tests.testabilities.tsgenerated import BEEF_TO_INTERNALIZE_HEIGHT

        expected = 1653933
        assert expected == BEEF_TO_INTERNALIZE_HEIGHT

    def test_beef_merkle_root_matches_go(self) -> None:
        """Verify BEEF merkle root matches Go implementation."""
        from tests.testabilities.tsgenerated import BEEF_TO_INTERNALIZE_MERKLE_ROOT

        expected = "6ee2e72ad8ca8db54d8272875d4b6a53f3afe194d82c1f71369a2983f6a343c8"
        assert expected == BEEF_TO_INTERNALIZE_MERKLE_ROOT

    def test_parent_beef_is_valid_hex(self) -> None:
        """Verify parent BEEF is valid hex."""
        from tests.testabilities.tsgenerated import PARENT_BEEF

        try:
            beef_bytes = bytes.fromhex(PARENT_BEEF)
        except ValueError:
            pytest.fail("PARENT_BEEF is not valid hex")

        # Verify BEEF header (0x0200beef)
        assert beef_bytes[:4] == b"\x02\x00\xbe\xef", "Invalid BEEF header"
