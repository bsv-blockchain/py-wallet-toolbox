"""Unit tests for WalletPermissionsManager initialization and configuration.

This module tests the initialization behavior and configuration options
of WalletPermissionsManager.

Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.initialization.test.ts
"""

from unittest.mock import AsyncMock, Mock

try:
    from bsv.wallet.wallet_interface import WalletInterface

    from bsv_wallet_toolbox.manager.wallet_permissions_manager import PermissionsManagerConfig, WalletPermissionsManager

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    WalletPermissionsManager = None
    WalletInterface = None
    PermissionsManagerConfig = None


class TestWalletPermissionsManagerInitialization:
    """Test suite for WalletPermissionsManager initialization and configuration.

    Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.initialization.test.ts
               describe('WalletPermissionsManager - Initialization & Configuration')
    """

    def test_should_initialize_with_default_config_if_none_is_provided(self) -> None:
        """Given: No config provided to constructor
           When: Create WalletPermissionsManager
           Then: All config flags default to True

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.initialization.test.ts
                   test('should initialize with default config if none is provided')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)

        # When
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet, admin_originator="admin.domain.com"
        )

        # Then - manager internally defaults all config flags to true
        internal_config = getattr(manager, "_config", {})
        assert internal_config.get("seekProtocolPermissionsForSigning") is True
        assert internal_config.get("seekProtocolPermissionsForEncrypting") is True
        assert internal_config.get("seekPermissionsForIdentityKeyRevelation") is True
        assert internal_config.get("encryptWalletMetadata") is True

        # The manager should store the admin originator
        admin = getattr(manager, "_admin_originator", None)
        assert admin == "admin.domain.com"

    def test_should_initialize_with_partial_config_overrides_merging_with_defaults(self) -> None:
        """Given: Partial config provided (some flags overridden)
           When: Create WalletPermissionsManager
           Then: Overridden flags set correctly, rest remain default

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.initialization.test.ts
                   test('should initialize with partial config overrides, merging with defaults')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        partial_config = {
            "seekProtocolPermissionsForSigning": False,
            "encryptWalletMetadata": False,
            # The rest remain default = true
        }

        # When
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet, admin_originator="admin.domain.com", config=partial_config
        )

        # Then - overridden to false
        internal_config = getattr(manager, "_config", {})
        assert internal_config.get("seekProtocolPermissionsForSigning") is False
        assert internal_config.get("encryptWalletMetadata") is False

        # Remaining defaults still true
        assert internal_config.get("seekBasketInsertionPermissions") is True
        assert internal_config.get("seekSpendingPermissions") is True

    def test_should_initialize_with_all_config_flags_set_to_false(self) -> None:
        """Given: All config flags set to False
           When: Create WalletPermissionsManager
           Then: All flags are False

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.initialization.test.ts
                   test('should initialize with all config flags set to false')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        all_false = {
            "seekProtocolPermissionsForSigning": False,
            "seekProtocolPermissionsForEncrypting": False,
            "seekProtocolPermissionsForHMAC": False,
            "seekPermissionsForKeyLinkageRevelation": False,
            "seekPermissionsForPublicKeyRevelation": False,
            "seekPermissionsForIdentityKeyRevelation": False,
            "seekPermissionsForIdentityResolution": False,
            "seekBasketInsertionPermissions": False,
            "seekBasketRemovalPermissions": False,
            "seekBasketListingPermissions": False,
            "seekPermissionWhenApplyingActionLabels": False,
            "seekPermissionWhenListingActionsByLabel": False,
            "seekCertificateDisclosurePermissions": False,
            "seekCertificateAcquisitionPermissions": False,
            "seekCertificateRelinquishmentPermissions": False,
            "seekCertificateListingPermissions": False,
            "encryptWalletMetadata": False,
            "seekSpendingPermissions": False,
            "differentiatePrivilegedOperations": False,
        }

        # When
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet, admin_originator="admin.domain.com", config=all_false
        )

        # Then
        internal_config = getattr(manager, "_config", {})
        for key, value in all_false.items():
            assert internal_config.get(key) == value

    def test_should_consider_calls_from_the_adminoriginator_as_admin_bypassing_checks(self) -> None:
        """Given: Manager with admin originator set
           When: Call method with admin originator
           Then: Bypasses all permission checks

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.initialization.test.ts
                   test('should consider calls from the adminOriginator as admin, bypassing checks')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = AsyncMock(return_value={"txid": "admin-tx"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet, admin_originator="admin.domain.com"
        )

        # When - call with admin originator
        result = manager.create_action(
            {
                "description": "Insertion to user basket",
                "outputs": [
                    {
                        "lockingScript": "abcd",
                        "satoshis": 1000,
                        "outputDescription": "some out desc",
                        "basket": "some-user-basket",
                    }
                ],
            },
            "admin.domain.com",
        )

        # Then - bypassed checks, call succeeded
        assert result is not None
        assert mock_underlying_wallet.create_action.call_count == 1

        # activeRequests map should be empty
        active_requests = getattr(manager, "_active_requests", {})
        assert len(active_requests) == 0

    async def test_should_skip_protocol_permission_checks_for_signing_if_seekprotocolpermissionsforsigning_false(
        self,
    ) -> None:
        """Given: Manager with seekProtocolPermissionsForSigning=False
           When: Non-admin creates signature with protocolID
           Then: No permission check, proceeds directly

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.initialization.test.ts
                   test('should skip protocol permission checks for signing if seekProtocolPermissionsForSigning=false')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_signature = AsyncMock(return_value={"signature": "sig"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.domain.com",
            config={"seekProtocolPermissionsForSigning": False},
        )

        # When - non-admin origin attempts createSignature
        await manager.create_signature(
            {"protocolID": [1, "some-protocol"], "privileged": False, "data": [0x01, 0x02], "keyID": "1"},
            "app.nonadmin.com",
        )

        # Then - underlying createSignature is invoked
        assert mock_underlying_wallet.create_signature.call_count == 1

        # The manager's internal request queue should remain empty
        active_requests = getattr(manager, "_active_requests", {})
        assert len(active_requests) == 0

    def test_should_enforce_protocol_permission_checks_for_signing_if_seekprotocolpermissionsforsigning_true(
        self,
    ) -> None:
        """Given: Manager with seekProtocolPermissionsForSigning=True
           When: Non-admin creates signature with protocolID
           Then: Permission check triggered, callback called

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.initialization.test.ts
                   test('should enforce protocol permission checks for signing if seekProtocolPermissionsForSigning=true')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_signature = Mock(return_value={"signature": [1, 2, 3]})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.domain.com",
            config={"seekProtocolPermissionsForSigning": True},
        )

        callback_called = []

        def permission_callback(request) -> None:
            callback_called.append(request)
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onProtocolPermissionRequested", permission_callback)

        # When - non-admin origin tries createSignature
        manager.create_signature(
            {"protocolID": [1, "test-protocol"], "keyID": "1", "data": [0x10, 0x20], "privileged": False},
            "nonadmin.com",
        )

        # Then - callback was triggered and signature was created
        assert len(callback_called) == 1
        assert callback_called[0]["type"] == "protocol"
        mock_underlying_wallet.create_signature.assert_called_once()

    def test_should_skip_basket_insertion_permission_checks_if_seekbasketinsertionpermissions_false(self) -> None:
        """Given: Manager with seekBasketInsertionPermissions=False
           When: Non-admin creates action with basket
           Then: No basket insertion permission check

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.initialization.test.ts
                   test('should skip basket insertion permission checks if seekBasketInsertionPermissions=false')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = AsyncMock(return_value={"txid": "tx1"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.domain.com",
            config={"seekBasketInsertionPermissions": False},
        )

        # Spending authorization is still required, grant it
        def auto_grant_spending(request) -> None:
            # grant_permission is synchronous, no need for create_task
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onSpendingAuthorizationRequested", auto_grant_spending)

        # When - non-admin origin tries to createAction specifying a basket
        manager.create_action(
            {
                "description": "Insert to user basket",
                "outputs": [
                    {
                        "lockingScript": "1234",
                        "satoshis": 888,
                        "basket": "somebasket",
                        "outputDescription": "some out desc",
                    }
                ],
            },
            "some-user.com",
        )

        # Then - no permission request should be queued (spending auth auto-granted)
        active_requests = getattr(manager, "_active_requests", {})
        assert len(active_requests) == 0

    async def test_should_skip_certificate_disclosure_permission_checks_if_seekcertificatedisclosurepermissions_false(
        self,
    ) -> None:
        """Given: Manager with seekCertificateDisclosurePermissions=False
           When: Non-admin discloses certificate
           Then: No disclosure permission check

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.initialization.test.ts
                   test('should skip certificate disclosure permission checks if seekCertificateDisclosurePermissions=false')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.disclose_certificate = AsyncMock(return_value={"certificate": "cert"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.domain.com",
            config={"seekCertificateDisclosurePermissions": False},
        )

        # When
        await manager.disclose_certificate(
            {"certifier": "some-certifier", "type": "some-type", "serialNumber": "123"}, "nonadmin.com"
        )

        # Then
        assert mock_underlying_wallet.disclose_certificate.call_count == 1
        active_requests = getattr(manager, "_active_requests", {})
        assert len(active_requests) == 0

    def test_should_skip_metadata_encryption_if_encryptwalletmetadata_false(self) -> None:
        """Given: Manager with encryptWalletMetadata=False
           When: Create action with metadata
           Then: Metadata not encrypted

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.initialization.test.ts
                   test('should skip metadata encryption if encryptWalletMetadata=false')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = AsyncMock(return_value={"txid": "tx1"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.domain.com",
            config={"encryptWalletMetadata": False},
        )

        # When - admin creates action with metadata
        result = manager.create_action(
            {"description": "Test action", "metadata": {"key": "plaintext-value"}, "outputs": []}, "admin.domain.com"
        )

        # Then - metadata passed through unencrypted
        assert result is not None
        call_args = mock_underlying_wallet.create_action.call_args[0][0]
        assert call_args.get("metadata") == {"key": "plaintext-value"}
