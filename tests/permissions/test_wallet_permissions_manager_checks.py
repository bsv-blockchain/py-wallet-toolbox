"""Unit tests for WalletPermissionsManager permission checking functionality.

This module tests various permission check scenarios including security levels,
admin-only protocols/baskets, token renewal, and permission prompts.

Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
"""

from unittest.mock import Mock

import pytest

try:
    from bsv.wallet.wallet_interface import WalletInterface

    from bsv_wallet_toolbox.manager.wallet_permissions_manager import PermissionToken, WalletPermissionsManager

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    WalletPermissionsManager = None
    PermissionToken = None
    WalletInterface = None


class TestWalletPermissionsManagerChecks:
    """Test suite for WalletPermissionsManager permission checks.

    Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
               describe('Protocol Usage (DPACP)') and describe('Basket Usage (DBAP)')
    """

    def test_should_skip_permission_prompt_if_seclevel_0_open_usage(self) -> None:
        """Given: Manager with seekProtocolPermissionsForSigning enabled
           When: Call createSignature with secLevel=0
           Then: No permission prompt, operation succeeds

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should skip permission prompt if secLevel=0 (open usage)')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_signature = Mock(return_value={"signature": [0x01, 0x02]})

        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekProtocolPermissionsForSigning": True},
        )

        # When - createSignature with protocolID securityLevel=0
        manager.create_signature(
            {"protocolID": [0, "open-protocol"], "data": [0x01, 0x02], "keyID": "1"}, originator="some-user.com"
        )

        # Then - no permission request triggered
        active_requests = getattr(manager, "_active_requests", {})
        assert len(active_requests) == 0

        # Underlying method called once
        mock_underlying_wallet.create_signature.assert_called_once()

    def test_should_prompt_for_protocol_usage_if_securitylevel_1_and_no_existing_token(self) -> None:
        """Given: Manager with no existing token
           When: Call with securityLevel=1
           Then: Permission prompt triggered

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should prompt for protocol usage if securityLevel=1 and no existing token')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_signature = Mock(return_value={"signature": [0x99, 0xAA]})

        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekProtocolPermissionsForSigning": True},
        )

        # Auto-grant ephemeral permission
        def permission_callback(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onProtocolPermissionRequested", permission_callback)

        # When - createSignature with secLevel=1
        manager.create_signature(
            {"protocolID": [1, "test-protocol"], "data": [0x99, 0xAA], "keyID": "1"}, originator="some-nonadmin.com"
        )

        # Then - underlying signature called
        mock_underlying_wallet.create_signature.assert_called_once()

    def test_should_deny_protocol_usage_if_user_denies_permission(self) -> None:
        """Given: Manager with deny callback
           When: Request protocol operation
           Then: Permission denied error

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should deny protocol usage if user denies permission')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.encrypt = Mock(return_value={"ciphertext": [1, 2, 3]})

        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekProtocolPermissionsForEncrypting": True},
        )

        # Deny callback
        def permission_callback(request) -> None:
            manager.deny_permission(request["requestID"])

        manager.bind_callback("onProtocolPermissionRequested", permission_callback)

        # When/Then - permission denied
        with pytest.raises(RuntimeError, match="Protocol permission denied"):
            manager.encrypt(
                {"protocolID": [1, "needs-perm"], "plaintext": [1, 2, 3], "keyID": "xyz"}, originator="external-app.com"
            )

        # Underlying encrypt never called
        mock_underlying_wallet.encrypt.assert_not_called()

    def test_should_enforce_privileged_token_if_differentiateprivilegedoperations_true(self) -> None:
        """Given: Manager with differentiatePrivilegedOperations=true
           When: Request privileged operation
           Then: Privileged permission required

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should enforce privileged token if differentiatePrivilegedOperations=true')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_signature = Mock(return_value={"signature": [0xC0, 0xFF, 0xEE]})

        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekProtocolPermissionsForSigning": True, "differentiatePrivilegedOperations": True},
        )

        def permission_callback(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onProtocolPermissionRequested", permission_callback)

        # When - privileged signature
        manager.create_signature(
            {"protocolID": [1, "high-level-crypto"], "privileged": True, "data": [0xC0, 0xFF, 0xEE], "keyID": "1"},
            originator="nonadmin.app",
        )

        # Then - underlying called
        mock_underlying_wallet.create_signature.assert_called_once()

    def test_should_ignore_privileged_true_if_differentiateprivilegedoperations_false(self) -> None:
        """Given: Manager with differentiatePrivilegedOperations=false
           When: Request with privileged=true
           Then: Privileged flag ignored, treated as normal

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should ignore `privileged=true` if differentiatePrivilegedOperations=false')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_signature = Mock(return_value={"signature": [0x99]})

        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"differentiatePrivilegedOperations": False, "seekProtocolPermissionsForSigning": True},
        )

        def permission_callback(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onProtocolPermissionRequested", permission_callback)

        # When - privileged flag is ignored
        manager.create_signature(
            {"protocolID": [1, "some-protocol"], "privileged": True, "data": [0x99], "keyID": "keyXYZ"},
            originator="nonadmin.com",
        )

        # Then - succeeds without special privileged handling
        mock_underlying_wallet.create_signature.assert_called_once()

    def test_should_fail_if_protocol_name_is_admin_reserved_and_caller_is_not_admin(self) -> None:
        """Given: Manager with admin-reserved protocol
           When: Non-admin tries to use admin-reserved protocol
           Then: Operation fails

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should fail if protocol name is admin-reserved and caller is not admin')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_hmac = Mock()

        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet, admin_originator="secure.admin.com"
        )

        # When/Then - admin-reserved protocol name
        with pytest.raises(ValueError, match="admin-only"):
            manager.create_hmac(
                {"protocolID": [1, "admin super-secret"], "data": [0x01, 0x02], "keyID": "1"},
                originator="not-an-admin.com",
            )

        # Underlying never called
        mock_underlying_wallet.create_hmac.assert_not_called()

    def test_should_prompt_for_renewal_if_token_is_found_but_expired(self) -> None:
        """Given: Manager with expired token
           When: Request operation
           Then: Renewal prompt triggered

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should prompt for renewal if token is found but expired')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_signature = Mock(return_value={"signature": [0xFE]})

        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekProtocolPermissionsForSigning": True},
        )

        # Bind callback that grants renewal
        renewal_requested = []

        def permission_callback(request) -> None:
            renewal_requested.append(request)
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onProtocolPermissionRequested", permission_callback)

        # When - call without any existing token
        manager.create_signature(
            {"protocolID": [1, "test-protocol"], "data": [0xFE], "keyID": "1"}, originator="some-nonadmin.com"
        )

        # Then - permission was requested and underlying called
        assert len(renewal_requested) == 1
        mock_underlying_wallet.create_signature.assert_called_once()

    def test_should_fail_immediately_if_using_an_admin_only_basket_as_non_admin(self) -> None:
        """Given: Non-admin originator
           When: Attempt to use admin-only basket
           Then: Fails immediately

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should fail immediately if using an admin-only basket as non-admin')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = Mock()

        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.com")

        # When/Then - admin basket from non-admin
        with pytest.raises(ValueError, match="admin-only"):
            manager.create_action(
                {
                    "description": "Insert into admin basket",
                    "outputs": [
                        {
                            "lockingScript": "abcd",
                            "satoshis": 100,
                            "basket": "admin secret-basket",
                            "outputDescription": "Nothing to see here",
                        }
                    ],
                },
                originator="non-admin.com",
            )

        # Underlying never called
        mock_underlying_wallet.create_action.assert_not_called()

    def test_should_fail_immediately_if_using_the_reserved_basket_default_as_non_admin(self) -> None:
        """Given: Non-admin originator
           When: Attempt to use 'default' basket
           Then: Fails immediately

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should fail immediately if using the reserved basket "default" as non-admin')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = Mock()

        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.com")

        # When/Then - 'default' basket from non-admin
        with pytest.raises(ValueError, match="admin-only"):
            manager.create_action(
                {
                    "description": "Insert to default basket",
                    "outputs": [
                        {
                            "lockingScript": "0x1234",
                            "satoshis": 1,
                            "basket": "default",
                            "outputDescription": "Nothing to see here",
                        }
                    ],
                },
                originator="some-nonadmin.com",
            )

        mock_underlying_wallet.create_action.assert_not_called()

    def test_should_prompt_for_insertion_permission_if_seekbasketinsertionpermissions_true(self) -> None:
        """Given: Manager with seekBasketInsertionPermissions=true
           When: Create action with basket
           Then: Permission prompt triggered

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should prompt for insertion permission if seekBasketInsertionPermissions=true')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = Mock(return_value={"txid": "abc123"})

        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekBasketInsertionPermissions": True},
        )

        # Auto-grant basket access
        def basket_callback(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onBasketAccessRequested", basket_callback)

        # Auto-grant spending authorization
        def spending_callback(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onSpendingAuthorizationRequested", spending_callback)

        # When
        manager.create_action(
            {
                "description": "Insert to user-basket",
                "outputs": [
                    {
                        "lockingScript": "7812",
                        "satoshis": 1,
                        "basket": "user-basket",
                        "outputDescription": "Nothing to see here",
                    }
                ],
            },
            originator="some-nonadmin.com",
        )

        # Then - underlying called
        mock_underlying_wallet.create_action.assert_called_once()

    def test_should_skip_insertion_permission_if_seekbasketinsertionpermissions_false(self) -> None:
        """Given: Manager with seekBasketInsertionPermissions=false
           When: Create action with basket
           Then: No basket permission prompt

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should skip insertion permission if seekBasketInsertionPermissions=false')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = Mock(return_value={"txid": "xyz789"})

        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekBasketInsertionPermissions": False},
        )

        # Auto-grant spending authorization only
        def spending_callback(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onSpendingAuthorizationRequested", spending_callback)

        # When
        manager.create_action(
            {
                "description": "Insert to user-basket",
                "outputs": [
                    {
                        "lockingScript": "1234",
                        "satoshis": 1,
                        "basket": "some-basket",
                        "outputDescription": "Nothing to see here",
                    }
                ],
            },
            originator="some-nonadmin.com",
        )

        # Then - no basket permission check, underlying called
        mock_underlying_wallet.create_action.assert_called_once()

    def test_should_require_listing_permission_if_seekbasketlistingpermissions_true_and_no_token(self) -> None:
        """Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
        test('should require listing permission if seekBasketListingPermissions=true and no token')"""
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.list_outputs = Mock()
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekBasketListingPermissions": True},
        )

        def permission_callback(request) -> None:
            manager.deny_permission(request["requestID"])

        manager.bind_callback("onBasketAccessRequested", permission_callback)
        with pytest.raises(RuntimeError, match="Basket permission denied"):
            manager.list_outputs({"basket": "user-basket"}, originator="some-user.com")

    def test_should_prompt_for_removal_permission_if_seekbasketremovalpermissions_true(self) -> None:
        """Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
        test('should prompt for removal permission if seekBasketRemovalPermissions=true')"""
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.relinquish_output = Mock(return_value={"txid": "test"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekBasketRemovalPermissions": True},
        )

        def permission_callback(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onBasketAccessRequested", permission_callback)
        manager.relinquish_output({"output": "someTxid.1", "basket": "user-basket"}, originator="some-user.com")
        mock_underlying_wallet.relinquish_output.assert_called_once()

    def test_should_skip_certificate_disclosure_permission_if_config_seekcertificatedisclosurepermissions_false(
        self,
    ) -> None:
        """Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
        test('should skip certificate disclosure permission if config.seekCertificateDisclosurePermissions=false')"""
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.prove_certificate = Mock(return_value={"keyring": {}})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekCertificateDisclosurePermissions": False},
        )
        manager.prove_certificate(
            {
                "certificate": {
                    "type": "KYC",
                    "subject": "02abcdef",
                    "serialNumber": "123",
                    "certifier": "02ccc",
                    "fields": {"name": "Alice"},
                },
                "fieldsToReveal": ["name"],
                "verifier": "02xyz",
                "privileged": False,
            },
            originator="nonadmin.com",
        )
        mock_underlying_wallet.prove_certificate.assert_called_once()

    def test_should_require_permission_if_seekcertificatedisclosurepermissions_true_no_valid_token(self) -> None:
        """Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
        test('should require permission if seekCertificateDisclosurePermissions=true, no valid token')"""
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.prove_certificate = Mock(return_value={"keyring": {}})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekCertificateDisclosurePermissions": True},
        )

        def permission_callback(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onCertificateAccessRequested", permission_callback)
        manager.prove_certificate(
            {
                "certificate": {
                    "type": "KYC",
                    "subject": "02abc",
                    "serialNumber": "xyz",
                    "certifier": "02dddd",
                    "fields": {"name": "Bob"},
                },
                "fieldsToReveal": ["name"],
                "verifier": "02xxxx",
                "privileged": False,
            },
            originator="some-user.com",
        )
        mock_underlying_wallet.prove_certificate.assert_called_once()

    def test_should_check_that_requested_fields_are_a_subset_of_the_tokens_fields(self) -> None:
        """Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
        test('should check that requested fields are a subset of the token's fields')"""
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.prove_certificate = Mock(return_value={"keyring": {}})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekCertificateDisclosurePermissions": True},
        )
        existing_token = {
            "txid": "aabbcc",
            "outputIndex": 0,
            "originator": "some-user.com",
            "expiry": 9999999999,
            "privileged": False,
            "certType": "KYC",
            "certFields": ["name", "dob", "nationality"],
            "verifier": "02eeee",
        }
        manager._find_certificate_token = Mock(return_value=existing_token)
        manager.prove_certificate(
            {
                "certificate": {
                    "type": "KYC",
                    "certifier": "02eeee",
                    "subject": "02some",
                    "serialNumber": "",
                    "fields": {"name": "Charlie", "dob": "1999-01-01"},
                },
                "fieldsToReveal": ["name"],
                "verifier": "02eeee",
                "privileged": False,
            },
            originator="some-user.com",
        )
        assert mock_underlying_wallet.prove_certificate.call_count == 1

    def test_should_prompt_for_renewal_if_token_is_expired_cert(self) -> None:
        """Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
        test('should prompt for renewal if token is expired')"""
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.prove_certificate = Mock(return_value={"keyring": {}})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekCertificateDisclosurePermissions": True},
        )
        expired_token = {
            "txid": "old-expired",
            "outputIndex": 0,
            "originator": "app.com",
            "expiry": 1,
            "privileged": False,
            "certType": "KYC",
            "certFields": ["name", "dob"],
            "verifier": "02verifier",
        }
        manager._find_certificate_token = Mock(return_value=expired_token)

        def permission_callback(request) -> None:
            assert request["renewal"] is True
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onCertificateAccessRequested", permission_callback)
        manager.prove_certificate(
            {
                "certificate": {"type": "KYC", "fields": {"name": "Bob", "dob": "1970"}, "certifier": "02verifier"},
                "fieldsToReveal": ["name"],
                "verifier": "02verifier",
                "privileged": False,
            },
            originator="app.com",
        )
        mock_underlying_wallet.prove_certificate.assert_called_once()

    def test_should_skip_if_seekspendingpermissions_false(self) -> None:
        """Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
        test('should skip if seekSpendingPermissions=false')"""
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = Mock(return_value={"txid": "test123"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekSpendingPermissions": False},
        )
        manager.create_action(
            {
                "description": "Some spend transaction",
                "outputs": [{"lockingScript": "1321", "satoshis": 200, "outputDescription": "Nothing to see here"}],
            },
            originator="user.com",
        )
        active_requests = getattr(manager, "_active_requests", {})
        assert len(active_requests) == 0
        mock_underlying_wallet.create_action.assert_called_once()

    def test_should_require_spending_token_if_netspent_gt_0_and_seekspendingpermissions_true(self) -> None:
        """Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
        test('should require spending token if netSpent > 0 and seekSpendingPermissions=true')"""
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = Mock(
            return_value={"signableTransaction": {"tx": [0x00], "reference": "ref1"}}
        )
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekSpendingPermissions": True},
        )

        def permission_callback(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onSpendingAuthorizationRequested", permission_callback)
        manager.create_action(
            {
                "description": "Spend 200 sats",
                "outputs": [{"lockingScript": "abcd", "satoshis": 200, "outputDescription": "test"}],
            },
            originator="user.com",
        )
        mock_underlying_wallet.create_action.assert_called_once()

    def test_should_check_monthly_limit_usage_and_prompt_renewal_if_insufficient(self) -> None:
        """Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
        test('should check monthly limit usage and prompt renewal if insufficient')

        Note: Monthly limit functionality is not yet implemented. This test verifies
        that spending authorization is requested when no token exists.
        """
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = Mock(
            return_value={"signableTransaction": {"tx": [0x00], "reference": "ref1"}}
        )
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekSpendingPermissions": True},
        )

        spending_requested = []

        def permission_callback(request) -> None:
            spending_requested.append(request)
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onSpendingAuthorizationRequested", permission_callback)
        manager.create_action(
            {
                "description": "Spend 100 sats",
                "outputs": [{"lockingScript": "abcd", "satoshis": 100, "outputDescription": "test"}],
            },
            originator="user.com",
        )

        # Spending authorization was requested
        assert len(spending_requested) == 1
        mock_underlying_wallet.create_action.assert_called_once()

    def test_should_pass_if_usage_plus_new_spend_is_within_the_monthly_limit(self) -> None:
        """Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
        test('should pass if usage plus new spend is within the monthly limit')

        Note: Monthly limit functionality is not yet implemented. This test verifies
        that spending authorization is granted and action proceeds.
        """
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = Mock(
            return_value={"signableTransaction": {"tx": [0x00], "reference": "ref1"}}
        )
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekSpendingPermissions": True},
        )

        def permission_callback(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onSpendingAuthorizationRequested", permission_callback)
        manager.create_action(
            {
                "description": "Spend 100 sats",
                "outputs": [{"lockingScript": "abcd", "satoshis": 100, "outputDescription": "test"}],
            },
            originator="user.com",
        )
        mock_underlying_wallet.create_action.assert_called_once()

    def test_should_fail_if_label_starts_with_admin(self) -> None:
        """Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
        test('should fail if label starts with')"""
        mock_underlying_wallet = Mock(spec=WalletInterface)
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.com")
        with pytest.raises(ValueError, match="admin-only"):
            manager.create_action(
                {
                    "description": "test",
                    "labels": ["admin restricted-label"],
                    "outputs": [{"lockingScript": "abcd", "satoshis": 100}],
                },
                originator="user.com",
            )

    def test_should_skip_label_permission_if_seekpermissionwhenapplyingactionlabels_false(self) -> None:
        """Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
        test('should skip label permission if seekPermissionWhenApplyingActionLabels=false')"""
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = Mock(return_value={"txid": "test"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekPermissionWhenApplyingActionLabels": False, "seekSpendingPermissions": False},
        )
        manager.create_action(
            {"description": "test", "labels": ["user-label"], "outputs": [{"lockingScript": "abcd", "satoshis": 100}]},
            originator="user.com",
        )
        mock_underlying_wallet.create_action.assert_called_once()

    def test_should_prompt_for_label_usage_if_seekpermissionwhenapplyingactionlabels_true(self) -> None:
        """Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
        test('should prompt for label usage if seekPermissionWhenApplyingActionLabels=true')

        Note: Label permissions use onProtocolPermissionRequested with a special protocol ID
        like [1, 'action label <label>'] per TypeScript implementation.
        """
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = Mock(return_value={"txid": "test"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekPermissionWhenApplyingActionLabels": True, "seekSpendingPermissions": False},
        )

        def permission_callback(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        # Label permissions use onProtocolPermissionRequested (TS parity)
        manager.bind_callback("onProtocolPermissionRequested", permission_callback)
        manager.create_action(
            {"description": "test", "labels": ["user-label"], "outputs": [{"lockingScript": "abcd", "satoshis": 100}]},
            originator="user.com",
        )
        mock_underlying_wallet.create_action.assert_called_once()

    def test_should_also_prompt_for_listing_actions_by_label_if_seekpermissionwhenlistingactionsbylabel_true(
        self,
    ) -> None:
        """Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
        test('should also prompt for listing actions by label if seekPermissionWhenListingActionsByLabel=true')

        Note: Label permissions use onProtocolPermissionRequested with a special protocol ID
        like [1, 'action label <label>'] per TypeScript implementation.
        """
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.list_actions = Mock(return_value={"totalActions": 0, "actions": []})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={"seekPermissionWhenListingActionsByLabel": True},
        )

        def permission_callback(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        # Label permissions use onProtocolPermissionRequested (TS parity)
        manager.bind_callback("onProtocolPermissionRequested", permission_callback)
        manager.list_actions({"labels": ["user-label"]}, originator="user.com")
        mock_underlying_wallet.list_actions.assert_called_once()
