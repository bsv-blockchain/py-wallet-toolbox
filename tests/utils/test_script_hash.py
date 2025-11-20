"""Unit tests for script_hash (GO port).

This module tests output script hashing logic.

Reference: go-wallet-toolbox/pkg/internal/txutils/script_hash_test.go
"""

import pytest

try:
    from bsv_wallet_toolbox.utils.script_hash import hash_output_script

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class TestScriptHashSuccessCases:
    """Test suite for script_hash success cases (GO port).

    Reference: go-wallet-toolbox/pkg/internal/txutils/script_hash_test.go
                func TestHashOutputScript_SuccessCases(t *testing.T)
    """

    def test_hash_output_script_success_cases(self) -> None:
        """Given: Valid script hex strings
           When: Hash output script
           Then: Returns expected hash in little-endian format

        Reference: go-wallet-toolbox/pkg/internal/txutils/script_hash_test.go
                   TestHashOutputScript_SuccessCases
        """
        tests = [
            {
                "name": "Valid P2PKH",
                "script_hex": "76a91489abcdefabbaabbaabbaabbaabbaabbaabbaabba88ac",
                "expected_le": "db46d31e84e16e7fb031b3ab375131a7bb65775c0818dc17fe0d4444efb3d0aa",
            },
            {
                "name": "Empty script",
                "script_hex": "",
                "expected_le": "55b852781b9995a44c939b64e441ae2724b96f99c8f4fb9a141cfc9842c4b0e3",
            },
            {
                "name": "Short script 0x00",
                "script_hex": "00",
                "expected_le": "1da0af1706a31185763837b33f1d90782c0a78bbe644a59c987ab3ff9c0b346e",
            },
            {
                "name": "Valid P2SH",
                "script_hex": "a91489abcdefabbaabbaabbaabbaabbaabbaabbaabba87",
                "expected_le": "e7e41b1311c9fc8248e8f6e87cc382ca4b1af9c3189bb896712c3aebdf018639",
            },
        ]

        for test in tests:
            # When
            result = hash_output_script(test["script_hex"])

            # Then
            assert result == test["expected_le"], f"Test '{test['name']}' failed"


class TestScriptHashErrorCases:
    """Test suite for script_hash error cases (GO port).

    Reference: go-wallet-toolbox/pkg/internal/txutils/script_hash_test.go
                func TestHashOutputScript_ErrorCases(t *testing.T)
    """

    def test_hash_output_script_error_cases(self) -> None:
        """Given: Invalid script hex strings
           When: Hash output script
           Then: Raises exception

        Reference: go-wallet-toolbox/pkg/internal/txutils/script_hash_test.go
                   TestHashOutputScript_ErrorCases
        """
        tests = [
            {
                "name": "Invalid hex input",
                "script_hex": "zzzz",
            },
            {
                "name": "Odd-length hex input",
                "script_hex": "abc",
            },
        ]

        for test in tests:
            # When/Then
            with pytest.raises(Exception):
                hash_output_script(test["script_hex"])
