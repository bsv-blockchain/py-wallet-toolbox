"""Universal Test Vectors for revealCounterpartyKeyLinkage method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/revealCounterpartyKeyLinkage-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/revealCounterpartyKeyLinkage-simple-result.json
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsRevealCounterpartyKeyLinkage:
    """Tests using Universal Test Vectors for revealCounterpartyKeyLinkage.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    @pytest.mark.skip(reason="Waiting for reveal_counterparty_key_linkage implementation")
    @pytest.mark.asyncio
    async def test_revealcounterpartykeylinkage_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """Given: Universal Test Vector input for revealCounterpartyKeyLinkage
        When: Call revealCounterpartyKeyLinkage
        Then: Result matches Universal Test Vector output (JSON)
        """
        # Given
        args_data, result_data = load_test_vectors("revealCounterpartyKeyLinkage-simple")
        wallet = Wallet(chain="main")

        # When
        result = await wallet.reveal_counterparty_key_linkage(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]

    @pytest.mark.skip(reason="ABI tests skipped - TypeScript doesn't test ABI wire format")
    @pytest.mark.asyncio
    async def test_revealcounterpartykeylinkage_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this."""
