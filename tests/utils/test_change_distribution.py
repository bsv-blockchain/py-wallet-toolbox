"""Unit tests for change_distribution (GO port).

This module tests change output distribution logic.

Reference: go-wallet-toolbox/pkg/internal/txutils/change_distribution_test.go
"""

import random
from collections.abc import Callable

import pytest

try:
    from bsv_wallet_toolbox.utils.change_distribution import ChangeDistribution

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


def mock_zero_randomizer(max_val: int) -> int:
    """Always return 0."""
    return 0


def mock_max_randomizer(max_val: int) -> int:
    """Always return max."""
    return max_val


def mock_const_randomizer(*factors: int) -> Callable[[int], int]:
    """Return randomizer that cycles through given factors."""
    max_factor = max(factors)
    i = 0

    def randomizer(max_val: int) -> int:
        nonlocal i
        index = i % len(factors)
        i += 1
        return max_val * factors[index] // max_factor

    return randomizer


class TestChangeDistribution:
    """Test suite for change_distribution (GO port).

    Reference: go-wallet-toolbox/pkg/internal/txutils/change_distribution_test.go
                func TestChangeDistribution(t *testing.T)
    """

    def test_change_distribution_with_various_scenarios(self) -> None:
        """Given: Various initial values, randomizers, counts, and amounts
           When: Distribute change
           Then: Returns expected distribution

        Reference: go-wallet-toolbox/pkg/internal/txutils/change_distribution_test.go
                   TestChangeDistribution
        """
        tests = {
            "single output": {
                "initialValue": 1000,
                "randomizer": mock_zero_randomizer,
                "count": 1,
                "amount": 5500,
                "expected": [5500],
            },
            "single output with one satoshi": {
                "initialValue": 1000,
                "randomizer": mock_zero_randomizer,
                "count": 1,
                "amount": 1,
                "expected": [1],
            },
            "zero outputs": {
                "initialValue": 1000,
                "randomizer": mock_zero_randomizer,
                "count": 0,
                "amount": 5500,
                "expected": [],
            },
            "zero amount": {
                "initialValue": 1000,
                "randomizer": mock_zero_randomizer,
                "count": 6,
                "amount": 0,
                "expected": [],
            },
            "zero amount & zero count": {
                "initialValue": 1000,
                "randomizer": mock_zero_randomizer,
                "count": 0,
                "amount": 0,
                "expected": [],
            },
            "not saturated: reminder + (count-1) * initialValue": {
                "initialValue": 1000,
                "randomizer": mock_zero_randomizer,
                "count": 6,
                "amount": 5500,
                "expected": [500, 1000, 1000, 1000, 1000, 1000],
            },
            "not saturated: initialValue/4 + (count-1) * initialValue": {
                "initialValue": 1000,
                "randomizer": mock_zero_randomizer,
                "count": 6,
                "amount": 5250,
                "expected": [250, 1000, 1000, 1000, 1000, 1000],
            },
            "equally saturated: (count) * initialValue": {
                "initialValue": 1000,
                "randomizer": mock_zero_randomizer,
                "count": 6,
                "amount": 6000,
                "expected": [1000, 1000, 1000, 1000, 1000, 1000],
            },
            "saturated: equal distribution +1": {
                "initialValue": 1000,
                "randomizer": mock_max_randomizer,
                "count": 6,
                "amount": 6001,
                "expected": [1000, 1000, 1000, 1000, 1000, 1001],
            },
            "saturated: equal distribution": {
                "initialValue": 1000,
                "randomizer": mock_zero_randomizer,
                "count": 6,
                "amount": 7200,
                "expected": [1200, 1200, 1200, 1200, 1200, 1200],
            },
            "saturated: not equal distribution": {
                "initialValue": 1000,
                "randomizer": mock_zero_randomizer,
                "count": 6,
                "amount": 7201,
                "expected": [1201, 1200, 1200, 1200, 1200, 1200],
            },
            "saturated: not equal distribution - mockMaxRandomizer": {
                "initialValue": 1000,
                "randomizer": mock_max_randomizer,
                "count": 6,
                "amount": 7205,
                "expected": [1200, 1200, 1200, 1200, 1200, 1205],
            },
            "saturated: not equal distribution - constRandomizer": {
                "initialValue": 1000,
                "randomizer": mock_const_randomizer(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
                "count": 6,
                "amount": 7205,
                "expected": [1305, 1260, 1220, 1180, 1140, 1100],
            },
            "saturated: zero initialValue": {
                "initialValue": 0,
                "randomizer": mock_max_randomizer,
                "count": 6,
                "amount": 7201,
                "expected": [1200, 1200, 1200, 1200, 1200, 1201],
            },
            "not saturated, minimal value: 1 + (count-1) * initialValue": {
                "initialValue": 1000,
                "randomizer": mock_zero_randomizer,
                "count": 6,
                "amount": 5001,
                "expected": [1, 1000, 1000, 1000, 1000, 1000],
            },
        }

        for _name, test in tests.items():
            # Given
            dist = ChangeDistribution(test["initialValue"], test["randomizer"])

            # When
            values = list(dist.distribute(test["count"], test["amount"]))

            # Then
            assert values == test["expected"], f"Test '{_name}' failed"


class TestChangeDistributionPanics:
    """Test suite for change_distribution panic cases (GO port).

    Reference: go-wallet-toolbox/pkg/internal/txutils/change_distribution_test.go
                func TestChangeDistributionPanics(t *testing.T)
    """

    def test_change_distribution_panics_on_invalid_inputs(self) -> None:
        """Given: Invalid combinations of count and amount
           When: Try to distribute change
           Then: Raises exception (panic in GO)

        Reference: go-wallet-toolbox/pkg/internal/txutils/change_distribution_test.go
                   TestChangeDistributionPanics
        """
        tests = {
            "reduced count: (count-1) * initialValue": {
                "initialValue": 1000,
                "randomizer": mock_zero_randomizer,
                "count": 6,
                "amount": 5000,
            },
            "not saturated, reduced count: (count-1) * initialValue": {
                "initialValue": 1000,
                "randomizer": mock_zero_randomizer,
                "count": 6,
                "amount": 4999,
            },
            "not saturated, reduced count to one": {
                "initialValue": 1000,
                "randomizer": mock_zero_randomizer,
                "count": 6,
                "amount": 1,
            },
        }

        for _name, test in tests.items():
            # Given
            dist = ChangeDistribution(test["initialValue"], test["randomizer"])

            # When/Then
            with pytest.raises(Exception):  # GO panic -> Python exception
                list(dist.distribute(test["count"], test["amount"]))


class TestChangeDistributionWithActualRandomizer:
    """Test suite for change_distribution with real randomizer (GO port).

    Reference: go-wallet-toolbox/pkg/internal/txutils/change_distribution_test.go
                func TestChangeDistributionWithActualRandomizer(t *testing.T)
    """

    def test_change_distribution_with_real_randomizer(self) -> None:
        """Given: ChangeDistribution with real randomizer
           When: Distribute 2000 * 1000 satoshis into 1000 outputs
           Then: All values >= initial_value and most are randomized (not equal)

        Reference: go-wallet-toolbox/pkg/internal/txutils/change_distribution_test.go
                   TestChangeDistributionWithActualRandomizer
        """

        # Given
        initial_value = 1000
        count = 1000

        def actual_randomizer(max_val: int) -> int:
            return random.randint(0, max_val)

        dist = ChangeDistribution(initial_value, actual_randomizer)

        # When
        values = list(dist.distribute(count, 2 * count * initial_value))

        # Then
        equals_to_initial = 0
        for v in values:
            assert v >= initial_value, "value was randomized wrongly - it should be >= initial_value"
            if v == initial_value:
                equals_to_initial += 1

        assert equals_to_initial < count, "random should not return equal values (~0% chance)"
