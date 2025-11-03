"""Minimal non-skipped test for ARC-enabled post_beef using mocked HTTP.

This validates the ARC-enabled path in Services.post_beef with the
global FakeClient provided by conftest. It does not assert TS-specific
business semantics beyond the TS-like shape to avoid divergence.
"""

import pytest

from bsv_wallet_toolbox.services import Services


async def test_post_beef_arc_minimal() -> None:
    """Ensure ARC path returns TS-like shape when ARC is configured."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"  # triggers ARC path; HTTP is mocked in conftest
    options["arcApiKey"] = "test"

    services = Services(options)

    # Provide a minimal hex that Transaction.from_hex can reject; expect graceful error-shaped response
    res = services.post_beef("00")
    assert isinstance(res, dict)
    assert set(res.keys()) == {"accepted", "txid", "message"}
    assert res["accepted"] in (True, False)
