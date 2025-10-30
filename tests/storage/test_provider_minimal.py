from bsv_wallet_toolbox.storage.db import create_engine_from_url
from bsv_wallet_toolbox.storage.models import Base
from bsv_wallet_toolbox.storage.provider import StorageProvider


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

