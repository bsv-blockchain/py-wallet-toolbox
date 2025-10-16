"""Unit tests for Wallet.get_version method.

Reference: ts-wallet-toolbox/test/Wallet/get/getVersion.test.ts
"""

import pytest

from bsv_wallet_toolbox import InvalidParameterError, Wallet


class TestWalletGetVersion:
    """Test suite for Wallet.get_version method."""
    
    @pytest.mark.asyncio
    async def test_get_version_returns_correct_version(self):
        """Given: A wallet instance
           When: get_version is called
           Then: Returns the hardcoded version constant"""
        # Given
        wallet = Wallet()
        
        # When
        result = await wallet.get_version({})
        
        # Then
        assert result == {"version": Wallet.VERSION}
        assert result["version"] == Wallet.VERSION
    
    @pytest.mark.asyncio
    async def test_get_version_with_valid_originator(self):
        """Given: A wallet
           When: get_version is called with valid originator
           Then: Returns version without error"""
        # Given
        wallet = Wallet()
        
        # When
        result = await wallet.get_version({}, originator="example.com")
        
        # Then
        assert result == {"version": Wallet.VERSION}
    
    @pytest.mark.asyncio
    async def test_get_version_with_invalid_originator_type(self):
        """Given: A wallet
           When: get_version is called with non-string originator
           Then: Raises InvalidParameterError"""
        # Given
        wallet = Wallet()
        
        # When/Then
        with pytest.raises(InvalidParameterError) as exc_info:
            await wallet.get_version({}, originator=123)  # type: ignore
        
        assert "originator" in str(exc_info.value)
        assert "must be a string" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_version_with_too_long_originator(self):
        """Given: A wallet
           When: get_version is called with originator over 250 bytes
           Then: Raises InvalidParameterError"""
        # Given
        wallet = Wallet()
        too_long_originator = "a" * 251  # 251 bytes
        
        # When/Then
        with pytest.raises(InvalidParameterError) as exc_info:
            await wallet.get_version({}, originator=too_long_originator)
        
        assert "originator" in str(exc_info.value)
        assert "250 bytes" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_version_result_type(self):
        """Given: A wallet
           When: get_version is called
           Then: Returns dict with 'version' key"""
        # Given
        wallet = Wallet()
        
        # When
        result = await wallet.get_version({})
        
        # Then
        assert isinstance(result, dict)
        assert "version" in result
        assert isinstance(result["version"], str)

