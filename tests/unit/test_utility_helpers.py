"""Unit tests for utility helper functions.

Reference: wallet-toolbox/src/utility/utilityHelpers.ts
"""

import pytest

from bsv_wallet_toolbox.utils import (
    to_wallet_network,
    verify_hex_string,
    verify_id,
    verify_integer,
    verify_number,
    verify_one,
    verify_one_or_none,
    verify_truthy,
)


class TestToWalletNetwork:
    """Test suite for to_wallet_network function.

    Note: This test is currently skipped as the to_wallet_network utility is not yet implemented.

    Reference: wallet-toolbox/src/utility/utilityHelpers.ts
               function toWalletNetwork
    """

    def test_converts_main_to_mainnet(self) -> None:
        """Given: Chain 'main'
           When: Call to_wallet_network
           Then: Returns 'mainnet'

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   toWalletNetwork function
        """
        # Given

        chain = "main"

        # When
        result = to_wallet_network(chain)

        # Then
        assert result == "mainnet"

    def test_converts_test_to_testnet(self) -> None:
        """Given: Chain 'test'
           When: Call to_wallet_network
           Then: Returns 'testnet'

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   toWalletNetwork function
        """
        # Given

        chain = "test"

        # When
        result = to_wallet_network(chain)

        # Then
        assert result == "testnet"


class TestVerifyTruthy:
    """Test suite for verify_truthy function.

    Note: This test is currently skipped as the verify_truthy utility is not yet implemented.

    Reference: wallet-toolbox/src/utility/utilityHelpers.ts
               function verifyTruthy
    """

    def test_returns_truthy_value(self) -> None:
        """Given: Truthy value
           When: Call verify_truthy
           Then: Returns the value unchanged

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyTruthy function
        """
        # Given

        values = ["test", 123, True, ["item"], {"key": "value"}]

        # When/Then
        for value in values:
            result = verify_truthy(value)
            assert result == value

    def test_raises_error_for_none(self) -> None:
        """Given: None value
           When: Call verify_truthy
           Then: Raises error

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyTruthy function
        """
        # Given

        # When/Then
        with pytest.raises(Exception):
            verify_truthy(None)

    def test_raises_error_for_empty_string(self) -> None:
        """Given: Empty string
           When: Call verify_truthy
           Then: Raises error

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyTruthy function
        """
        # Given

        # When/Then
        with pytest.raises(Exception):
            verify_truthy("")

    def test_uses_custom_description(self) -> None:
        """Given: None value and custom description
           When: Call verify_truthy with description
           Then: Error message includes custom description

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyTruthy function with description parameter
        """
        # Given

        description = "Custom error message"

        # When/Then
        with pytest.raises(Exception) as exc_info:
            verify_truthy(None, description)

        assert description in str(exc_info.value)


class TestVerifyHexString:
    """Test suite for verify_hex_string function.

    Note: This test is currently skipped as the verify_hex_string utility is not yet implemented.

    Reference: wallet-toolbox/src/utility/utilityHelpers.ts
               function verifyHexString
    """

    def test_trims_and_lowercases_hex_string(self) -> None:
        """Given: Hex string with whitespace and uppercase
           When: Call verify_hex_string
           Then: Returns trimmed lowercase string

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyHexString function
        """
        # Given

        test_cases = [
            ("  ABC123  ", "abc123"),
            ("DEF456", "def456"),
            ("\n789ABC\t", "789abc"),
        ]

        # When/Then
        for input_val, expected in test_cases:
            result = verify_hex_string(input_val)
            assert result == expected

    def test_raises_error_for_non_string(self) -> None:
        """Given: Non-string value
           When: Call verify_hex_string
           Then: Raises error

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyHexString function
        """
        # Given

        invalid_values = [123, None, [], {}]

        # When/Then
        for value in invalid_values:
            with pytest.raises(Exception):
                verify_hex_string(value)

    def test_raises_error_for_invalid_hex_string(self) -> None:
        """Given: String that is not valid hex
           When: Call verify_hex_string
           Then: Raises ValueError with descriptive message

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyHexString function
        """
        # Given
        invalid_hex_values = ["xyz", "123g", "abc!", "  invalid  "]

        # When/Then
        for value in invalid_hex_values:
            with pytest.raises(ValueError, match="Value is not a valid hex string"):
                verify_hex_string(value)

    def test_raises_error_for_invalid_hex_with_custom_description(self) -> None:
        """Given: Invalid hex string with custom description
           When: Call verify_hex_string
           Then: Raises ValueError with custom description

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyHexString function
        """
        # Given
        invalid_value = "not_hex"
        custom_description = "Transaction ID must be valid hex"

        # When/Then
        with pytest.raises(ValueError, match=custom_description):
            verify_hex_string(invalid_value, custom_description)


class TestVerifyNumber:
    """Test suite for verify_number function.

    Note: This test is currently skipped as the verify_number utility is not yet implemented.

    Reference: wallet-toolbox/src/utility/utilityHelpers.ts
               function verifyNumber
    """

    def test_returns_valid_number(self) -> None:
        """Given: Valid number
           When: Call verify_number
           Then: Returns the number

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyNumber function
        """
        # Given

        numbers = [0, 1, -1, 3.14, -2.5, 1000]

        # When/Then
        for num in numbers:
            result = verify_number(num)
            assert result == num

    def test_raises_error_for_none(self) -> None:
        """Given: None value
           When: Call verify_number
           Then: Raises error

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyNumber function
        """
        # Given

        # When/Then
        with pytest.raises(Exception):
            verify_number(None)

    def test_raises_error_for_non_number(self) -> None:
        """Given: Non-number value
           When: Call verify_number
           Then: Raises error

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyNumber function
        """
        # Given

        invalid_values = ["123", [], {}, True]

        # When/Then
        for value in invalid_values:
            with pytest.raises(Exception):
                verify_number(value)


