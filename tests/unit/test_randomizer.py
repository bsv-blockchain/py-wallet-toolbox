"""Unit tests for TestRandomizer - Go compatibility tests.

These tests verify that Python's TestRandomizer produces the exact same
outputs as Go's TestRandomizer for interoperability testing.

Reference: go-wallet-toolbox/pkg/randomizer/test_randomizer_test.go
"""

import pytest

from bsv_wallet_toolbox.utils.randomizer import DeterministicRandomizer


class TestDeterministicRandomizerGoCompatibility:
    """Tests matching Go's test_randomizer_test.go"""

    def test_random_base64_by_test_randomizer(self) -> None:
        """Test that Base64(16) returns the expected Go-compatible value.

        Reference: TestRandomBase64ByTestRandomizer
        """
        # given:
        random = DeterministicRandomizer()

        # when:
        randomized = random.base64(16)

        # then:
        # Go test expects: "YWFhYWFhYWFhYWFhYWFhYQ=="
        # This is base64 of 16 'a' characters (0x61 * 16)
        assert randomized == "YWFhYWFhYWFhYWFhYWFhYQ=="

    def test_random_base64_on_zero_length_by_test_randomizer(self) -> None:
        """Test that Base64(0) returns an error.

        Reference: TestRandomBase64OnZeroLengthByTestRandomizer
        """
        # given:
        random = DeterministicRandomizer()

        # when/then:
        with pytest.raises(ValueError, match="length cannot be zero"):
            random.base64(0)

    def test_shuffle_by_test_randomizer(self) -> None:
        """Test that shuffle preserves original order via double-swap.

        Reference: TestShuffleByTestRandomizer
        """
        # given:
        random = DeterministicRandomizer()

        # and:
        original = list(range(100))

        # and:
        numbers = original.copy()

        # when:
        result = random.shuffle(numbers)

        # then:
        assert result == original, "Numbers should be in the same order"

    def test_random_uint64_by_test_randomizer(self) -> None:
        """Test that Uint64 always returns 0.

        Reference: TestRandomUint64ByTestRandomizer
        """
        # given:
        random = DeterministicRandomizer()

        # when:
        value = random.uint64(1000)

        # then:
        assert value == 0, "Random value should be 0"

    def test_random_bytes_sequence(self) -> None:
        """Test that successive calls produce incrementing characters.

        First call: all 'a' (0x61)
        Second call: all 'b' (0x62)
        etc.
        """
        # given:
        random = DeterministicRandomizer()

        # when:
        first = random.random_bytes(4)
        second = random.random_bytes(4)
        third = random.random_bytes(4)

        # then:
        assert first == b"aaaa"  # 0x61 * 4
        assert second == b"bbbb"  # 0x62 * 4
        assert third == b"cccc"  # 0x63 * 4

    def test_random_many_base64_values(self) -> None:
        """Test that many calls produce unique values.

        Reference: TestRandomManyBase64Values (simplified)
        """
        # given:
        random = DeterministicRandomizer()
        lookup: set[str] = set()

        # Using smaller count for faster testing
        count = 100
        length = 3

        # when:
        for _ in range(count):
            randomized = random.base64(length)

            # then:
            assert randomized, "Randomized value should not be empty"

            # and:
            assert randomized not in lookup, "Randomized value should be unique"

            # and:
            lookup.add(randomized)

    def test_random_int_returns_min_value(self) -> None:
        """Test that random_int returns min_value (Go compatibility).

        Go's Uint64(max) always returns 0, so random_int should
        return min_value.
        """
        # given:
        random = DeterministicRandomizer()

        # when:
        value = random.random_int(5, 10)

        # then:
        assert value == 5  # Returns min_value

    def test_base64_length_matches(self) -> None:
        """Test that base64 output length is consistent.

        Reference: TestLengthOfBase64TestImplEqualsDefaultRandomizer (concept)
        """
        # given:
        random = DeterministicRandomizer()

        for length in range(1, 50):
            # when:
            result = random.base64(length)

            # then:
            # base64 encoding: output length = ceil(input_length * 4 / 3) rounded to multiple of 4
            import base64

            expected_len = len(base64.b64encode(b"x" * length))
            assert len(result) == expected_len
