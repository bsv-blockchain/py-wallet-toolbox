import pytest
from bsv_wallet_toolbox.storage.db import create_engine_from_url, async_session_scope
from bsv_wallet_toolbox.storage.models import Base, ProvenTxReq
from bsv_wallet_toolbox.storage.provider import StorageProvider


@pytest.fixture
async def sp():
    """Create a StorageProvider with async engine for in-memory SQLite."""
    engine = create_engine_from_url("sqlite:///:memory:")
    
    # Create tables
    async with engine.begin() as conn:
        def _create_tables(sync_conn):
            Base.metadata.create_all(bind=sync_conn)
        
        await conn.run_sync(_create_tables)
    
    # Create and initialize provider
    storage_provider = StorageProvider(engine=engine, chain="test", storage_identity_key="K" * 64)
    await storage_provider.make_available()
    
    return storage_provider


@pytest.mark.asyncio
async def test_list_outputs_min_shape(sp):
    r = await sp.list_outputs({"userId": 1}, {"limit": 10})
    assert set(r.keys()) == {"totalOutputs", "outputs"}
    assert isinstance(r["totalOutputs"], int)
    assert isinstance(r["outputs"], list)


@pytest.mark.asyncio
async def test_find_outputs_auth_min_shape(sp):
    rows = await sp.find_outputs_auth({"userId": 1}, {"basket": "default", "spendable": True})
    assert isinstance(rows, list)


@pytest.mark.asyncio
async def test_list_certificates_min_shape(sp):
    r = await sp.list_certificates({"userId": 1}, {})
    assert set(r.keys()) == {"totalCertificates", "certificates"}
    assert isinstance(r["totalCertificates"], int)
    assert isinstance(r["certificates"], list)


@pytest.mark.asyncio
async def test_list_actions_min_shape(sp):
    r = await sp.list_actions({"userId": 1}, {})
    assert set(r.keys()) == {"totalActions", "actions"}
    assert isinstance(r["totalActions"], int)
    assert isinstance(r["actions"], list)


@pytest.mark.asyncio
async def test_get_proven_or_raw_tx_min_shape(sp):
    r = await sp.get_proven_or_raw_tx("00" * 32)
    assert set(r.keys()) >= {"proven", "rawTx"}


@pytest.mark.asyncio
async def test_verify_known_valid_transaction_false(sp):
    assert await sp.verify_known_valid_transaction("00" * 32) is False


@pytest.mark.asyncio
async def test_list_outputs_include_transactions_returns_beef_key(sp):
    r = await sp.list_outputs({"userId": 1}, {"limit": 10, "includeTransactions": True})
    assert "BEEF" in r
    assert isinstance(r["BEEF"], (bytes, bytearray))


@pytest.mark.asyncio
async def test_list_outputs_specop_tags_do_not_error(sp):
    # 'all' clears basket and includes spent
    r1 = await sp.list_outputs({"userId": 1}, {"tags": ["all"]})
    assert set(r1.keys()) == {"totalOutputs", "outputs"}
    # 'change' filters to change-only
    r2 = await sp.list_outputs({"userId": 1}, {"tags": ["change"]})
    assert set(r2.keys()) == {"totalOutputs", "outputs"}


@pytest.mark.asyncio
async def test_list_outputs_include_transactions_accepts_known_txids(sp):
    # knownTxids provided should not error and should still return BEEF bytes
    r = await sp.list_outputs(
        {"userId": 1},
        {"limit": 5, "includeTransactions": True, "knownTxids": ["00" * 32]},
    )
    assert "BEEF" in r
    assert isinstance(r["BEEF"], (bytes, bytearray))


@pytest.mark.asyncio
async def test_list_outputs_specop_wallet_balance_min_shape(sp):
    # Accept both idとフレンドリ名
    r = await sp.list_outputs({"userId": 1}, {"basket": "specOpWalletBalance", "limit": 3})
    assert set(r.keys()) == {"totalOutputs", "outputs"}
    assert isinstance(r["totalOutputs"], int)
    assert r["outputs"] == []


@pytest.mark.asyncio
async def test_list_outputs_specop_set_wallet_change_params_min_shape(sp):
    # 2つの数値タグを受理して空配列を返す
    r = await sp.list_outputs(
        {"userId": 1},
        {"basket": "specOpSetWalletChangeParams", "tags": ["2", "5000"]},
    )
    assert set(r.keys()) == {"totalOutputs", "outputs"}
    assert r["totalOutputs"] == 0
    assert r["outputs"] == []


@pytest.mark.asyncio
async def test_find_or_insert_proven_tx_min_shape(sp):
    row, is_new = await sp.find_or_insert_proven_tx(
        {
            "txid": "00" * 32,
            "height": 1,
            "index": 0,
            "merklePath": b"",
            "rawTx": b"\x00",
            "blockHash": "00" * 32,
            "merkleRoot": "00" * 32,
        }
    )
    assert set(row.keys()) >= {"provenTxId", "txid", "height", "index"}
    assert isinstance(is_new, bool)


@pytest.mark.asyncio
async def test_update_proven_tx_req_with_new_proven_tx_min_shape(sp):
    # create a ProvenTxReq row directly using async session
    async with sp.AsyncSessionLocal() as s:
        req = ProvenTxReq(
            status="unknown",
            attempts=0,
            notified=False,
            txid="11" * 32,
            batch=None,
            history="{}",
            notify="{}",
            raw_tx=b"\x00",
            input_beef=None,
        )
        s.add(req)
        await s.flush()
        req_id = req.proven_tx_req_id
        await s.commit()

    r = await sp.update_proven_tx_req_with_new_proven_tx(
        {
            "provenTxReqId": req_id,
            "txid": "11" * 32,
            "height": 2,
            "index": 0,
            "merklePath": b"",
            "rawTx": b"\x00\x01",
            "blockHash": "22" * 32,
            "merkleRoot": "33" * 32,
        }
    )
    assert set(r.keys()) >= {"status", "provenTxId", "history"}


@pytest.mark.asyncio
async def test_get_valid_beef_for_txid_min_bytes(sp):
    # Prepare a simple req row so rawTx exists
    async with sp.AsyncSessionLocal() as s:
        txid = "aa" * 32
        req = ProvenTxReq(
            status="unknown",
            attempts=0,
            notified=False,
            txid=txid,
            batch=None,
            history="{}",
            notify="{}",
            raw_tx=b"\x00",
            input_beef=None,
        )
        s.add(req)
        await s.flush()
        await s.commit()
    
    beef = await sp.get_valid_beef_for_txid(txid, known_txids=[txid])
    assert isinstance(beef, (bytes, bytearray))

