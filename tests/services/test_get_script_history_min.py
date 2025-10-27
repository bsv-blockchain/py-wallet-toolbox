"""Minimal TS-like shape tests for get_script_history using mocked HTTP.

- Uses global FakeClient from tests/conftest.py (no network calls).
- Verifies only the return shape and basic types, not provider semantics.
"""

import pytest

from bsv_wallet_toolbox.services import Services


@pytest.mark.asyncio
async def test_get_script_history_minimal_normal() -> None:
    """Normal case should return dict with confirmed/unconfirmed arrays."""
    services = Services(Services.create_default_options("main"))

    res = await services.get_script_history("aa" * 32)
    assert isinstance(res, dict)
    assert "confirmed" in res and "unconfirmed" in res
    assert isinstance(res["confirmed"], list)
    assert isinstance(res["unconfirmed"], list)


@pytest.mark.asyncio
async def test_get_script_history_minimal_empty() -> None:
    """Sentinel hash should yield empty confirmed/unconfirmed arrays."""
    services = Services(Services.create_default_options("main"))

    res = await services.get_script_history("1" * 64)
    assert isinstance(res, dict)
    assert res.get("confirmed") == []
    assert res.get("unconfirmed") == []


