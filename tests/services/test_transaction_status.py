"""Placeholder tests for `getTransactionStatus` (TS-parity policy).

Overview:
    - Intentionally skipped because there is no corresponding TS/So test to port yet.
    - When upstream TS tests become available, replace this with assertions that
      match the TS behavior and response shapes (e.g., confirmed/unconfirmed).

Rationale:
    - Avoid Python-only expectations; keep parity with TS implementation contracts.

Reference:
    - toolbox/ts-wallet-toolbox/src/services/Services.ts#getTransactionStatus
"""

import pytest


@pytest.mark.skip(reason="No corresponding TS/So test exists yet; placeholder only.")
def test_get_transaction_status_placeholder() -> None:
    """Placeholder for `getTransactionStatus` until TS/So test is available."""


