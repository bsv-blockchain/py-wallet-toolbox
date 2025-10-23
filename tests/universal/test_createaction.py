"""Universal Test Vectors for createAction method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/createAction-1-out-args.json
- tests/data/universal-test-vectors/generated/brc100/createAction-1-out-result.json
- tests/data/universal-test-vectors/generated/brc100/createAction-no-signAndProcess-args.json
- tests/data/universal-test-vectors/generated/brc100/createAction-no-signAndProcess-result.json
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsCreateAction:
    """Tests using Universal Test Vectors for createAction.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    @pytest.mark.skip(reason="Waiting for create_action implementation")
    @pytest.mark.asyncio
    async def test_createaction_1out_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """Given: Universal Test Vector input for createAction (1 output)
        When: Call createAction with 1 output
        Then: Result matches Universal Test Vector output (JSON)
        """
        # Given
        args_data, result_data = load_test_vectors("createAction-1-out")
        wallet = Wallet(chain="main")

        # When
        result = await wallet.create_action(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]

    @pytest.mark.skip(reason="ABI tests skipped - TypeScript doesn't test ABI wire format")
    @pytest.mark.asyncio
    async def test_createaction_1out_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this."""

    @pytest.mark.skip(reason="Waiting for create_action implementation")
    @pytest.mark.asyncio
    async def test_createaction_nosignandprocess_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """Given: Universal Test Vector input for createAction (no signAndProcess)
        When: Call createAction without signAndProcess
        Then: Result matches Universal Test Vector output (JSON)
        """
        # Given
        args_data, result_data = load_test_vectors("createAction-no-signAndProcess")
        wallet = Wallet(chain="main")

        # When
        result = await wallet.create_action(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]

    @pytest.mark.skip(reason="ABI tests skipped - TypeScript doesn't test ABI wire format")
    @pytest.mark.asyncio
    async def test_createaction_nosignandprocess_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this."""
