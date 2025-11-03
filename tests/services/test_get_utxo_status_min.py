"""Minimal TS-like shape tests for get_utxo_status using mocked HTTP.

- Uses global FakeClient from tests/conftest.py (no network calls).
- Verifies only the return shape and basic types, not provider semantics.
"""

import pytest

from bsv_wallet_toolbox.services import Services


async def test_get_utxo_status_minimal_normal() -> None:
    """Normal case should return a dict with details: list of entries."""
    services = Services(Services.create_default_options("main"))

    res = services.get_utxo_status("aa" * 32)
    assert isinstance(res, dict)
    assert "details" in res
    assert isinstance(res["details"], list)
    if res["details"]:
        entry = res["details"][0]
        assert isinstance(entry, dict)
        assert "outpoint" in entry
        assert "spent" in entry
        assert isinstance(entry["spent"], bool)


async def test_get_utxo_status_minimal_not_found() -> None:
    """Sentinel hash should yield an empty details list (not_found-like)."""
    services = Services(Services.create_default_options("main"))

    res = services.get_utxo_status("1" * 64)
    assert isinstance(res, dict)
    assert isinstance(res.get("details"), list)
    assert res["details"] == []
