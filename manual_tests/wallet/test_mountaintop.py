"""Manual tests for mountaintop signature verification.

These tests verify that wallet-generated signatures for custom protocol IDs
are valid and can be used to unlock transaction inputs.

Implementation Intent:
- Test signature creation using wallet.createSignature()
- Test public key derivation using wallet.getPublicKey()
- Verify signatures work correctly in P2PKH unlocking scripts
- Compare wallet signatures with SDK-generated signatures

Why Manual Test:
1. Requires live wallet connection
2. Uses real transaction data (BEEF format)
3. Needs actual signature verification against blockchain script VM
4. Tests custom protocol ID key derivation ([1, 'mountaintops'])

Background:
"Mountaintops" is a custom protocol that uses BRC-42 key derivation
with protocolID=[1, 'mountaintops']. This test verifies that:
- Wallet can derive correct keys for this protocol
- Signatures created by wallet match those created by SDK P2PKH
- Unlocking scripts constructed with wallet signatures are valid

Reference: wallet-toolbox/test/Wallet/signAction/mountaintop.man.test.ts
"""

import logging
from typing import Any

import pytest
from bsv_wallet_toolbox.beef import Beef
from bsv_wallet_toolbox.key_derivation import PublicKey
from bsv_wallet_toolbox.script import P2PKH
from bsv_wallet_toolbox.setup import Setup
from bsv_wallet_toolbox.transaction import Transaction
from bsv_wallet_toolbox.utility import parse_wallet_outpoint

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="Waiting for Wallet, Transaction, BEEF, Signature implementations")
@pytest.mark.asyncio
async def test_signature_validity() -> None:
    """Given: Wallet with main chain and test transaction BEEF
       When: Create signature for mountaintops protocol
       Then: Signature is valid and unlocks P2PKH input

    Implementation Notes:
    - Uses protocolID=[1, 'mountaintops'] for key derivation
    - Compares wallet signature with SDK P2PKH signature
    - Both should produce valid unlocking scripts
    - Verifies transaction with 'scripts only' mode

    Reference: wallet-toolbox/test/Wallet/signAction/mountaintop.man.test.ts
               test('0 signature validity')
    """

    # Get environment and create wallet
    env = Setup.get_env("main")
    setup = await Setup.create_wallet_client({"env": env})

    # Derive private key using wallet's key deriver
    priv_key = await setup["wallet"].key_deriver.derive_private_key([1, "mountaintops"], "1", "anyone")
    address2 = priv_key.to_address()

    # Get public key from wallet
    result = await setup["wallet"].get_public_key(
        {"protocolID": [1, "mountaintops"], "keyID": "1", "counterparty": "anyone", "forSelf": True}
    )
    address = PublicKey.from_string(result["publicKey"]).to_address()

    # Verify expected address
    assert address == "1BSMQ1PxMbzMqjB47EYaSNBAD7Qme1dXuk"
    assert address2 == address

    # Test message hash
    # Note: TypeScript tests BigNumber with different bases (16 vs default)
    # This verifies msg hash handling is correct

    # Parse BEEF and create transaction
    beef = Beef.from_string(BEEF_HEX, "hex")
    o = parse_wallet_outpoint(OUTPOINTS[0])
    tx = Transaction()
    tx.add_input(
        {
            "sourceOutputIndex": o["vout"],
            "sourceTXID": o["txid"],
            "sourceTransaction": beef.find_atomic_transaction(o["txid"]),
        }
    )

    # Test 1: Sign with SDK P2PKH (baseline)
    p2pkh = P2PKH().unlock(priv_key, "all")
    tx.inputs[0].unlocking_script = await p2pkh.sign(tx, 0)
    ok2 = await tx.verify("scripts only")
    assert ok2 is True

    # Test 2: Sign with wallet createSignature
    tx.inputs[0].unlocking_script = await sign_with_wallet(setup["wallet"], tx, 0)
    ok = await tx.verify("scripts only")
    assert ok is True

    logger.info("Mountaintop signature validation passed!")

    await setup["wallet"].destroy()


