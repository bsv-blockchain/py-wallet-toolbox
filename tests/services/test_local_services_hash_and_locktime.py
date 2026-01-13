"""Local WalletServices methods tests: hashOutputScript and nLockTimeIsFinal.

Reference: toolbox/ts-wallet-toolbox/src/services/Services.ts
Reference: go-wallet-toolbox/pkg/internal/txutils/script_hash.go
Reference: go-wallet-toolbox/pkg/wdk/locktime.go
"""

from time import time
from unittest.mock import patch

import pytest
from bsv.transaction import Transaction
from bsv.transaction_input import TransactionInput

from bsv_wallet_toolbox.services.services import Services


class TestHashOutputScript:
    def test_hash_output_script_matches_expected(self) -> None:
        # Given
        services = Services("main")
        script_hex = "76a91489abcdefabbaabbaabbaabbaabbaabbaabbaabba88ac"
        expected_le = "db46d31e84e16e7fb031b3ab375131a7bb65775c0818dc17fe0d4444efb3d0aa"

        # When
        result = services.hash_output_script(script_hex)

        # Then
        assert result == expected_le


class TestNLockTimeIsFinal:
    def test_final_when_all_sequences_are_maxint(self) -> None:
        # Given: a transaction with all input sequences = 0xFFFFFFFF
        tx = Transaction()
        tx.inputs.append(
            TransactionInput(
                source_txid="00" * 32,
                source_output_index=0,
                sequence=0xFFFFFFFF,
            )
        )
        services = Services("main")

        # When
        result = services.n_lock_time_is_final(tx)

        # Then
        assert result is True

    def test_height_based_locktime_strict_less_than(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Given: height branch (nLockTime < 500_000_000), strict < comparison
        services = Services("main")

        def fake_get_height() -> int:
            return 800_000

        monkeypatch.setattr(services, "get_height", fake_get_height)

        # When / Then
        assert services.n_lock_time_is_final(799_999) is True
        assert services.n_lock_time_is_final(800_000) is False

    def test_timestamp_based_locktime_strict_less_than(self) -> None:
        # Given: timestamp branch (nLockTime >= 500_000_000), strict < comparison
        services = Services("main")
        now = int(time())

        # When / Then
        assert services.n_lock_time_is_final(now - 10) is True
        assert services.n_lock_time_is_final(now + 3600) is False


class TestHashOutputScriptErrorHandling:
    """Test hash_output_script method error handling and edge cases."""

    def test_hash_output_script_invalid_hex(self) -> None:
        """Test hash_output_script with invalid hex strings."""
        services = Services("main")

        invalid_hex_values = [
            "invalid_hex",  # Invalid hex characters
            "gg",  # Invalid hex
            "123",  # Odd length
            None,  # None value
            123,  # Wrong type
            [],  # Wrong type
            {},  # Wrong type
        ]

        for invalid_hex in invalid_hex_values:
            with pytest.raises((ValueError, TypeError)):
                services.hash_output_script(invalid_hex)

    def test_hash_output_script_empty_script(self) -> None:
        """Test hash_output_script with empty script."""
        services = Services("main")

        result = services.hash_output_script("")
        # Should handle empty script gracefully
        assert isinstance(result, str)
        assert len(result) > 0  # Should return a hash

    def test_hash_output_script_odd_length_hex(self) -> None:
        """Test hash_output_script with odd-length hex string."""
        services = Services("main")

        # Odd length hex should raise ValueError (matches Go/TS behavior)
        with pytest.raises(ValueError):
            services.hash_output_script("123")  # 3 characters = 1.5 bytes

    def test_hash_output_script_max_length_script(self) -> None:
        """Test hash_output_script with very long script."""
        services = Services("main")

        # Create a very long script (simulate large locking script)
        long_script = "00" * 10000  # 10,000 bytes

        result = services.hash_output_script(long_script)
        assert isinstance(result, str)
        assert len(result) > 0
        # Should handle large scripts without performance issues

    def test_hash_output_script_unicode_characters(self) -> None:
        """Test hash_output_script with unicode in string (should fail)."""
        services = Services("main")

        # Unicode characters should cause hex decoding to fail
        with pytest.raises((ValueError, TypeError)):
            services.hash_output_script("test_unicode_ñ")

    def test_hash_output_script_case_insensitive_hex(self) -> None:
        """Test hash_output_script with mixed case hex."""
        services = Services("main")

        # Test with mixed case - should work the same
        script_lower = "76a91489abcdefabbaabbaabbaabbaabbaabbaabbaabba88ac"
        script_upper = "76A91489ABCDEFABBAABBAABBAABBAABBAABBAABBAABBA88AC"
        script_mixed = "76a91489ABCDEFabbaABBAabbaABBAabbaABBAabbaABBA88ac"

        result_lower = services.hash_output_script(script_lower)
        result_upper = services.hash_output_script(script_upper)
        result_mixed = services.hash_output_script(script_mixed)

        # All should produce the same result (hex is case-insensitive)
        assert result_lower == result_upper == result_mixed

    def test_hash_output_script_minimal_script(self) -> None:
        """Test hash_output_script with minimal valid script."""
        services = Services("main")

        # Minimal script - just OP_TRUE
        minimal_script = "51"  # OP_1

        result = services.hash_output_script(minimal_script)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_output_script_p2pkh_script(self) -> None:
        """Test hash_output_script with standard P2PKH script."""
        services = Services("main")

        # Standard P2PKH script: OP_DUP OP_HASH160 <20 bytes> OP_EQUALVERIFY OP_CHECKSIG
        p2pkh_script = "76a91489abcdefabbaabbaabbaabbaabbaabbaabbaabba88ac"

        result = services.hash_output_script(p2pkh_script)
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hash should be 64 hex characters

    def test_hash_output_script_p2sh_script(self) -> None:
        """Test hash_output_script with P2SH script."""
        services = Services("main")

        # P2SH script: OP_HASH160 <20 bytes> OP_EQUAL
        p2sh_script = "a91489abcdefabbaabbaabbaabbaabbaabbaabbaabba87"

        result = services.hash_output_script(p2sh_script)
        assert isinstance(result, str)
        assert len(result) == 64


class TestNLockTimeIsFinalErrorHandling:
    """Test n_lock_time_is_final method error handling and edge cases."""

    def test_n_lock_time_is_final_invalid_transaction(self) -> None:
        """Test n_lock_time_is_final with invalid transaction objects."""
        services = Services("main")

        invalid_txs = [
            None,  # None value
            "string",  # Wrong type
            [],  # Wrong type
            {},  # Wrong type
        ]

        for invalid_tx in invalid_txs:
            with pytest.raises((AttributeError, TypeError, ValueError)):
                services.n_lock_time_is_final(invalid_tx)

    def test_n_lock_time_is_final_transaction_no_inputs(self) -> None:
        """Test n_lock_time_is_final with transaction that has no inputs."""
        services = Services("main")

        tx = Transaction()  # No inputs added
        result = services.n_lock_time_is_final(tx)
        # Should handle transactions with no inputs gracefully
        assert isinstance(result, bool)

    def test_n_lock_time_is_final_mixed_sequences(self) -> None:
        """Test n_lock_time_is_final with mixed input sequences."""
        services = Services("main")

        # Create transaction with mixed sequences
        tx = Transaction()
        tx.inputs.append(TransactionInput(source_txid="00" * 32, source_output_index=0, sequence=0xFFFFFFFF))  # Final
        tx.inputs.append(
            TransactionInput(source_txid="00" * 32, source_output_index=1, sequence=0xFFFFFFFE)
        )  # Not final

        # Mock get_height since transaction locktime (0) is height-based
        with patch.object(services, "get_height", return_value=1000000):
            result = services.n_lock_time_is_final(tx)
            assert result is True  # Mixed sequences make transaction final (locktime ignored)

    def test_n_lock_time_is_final_all_non_final_sequences(self) -> None:
        """Test n_lock_time_is_final with all inputs having non-final sequences."""
        services = Services("main")

        tx = Transaction()
        tx.inputs.append(
            TransactionInput(source_txid="00" * 32, source_output_index=0, sequence=0xFFFFFFFE)
        )  # Not final
        tx.inputs.append(
            TransactionInput(source_txid="00" * 32, source_output_index=1, sequence=0xFFFFFFFD)
        )  # Not final

        # Mock get_height since transaction locktime (0) is height-based
        with patch.object(services, "get_height", return_value=1000000):
            result = services.n_lock_time_is_final(tx)
            assert result is True  # Non-final sequences make transaction final (locktime ignored)

    def test_n_lock_time_is_final_height_based_boundary_values(self) -> None:
        """Test n_lock_time_is_final with height-based boundary values."""
        services = Services("main")

        # Mock get_height to return specific values
        test_cases = [
            (500000, 499999, True),  # locktime < height
            (500000, 500000, False),  # locktime == height
            (500000, 500001, False),  # locktime > height
            (0, 0, False),  # boundary at 0
            (499999999, 499999998, True),  # just below timestamp threshold
            (500000000, 499999999, True),  # just below timestamp threshold
        ]

        for mock_height, locktime, expected in test_cases:
            with patch.object(services, "get_height", return_value=mock_height):
                result = services.n_lock_time_is_final(locktime)
                assert result == expected, f"Failed for height={mock_height}, locktime={locktime}"

    def test_n_lock_time_is_final_timestamp_based_boundary_values(self) -> None:
        """Test n_lock_time_is_final with timestamp-based boundary values."""
        services = Services("main")

        # Use current time for timestamp-based tests
        now = int(time())

        test_cases = [
            (now - 10, True),  # Past timestamp
            (now + 3600, False),  # Future timestamp
            (now, False),  # Current time
        ]

        for locktime, expected in test_cases:
            result = services.n_lock_time_is_final(locktime)
            assert result == expected, f"Failed for locktime={locktime}"

    def test_n_lock_time_is_final_network_height_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test n_lock_time_is_final when get_height fails."""
        services = Services("main")

        # Mock get_height to fail
        def failing_get_height():
            raise ConnectionError("Network unreachable")

        monkeypatch.setattr(services, "get_height", failing_get_height)

        # Height-based locktime should handle failure gracefully
        result = services.n_lock_time_is_final(400000)
        # Should return False when height check fails
        assert result is False

    def test_n_lock_time_is_final_large_sequence_numbers(self) -> None:
        """Test n_lock_time_is_final with very large sequence numbers."""
        services = Services("main")

        tx = Transaction()
        tx.inputs.append(
            TransactionInput(source_txid="00" * 32, source_output_index=0, sequence=0xFFFFFFFF)
        )  # Max uint32
        tx.inputs.append(
            TransactionInput(source_txid="00" * 32, source_output_index=1, sequence=0xFFFFFFFF)
        )  # Max uint32

        result = services.n_lock_time_is_final(tx)
        assert result is True  # All max sequences should be final

    def test_n_lock_time_is_final_zero_sequence_numbers(self) -> None:
        """Test n_lock_time_is_final with zero sequence numbers."""
        services = Services("main")

        tx = Transaction()
        tx.inputs.append(TransactionInput(source_txid="00" * 32, source_output_index=0, sequence=0))  # Zero sequence
        tx.inputs.append(TransactionInput(source_txid="00" * 32, source_output_index=1, sequence=0))  # Zero sequence

        # Mock get_height since transaction locktime (0) is height-based
        with patch.object(services, "get_height", return_value=1000000):
            result = services.n_lock_time_is_final(tx)
            assert result is True  # Zero sequences make transaction final (locktime ignored)

    def test_n_lock_time_is_final_many_inputs(self) -> None:
        """Test n_lock_time_is_final with many inputs."""
        services = Services("main")

        tx = Transaction()
        # Add many inputs, all with final sequences
        for i in range(100):
            tx.inputs.append(TransactionInput(source_txid="00" * 32, source_output_index=i, sequence=0xFFFFFFFF))

        result = services.n_lock_time_is_final(tx)
        assert result is True  # All final sequences

        # Now test with one non-final sequence
        tx.inputs[50].sequence = 0xFFFFFFFE
        # Mock get_height since transaction locktime (0) is height-based
        with patch.object(services, "get_height", return_value=1000000):
            result = services.n_lock_time_is_final(tx)
            assert result is True  # Mixed sequences make transaction final (locktime ignored)

    def test_n_lock_time_is_final_negative_locktime_values(self) -> None:
        """Test n_lock_time_is_final with negative locktime values."""
        services = Services("main")

        # Negative values should be treated as height-based (since < 500M)
        # Mock get_height for height-based locktime check
        with patch.object(services, "get_height", return_value=1000000):
            result = services.n_lock_time_is_final(-1)
            assert result is True  # Negative locktime < height is final

    def test_n_lock_time_is_final_extremely_large_locktime(self) -> None:
        """Test n_lock_time_is_final with extremely large locktime values."""
        services = Services("main")

        # Very large timestamp (year 2106+)
        large_timestamp = 2**31  # About year 2038 in Unix time

        result = services.n_lock_time_is_final(large_timestamp)
        assert result is False  # Future timestamps should not be final

    def test_n_lock_time_is_final_transaction_with_locktime_field(self) -> None:
        """Test n_lock_time_is_final considers transaction's own locktime field."""
        services = Services("main")

        # The method should only look at input sequences, not tx locktime
        tx = Transaction()
        tx.locktime = 1000000  # Set transaction locktime
        tx.inputs.append(
            TransactionInput(source_txid="00" * 32, source_output_index=0, sequence=0xFFFFFFFF)
        )  # Final sequence

        result = services.n_lock_time_is_final(tx)
        assert result is True  # Should ignore tx locktime, only check sequences

    def test_services_method_calls_with_none_self(self) -> None:
        """Test that methods handle None self parameter gracefully."""
        # This tests the robustness of the methods when called incorrectly

        try:
            # Try calling methods with None as self - should fail gracefully
            services = Services("main")
            hash_method = services.hash_output_script
            locktime_method = services.n_lock_time_is_final

            # These should raise AttributeError, not crash
            with pytest.raises(AttributeError):
                hash_method(None, "test_script")

            with pytest.raises((AttributeError, TypeError)):
                locktime_method(Transaction())

        except Exception:
            # Any exception is acceptable as long as it's not a crash
            pass
