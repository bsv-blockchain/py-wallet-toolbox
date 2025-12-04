import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

"""Token minting implementation for PushDrop example."""

from typing import List, Tuple

from bsv.script.type import P2PKH
from bsv.keys import PublicKey
from bsv_wallet_toolbox.wallet import Wallet
from internal import show
from .token import Token

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
    locking_script = P2PKH.lock(address)

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
    # In NoSend mode, we might get the raw tx in 'tx' field.
    
    tok = Token(
        tx_id=tx_id,
        beef=result.get("tx"), 
        key_id=key_id,
        from_identity_key=identity_key,
        satoshis=MINT_SATOSHIS
    )
    
    return tok, result.get("noSendChange", [])
