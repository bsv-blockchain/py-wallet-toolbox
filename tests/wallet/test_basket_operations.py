"""Unit tests for Wallet basket-related operations.

Baskets are collections/categories for organizing outputs (UTXOs).

Reference: wallet-toolbox test files
"""

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError


class TestWalletBasketOperations:
    """Test suite for Wallet basket management methods."""

    @pytest.mark.skip(reason="Waiting for basket operations implementation with test database")
    @pytest.mark.asyncio
    async def test_create_basket(self, wallet: Wallet) -> None:
        """Given: Valid basket name
           When: Create a new basket
           Then: Basket is created successfully

        Note: Baskets are used to organize outputs into categories.
        """
        # Given
        basket_name = "payments"

        # When
        result = await wallet.create_basket({"name": basket_name})

        # Then
        assert "basketId" in result or "name" in result
        assert result.get("name") == basket_name

    @pytest.mark.skip(reason="Waiting for basket operations implementation with test database")
    @pytest.mark.asyncio
    async def test_create_basket_invalid_name_empty(self, wallet: Wallet) -> None:
        """Given: Empty basket name
           When: Attempt to create basket
           Then: Raises InvalidParameterError

        Note: Basket name must be non-empty and under 300 characters.
        """
        # Given
        invalid_args = {"name": ""}  # Empty name

        # When / Then
        with pytest.raises(InvalidParameterError):
            await wallet.create_basket(invalid_args)

    @pytest.mark.skip(reason="Waiting for basket operations implementation with test database")
    @pytest.mark.asyncio
    async def test_create_basket_invalid_name_too_long(self, wallet: Wallet) -> None:
        """Given: Basket name exceeding 300 characters
           When: Attempt to create basket
           Then: Raises InvalidParameterError

        Note: Basket name must be at most 300 characters.
        """
        # Given
        invalid_args = {"name": "a" * 301}  # 301 characters

        # When / Then
        with pytest.raises(InvalidParameterError):
            await wallet.create_basket(invalid_args)

    @pytest.mark.skip(reason="Waiting for basket operations implementation with test database")
    @pytest.mark.asyncio
    async def test_list_baskets(self, wallet: Wallet) -> None:
        """Given: Wallet with existing baskets
           When: Call list_baskets
           Then: Returns list of all baskets

        Note: Should include at least the 'default' basket.
        """
        # When
        result = await wallet.list_baskets()

        # Then
        assert "baskets" in result
        assert isinstance(result["baskets"], list)
        assert len(result["baskets"]) >= 1  # At least 'default' basket

        # Check for default basket
        basket_names = [b["name"] for b in result["baskets"]]
        assert "default" in basket_names

    @pytest.mark.skip(reason="Waiting for basket operations implementation with test database")
    @pytest.mark.asyncio
    async def test_get_basket_by_name(self, wallet: Wallet) -> None:
        """Given: Wallet with a specific basket
           When: Get basket by name
           Then: Returns basket information

        Note: Used to retrieve basket details and statistics.
        """
        # Given
        basket_name = "default"

        # When
        result = await wallet.get_basket({"name": basket_name})

        # Then
        assert "basket" in result
        assert result["basket"]["name"] == basket_name
        assert "outputCount" in result["basket"] or "totalSatoshis" in result["basket"]

    @pytest.mark.skip(reason="Waiting for basket operations implementation with test database")
    @pytest.mark.asyncio
    async def test_delete_basket(self, wallet: Wallet) -> None:
        """Given: Wallet with a non-default basket
           When: Delete the basket
           Then: Basket is removed (outputs may be moved to default)

        Note: The 'default' basket cannot be deleted.
        """
        # Given - First create a basket
        await wallet.create_basket({"name": "temporary"})

        # When
        delete_result = await wallet.delete_basket({"name": "temporary"})

        # Then
        assert "deleted" in delete_result
        assert delete_result["deleted"] is True

    @pytest.mark.skip(reason="Waiting for basket operations implementation with test database")
    @pytest.mark.asyncio
    async def test_delete_default_basket_fails(self, wallet: Wallet) -> None:
        """Given: Attempt to delete the 'default' basket
           When: Call delete_basket for 'default'
           Then: Raises InvalidParameterError or returns error

        Note: Default basket is protected and cannot be deleted.
        """
        # Given / When / Then
        with pytest.raises((InvalidParameterError, Exception)):
            await wallet.delete_basket({"name": "default"})


class TestWalletOutputTagOperations:
    """Test suite for output tag operations.

    Tags are labels/metadata attached to outputs for organization and filtering.
    """

    @pytest.mark.skip(reason="Waiting for tag operations implementation with test database")
    @pytest.mark.asyncio
    async def test_add_tags_to_output(self, wallet: Wallet) -> None:
        """Given: Existing output and tags
           When: Add tags to the output
           Then: Tags are associated with the output

        Note: Tags are used in listOutputs filtering.
        """
        # Given
        args = {"output": "txid.0", "tags": ["payment", "urgent"]}  # Output identifier

        # When
        result = await wallet.add_output_tags(args)

        # Then
        assert "added" in result
        assert result["added"] is True

    @pytest.mark.skip(reason="Waiting for tag operations implementation with test database")
    @pytest.mark.asyncio
    async def test_remove_tags_from_output(self, wallet: Wallet) -> None:
        """Given: Output with existing tags
           When: Remove specific tags
           Then: Tags are removed from the output

        Note: Used to update output metadata.
        """
        # Given
        args = {"output": "txid.0", "tags": ["urgent"]}  # Remove this tag

        # When
        result = await wallet.remove_output_tags(args)

        # Then
        assert "removed" in result
        assert result["removed"] is True

    @pytest.mark.skip(reason="Waiting for tag operations implementation with test database")
    @pytest.mark.asyncio
    async def test_list_output_tags(self, wallet: Wallet) -> None:
        """Given: Output with tags
           When: List tags for the output
           Then: Returns all associated tags

        Note: Used to inspect output metadata.
        """
        # Given
        args = {"output": "txid.0"}

        # When
        result = await wallet.list_output_tags(args)

        # Then
        assert "tags" in result
        assert isinstance(result["tags"], list)
