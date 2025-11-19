"""Manual tests for WABClient (Wallet Authentication Bridge Client).

This module tests WABClient functionality including server info, auth methods,
faucet requests, and user management.

Reference: wallet-toolbox/src/wab-client/__tests/WABClient.man.test.ts

Note: This test suite requires the WAB server to be running on localhost:3000
      or you can spin up a test environment or mock server.
"""

from datetime import datetime

import pytest

try:
    from bsv_wallet_toolbox.wab_client import WABClient
    from bsv_wallet_toolbox.wab_client.auth_method_interactors import TwilioPhoneInteractor

    from bsv_wallet_toolbox.utils import TestUtils

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class TestWABClientManual:
    """Manual test suite for WABClient.

    Reference: wallet-toolbox/src/wab-client/__tests/WABClient.man.test.ts
               describe('WABClient')
    """

    @pytest.fixture(scope="class")
    def setup_client(self):
        """Setup WABClient instance for tests.

        Reference: wallet-toolbox/src/wab-client/__tests/WABClient.man.test.ts
                   beforeAll()
        """
        server_url = "http://localhost:3000"  # Adjust if your server is different
        test_presentation_key = f"clientTestKey{int(datetime.now().timestamp() * 1000)}"
        client = WABClient(server_url)
        return {"client": client, "test_presentation_key": test_presentation_key}

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WABClient implementation")
    @pytest.mark.asyncio
    async def test_placeholder(self) -> None:
        """Given: WABClient
           When: Placeholder test
           Then: Pass (empty test)

        Reference: wallet-toolbox/src/wab-client/__tests/WABClient.man.test.ts
                   it('00')

        Note: TypeScript also has a meaningless test name 'it('00')' with empty body.
              This is kept as a placeholder to match TypeScript's test structure.
        """

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WABClient implementation")
    @pytest.mark.asyncio
    async def test_should_get_server_info(self, setup_client) -> None:
        """Given: WABClient instance
           When: Call getInfo
           Then: Returns server info with supportedAuthMethods containing 'TwilioPhone'

        Reference: wallet-toolbox/src/wab-client/__tests/WABClient.man.test.ts
                   it('should get server info')
        """
        # Given
        if TestUtils.no_env("main"):
            pytest.skip("No 'main' environment configured")

        client = setup_client["client"]

        # When
        info = await client.get_info()

        # Then
        assert "TwilioPhone" in info["supportedAuthMethods"]

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WABClient implementation")
    @pytest.mark.asyncio
    async def test_should_do_twilio_phone_flow(self, setup_client) -> None:
        """Given: WABClient instance, TwilioPhoneInteractor, and test presentation key
           When: Start auth method with phone number, then complete with OTP
           Then: Both operations succeed and presentation key matches

        Reference: wallet-toolbox/src/wab-client/__tests/WABClient.man.test.ts
                   it('should do Twilio phone flow')
        """
        # Given
        if TestUtils.no_env("main"):
            pytest.skip("No 'main' environment configured")

        client = setup_client["client"]
        test_presentation_key = setup_client["test_presentation_key"]
        twilio = TwilioPhoneInteractor()

        # When - start auth method
        start_res = await client.start_auth_method(twilio, test_presentation_key, {"phoneNumber": "+12223334444"})

        # Then - start succeeds
        assert start_res["success"] is True

        # When - complete auth method
        complete_res = await client.complete_auth_method(
            twilio, test_presentation_key, {"otp": "123456", "phoneNumber": "+12223334444"}
        )

        # Then - complete succeeds
        assert complete_res["success"] is True
        assert complete_res["presentationKey"] == test_presentation_key

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WABClient implementation")
    @pytest.mark.asyncio
    async def test_should_request_faucet(self, setup_client) -> None:
        """Given: WABClient instance and test presentation key
           When: Call requestFaucet
           Then: Returns success with paymentData containing amount=1000

        Reference: wallet-toolbox/src/wab-client/__tests/WABClient.man.test.ts
                   it('should request faucet')
        """
        # Given
        if TestUtils.no_env("main"):
            pytest.skip("No 'main' environment configured")

        client = setup_client["client"]
        test_presentation_key = setup_client["test_presentation_key"]

        # When
        faucet_res = await client.request_faucet(test_presentation_key)

        # Then
        assert faucet_res["success"] is True
        assert faucet_res["paymentData"] is not None
        assert faucet_res["paymentData"]["amount"] == 1000

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WABClient implementation")
    @pytest.mark.asyncio
    async def test_should_list_linked_methods(self, setup_client) -> None:
        """Given: WABClient instance and test presentation key with linked auth method
           When: Call listLinkedMethods
           Then: Returns authMethods array with length 1 and methodType 'TwilioPhone'

        Reference: wallet-toolbox/src/wab-client/__tests/WABClient.man.test.ts
                   it('should list linked methods')
        """
        # Given
        if TestUtils.no_env("main"):
            pytest.skip("No 'main' environment configured")

        client = setup_client["client"]
        test_presentation_key = setup_client["test_presentation_key"]

        # When
        linked = await client.list_linked_methods(test_presentation_key)

        # Then
        assert len(linked["authMethods"]) == 1
        assert linked["authMethods"][0]["methodType"] == "TwilioPhone"

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WABClient implementation")
    @pytest.mark.asyncio
    async def test_can_delete_user(self, setup_client) -> None:
        """Given: WABClient instance and test presentation key
           When: Call deleteUser
           Then: Returns success=True

        Reference: wallet-toolbox/src/wab-client/__tests/WABClient.man.test.ts
                   it('can delete user')
        """
        # Given
        if TestUtils.no_env("main"):
            pytest.skip("No 'main' environment configured")

        client = setup_client["client"]
        test_presentation_key = setup_client["test_presentation_key"]

        # When
        delete_res = await client.delete_user(test_presentation_key)

        # Then
        assert delete_res["success"] is True