class TestVerifyInteger:
    """Test suite for verify_integer function.

    Note: This test is currently skipped as the verify_integer utility is not yet implemented.

    Reference: wallet-toolbox/src/utility/utilityHelpers.ts
               function verifyInteger
    """

    def test_returns_valid_integer(self) -> None:
        """Given: Valid integer
           When: Call verify_integer
           Then: Returns the integer

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyInteger function
        """
        # Given

        integers = [0, 1, -1, 1000, -500]

        # When/Then
        for num in integers:
            result = verify_integer(num)
            assert result == num

    def test_raises_error_for_float(self) -> None:
        """Given: Float value
           When: Call verify_integer
           Then: Raises error

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyInteger function
        """
        # Given

        floats = [3.14, -2.5, 0.1]

        # When/Then
        for value in floats:
            with pytest.raises(Exception):
                verify_integer(value)

    def test_raises_error_for_none(self) -> None:
        """Given: None value
           When: Call verify_integer
           Then: Raises error

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyInteger function
        """
        # Given

        # When/Then
        with pytest.raises(Exception):
            verify_integer(None)


class TestVerifyId:
    """Test suite for verify_id function.

    Note: This test is currently skipped as the verify_id utility is not yet implemented.

    Reference: wallet-toolbox/src/utility/utilityHelpers.ts
               function verifyId
    """

    def test_returns_valid_id(self) -> None:
        """Given: Valid ID (integer > 0)
           When: Call verify_id
           Then: Returns the ID

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyId function
        """
        # Given

        valid_ids = [1, 2, 100, 999999]

        # When/Then
        for id_val in valid_ids:
            result = verify_id(id_val)
            assert result == id_val

    def test_raises_error_for_zero(self) -> None:
        """Given: ID value of 0
           When: Call verify_id
           Then: Raises error

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyId function
        """
        # Given

        # When/Then
        with pytest.raises(Exception):
            verify_id(0)

    def test_raises_error_for_negative(self) -> None:
        """Given: Negative ID value
           When: Call verify_id
           Then: Raises error

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyId function
        """
        # Given

        # When/Then
        with pytest.raises(Exception):
            verify_id(-1)

    def test_raises_error_for_float(self) -> None:
        """Given: Float ID value
           When: Call verify_id
           Then: Raises error

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyId function (calls verifyInteger)
        """
        # Given

        # When/Then
        with pytest.raises(Exception):
            verify_id(1.5)


class TestVerifyOneOrNone:
    """Test suite for verify_one_or_none function.

    Note: This test is currently skipped as the verify_one_or_none utility is not yet implemented.

    Reference: wallet-toolbox/src/utility/utilityHelpers.ts
               function verifyOneOrNone
    """

    def test_returns_first_element_for_single_item(self) -> None:
        """Given: List with one element
           When: Call verify_one_or_none
           Then: Returns the element

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyOneOrNone function
        """
        # Given

        results = ["item"]

        # When
        result = verify_one_or_none(results)

        # Then
        assert result == "item"

    def test_returns_none_for_empty_list(self) -> None:
        """Given: Empty list
           When: Call verify_one_or_none
           Then: Returns None

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyOneOrNone function
        """
        # Given

        results = []

        # When
        result = verify_one_or_none(results)

        # Then
        assert result is None

    def test_raises_error_for_multiple_items(self) -> None:
        """Given: List with multiple elements
           When: Call verify_one_or_none
           Then: Raises error

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyOneOrNone function
        """
        # Given

        results = ["item1", "item2"]

        # When/Then
        with pytest.raises(Exception) as exc_info:
            verify_one_or_none(results)

        assert "unique" in str(exc_info.value).lower()


class TestVerifyOne:
    """Test suite for verify_one function.

    Note: This test is currently skipped as the verify_one utility is not yet implemented.

    Reference: wallet-toolbox/src/utility/utilityHelpers.ts
               function verifyOne
    """

    def test_returns_element_for_single_item(self) -> None:
        """Given: List with exactly one element
           When: Call verify_one
           Then: Returns the element

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyOne function
        """
        # Given

        results = ["item"]

        # When
        result = verify_one(results)

        # Then
        assert result == "item"

    def test_raises_error_for_empty_list(self) -> None:
        """Given: Empty list
           When: Call verify_one
           Then: Raises error

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyOne function
        """
        # Given

        results = []

        # When/Then
        with pytest.raises(Exception) as exc_info:
            verify_one(results)

        assert "unique" in str(exc_info.value).lower() or "exist" in str(exc_info.value).lower()

    def test_raises_error_for_multiple_items(self) -> None:
        """Given: List with multiple elements
           When: Call verify_one
           Then: Raises error

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyOne function
        """
        # Given

        results = ["item1", "item2"]

        # When/Then
        with pytest.raises(Exception) as exc_info:
            verify_one(results)

        assert "unique" in str(exc_info.value).lower()

    def test_uses_custom_error_description(self) -> None:
        """Given: Empty list and custom error description
           When: Call verify_one with error description
           Then: Error message includes custom description

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   verifyOne function with errorDescrition parameter
        """
        # Given

        results = []
        description = "Custom error message"

        # When/Then
        with pytest.raises(Exception) as exc_info:
            verify_one(results, description)

        assert description in str(exc_info.value)
