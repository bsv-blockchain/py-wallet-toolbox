"""Placeholder tests for `postBeef`/`postBeefArray` (TS-parity policy).

Overview:
    - Intentionally skipped because there is no corresponding TS/So test to port yet.
    - When upstream TS tests become available, replace these with assertions that
      match the TS behavior, shapes, and edge cases (success, double-spend, errors).

Rationale:
    - Keep placeholders to make intended coverage explicit while avoiding Python-only
      expectations that drift from TS.

Reference:
    - toolbox/ts-wallet-toolbox/src/services/Services.ts#postBeef
    - toolbox/ts-wallet-toolbox/src/services/Services.ts#postBeefArray
"""

import pytest

# =============================
# Section B: Minimal (enabled)
# =============================
from bsv_wallet_toolbox.services import Services


async def test_post_beef_arc_minimal_enabled() -> None:
    """Ensure ARC path returns TS-like shape for single BEEF (mocked).

    - Uses conftest's FakeClient to avoid network.
    - Asserts only TS-like return shape and basic types.
    """
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    res = services.post_beef("00")
    assert isinstance(res, dict)
    assert set(res.keys()) == {"accepted", "txid", "message"}
    assert res["accepted"] in (True, False)


async def test_post_beef_array_arc_minimal_enabled() -> None:
    """Ensure ARC path returns TS-like shape for multiple BEEFs (mocked).

    - Uses conftest's FakeClient to avoid network.
    - Asserts only TS-like return shape and basic types.
    """
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    res_list = services.post_beef_array(["00", "01"])
    assert isinstance(res_list, list)
    assert len(res_list) == 2
    for res in res_list:
        assert isinstance(res, dict)
        assert set(res.keys()) == {"accepted", "txid", "message"}
        assert res["accepted"] in (True, False)


def test_post_beef_placeholder() -> None:
    """Placeholder for `postBeef` until TS/So test is available."""


def test_post_beef_array_placeholder() -> None:
    """Placeholder for `postBeefArray` until TS/So test is available."""


"""Unit tests for postBeef service.

This module tests postBeef service functionality for mainnet and testnet.

Reference: wallet-toolbox/src/services/__tests/postBeef.test.ts
"""


try:
    from bsv_wallet_toolbox.beef import BeefTx

    from bsv_wallet_toolbox.services import Services
    from bsv_wallet_toolbox.utils import Setup, TestUtils, logger

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class TestPostBeef:
    """Test suite for postBeef service.

    Reference: wallet-toolbox/src/services/__tests/postBeef.test.ts
               describe.skip('postBeef service tests')
    """

    def test_postbeef_mainnet(self) -> None:
        """Given: Services with mainnet configuration
           When: Post BEEF with valid transactions and then with double spend
           Then: First post succeeds, second detects double spend

        Reference: wallet-toolbox/src/services/__tests/postBeef.test.ts
                   test('0 postBeef mainnet')
        """
        # Given
        if Setup.no_env("main"):
            return

        services = self._create_services("main")

        # When/Then
        self._post_beef_test(services)

    def test_postbeef_testnet(self) -> None:
        """Given: Services with testnet configuration
           When: Post BEEF with valid transactions and then with double spend
           Then: First post succeeds, second detects double spend

        Reference: wallet-toolbox/src/services/__tests/postBeef.test.ts
                   test('1 postBeef testnet')
        """
        # Given
        if Setup.no_env("test"):
            return

        services = self._create_services("test")

        # When/Then
        self._post_beef_test(services)

    def _create_services(self, chain: str) -> "Services":
        """Create Services instance with API keys from environment.

        Reference: wallet-toolbox/src/services/__tests/postBeef.test.ts
                   function createServices(chain: sdk.Chain)
        """
        env = TestUtils.get_env(chain)
        options = Services.create_default_options(chain)

        if env.taal_api_key:
            options.taal_api_key = env.taal_api_key
            options.arc_config.api_key = env.taal_api_key
        if env.whatsonchain_api_key:
            options.whats_on_chain_api_key = env.whatsonchain_api_key
        if env.bitails_api_key:
            options.bitails_api_key = env.bitails_api_key

        logger(
            f"""
API Keys:
TAAL {options.taal_api_key[:20] if options.taal_api_key else 'N/A'}
WHATSONCHAIN {options.whats_on_chain_api_key[:20] if options.whats_on_chain_api_key else 'N/A'}
BITAILS {options.bitails_api_key[:20] if options.bitails_api_key else 'N/A'}
"""
        )

        return Services(options)

    async def _post_beef_test(self, services: "Services") -> None:
        """Test posting BEEF with valid transactions and double spend detection.

        Reference: wallet-toolbox/src/services/__tests/postBeef.test.ts
                   async function postBeefTest(services: Services)
        """
        # Given
        chain = services.chain
        if Setup.no_env(chain):
            return

        c = TestUtils.create_no_send_tx_pair(chain)
        txids = [c.txid_do, c.txid_undo]

        # When - Post valid BEEF
        rs = services.post_beef(c.beef, txids)

        # Then - Verify success
        for r in rs:
            log_func = logger if r.status == "success" else print
            log_func(f"r.notes = {r.notes}")
            log_func(f"r.txidResults = {r.txid_results}")
            assert r.status == "success"

            for txid in txids:
                tr = next((tx for tx in r.txid_results if tx.txid == txid), None)
                assert tr is not None
                assert tr.status == "success"

        # When - Replace Undo transaction with double spend transaction and send again
        beef2 = c.beef.clone()
        beef2.txs[-1] = BeefTx.from_tx(c.double_spend_tx)
        txids2 = [c.txid_do, c.double_spend_tx.id("hex")]

        r2s = services.post_beef(beef2, txids2)

        # Then - Verify double spend detection
        for r2 in r2s:
            log_func = logger if r2.status == "error" else print
            log_func(f"r2.notes = {r2.notes}")
            log_func(f"r2.txidResults = {r2.txid_results}")
            assert r2.status == "error"

            for txid in txids2:
                tr = next((tx for tx in r2.txid_results if tx.txid == txid), None)
                assert tr is not None

                if txid == c.txid_do:
                    assert tr.status == "success"
                else:
                    assert tr.status == "error"
                    assert tr.double_spend is True
                    if tr.competing_txs is not None:
                        assert tr.competing_txs == [c.txid_undo]
