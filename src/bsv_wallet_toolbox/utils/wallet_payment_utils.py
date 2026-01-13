"""Wallet payment convenience helpers (BRC-29 + BRC-100).

Why this exists
Consumers of the toolbox should NOT have to repeatedly re-implement the same "wallet payment" flow:
- build a BRC-29 locking script
- attach `paymentRemittance` so the receiver can reconstruct the derivation context
- broadcast via `createAction({ signAndProcess: true })`
- internalize the received output via `internalizeAction` using AtomicBEEF

These helpers keep example scripts thin, and provide a stable, reusable API surface.
"""

from __future__ import annotations

import base64
from typing import Any

from bsv_wallet_toolbox.brc29 import KeyID, address_for_counterparty, lock_for_counterparty
from bsv_wallet_toolbox.errors.wallet_errors import ReviewActionsError
from bsv_wallet_toolbox.utils.atomic_beef_utils import build_atomic_beef_for_txid


def make_wallet_payment_remittance(
    *, sender_identity_key: str, derivation_prefix: str, derivation_suffix: str
) -> dict[str, str]:
    """Create a `paymentRemittance` object for protocol='wallet payment' (BRC-29).

    This is the metadata the receiver needs to reconstruct the BRC-29 derivation context.
    It is attached to the output in `createAction.outputs[*]`.

    Parameters:
        sender_identity_key: Sender's identity public key hex (root identity key).
        derivation_prefix: Application-defined prefix (human readable string).
        derivation_suffix: Application-defined suffix (human readable string).

    Returns:
        Dict with camelCase keys matching TS/Go payloads.
    """
    return {
        "senderIdentityKey": sender_identity_key,
        "derivationPrefix": base64.b64encode(derivation_prefix.encode("utf-8")).decode("ascii"),
        "derivationSuffix": base64.b64encode(derivation_suffix.encode("utf-8")).decode("ascii"),
    }


