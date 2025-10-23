"""Manual tests for ARC (Atomic Router and Cache) service.

These tests verify ARC service integration for transaction broadcast and validation.

Implementation Intent:
- Test ARC transaction broadcast
- Test ARC transaction validation
- Test ARC endpoint configuration
- Verify ARC response handling

Why Manual Test:
1. Requires live ARC service endpoint
2. Uses real transaction broadcast
3. Needs network connectivity
4. Tests actual blockchain service integration

Note: TypeScript does not have a dedicated arc.man.test.ts file.
      ARC functionality is tested within other manual tests (e.g., walletLive, operations).
      This file is a Python-specific consolidation of ARC-related manual tests.

Reference: wallet-toolbox/test/Wallet/live/walletLive.man.test.ts (ARC-related tests)
"""

import logging

import pytest

from bsv_wallet_toolbox.services import ARCService
from bsv_wallet_toolbox.wallet import Wallet

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="Waiting for ARC service implementation")
@pytest.mark.asyncio
async def test_arc_broadcast_transaction() -> None:
    """Given: Wallet with transaction
       When: Broadcast transaction to ARC
       Then: Transaction is accepted and txid is returned

    Note: TypeScript tests ARC broadcast within walletLive and operations tests.
          This is a Python-specific consolidation test.
    """

    # Create wallet and transaction
    wallet = Wallet(chain="test")
    tx_result = await wallet.create_action(
        {
            "description": "test transaction for ARC",
            "outputs": [
                {
                    "satoshis": 1,
                    "lockingScript": "76a914" + "00" * 20 + "88ac",  # P2PKH to dummy address
                    "outputDescription": "test output",
                }
            ],
        }
    )

    # Broadcast to ARC
    arc_service = ARCService(endpoint="https://arc-testnet.taal.com")
    result = await arc_service.broadcast_transaction(tx_result["tx"])

    assert result["txid"] == tx_result["txid"]
    logger.info(f"Successfully broadcast transaction to ARC: {result['txid']}")

    await wallet.destroy()


@pytest.mark.skip(reason="Waiting for ARC service implementation")
@pytest.mark.asyncio
async def test_arc_validate_transaction() -> None:
    """Given: Transaction data
       When: Validate transaction with ARC
       Then: Validation result is returned

    Note: TypeScript tests ARC validation within integration tests.
          This is a Python-specific consolidation test.
    """

    # Sample transaction data
    txid = "6dd8e416dfaf14c04899ccad2bf76a67c1d5598fece25cf4dcb7a076012b7d8d"

    # Validate with ARC
    arc_service = ARCService(endpoint="https://arc-testnet.taal.com")
    result = await arc_service.validate_transaction(txid)

    assert "status" in result
    logger.info(f"ARC validation result: {result}")
