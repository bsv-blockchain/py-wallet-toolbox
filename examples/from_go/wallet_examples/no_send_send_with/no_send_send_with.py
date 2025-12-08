import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

"""NoSend and SendWith Example based on PushDrop Tokens.

This example shows how to construct multiple transactions without broadcasting them immediately (NoSend),
chain their internal change across steps (NoSendChange), and then broadcast them together in a single batch using SendWith.
The demo uses simple PushDrop "tokens" to make the flow concrete.
"""

import secrets
from typing import List

from internal import setup, show

# Import token modules from local directory
import importlib.util
from pathlib import Path

# Import token.py (Token, Tokens classes)
_token_path = Path(__file__).parent / "token" / "token.py"
_spec = importlib.util.spec_from_file_location("token", _token_path)
token = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(token)

# Import mint.py (mint_push_drop_token function)
_mint_path = Path(__file__).parent / "token" / "mint.py"
_mint_spec = importlib.util.spec_from_file_location("mint", _mint_path)
mint_module = importlib.util.module_from_spec(_mint_spec)
_mint_spec.loader.exec_module(mint_module)

# Import redeem.py (redeem_push_drop_token function)
_redeem_path = Path(__file__).parent / "token" / "redeem.py"
_redeem_spec = importlib.util.spec_from_file_location("redeem", _redeem_path)
redeem_module = importlib.util.module_from_spec(_redeem_spec)
_redeem_spec.loader.exec_module(redeem_module)

TOKENS_COUNT = 3
DATA_PREFIX = "exampletoken"


def random_key_id() -> str:
    """Generate random key ID."""
    return secrets.token_urlsafe(8)


def mint(alice: setup.Setup, alice_wallet, key_id: str) -> token.Tokens:
    """Mint multiple tokens."""
    prev_no_send_change = []
    tokens = token.Tokens()

    show.step("Mint multiple tokens", "all mints are done with noSend = true, so they are not broadcasted immediately")
    # Mint multiple tokens with noSend = true, each time passing the change from the previous mint as noSendChange to the next mint
    # This way we ensure that all mints will be broadcasted in a single batch
    for counter in range(TOKENS_COUNT):
        data_field = f"{DATA_PREFIX}-{counter}".encode("utf-8")

        tok, no_send_change_outpoints = mint_module.mint_push_drop_token(
            alice.identity_key,
            alice_wallet,
            data_field,
            key_id,
            prev_no_send_change,
        )

        tokens.append(tok)
        prev_no_send_change = no_send_change_outpoints

        show.info("Minted Token", tok.tx_id)

    show.step("Broadcast all mints in a single batch using sendWith", "all mints are now broadcasted in a single batch using sendWith")
    # Now send all the mints in a single batch using sendWith
    send_with(alice_wallet, tokens.tx_ids())

    show.success("All tokens minted and broadcasted")

    return tokens


def redeem(tokens: token.Tokens, alice_wallet) -> None:
    """Redeem multiple tokens."""
    show.step("Redeem multiple tokens", "all redeems are done with noSend = true, so they are not broadcasted immediately")
    # Redeem multiple tokens with noSend = true, each time passing the change from the previous redeem as noSendChange to the next redeem
    # This way we ensure that all redeems will be broadcasted in a single batch
    # We also collect the txIDs of all redeems to use them in sendWith later
    prev_no_send_change = []
    redeemed = []
    
    for tok in tokens:
        redeemed_tx_id, no_send_change = redeem_module.redeem_push_drop_token(
            alice_wallet,
            tok,
            prev_no_send_change,
        )

        redeemed.append(redeemed_tx_id)
        prev_no_send_change = no_send_change

    show.step("Broadcast all redeems in a single batch using sendWith", "all redeems are now broadcasted in a single batch using sendWith")
    # Now send all the redeems in a single batch using sendWith
    send_with(alice_wallet, redeemed)

    show.success("All tokens redeemed and broadcasted")


def send_with(alice_wallet, tx_ids: List[str]) -> None:
    """Broadcast a batch of transactions using SendWith."""
    alice_wallet.create_action({
        "options": {
            "sendWith": tx_ids,
        },
        "description": "sendWith",
        "outputs": [], # Required by CreateActionArgs usually?
    }, "")


def main() -> None:
    show.process_start("NoSend and SendWith Example based on PushDrop Tokens")

    alice = setup.create_alice()
    alice_wallet, cleanup = alice.create_wallet()
    try:
        key_id = random_key_id()

        tokens = mint(alice, alice_wallet, key_id)

        redeem(tokens, alice_wallet)

        show.process_complete("NoSend and SendWith Example based on PushDrop Tokens")

    finally:
        cleanup()


if __name__ == "__main__":
    main()

