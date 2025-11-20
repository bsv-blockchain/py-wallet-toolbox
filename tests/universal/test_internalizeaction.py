"""Universal Test Vectors for internalizeAction method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/internalizeAction-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/internalizeAction-simple-result.json
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsInternalizeAction:
    """Tests using Universal Test Vectors for internalizeAction.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    def test_internalizeaction_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], wallet_with_services: Wallet
    ) -> None:
        """Given: Universal Test Vector input for internalizeAction
        When: Call internalizeAction
        Then: Result matches Universal Test Vector output (JSON)
        """
        # Given
        args_data, result_data = load_test_vectors("internalizeAction-simple")

        # When
        result = wallet_with_services.internalize_action(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]

    def test_internalizeaction_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this."""
