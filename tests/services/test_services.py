"""Unit tests for WhatsOnChain services.

This module tests WhatsOnChain API integration for header retrieval.

Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/WhatsOnChainServices.test.ts
"""

import json

import pytest

pytestmark = pytest.mark.skip(reason="Module not yet implemented")

try:
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.ingest import WhatsOnChainServices
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.util import (
        ChaintracksFetch,
        HeightRange,
        deserialize_block_header,
    )

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class _HeaderListeners:
    """Helper class for header listener stubs."""

    @staticmethod
    def woc_headers_bulk_listener(*_args, **_kwargs) -> bool:
        """Stub for bulk header listening from WhatsOnChain.

        Accepts: height_from, height_to, header_handler, error_handler, stop_token, chain
        """
        # This is a placeholder for the actual implementation
        # The test that uses this is skipped, so it won't be called in normal testing
        return True

    @staticmethod
    def woc_headers_live_listener(*_args, **_kwargs) -> bool:
        """Stub for live header listening from WhatsOnChain.

        Accepts: enqueue_handler, error_handler, stop_token, chain, logger
        """
        # This is a placeholder for the actual implementation
        # The test that uses this is skipped, so it won't be called in normal testing
        return True


# Create aliases for compatibility with test code
WocHeadersBulkListener = _HeaderListeners.woc_headers_bulk_listener
WocHeadersLiveListener = _HeaderListeners.woc_headers_live_listener


