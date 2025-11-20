"""Universal Test Vectors for discoverByAttributes method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/discoverByAttributes-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/discoverByAttributes-simple-result.json
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsDiscoverByAttributes:
    """Tests using Universal Test Vectors for discoverByAttributes.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    def test_discoverbyattributes_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """Given: Universal Test Vector input for discoverByAttributes
        When: Call discoverByAttributes
        Then: Result matches Universal Test Vector output (JSON)
        """
        # Given
        args_data, result_data = load_test_vectors("discoverByAttributes-simple")
        wallet = Wallet(chain="main")

        # When
        result = wallet.discover_by_attributes(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]

    def test_discoverbyattributes_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this."""
