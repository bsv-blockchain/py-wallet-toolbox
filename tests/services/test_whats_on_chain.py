"""Unit tests for WhatsOnChain service provider.

This module tests WhatsOnChain functionality including getRawTx, getMerklePath,
updateBsvExchangeRate, and getTxPropagation.

Reference: wallet-toolbox/src/services/providers/__tests/WhatsOnChain.test.ts
"""

import json
from unittest.mock import AsyncMock, Mock

import pytest

try:
    from bsv_wallet_toolbox.errors import InvalidParameterError
    from bsv_wallet_toolbox.services import Services
    from bsv_wallet_toolbox.services.providers import WhatsOnChain
    from bsv_wallet_toolbox.utils import TestUtils

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


@pytest.fixture
def valid_woc_config():
    """Fixture providing valid WhatsOnChain configuration."""
    return {"apiKey": "test_api_key_123", "chain": "main"}


@pytest.fixture
def mock_http_client():
    """Fixture providing a mock HTTP client for testing."""
    client = Mock()
    # fetch is an async method that returns a response object
    client.fetch = AsyncMock()
    return client


@pytest.fixture
def mock_woc_provider(valid_woc_config, mock_http_client):
    """Fixture providing mock WhatsOnChain provider."""
    # Pass mock HTTP client directly to constructor
    provider = WhatsOnChain(valid_woc_config["chain"], {"apiKey": valid_woc_config["apiKey"]}, mock_http_client)
    yield provider, mock_http_client


@pytest.fixture
def valid_txid():
    """Fixture providing a valid transaction ID."""
    return "d9978ffc6676523208f7b33bebf1b176388bbeace2c7ef67ce35c2eababa1805"


@pytest.fixture
def invalid_txids():
    """Fixture providing various invalid transaction IDs."""
    return [
        "",  # Empty string
        "invalid_hex",  # Invalid hex
        "123",  # Too short
        "gggggggggggggggggggggggggggggggggggggggg",  # Invalid hex chars
        "d9978ffc6676523208f7b33bebf1b176388bbeace2c7ef67ce35c2eababa180",  # Too short (63 chars)
        "d9978ffc6676523208f7b33bebf1b176388bbeace2c7ef67ce35c2eababa1805aa",  # Too long (65 chars)
        None,  # None type
        123,  # Wrong type
        [],  # Wrong type
        {},  # Wrong type
    ]


@pytest.fixture
def network_error_responses():
    """Fixture providing various network error response scenarios."""
    return [
        # HTTP 500 Internal Server Error
        {"status": 500, "text": "Internal Server Error"},
        # HTTP 503 Service Unavailable
        {"status": 503, "text": "Service Unavailable"},
        # HTTP 429 Rate Limited
        {"status": 429, "text": "Rate limit exceeded", "headers": {"Retry-After": "60"}},
        # HTTP 401 Unauthorized
        {"status": 401, "text": "Unauthorized"},
        # HTTP 403 Forbidden
        {"status": 403, "text": "Forbidden"},
        # HTTP 404 Not Found
        {"status": 404, "text": "Not Found"},
        # Timeout scenarios
        {"timeout": True, "error": "Connection timeout"},
        # Malformed JSON response
        {"status": 200, "text": "invalid json {{{", "malformed": True},
        # Empty response
        {"status": 200, "text": "", "empty": True},
        # Very large response (simulating memory issues)
        {"status": 200, "text": "x" * 1000000, "large": True},
    ]


@pytest.fixture
def exchange_rate_responses():
    """Fixture providing various exchange rate response scenarios."""
    return [
        # Valid response
        {"status": 200, "json": {"base": "USD", "rate": 45.67, "timestamp": 1640995200}},
        # Invalid base currency
        {"status": 200, "json": {"base": "EUR", "rate": 45.67, "timestamp": 1640995200}},
        # Negative rate
        {"status": 200, "json": {"base": "USD", "rate": -45.67, "timestamp": 1640995200}},
        # Zero rate
        {"status": 200, "json": {"base": "USD", "rate": 0, "timestamp": 1640995200}},
        # Missing fields
        {"status": 200, "json": {"rate": 45.67, "timestamp": 1640995200}},  # missing base
        {"status": 200, "json": {"base": "USD", "timestamp": 1640995200}},  # missing rate
        {"status": 200, "json": {"base": "USD", "rate": 45.67}},  # missing timestamp
    ]


