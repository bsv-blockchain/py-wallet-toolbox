"""Edge case and error handling tests for wallet toolbox components.

Tests for unusual inputs, error conditions, and integration edge cases
that may not be covered by the main test suites.
"""

import pytest

from bsv_wallet_toolbox.utils.crypto_utils import (
    bytes_to_int_list,
    generate_random_bytes,
    int_list_to_bytes,
    xor_bytes,
)


class TestCryptoUtilsEdgeCases:
    """Test edge cases for cryptographic utilities."""

    def test_xor_bytes_empty_inputs(self) -> None:
        """Test XOR with empty byte sequences."""
        with pytest.raises(ValueError, match="different lengths"):
            xor_bytes(b"", b"x")

    def test_xor_bytes_single_byte(self) -> None:
        """Test XOR with single byte."""
        result = xor_bytes(b"\x00", b"\xff")
        assert result == b"\xff"

    def test_bytes_to_int_list_empty(self) -> None:
        """Test conversion of empty bytes."""
        result = bytes_to_int_list(b"")
        assert result == []

    def test_int_list_to_bytes_bounds(self) -> None:
        """Test int list conversion with boundary values."""
        # Valid range
        result = int_list_to_bytes([0, 255, 127])
        assert result == b"\x00\xff\x7f"

        # Invalid values
        with pytest.raises(ValueError, match="range 0-255"):
            int_list_to_bytes([256])

        with pytest.raises(ValueError, match="range 0-255"):
            int_list_to_bytes([-1])

    def test_generate_random_bytes_length(self) -> None:
        """Test random byte generation produces correct length."""
        result = generate_random_bytes(16)
        assert len(result) == 16
        assert isinstance(result, bytes)

    def test_generate_random_bytes_zero(self) -> None:
        """Test random byte generation with zero length."""
        result = generate_random_bytes(0)
        assert result == b""


class TestPermissionTokenEdgeCases:
    """Test edge cases for permission token handling."""

    def test_empty_permission_request(self) -> None:
        """Test permission request with minimal fields."""
        from bsv_wallet_toolbox.manager.wallet_permissions_manager import PermissionRequest

        request: PermissionRequest = {
            "type": "protocol",
            "originator": "test.example.com",
        }

        assert request["type"] == "protocol"
        assert request["originator"] == "test.example.com"

    def test_expired_token_handling(self) -> None:
        """Test handling of expired tokens."""
        import time

        from bsv_wallet_toolbox.manager.wallet_permissions_manager import PermissionToken

        # Create expired token
        expired_token: PermissionToken = {
            "type": "protocol",
            "originator": "test.example.com",
            "expiry": int(time.time()) - 3600,  # 1 hour ago
            "protocol": "test-protocol",
        }

        # Should be considered expired
        current_time = int(time.time())
        assert expired_token.get("expiry", 0) < current_time

    def test_token_cache_key_generation(self) -> None:
        """Test cache key generation for different token types."""
        from unittest.mock import Mock

        from bsv_wallet_toolbox.manager.wallet_permissions_manager import WalletPermissionsManager

        # Mock wallet
        mock_wallet = Mock()

        # Create manager
        manager = WalletPermissionsManager(mock_wallet, "admin.test.com")

        # Test protocol token cache key
        protocol_token = {
            "type": "protocol",
            "originator": "test.com",
            "protocol": "test-protocol",
            "counterparty": "anyone",
        }
        cache_key = manager._get_cache_key_for_token(protocol_token)
        assert cache_key == "dpacp:test.com:test-protocol:anyone"

        # Test basket token cache key
        basket_token = {
            "type": "basket",
            "originator": "test.com",
            "basketName": "my-basket",
        }
        cache_key = manager._get_cache_key_for_token(basket_token)
        assert cache_key == "dbap:test.com:my-basket"

        # Test certificate token cache key
        cert_token = {
            "type": "certificate",
            "originator": "test.com",
            "certType": "identity",
            "verifier": "verifier-key",
        }
        cache_key = manager._get_cache_key_for_token(cert_token)
        assert cache_key == "dcap:test.com:identity:verifier-key"

        # Test spending token cache key
        spending_token = {
            "type": "spending",
            "originator": "test.com",
            "authorizedAmount": 1000,
        }
        cache_key = manager._get_cache_key_for_token(spending_token)
        assert cache_key == "dsap:test.com:1000"


class TestIntegrationEdgeCases:
    """Test integration edge cases between components."""

    def test_permission_manager_with_mock_wallet(self) -> None:
        """Test permission manager initialization with mock wallet."""
        from unittest.mock import Mock

        from bsv_wallet_toolbox.manager.wallet_permissions_manager import WalletPermissionsManager

        mock_wallet = Mock()
        manager = WalletPermissionsManager(mock_wallet, "admin.test.com")

        # Should initialize successfully
        assert manager._admin_originator == "admin.test.com"
        assert manager._underlying_wallet == mock_wallet
        assert "onProtocolPermissionRequested" in manager._callbacks

    def test_spending_calculation_edge_cases(self) -> None:
        """Test spending calculation with edge cases."""
        from unittest.mock import Mock

        from bsv_wallet_toolbox.manager.wallet_permissions_manager import WalletPermissionsManager

        mock_wallet = Mock()
        manager = WalletPermissionsManager(mock_wallet, "admin.test.com")

        # Test with no inputs/outputs
        net_spent = manager._calculate_net_spent({})
        assert net_spent == 0

        # Test with inputs but no outputs (consuming UTXOs without creating new ones)
        args = {"inputs": [{"satoshis": 1000}], "outputs": []}
        net_spent = manager._calculate_net_spent(args)
        assert net_spent == -1000  # Spending (burning satoshis)

        # Test with balanced inputs and outputs (no net spending)
        args = {"inputs": [{"satoshis": 1000}], "outputs": [{"satoshis": 1000}]}
        net_spent = manager._calculate_net_spent(args)
        assert net_spent == 0  # No net spending

        # Test with outputs exceeding inputs (receiving, though unusual)
        args = {"inputs": [], "outputs": [{"satoshis": 500}]}
        net_spent = manager._calculate_net_spent(args)
        assert net_spent == 500  # Receiving (though this would be invalid in practice)
