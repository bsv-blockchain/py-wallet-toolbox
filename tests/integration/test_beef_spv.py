"""SPV verification of caller-supplied BEEF (internalizeAction tx, createAction inputBEEF).

TS parity: both layers call ``beef.verify(await services.getChainTracker(), allowTxidOnly)``
(signer/methods/internalizeActionCore.ts, storage/methods/internalizeActionCore.ts,
storage/methods/createAction.ts validateRequiredInputs).
"""

from typing import Any

import pytest
from bsv.keys import PrivateKey
from bsv.transaction.beef import BEEF_V1, BEEF_V2, parse_beef_ex
from bsv.utils import unsigned_to_varint
from bsv.wallet import KeyDeriver

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError
from tests.testabilities.testservices import create_in_memory_storage_provider
from tests.testabilities.testusers import ALICE
from tests.testabilities.tsgenerated import (
    BEEF_TO_INTERNALIZE_HEIGHT,
    BEEF_TO_INTERNALIZE_MERKLE_ROOT,
    PARENT_BEEF_TXID,
    parent_transaction_atomic_beef,
)


class Tracker:
    """ChainTracker that accepts only the given roots (None accepts every root)."""

    def __init__(self, roots: dict[int, str] | None) -> None:
        self.roots = roots
        self.calls: list[tuple[str, int]] = []

    async def is_valid_root_for_height(self, root: str, height: int) -> bool:
        self.calls.append((root, height))
        return self.roots is None or self.roots.get(height) == root


def chain() -> Tracker:
    return Tracker({BEEF_TO_INTERNALIZE_HEIGHT: BEEF_TO_INTERNALIZE_MERKLE_ROOT})


class FakeServices:
    def __init__(self, tracker: Tracker) -> None:
        self.tracker = tracker

    def get_chain_tracker(self) -> Tracker:
        return self.tracker


def atomic_beef(version: int = BEEF_V2, leaf: int | None = None) -> bytes:
    """Fixture AtomicBEEF; ``leaf`` replaces that level-0 hash of the parent's BUMP.

    V1 is encoded here rather than by the SDK: bsv-sdk 2.4.0 writes a V2 body under a V1 header.
    """
    ab, txid, _ = parse_beef_ex(parent_transaction_atomic_beef())
    if leaf is not None:
        ab.bumps[0].path[0][leaf]["hash_str"] = "11" * 32
    if version == BEEF_V2:
        return ab.to_binary_atomic(txid)
    body = b"\x01\x00\xbe\xef" + unsigned_to_varint(len(ab.bumps)) + b"".join(b.to_binary() for b in ab.bumps)
    body += unsigned_to_varint(len(ab.txs))
    for btx in ab.txs.values():  # parents first; V1 entry = rawTx, hasBump, [bumpIndex]
        bump = b"\x00" if btx.bump_index is None else b"\x01" + unsigned_to_varint(btx.bump_index)
        body += btx.tx_obj.serialize() + bump
    return b"\x01\x01\x01\x01" + bytes.fromhex(txid)[::-1] + body


def internalize_args(tx: bytes, protocol: str = "basket insertion") -> dict[str, Any]:
    output: dict[str, Any] = {"outputIndex": 0, "protocol": protocol}
    if protocol == "basket insertion":
        output["insertionRemittance"] = {"basket": "received"}
    else:
        output["paymentRemittance"] = {
            "derivationPrefix": "Pr==",
            "derivationSuffix": "Su==",
            "senderIdentityKey": "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798",
        }
    return {"tx": tx, "outputs": [output], "description": "spv test"}


@pytest.fixture
def storage():
    sp, cleanup = create_in_memory_storage_provider(chain="testnet")
    user_id = sp.find_or_insert_user(ALICE.identity_key())["user"]["userId"]
    sp.auth = {"identityKey": ALICE.identity_key(), "userId": user_id}
    sp.configure_basket(sp.auth, {"name": "default", "numberOfDesiredUTXOs": 31, "minimumDesiredUTXOValue": 1000})
    yield sp
    cleanup()


def stored_txids(sp: Any) -> list[str]:
    return [t["txid"] for t in sp.find_transactions({"partial": {"userId": sp.auth["userId"]}})]