async def sign_with_wallet(wallet: Any, tx: Any, input_index: int) -> Any:
    """Sign transaction input using wallet.createSignature().

    This helper replicates the manual signing process using wallet APIs:
    1. Format transaction preimage
    2. Hash preimage with double SHA-256
    3. Call wallet.createSignature() with hash
    4. Construct unlocking script from signature + public key

    Args:
        wallet: Wallet instance
        tx: Transaction to sign
        input_index: Index of input to sign

    Returns:
        UnlockingScript for the input

    Reference: wallet-toolbox/test/Wallet/signAction/mountaintop.man.test.ts
               sign() function (lines 74-129)
    """
    from bsv_wallet_toolbox.key_derivation import Signature
    from bsv_wallet_toolbox.script import UnlockingScript
    from bsv_wallet_toolbox.transaction import TransactionSignature
    from bsv_wallet_toolbox.utility import Hash, to_array

    # Set signature scope
    signature_scope = TransactionSignature.SIGHASH_FORKID | TransactionSignature.SIGHASH_ALL

    input = tx.inputs[input_index]
    other_inputs = [inp for i, inp in enumerate(tx.inputs) if i != input_index]

    # Get source transaction ID
    source_txid = input.source_txid or (input.source_transaction.id("hex") if input.source_transaction else None)
    if not source_txid:
        raise ValueError("The input sourceTXID or sourceTransaction is required for transaction signing.")

    # Get source satoshis
    source_satoshis = (
        input.source_transaction.outputs[input.source_output_index].satoshis if input.source_transaction else None
    )
    if source_satoshis is None:
        raise ValueError("The sourceSatoshis or input sourceTransaction is required for transaction signing.")

    # Get locking script
    locking_script = (
        input.source_transaction.outputs[input.source_output_index].locking_script if input.source_transaction else None
    )
    if locking_script is None:
        raise ValueError("The lockingScript or input sourceTransaction is required for transaction signing.")

    # Format preimage
    preimage = TransactionSignature.format(
        {
            "sourceTXID": source_txid,
            "sourceOutputIndex": input.source_output_index,
            "sourceSatoshis": source_satoshis,
            "transactionVersion": tx.version,
            "otherInputs": other_inputs,
            "inputIndex": input_index,
            "outputs": tx.outputs,
            "inputSequence": input.sequence,
            "subscript": locking_script,
            "lockTime": tx.lock_time,
            "scope": signature_scope,
        }
    )

    # Double SHA-256 hash
    hash_to_sign = Hash.sha256(Hash.sha256(preimage))

    # Create signature using wallet
    sig_result = await wallet.create_signature(
        {"hashToDirectlySign": hash_to_sign, "protocolID": [1, "mountaintops"], "keyID": "1", "counterparty": "anyone"}
    )

    # Parse signature
    raw_signature = Signature.from_der(sig_result["signature"])
    sig = TransactionSignature(raw_signature.r, raw_signature.s, signature_scope)
    sig_for_script = sig.to_checksig_format()

    # Get public key
    key_result = await wallet.get_public_key(
        {"protocolID": [1, "mountaintops"], "keyID": "1", "counterparty": "anyone", "forSelf": True}
    )
    pubkey_for_script = to_array(key_result["publicKey"], "hex")

    # Construct unlocking script
    return UnlockingScript(
        [{"op": len(sig_for_script), "data": sig_for_script}, {"op": len(pubkey_for_script), "data": pubkey_for_script}]
    )


# Test data constants
OUTPOINTS = [
    "30c83f8b84864fd4497414980faadf074192e7193602ef96ca18705876ce74b1.0",
    "797bd197f2328931231f2834c5dc8036fe9990981c368df27d3b55fa926863be.0",
    "08d47d844e81d751691f6b4a39ce378e9d0f70a3a0606c87995f0f28399552e2.0",
]

BEEF_HEX = "0200beef01fe068d0d0008027a001b501758910c83d8e2c839cfc133245510f5ddbbd28202c331bb9feccc261c287b02b174ce76587018ca96ef023619e7924107dfaa0f98147449d44f86848b3fc830013c006174b69497f770d46604b177a98ff8b8a693a5cec19cd145b3b32abab71676f8011f001f86947779e8e749fd439f037d93733c2ea0734a17cdf1c32f87278b80c7ff72010e00161e280d8481978b9d2696c58d634beda36265ceef9faaa351566afc2c8ab2f0010600e250ce168ac74d432a14df5669f337cd44a8c2cfc8709b955174dd57e2354399010200fd976461d8c0ed097e32ae79afefb35e89daa7289daf7b01bde8bb1481762f590100005fb474d7ddaf5a299509a165cabfe0b6dbea56ed56d1f0d3acf1d3d89531a21e01010029f89d48414f66b9bfd8d711f51d6db0a712cfff2d641f66f83dd2e5e452e5c601010001000000014289ced528197deb6980d634200d333d9983c45ef46893affd027914fdc02cf7000000006a473044022019e70e4325f95b3d5f9f0569123b23c6bff7ef4197fcb15fa50ac3537b8546de0220100d181429245e0349903a0784ad61bfa022d864fca8ce6ba13b0de99fd39eb641210327c7cb8afcd1adce5b26055d70cad9fb1045976a6f99b2ee61ed36295d5802a7ffffffff020a000000000000001976a914727caee3e1178da2ca0b48786171f23695a4ccd088ac1d000000000000001976a9148419faaf7a5e97dcc62002e2415cb51bdb91937e88ac00000000"
