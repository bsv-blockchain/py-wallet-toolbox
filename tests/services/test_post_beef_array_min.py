"""Minimal non-skipped test for post_beef_array with mocked ARC.

Validates only TS-like result shape per element, without asserting ARC semantics.
"""


from bsv_wallet_toolbox.services import Services


async def test_post_beef_array_minimal() -> None:
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    res_list = services.post_beef_array(["00", "11"])
    assert isinstance(res_list, list)
    assert len(res_list) == 2
    for res in res_list:
        assert isinstance(res, dict)
        assert set(res.keys()) == {"accepted", "txid", "message"}
        assert res["accepted"] in (True, False)
