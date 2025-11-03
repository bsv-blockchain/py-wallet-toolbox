"""Placeholder tests for `getChainTracker` (TS-parity policy).

Overview:
    - This file intentionally contains only skipped placeholder tests because
      there is no corresponding TypeScript/So test to port at the moment.
    - Once upstream TS tests exist, replace this with assertions matching the
      TS behavior and response shapes.

Rationale:
    - We keep a placeholder to make the intended coverage explicit and to
      avoid diverging from TS by inventing Python-only expectations.

Reference:
    - toolbox/ts-wallet-toolbox/src/services/Services.ts#getChainTracker
"""

import pytest


@pytest.mark.skip(reason="No corresponding TS/So test exists yet; placeholder only.")
def test_get_chain_tracker_placeholder() -> None:
    """Placeholder for `getChainTracker` until TS/So test is available."""