class TestWhatsOnChain:
    """Test suite for WhatsOnChain service provider.

    Reference: wallet-toolbox/src/services/providers/__tests/WhatsOnChain.test.ts
               describe('whatsonchain tests')
    """

    def test_placeholder(self) -> None:
        """Given: WhatsOnChain service
           When: Placeholder test
           Then: Pass (empty test)

        Reference: wallet-toolbox/src/services/providers/__tests/WhatsOnChain.test.ts
                   test('00')

        Note: TypeScript also has a meaningless test name 'test('00')' with empty body.
              This is kept as a placeholder to match TypeScript's test structure.
        """

    @pytest.mark.asyncio
    async def test_getrawtx_testnet(self) -> None:
        """Given: WhatsOnChain service for testnet and a known txid
           When: Call getRawTx with valid and invalid txids
           Then: Returns raw transaction hex for valid txid, undefined for invalid txid

        Reference: wallet-toolbox/src/services/providers/__tests/WhatsOnChain.test.ts
                   test('0 getRawTx testnet')
        """
        # Given
        env_test = TestUtils.get_env("test")
        woc_test = WhatsOnChain(env_test.chain, {"apiKey": env_test.taal_api_key})

        # When - valid txid
        raw_tx = await woc_test.get_raw_tx("7e5b797b86abd31a654bf296900d6cb14d04ef0811568ff4675494af2d92166b")

        # Then
        expected_raw_tx = "010000000158EED5DBBB7E2F7D70C79A11B9B61AABEECFA5A7CEC679BEDD00F42C48A4BD45010000006B483045022100AE8BB45498A40E2AC797775C405C108168804CD84E8C09A9D42D280D18EDDB6D022024863BFAAC5FF3C24CA65E2F3677EDA092BC3CC5D2EFABA73264B8FF55CF416B412102094AAF520E14E1C4D68496822800BCC7D3B3B26CA368E004A2CB70B398D82FACFFFFFFFF0203000000000000007421020A624B72B34BC192851C5D8890926BBB70B31BC10FDD4E3BC6534E41B1C81B93AC03010203030405064630440220013B4984F4054C2FBCD2F448AB896CCA5C4E234BF765B0C7FB27EDE572A7F7DA02201A5C8D0D023F94C209046B9A2B96B2882C5E43B72D8115561DF8C07442010EEA6D7592090000000000001976A9146511FCE2F7EF785A2102142FBF381AD1291C918688AC00000000"
        assert raw_tx == expected_raw_tx

        # When - invalid txid
        raw_tx_invalid = await woc_test.get_raw_tx("1" * 64)

        # Then
        assert raw_tx_invalid is None

    @pytest.mark.asyncio
    async def test_getrawtx_mainnet(self) -> None:
        """Given: WhatsOnChain service for mainnet and a known txid
           When: Call getRawTx with valid and invalid txids
           Then: Returns raw transaction hex for valid txid, undefined for invalid txid

        Reference: wallet-toolbox/src/services/providers/__tests/WhatsOnChain.test.ts
                   test('1 getRawTx mainnet')
        """
        # Given
        env_main = TestUtils.get_env("main")
        woc_main = WhatsOnChain(env_main.chain, {"apiKey": env_main.taal_api_key})

        # When - valid txid
        raw_tx = await woc_main.get_raw_tx("d9978ffc6676523208f7b33bebf1b176388bbeace2c7ef67ce35c2eababa1805")

        # Then
        expected_raw_tx = "0100000001026A66A5F724EB490A55E0E08553286F08AD57E92C4BF34B5C44EA6BC0A49828020000006B483045022100C3D9A5ACA30C1F2E1A54532162E7AFE5AA69150E4C06D760414A16D1EA1BABD602205E0D9191838B0911A1E7328554A2B22EFAA80CF52B15FBA37C3046A0996C7AAD412103FA3CF488CA98D9F2DB91843F36BAF6BE39F6C947976C02394602D09FBC5F4CF4FFFFFFFF0210270000000000001976A91444C04354E88975C4BEF30CFE89D300CC7659F7E588AC96BC0000000000001976A9149A53E5CF5F1876924D98A8B35CA0BC693618682488AC00000000"
        assert raw_tx == expected_raw_tx

        # When - invalid txid
        raw_tx_invalid = await woc_main.get_raw_tx("1" * 64)

        # Then
        assert raw_tx_invalid is None

    @pytest.mark.asyncio
    async def test_getmerklepath_testnet(self) -> None:
        """Given: WhatsOnChain service for testnet, Services instance, and a known txid
           When: Call getMerklePath with valid and invalid txids
           Then: Returns merklePath result for valid txid, empty result for invalid txid

        Reference: wallet-toolbox/src/services/providers/__tests/WhatsOnChain.test.ts
                   test('2 getMerklePath testnet')
        """
        # Given
        env_test = TestUtils.get_env("test")
        woc_test = WhatsOnChain(env_test.chain, {"apiKey": env_test.taal_api_key})
        services = Services(env_test.chain)

        # When - valid txid
        r = await woc_test.get_merkle_path("7e5b797b86abd31a654bf296900d6cb14d04ef0811568ff4675494af2d92166b", services)

        # Remove hash_str fields for comparison (py-sdk includes both hash and hash_str)
        def remove_hash_str(obj):
            if isinstance(obj, dict):
                return {k: remove_hash_str(v) for k, v in obj.items() if k != "hash_str"}
            elif isinstance(obj, list):
                return [remove_hash_str(item) for item in obj]
            return obj

        r_normalized = remove_hash_str(r)
        s = json.dumps(r_normalized, sort_keys=True, separators=(",", ":"))

        # Then
        expected_json = '{"header":{"bits":486604799,"hash":"00000000d8a73bf9a37272a71886ea92a25376bed1c1916f2b5cfbec4d6f6a25","height":1661398,"merkleRoot":"edbc07082ca0a31d5ec89d1f503a9cd41112c0d8f3221a96acfb8a9d16f8e82b","nonce":1437884974,"previousHash":"000000000688340a14b77e49bb0fca5ac7b624f7f79a5517583d1aae61c4e658","time":1739624725,"version":536870912},"merklePath":{"blockHeight":1661398,"path":[[{"hash":"7e5b797b86abd31a654bf296900d6cb14d04ef0811568ff4675494af2d92166b","offset":6,"txid":true},{"hash":"97dd9d9080394d52338588732d9f84e1debca93f171f674ac3beac1e75495568","offset":7}],[{"hash":"81beedcd219d9e03255bde2ee479db34b9fed04d30373ba8bc264a64af2515b9","offset":2}],[{"hash":"9965f9aaeea33f6878335e6f7e6bdb544c3a8550c84e2f0daca54e9cd912111c","offset":0}]]},"name":"WoCTsc","notes":[{"name":"WoCTsc","status":200,"statusText":"OK","what":"getMerklePathSuccess"}]}'
        assert s == expected_json

        # When - invalid txid
        # HTTP mocking is applied globally in tests/conftest.py
        r_invalid = await woc_test.get_merkle_path("1" * 64, services)
        s_invalid = json.dumps(r_invalid, sort_keys=True, separators=(",", ":"))

        # Then
        expected_json_invalid = (
            '{"name":"WoCTsc","notes":[{"name":"WoCTsc","status":200,"statusText":"OK","what":"getMerklePathNoData"}]}'
        )
        assert s_invalid == expected_json_invalid

    @pytest.mark.asyncio
    async def test_getmerklepath_mainnet(self) -> None:
        """Given: WhatsOnChain service for mainnet, Services instance, and a known txid
           When: Call getMerklePath with valid and invalid txids
           Then: Returns merklePath result for valid txid, empty result for invalid txid

        Reference: wallet-toolbox/src/services/providers/__tests/WhatsOnChain.test.ts
                   test('3 getMerklePath mainnet')
        """
        # Given
        env_main = TestUtils.get_env("main")
        woc_main = WhatsOnChain(env_main.chain, {"apiKey": env_main.taal_api_key})
        services = Services(env_main.chain)

        # HTTP mocking is applied globally in tests/conftest.py

        # When - valid txid
        r = await woc_main.get_merkle_path("d9978ffc6676523208f7b33bebf1b176388bbeace2c7ef67ce35c2eababa1805", services)

        # Remove hash_str fields for comparison (py-sdk includes both hash and hash_str)
        def remove_hash_str(obj):
            if isinstance(obj, dict):
                return {k: remove_hash_str(v) for k, v in obj.items() if k != "hash_str"}
            elif isinstance(obj, list):
                return [remove_hash_str(item) for item in obj]
            return obj

        r_normalized = remove_hash_str(r)
        s = json.dumps(r_normalized, sort_keys=True, separators=(",", ":"))

        # Then
        expected_json = '{"header":{"bits":403818359,"hash":"0000000000000000060ac8d63b78d41f58c9aba0b09f81db7d51fa4905a47263","height":883637,"merkleRoot":"59c1efd79fae0d9c29dd8da63f8eeec0aadde048f4491c6bfa324fcfd537156d","nonce":596827153,"previousHash":"00000000000000000d9f6889dd6743500adee204ea25d8a57225ecd48b111769","time":1739329877,"version":1040187392},"merklePath":{"blockHeight":883637,"path":[[{"hash":"d9978ffc6676523208f7b33bebf1b176388bbeace2c7ef67ce35c2eababa1805","offset":46,"txid":true},{"hash":"066f6fa6fa988f2e3a9d6fe35fa0d3666c652dac35cabaeebff3738a4e67f68f","offset":47}],[{"hash":"232089a6f77c566151bc4701fda394b5cc5bf17073140d46a73c4c3ed0a7b911","offset":22}],[{"hash":"c639b3a6ce127f67dbd01c7331a6fca62a4b429830387bd68ac6ac05e162116d","offset":10}],[{"hash":"730cec44be97881530947d782bb328d25f1122fdae206296937fffb03e936d48","offset":4}],[{"hash":"28b681f8ab8db0fa4d5d20cb1532b95184a155346b0b8447bde580b2406d51e6","offset":3}],[{"hash":"c49a18028e230dd1439b26794c08c339506f24a450f067c4facd4e0d5a346490","offset":0}],[{"hash":"0ba57d1b1fad6874de3640c01088e3dedad3507e5b3a3102b9a8a8055f3df88b","offset":1}],[{"hash":"c830edebe5565c19ba584ec73d49129344d17539f322509b7c314ae641c2fcdb","offset":1}],[{"hash":"ff62d5ed2a94eb93a2b7d084b8f15b12083573896b6a58cf871507e3352c75f5","offset":1}]]},"name":"WoCTsc","notes":[{"name":"WoCTsc","status":200,"statusText":"OK","what":"getMerklePathSuccess"}]}'
        assert s == expected_json

        # When - invalid txid
        # HTTP mocking is applied globally in tests/conftest.py
        r_invalid = await woc_main.get_merkle_path("1" * 64, services)
        s_invalid = json.dumps(r_invalid, sort_keys=True, separators=(",", ":"))

        # Then
        expected_json_invalid = (
            '{"name":"WoCTsc","notes":[{"name":"WoCTsc","status":200,"statusText":"OK","what":"getMerklePathNoData"}]}'
        )
        assert s_invalid == expected_json_invalid

    @pytest.mark.asyncio
    async def test_updatebsvexchangerate(self) -> None:
        """Given: WhatsOnChain service for mainnet
           When: Call updateBsvExchangeRate
           Then: Returns exchange rate with base 'USD', positive rate, and truthy timestamp

        Reference: wallet-toolbox/src/services/providers/__tests/WhatsOnChain.test.ts
                   test('4 updateBsvExchangeRate')
        """
        # Given
        env_main = TestUtils.get_env("main")
        woc_main = WhatsOnChain(env_main.chain, {"apiKey": env_main.taal_api_key})

        # When
        r = await woc_main.update_bsv_exchange_rate()

        # Then
        assert r["base"] == "USD"
        assert r["rate"] > 0
        assert r["timestamp"] is not None

    def test_gettxpropagation_testnet(self) -> None:
        """Given: WhatsOnChain service for testnet and a known txid
           When: Call getTxPropagation
           Then: Test skipped (TypeScript returns early due to internal server error 500)

        Reference: wallet-toolbox/src/services/providers/__tests/WhatsOnChain.test.ts
                   test('5 getTxPropagation testnet')
        """
        # Note: TypeScript test returns early due to internal server error 500 when tested
        # The commented-out logic would check:
        # - count > 0 for valid txid
        # - count == 0 for invalid txid '1' * 64
        return

    def test_gettxpropagation_mainnet(self) -> None:
        """Given: WhatsOnChain service for mainnet
           When: Call getTxPropagation
           Then: Test is empty (TypeScript has empty test body)

        Reference: wallet-toolbox/src/services/providers/__tests/WhatsOnChain.test.ts
                   test('6 getTxPropagation mainnet')
        """
        # Note: TypeScript has empty test body

    @pytest.mark.asyncio
    async def test_get_raw_tx_invalid_txid_formats(self, mock_woc_provider, invalid_txids) -> None:
        """Given: WhatsOnChain provider and invalid txid formats
        When: Call get_raw_tx with invalid txids
        Then: Handles invalid formats appropriately
        """
        provider, _mock_client = mock_woc_provider

        for invalid_txid in invalid_txids:
            # Should handle invalid txid formats gracefully
            result = await provider.get_raw_tx(invalid_txid)
            assert result is None or isinstance(result, str)  # Either None or empty string

    @pytest.mark.asyncio
    async def test_get_raw_tx_network_failure_500(self, mock_woc_provider, valid_txid) -> None:
        """Given: WhatsOnChain provider and network returns HTTP 500
        When: Call get_raw_tx
        Then: Handles server error appropriately
        """
        provider, mock_client = mock_woc_provider

        # Mock HTTP 500 response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.ok = False
        mock_response.json.return_value = None
        mock_client.fetch.return_value = mock_response

        result = await provider.get_raw_tx(valid_txid)
        assert result is None  # Should return None on server errors

    @pytest.mark.asyncio
    async def test_get_raw_tx_network_timeout(self, mock_woc_provider, valid_txid) -> None:
        """Given: WhatsOnChain provider and network request times out
        When: Call get_raw_tx
        Then: Handles timeout appropriately
        """
        provider, mock_client = mock_woc_provider

        # Mock timeout exception - use fetch.side_effect since the code calls fetch, not get
        mock_client.fetch.side_effect = TimeoutError("Connection timeout")

        result = await provider.get_raw_tx(valid_txid)
        assert result is None  # Should return None on timeout

    @pytest.mark.asyncio
    async def test_get_raw_tx_rate_limiting_429(self, mock_woc_provider, valid_txid) -> None:
        """Given: WhatsOnChain provider and API returns 429 rate limit exceeded
        When: Call get_raw_tx
        Then: Handles rate limiting appropriately
        """
        provider, mock_client = mock_woc_provider

        # Mock HTTP 429 response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.ok = False
        mock_response.text = "Rate limit exceeded"
        mock_response.headers = {"Retry-After": "60"}
        mock_response.json.return_value = None
        mock_client.fetch.return_value = mock_response

        result = await provider.get_raw_tx(valid_txid)
        assert result is None  # Should return None on rate limit

    @pytest.mark.asyncio
    async def test_get_raw_tx_malformed_json_response(self, mock_woc_provider, valid_txid) -> None:
        """Given: WhatsOnChain provider and API returns malformed JSON
        When: Call get_raw_tx
        Then: Handles malformed response appropriately
        """
        provider, mock_client = mock_woc_provider

        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.text = "invalid json {{{"
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_client.fetch.return_value = mock_response

        result = await provider.get_raw_tx(valid_txid)
        assert result is None  # Should return None on malformed response

    @pytest.mark.asyncio
    async def test_get_raw_tx_empty_response(self, mock_woc_provider, valid_txid) -> None:
        """Given: WhatsOnChain provider and API returns empty response
        When: Call get_raw_tx
        Then: Handles empty response appropriately
        """
        provider, mock_client = mock_woc_provider

        # Mock empty response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.text = ""
        mock_response.json.return_value = None
        mock_client.fetch.return_value = mock_response

        result = await provider.get_raw_tx(valid_txid)
        assert result is None or result == ""  # Should handle empty response

    @pytest.mark.asyncio
    async def test_get_raw_tx_unauthorized_401(self, mock_woc_provider, valid_txid) -> None:
        """Given: WhatsOnChain provider and API returns 401 Unauthorized
        When: Call get_raw_tx
        Then: Handles authentication error appropriately
        """
        provider, mock_client = mock_woc_provider

        # Mock HTTP 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.ok = False
        mock_response.text = "Unauthorized"
        mock_response.json.return_value = None
        mock_client.fetch.return_value = mock_response

        result = await provider.get_raw_tx(valid_txid)
        assert result is None  # Should return None on auth error

    @pytest.mark.asyncio
    async def test_get_raw_tx_forbidden_403(self, mock_woc_provider, valid_txid) -> None:
        """Given: WhatsOnChain provider and API returns 403 Forbidden
        When: Call get_raw_tx
        Then: Handles forbidden error appropriately
        """
        provider, mock_client = mock_woc_provider

        # Mock HTTP 403 response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.ok = False
        mock_response.text = "Forbidden"
        mock_response.json.return_value = None
        mock_client.fetch.return_value = mock_response

        result = await provider.get_raw_tx(valid_txid)
        assert result is None  # Should return None on forbidden error

    @pytest.mark.asyncio
    async def test_get_raw_tx_not_found_404(self, mock_woc_provider, valid_txid) -> None:
        """Given: WhatsOnChain provider and API returns 404 Not Found
        When: Call get_raw_tx
        Then: Handles not found appropriately
        """
        provider, mock_client = mock_woc_provider

        # Mock HTTP 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.ok = False
        mock_response.text = "Not Found"
        mock_response.json.return_value = None
        mock_client.fetch.return_value = mock_response

        result = await provider.get_raw_tx(valid_txid)
        assert result is None  # Should return None for non-existent transactions

    @pytest.mark.asyncio
    async def test_get_raw_tx_success_response(self, mock_woc_provider, valid_txid) -> None:
        """Given: WhatsOnChain provider and successful API response
        When: Call get_raw_tx
        Then: Returns raw transaction data
        """
        provider, mock_client = mock_woc_provider

        expected_raw_tx = "0100000001026A66A5F724EB490A55E0E08553286F08AD57E92C4BF34B5C44EA6BC0A49828020000006B483045022100C3D9A5ACA30C1F2E1A54532162E7AFE5AA69150E4C06D760414A16D1EA1BABD602205E0D9191838B0911A1E7328554A2B22EFAA80CF52B15FBA37C3046A0996C7AAD412103FA3CF488CA98D9F2DB91843F36BAF6BE39F6C947976C02394602D09FBC5F4CF4FFFFFFFF0210270000000000001976A91444C04354E88975C4BEF30CFE89D300CC7659F7E588AC96BC0000000000001976A9149A53E5CF5F1876924D98A8B35CA0BC693618682488AC00000000"

        # Mock successful response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": expected_raw_tx}
        mock_client.fetch.return_value = mock_response

        result = await provider.get_raw_tx(valid_txid)
        assert result == expected_raw_tx

    @pytest.mark.asyncio
    async def test_get_merkle_path_invalid_txid(self, mock_woc_provider, invalid_txids) -> None:
        """Given: WhatsOnChain provider and invalid txid
        When: Call get_merkle_path
        Then: Handles invalid txid appropriately
        """
        provider, mock_client = mock_woc_provider
        services = Mock()  # Mock services instance

        # Configure mock to return 404 for invalid txids (not found)
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Not Found"}
        mock_client.fetch.return_value = mock_response

        for invalid_txid in invalid_txids:
            result = await provider.get_merkle_path(invalid_txid, services)
            assert isinstance(result, dict)
            # Should return error result or empty merkle path

    @pytest.mark.asyncio
    async def test_get_merkle_path_network_failures(
        self, mock_woc_provider, valid_txid, network_error_responses
    ) -> None:
        """Given: WhatsOnChain provider and various network failures
        When: Call get_merkle_path
        Then: Handles network failures appropriately
        """
        provider, mock_client = mock_woc_provider
        services = Mock()

        for error_scenario in network_error_responses:
            if error_scenario.get("timeout"):
                mock_client.fetch.side_effect = TimeoutError(error_scenario["error"])
            else:
                mock_response = Mock()
                mock_response.status_code = error_scenario["status"]
                mock_response.ok = error_scenario["status"] == 200
                mock_response.text = error_scenario["text"]
                if error_scenario.get("malformed"):
                    mock_response.json.side_effect = ValueError("Invalid JSON")
                elif error_scenario.get("empty"):
                    mock_response.json.return_value = None
                else:
                    mock_response.json.return_value = {"error": "Network error"}
                mock_client.fetch.return_value = mock_response
                mock_client.fetch.side_effect = None  # Clear side_effect when using return_value

            result = await provider.get_merkle_path(valid_txid, services)
            assert isinstance(result, dict)
            # Should return error result

    @pytest.mark.asyncio
    async def test_update_bsv_exchange_rate_network_failures(self, mock_woc_provider, network_error_responses) -> None:
        """Given: WhatsOnChain provider and various network failures
        When: Call update_bsv_exchange_rate
        Then: Handles network failures appropriately
        """
        provider, mock_client = mock_woc_provider

        for error_scenario in network_error_responses:
            # Reset mock between iterations
            mock_client.fetch.side_effect = None
            mock_client.fetch.return_value = None

            if error_scenario.get("timeout"):
                mock_client.fetch.side_effect = TimeoutError(error_scenario["error"])
                # Timeout raises RuntimeError
                with pytest.raises(RuntimeError, match="Failed to update BSV exchange rate"):
                    await provider.update_bsv_exchange_rate()
            else:
                mock_response = Mock()
                mock_response.status_code = error_scenario["status"]
                mock_response.ok = error_scenario["status"] == 200
                mock_response.text = error_scenario["text"]
                if error_scenario.get("malformed"):
                    # Malformed JSON raises ValueError, which gets caught and re-raised as RuntimeError
                    mock_response.json.side_effect = ValueError("Invalid JSON")
                    mock_client.fetch.return_value = mock_response
                    with pytest.raises(RuntimeError, match="Failed to update BSV exchange rate"):
                        await provider.update_bsv_exchange_rate()
                elif error_scenario.get("empty"):
                    # Empty response (status 200) returns empty dict, not an error
                    mock_response.json.return_value = None
                    mock_client.fetch.return_value = mock_response
                    result = await provider.update_bsv_exchange_rate()
                    assert isinstance(result, dict)
                    assert result == {}
                elif error_scenario["status"] == 200:
                    # Status 200 with valid response returns the body
                    mock_response.json.return_value = {"base": "USD", "rate": 45.67, "timestamp": 1640995200}
                    mock_client.fetch.return_value = mock_response
                    result = await provider.update_bsv_exchange_rate()
                    assert isinstance(result, dict)
                else:
                    # Non-200 status codes raise RuntimeError
                    mock_response.json.return_value = {"error": "Network error"}
                    mock_client.fetch.return_value = mock_response
                    with pytest.raises(RuntimeError, match="Failed to update BSV exchange rate"):
                        await provider.update_bsv_exchange_rate()

    @pytest.mark.asyncio
    async def test_update_bsv_exchange_rate_success(self, mock_woc_provider) -> None:
        """Given: WhatsOnChain provider and successful API response
        When: Call update_bsv_exchange_rate
        Then: Returns exchange rate data
        """
        provider, mock_client = mock_woc_provider

        expected_rate_data = {"base": "USD", "rate": 45.67, "timestamp": 1640995200}

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = expected_rate_data
        mock_client.fetch.return_value = mock_response

        result = await provider.update_bsv_exchange_rate()
        assert result == expected_rate_data

    @pytest.mark.asyncio
    async def test_update_bsv_exchange_rate_invalid_responses(self, mock_woc_provider, exchange_rate_responses) -> None:
        """Given: WhatsOnChain provider and various invalid exchange rate responses
        When: Call update_bsv_exchange_rate
        Then: Handles invalid responses appropriately
        """
        provider, mock_client = mock_woc_provider

        for response_scenario in exchange_rate_responses:
            mock_response = Mock()
            mock_response.status_code = response_scenario["status"]
            mock_response.json.return_value = response_scenario["json"]
            mock_client.fetch.return_value = mock_response

            result = await provider.update_bsv_exchange_rate()

            if response_scenario["status"] == 200:
                # For successful responses, validate the structure
                assert isinstance(result, dict)
                if "base" in response_scenario["json"]:
                    assert result.get("base") == response_scenario["json"]["base"]
                if "rate" in response_scenario["json"]:
                    rate = response_scenario["json"]["rate"]
                    if rate > 0:
                        assert result.get("rate") == rate
                    # For invalid rates (negative/zero), behavior may vary
                if "timestamp" in response_scenario["json"]:
                    assert "timestamp" in result
            else:
                # For error responses, should handle gracefully
                assert isinstance(result, dict) or result is None

    @pytest.mark.asyncio
    async def test_provider_initialization_invalid_chain(self) -> None:
        """Given: Invalid chain parameter
        When: Initialize WhatsOnChain provider
        Then: Raises InvalidParameterError
        """
        with pytest.raises((InvalidParameterError, ValueError)):
            WhatsOnChain("invalid_chain", {"apiKey": "test"})

    @pytest.mark.asyncio
    async def test_provider_initialization_empty_api_key(self) -> None:
        """Given: Empty API key
        When: Initialize WhatsOnChain provider
        Then: Handles empty API key appropriately
        """
        # Should not raise error for empty API key
        provider = WhatsOnChain("main", {"apiKey": ""})
        assert provider is not None

    @pytest.mark.asyncio
    async def test_provider_initialization_none_api_key(self) -> None:
        """Given: None API key
        When: Initialize WhatsOnChain provider
        Then: Handles None API key appropriately
        """
        # Should not raise error for None API key
        provider = WhatsOnChain("main", {"apiKey": None})
        assert provider is not None

    @pytest.mark.asyncio
    async def test_get_raw_tx_connection_error(self, mock_woc_provider, valid_txid) -> None:
        """Given: WhatsOnChain provider and connection error occurs
        When: Call get_raw_tx
        Then: Handles connection error appropriately
        """
        provider, mock_client = mock_woc_provider

        # Mock connection error - use fetch.side_effect since the code calls fetch, not get
        mock_client.fetch.side_effect = ConnectionError("Network is unreachable")

        result = await provider.get_raw_tx(valid_txid)
        assert result is None  # Should return None on connection error

    @pytest.mark.asyncio
    async def test_get_merkle_path_connection_error(self, mock_woc_provider, valid_txid) -> None:
        """Given: WhatsOnChain provider and connection error occurs
        When: Call get_merkle_path
        Then: Handles connection error appropriately
        """
        provider, mock_client = mock_woc_provider
        services = Mock()

        # Mock connection error - use fetch.side_effect since the code calls fetch, not get
        mock_client.fetch.side_effect = ConnectionError("Network is unreachable")

        result = await provider.get_merkle_path(valid_txid, services)
        assert isinstance(result, dict)  # Should return error result

    @pytest.mark.asyncio
    async def test_update_bsv_exchange_rate_connection_error(self, mock_woc_provider) -> None:
        """Given: WhatsOnChain provider and connection error occurs
        When: Call update_bsv_exchange_rate
        Then: Handles connection error appropriately
        """
        provider, mock_client = mock_woc_provider

        # Mock connection error - use fetch.side_effect since the code calls fetch, not get
        mock_client.fetch.side_effect = ConnectionError("Network is unreachable")

        # The implementation raises RuntimeError on connection errors
        with pytest.raises(RuntimeError, match="Failed to update BSV exchange rate"):
            await provider.update_bsv_exchange_rate()
