import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

"""Token redemption implementation for PushDrop example."""

from typing import List, Tuple

from bsv.script.type import P2PKH
from bsv_wallet_toolbox.wallet import Wallet
from internal import show
from .token import Token

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
    address = wallet.get_public_key().address() 
    # If not, we can use token.from_identity_key since we are Alice
    
    locking_script = P2PKH.lock(address)
    
    create_args = {
        "inputBEEF": token.beef,
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
        },
        "labels": [label],
        "description": label,
    }
    
    result = wallet.create_action(create_args)
    
    signed_tx_id = result["txid"]
    next_no_send_change = result.get("noSendChange", [])
    
    show.info("Redeemed Token", signed_tx_id)
    
    return signed_tx_id, next_no_send_change
