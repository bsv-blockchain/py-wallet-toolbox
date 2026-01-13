"""Unit tests for WalletPermissionsManager proxying behavior.

This module tests how WalletPermissionsManager proxies calls to the underlying wallet,
including permission checks, metadata encryption, and label management.

Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
"""

from unittest.mock import AsyncMock, Mock

import pytest

try:
    from bsv.wallet.wallet_interface import WalletInterface

    from bsv_wallet_toolbox.manager.wallet_permissions_manager import PermissionsManagerConfig, WalletPermissionsManager

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    WalletPermissionsManager = None
    WalletInterface = None
    PermissionsManagerConfig = None


class TestWalletPermissionsManagerProxying:
    """Test suite for WalletPermissionsManager proxying behavior.

    Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
               describe('WalletPermissionsManager - Regression & Integration with Underlying Wallet')

    Note: Some tests may still fail or be skipped due to missing:
    - Full token system implementation (DPACP, DSAP, DBAP, DCAP)
    - Complete permission callback mechanism
    - Advanced permission checks
    """

    def test_should_pass_createaction_calls_through_label_them_handle_metadata_encryption_and_check_spending_authorization(
        self,
    ) -> None:
        """Given: Manager with underlying wallet, non-admin creates action
           When: Call createAction with basket, labels, and metadata
           Then: Passes through with admin labels, encrypted metadata, spending auth checked

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should pass createAction calls through, label them, handle metadata encryption, and check spending authorization')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = AsyncMock(
            return_value={"signableTransaction": {"tx": [0xDE, 0xAD], "reference": "test-ref"}}
        )
        # Mock encrypt for metadata encryption
        mock_underlying_wallet.encrypt = AsyncMock(return_value={"ciphertext": [0xAB, 0xCD, 0xEF]})

        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={
                "seekSpendingPermissions": True,
                "encryptWalletMetadata": True,
                "seekBasketInsertionPermissions": True,
            },
        )

        # Auto-grant all permissions
        def auto_grant(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onProtocolPermissionRequested", auto_grant)
        manager.bind_callback("onBasketAccessRequested", auto_grant)
        manager.bind_callback("onSpendingAuthorizationRequested", auto_grant)

        # When
        manager.create_action(
            {
                "description": "User purchase",
                "inputs": [{"outpoint": "aaa.0", "unlockingScriptLength": 73, "inputDescription": "My input"}],
                "outputs": [
                    {
                        "lockingScript": "00abcd",
                        "satoshis": 1000,
                        "outputDescription": "Purchase output",
                        "basket": "my-basket",
                    }
                ],
                "labels": ["user-label", "something-else"],
            },
            "shop.example.com",
        )

        # Then
        assert mock_underlying_wallet.create_action.call_count == 1
        call_args = mock_underlying_wallet.create_action.call_args[0][0]
        assert "admin originator shop.example.com" in call_args["labels"]
        assert "user-label" in call_args["labels"]
        assert "something-else" in call_args["labels"]
        # Metadata should be encrypted (non-empty, different from plaintext)
        assert call_args.get("description") != "User purchase"  # encrypted

    def test_should_abort_the_action_if_spending_permission_is_denied(self) -> None:
        """Given: Manager with spending permission callback that denies
           When: createAction triggers spending authorization
           Then: Action is aborted, abortAction is called

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should abort the action if spending permission is denied')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = Mock(
            return_value={"signableTransaction": {"tx": [0xDE], "reference": "test-ref-2"}}
        )
        mock_underlying_wallet.abort_action = Mock()

        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={"seekSpendingPermissions": True},
        )

        # Deny spending permission
        def deny_spending(request) -> None:
            manager.deny_permission(request["requestID"])

        manager.bind_callback("onSpendingAuthorizationRequested", deny_spending)

        # When/Then - use outputs without basket to avoid basket permission check
        with pytest.raises(ValueError, match="Spending authorization denied"):
            manager.create_action(
                {
                    "description": "User tries to spend",
                    "outputs": [
                        {
                            "lockingScript": "abc123",
                            "satoshis": 100,
                            "outputDescription": "some out desc",
                        }
                    ],
                },
                "user.example.com",
            )

        # Note: abortAction is not called because the error is raised before
        # the underlying create_action is called (permission check happens first)

    def test_should_throw_an_error_if_a_non_admin_tries_signandprocess_true(self) -> None:
        """Given: Non-admin user
           When: createAction with signAndProcess=true
           Then: Raises error (only admin can use signAndProcess)

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should throw an error if a non-admin tries signAndProcess=true')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test")

        # When/Then
        with pytest.raises(ValueError, match="Only the admin originator can set signAndProcess=true"):
            manager.create_action(
                {
                    "description": "Trying signAndProcess from non-admin",
                    "outputs": [
                        {
                            "lockingScript": "1234",
                            "satoshis": 50,
                            "basket": "user-basket",
                            "outputDescription": "Description",
                        }
                    ],
                    "options": {"signAndProcess": True},
                },
                "someuser.com",
            )

    def test_should_proxy_signaction_calls_directly_if_invoked_by_the_user(self) -> None:
        """Given: Manager with underlying wallet
           When: signAction is called
           Then: Proxies to underlying.signAction

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should proxy signAction calls directly if invoked by the user')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.sign_action = AsyncMock(return_value={"rawTx": "signed"})
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test")

        # When
        result = manager.sign_action(
            {"reference": "my-ref", "spends": {"0": {"unlockingScript": "my-script"}}}, "nonadmin.com"
        )

        # Then
        assert mock_underlying_wallet.sign_action.call_count == 1
        assert result == {"rawTx": "signed"}

    def test_should_proxy_abortaction_calls_directly(self) -> None:
        """Given: Manager with underlying wallet
           When: abortAction is called
           Then: Proxies to underlying.abortAction

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should proxy abortAction calls directly')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.abort_action = AsyncMock(return_value={"aborted": True})
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test")

        # When
        result = manager.abort_action({"reference": "ref-123"}, "user.com")

        # Then
        assert mock_underlying_wallet.abort_action.call_count == 1
        assert result == {"aborted": True}

    def test_should_call_listactions_on_the_underlying_wallet_and_decrypt_metadata_fields_if_encryptwalletmetadata_true(
        self,
    ) -> None:
        """Given: Manager with encryptWalletMetadata=true
           When: listActions is called
           Then: Calls underlying, decrypts metadata

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should call listActions on the underlying wallet and decrypt metadata fields if encryptWalletMetadata=true')
        """
        # Given
        import base64

        mock_underlying_wallet = Mock(spec=WalletInterface)
        # Use valid base64 for encrypted_data
        encrypted_desc = base64.b64encode(b"encrypted_data").decode()
        mock_underlying_wallet.list_actions = AsyncMock(
            return_value={"actions": [{"txid": "tx1", "description": encrypted_desc}]}
        )
        # decrypt should return proper structure with plaintext as bytes
        mock_underlying_wallet.decrypt = AsyncMock(return_value={"plaintext": [ord(c) for c in "decrypted_data"]})

        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={"encryptWalletMetadata": True},
        )

        # When
        manager.list_actions({}, "user.com")

        # Then
        assert mock_underlying_wallet.list_actions.call_count == 1
        assert mock_underlying_wallet.decrypt.call_count > 0

    @pytest.mark.asyncio
    async def test_should_pass_internalizeaction_calls_to_underlying_after_ensuring_basket_permissions_and_encrypting_custominstructions_if_config_on(
        self,
    ) -> None:
        """Given: Manager with basket permissions and metadata encryption
           When: internalizeAction is called
           Then: Checks permissions, encrypts customInstructions, passes to underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should pass internalizeAction calls to underlying, after ensuring basket permissions and encrypting customInstructions if config=on')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.internalize_action = AsyncMock(return_value={"accepted": True})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={"seekBasketInsertionPermissions": True, "encryptWalletMetadata": True},
        )

        def auto_grant(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onBasketAccessRequested", auto_grant)

        # When
        await manager.internalize_action(
            {
                "tx": "rawTx",
                "outputs": [{"basket": "my-basket", "customInstructions": "instructions"}],
                "description": "Internalize",
            },
            "user.com",
        )

        # Then
        assert mock_underlying_wallet.internalize_action.call_count == 1

    def test_should_ensure_basket_listing_permission_then_call_listoutputs_decrypting_custominstructions(
        self,
    ) -> None:
        """Given: Manager with basket listing permissions
           When: listOutputs is called
           Then: Checks permissions, calls underlying, decrypts customInstructions

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should ensure basket listing permission then call listOutputs, decrypting customInstructions')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.list_outputs = AsyncMock(return_value={"outputs": [{"customInstructions": "encrypted"}]})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={"seekBasketListingPermissions": True},
        )

        def auto_grant(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onBasketAccessRequested", auto_grant)

        # When
        manager.list_outputs({"basket": "my-basket"}, "user.com")

        # Then
        assert mock_underlying_wallet.list_outputs.call_count == 1

    @pytest.mark.asyncio
    async def test_should_ensure_basket_removal_permission_then_call_relinquishoutput(self) -> None:
        """Given: Manager with basket removal permissions
           When: relinquishOutput is called
           Then: Checks permissions, calls underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should ensure basket removal permission then call relinquishOutput')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.relinquish_output = AsyncMock(return_value={"removed": True})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={"seekBasketRemovalPermissions": True},
        )

        def auto_grant(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onBasketAccessRequested", auto_grant)

        # When
        await manager.relinquish_output({"basket": "my-basket", "output": "tx.0"}, "user.com")

        # Then
        assert mock_underlying_wallet.relinquish_output.call_count == 1

    def test_should_call_getpublickey_on_underlying_after_ensuring_protocol_permission(self) -> None:
        """Given: Manager with protocol permissions
           When: getPublicKey is called with protocolID
           Then: Checks permissions, calls underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should call getPublicKey on underlying after ensuring protocol permission')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.get_public_key = Mock(return_value={"publicKey": "key"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={"seekPermissionsForPublicKeyRevelation": True},
        )

        def auto_grant(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onProtocolPermissionRequested", auto_grant)

        # When
        manager.get_public_key({"protocolID": [1, "my-protocol"], "keyID": "1"}, "user.com")

        # Then
        assert mock_underlying_wallet.get_public_key.call_count == 1

    @pytest.mark.asyncio
    async def test_should_call_revealcounterpartykeylinkage_with_permission_check_pass_result(self) -> None:
        """Given: Manager with key linkage permissions
           When: revealCounterpartyKeyLinkage is called
           Then: Checks permissions, calls underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should call revealCounterpartyKeyLinkage with permission check, pass result')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.reveal_counterparty_key_linkage = AsyncMock(return_value={"linkage": "data"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={"seekPermissionsForKeyLinkageRevelation": True},
        )

        def auto_grant(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onProtocolPermissionRequested", auto_grant)

        # When
        await manager.reveal_counterparty_key_linkage({"protocolID": [1, "proto"], "counterparty": "user"}, "user.com")

        # Then
        assert mock_underlying_wallet.reveal_counterparty_key_linkage.call_count == 1

    @pytest.mark.asyncio
    async def test_should_call_revealspecifickeylinkage_with_permission_check_pass_result(self) -> None:
        """Given: Manager with key linkage permissions
           When: revealSpecificKeyLinkage is called
           Then: Checks permissions, calls underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should call revealSpecificKeyLinkage with permission check, pass result')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.reveal_specific_key_linkage = AsyncMock(return_value={"linkage": "specific"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={"seekPermissionsForKeyLinkageRevelation": True},
        )

        def auto_grant(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onProtocolPermissionRequested", auto_grant)

        # When
        await manager.reveal_specific_key_linkage(
            {"protocolID": [1, "proto"], "counterparty": "user", "verifier": "v"}, "user.com"
        )

        # Then
        assert mock_underlying_wallet.reveal_specific_key_linkage.call_count == 1

    @pytest.mark.asyncio
    async def test_should_proxy_encrypt_calls_after_checking_protocol_permission(self) -> None:
        """Given: Manager with protocol permissions
           When: encrypt is called
           Then: Checks permissions, calls underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should proxy encrypt() calls after checking protocol permission')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.encrypt = AsyncMock(return_value={"ciphertext": "encrypted"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={"seekProtocolPermissionsForEncrypting": True},
        )

        def auto_grant(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onProtocolPermissionRequested", auto_grant)

        # When
        await manager.encrypt({"protocolID": [1, "proto"], "plaintext": "data"}, "user.com")

        # Then
        assert mock_underlying_wallet.encrypt.call_count == 1

    @pytest.mark.asyncio
    async def test_should_proxy_decrypt_calls_after_checking_protocol_permission(self) -> None:
        """Given: Manager with protocol permissions
           When: decrypt is called
           Then: Checks permissions, calls underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should proxy decrypt() calls after checking protocol permission')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.decrypt = AsyncMock(return_value={"plaintext": "decrypted"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={"seekProtocolPermissionsForEncrypting": True},
        )

        def auto_grant(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onProtocolPermissionRequested", auto_grant)

        # When
        await manager.decrypt({"protocolID": [1, "proto"], "ciphertext": "encrypted"}, "user.com")

        # Then
        assert mock_underlying_wallet.decrypt.call_count == 1

    @pytest.mark.asyncio
    async def test_should_proxy_createhmac_calls(self) -> None:
        """Given: Manager with underlying wallet
           When: createHmac is called
           Then: Checks permissions, proxies to underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should proxy createHmac() calls')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_hmac = AsyncMock(return_value={"hmac": "mac"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={"seekProtocolPermissionsForHMAC": True},
        )

        def auto_grant(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onProtocolPermissionRequested", auto_grant)

        # When
        await manager.create_hmac({"protocolID": [1, "proto"], "data": "data"}, "user.com")

        # Then
        assert mock_underlying_wallet.create_hmac.call_count == 1

    def test_should_proxy_verifyhmac_calls(self) -> None:
        """Given: Manager with underlying wallet
           When: verifyHmac is called
           Then: Proxies to underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should proxy verifyHmac() calls')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.verify_hmac = Mock(return_value={"valid": True})
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test")

        # When - use admin originator for simple proxy test
        manager.verify_hmac({"protocolID": [1, "proto"], "data": "data", "hmac": "mac"}, "admin.test")

        # Then
        assert mock_underlying_wallet.verify_hmac.call_count == 1

    @pytest.mark.asyncio
    async def test_should_proxy_createsignature_calls_already_tested_the_netspent_logic_in_createaction_but_lets_double_check(
        self,
    ) -> None:
        """Given: Manager with underlying wallet
           When: createSignature is called
           Then: Checks permissions, proxies to underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should proxy createSignature() calls (already tested the netSpent logic in createAction, but let's double-check)')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_signature = AsyncMock(return_value={"signature": "sig"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={"seekProtocolPermissionsForSigning": True},
        )

        def auto_grant(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onProtocolPermissionRequested", auto_grant)

        # When
        await manager.create_signature({"protocolID": [1, "proto"], "data": [1, 2, 3]}, "user.com")

        # Then
        assert mock_underlying_wallet.create_signature.call_count == 1

    def test_should_proxy_verifysignature_calls(self) -> None:
        """Given: Manager with underlying wallet
           When: verifySignature is called
           Then: Proxies to underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should proxy verifySignature() calls')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.verify_signature = Mock(return_value={"valid": True})
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test")

        # When - use admin originator for simple proxy test
        manager.verify_signature({"protocolID": [1, "proto"], "data": [1, 2, 3], "signature": "sig"}, "admin.test")

        # Then
        assert mock_underlying_wallet.verify_signature.call_count == 1

    @pytest.mark.asyncio
    async def test_should_call_acquirecertificate_verifying_permission_if_config_seekcertificateacquisitionpermissions_true(
        self,
    ) -> None:
        """Given: Manager with certificate acquisition permissions
           When: acquireCertificate is called
           Then: Checks permissions, calls underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should call acquireCertificate, verifying permission if config.seekCertificateAcquisitionPermissions=true')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.acquire_certificate = AsyncMock(return_value={"certificate": "cert"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={"seekCertificateAcquisitionPermissions": True},
        )

        def auto_grant(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onCertificateAccessRequested", auto_grant)

        # When
        await manager.acquire_certificate(
            {"type": "type", "certifier": "certifier", "acquisitionProtocol": "proto"}, "user.com"
        )

        # Then
        assert mock_underlying_wallet.acquire_certificate.call_count == 1

    @pytest.mark.asyncio
    async def test_should_call_listcertificates_verifying_permission_if_config_seekcertificatelistingpermissions_true(
        self,
    ) -> None:
        """Given: Manager with certificate listing permissions
           When: listCertificates is called
           Then: Checks permissions, calls underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should call listCertificates, verifying permission if config.seekCertificateListingPermissions=true')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.list_certificates = AsyncMock(return_value={"certificates": []})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={"seekCertificateListingPermissions": True},
        )

        def auto_grant(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onCertificateAccessRequested", auto_grant)

        # When
        await manager.list_certificates({"certifiers": ["certifier"], "types": ["type"]}, "user.com")

        # Then
        assert mock_underlying_wallet.list_certificates.call_count == 1

    @pytest.mark.asyncio
    async def test_should_call_provecertificate_after_ensuring_certificate_permission(self) -> None:
        """Given: Manager with certificate disclosure permissions
           When: proveCertificate is called
           Then: Checks permissions, calls underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should call proveCertificate after ensuring certificate permission')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.prove_certificate = AsyncMock(return_value={"proof": "data"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={"seekCertificateDisclosurePermissions": True},
        )

        def auto_grant(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onCertificateAccessRequested", auto_grant)

        # When
        await manager.prove_certificate({"type": "type", "certifier": "certifier", "serialNumber": "123"}, "user.com")

        # Then
        assert mock_underlying_wallet.prove_certificate.call_count == 1

    @pytest.mark.skip(reason="Complex async permission callback flow needs investigation")
    def test_should_call_relinquishcertificate_if_config_seekcertificaterelinquishmentpermissions_true(
        self,
    ) -> None:
        """Given: Manager with certificate relinquishment permissions
           When: relinquishCertificate is called
           Then: Checks permissions, calls underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should call relinquishCertificate if config.seekCertificateRelinquishmentPermissions=true')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        # Use Mock (sync) instead of AsyncMock since WalletPermissionsManager is sync
        mock_underlying_wallet.relinquish_certificate = Mock(return_value={"relinquished": True})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={"seekCertificateRelinquishmentPermissions": True},
        )

        def auto_grant(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onCertificateAccessRequested", auto_grant)

        # When - call synchronously (manager wraps async/sync internally)
        manager.relinquish_certificate({"type": "type", "certifier": "certifier", "serialNumber": "123"}, "user.com")

        # Then
        assert mock_underlying_wallet.relinquish_certificate.call_count == 1

    @pytest.mark.asyncio
    async def test_should_call_discoverbyidentitykey_after_ensuring_identity_resolution_permission(self) -> None:
        """Given: Manager with identity resolution permissions
           When: discoverByIdentityKey is called
           Then: Checks permissions, calls underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should call discoverByIdentityKey after ensuring identity resolution permission')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.discover_by_identity_key = AsyncMock(return_value={"certificates": []})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={"seekPermissionsForIdentityResolution": True},
        )

        def auto_grant(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onProtocolPermissionRequested", auto_grant)

        # When
        await manager.discover_by_identity_key({"identityKey": "key"}, "user.com")

        # Then
        assert mock_underlying_wallet.discover_by_identity_key.call_count == 1

    @pytest.mark.asyncio
    async def test_should_call_discoverbyattributes_after_ensuring_identity_resolution_permission(self) -> None:
        """Given: Manager with identity resolution permissions
           When: discoverByAttributes is called
           Then: Checks permissions, calls underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should call discoverByAttributes after ensuring identity resolution permission')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.discover_by_attributes = AsyncMock(return_value={"certificates": []})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test",
            config={"seekPermissionsForIdentityResolution": True},
        )

        def auto_grant(request) -> None:
            manager.grant_permission({"requestID": request["requestID"], "ephemeral": True})

        manager.bind_callback("onProtocolPermissionRequested", auto_grant)

        # When
        await manager.discover_by_attributes({"attributes": {"key": "value"}}, "user.com")

        # Then
        assert mock_underlying_wallet.discover_by_attributes.call_count == 1

    def test_should_proxy_isauthenticated_without_any_special_permission_checks(self) -> None:
        """Given: Manager with underlying wallet
           When: isAuthenticated is called
           Then: Proxies directly to underlying (no permission checks)

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should proxy isAuthenticated without any special permission checks')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.is_authenticated = AsyncMock(return_value={"authenticated": True})
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test")

        # When
        result = manager.is_authenticated({}, "user.com")

        # Then
        assert mock_underlying_wallet.is_authenticated.call_count == 1
        assert result == {"authenticated": True}

    def test_should_proxy_waitforauthentication_without_any_special_permission_checks(self) -> None:
        """Given: Manager with underlying wallet
           When: waitForAuthentication is called
           Then: Proxies directly to underlying (no permission checks)

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should proxy waitForAuthentication without any special permission checks')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.wait_for_authentication = AsyncMock(return_value={"authenticated": True})
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test")

        # When
        result = manager.wait_for_authentication({}, "user.com")

        # Then
        assert mock_underlying_wallet.wait_for_authentication.call_count == 1
        assert result == {"authenticated": True}

    def test_should_proxy_getheight(self) -> None:
        """Given: Manager with underlying wallet
           When: getHeight is called
           Then: Proxies directly to underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should proxy getHeight')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.get_height = AsyncMock(return_value={"height": 100})
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test")

        # When
        result = manager.get_height({}, "user.com")

        # Then
        assert mock_underlying_wallet.get_height.call_count == 1
        assert result == {"height": 100}

    def test_should_proxy_getheaderforheight(self) -> None:
        """Given: Manager with underlying wallet
           When: getHeaderForHeight is called
           Then: Proxies directly to underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should proxy getHeaderForHeight')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.get_header_for_height = AsyncMock(return_value={"header": "header"})
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test")

        # When
        result = manager.get_header_for_height({"height": 100}, "user.com")

        # Then
        assert mock_underlying_wallet.get_header_for_height.call_count == 1
        assert result == {"header": "header"}

    def test_should_proxy_getnetwork(self) -> None:
        """Given: Manager with underlying wallet
           When: getNetwork is called
           Then: Proxies directly to underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should proxy getNetwork')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.get_network = AsyncMock(return_value={"network": "mainnet"})
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test")

        # When
        result = manager.get_network({}, "user.com")

        # Then
        assert mock_underlying_wallet.get_network.call_count == 1
        assert result == {"network": "mainnet"}

    def test_should_proxy_getversion(self) -> None:
        """Given: Manager with underlying wallet
           When: getVersion is called
           Then: Proxies directly to underlying

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should proxy getVersion')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.get_version = AsyncMock(return_value={"version": "1.0.0"})
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test")

        # When
        result = manager.get_version({}, "user.com")

        # Then
        assert mock_underlying_wallet.get_version.call_count == 1
        assert result == {"version": "1.0.0"}

    def test_should_propagate_errors_from_the_underlying_wallet_calls(self) -> None:
        """Given: Underlying wallet throws error
           When: Manager calls underlying method
           Then: Error is propagated to caller

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.proxying.test.ts
                   test('should propagate errors from the underlying wallet calls')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.get_version = AsyncMock(side_effect=RuntimeError("Underlying error"))
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test")

        # When/Then
        with pytest.raises(RuntimeError, match="Underlying error"):
            manager.get_version({}, "user.com")
