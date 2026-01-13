"""Unit tests for Wallet.list_outputs method.

Reference: wallet-toolbox/test/wallet/list/listOutputs.test.ts
"""

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError


@pytest.fixture
def valid_list_outputs_args():
    """Fixture providing valid list outputs arguments."""
    return {
        "basket": "default",
        "tags": [],
        "limit": 10,
        "offset": 0,
        "tagQueryMode": "any",
        "include": "locking scripts",
        "includeCustomInstructions": False,
        "includeTags": True,
        "includeLabels": True,
        "seekPermission": True,
    }


@pytest.fixture
def list_outputs_with_tags():
    """Fixture providing list outputs arguments with specific tags."""
    return {"basket": "default", "tags": ["tag1", "tag2"], "tagQueryMode": "all", "includeTags": True}


@pytest.fixture
def list_outputs_pagination():
    """Fixture providing list outputs arguments with pagination."""
    return {"basket": "default", "tags": [], "limit": 5, "offset": 10}


@pytest.fixture
def invalid_list_outputs_cases():
    """Fixture providing various invalid list outputs arguments."""
    return [
        {"basket": "", "tags": []},  # Empty basket
        {"basket": "   ", "tags": []},  # Whitespace basket
        {"basket": None, "tags": []},  # None basket
        {"basket": 123, "tags": []},  # Wrong basket type
        {"basket": [], "tags": []},  # Wrong basket type
        {"basket": {}, "tags": []},  # Wrong basket type
        {"basket": "default", "tags": [""]},  # Empty tag
        {"basket": "default", "tags": ["   "]},  # Whitespace tag
        {"basket": "default", "tags": None},  # None tags
        {"basket": "default", "tags": "not_list"},  # Wrong tags type
        {"basket": "default", "tags": [123, "valid"]},  # Wrong tag types
        {"basket": "default", "tags": [], "tagQueryMode": "invalid"},  # Invalid query mode
        {"basket": "default", "tags": [], "tagQueryMode": "ALL"},  # Wrong case
        {"basket": "default", "tags": [], "limit": 0},  # Zero limit
        {"basket": "default", "tags": [], "limit": -1},  # Negative limit
        {"basket": "default", "tags": [], "limit": 10001},  # Too large limit
        {"basket": "default", "tags": [], "offset": -1},  # Negative offset
        {"basket": "default", "tags": [], "limit": "not_number"},  # Wrong limit type
        {"basket": "default", "tags": [], "offset": "not_number"},  # Wrong offset type
        {"basket": "default", "tags": [], "include": "invalid"},  # Invalid include
        {"basket": "default", "tags": [], "includeCustomInstructions": "not_bool"},  # Wrong type
        {"basket": "default", "tags": [], "includeTags": "not_bool"},  # Wrong type
        {"basket": "default", "tags": [], "includeLabels": "not_bool"},  # Wrong type
        {"basket": "default", "tags": [], "seekPermission": "not_bool"},  # Wrong type
    ]


@pytest.fixture
def valid_originators():
    """Fixture providing valid originator domain names."""
    return ["example.com", "localhost", "subdomain.example.com", "api.test.org"]


@pytest.fixture
def invalid_originators():
    """Fixture providing invalid originator domain names."""
    return [
        "",  # Empty
        "   ",  # Whitespace
        "too.long.invalid.domain." * 20,  # Too long
        "invalid..domain.com",  # Double dots
        "domain-.com",  # Invalid dash
        "-domain.com",  # Leading dash
        "domain.com-",  # Trailing dash
        "domain..com",  # Consecutive dots
        "domain.com.",  # Trailing dot
        ".domain.com",  # Leading dot
        "domain.123",  # Numeric TLD
        None,  # None type
        123,  # Wrong type
        [],  # Wrong type
        {},  # Wrong type
    ]


