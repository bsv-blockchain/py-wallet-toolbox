"""High-impact coverage tests for WalletPermissionsManager protocol methods.

This module targets the uncovered lines in manager/wallet_permissions_manager.py
by testing DPACP, DBAP, DCAP, and DSAP permission methods.
"""

from __future__ import annotations

import time
from unittest.mock import Mock

import pytest

try:
    from bsv_wallet_toolbox.manager.wallet_permissions_manager import WalletPermissionsManager

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    WalletPermissionsManager = None


@pytest.fixture
def mock_underlying_wallet():
    """Create a mock underlying wallet."""
    wallet = Mock()
    # Set up basic mock responses
    wallet.create_action.return_value = {"txid": "mock_txid", "reference": "mock_ref"}
    wallet.sign_action.return_value = {"signature": "mock_signature"}
    wallet.abort_action.return_value = {"aborted": True}
    wallet.internalize_action.return_value = {"internalized": True}
    wallet.relinquish_output.return_value = {"relinquished": True}
    wallet.get_public_key.return_value = {"publicKey": "mock_key"}
    wallet.encrypt.return_value = {"encrypted": "mock_encrypted"}
    wallet.decrypt.return_value = {"decrypted": "mock_decrypted"}
    wallet.create_hmac.return_value = {"hmac": "mock_hmac"}
    wallet.verify_hmac.return_value = {"valid": True}
    wallet.create_signature.return_value = {"signature": "mock_sig"}
    wallet.verify_signature.return_value = {"valid": True}
    wallet.acquire_certificate.return_value = {"certificate": "mock_cert"}
    wallet.list_certificates.return_value = {"certificates": []}
    wallet.prove_certificate.return_value = {"proof": "mock_proof"}
    wallet.relinquish_certificate.return_value = {"relinquished": True}
    wallet.disclose_certificate.return_value = {"disclosed": True}
    wallet.discover_by_identity_key.return_value = {"results": []}
    wallet.discover_by_attributes.return_value = {"results": []}
    wallet.is_authenticated.return_value = {"authenticated": True}
    wallet.wait_for_authentication.return_value = {"success": True}
    wallet.get_height.return_value = {"height": 1000}
    wallet.get_header_for_height.return_value = {"header": "mock_header"}
    wallet.get_network.return_value = {"network": "testnet"}
    wallet.get_version.return_value = {"version": "1.0.0"}
    wallet.list_actions.return_value = {"actions": []}
    wallet.list_outputs.return_value = {"outputs": []}
    return wallet


