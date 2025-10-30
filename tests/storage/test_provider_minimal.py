from bsv_wallet_toolbox.storage.db import create_engine_from_url
from bsv_wallet_toolbox.storage.models import Base
from bsv_wallet_toolbox.storage.provider import StorageProvider
from bsv_wallet_toolbox.storage.models import ProvenTxReq


def make_provider():
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    sp = StorageProvider(engine=engine, chain="test", storage_identity_key="K" * 64)
    sp.make_available()
    return sp


def test_list_outputs_min_shape():
    sp = make_provider()
    r = sp.list_outputs({"userId": 1}, {"limit": 10})
    assert set(r.keys()) == {"totalOutputs", "outputs"}
    assert isinstance(r["totalOutputs"], int)
    assert isinstance(r["outputs"], list)


def test_find_outputs_auth_min_shape():
    sp = make_provider()
    rows = sp.find_outputs_auth({"userId": 1}, {"basket": "default", "spendable": True})
    assert isinstance(rows, list)


def test_list_certificates_min_shape():
    sp = make_provider()
    r = sp.list_certificates({"userId": 1}, {})
    assert set(r.keys()) == {"totalCertificates", "certificates"}
    assert isinstance(r["totalCertificates"], int)
    assert isinstance(r["certificates"], list)


def test_list_actions_min_shape():
    sp = make_provider()
    r = sp.list_actions({"userId": 1}, {})
    assert set(r.keys()) == {"totalActions", "actions"}
    assert isinstance(r["totalActions"], int)
    assert isinstance(r["actions"], list)


def test_get_proven_or_raw_tx_min_shape():
    sp = make_provider()
    r = sp.get_proven_or_raw_tx("00" * 32)
    assert set(r.keys()) >= {"proven", "rawTx"}


def test_verify_known_valid_transaction_false():
    sp = make_provider()
    assert sp.verify_known_valid_transaction("00" * 32) is False


def test_list_outputs_include_transactions_returns_beef_key():
    sp = make_provider()
    r = sp.list_outputs({"userId": 1}, {"limit": 10, "includeTransactions": True})
    assert "BEEF" in r
    assert isinstance(r["BEEF"], (bytes, bytearray))


def test_list_outputs_specop_tags_do_not_error():
    sp = make_provider()
    # 'all' clears basket and includes spent
    r1 = sp.list_outputs({"userId": 1}, {"tags": ["all"]})
    assert set(r1.keys()) == {"totalOutputs", "outputs"}
    # 'change' filters to change-only
    r2 = sp.list_outputs({"userId": 1}, {"tags": ["change"]})
    assert set(r2.keys()) == {"totalOutputs", "outputs"}


def test_list_outputs_include_transactions_accepts_known_txids():
    sp = make_provider()
    # knownTxids provided should not error and should still return BEEF bytes
    r = sp.list_outputs(
        {"userId": 1},
        {"limit": 5, "includeTransactions": True, "knownTxids": ["00" * 32]},
    )
    assert "BEEF" in r
    assert isinstance(r["BEEF"], (bytes, bytearray))


def test_list_outputs_specop_wallet_balance_min_shape():
    sp = make_provider()
    # Accept both idとフレンドリ名
    r = sp.list_outputs({"userId": 1}, {"basket": "specOpWalletBalance", "limit": 3})
    assert set(r.keys()) == {"totalOutputs", "outputs"}
    assert isinstance(r["totalOutputs"], int)
    assert r["outputs"] == []


def test_list_outputs_specop_set_wallet_change_params_min_shape():
    sp = make_provider()
    # 2つの数値タグを受理して空配列を返す
    r = sp.list_outputs(
        {"userId": 1},
        {"basket": "specOpSetWalletChangeParams", "tags": ["2", "5000"]},
    )
    assert set(r.keys()) == {"totalOutputs", "outputs"}
    assert r["totalOutputs"] == 0
    assert r["outputs"] == []


def test_find_or_insert_proven_tx_min_shape():
    sp = make_provider()
    row, is_new = sp.find_or_insert_proven_tx(
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


def test_update_proven_tx_req_with_new_proven_tx_min_shape():
    sp = make_provider()
    # create a ProvenTxReq row directly
    s = sp.SessionLocal()
    try:
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
        s.flush()
        req_id = req.proven_tx_req_id
        s.commit()
    finally:
        s.close()

    r = sp.update_proven_tx_req_with_new_proven_tx(
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


def test_get_valid_beef_for_txid_min_bytes():
    sp = make_provider()
    # Prepare a simple req row so rawTx exists
    s = sp.SessionLocal()
    try:
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
        s.flush()
        s.commit()
    finally:
        s.close()
    beef = sp.get_valid_beef_for_txid(txid, known_txids=[txid])
    assert isinstance(beef, (bytes, bytearray))

