"""Minimal TS-like shape tests for create_hmac / verify_hmac."""


def test_create_hmac_and_verify_roundtrip(wallet_with_key_deriver):
    data = b"auth data"
    args = {"data": data, "protocolID": [2, "context"], "keyID": "default", "counterparty": "self"}
    res = wallet_with_key_deriver.create_hmac(args)
    assert isinstance(res, dict)
    tag = res.get("hmac")
    assert isinstance(tag, list)
    assert all(isinstance(x, int) and 0 <= x <= 255 for x in tag)

    vres = wallet_with_key_deriver.verify_hmac(
        {"data": data, "hmac": tag, "protocolID": [2, "context"], "keyID": "default", "counterparty": "self"}
    )
    assert isinstance(vres, dict)
    assert vres.get("valid") is True


def test_verify_hmac_fail_on_tamper(wallet_with_key_deriver):
    data = b"auth data"
    res = wallet_with_key_deriver.create_hmac({"data": data, "protocolID": [2, "context"], "keyID": "default"})
    tag = list(res["hmac"])  # mutate one byte in JSON array
    tag[0] = (int(tag[0]) ^ 0x01) & 0xFF
    vres = wallet_with_key_deriver.verify_hmac(
        {"data": data, "hmac": bytes(tag), "protocolID": [2, "context"], "keyID": "default"}
    )
    assert vres.get("valid") is False