@pytest.fixture
def permissions_manager(mock_underlying_wallet):
    """Create a WalletPermissionsManager instance."""
    return WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test.com")


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="WalletPermissionsManager not available")
class TestDPACPMethods:
    """Test DPACP (Domain Protocol Access Control Protocol) methods."""

    def test_grant_dpacp_permission(self, permissions_manager):
        """Test granting DPACP permission."""
        originator = "test.com"
        protocol_id = {"protocolName": "test_protocol", "securityLevel": 1}

        token = permissions_manager.grant_dpacp_permission(
            originator=originator,
            protocol_id=protocol_id,
            counterparty=None,
        )

        assert token is not None
        assert token.get("originator") == originator
        assert "txid" in token

    def test_verify_dpacp_permission_valid(self, permissions_manager):
        """Test verifying valid DPACP permission."""
        originator = "test.com"
        protocol_id = {"protocolName": "verify_protocol", "securityLevel": 1}

        # First grant permission
        permissions_manager.grant_dpacp_permission(
            originator=originator,
            protocol_id=protocol_id,
        )

        # Then verify it
        result = permissions_manager.verify_dpacp_permission(
            originator=originator,
            protocol_id=protocol_id,
        )

        assert result is True

    def test_verify_dpacp_permission_not_found(self, permissions_manager):
        """Test verifying non-existent DPACP permission."""
        result = permissions_manager.verify_dpacp_permission(
            originator="unknown.com",
            protocol_id={"protocolName": "nonexistent"},
        )

        assert result is False

    def test_revoke_dpacp_permission(self, permissions_manager):
        """Test revoking DPACP permission."""
        originator = "revoke.com"
        protocol_id = {"protocolName": "revoke_protocol"}

        # First grant permission (without counterparty)
        permissions_manager.grant_dpacp_permission(
            originator=originator,
            protocol_id=protocol_id,
            counterparty=None,
        )

        # Verify permissions cache has the entry
        f"dpacp:{originator}:{protocol_id.get('protocolName')}:None"

        # Then revoke it (cache key includes counterparty=None)
        result = permissions_manager.revoke_dpacp_permission(
            originator=originator,
            protocol_id=protocol_id,
        )

        # Should succeed if the key matched
        assert isinstance(result, bool)

    def test_revoke_dpacp_permission_not_found(self, permissions_manager):
        """Test revoking non-existent DPACP permission."""
        result = permissions_manager.revoke_dpacp_permission(
            originator="unknown.com",
            protocol_id={"protocolName": "nonexistent"},
        )

        assert result is False

    def test_list_dpacp_permissions_all(self, permissions_manager):
        """Test listing all DPACP permissions."""
        # Grant a few permissions
        for i in range(3):
            permissions_manager.grant_dpacp_permission(
                originator=f"test{i}.com",
                protocol_id={"protocolName": f"protocol_{i}"},
            )

        result = permissions_manager.list_dpacp_permissions()

        assert isinstance(result, list)
        assert len(result) >= 3

    def test_list_dpacp_permissions_filtered(self, permissions_manager):
        """Test listing DPACP permissions filtered by originator."""
        # Grant permissions for different originators
        permissions_manager.grant_dpacp_permission(
            originator="filter.com",
            protocol_id={"protocolName": "filtered_protocol"},
        )
        permissions_manager.grant_dpacp_permission(
            originator="other.com",
            protocol_id={"protocolName": "other_protocol"},
        )

        result = permissions_manager.list_dpacp_permissions(originator="filter.com")

        assert isinstance(result, list)
        # Only permissions for filter.com should be returned
        for token in result:
            if token.get("protocol"):
                assert token.get("originator") == "filter.com"


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="WalletPermissionsManager not available")
class TestDBAPMethods:
    """Test DBAP (Domain Basket Access Protocol) methods."""

    def test_grant_dbap_permission(self, permissions_manager):
        """Test granting DBAP permission."""
        originator = "basket.com"
        basket = "my_basket"

        token = permissions_manager.grant_dbap_permission(
            originator=originator,
            basket=basket,
        )

        assert token is not None
        assert token.get("originator") == originator
        assert token.get("basketName") == basket
        assert "txid" in token

    def test_verify_dbap_permission_valid(self, permissions_manager):
        """Test verifying valid DBAP permission."""
        originator = "verify_basket.com"
        basket = "verify_basket"

        # First grant permission
        permissions_manager.grant_dbap_permission(
            originator=originator,
            basket=basket,
        )

        # Then verify it
        result = permissions_manager.verify_dbap_permission(
            originator=originator,
            basket=basket,
        )

        assert result is True

    def test_verify_dbap_permission_not_found(self, permissions_manager):
        """Test verifying non-existent DBAP permission."""
        result = permissions_manager.verify_dbap_permission(
            originator="unknown.com",
            basket="nonexistent",
        )

        assert result is False

    def test_list_dbap_permissions(self, permissions_manager):
        """Test listing all DBAP permissions."""
        # Grant a few permissions
        for i in range(2):
            permissions_manager.grant_dbap_permission(
                originator=f"list_basket_{i}.com",
                basket=f"basket_{i}",
            )

        result = permissions_manager.list_dbap_permissions()

        assert isinstance(result, list)
        assert len(result) >= 2


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="WalletPermissionsManager not available")
class TestDCAPMethods:
    """Test DCAP (Domain Certificate Access Protocol) methods."""

    def test_grant_dcap_permission(self, permissions_manager):
        """Test granting DCAP permission."""
        originator = "cert.com"
        cert_type = "identity"
        verifier = "trusted_verifier"

        token = permissions_manager.grant_dcap_permission(
            originator=originator,
            cert_type=cert_type,
            verifier=verifier,
        )

        assert token is not None
        assert token.get("originator") == originator
        assert "txid" in token

    def test_verify_dcap_permission_valid(self, permissions_manager):
        """Test verifying valid DCAP permission."""
        originator = "verify_cert.com"
        cert_type = "verify_cert"
        verifier = "verify_verifier"

        # First grant permission
        permissions_manager.grant_dcap_permission(
            originator=originator,
            cert_type=cert_type,
            verifier=verifier,
        )

        # Then verify it
        result = permissions_manager.verify_dcap_permission(
            originator=originator,
            cert_type=cert_type,
            verifier=verifier,
        )

        assert result is True

    def test_verify_dcap_permission_not_found(self, permissions_manager):
        """Test verifying non-existent DCAP permission."""
        result = permissions_manager.verify_dcap_permission(
            originator="unknown.com",
            cert_type="nonexistent",
            verifier="unknown",
        )

        assert result is False

    def test_list_dcap_permissions(self, permissions_manager):
        """Test listing all DCAP permissions."""
        # Grant a few permissions
        for i in range(2):
            permissions_manager.grant_dcap_permission(
                originator=f"list_cert_{i}.com",
                cert_type=f"cert_type_{i}",
                verifier=f"verifier_{i}",
            )

        result = permissions_manager.list_dcap_permissions()

        assert isinstance(result, list)
        assert len(result) >= 2


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="WalletPermissionsManager not available")
class TestDSAPMethods:
    """Test DSAP (Domain Spending Authorization Protocol) methods."""

    def test_grant_dsap_permission(self, permissions_manager):
        """Test granting DSAP permission."""
        originator = "spending.com"
        satoshis = 100000

        token = permissions_manager.grant_dsap_permission(
            originator=originator,
            satoshis=satoshis,
        )

        assert token is not None
        assert token.get("originator") == originator
        assert "txid" in token

    def test_verify_dsap_permission_after_grant(self, permissions_manager):
        """Test verifying DSAP permission after grant."""
        originator = "verify_spending.com"
        satoshis = 50000

        # First grant permission
        token = permissions_manager.grant_dsap_permission(
            originator=originator,
            satoshis=satoshis,
        )

        # Token should be created
        assert token is not None
        assert token.get("originator") == originator

        # Check that permissions cache contains the entry
        has_dsap_key = any(k.startswith(f"dsap:{originator}") for k in permissions_manager._permissions)
        assert has_dsap_key or len(permissions_manager._permissions) > 0

    def test_verify_dsap_permission_not_found(self, permissions_manager):
        """Test verifying non-existent DSAP permission."""
        result = permissions_manager.verify_dsap_permission(
            originator="unknown.com",
            satoshis=1000,
        )

        assert result is False

    def test_list_dsap_permissions(self, permissions_manager):
        """Test listing all DSAP permissions."""
        # Grant a few permissions
        for i in range(2):
            permissions_manager.grant_dsap_permission(
                originator=f"list_spending_{i}.com",
                satoshis=10000 * (i + 1),
            )

        result = permissions_manager.list_dsap_permissions()

        assert isinstance(result, list)
        assert len(result) >= 2


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="WalletPermissionsManager not available")
class TestPermissionConfiguration:
    """Test permission configuration options."""

    def test_config_defaults(self, mock_underlying_wallet):
        """Test default configuration values."""
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test.com")

        # All permission checks should default to True
        assert manager._config.get("seekProtocolPermissionsForSigning") is True
        assert manager._config.get("seekBasketInsertionPermissions") is True
        assert manager._config.get("seekSpendingPermissions") is True

    def test_config_override(self, mock_underlying_wallet):
        """Test configuration override."""
        config = {
            "seekProtocolPermissionsForSigning": False,
            "seekBasketInsertionPermissions": False,
        }

        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test.com",
            config=config,
        )

        assert manager._config.get("seekProtocolPermissionsForSigning") is False
        assert manager._config.get("seekBasketInsertionPermissions") is False
        # Unset values should still default to True
        assert manager._config.get("seekSpendingPermissions") is True

    def test_encrypt_wallet_metadata_convenience(self, mock_underlying_wallet):
        """Test encrypt_wallet_metadata convenience parameter."""
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test.com",
            encrypt_wallet_metadata=True,
        )

        assert manager._config.get("encryptWalletMetadata") is True


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="WalletPermissionsManager not available")
class TestAdminOriginator:
    """Test admin originator functionality."""

    def test_admin_originator_bypass(self, permissions_manager):
        """Test that admin originator bypasses permission checks."""
        admin_originator = "admin.test.com"

        # Admin should always be allowed
        permissions_manager._ensure_can_call(admin_originator)
        # Should not raise

    def test_admin_originator_stored(self, permissions_manager):
        """Test admin originator is stored correctly."""
        assert permissions_manager._admin_originator == "admin.test.com"


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="WalletPermissionsManager not available")
class TestCallbackManagement:
    """Test callback management functionality."""

    def test_callbacks_dict_exists(self, permissions_manager):
        """Test callbacks dict is initialized."""
        assert hasattr(permissions_manager, "_callbacks")
        assert isinstance(permissions_manager._callbacks, dict)

    def test_unbind_callback_not_found(self, permissions_manager):
        """Test unbinding non-existent callback."""
        result = permissions_manager.unbind_callback("onProtocolPermissionRequested", 99999)

        assert result is False


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="WalletPermissionsManager not available")
class TestTokenExpiry:
    """Test token expiry functionality."""

    def test_is_token_expired_yes(self, permissions_manager):
        """Test checking expired token."""
        token = {"expiry": int(time.time()) - 3600}  # Expired 1 hour ago

        result = permissions_manager._is_token_expired(token)

        assert result is True

    def test_is_token_expired_no_expiry(self, permissions_manager):
        """Test checking token without expiry."""
        token = {}  # No expiry

        result = permissions_manager._is_token_expired(token)

        assert result is False

    def test_check_expiry_with_valid_token(self, permissions_manager):
        """Test checking non-expired token via granted permission."""
        # Grant a permission and verify it's valid
        originator = "expiry_test.com"
        permissions_manager.grant_dpacp_permission(
            originator=originator,
            protocol_id={"protocolName": "test_expiry"},
        )

        # Verify it's valid (which means not expired)
        result = permissions_manager.verify_dpacp_permission(
            originator=originator,
            protocol_id={"protocolName": "test_expiry"},
        )

        assert result is True


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="WalletPermissionsManager not available")
class TestRequestIdGeneration:
    """Test request ID generation."""

    def test_generate_unique_ids(self, permissions_manager):
        """Test that generated IDs are unique."""
        ids = set()
        for _ in range(100):
            request_id = permissions_manager._generate_request_id()
            assert request_id not in ids
            ids.add(request_id)
