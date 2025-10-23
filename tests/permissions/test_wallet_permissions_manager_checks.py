"""Unit tests for WalletPermissionsManager permission checking functionality.

This module tests various permission check scenarios including security levels,
admin-only protocols/baskets, token renewal, and permission prompts.

Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
"""

import pytest
from typing import Optional, Dict, Any, List
from unittest.mock import Mock, AsyncMock, MagicMock
import time

try:
    from bsv_wallet_toolbox.wallet_permissions_manager import (
        WalletPermissionsManager,
        PermissionToken
    )
    from bsv.wallet.wallet_interface import WalletInterface
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    WalletPermissionsManager = None
    PermissionToken = None
    WalletInterface = None


class TestWalletPermissionsManagerChecks:
    """Test suite for WalletPermissionsManager permission checks.
    
    Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
               describe('Protocol Usage (DPACP)') and describe('Basket Usage (DBAP)')
    """
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_should_skip_permission_prompt_if_seclevel_0_open_usage(self) -> None:
        """Given: Manager with seekProtocolPermissionsForSigning enabled
           When: Call createSignature with secLevel=0
           Then: No permission prompt, operation succeeds
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should skip permission prompt if secLevel=0 (open usage)')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_signature = AsyncMock(return_value={"signature": [0x01, 0x02]})
        
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={
                "seekProtocolPermissionsForSigning": True
            }
        )
        
        # When - createSignature with protocolID securityLevel=0
        result = await manager.create_signature(
            {
                "protocolID": [0, "open-protocol"],
                "data": [0x01, 0x02],
                "keyID": "1"
            },
            originator="some-user.com"
        )
        
        # Then - no permission request triggered
        active_requests = getattr(manager, "_active_requests", {})
        assert len(active_requests) == 0
        
        # Underlying method called once
        mock_underlying_wallet.create_signature.assert_called_once()
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_should_prompt_for_protocol_usage_if_securitylevel_1_and_no_existing_token(self) -> None:
        """Given: Manager with no existing token
           When: Call with securityLevel=1
           Then: Permission prompt triggered
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should prompt for protocol usage if securityLevel=1 and no existing token')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_signature = AsyncMock(return_value={"signature": [0x99, 0xaa]})
        
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={
                "seekProtocolPermissionsForSigning": True
            }
        )
        
        # Auto-grant ephemeral permission
        async def permission_callback(request):
            await manager.grant_permission({
                "requestID": request["requestID"],
                "ephemeral": True
            })
        
        manager.bind_callback("onProtocolPermissionRequested", permission_callback)
        
        # When - createSignature with secLevel=1
        result = await manager.create_signature(
            {
                "protocolID": [1, "test-protocol"],
                "data": [0x99, 0xaa],
                "keyID": "1"
            },
            originator="some-nonadmin.com"
        )
        
        # Then - underlying signature called
        mock_underlying_wallet.create_signature.assert_called_once()
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_should_deny_protocol_usage_if_user_denies_permission(self) -> None:
        """Given: Manager with deny callback
           When: Request protocol operation
           Then: Permission denied error
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should deny protocol usage if user denies permission')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.encrypt = AsyncMock(return_value={"ciphertext": [1, 2, 3]})
        
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com"
        )
        
        # Deny callback
        def permission_callback(request):
            manager.deny_permission(request["requestID"])
        
        manager.bind_callback("onProtocolPermissionRequested", permission_callback)
        
        # When/Then - permission denied
        with pytest.raises(ValueError, match="Permission denied"):
            await manager.encrypt(
                {
                    "protocolID": [1, "needs-perm"],
                    "plaintext": [1, 2, 3],
                    "keyID": "xyz"
                },
                originator="external-app.com"
            )
        
        # Underlying encrypt never called
        mock_underlying_wallet.encrypt.assert_not_called()
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_should_enforce_privileged_token_if_differentiateprivilegedoperations_true(self) -> None:
        """Given: Manager with differentiatePrivilegedOperations=true
           When: Request privileged operation
           Then: Privileged permission required
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should enforce privileged token if differentiatePrivilegedOperations=true')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_signature = AsyncMock(return_value={"signature": [0xc0, 0xff, 0xee]})
        
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={
                "seekProtocolPermissionsForSigning": True,
                "differentiatePrivilegedOperations": True
            }
        )
        
        async def permission_callback(request):
            await manager.grant_permission({
                "requestID": request["requestID"],
                "ephemeral": True
            })
        
        manager.bind_callback("onProtocolPermissionRequested", permission_callback)
        
        # When - privileged signature
        result = await manager.create_signature(
            {
                "protocolID": [1, "high-level-crypto"],
                "privileged": True,
                "data": [0xc0, 0xff, 0xee],
                "keyID": "1"
            },
            originator="nonadmin.app"
        )
        
        # Then - underlying called
        mock_underlying_wallet.create_signature.assert_called_once()
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_should_ignore_privileged_true_if_differentiateprivilegedoperations_false(self) -> None:
        """Given: Manager with differentiatePrivilegedOperations=false
           When: Request with privileged=true
           Then: Privileged flag ignored, treated as normal
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should ignore `privileged=true` if differentiatePrivilegedOperations=false')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_signature = AsyncMock(return_value={"signature": [0x99]})
        
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={
                "differentiatePrivilegedOperations": False,
                "seekProtocolPermissionsForSigning": True
            }
        )
        
        async def permission_callback(request):
            await manager.grant_permission({
                "requestID": request["requestID"],
                "ephemeral": True
            })
        
        manager.bind_callback("onProtocolPermissionRequested", permission_callback)
        
        # When - privileged flag is ignored
        result = await manager.create_signature(
            {
                "protocolID": [1, "some-protocol"],
                "privileged": True,
                "data": [0x99],
                "keyID": "keyXYZ"
            },
            originator="nonadmin.com"
        )
        
        # Then - succeeds without special privileged handling
        mock_underlying_wallet.create_signature.assert_called_once()
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_should_fail_if_protocol_name_is_admin_reserved_and_caller_is_not_admin(self) -> None:
        """Given: Manager with admin-reserved protocol
           When: Non-admin tries to use admin-reserved protocol
           Then: Operation fails
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should fail if protocol name is admin-reserved and caller is not admin')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_hmac = AsyncMock()
        
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="secure.admin.com"
        )
        
        # When/Then - admin-reserved protocol name
        with pytest.raises(ValueError, match="admin-only"):
            await manager.create_hmac(
                {
                    "protocolID": [1, "admin super-secret"],
                    "data": [0x01, 0x02],
                    "keyID": "1"
                },
                originator="not-an-admin.com"
            )
        
        # Underlying never called
        mock_underlying_wallet.create_hmac.assert_not_called()
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_should_prompt_for_renewal_if_token_is_found_but_expired(self) -> None:
        """Given: Manager with expired token
           When: Request operation
           Then: Renewal prompt triggered
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should prompt for renewal if token is found but expired')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_signature = AsyncMock(return_value={"signature": [0xfe]})
        
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com"
        )
        
        # Mock expired token
        expired_token = {
            "tx": [],
            "txid": "oldtxid123",
            "outputIndex": 0,
            "outputScript": "deadbeef",
            "satoshis": 1,
            "originator": "some-nonadmin.com",
            "expiry": 1,  # Past timestamp
            "privileged": False,
            "securityLevel": 1,
            "protocol": "test-protocol",
            "counterparty": "self"
        }
        
        # Mock findProtocolToken to return expired token
        manager._find_protocol_token = AsyncMock(return_value=expired_token)
        
        # Bind callback that grants renewal
        async def permission_callback(request):
            assert request["renewal"] is True
            assert request["previousToken"] == expired_token
            await manager.grant_permission({
                "requestID": request["requestID"],
                "ephemeral": True
            })
        
        manager.bind_callback("onProtocolPermissionRequested", permission_callback)
        
        # When - call with expired token
        await manager.create_signature(
            {
                "protocolID": [1, "test-protocol"],
                "data": [0xfe],
                "keyID": "1"
            },
            originator="some-nonadmin.com"
        )
        
        # Then - underlying called after renewal
        mock_underlying_wallet.create_signature.assert_called_once()
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_should_fail_immediately_if_using_an_admin_only_basket_as_non_admin(self) -> None:
        """Given: Non-admin originator
           When: Attempt to use admin-only basket
           Then: Fails immediately
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should fail immediately if using an admin-only basket as non-admin')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = AsyncMock()
        
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com"
        )
        
        # When/Then - admin basket from non-admin
        with pytest.raises(ValueError, match="admin-only"):
            await manager.create_action(
                {
                    "description": "Insert into admin basket",
                    "outputs": [
                        {
                            "lockingScript": "abcd",
                            "satoshis": 100,
                            "basket": "admin secret-basket",
                            "outputDescription": "Nothing to see here"
                        }
                    ]
                },
                originator="non-admin.com"
            )
        
        # Underlying never called
        mock_underlying_wallet.create_action.assert_not_called()
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_should_fail_immediately_if_using_the_reserved_basket_default_as_non_admin(self) -> None:
        """Given: Non-admin originator
           When: Attempt to use 'default' basket
           Then: Fails immediately
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should fail immediately if using the reserved basket "default" as non-admin')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = AsyncMock()
        
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com"
        )
        
        # When/Then - 'default' basket from non-admin
        with pytest.raises(ValueError, match="admin-only"):
            await manager.create_action(
                {
                    "description": "Insert to default basket",
                    "outputs": [
                        {
                            "lockingScript": "0x1234",
                            "satoshis": 1,
                            "basket": "default",
                            "outputDescription": "Nothing to see here"
                        }
                    ]
                },
                originator="some-nonadmin.com"
            )
        
        mock_underlying_wallet.create_action.assert_not_called()
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_should_prompt_for_insertion_permission_if_seekbasketinsertionpermissions_true(self) -> None:
        """Given: Manager with seekBasketInsertionPermissions=true
           When: Create action with basket
           Then: Permission prompt triggered
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should prompt for insertion permission if seekBasketInsertionPermissions=true')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = AsyncMock(return_value={"txid": "abc123"})
        
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={
                "seekBasketInsertionPermissions": True
            }
        )
        
        # Auto-grant basket access
        async def basket_callback(request):
            await manager.grant_permission({
                "requestID": request["requestID"],
                "ephemeral": True
            })
        
        manager.bind_callback("onBasketAccessRequested", basket_callback)
        
        # Auto-grant spending authorization
        async def spending_callback(request):
            await manager.grant_permission({
                "requestID": request["requestID"],
                "ephemeral": True
            })
        
        manager.bind_callback("onSpendingAuthorizationRequested", spending_callback)
        
        # When
        result = await manager.create_action(
            {
                "description": "Insert to user-basket",
                "outputs": [
                    {
                        "lockingScript": "7812",
                        "satoshis": 1,
                        "basket": "user-basket",
                        "outputDescription": "Nothing to see here"
                    }
                ]
            },
            originator="some-nonadmin.com"
        )
        
        # Then - underlying called
        mock_underlying_wallet.create_action.assert_called_once()
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_should_skip_insertion_permission_if_seekbasketinsertionpermissions_false(self) -> None:
        """Given: Manager with seekBasketInsertionPermissions=false
           When: Create action with basket
           Then: No basket permission prompt
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.checks.test.ts
                   test('should skip insertion permission if seekBasketInsertionPermissions=false')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.create_action = AsyncMock(return_value={"txid": "xyz789"})
        
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.com",
            config={
                "seekBasketInsertionPermissions": False
            }
        )
        
        # Auto-grant spending authorization only
        async def spending_callback(request):
            await manager.grant_permission({
                "requestID": request["requestID"],
                "ephemeral": True
            })
        
        manager.bind_callback("onSpendingAuthorizationRequested", spending_callback)
        
        # When
        result = await manager.create_action(
            {
                "description": "Insert to user-basket",
                "outputs": [
                    {
                        "lockingScript": "1234",
                        "satoshis": 1,
                        "basket": "some-basket",
                        "outputDescription": "Nothing to see here"
                    }
                ]
            },
            originator="some-nonadmin.com"
        )
        
        # Then - no basket permission check, underlying called
        mock_underlying_wallet.create_action.assert_called_once()

