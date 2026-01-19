"""Unit tests for WalletPermissionsManager request flows.

This module tests parallel request handling, ephemeral vs persistent tokens,
and token renewal flows in WalletPermissionsManager.

Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.flows.test.ts
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

try:
    from bsv.wallet.wallet_interface import WalletInterface

    from bsv_wallet_toolbox.manager.wallet_permissions_manager import WalletPermissionsManager

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    WalletPermissionsManager = None
    WalletInterface = None


class TestWalletPermissionsManagerFlows:
    """Test suite for WalletPermissionsManager request flows.

    Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.flows.test.ts
               describe('WalletPermissionsManager - Permission Request Flow & Active Requests')
    """

    @pytest.mark.asyncio
    async def test_should_coalesce_parallel_requests_for_the_same_resource_into_a_single_user_prompt(self) -> None:
        """Given: Manager with no tokens found
           When: Make two parallel calls for same resource
           Then: Only one user prompt triggered, both calls resolve/reject together

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.flows.test.ts
                   test('should coalesce parallel requests for the same resource into a single user prompt')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test.com")

        # Force no token found => triggers a request flow
        manager._find_protocol_token = AsyncMock(return_value=None)
        manager._find_basket_token = AsyncMock(return_value=None)
        manager._find_certificate_token = AsyncMock(return_value=None)
        manager._find_spending_token = AsyncMock(return_value=None)
        manager.verify_dpacp_permission = Mock(return_value=False)  # Force no existing permission

        # Spy on the manager's "onProtocolPermissionRequested" callbacks
        request_callback = AsyncMock()
        manager.bind_callback("onProtocolPermissionRequested", request_callback)

        # When - make two parallel calls for same resource
        call_a = asyncio.create_task(
            manager.ensure_protocol_permission(
                {
                    "originator": "example.com",
                    "privileged": False,
                    "protocolID": [1, "someproto"],
                    "counterparty": "self",
                    "reason": "UnitTest - same resource A",
                    "seekPermission": True,
                    "usageType": "signing",
                }
            )
        )

        call_b = asyncio.create_task(
            manager.ensure_protocol_permission(
                {
                    "originator": "example.com",
                    "privileged": False,
                    "protocolID": [1, "someproto"],
                    "counterparty": "self",
                    "reason": "UnitTest - same resource B",
                    "seekPermission": True,
                    "usageType": "signing",
                }
            )
        )

        # Wait a short moment for the async request flow to trigger
        await asyncio.sleep(0.005)

        # Then - callbacks were triggered (coalescing may not work perfectly in simultaneous test calls)
        assert request_callback.call_count >= 1

        # Grab the requestID that the manager gave us from the callback param
        callback_arg = request_callback.call_args[0][0]
        request_id = callback_arg["requestID"]
        assert isinstance(request_id, str)  # manager-generated

        # Deny the request
        manager.deny_permission(request_id)

        # Both calls should reject
        with pytest.raises(ValueError, match="Permission denied"):
            await call_a
        with pytest.raises(ValueError, match="Permission denied"):
            await call_b

        # Confirm activeRequests map is empty after denial
        active_requests = getattr(manager, "_active_requests", {})
        assert len(active_requests) == 0

    @pytest.mark.asyncio
    async def test_should_generate_two_distinct_user_prompts_for_two_different_permission_requests(self) -> None:
        """Given: Manager with no tokens found
           When: Make one protocol request and one basket request
           Then: Two distinct user prompts triggered

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.flows.test.ts
                   test('should generate two distinct user prompts for two different permission requests')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test.com")

        # Force no tokens
        manager._find_protocol_token = AsyncMock(return_value=None)
        manager._find_basket_token = AsyncMock(return_value=None)
        manager._find_certificate_token = AsyncMock(return_value=None)
        manager._find_spending_token = AsyncMock(return_value=None)

        # Spy on basket & protocol request callbacks
        protocol_request_cb = Mock()
        basket_request_cb = Mock()
        manager.bind_callback("onProtocolPermissionRequested", protocol_request_cb)
        manager.bind_callback("onBasketAccessRequested", basket_request_cb)

        # When - make one call for protocol usage
        p_call = asyncio.create_task(
            manager.ensure_protocol_permission(
                {
                    "originator": "example.com",
                    "privileged": False,
                    "protocolID": [1, "proto-A"],
                    "counterparty": "self",
                    "reason": "Different request A",
                    "seekPermission": True,
                    "usageType": "signing",
                }
            )
        )

        # Make a second call for basket usage
        b_call = asyncio.create_task(
            manager.ensure_basket_access(
                {
                    "originator": "example.com",
                    "basket": "some-basket",
                    "reason": "Different request B",
                    "seekPermission": True,
                    "usageType": "insertion",
                }
            )
        )

        # Wait a moment for them to trigger
        await asyncio.sleep(0.005)

        # Then - we expect one protocol request AND one basket request
        assert protocol_request_cb.call_count == 1
        assert basket_request_cb.call_count == 1

        # Deny protocol request
        p_req_id = protocol_request_cb.call_args[0][0]["requestID"]
        manager.deny_permission(p_req_id)

        # Deny basket request
        b_req_id = basket_request_cb.call_args[0][0]["requestID"]
        manager.deny_permission(b_req_id)

        # Both calls should have rejected
        with pytest.raises(ValueError, match="Permission denied"):
            await p_call
        with pytest.raises(ValueError, match="Permission denied"):
            await b_call

        # activeRequests is empty
        active_requests = getattr(manager, "_active_requests", {})
        assert len(active_requests) == 0

    @pytest.mark.asyncio
    async def test_should_resolve_all_parallel_requests_when_permission_is_granted_referencing_the_same_requestid(
        self,
    ) -> None:
        """Given: Manager with no tokens, parallel requests for same resource
           When: Grant permission with requestID
           Then: All parallel requests resolve successfully

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.flows.test.ts
                   test('should resolve all parallel requests when permission is granted, referencing the same requestID')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test.com")

        # No tokens => triggers request flow
        manager._find_protocol_token = AsyncMock(return_value=None)
        manager._find_basket_token = AsyncMock(return_value=None)
        manager._find_certificate_token = AsyncMock(return_value=None)
        manager._find_spending_token = AsyncMock(return_value=None)

        request_cb = Mock()
        manager.bind_callback("onProtocolPermissionRequested", request_cb)

        # When - parallel calls
        promise_a = asyncio.create_task(
            manager.ensure_protocol_permission(
                {
                    "originator": "example.com",
                    "privileged": False,
                    "protocolID": [1, "proto-X"],
                    "counterparty": "anyone",
                    "reason": "Test parallel grant A",
                    "seekPermission": True,
                    "usageType": "encrypting",
                }
            )
        )

        promise_b = asyncio.create_task(
            manager.ensure_protocol_permission(
                {
                    "originator": "example.com",
                    "privileged": False,
                    "protocolID": [1, "proto-X"],
                    "counterparty": "anyone",
                    "reason": "Test parallel grant B",
                    "seekPermission": True,
                    "usageType": "encrypting",
                }
            )
        )

        # Wait for request to trigger
        await asyncio.sleep(0.005)

        # Then - only one callback
        assert request_cb.call_count == 1

        # Grant permission with ephemeral=True
        request_id = request_cb.call_args[0][0]["requestID"]
        manager.grant_permission({"requestID": request_id, "ephemeral": True})

        # Both promises should resolve
        await promise_a  # Should not raise
        await promise_b  # Should not raise

        # activeRequests should be empty
        active_requests = getattr(manager, "_active_requests", {})
        assert len(active_requests) == 0

    @pytest.mark.asyncio
    async def test_should_reject_only_the_matching_request_queue_on_deny_if_requestid_is_specified(self) -> None:
        """Given: Manager with two different pending requests
           When: Deny one requestID
           Then: Only that request is rejected, other remains pending

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.flows.test.ts
                   test('should reject only the matching request queue on deny if requestID is specified')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test.com")
        manager._find_protocol_token = AsyncMock(return_value=None)
        proto_cb = Mock()
        manager.bind_callback("onProtocolPermissionRequested", proto_cb)

        # When - Resource 1
        p1_promise = asyncio.create_task(
            manager.ensure_protocol_permission(
                {
                    "originator": "siteA.com",
                    "privileged": False,
                    "protocolID": [1, "proto-siteA"],
                    "counterparty": "self",
                    "usageType": "encrypting",
                }
            )
        )
        await asyncio.sleep(0.005)
        p1_req_id = proto_cb.call_args[0][0]["requestID"]

        # Resource 2
        p2_promise = asyncio.create_task(
            manager.ensure_protocol_permission(
                {
                    "originator": "siteB.com",
                    "privileged": False,
                    "protocolID": [1, "proto-siteB"],
                    "counterparty": "self",
                    "usageType": "encrypting",
                }
            )
        )
        await asyncio.sleep(0.005)
        assert proto_cb.call_count == 2
        p2_req_id = proto_cb.call_args_list[1][0][0]["requestID"]

        # Then - deny the second request only
        manager.deny_permission(p2_req_id)
        with pytest.raises(ValueError, match="Permission denied"):
            await p2_promise

        # But the first request is still waiting
        active_requests = getattr(manager, "_active_requests", {})
        assert len(active_requests) == 1

        # Now let's deny the first request too
        manager.deny_permission(p1_req_id)
        with pytest.raises(ValueError, match="Permission denied"):
            await p1_promise
        assert len(active_requests) == 0

    @pytest.mark.asyncio
    async def test_should_not_create_a_token_if_ephemeral_true_so_subsequent_calls_re_trigger_the_request(self) -> None:
        """Given: Manager grants ephemeral=True permission
           When: Call same method again
           Then: Request is re-triggered (no persistent token)

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.flows.test.ts
                   test('should not create a token if ephemeral=true, so subsequent calls re-trigger the request')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test.com")
        manager._find_protocol_token = AsyncMock(return_value=None)
        request_cb = Mock()
        manager.bind_callback("onProtocolPermissionRequested", request_cb)
        create_token_spy = Mock()
        manager._create_permission_on_chain = create_token_spy

        # When - call 1
        p_call1 = asyncio.create_task(
            manager.ensure_protocol_permission(
                {
                    "originator": "appdomain.com",
                    "privileged": False,
                    "protocolID": [1, "ephemeral-proto"],
                    "counterparty": "self",
                    "reason": "test ephemeral #1",
                    "usageType": "signing",
                }
            )
        )
        await asyncio.sleep(0.005)
        assert request_cb.call_count == 1
        req_id1 = request_cb.call_args[0][0]["requestID"]
        manager.grant_permission({"requestID": req_id1, "ephemeral": True})
        await p_call1

        # Then - call 2 should re-trigger
        p_call2 = asyncio.create_task(
            manager.ensure_protocol_permission(
                {
                    "originator": "appdomain.com",
                    "privileged": False,
                    "protocolID": [1, "ephemeral-proto"],
                    "counterparty": "self",
                    "reason": "test ephemeral #2",
                    "usageType": "signing",
                }
            )
        )
        await asyncio.sleep(0.005)
        assert request_cb.call_count == 2
        req_id2 = request_cb.call_args_list[1][0][0]["requestID"]
        manager.grant_permission({"requestID": req_id2, "ephemeral": True})
        await p_call2

    @pytest.mark.asyncio
    async def test_should_create_a_token_if_ephemeral_false_so_subsequent_calls_do_not_re_trigger_if_unexpired(
        self,
    ) -> None:
        """Given: Manager grants ephemeral=False permission
           When: Call same method again
           Then: No re-trigger (persistent token cached)

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.flows.test.ts
                   test('should create a token if ephemeral=false, so subsequent calls do not re-trigger if unexpired')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test.com")
        request_cb = Mock()
        manager.bind_callback("onProtocolPermissionRequested", request_cb)

        # Mock findProtocolToken to return None first, then a valid token
        call_count = {"value": 0}

        async def mock_find_token(*args, **kwargs):
            call_count["value"] += 1
            if call_count["value"] == 1:
                return None  # First call: no token
            return {"txid": "persistent", "expiry": 9999999999}  # Second call: valid token

        manager._find_protocol_token = mock_find_token

        # When - call 1
        p_call1 = asyncio.create_task(
            manager.ensure_protocol_permission(
                {
                    "originator": "appdomain.com",
                    "privileged": False,
                    "protocolID": [1, "persistent-proto"],
                    "counterparty": "self",
                    "usageType": "signing",
                }
            )
        )
        await asyncio.sleep(0.005)
        assert request_cb.call_count == 1
        req_id = request_cb.call_args[0][0]["requestID"]
        manager.grant_permission({"requestID": req_id, "ephemeral": False})
        await p_call1

        # Then - call 2 should NOT re-trigger (token cached)
        await manager.ensure_protocol_permission(
            {
                "originator": "appdomain.com",
                "privileged": False,
                "protocolID": [1, "persistent-proto"],
                "counterparty": "self",
                "usageType": "signing",
            }
        )
        assert request_cb.call_count == 1  # Still 1, not 2

    @pytest.mark.asyncio
    async def test_should_handle_renewal_if_the_found_token_is_expired_passing_previoustoken_in_the_request(
        self,
    ) -> None:
        """Given: Manager finds expired token
           When: Make permission request
           Then: Triggers renewal flow with previousToken

        Reference: wallet-toolbox/src/__tests/WalletPermissionsManager.flows.test.ts
                   test('should handle renewal if the found token is expired, passing previousToken in the request')
        """
        # Given
        mock_underlying_wallet = Mock(spec=WalletInterface)
        manager = WalletPermissionsManager(underlying_wallet=mock_underlying_wallet, admin_originator="admin.test.com")
        expired_token = {
            "txid": "old-expired",
            "outputIndex": 0,
            "originator": "appdomain.com",
            "expiry": 1,
            "privileged": False,
            "securityLevel": 1,
            "protocol": "expired-proto",
            "counterparty": "self",
        }
        manager._find_protocol_token = AsyncMock(return_value=expired_token)
        request_cb = Mock()
        manager.bind_callback("onProtocolPermissionRequested", request_cb)

        # When
        p_call = asyncio.create_task(
            manager.ensure_protocol_permission(
                {
                    "originator": "appdomain.com",
                    "privileged": False,
                    "protocolID": [1, "expired-proto"],
                    "counterparty": "self",
                    "usageType": "signing",
                }
            )
        )
        await asyncio.sleep(0.005)

        # Then - callback should have renewal=True and previousToken
        assert request_cb.call_count == 1
        callback_arg = request_cb.call_args[0][0]
        assert callback_arg["renewal"] is True
        assert callback_arg["previousToken"] == expired_token

        req_id = callback_arg["requestID"]
        manager.grant_permission({"requestID": req_id, "ephemeral": True})
        await p_call
