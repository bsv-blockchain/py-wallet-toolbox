"""Minimal TS-like shape tests for create_signature / verify_signature.

既存の包括的テストは保持・スキップ方針。.cursor/rules/test-editing-rules.md に準拠し、
ここでは戻り値の形状と基本的挙動のみ検証する。
"""

import pytest


@pytest.mark.asyncio
async def test_create_signature_and_verify_roundtrip(wallet_with_key_deriver):
    # Sign data (implicit: SHA-256 のハッシュを直接署名)
    args = {
        "data": b"hello world",
        "protocolID": [2, "auth message signature"],
        "keyID": "default",
        "counterparty": "self",
    }
    res = await wallet_with_key_deriver.create_signature(args)
    assert isinstance(res, dict)
    assert "signature" in res
    sig = res["signature"]
    assert isinstance(sig, (bytes, bytearray))

    # Verify OK
    vres = await wallet_with_key_deriver.verify_signature(
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


@pytest.mark.asyncio
async def test_verify_signature_fail_on_modified_data(wallet_with_key_deriver):
    args = {
        "data": b"original",
        "protocolID": [2, "auth message signature"],
        "keyID": "default",
    }
    res = await wallet_with_key_deriver.create_signature(args)
    sig = res["signature"]

    # 異なるデータで検証 → False
    vres = await wallet_with_key_deriver.verify_signature(
        {
            "data": b"tampered",
            "protocolID": [2, "auth message signature"],
            "keyID": "default",
            "signature": sig,
        }
    )
    assert vres.get("valid") is False


@pytest.mark.asyncio
async def test_direct_hash_sign_and_verify(wallet_with_key_deriver):
    # 事前ハッシュを直接署名/検証
    import hashlib

    data = b"hash me"
    digest = hashlib.sha256(data).digest()

    sres = await wallet_with_key_deriver.create_signature(
        {
            "hashToDirectlySign": digest,
            "protocolID": [2, "auth message signature"],
            "keyID": "default",
        }
    )
    sig = sres["signature"]

    vres = await wallet_with_key_deriver.verify_signature(
        {
            "hashToDirectlyVerify": digest,
            "protocolID": [2, "auth message signature"],
            "keyID": "default",
            "signature": sig,
        }
    )
    assert vres.get("valid") is True


