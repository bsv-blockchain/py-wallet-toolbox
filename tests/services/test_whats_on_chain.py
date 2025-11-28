"""Unit tests for WhatsOnChain service provider.

This module tests WhatsOnChain functionality including getRawTx, getMerklePath,
updateBsvExchangeRate, and getTxPropagation.

Reference: wallet-toolbox/src/services/providers/__tests/WhatsOnChain.test.ts
"""

import json

import pytest

try:
    from bsv_wallet_toolbox.services import Services
    from bsv_wallet_toolbox.services.providers import WhatsOnChain
    from bsv_wallet_toolbox.utils import TestUtils

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


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
        s = json.dumps(r, sort_keys=True, separators=(",", ":"))

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
        s = json.dumps(r, sort_keys=True, separators=(",", ":"))

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