class TestStorageInternalize:
    @pytest.mark.parametrize("version", [BEEF_V1, BEEF_V2], ids=["v1", "v2"])
    def test_accepts_beef_confirmed_by_chain_tracker(self, storage, version) -> None:
        tracker = chain()
        storage.set_services(FakeServices(tracker))

        result = storage.internalize_action(storage.auth, internalize_args(atomic_beef(version)))

        assert result["accepted"] is True
        assert tracker.calls == [(BEEF_TO_INTERNALIZE_MERKLE_ROOT, BEEF_TO_INTERNALIZE_HEIGHT)]

    @pytest.mark.parametrize("version", [BEEF_V1, BEEF_V2], ids=["v1", "v2"])
    def test_rejects_root_unknown_to_chain_tracker(self, storage, version) -> None:
        storage.set_services(FakeServices(Tracker({})))

        with pytest.raises(InvalidParameterError, match="tx"):
            storage.internalize_action(storage.auth, internalize_args(atomic_beef(version)))
        assert stored_txids(storage) == []

    def test_rejects_tampered_bump_sibling(self, storage) -> None:
        storage.set_services(FakeServices(chain()))

        with pytest.raises(InvalidParameterError, match="tx"):
            storage.internalize_action(storage.auth, internalize_args(atomic_beef(leaf=0)))
        assert stored_txids(storage) == []

    def test_rejects_bump_without_the_proven_txid_even_if_tracker_accepts_all(self, storage) -> None:
        storage.set_services(FakeServices(Tracker(None)))

        with pytest.raises(InvalidParameterError, match="tx"):
            storage.internalize_action(storage.auth, internalize_args(atomic_beef(leaf=1)))
        assert stored_txids(storage) == []

    def test_fails_closed_without_services(self, storage) -> None:
        with pytest.raises(RuntimeError):
            storage.internalize_action(storage.auth, internalize_args(atomic_beef()))
        assert stored_txids(storage) == []


class TestWalletInternalize:
    @pytest.fixture
    def wallet(self, storage):
        kd = KeyDeriver(PrivateKey(bytes.fromhex(ALICE.priv_key)))
        return Wallet(chain="test", key_deriver=kd, storage_provider=storage, services=FakeServices(chain()))

    def test_accepts_and_forwards_the_verified_beef(self, wallet, storage) -> None:
        result = wallet.internalize_action(internalize_args(atomic_beef(), protocol="wallet payment"))

        assert result["accepted"] is True
        assert result["txid"] == PARENT_BEEF_TXID

    def test_signer_rejects_before_storage(self, wallet, storage) -> None:
        wallet.services = FakeServices(Tracker({}))
        storage.set_services(FakeServices(Tracker(None)))  # storage alone would accept

        with pytest.raises(InvalidParameterError, match="tx"):
            wallet.internalize_action(internalize_args(atomic_beef(), protocol="wallet payment"))
        assert stored_txids(storage) == []


class TestCreateActionInputBeef:
    def create_args(self, input_beef: bytes, trust_self: str | None = None) -> dict[str, Any]:
        return {
            "description": "spend received",
            "inputs": [
                {
                    "outpoint": {"txid": PARENT_BEEF_TXID, "vout": 0},
                    "inputDescription": "received output",
                    "unlockingScriptLength": 108,
                }
            ],
            "inputBEEF": input_beef,
            "outputs": [
                {
                    "lockingScript": "76a9144b0d6cbef5a813d2d12dcec1de2584b250dc96a388ac",
                    "satoshis": 1000,
                    "outputDescription": "out",
                }
            ],
            "options": {"signAndProcess": False, "randomizeOutputs": False, "trustSelf": trust_self},
        }

    @pytest.fixture
    def tracker(self, storage) -> Tracker:
        tracker = chain()
        storage.set_services(FakeServices(tracker))
        storage.internalize_action(storage.auth, internalize_args(atomic_beef()))
        # Python stores P2PKH basket insertions as change; createAction only spends non-change inputs.
        for o in storage.find_outputs({"partial": {"txid": PARENT_BEEF_TXID, "vout": 0}}):
            storage.update_output(o["outputId"], {"change": False})
        return tracker

    @pytest.mark.xfail(
        strict=True,
        raises=AttributeError,
        reason="pre-existing: storage create_action calls vargs.get() on NormalizedCreateActionArgs for user inputs",
    )
    @pytest.mark.parametrize("txid_only", [False, True])
    def test_accepts_input_beef_confirmed_by_chain_tracker(self, storage, tracker, txid_only) -> None:
        beef = parse_beef_ex(atomic_beef())[0].txid_only().to_binary() if txid_only else atomic_beef()
        trust_self = "known" if txid_only else None

        result = storage.create_action(storage.auth, self.create_args(beef, trust_self))

        assert result["reference"]

    def test_rejects_input_beef_unknown_to_chain_tracker(self, storage, tracker) -> None:
        tracker.roots = {}

        with pytest.raises(InvalidParameterError, match="inputBEEF"):
            storage.create_action(storage.auth, self.create_args(atomic_beef()))

    def test_rejects_tampered_input_beef(self, storage, tracker) -> None:
        with pytest.raises(InvalidParameterError, match="inputBEEF"):
            storage.create_action(storage.auth, self.create_args(atomic_beef(leaf=0)))

    def test_rejects_txid_only_without_trust_self(self, storage, tracker) -> None:
        txid_only = parse_beef_ex(atomic_beef())[0].txid_only().to_binary()

        with pytest.raises(InvalidParameterError, match="inputBEEF"):
            storage.create_action(storage.auth, self.create_args(txid_only))
