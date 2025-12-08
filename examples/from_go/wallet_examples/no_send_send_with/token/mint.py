import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

"""Token minting implementation for PushDrop example."""

from typing import List, Tuple

from bsv.script.type import P2PKH
from bsv.keys import PublicKey
from bsv.transaction import Beef, Transaction
from bsv.transaction import beef as beef_constants
from bsv_wallet_toolbox.wallet import Wallet
from internal import show
# Import Token from same directory
import importlib.util
from pathlib import Path
_token_path = Path(__file__).parent / "token.py"
_spec = importlib.util.spec_from_file_location("token_module", _token_path)
_token_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_token_mod)
Token = _token_mod.Token

PROTOCOL_NAME = "nosendexample"
MINT_LABEL = "mintPushDropToken"
MINT_SATOSHIS = 1000 # Enough for fees

def mint_push_drop_token(
    identity_key: PublicKey,
    wallet: Wallet,
    data_field: bytes,
    key_id: str,
    no_send_change: List[str],
) -> Tuple[Token, List[str]]:
    """Mint a Token (simulated using P2PKH for now)."""
    
    # Use P2PKH to self to allow easy redemption
    # We need an address.
    # In `internal/setup.py`, we have identity_key.
    # We can derive address from it?
    # IdentityKey is a PublicKey.
    address = identity_key.address()
    locking_script = P2PKH().lock(address)

    show.info("Mint token, Locking Script", locking_script.hex())

    create_args = {
        "outputs": [
            {
                "lockingScript": locking_script.hex(),
                "satoshis": MINT_SATOSHIS,
                "outputDescription": MINT_LABEL,
                "tags": ["mint"],
            },
        ],
        "options": {
            "noSend": True,
            "noSendChange": no_send_change,
            "randomizeOutputs": False,
            "acceptDelayedBroadcast": False,
        },
        "labels": [MINT_LABEL],
        "description": MINT_LABEL,
    }

    result = wallet.create_action(create_args)

    tx_id = result["txid"]
    
    # Create a BEEF from the raw transaction for use in subsequent inputs
    # BRC-100 create_action returns raw tx bytes in 'tx' field
    raw_tx = result.get("tx")
    if raw_tx:
        if isinstance(raw_tx, list):
            raw_tx = bytes(raw_tx)
        # Parse raw transaction and wrap in BEEF
        tx_obj = Transaction.from_hex(raw_tx)
        # Use BEEF_V1 constant (0xefbe0001)
        beef = Beef(version=beef_constants.BEEF_V1)
        beef.merge_transaction(tx_obj)
        beef_bytes = beef.to_binary()
    else:
        beef_bytes = None
    
    tok = Token(
        tx_id=tx_id,
        beef=beef_bytes, 
        key_id=key_id,
        from_identity_key=identity_key,
        satoshis=MINT_SATOSHIS
    )
    
    return tok, result.get("noSendChange", [])
