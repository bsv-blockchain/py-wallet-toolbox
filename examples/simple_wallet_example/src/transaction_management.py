"""Transaction-specific demos (internalizeAction)."""

from __future__ import annotations

from pprint import pprint
from typing import Any

from bsv.merkle_path import MerklePath as PyMerklePath
from bsv.transaction.beef import BEEF_V2, Beef
from bsv.transaction.beef_builder import merge_bump, merge_raw_tx
from bsv.transaction.beef_serialize import to_binary_atomic

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.services import Services
from bsv_wallet_toolbox.utils.merkle_path_utils import convert_proof_to_merkle_path

from .config import Chain


def demo_internalize_action(wallet: Wallet, chain: Chain) -> None:
    """Guide the user through internalizing an externally created transaction."""
    print("\n🏗️  Internalize an external transaction")
    print("    - Send coins to this wallet (use menu 4 to view the receive address).")
    print("    - Obtain the transaction ID from an explorer (e.g., Whatsonchain).")
    print("    - We will download Atomic BEEF data automatically unless you paste it.")
    print()

    beef_hex = input("Paste Atomic BEEF hex (Enter to download via txid): ").strip().replace(" ", "")
    if beef_hex:
        try:
            atomic_beef = bytes.fromhex(beef_hex)
        except ValueError:
            print("❌ Invalid hex. Please ensure the Atomic BEEF string is hex-encoded.")
            return
        txid = None
    else:
        txid = input("Enter transaction ID to internalize: ").strip()
        if len(txid) != 64:
            print("❌ txid must be 64 hex characters.")
            return
        try:
            atomic_beef = _build_atomic_beef_for_txid(chain, txid)
        except Exception as err:
            print(f"❌ Failed to download Atomic BEEF: {err}")
            return

    raw_indexes = input("Output indexes paid to you (comma separated, default 0): ").strip()
    indexes = _parse_output_indexes(raw_indexes or "0")
    if not indexes:
        print("❌ At least one valid output index is required.")
        return

    basket = input("Basket to link these outputs to [default]: ").strip() or "default"
    description = (
        input("Description (5-2000 chars) [Internalize external transaction]: ").strip()
        or "Internalize external transaction"
    )
    labels_raw = input("Optional labels (comma separated): ").strip()
    labels = [lbl.strip() for lbl in labels_raw.split(",") if lbl.strip()]

    custom_instructions = input("Custom instructions JSON (optional): ").strip()
    tags_raw = input("Optional tags for this basket insertion (comma separated): ").strip()
    tag_list = [tag.strip() for tag in tags_raw.split(",") if tag.strip()]

    outputs = []
    for idx in indexes:
        insertion = {"basket": basket}
        if custom_instructions:
            insertion["customInstructions"] = custom_instructions
        if tag_list:
            insertion["tags"] = tag_list
        outputs.append(
            {
                "outputIndex": idx,
                "protocol": "basket insertion",
                "insertionRemittance": insertion,
            }
        )

    internalize_args: dict[str, Any] = {
        "tx": atomic_beef,
        "outputs": outputs,
        "description": description,
    }
    if labels:
        internalize_args["labels"] = labels

    if txid:
        internalize_args.setdefault("labels", []).append(f"txid:{txid}")

    print("\n🚀 Internalizing transaction...")
    try:

        result = wallet.internalize_action(internalize_args)
    except Exception as err:
        print(f"❌ InternalizeAction failed: {err}")
        return

    print("\n✅ Transaction internalized")
    print(f"   State : {result.get('state', 'unknown')}")
    print(f"   TxID  : {result.get('txid', 'n/a')}")
    print(f"   Labels: {', '.join(result.get('labels', [])) or '(none)'}")
    tracked_outputs = result.get("outputs") or []
    if tracked_outputs:
        print(f"   Outputs tracked: {len(tracked_outputs)}")
    else:
        print("   Outputs tracked: (not returned)")


def _parse_output_indexes(raw: str) -> list[int]:
    indexes: list[int] = []
    for part in raw.split(","):
        value = part.strip()
        if not value:
            continue
        try:
            idx = int(value)
        except ValueError:
            print(f"⚠️  Ignoring invalid index '{value}'.")
            continue
        if idx < 0:
            print(f"⚠️  Ignoring negative index '{idx}'.")
            continue
        indexes.append(idx)
    return indexes


def _build_atomic_beef_for_txid(chain: Chain, txid: str) -> bytes:
    services = Services(chain)

    print(f"\n🔎 Fetching raw transaction via Services for txid={txid} (chain={chain})")
    raw_hex = services.get_raw_tx(txid)
    if not raw_hex:
        print("⚠️  Services.get_raw_tx returned None. Call history snapshot:")
        call_history = services.get_services_call_history()
        pprint(call_history.get("getRawTx"), width=120)
        raise RuntimeError("Unable to locate raw transaction data.")

    print(f"✅ Raw transaction fetched ({len(raw_hex)} hex chars). Building Merkle data...")
    merkle_result = services.get_merkle_path_for_transaction(txid)
    if not merkle_result:
        print("⚠️  get_merkle_path_for_transaction returned empty result.")
    merkle_path = _convert_merkle_result(txid, merkle_result)
    if not merkle_path:
        print("⚠️  Unable to convert merkle path result. Continuing without BUMP info.")

    beef = Beef(version=BEEF_V2)
    bump_index = merge_bump(beef, merkle_path) if merkle_path else None
    merge_raw_tx(beef, bytes.fromhex(raw_hex), bump_index)
    print("✅ Atomic BEEF built successfully.")
    return to_binary_atomic(beef, txid)


def _convert_merkle_result(txid: str, result: dict[str, Any] | None) -> PyMerklePath | None:
    if not isinstance(result, dict):
        return None

    proof = result.get("merklePath")
    if isinstance(proof, dict) and {"blockHeight", "path"} <= proof.keys():
        return PyMerklePath(proof["blockHeight"], proof["path"])

    nodes = proof.get("nodes") if isinstance(proof, dict) else None
    index = proof.get("index") if isinstance(proof, dict) else None
    height = proof.get("height") if isinstance(proof, dict) else None

    header = result.get("header")
    if height is None and isinstance(header, dict):
        height = header.get("height")

    if nodes is None or index is None or height is None:
        return None

    tsc_proof = {"height": height, "index": index, "nodes": nodes}
    mp_dict = convert_proof_to_merkle_path(txid, tsc_proof)
    return PyMerklePath(mp_dict["blockHeight"], mp_dict["path"])