class TestServices:
    """Test suite for WhatsOnChain services.

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/WhatsOnChainServices.test.ts
               describe('WhatsOnChainServices tests')
    """

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WhatsOnChainServices implementation")
    def test_getheaderbyhash(self) -> None:
        """Given: WhatsOnChainServices for mainnet
           When: Get header by known hash
           Then: Returns header with correct height 781348

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/WhatsOnChainServices.test.ts
                   test('getHeaderByHash')
        """
        # Given
        chain = "main"
        options = WhatsOnChainServices.create_whats_on_chain_services_options(chain)
        woc = WhatsOnChainServices(options)

        # When
        header = woc.get_header_by_hash("000000000000000001b3e99847d57ff3e0bfc4222cea5c29f10bf24387a250a2")

        # Then
        assert header is not None
        assert header.height == 781348

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WhatsOnChainServices implementation")
    def test_getchaintipheight(self) -> None:
        """Given: WhatsOnChainServices for mainnet
           When: Get chain tip height
           Then: Returns height > 600000

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/WhatsOnChainServices.test.ts
                   test('getChainTipHeight')
        """
        # Given
        chain = "main"
        options = WhatsOnChainServices.create_whats_on_chain_services_options(chain)
        woc = WhatsOnChainServices(options)

        # When
        height = woc.get_chain_tip_height()

        # Then
        assert height > 600000

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WhatsOnChainServices implementation")
    def test_listen_for_old_block_headers(self) -> None:
        """Given: WhatsOnChainServices and height range
           When: Listen for old block headers via WocHeadersBulkListener
           Then: Receives headers for the requested height range

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/WhatsOnChainServices.test.ts
                   test.skip('0 listenForOldBlockHeaders')

        Note: TypeScript has test.skip() because the service appears to be deprecated.
              This Python test matches TypeScript structure but is also expected to be skipped.
        """
        # Given
        chain = "main"
        options = WhatsOnChainServices.create_whats_on_chain_services_options(chain)
        woc = WhatsOnChainServices(options)

        height = woc.get_chain_tip_height()
        assert height > 600000

        headers_old = []
        errors_old = []
        stop_old_listeners_token = {"stop": None}

        def stop_old_listener() -> None:
            if stop_old_listeners_token["stop"]:
                stop_old_listeners_token["stop"]()

        # When

        ok_old = WocHeadersBulkListener(
            height - 4,
            height,
            lambda h: headers_old.append(h),
            lambda code, message: errors_old.append({"code": code, "message": message}) or True,
            stop_old_listeners_token,
            chain,
        )

        # Then
        assert ok_old is True
        assert len(errors_old) == 0
        assert len(headers_old) >= 4

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WhatsOnChainServices implementation")
    def test_listen_for_new_block_headers(self) -> None:
        """Given: WhatsOnChainServices
           When: Listen for new block headers via WocHeadersLiveListener
           Then: Receives new headers as they arrive

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/WhatsOnChainServices.test.ts
                   test.skip('1 listenForNewBlockHeaders')

        Note: TypeScript has test.skip() because the service appears to be deprecated.
              This Python test matches TypeScript structure but is also expected to be skipped.
        """
        # Given
        chain = "main"
        options = WhatsOnChainServices.create_whats_on_chain_services_options(chain)
        woc = WhatsOnChainServices(options)

        height = woc.get_chain_tip_height()
        assert height > 600000

        headers_new = []
        errors_new = []
        stop_new_listeners_token = {"stop": None}

        def enqueue_handler(h) -> None:
            headers_new.append(h)
            if len(headers_new) >= 1 and stop_new_listeners_token["stop"]:
                stop_new_listeners_token["stop"]()

        def error_handler(code, message) -> bool:
            errors_new.append({"code": code, "message": message})
            return True

        # When

        ok_new = WocHeadersLiveListener(enqueue_handler, error_handler, stop_new_listeners_token, chain, print)

        # Then
        if errors_new:

            print(json.dumps(errors_new))
        assert len(errors_new) == 0
        assert ok_new is True
        assert len(headers_new) >= 0

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WhatsOnChainServices implementation")
    def test_get_latest_header_bytes(self) -> None:
        """Given: ChaintracksFetch instance
           When: Download latest header bytes from WhatsOnChain
           Then: Successfully downloads header bytes and can deserialize latest header

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/WhatsOnChainServices.test.ts
                   test('2 get latest header bytes')
        """
        # Given
        fetch = ChaintracksFetch()

        # When
        bytes_data = fetch.download("https://api.whatsonchain.com/v1/bsv/main/block/headers/latest")
        print(f"headers: {len(bytes_data) / 80}")

        latest = fetch.download("https://api.whatsonchain.com/v1/bsv/main/block/headers/latest?count=1")
        bh = deserialize_block_header(latest, 0, 0)
        print(f"latest hash: {bh.hash}")

        # Then
        assert len(bytes_data) > 0
        assert bh.hash is not None

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WhatsOnChainServices implementation")
    def test_get_headers(self) -> None:
        """Given: ChaintracksFetch instance
           When: Fetch headers JSON from WhatsOnChain
           Then: Returns array of headers with height, hash, confirmations, nTx

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/WhatsOnChainServices.test.ts
                   test('3 get headers')
        """
        # Given
        fetch = ChaintracksFetch()

        # When
        headers = fetch.fetch_json("https://api.whatsonchain.com/v1/bsv/main/block/headers")

        log = ""
        for h in headers:
            log += f"{h['height']} {h['hash']} {h['confirmations']} {h['nTx']}\n"
        print(log)

        # Then
        assert len(headers) > 0
        assert "height" in headers[0]
        assert "hash" in headers[0]

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for WhatsOnChainServices implementation")
    def test_get_header_byte_file_links(self) -> None:
        """Given: WhatsOnChainServices instance
           When: Get header byte file links for height range 907123-911000
           Then: Returns 3 files with correct height ranges

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/WhatsOnChainServices.test.ts
                   test('4 get header byte file links')
        """
        # Given
        ChaintracksFetch()
        woc = WhatsOnChainServices(WhatsOnChainServices.create_whats_on_chain_services_options("main"))

        # When
        files = woc.get_header_byte_file_links(HeightRange(907123, 911000))

        # Then
        assert len(files) == 3
        assert files[0].range.min_height == 906001
        assert files[0].range.max_height == 908000
        assert files[1].range.min_height == 908001
        assert files[1].range.max_height == 910000
        assert files[2].range.min_height == 910001
        assert files[2].range.max_height > 910001
