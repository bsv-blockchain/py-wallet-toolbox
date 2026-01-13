"""Unit tests for contains_utxo (GO port).

This module tests UTXO containment checking logic.

Reference: go-wallet-toolbox/pkg/internal/txutils/contains_utxo_test.go
"""

try:

    from bsv_wallet_toolbox.utils.contains_utxo import contains_utxo

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class TestContainsUtxo:
    """Test suite for contains_utxo (GO port).

    Reference: go-wallet-toolbox/pkg/internal/txutils/contains_utxo_test.go
                func TestContainsUtxo(t *testing.T)
    """

    def test_contains_utxo_checks_presence_correctly(self) -> None:
        """Given: List of UTXO details and an outpoint
           When: Check if outpoint is in the list
           Then: Returns correct boolean

        Reference: go-wallet-toolbox/pkg/internal/txutils/contains_utxo_test.go
                   TestContainsUtxo
        """
        txid = "9ca4300a599b48638073cb35f833475a8c6cfca0d4bbe6dd7244d174e7a0e7f6"

        tests = [
            {
                "name": "UTXO found",
                "details": [
                    {"txid": txid, "vout": 1},
                    {"txid": "abc", "vout": 2},
                ],
                "outpoint": {"txid": txid, "vout": 1},
                "expected": True,
            },
            {
                "name": "UTXO not found",
                "details": [
                    {"txid": txid, "vout": 0},
                ],
                "outpoint": {"txid": txid, "vout": 1},
                "expected": False,
            },
            {
                "name": "Empty list",
                "details": [],
                "outpoint": {"txid": txid, "vout": 1},
                "expected": False,
            },
        ]

        for test in tests:
            # When
            actual = contains_utxo(test["details"], test["outpoint"])

            # Then
            assert actual == test["expected"], f"Test '{test['name']}' failed"
