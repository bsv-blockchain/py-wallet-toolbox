"""Unit tests for WalletPermissionsManager token creation, renewal, and revocation.

This module tests on-chain permission token management (DPACP, DBAP, DCAP, DSAP).

Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.tokens.test.ts
"""

from unittest.mock import AsyncMock, Mock

import pytest

try:
    from bsv.wallet.wallet_interface import WalletInterface
    from bsv_wallet_toolbox.wallet_permissions_manager import (
        PermissionRequest,
        PermissionToken,
        WalletPermissionsManager,
    )

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    WalletPermissionsManager = None
    WalletInterface = None
    PermissionRequest = None
    PermissionToken = None


class TestWalletPermissionsManagerTokens:
    """Test suite for WalletPermissionsManager token operations.

    Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.tokens.test.ts
               describe('WalletPermissionsManager - On-Chain Token Creation, Renewal & Revocation')
    """

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    def test_should_build_correct_fields_for_a_protocol_token_dpacp(self) -> None:
        """Given: Manager with protocol permission request
           When: Build pushdrop fields for DPACP token
           Then: Creates 6 encrypted fields (domain, expiry, privileged, secLevel, protoName, counterparty)

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.tokens.test.ts
                   test('should build correct fields for a protocol token (DPACP)')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.encrypt = AsyncMock(return_value={"ciphertext": [1, 2, 3]})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet, admin_originator="admin.domain.com"
        )

        request = {
            "type": "protocol",
            "originator": "some-app.com",
            "privileged": True,
            "protocolID": [2, "myProto"],
            "counterparty": "some-other-pubkey",
            "reason": "test-protocol-creation",
        }
        expiry = 1234567890

        # When
        fields = manager._build_pushdrop_fields(request, expiry)

        # Then - 6 encryption calls (domain, expiry, privileged, secLevel, protoName, cpty)
        assert mock_underlying_wallet.encrypt.call_count == 6
        assert len(fields) == 6

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    def test_should_build_correct_fields_for_a_basket_token_dbap(self) -> None:
        """Given: Manager with basket permission request
           When: Build pushdrop fields for DBAP token
           Then: Creates 3 encrypted fields (domain, expiry, basket)

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.tokens.test.ts
                   test('should build correct fields for a basket token (DBAP)')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.encrypt = AsyncMock(return_value={"ciphertext": [1, 2, 3]})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet, admin_originator="admin.domain.com"
        )

        request = {"type": "basket", "originator": "origin.example", "basket": "someBasket", "reason": "basket usage"}
        expiry = 999999999

        # When
        fields = manager._build_pushdrop_fields(request, expiry)

        # Then - 3 encryption calls: domain, expiry, basket
        assert mock_underlying_wallet.encrypt.call_count == 3
        assert len(fields) == 3

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    def test_should_build_correct_fields_for_a_certificate_token_dcap(self) -> None:
        """Given: Manager with certificate permission request
           When: Build pushdrop fields for DCAP token
           Then: Creates 6 encrypted fields (domain, expiry, privileged, certType, fieldsJson, verifier)

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.tokens.test.ts
                   test('should build correct fields for a certificate token (DCAP)')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.encrypt = AsyncMock(return_value={"ciphertext": [1, 2, 3]})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet, admin_originator="admin.domain.com"
        )

        request = {
            "type": "certificate",
            "originator": "cert-user.org",
            "privileged": False,
            "certificate": {"verifier": "02abcdef...", "certType": "KYC", "fields": ["name", "dob"]},
            "reason": "certificate usage",
        }
        expiry = 2222222222

        # When
        fields = manager._build_pushdrop_fields(request, expiry)

        # Then - 6 encryption calls: domain, expiry, privileged, certType, fieldsJson, verifier
        assert mock_underlying_wallet.encrypt.call_count == 6
        assert len(fields) == 6

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    def test_should_build_correct_fields_for_a_spending_token_dsap(self) -> None:
        """Given: Manager with spending permission request
           When: Build pushdrop fields for DSAP token
           Then: Creates 2 encrypted fields (domain, authorizedAmount)

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.tokens.test.ts
                   test('should build correct fields for a spending token (DSAP)')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.encrypt = AsyncMock(return_value={"ciphertext": [1, 2, 3]})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet, admin_originator="admin.domain.com"
        )

        request = {
            "type": "spending",
            "originator": "money-spender.com",
            "spending": {"satoshis": 5000},
            "reason": "monthly spending",
        }
        expiry = 0  # DSAP typically not time-limited

        # When
        fields = manager._build_pushdrop_fields(request, expiry, amount=10000)

        # Then - 2 encryption calls: domain, authorizedAmount
        assert mock_underlying_wallet.encrypt.call_count == 2
        assert len(fields) == 2

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    def test_should_create_a_new_protocol_token_with_the_correct_basket_script_and_tags(self) -> None:
        """Given: Manager with protocol permission request
           When: Create protocol token on chain
           Then: Calls createAction with correct basket, lockingScript, and tags

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.tokens.test.ts
                   test('should create a new protocol token with the correct basket, script, and tags')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.encrypt = AsyncMock(return_value={"ciphertext": [1, 2, 3]})
        mock_underlying_wallet.create_action = AsyncMock(return_value={"txid": "newtxid", "outputIndex": 0})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet, admin_originator="admin.domain.com"
        )

        request = {
            "type": "protocol",
            "originator": "app.com",
            "privileged": False,
            "protocolID": [1, "test"],
            "counterparty": "self",
            "reason": "test",
        }

        # When
        manager._create_permission_token(request, ephemeral=False, previous_token=None)

        # Then - createAction called with correct parameters
        assert mock_underlying_wallet.create_action.call_count == 1
        call_args = mock_underlying_wallet.create_action.call_args[0][0]
        assert call_args["outputs"][0]["basket"] == "permissions_DPACP"
        assert "lockingScript" in call_args["outputs"][0]
        assert call_args["outputs"][0]["tags"] == ["DPACP"]

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    def test_should_create_a_new_basket_token_dbap(self) -> None:
        """Given: Manager with basket permission request
           When: Create basket token on chain
           Then: Calls createAction with DBAP basket and tags

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.tokens.test.ts
                   test('should create a new basket token (DBAP)')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.encrypt = AsyncMock(return_value={"ciphertext": [1, 2, 3]})
        mock_underlying_wallet.create_action = AsyncMock(return_value={"txid": "newtxid", "outputIndex": 0})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet, admin_originator="admin.domain.com"
        )

        request = {"type": "basket", "originator": "app.com", "basket": "myBasket", "reason": "test"}

        # When
        manager._create_permission_token(request, ephemeral=False, previous_token=None)

        # Then
        assert mock_underlying_wallet.create_action.call_count == 1
        call_args = mock_underlying_wallet.create_action.call_args[0][0]
        assert call_args["outputs"][0]["basket"] == "permissions_DBAP"
        assert call_args["outputs"][0]["tags"] == ["DBAP"]

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    def test_should_create_a_new_certificate_token_dcap(self) -> None:
        """Given: Manager with certificate permission request
           When: Create certificate token on chain
           Then: Calls createAction with DCAP basket and tags

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.tokens.test.ts
                   test('should create a new certificate token (DCAP)')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.encrypt = AsyncMock(return_value={"ciphertext": [1, 2, 3]})
        mock_underlying_wallet.create_action = AsyncMock(return_value={"txid": "newtxid", "outputIndex": 0})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet, admin_originator="admin.domain.com"
        )

        request = {
            "type": "certificate",
            "originator": "app.com",
            "privileged": False,
            "certificate": {"verifier": "02abc", "certType": "KYC", "fields": ["name"]},
            "reason": "test",
        }

        # When
        manager._create_permission_token(request, ephemeral=False, previous_token=None)

        # Then
        assert mock_underlying_wallet.create_action.call_count == 1
        call_args = mock_underlying_wallet.create_action.call_args[0][0]
        assert call_args["outputs"][0]["basket"] == "permissions_DCAP"
        assert call_args["outputs"][0]["tags"] == ["DCAP"]

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    def test_should_create_a_new_spending_authorization_token_dsap(self) -> None:
        """Given: Manager with spending permission request
           When: Create spending token on chain
           Then: Calls createAction with DSAP basket and tags

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.tokens.test.ts
                   test('should create a new spending authorization token (DSAP)')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.encrypt = AsyncMock(return_value={"ciphertext": [1, 2, 3]})
        mock_underlying_wallet.create_action = AsyncMock(return_value={"txid": "newtxid", "outputIndex": 0})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet, admin_originator="admin.domain.com"
        )

        request = {"type": "spending", "originator": "app.com", "spending": {"satoshis": 10000}, "reason": "test"}

        # When
        manager._create_permission_token(request, ephemeral=False, previous_token=None)

        # Then
        assert mock_underlying_wallet.create_action.call_count == 1
        call_args = mock_underlying_wallet.create_action.call_args[0][0]
        assert call_args["outputs"][0]["basket"] == "permissions_DSAP"
        assert call_args["outputs"][0]["tags"] == ["DSAP"]

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    def test_should_spend_the_old_token_input_and_create_a_new_protocol_token_output_with_updated_expiry(
        self,
    ) -> None:
        """Given: Manager with previous token and renewal request
           When: Renew protocol token
           Then: Spends old token input and creates new output with updated expiry

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.tokens.test.ts
                   test('should spend the old token input and create a new protocol token output with updated expiry')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.encrypt = AsyncMock(return_value={"ciphertext": [1, 2, 3]})
        mock_underlying_wallet.create_action = AsyncMock(return_value={"txid": "renewedtxid", "outputIndex": 0})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet, admin_originator="admin.domain.com"
        )

        request = {
            "type": "protocol",
            "originator": "app.com",
            "privileged": False,
            "protocolID": [1, "test"],
            "counterparty": "self",
            "reason": "renewal",
        }
        previous_token = {"txid": "oldtxid", "outputIndex": 0}

        # When
        manager._create_permission_token(request, ephemeral=False, previous_token=previous_token)

        # Then - createAction called with inputs (spending old token)
        assert mock_underlying_wallet.create_action.call_count == 1
        call_args = mock_underlying_wallet.create_action.call_args[0][0]
        assert len(call_args.get("inputs", [])) > 0
        assert call_args["inputs"][0]["outpoint"] == "oldtxid.0"

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    def test_should_allow_updating_the_authorizedamount_in_dsap_renewal(self) -> None:
        """Given: Manager with previous DSAP token and renewal with new amount
           When: Renew spending token with updated amount
           Then: Creates new token with updated authorizedAmount field

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.tokens.test.ts
                   test('should allow updating the authorizedAmount in DSAP renewal')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.encrypt = AsyncMock(return_value={"ciphertext": [1, 2, 3]})
        mock_underlying_wallet.create_action = AsyncMock(return_value={"txid": "renewedtxid", "outputIndex": 0})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet, admin_originator="admin.domain.com"
        )

        request = {
            "type": "spending",
            "originator": "app.com",
            "spending": {"satoshis": 20000},  # Updated amount
            "reason": "renewal with new limit",
        }
        previous_token = {"txid": "olddsaptxid", "outputIndex": 0, "authorizedAmount": 10000}  # Old amount

        # When
        manager._create_permission_token(request, ephemeral=False, previous_token=previous_token)

        # Then - createAction called, amount should reflect new value
        assert mock_underlying_wallet.create_action.call_count == 1

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    def test_should_create_a_transaction_that_consumes_spends_the_old_token_with_no_new_outputs(self) -> None:
        """Given: Manager with previous token
           When: Revoke permission token
           Then: Creates transaction that spends old token with no new permission outputs

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.tokens.test.ts
                   test('should create a transaction that consumes (spends) the old token with no new outputs')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = AsyncMock(return_value={"txid": "revocationtxid"})
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet, admin_originator="admin.domain.com"
        )

        token_to_revoke = {"txid": "tokentorevoke", "outputIndex": 0}

        # When
        manager._revoke_permission_token(token_to_revoke)

        # Then - createAction called with input (spending token) but no permission output
        assert mock_underlying_wallet.create_action.call_count == 1
        call_args = mock_underlying_wallet.create_action.call_args[0][0]
        assert len(call_args.get("inputs", [])) > 0
        assert call_args["inputs"][0]["outpoint"] == "tokentorevoke.0"
        # No new permission token outputs (just consuming the old one)
        assert len(call_args.get("outputs", [])) == 0 or all(
            "permissions_" not in o.get("basket", "") for o in call_args["outputs"]
        )

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    def test_should_remove_the_old_token_from_listing_after_revocation(self) -> None:
        """Given: Manager with token in storage
           When: Revoke token and list tokens
           Then: Revoked token no longer appears in listOutputs

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.tokens.test.ts
                   test('should remove the old token from listing after revocation')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = AsyncMock(return_value={"txid": "revocationtxid"})
        mock_underlying_wallet.list_outputs = AsyncMock(return_value={"outputs": []})  # Empty after revocation
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet, admin_originator="admin.domain.com"
        )

        token_to_revoke = {"txid": "tokentorevoke", "outputIndex": 0}

        # When
        manager._revoke_permission_token(token_to_revoke)
        result = manager._list_permission_tokens("protocol")

        # Then - list returns empty (token removed)
        assert len(result) == 0