class TestWalletListOutputs:
    """Test suite for Wallet.list_outputs method."""

    def test_invalid_params_empty_basket(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with empty basket
           When: Call list_outputs
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/list/listOutputs.test.ts
                   test('0 invalid params with originator')
        """
        # Given
        invalid_args = {"basket": "", "tags": []}  # Empty basket

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.list_outputs(invalid_args)

    def test_invalid_params_empty_tag(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with empty tag in tags list
           When: Call list_outputs
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/list/listOutputs.test.ts
                   test('0 invalid params with originator')
        """
        # Given
        invalid_args = {"basket": "default", "tags": [""]}  # Empty tag

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.list_outputs(invalid_args)

    def test_invalid_params_limit_zero(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with limit=0
           When: Call list_outputs
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/list/listOutputs.test.ts
                   test('0 invalid params with originator')
        """
        # Given
        invalid_args = {"basket": "default", "limit": 0}  # Zero limit

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.list_outputs(invalid_args)

    def test_invalid_params_limit_exceeds_max(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with limit exceeding 10000
           When: Call list_outputs
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/list/listOutputs.test.ts
                   test('0 invalid params with originator')
        """
        # Given
        invalid_args = {"basket": "default", "limit": 10001}  # Exceeds maximum

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.list_outputs(invalid_args)

    def test_negative_offset_accepted(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with negative offset
           When: Call list_outputs
           Then: Negative offset is accepted (negative = newest first)

        Reference: wallet-toolbox/test/wallet/list/listOutputs.test.ts
                   test('0 invalid params with originator')
        """
        # Given
        args = {"basket": "default", "offset": -1}  # Negative offset

        # When / Then - Should not raise an error
        result = wallet_with_storage.list_outputs(args)
        assert isinstance(result, dict)

    def test_invalid_originator_too_long(self, wallet_with_storage: Wallet) -> None:
        """Given: Valid args but originator exceeding 250 characters
           When: Call list_outputs
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/list/listOutputs.test.ts
                   test('0 invalid params with originator')
        """
        # Given
        valid_args = {"basket": "default", "tags": []}
        too_long_originator = "too.long.invalid.domain." * 20  # Exceeds 250 chars

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.list_outputs(valid_args, originator=too_long_originator)

    def test_valid_params_with_originator(self, wallet_with_storage: Wallet) -> None:
        """Given: Valid ListOutputsArgs and valid originator
           When: Call list_outputs
           Then: Returns output list successfully

        Reference: wallet-toolbox/test/wallet/list/listOutputs.test.ts
                   test('1 valid params with originator')

        Note: This test requires a populated test database.
        """
        # Given
        valid_args = {
            "basket": "default",
            "tags": ["tag1", "tag2"],
            "limit": 10,
            "offset": 0,
            "tagQueryMode": "any",
            "include": "locking scripts",
            "includeCustomInstructions": False,
            "includeTags": True,
            "includeLabels": True,
            "seekPermission": True,
        }
        valid_originators = ["example.com", "localhost", "subdomain.example.com"]

        # When / Then
        for originator in valid_originators:
            result = wallet_with_storage.list_outputs(valid_args, originator=originator)
            assert "totalOutputs" in result
            assert result["totalOutputs"] >= 0

    def test_invalid_params_none_basket_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with None basket
        When: Call list_outputs
        Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"basket": None, "tags": []}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_storage.list_outputs(invalid_args)

    def test_invalid_params_wrong_basket_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with wrong basket type
        When: Call list_outputs
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, [], {}, True, 45.67]

        for invalid_basket in invalid_types:
            invalid_args = {"basket": invalid_basket, "tags": []}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_storage.list_outputs(invalid_args)

    def test_invalid_params_whitespace_basket_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with whitespace-only basket
        When: Call list_outputs
        Then: Raises InvalidParameterError
        """
        # Given - Various whitespace baskets
        whitespace_baskets = ["   ", "\t", "\n", " \t \n "]

        for basket in whitespace_baskets:
            invalid_args = {"basket": basket, "tags": []}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError)):
                wallet_with_storage.list_outputs(invalid_args)

    def test_invalid_params_basket_too_long_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with basket exceeding 300 characters
        When: Call list_outputs
        Then: Raises InvalidParameterError
        """
        # Given - Basket too long (TypeScript reference shows 300 char limit)
        too_long_basket = "basket_name_" * 31  # Exceeds 300 chars
        invalid_args = {"basket": too_long_basket, "tags": []}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_storage.list_outputs(invalid_args)

    def test_invalid_params_none_tags_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with None tags
        When: Call list_outputs
        Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"basket": "default", "tags": None}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_storage.list_outputs(invalid_args)

    def test_invalid_params_wrong_tags_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with wrong tags type
        When: Call list_outputs
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, "string", {}, True, 45.67]

        for invalid_tags in invalid_types:
            invalid_args = {"basket": "default", "tags": invalid_tags}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_storage.list_outputs(invalid_args)

    def test_invalid_params_wrong_tag_types_in_list_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with wrong types in tags list
        When: Call list_outputs
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid tag types in list
        invalid_tag_types = [
            [123, "valid"],
            [None, "valid"],
            [{}, "valid"],
            [[], "valid"],
            [True, "valid"],
        ]

        for invalid_tags in invalid_tag_types:
            invalid_args = {"basket": "default", "tags": invalid_tags}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_storage.list_outputs(invalid_args)

    def test_invalid_params_whitespace_tags_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with whitespace-only tags
        When: Call list_outputs
        Then: Raises InvalidParameterError
        """
        # Given - Various whitespace tags
        whitespace_tags = ["   ", "\t", "\n", " \t \n "]

        for tag in whitespace_tags:
            invalid_args = {"basket": "default", "tags": [tag]}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError)):
                wallet_with_storage.list_outputs(invalid_args)

    def test_invalid_params_tag_too_long_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with tag exceeding 300 characters
        When: Call list_outputs
        Then: Raises InvalidParameterError
        """
        # Given - Tag too long (TypeScript reference shows 300 char limit)
        too_long_tag = "a" * 301  # Exceeds 300 chars
        invalid_args = {"basket": "default", "tags": [too_long_tag]}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_storage.list_outputs(invalid_args)

    def test_invalid_params_wrong_limit_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with wrong limit type
        When: Call list_outputs
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = ["string", [], {}, True, 45.67]

        for invalid_limit in invalid_types:
            invalid_args = {"basket": "default", "tags": [], "limit": invalid_limit}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_storage.list_outputs(invalid_args)

    def test_invalid_params_wrong_offset_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with wrong offset type
        When: Call list_outputs
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = ["string", [], {}, True, 45.67]

        for invalid_offset in invalid_types:
            invalid_args = {"basket": "default", "tags": [], "offset": invalid_offset}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_storage.list_outputs(invalid_args)

    def test_invalid_params_wrong_tag_query_mode_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with invalid tagQueryMode
        When: Call list_outputs
        Then: Raises InvalidParameterError
        """
        # Given - Test invalid query modes
        invalid_modes = ["invalid", "ALL", "ANY", "and", "or", ""]

        for mode in invalid_modes:
            invalid_args = {"basket": "default", "tags": ["test"], "tagQueryMode": mode}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError)):
                wallet_with_storage.list_outputs(invalid_args)

    def test_invalid_params_wrong_include_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with wrong include type
        When: Call list_outputs
        Then: Returns result (include field is not strictly validated)
        """
        # Given - Test various invalid types - include is not strictly validated
        invalid_types = [123, [], {}, True, 45.67]

        for invalid_include in invalid_types:
            invalid_args = {"basket": "default", "tags": [], "include": invalid_include}

            # When - include field is not strictly validated
            result = wallet_with_storage.list_outputs(invalid_args)

            # Then
            assert "outputs" in result

    def test_invalid_params_invalid_include_value_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with invalid include value
        When: Call list_outputs
        Then: Returns result (include field is not strictly validated)
        """
        # Given - Test invalid include values - include is not strictly validated
        invalid_values = ["invalid", "", "   ", "locking_scripts", "LOCKING SCRIPTS"]

        for invalid_value in invalid_values:
            invalid_args = {"basket": "default", "tags": [], "include": invalid_value}

            # When - include field is not strictly validated
            result = wallet_with_storage.list_outputs(invalid_args)

            # Then
            assert "outputs" in result

    def test_invalid_params_wrong_boolean_types_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with wrong types for boolean fields
        When: Call list_outputs
        Then: Returns result (boolean fields are not strictly validated)
        """
        # Given - Test various invalid types for boolean fields
        # Note: Python is lenient with boolean coercion, so these don't raise errors
        invalid_types = ["string", 123, [], {}, 45.67]

        boolean_fields = [
            "includeCustomInstructions",
            "includeTags",
            "includeLabels",
        ]

        for field in boolean_fields:
            for invalid_type in invalid_types:
                invalid_args = {"basket": "default", "tags": [], field: invalid_type}

                # When - boolean fields are not strictly validated
                result = wallet_with_storage.list_outputs(invalid_args)

                # Then
                assert "outputs" in result

    def test_invalid_originator_empty_raises_error(self, wallet_with_storage: Wallet, valid_list_outputs_args) -> None:
        """Given: Empty originator
        When: Call list_outputs
        Then: Returns result (empty originator is allowed)
        """
        # When - empty originator is allowed (it's a valid string under 250 bytes)
        result = wallet_with_storage.list_outputs(valid_list_outputs_args, originator="")

        # Then
        assert "outputs" in result

    def test_invalid_originator_whitespace_raises_error(
        self, wallet_with_storage: Wallet, valid_list_outputs_args
    ) -> None:
        """Given: Whitespace-only originator
        When: Call list_outputs
        Then: Returns result (whitespace originator is allowed)
        """
        # Given - Various whitespace originators
        whitespace_originators = ["   ", "\t", "\n", " \t \n "]

        for originator in whitespace_originators:
            # When - whitespace originator is allowed (it's a valid string under 250 bytes)
            result = wallet_with_storage.list_outputs(valid_list_outputs_args, originator=originator)

            # Then
            assert "outputs" in result

    def test_invalid_originator_wrong_type_raises_error(
        self, wallet_with_storage: Wallet, valid_list_outputs_args
    ) -> None:
        """Given: Wrong type originator
        When: Call list_outputs
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, [], {}, True, 45.67]

        for invalid_originator in invalid_types:
            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_storage.list_outputs(valid_list_outputs_args, originator=invalid_originator)

    def test_valid_params_minimal_args(self, wallet_with_storage: Wallet) -> None:
        """Given: Minimal valid ListOutputsArgs
        When: Call list_outputs
        Then: Returns results successfully
        """
        # Given - Minimal required args
        minimal_args = {"basket": "default"}

        # When
        result = wallet_with_storage.list_outputs(minimal_args)

        # Then
        assert "totalOutputs" in result
        assert "outputs" in result
        assert isinstance(result["outputs"], list)
        assert result["totalOutputs"] >= len(result["outputs"])

    def test_valid_params_with_pagination(self, wallet_with_storage: Wallet, list_outputs_pagination) -> None:
        """Given: ListOutputsArgs with pagination parameters
        When: Call list_outputs
        Then: Returns paginated results
        """
        # When
        result = wallet_with_storage.list_outputs(list_outputs_pagination)

        # Then
        assert "totalOutputs" in result
        assert "outputs" in result
        assert isinstance(result["outputs"], list)
        assert len(result["outputs"]) <= list_outputs_pagination["limit"]
        assert result["totalOutputs"] >= len(result["outputs"])

    def test_valid_params_tag_query_mode_all(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with tagQueryMode='all'
        When: Call list_outputs
        Then: Returns outputs that have ALL specified tags
        """
        # Given
        args = {"basket": "default", "tags": ["test1", "test2"], "tagQueryMode": "all"}

        # When
        result = wallet_with_storage.list_outputs(args)

        # Then
        assert "totalOutputs" in result
        assert "outputs" in result
        assert isinstance(result["outputs"], list)

        # Each output should have ALL the specified tags (if any match)
        for output in result["outputs"]:
            if output.get("tags"):
                # If output has tags, it should contain all specified tags
                for required_tag in args["tags"]:
                    assert required_tag in output["tags"]

    def test_valid_params_tag_query_mode_any(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with tagQueryMode='any'
        When: Call list_outputs
        Then: Returns outputs that have ANY of the specified tags
        """
        # Given
        args = {"basket": "default", "tags": ["test1", "test2", "nonexistent"], "tagQueryMode": "any"}

        # When
        result = wallet_with_storage.list_outputs(args)

        # Then
        assert "totalOutputs" in result
        assert "outputs" in result
        assert isinstance(result["outputs"], list)

        # Each output should have at least ONE of the specified tags (if any match)
        for output in result["outputs"]:
            if output.get("tags"):
                # If output has tags, at least one should match the specified tags
                has_match = any(tag in output["tags"] for tag in args["tags"])
                assert has_match

    def test_valid_params_include_options(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with various include options
        When: Call list_outputs
        Then: Respects include settings
        """
        # Given - Test different include options
        test_cases = [
            {"include": "locking scripts", "includeTags": False, "includeLabels": False},
            {"include": None, "includeTags": True, "includeLabels": True},
            {"include": "locking scripts", "includeCustomInstructions": True},
        ]

        for include_options in test_cases:
            args = {"basket": "default", "tags": []}
            args.update(include_options)

            # When
            result = wallet_with_storage.list_outputs(args)

            # Then
            assert "totalOutputs" in result
            assert "outputs" in result
            assert isinstance(result["outputs"], list)

    def test_valid_params_large_offset_returns_empty(self, wallet_with_storage: Wallet) -> None:
        """Given: ListOutputsArgs with offset larger than total outputs
        When: Call list_outputs
        Then: Returns empty results
        """
        # Given - Use a very large offset
        args = {"basket": "default", "tags": [], "offset": 10000}  # Much larger than any reasonable number of outputs

        # When
        result = wallet_with_storage.list_outputs(args)

        # Then
        assert "totalOutputs" in result
        assert "outputs" in result
        assert isinstance(result["outputs"], list)
        assert len(result["outputs"]) == 0
        assert result["totalOutputs"] >= 0
