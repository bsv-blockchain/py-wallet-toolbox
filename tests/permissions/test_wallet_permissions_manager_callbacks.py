"""Unit tests for WalletPermissionsManager callback functionality.

This module tests the callback registration, unbinding, and event handling
for permission requests in WalletPermissionsManager.

Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.callbacks.test.ts
"""

import pytest
from typing import Optional, Dict, Any, List
from unittest.mock import Mock, AsyncMock, MagicMock, call

try:
    from bsv_wallet_toolbox.wallet_permissions_manager import (
        WalletPermissionsManager,
        PermissionCallback
    )
    from bsv.wallet.wallet_interface import WalletInterface
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    WalletPermissionsManager = None
    PermissionCallback = None
    WalletInterface = None


class TestWalletPermissionsManagerCallbacks:
    """Test suite for WalletPermissionsManager callback functionality.
    
    Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.callbacks.test.ts
    """
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_bindcallback_should_register_multiple_callbacks_for_the_same_event_which_are_called_in_sequence(self) -> None:
        """Given: Permission manager with multiple callbacks for same event
           When: Trigger the event
           Then: All callbacks are called in sequence
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.callbacks.test.ts
                   test('bindCallback() should register multiple callbacks for the same event, which are called in sequence')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test.com"
        )
        
        call_order = []
        
        async def callback1(event_data):
            call_order.append("callback1")
        
        async def callback2(event_data):
            call_order.append("callback2")
        
        async def callback3(event_data):
            call_order.append("callback3")
        
        # When - bind multiple callbacks to same event
        id1 = manager.bind_callback("onProtocolPermissionRequested", callback1)
        id2 = manager.bind_callback("onProtocolPermissionRequested", callback2)
        id3 = manager.bind_callback("onProtocolPermissionRequested", callback3)
        
        assert isinstance(id1, int)
        assert isinstance(id2, int)
        assert isinstance(id3, int)
        
        # Trigger event internally (simulate permission request)
        await manager._trigger_callbacks("onProtocolPermissionRequested", {"test": "data"})
        
        # Then
        assert call_order == ["callback1", "callback2", "callback3"]
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_unbindcallback_by_numeric_id_should_prevent_the_callback_from_being_called_again(self) -> None:
        """Given: Permission manager with registered callback
           When: Unbind by numeric ID
           Then: Callback is no longer called
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.callbacks.test.ts
                   test('unbindCallback() by numeric ID should prevent the callback from being called again')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test.com"
        )
        
        call_count = 0
        
        async def callback(event_data):
            nonlocal call_count
            call_count += 1
        
        callback_id = manager.bind_callback("onProtocolPermissionRequested", callback)
        
        # When - unbind by ID
        manager.unbind_callback(callback_id)
        
        # Trigger event
        await manager._trigger_callbacks("onProtocolPermissionRequested", {"test": "data"})
        
        # Then
        assert call_count == 0  # Callback was not called
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_unbindcallback_by_function_reference_should_remove_the_callback(self) -> None:
        """Given: Permission manager with registered callback
           When: Unbind by function reference
           Then: Callback is removed
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.callbacks.test.ts
                   test('unbindCallback() by function reference should remove the callback')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test.com"
        )
        
        call_count = 0
        
        async def callback(event_data):
            nonlocal call_count
            call_count += 1
        
        manager.bind_callback("onProtocolPermissionRequested", callback)
        
        # When - unbind by function reference
        manager.unbind_callback(callback)
        
        # Trigger event
        await manager._trigger_callbacks("onProtocolPermissionRequested", {"test": "data"})
        
        # Then
        assert call_count == 0
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_a_failing_callback_throwing_an_error_does_not_block_subsequent_callbacks(self) -> None:
        """Given: Multiple callbacks, one throws error
           When: Trigger event
           Then: Error does not block subsequent callbacks
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.callbacks.test.ts
                   test('a failing callback (throwing an error) does not block subsequent callbacks')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test.com"
        )
        
        call_order = []
        
        async def callback1(event_data):
            call_order.append("callback1")
            raise ValueError("Callback1 failed")
        
        async def callback2(event_data):
            call_order.append("callback2")
        
        async def callback3(event_data):
            call_order.append("callback3")
        
        manager.bind_callback("onProtocolPermissionRequested", callback1)
        manager.bind_callback("onProtocolPermissionRequested", callback2)
        manager.bind_callback("onProtocolPermissionRequested", callback3)
        
        # When - trigger event (should not throw)
        await manager._trigger_callbacks("onProtocolPermissionRequested", {"test": "data"})
        
        # Then - all callbacks were called despite error
        assert "callback1" in call_order
        assert "callback2" in call_order
        assert "callback3" in call_order
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_should_trigger_onprotocolpermissionrequested_with_correct_params_when_a_non_admin_domain_requests_a_protocol_operation(self) -> None:
        """Given: Permission manager with callback
           When: Non-admin domain requests protocol operation
           Then: onProtocolPermissionRequested callback is triggered with correct params
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.callbacks.test.ts
                   test('should trigger onProtocolPermissionRequested with correct params when a non-admin domain requests a protocol operation')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.get_public_key = AsyncMock(return_value={"publicKey": "test"})
        
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test.com",
            config={
                "securityLevel": 1,
                "seekProtocolPermissions": True
            }
        )
        
        captured_params = None
        
        async def permission_callback(params):
            nonlocal captured_params
            captured_params = params
            # Grant permission
            manager.grant_permission(params["requestID"], {"ephemeral": False})
        
        manager.bind_callback("onProtocolPermissionRequested", permission_callback)
        
        # When - non-admin domain requests protocol operation
        await manager.get_public_key(
            {"identityKey": True, "protocolID": [1, "test-protocol"], "keyID": "1"},
            originator="example.com"
        )
        
        # Then
        assert captured_params is not None
        assert captured_params["originator"] == "example.com"
        assert captured_params["protocolID"] == [1, "test-protocol"]
        assert "requestID" in captured_params
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_should_resolve_the_original_caller_promise_when_requests_are_granted(self) -> None:
        """Given: Permission manager with pending request
           When: Permission is granted
           Then: Original caller's promise resolves
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.callbacks.test.ts
                   test('should resolve the original caller promise when requests are granted')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.get_public_key = AsyncMock(return_value={"publicKey": "test-key"})
        
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test.com",
            config={
                "securityLevel": 1,
                "seekProtocolPermissions": True
            }
        )
        
        async def permission_callback(params):
            # Grant permission immediately
            manager.grant_permission(params["requestID"], {"ephemeral": False})
        
        manager.bind_callback("onProtocolPermissionRequested", permission_callback)
        
        # When - request permission
        result = await manager.get_public_key(
            {"identityKey": True, "protocolID": [1, "test"], "keyID": "1"},
            originator="example.com"
        )
        
        # Then - promise resolved with result
        assert result == {"publicKey": "test-key"}
        mock_underlying_wallet.get_public_key.assert_called_once()
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_should_reject_the_original_caller_promise_when_permission_is_denied(self) -> None:
        """Given: Permission manager with pending request
           When: Permission is denied
           Then: Original caller's promise is rejected
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.callbacks.test.ts
                   test('should reject the original caller promise when permission is denied')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.get_public_key = AsyncMock(return_value={"publicKey": "test-key"})
        
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test.com",
            config={
                "securityLevel": 1,
                "seekProtocolPermissions": True
            }
        )
        
        async def permission_callback(params):
            # Deny permission
            manager.deny_permission(params["requestID"])
        
        manager.bind_callback("onProtocolPermissionRequested", permission_callback)
        
        # When/Then - request should be denied
        with pytest.raises(ValueError, match="Permission denied"):
            await manager.get_public_key(
                {"identityKey": True, "protocolID": [1, "test"], "keyID": "1"},
                originator="example.com"
            )
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_multiple_pending_requests_for_the_same_resource_should_trigger_only_one_onxxxrequested_callback(self) -> None:
        """Given: Multiple parallel requests for same resource
           When: Requests are made simultaneously
           Then: Only one callback is triggered
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.callbacks.test.ts
                   test('multiple pending requests for the same resource should trigger only one onXxxRequested callback')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.get_public_key = AsyncMock(return_value={"publicKey": "test-key"})
        
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test.com",
            config={
                "securityLevel": 1,
                "seekProtocolPermissions": True
            }
        )
        
        callback_count = 0
        
        async def permission_callback(params):
            nonlocal callback_count
            callback_count += 1
            # Grant permission
            manager.grant_permission(params["requestID"], {"ephemeral": False})
        
        manager.bind_callback("onProtocolPermissionRequested", permission_callback)
        
        # When - make multiple parallel requests for same protocol
        import asyncio
        results = await asyncio.gather(
            manager.get_public_key(
                {"identityKey": True, "protocolID": [1, "test"], "keyID": "1"},
                originator="example.com"
            ),
            manager.get_public_key(
                {"identityKey": True, "protocolID": [1, "test"], "keyID": "1"},
                originator="example.com"
            ),
            manager.get_public_key(
                {"identityKey": True, "protocolID": [1, "test"], "keyID": "1"},
                originator="example.com"
            )
        )
        
        # Then - only one callback triggered
        assert callback_count == 1
        assert len(results) == 3
        assert all(r == {"publicKey": "test-key"} for r in results)
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WalletPermissionsManager implementation")
    @pytest.mark.asyncio
    async def test_multiple_pending_requests_for_different_resources_should_trigger_separate_onxxxrequested_callbacks(self) -> None:
        """Given: Multiple parallel requests for different resources
           When: Requests are made simultaneously
           Then: Separate callbacks are triggered for each resource
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/WalletPermissionsManager.callbacks.test.ts
                   test('multiple pending requests for different resources should trigger separate onXxxRequested callbacks')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        mock_underlying_wallet.get_public_key = AsyncMock(return_value={"publicKey": "test-key"})
        
        manager = WalletPermissionsManager(
            underlying_wallet=mock_underlying_wallet,
            admin_originator="admin.test.com",
            config={
                "securityLevel": 1,
                "seekProtocolPermissions": True
            }
        )
        
        callback_count = 0
        
        async def permission_callback(params):
            nonlocal callback_count
            callback_count += 1
            # Grant permission
            manager.grant_permission(params["requestID"], {"ephemeral": False})
        
        manager.bind_callback("onProtocolPermissionRequested", permission_callback)
        
        # When - make parallel requests for different protocols
        import asyncio
        results = await asyncio.gather(
            manager.get_public_key(
                {"identityKey": True, "protocolID": [1, "protocol-A"], "keyID": "1"},
                originator="example.com"
            ),
            manager.get_public_key(
                {"identityKey": True, "protocolID": [1, "protocol-B"], "keyID": "1"},
                originator="example.com"
            ),
            manager.get_public_key(
                {"identityKey": True, "protocolID": [1, "protocol-C"], "keyID": "1"},
                originator="example.com"
            )
        )
        
        # Then - separate callbacks for each different protocol
        assert callback_count == 3
        assert len(results) == 3

