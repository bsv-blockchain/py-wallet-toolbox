#!/usr/bin/env python3
"""Interactive E2E example: Alice & Bob 2-party roundtrip.

This is an *example* file: it keeps logic linear and comments explicit. Reusable primitives live in
the package (not here), e.g. `bsv_wallet_toolbox.utils.atomic_beef_utils`.

Flow:
1) Create Alice+Bob wallets
2) Fund Alice via a BRC-29 derived address
3) `internalizeAction` imports the funded output into spendable wallet state (AtomicBEEF required for Go server)
4) Alice pays Bob (BRC-29 wallet payment), Bob internalizes
5) Bob pays Alice back, Alice internalizes

Storage:
- Local: per-wallet SQLite file
- Remote (`USE_STORAGE_SERVER=true`): Go WalletStorageServer + BRC-104 auth (bootstrap wallet with in-memory SQLite)

Env:
- Required: TAAL_ARC_API_KEY
- Optional: BSV_NETWORK=test|main, USE_STORAGE_SERVER, STORAGE_SERVER_URL, BSV_MNEMONIC
"""

from __future__ import annotations

import logging
import os
from typing import Literal

from bsv.constants import Network
from bsv.hd.bip32 import bip32_derive_xprv_from_mnemonic
from bsv.hd.bip39 import mnemonic_from_entropy
from bsv.keys import PrivateKey, PublicKey
from bsv.wallet import KeyDeriver
from dotenv import load_dotenv
from sqlalchemy import create_engine

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.brc29 import KeyID, address_for_counterparty, address_for_self
from bsv_wallet_toolbox.errors.wallet_errors import ReviewActionsError
from bsv_wallet_toolbox.rpc import StorageClient
from bsv_wallet_toolbox.services import Services, create_default_options
from bsv_wallet_toolbox.storage import StorageProvider
from bsv_wallet_toolbox.utils import configure_logger
from bsv_wallet_toolbox.utils.wallet_payment_utils import (
    internalize_wallet_payment,
    make_wallet_payment_remittance,
    send_wallet_payment_ex,
)

logger = logging.getLogger(__name__)

Chain = Literal["main", "test"]

# These "derivation prefix/suffix" strings are BRC-29 application parameters.
# For an example, it's helpful if they are deterministic (so runs are reproducible).
FAUCET_DERIVATION_PREFIX = "faucet-prefix-01"
FAUCET_DERIVATION_SUFFIX = "faucet-suffix-01"

ALICE_TO_BOB_DERIVATION_PREFIX = "alice-to-bob-prefix-01"
ALICE_TO_BOB_DERIVATION_SUFFIX = "alice-to-bob-suffix-01"
BOB_TO_ALICE_DERIVATION_PREFIX = "bob-to-alice-prefix-01"
BOB_TO_ALICE_DERIVATION_SUFFIX = "bob-to-alice-suffix-01"


def _env_truthy(name: str) -> bool:
    """Return True if the environment variable is set to a typical truthy value.

    Accepted values (case-insensitive): 1, true, yes, y, on
    """
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _require_env(name: str) -> str:
    """Return the env var value or exit with a clear message.

    We keep this small but explicit because missing API keys is the most common failure mode
    when running the example for the first time.
    """
    value = os.getenv(name, "").strip()
    if not value:
        print(f"❌ {name} is not set (check your `.env` or environment)")
        raise SystemExit(1)
    return value


def _make_services(chain: Chain) -> Services:
    """Create `Services` configured for this example.

    This example uses ARC for broadcast (via `TAAL_ARC_API_KEY`) and disables other providers
    to reduce variability between runs.
    """
    options = create_default_options(chain)
    options["arcApiKey"] = _require_env("TAAL_ARC_API_KEY")
    options["bitailsApiKey"] = None
    options["arcGorillaPoolUrl"] = None
    options["arcGorillaPoolApiKey"] = None
    options["arcGorillaPoolHeaders"] = None
    return Services(options)


