"""Universal Test Vectors for listActions method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/listActions-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/listActions-simple-result.json
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsListActions:
    """Tests using Universal Test Vectors for listActions.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    def test_listactions_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], wallet_with_services: Wallet
    ) -> None:
        """Given: Universal Test Vector input for listActions
        When: Call listActions
        Then: Result matches Universal Test Vector output (JSON)
        """
        # Given
        args_data, result_data = load_test_vectors("listActions-simple")

        # When
        result = wallet_with_services.list_actions(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]

    def test_listactions_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this."""
