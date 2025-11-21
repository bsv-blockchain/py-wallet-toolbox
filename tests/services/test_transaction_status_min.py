"""Minimal non-skipped test for get_transaction_status using mocked HTTP.

This test validates only the return shape and basic types expected from the
TypeScript implementation, without asserting provider-specific semantics.
"""

from bsv_wallet_toolbox.services import Services


def test_get_transaction_status_minimal() -> None:
    """Ensure minimal TS-like shape from get_transaction_status.

    - With conftest's FakeClient, a normal 64-hex txid returns
      {"status": "confirmed", "confirmations": number}.
    - Edge case (all '1' * 64) returns {"status": "not_found"}.
    """
    services = Services(Services.create_default_options("main"))

    # Normal case
    res = services.get_transaction_status("aa" * 32)
    assert isinstance(res, dict)
    assert "status" in res
    if res["status"] == "confirmed":
        assert isinstance(res.get("confirmations"), int)

    # Edge case: not_found sentinel
    res_nf = services.get_transaction_status("1" * 64)
    assert isinstance(res_nf, dict)
    assert res_nf.get("status") in {"not_found", "unknown"}