def _make_wallet(name: str, chain: Chain, services: Services, use_remote: bool) -> tuple[Wallet, PrivateKey]:
    """Create a wallet + root private key for this example.

    Key points (important for people copying this code):
    - This returns the same Wallet instance you will use for all later calls.
    - We call `wallet.ensure_initialized()` so the storage side has:
      - a user row (auth.userId)
      - and (best-effort) the "default" output basket
      This prevents the common "fresh wallet cannot internalize" failure mode.

    Remote mode (`USE_STORAGE_SERVER=true`):
    - The StorageClient needs a Wallet instance for BRC-104 signing.
    - We bootstrap with in-memory SQLite, create the StorageClient, then swap `wallet.storage`
      to the remote client.
    """
    mnemonic = os.getenv("BSV_MNEMONIC")
    if not mnemonic:
        mnemonic = mnemonic_from_entropy(entropy=None, lang="en")
        print("\n⚠️  Generated a new mnemonic. Save it if you want repeatable runs:\n")
        print(f"BSV_MNEMONIC={mnemonic}\n")

    # Derive Alice and Bob from different paths so they are distinct wallets.
    path = "m/0" if name == "alice" else "m/1"
    xprv = bip32_derive_xprv_from_mnemonic(mnemonic=mnemonic, lang="en", passphrase="", prefix="mnemonic", path=path)
    root_priv = xprv.private_key()
    key_deriver = KeyDeriver(root_private_key=root_priv)

    if use_remote:
        bootstrap = StorageProvider(
            engine=create_engine("sqlite:///:memory:"), chain=chain, storage_identity_key=f"{chain}-{name}-bootstrap"
        )
        bootstrap.make_available()
        wallet = Wallet(chain=chain, services=services, key_deriver=key_deriver, storage_provider=bootstrap)

        url = os.getenv("STORAGE_SERVER_URL", "http://localhost:8080").strip()
        print(f"🌐 {name}: remote storage server = {url}")
        client = StorageClient(wallet, url)
        client.make_available()
        wallet.storage = client
        wallet.ensure_initialized()
        return wallet, root_priv

    db_file = f"wallet_{name}.db"
    print(f"💾 {name}: local sqlite = {db_file}")
    storage = StorageProvider(
        engine=create_engine(f"sqlite:///{db_file}"), chain=chain, storage_identity_key=f"{chain}-{name}"
    )
    storage.make_available()
    storage.set_services(services)
    wallet = Wallet(chain=chain, services=services, key_deriver=key_deriver, storage_provider=storage)
    wallet.ensure_initialized()
    return wallet, root_priv


def _balance(wallet: Wallet) -> int:
    """Return the spendable wallet balance in satoshis (best-effort).

    BRC-100: `wallet.balance()` returns a dict like `{"total": int}`.
    """
    r = wallet.balance()
    return int(r.get("total", 0) or 0) if isinstance(r, dict) else 0


