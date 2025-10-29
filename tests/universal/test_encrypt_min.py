"""Minimal TS-like shape tests for encrypt/decrypt.

- Validate only shapes and basic roundtrip behavior.
"""

import pytest


@pytest.mark.asyncio
async def test_encrypt_decrypt_roundtrip(wallet_with_key_deriver):
    plaintext = b"secret message"
    args = {
        "plaintext": plaintext,
        "protocolID": [2, "ctx"],
        "keyID": "default",
        "counterparty": "self",
    }
    enc = await wallet_with_key_deriver.encrypt(args)
    assert isinstance(enc, dict)
    assert "ciphertext" in enc
    ct = enc["ciphertext"]
    assert isinstance(ct, (bytes, bytearray))

    dec = await wallet_with_key_deriver.decrypt(
        {
            "ciphertext": ct,
            "protocolID": [2, "ctx"],
            "keyID": "default",
            "counterparty": "self",
        }
    )
    assert isinstance(dec, dict)
    assert dec.get("plaintext") == plaintext


@pytest.mark.asyncio
async def test_encrypt_requires_bytes(wallet_with_key_deriver):
    with pytest.raises(Exception):
        await wallet_with_key_deriver.encrypt(
            {"plaintext": "not-bytes", "protocolID": [2, "ctx"], "keyID": "default"}
        )