def internalize_wallet_payment(
    wallet: Any,
    services: Any,
    *,
    txid: str,
    output_index: int,
    remittance: dict[str, str],
    description: str,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Internalize one wallet-payment output into `wallet` using AtomicBEEF.

    Think of this as the canonical "receiver side" step in the BRC-29 flow:
    - sender broadcasts a tx paying a BRC-29 derived address
    - receiver calls internalizeAction to explicitly accept that UTXO into spendable state

    Parameters:
        wallet: A `bsv_wallet_toolbox.Wallet` instance (or compatible).
        services: A `bsv_wallet_toolbox.services.Services` instance (used to fetch rawTx/merkle data).
        txid: The transaction id that created the output.
        output_index: The vout index paid to the derived address.
        remittance: The `paymentRemittance` object from the sender.
        description: Human-readable description stored with the action.
        labels: Optional labels stored with the action.

    Returns:
        The `internalizeAction` result dict.
    """
    atomic_beef = build_atomic_beef_for_txid(services, txid)
    args: dict[str, Any] = {
        "tx": list(atomic_beef),
        "outputs": [{"outputIndex": int(output_index), "protocol": "wallet payment", "paymentRemittance": remittance}],
        "description": description,
        "labels": labels or [f"txid:{txid}", "wallet-payment"],
    }
    return wallet.internalize_action(args)


def send_wallet_payment_ex(
    sender_wallet: Any,
    recipient_wallet: Any,
    *,
    amount_satoshis: int,
    derivation_prefix: str,
    derivation_suffix: str,
    output_description: str = "BRC-29 payment",
    sign_and_process: bool = True,
    accept_delayed_broadcast: bool = False,
) -> dict[str, Any]:
    """Send a single-output BRC-29 wallet payment and return rich diagnostics.

    This is the same flow as `send_wallet_payment`, but returns extra information that is
    useful for CLI demos and debugging:
    - the derived destination address (`derivedAddress`)
    - the output locking script (`lockingScriptHex`)
    - the raw `createAction` and (optional) `signAction` results
    """
    if amount_satoshis <= 0:
        raise ValueError("amount_satoshis must be > 0")

    sender_identity_key = sender_wallet.get_public_key({"identityKey": True, "reason": "sender"})["publicKey"]
    recipient_identity_key = recipient_wallet.get_public_key({"identityKey": True, "reason": "recipient"})["publicKey"]

    key_id = KeyID(derivation_prefix=derivation_prefix, derivation_suffix=derivation_suffix)
    testnet = getattr(sender_wallet, "chain", "test") == "test"

    derived_addr = address_for_counterparty(
        sender_private_key=sender_wallet.key_deriver,
        key_id=key_id,
        recipient_public_key=recipient_identity_key,
        testnet=testnet,
    )["addressString"]

    locking_script = lock_for_counterparty(
        sender_private_key=sender_wallet.key_deriver,
        key_id=key_id,
        recipient_public_key=recipient_identity_key,
        testnet=testnet,
    )

    remittance = make_wallet_payment_remittance(
        sender_identity_key=sender_identity_key,
        derivation_prefix=derivation_prefix,
        derivation_suffix=derivation_suffix,
    )

    create_result: dict[str, Any]
    sign_result: dict[str, Any] | None = None

    try:
        r = sender_wallet.create_action(
            {
                "description": f"Send {int(amount_satoshis)} satoshis",
                "outputs": [
                    {
                        "satoshis": int(amount_satoshis),
                        "lockingScript": locking_script.hex(),
                        "protocol": "wallet payment",
                        "paymentRemittance": remittance,
                        "outputDescription": output_description,
                    }
                ],
                "options": {
                    "signAndProcess": bool(sign_and_process),
                    "acceptDelayedBroadcast": bool(accept_delayed_broadcast),
                },
            }
        )
        create_result = r if isinstance(r, dict) else {}
    except ReviewActionsError:
        raise

    signable = create_result.get("signableTransaction")
    if isinstance(signable, dict) and signable.get("reference"):
        signed = sender_wallet.sign_action({"reference": signable["reference"], "accept": True})
        sign_result = signed if isinstance(signed, dict) else {}

    txid = (sign_result.get("txid") or sign_result.get("txID")) if isinstance(sign_result, dict) else None
    if not txid:
        txid = create_result.get("txid") or create_result.get("txID")
    if not isinstance(txid, str) or not txid:
        raise RuntimeError("create_action did not return txid")

    return {
        "txid": txid,
        "vout": 0,
        "remittance": remittance,
        "derivedAddress": derived_addr,
        "lockingScriptHex": locking_script.hex(),
        "createActionResult": create_result,
        "signActionResult": sign_result,
        "keyID": {"derivationPrefix": derivation_prefix, "derivationSuffix": derivation_suffix},
    }


def send_wallet_payment(
    sender_wallet: Any,
    recipient_wallet: Any,
    *,
    amount_satoshis: int,
    derivation_prefix: str,
    derivation_suffix: str,
    output_description: str = "BRC-29 payment",
    sign_and_process: bool = True,
    accept_delayed_broadcast: bool = False,
) -> tuple[str, int, dict[str, str]]:
    """Send a single-output BRC-29 wallet payment from sender -> recipient.

    What this helper does:
    - Computes a BRC-29 locking script for (sender, recipient, key_id).
    - Attaches a `paymentRemittance` object to the output.
    - Calls `createAction({ signAndProcess: true })` and, if necessary, `signAction(accept=true)`.

    Notes:
    - Returns `(txid, vout, remittance)`.
    - `vout` is always 0 because this helper constructs exactly one destination output.
    - This helper intentionally keeps the policy surface small and explicit; if your app needs more
      control, call wallet methods directly.
    """
    r = send_wallet_payment_ex(
        sender_wallet,
        recipient_wallet,
        amount_satoshis=amount_satoshis,
        derivation_prefix=derivation_prefix,
        derivation_suffix=derivation_suffix,
        output_description=output_description,
        sign_and_process=sign_and_process,
        accept_delayed_broadcast=accept_delayed_broadcast,
    )
    return str(r["txid"]), int(r["vout"]), dict(r["remittance"])
