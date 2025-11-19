import pytest

from bsv_wallet_toolbox.storage.db import create_engine_from_url
from bsv_wallet_toolbox.storage.models import Base, ProvenTxReq
from bsv_wallet_toolbox.storage.provider import StorageProvider


@pytest.fixture
def sp():
    """Create a StorageProvider with sync engine for in-memory SQLite."""
    engine = create_engine_from_url("sqlite:///:memory:")
    # Create tables synchronously
    Base.metadata.create_all(bind=engine)

    # Create and initialize provider
    storage_provider = StorageProvider(engine=engine, chain="test", storage_identity_key="K" * 64)
    storage_provider.make_available()
    return storage_provider


def test_list_outputs_min_shape(sp):
    r = sp.list_outputs({"userId": 1}, {"limit": 10})
    assert set(r.keys()) == {"totalOutputs", "outputs"}
    assert isinstance(r["totalOutputs"], int)
    assert isinstance(r["outputs"], list)


def test_find_outputs_auth_min_shape(sp):
    rows = sp.find_outputs_auth({"userId": 1}, {"basket": "default", "spendable": True})
    assert isinstance(rows, list)


def test_list_certificates_min_shape(sp):
    r = sp.list_certificates({"userId": 1}, {})
    assert set(r.keys()) == {"totalCertificates", "certificates"}
    assert isinstance(r["totalCertificates"], int)
    assert isinstance(r["certificates"], list)


def test_list_actions_min_shape(sp):
    r = sp.list_actions({"userId": 1}, {})
    assert set(r.keys()) == {"totalActions", "actions"}
    assert isinstance(r["totalActions"], int)
    assert isinstance(r["actions"], list)


def test_get_proven_or_raw_tx_min_shape(sp):
    r = sp.get_proven_or_raw_tx("00" * 32)
    assert set(r.keys()) >= {"proven", "rawTx"}


def test_verify_known_valid_transaction_false(sp):
    assert sp.verify_known_valid_transaction("00" * 32) is False


def test_list_outputs_include_transactions_returns_beef_key(sp):
    r = sp.list_outputs({"userId": 1}, {"limit": 10, "includeTransactions": True})
    assert "BEEF" in r
    assert isinstance(r["BEEF"], (bytes, bytearray))


def test_list_outputs_specop_tags_do_not_error(sp):
    # 'all' clears basket and includes spent
    r1 = sp.list_outputs({"userId": 1}, {"tags": ["all"]})
    assert set(r1.keys()) == {"totalOutputs", "outputs"}
    # 'change' filters to change-only
    r2 = sp.list_outputs({"userId": 1}, {"tags": ["change"]})
    assert set(r2.keys()) == {"totalOutputs", "outputs"}


def test_list_outputs_include_transactions_accepts_known_txids(sp):
    # knownTxids provided should not error and should still return BEEF bytes
    r = sp.list_outputs(
        {"userId": 1},
        {"limit": 5, "includeTransactions": True, "knownTxids": ["00" * 32]},
    )
    assert "BEEF" in r
    assert isinstance(r["BEEF"], (bytes, bytearray))


def test_list_outputs_specop_wallet_balance_min_shape(sp):
    # Accept both id and friendly name
    r = sp.list_outputs({"userId": 1}, {"basket": "specOpWalletBalance", "limit": 3})
    assert set(r.keys()) == {"totalOutputs", "outputs"}
    assert isinstance(r["totalOutputs"], int)
    assert r["outputs"] == []


def test_list_outputs_specop_set_wallet_change_params_min_shape(sp):
    # Accept two numeric tags and return empty array
    r = sp.list_outputs(
        {"userId": 1},
        {"basket": "specOpSetWalletChangeParams", "tags": ["2", "5000"]},
    )
    assert set(r.keys()) == {"totalOutputs", "outputs"}
    assert r["totalOutputs"] == 0
    assert r["outputs"] == []


def test_find_or_insert_proven_tx_min_shape(sp):
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


def test_update_proven_tx_req_with_new_proven_tx_min_shape(sp):
    # create a ProvenTxReq row directly using sync session
    with sp.SessionLocal() as s:
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


def test_get_valid_beef_for_txid_min_bytes(sp):
    # Prepare a simple req row so rawTx exists
    with sp.SessionLocal() as s:
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

    beef = sp.get_valid_beef_for_txid(txid, known_txids=[txid])
    assert isinstance(beef, (bytes, bytearray))
