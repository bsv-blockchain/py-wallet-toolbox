"""Unit tests for LiveIngestorWhatsOnChainPoll.

This module tests live header ingestion from WhatsOnChain API via polling.

Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/LiveIngestorWhatsOnChainPoll.test.ts
"""

import asyncio

import pytest

try:
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.api import BlockHeader
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.ingest import LiveIngestorWhatsOnChainPoll

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class TestLiveIngestorWhatsOnChainPoll:
    """Test suite for LiveIngestorWhatsOnChainPoll.

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/LiveIngestorWhatsOnChainPoll.test.ts
               describe('LiveIngestorWhatsOnChainPoll tests')
    """

    @pytest.mark.integration
    def test_listen_for_first_new_header(self) -> None:
        """Given: LiveIngestorWhatsOnChainPoll with mainnet options
           When: Start listening for new headers
           Then: Receives at least one new header and can log it

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/LiveIngestorWhatsOnChainPoll.test.ts
                   test('0 listen for first new header')
        """
        if not IMPORTS_AVAILABLE:
            pytest.skip("LiveIngestorWhatsOnChainPoll not available")

        # Given
        live_headers: list[BlockHeader] = []
        options = LiveIngestorWhatsOnChainPoll.create_live_ingestor_whats_on_chain_options("main")
        ingestor = LiveIngestorWhatsOnChainPoll(options)

        # When
        p = ingestor.start_listening(live_headers)
        log = ""
        count = 0

        while True:
            if live_headers:
                h = live_headers.pop(0)
                log += f"{h.height} {h.hash}\n"
                count += 1
            else:
                if log:
                    print(f"LiveIngestorWhatsOnChain received {count} headers:\n{log}")
                    log = ""
                    break
                asyncio.sleep(0.1)

        # Then
        ingestor.stop_listening()
        p
        assert count > 0