def _banner(title: str) -> None:
    """Print a prominent section banner (human-friendly CLI output)."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _debug_enabled() -> bool:
    """Return True if the user requested DEBUG output (LOGLEVEL=DEBUG)."""
    return (os.getenv("LOGLEVEL") or os.getenv("PY_WALLET_TOOLBOX_LOG_LEVEL") or "").upper() == "DEBUG"


def _maybe_print_rawtx_hex(result: dict | None, *, context: str) -> None:
    """Emit raw tx hex to logger when available (DEBUG only)."""
    if not _debug_enabled() or not isinstance(result, dict):
        return
    tx = result.get("tx")
    if not isinstance(tx, list) or not tx:
        return
    try:
        raw_hex = bytes(tx).hex()
    except Exception:
        return
    logger.debug("rawTxHex context=%s len_hex_chars=%s raw=%s", context, len(raw_hex), raw_hex)


def _print_review_actions_error(err: ReviewActionsError, *, context: str) -> None:
    """Pretty-print a ReviewActionsError for CLI debugging."""
    _banner(f"❌ {context} requires review")
    if getattr(err, "txid", None):
        logger.error("%s txid=%s", context, err.txid)
    if getattr(err, "tx", None):
        try:
            raw_hex = bytes(err.tx).hex()
            logger.error("%s rawTxHex len_hex_chars=%s raw=%s", context, len(raw_hex), raw_hex)
        except Exception:
            pass
    rar = getattr(err, "review_action_results", None) or []
    if isinstance(rar, list) and rar:
        logger.error("%s review_action_results=%s", context, len(rar))
        for i, r in enumerate(rar):
            if isinstance(r, dict):
                logger.error(
                    "%s review_action_result idx=%s status=%s fatal=%s txid=%s message=%s",
                    context,
                    i,
                    r.get("status"),
                    r.get("fatal"),
                    r.get("txid"),
                    r.get("message"),
                )


def main() -> None:
    load_dotenv()
    # This enables toolbox trace() output when you run with LOGLEVEL=DEBUG.
    configure_logger(level=os.getenv("LOGLEVEL", "INFO"))
    chain = os.getenv("BSV_NETWORK", "test").strip().lower()
    if chain not in {"test", "main"}:
        print(f"⚠️  Invalid BSV_NETWORK '{chain}', using 'test'")
        chain = "test"
    chain = chain  # type: ignore[assignment]

    use_remote = _env_truthy("USE_STORAGE_SERVER")
    services = _make_services(chain)

    _banner("🚀 E2E: Alice & Bob 2-party roundtrip")
    print(f"chain               : {chain}")
    print(f"use_remote_storage  : {use_remote}")
    if use_remote:
        print(f"storage_server_url  : {os.getenv('STORAGE_SERVER_URL', 'http://localhost:8080')}")
    print(f"loglevel            : {os.getenv('LOGLEVEL', 'INFO')}")

    # Create wallets. Each wallet has a deterministic root key (mnemonic+path) and a storage backend.
    alice, alice_root = _make_wallet("alice", chain, services, use_remote)
    bob, _bob_root = _make_wallet("bob", chain, services, use_remote)

    alice_id = alice.get_public_key({"identityKey": True, "reason": "alice"})["publicKey"]
    bob_id = bob.get_public_key({"identityKey": True, "reason": "bob"})["publicKey"]
    network = Network.TESTNET if chain == "test" else Network.MAINNET
    print("\n--- Wallet identity keys (for explorer correlation) ---")
    print(f"Alice identityKey: {alice_id}")
    print(f"Bob   identityKey: {bob_id}")
    print(f"Alice identity address: {PublicKey(alice_id).address(network=network)}")
    print(f"Bob   identity address: {PublicKey(bob_id).address(network=network)}")

    # Step 1: Fund Alice using a BRC-29 derived address (sender=anyone, recipient=Alice root key).
    faucet_key_id = KeyID(derivation_prefix=FAUCET_DERIVATION_PREFIX, derivation_suffix=FAUCET_DERIVATION_SUFFIX)
    faucet_sender_pubkey_hex = PrivateKey(1).public_key().hex()
    alice_faucet_addr = address_for_self(
        sender_public_key=faucet_sender_pubkey_hex,
        key_id=faucet_key_id,
        recipient_private_key=alice_root,
        testnet=(chain == "test"),
    )["address_string"]

    _banner("💧 Fund Alice (BRC-29 derived address)")
    print("Send BSV to this address, then come back with the funding txid (and the paid output index).")
    print(f"Alice faucet address (BRC-29): {alice_faucet_addr}")
    print(f"key_id: {faucet_key_id}")
    input("Press Enter after the transaction is visible in an explorer...")

    # Step 2: Internalize faucet output (recommended). Without this, wallet balance may remain 0.
    faucet_txid = input("Funding txid (64 hex, blank to skip internalize): ").strip()
    if faucet_txid:
        output_index_raw = input("Funding output index (default: 0): ").strip()
        faucet_vout = int(output_index_raw) if output_index_raw else 0
        faucet_remittance = make_wallet_payment_remittance(
            sender_identity_key=faucet_sender_pubkey_hex,
            derivation_prefix=FAUCET_DERIVATION_PREFIX,
            derivation_suffix=FAUCET_DERIVATION_SUFFIX,
        )
        _banner("📥 internalizeAction (Alice funding)")
        print(f"txid: {faucet_txid}")
        print(f"vout: {faucet_vout}")
        try:
            r = internalize_wallet_payment(
                alice,
                services,
                txid=faucet_txid,
                output_index=faucet_vout,
                remittance=faucet_remittance,
                description="Internalize faucet funding",
            )
            if isinstance(r, dict):
                print(f"accepted: {r.get('accepted')}")
                print(f"satoshis: {r.get('satoshis')}")
        except Exception as e:
            print(f"❌ internalize failed: {e}")
            return

    alice_bal = _balance(alice)
    _banner("💰 Balance after funding")
    print(f"Alice balance: {alice_bal} sats")
    if alice_bal < 1000:
        print("Balance too low for this demo. Fund more and retry.")
        return

    # Step 3: Alice pays Bob (80%), then Bob internalizes.
    send_a = int(alice_bal * 0.8)
    _banner(f"💸 Alice -> Bob ({send_a} sats)")
    # Show the derived destination address to make explorer debugging easy.
    to_addr = address_for_counterparty(
        sender_private_key=alice.key_deriver,
        key_id=KeyID(
            derivation_prefix=ALICE_TO_BOB_DERIVATION_PREFIX, derivation_suffix=ALICE_TO_BOB_DERIVATION_SUFFIX
        ),
        recipient_public_key=bob_id,
        testnet=(chain == "test"),
    )["address_string"]
    print(f"to (derived address): {to_addr}")
    try:
        a = send_wallet_payment_ex(
            alice,
            bob,
            amount_satoshis=send_a,
            derivation_prefix=ALICE_TO_BOB_DERIVATION_PREFIX,
            derivation_suffix=ALICE_TO_BOB_DERIVATION_SUFFIX,
        )
    except ReviewActionsError as err:
        _print_review_actions_error(err, context="create_action (Alice->Bob)")
        return
    a_txid, a_vout, a_remit = a["txid"], a["vout"], a["remittance"]
    print(f"Broadcast txid: {a_txid}")
    _maybe_print_rawtx_hex(a.get("signActionResult") or a.get("createActionResult"), context="Alice->Bob")
    input("Press Enter after the transaction is visible (then Bob will internalize it)...")

    _banner("📥 internalizeAction (Bob receives from Alice)")
    internalize_wallet_payment(
        bob, services, txid=a_txid, output_index=a_vout, remittance=a_remit, description="Internalize from Alice"
    )
    bob_bal = _balance(bob)
    print(f"Bob balance: {bob_bal} sats")

    # Step 4: Bob pays Alice back (80%), then Alice internalizes.
    send_b = int(bob_bal * 0.8)
    _banner(f"💸 Bob -> Alice ({send_b} sats)")
    to_addr2 = address_for_counterparty(
        sender_private_key=bob.key_deriver,
        key_id=KeyID(
            derivation_prefix=BOB_TO_ALICE_DERIVATION_PREFIX, derivation_suffix=BOB_TO_ALICE_DERIVATION_SUFFIX
        ),
        recipient_public_key=alice_id,
        testnet=(chain == "test"),
    )["address_string"]
    print(f"to (derived address): {to_addr2}")
    try:
        b = send_wallet_payment_ex(
            bob,
            alice,
            amount_satoshis=send_b,
            derivation_prefix=BOB_TO_ALICE_DERIVATION_PREFIX,
            derivation_suffix=BOB_TO_ALICE_DERIVATION_SUFFIX,
        )
    except ReviewActionsError as err:
        _print_review_actions_error(err, context="create_action (Bob->Alice)")
        return
    b_txid, b_vout, b_remit = b["txid"], b["vout"], b["remittance"]
    print(f"Broadcast txid: {b_txid}")
    _maybe_print_rawtx_hex(b.get("signActionResult") or b.get("createActionResult"), context="Bob->Alice")
    input("Press Enter after the transaction is visible (then Alice will internalize it)...")
    _banner("📥 internalizeAction (Alice receives from Bob)")
    internalize_wallet_payment(
        alice, services, txid=b_txid, output_index=b_vout, remittance=b_remit, description="Internalize from Bob"
    )

    _banner("📊 Final balances")
    print(f"Alice: {_balance(alice)} sats")
    print(f"Bob  : {_balance(bob)} sats")


if __name__ == "__main__":
    main()
