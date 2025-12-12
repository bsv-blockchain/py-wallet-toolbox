import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

"""Token redemption implementation for PushDrop example."""

from typing import List, Tuple

from bsv.script.type import P2PKH
from bsv_wallet_toolbox.wallet import Wallet
from internal import show
# Import Token from same directory
import importlib.util
from pathlib import Path as _Path
_token_path = _Path(__file__).parent / "token.py"
_spec = importlib.util.spec_from_file_location("token_module", _token_path)
_token_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_token_mod)
Token = _token_mod.Token

REDEEM_LABEL = "redeemPushDropToken"


def redeem_push_drop_token(
    wallet: Wallet,
    token: Token,
    no_send_change: List[str],
) -> Tuple[str, List[str]]:
    """Redeem a Token."""
    
    label = REDEEM_LABEL
    
    # Spend to self (change)
    # We need a dummy output to satisfy validation
    # Or we can just spend to self P2PKH
    # We need wallet address. 
    # Getting address from wallet instance is not direct in BRC-100 wallet interface?
    # Wallet has private_key.
    # Assuming wallet.get_public_key() returns PublicKey object from sdk
    # Use token's from_identity_key since we are Alice
    address = token.from_identity_key.address()
    
    locking_script = P2PKH().lock(address)
    
    # For noSend chains, don't pass inputBEEF (it has no merkle path)
    # Instead, use knownTxids to let wallet look up from storage
    create_args = {
        "inputs": [
            {
                "outpoint": {
                    "txid": token.tx_id,
                    "vout": 0, 
                },
                "inputDescription": label,
            }
        ],
        "outputs": [
            {
                "lockingScript": locking_script.hex(),
                "satoshis": 500, # Less than input to pay fee
                "outputDescription": "Redeem Output",
            }
        ],
        "options": {
            "noSend": True,
            "noSendChange": no_send_change,
            "randomizeOutputs": False,
            "signAndProcess": True,
            # Tell wallet this txid is known valid (from previous noSend)
            "knownTxids": [token.tx_id],
        },
        "labels": [label],
        "description": label,
    }
    
    result = wallet.create_action(create_args)
    
    signed_tx_id = result["txid"]
    next_no_send_change = result.get("noSendChange", [])
    
    show.info("Redeemed Token", signed_tx_id)
    
    return signed_tx_id, next_no_send_change
