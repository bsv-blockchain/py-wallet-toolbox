"""Manual tests for getBeefForTransaction service.

These tests verify BEEF (Background Evaluation Extended Format) retrieval
for specific transactions.

Implementation Intent:
- Test BEEF retrieval from transaction IDs
- Verify BEEF format and structure
- Test BEEF validation

Why Manual Test:
1. Requires live blockchain service connection
2. Uses actual transaction data from blockchain
3. Needs BEEF service endpoint
4. Tests real BEEF generation and retrieval

Reference: wallet-toolbox/test/WalletClient/getBeefForTransaction.man.test.ts (deprecated)
           Functionality moved to services integration tests
"""

import logging

import pytest
from bsv_wallet_toolbox.beef import Beef

from bsv_wallet_toolbox.services import BEEFService

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="Waiting for BEEF service implementation")
@pytest.mark.asyncio
async def test_get_beef_for_transaction() -> None:
    """Given: Transaction ID
       When: Request BEEF for transaction
       Then: BEEF data is returned and valid

    Note: This functionality is now part of services integration tests.
          TypeScript deprecated this as a standalone test.

    Reference: wallet-toolbox/test/WalletClient/getBeefForTransaction.man.test.ts
    """


    # Sample transaction ID
    txid = "6dd8e416dfaf14c04899ccad2bf76a67c1d5598fece25cf4dcb7a076012b7d8d"

    # Get BEEF
    beef_service = BEEFService()
    beef_data = await beef_service.get_beef_for_transaction(txid)

    # Validate BEEF format
    beef = Beef.from_binary(beef_data)
    assert beef is not None
    assert len(beef.txs) > 0

    logger.info(f"Retrieved BEEF for transaction {txid}: {len(beef.txs)} transactions")
