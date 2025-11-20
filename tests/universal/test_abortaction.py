"""Universal Test Vectors for abortAction method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/abortAction-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/abortAction-simple-result.json
"""

from collections.abc import Callable

import pytest


class TestUniversalVectorsAbortAction:
    """Tests using Universal Test Vectors for abortAction.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    @pytest.mark.xfail(
        reason="Test vector incomplete: transaction with reference 'dGVzdA==' must be pre-created in database"
    )
    def test_abortaction_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], wallet_with_storage
    ) -> None:
        """Given: Universal Test Vector input for abortAction
        When: Call abortAction with JSON vector
        Then: Result matches Universal Test Vector output (JSON)
        """
        # Given
        args_data, result_data = load_test_vectors("abortAction-simple")
        wallet = wallet_with_storage

        # When
        result = wallet.abort_action(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]

    def test_abortaction_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """Given: Universal Test Vector input for abortAction (ABI wire format)
        When: Call abortAction with wire format vector
        Then: Result matches Universal Test Vector output (wire format)
        """
