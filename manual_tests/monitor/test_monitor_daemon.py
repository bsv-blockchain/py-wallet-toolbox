"""Manual tests for MonitorDaemon.

This module tests MonitorDaemon functionality for running monitor as a daemon.

Reference: wallet-toolbox/src/monitor/__test/MonitorDaemon.man.test.ts
"""

import pytest

try:
    from bsv_wallet_toolbox.monitor import MonitorDaemon

    from bsv_wallet_toolbox.services import Services
    from bsv_wallet_toolbox.services.chaintracker.chaintracks import (
        Chaintracks,
        create_default_no_db_chaintracks_options,
    )
    from bsv_wallet_toolbox.utils import TestUtils

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class TestMonitorDaemonManual:
    """Manual test suite for MonitorDaemon.

    Reference: wallet-toolbox/src/monitor/__test/MonitorDaemon.man.test.ts
               describe('MonitorDaemon tests')
    """

    async def _test_body(self, chain: str) -> None:
        """Test body for MonitorDaemon with specified chain.

        Reference: wallet-toolbox/src/monitor/__test/MonitorDaemon.man.test.ts
                   async function test0Body(chain: Chain)
        """
        # Given
        env = TestUtils.get_env(chain)

        services_options = Services.create_default_options(chain)
        if env.taal_api_key:
            services_options["taalApiKey"] = env.taal_api_key
            services_options["arcConfig"]["apiKey"] = env.taal_api_key
        if env.whatsonchain_api_key:
            services_options["whatsOnChainApiKey"] = env.whatsonchain_api_key
        if env.bitails_api_key:
            services_options["bitailsApiKey"] = env.bitails_api_key

        max_retained = 32
        chaintracks_options = create_default_no_db_chaintracks_options(
            chain, env.whatsonchain_api_key, None, max_retained
        )
        chaintracks = Chaintracks(chaintracks_options)
        services_options["chaintracks"] = chaintracks

        d = MonitorDaemon(
            {
                "chain": "test",
                "mySQLConnection": env.cloud_mysql_connection,
                "servicesOptions": services_options,
                "chaintracks": chaintracks,
            }
        )

        # When
        await d.run_daemon()

        # Then - daemon runs until interrupted
        # (no assertions, this is a long-running daemon test)

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for MonitorDaemon implementation")
    @pytest.mark.asyncio
    async def test_mainnet(self) -> None:
        """Given: MonitorDaemon configured for mainnet
           When: Run daemon with mainnet configuration
           Then: Daemon runs until interrupted

        Reference: wallet-toolbox/src/monitor/__test/MonitorDaemon.man.test.ts
                   test('0 mainnet')
        """
        await self._test_body("main")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for MonitorDaemon implementation")
    @pytest.mark.asyncio
    async def test_testnet(self) -> None:
        """Given: MonitorDaemon configured for testnet
           When: Run daemon with testnet configuration
           Then: Daemon runs until interrupted

        Reference: wallet-toolbox/src/monitor/__test/MonitorDaemon.man.test.ts
                   test('0a testnet')
        """
        await self._test_body("test")
