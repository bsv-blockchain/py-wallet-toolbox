"""Minimal TS-like shape tests for create_signature / verify_signature.

Comprehensive existing tests are kept and skipped per policy.
This tests only return value shapes and basic behavior.
"""

import hashlib


def test_create_signature_and_verify_roundtrip(wallet_with_key_deriver):
    # Sign data (implicit: direct SHA-256 hash signature)
    args = {
        "data": b"hello world",
        "protocolID": [2, "auth message signature"],
        "keyID": "default",
        "counterparty": "self",
    }
    res = wallet_with_key_deriver.create_signature(args)
    assert isinstance(res, dict)
    assert "signature" in res
    sig = res["signature"]
    # JSON byte array (list[int])
    assert isinstance(sig, list)
    assert all(isinstance(x, int) and 0 <= x <= 255 for x in sig)

    # Verify OK
    vres = wallet_with_key_deriver.verify_signature(
        {
            "data": b"hello world",
            "protocolID": [2, "auth message signature"],
            "keyID": "default",
            "counterparty": "self",
            "signature": sig,
        }
    )
    assert isinstance(vres, dict)
    assert vres.get("valid") is True


def test_verify_signature_fail_on_modified_data(wallet_with_key_deriver):
    args = {
        "data": b"original",
        "protocolID": [2, "auth message signature"],
        "keyID": "default",
    }
    res = wallet_with_key_deriver.create_signature(args)
    sig = res["signature"]

    # Verify with different data → False
    vres = wallet_with_key_deriver.verify_signature(
        {
            "data": b"tampered",
            "protocolID": [2, "auth message signature"],
            "keyID": "default",
            "signature": sig,
        }
    )
    assert vres.get("valid") is False


def test_direct_hash_sign_and_verify(wallet_with_key_deriver):
    # Direct pre-hash signature/verification
    # Use counterparty='self' for consistency - same key for create and verify
    data = b"hash me"
    digest = hashlib.sha256(data).digest()

    sres = wallet_with_key_deriver.create_signature(
        {
            "hashToDirectlySign": digest,
            "protocolID": [2, "auth message signature"],
            "keyID": "default",
            "counterparty": "self",
        }
    )
    sig = sres["signature"]

    vres = wallet_with_key_deriver.verify_signature(
        {
            "hashToDirectlyVerify": digest,
            "protocolID": [2, "auth message signature"],
            "keyID": "default",
            "signature": sig,
            "counterparty": "self",
        }
    )
    assert vres.get("valid") is True
