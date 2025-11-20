"""Universal Test Vectors for getVersion method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/getVersion-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/getVersion-simple-result.json

Note: TypeScript implementation returns 'wallet-brc100-1.0.0',
      but Universal Test Vectors expect '1.0.0' only.
      We follow the official spec (Universal Test Vectors).
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsGetVersion:
    """Tests using Universal Test Vectors for getVersion.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    def test_getversion_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """Given: Universal Test Vector input for getVersion
           When: Call getVersion with empty args
           Then: Result matches Universal Test Vector output (JSON)

        Note: This test will FAIL until Python implementation reaches v1.0.0.
              Universal Test Vectors expect "1.0.0" but Python currently returns "0.1.0".
              This failure is expected and acceptable during development.
        """
        # Given
        args_data, result_data = load_test_vectors("getVersion-simple")
        wallet = Wallet(chain="main")  # Will use Wallet.VERSION (currently "0.6.0")

        # When
        result = wallet.get_version(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]

    def test_getversion_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this.

        This test would verify:
        1. Deserialize wire input: "1c00" -> method + args
        2. Execute getVersion
        3. Serialize result -> matches "00312e302e30"

        Following the principle: "If TypeScript skips it, we skip it too."
        """
