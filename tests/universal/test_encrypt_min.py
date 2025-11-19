"""Minimal TS-like shape tests for encrypt/decrypt.

- Validate only shapes and basic roundtrip behavior.
"""

import pytest


def test_encrypt_decrypt_roundtrip(wallet_with_key_deriver):
    plaintext = b"secret message"
    args = {
        "plaintext": plaintext,
        "protocolID": [2, "encryption"],
        "keyID": "default",
        "counterparty": "self",
    }
    enc = wallet_with_key_deriver.encrypt(args)
    assert isinstance(enc, dict)
    assert "ciphertext" in enc
    ct = enc["ciphertext"]
    # JSON byte array
    assert isinstance(ct, list)
    assert all(isinstance(x, int) and 0 <= x <= 255 for x in ct)

    dec = wallet_with_key_deriver.decrypt(
        {
            "ciphertext": ct,
            "protocolID": [2, "encryption"],
            "keyID": "default",
            "counterparty": "self",
        }
    )
    assert isinstance(dec, dict)
    pt = dec.get("plaintext")
    assert isinstance(pt, list)
    assert bytes(pt) == plaintext


def test_encrypt_requires_bytes(wallet_with_key_deriver):
    with pytest.raises(Exception):
        wallet_with_key_deriver.encrypt({"plaintext": "not-bytes", "protocolID": [2, "encryption"], "keyID": "default"})
