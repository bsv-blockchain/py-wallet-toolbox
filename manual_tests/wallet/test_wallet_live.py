"""Manual tests for live wallet operations with blockchain.

These tests verify wallet operations in live blockchain environment,
including UTXO validation, change management, wallet payments, and
multi-wallet interactions.

Implementation Intent:
- Test UTXO validation and spendable flag management
- Test available change review across transaction statuses
- Test wallet payment creation and internalization
- Test multi-wallet interactions
- Test BEEF extraction and atomicBEEF generation
- Test monitor operations in live environment

Why Manual Test:
1. Requires live blockchain connection (testnet)
2. Uses real wallet with funded outputs
3. Needs actual transaction broadcast
4. Tests real wallet-to-wallet transfers
5. Requires environment variables (MY_TEST_IDENTITY, DEV_KEYS, etc.)

Background:
These tests operate on live wallets with real blockchain interactions.
They verify end-to-end functionality including transaction creation,
broadcasting, and internalization across multiple wallet instances.

Reference: wallet-toolbox/test/Wallet/live/walletLive.man.test.ts
"""

import json
import logging

import pytest
from bsv_wallet_toolbox.beef import Beef
from bsv_wallet_toolbox.key_derivation import PrivateKey
from bsv_wallet_toolbox.storage.models import EntityProvenTxReq
from bsv_wallet_toolbox.test_utils import (
    confirm_spendable_outputs,
    create_test_wallet_with_storage_client,
    create_wallet_payment_action,
    create_wallet_payment_output,
    get_env,
    verify_one,
)
from bsv_wallet_toolbox.utility import Utils, random_bytes

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="Waiting for confirmSpendableOutputs, Storage implementation")
@pytest.mark.asyncio
async def test_set_change_outputs_spendable_false_if_not_valid_utxos() -> None:
    """Given: Wallet contexts with outputs marked as spendable
       When: Validate outputs against blockchain UTXO status
       Then: Set spendable=false for outputs that are not valid UTXOs

    This test checks all outputs marked as spendable=true and verifies
    them against actual blockchain state. Invalid outputs are updated
    to spendable=false to prevent spending attempts on non-existent UTXOs.

    Reference: wallet-toolbox/test/Wallet/live/walletLive.man.test.ts
               test('1 set change outputs spendable false if not valid utxos')
    """

    # Note: ctxs should be initialized in beforeAll
    ctxs = []  # List of wallet contexts

    for ctx in ctxs:
        ctx["wallet"]
        storage = ctx["activeStorage"]
        services = ctx["services"]

        # Validate spendable outputs
        result = await confirm_spendable_outputs(storage, services)
        not_utxos = result["invalidSpendableOutputs"]

        outputs_to_update = [{"id": o["outputId"], "satoshis": o["satoshis"]} for o in not_utxos]

        total = sum(o["satoshis"] for o in outputs_to_update)

        # Manual review point (TypeScript has debugger here)
        logger.info(f"Found {len(outputs_to_update)} invalid spendable outputs, total: {total} sats")

        # Update outputs to spendable=false
        for o in outputs_to_update:
            await storage.update_output(o["id"], {"spendable": False})


@pytest.mark.skip(reason="Waiting for Storage implementation")
@pytest.mark.asyncio
async def test_review_available_change() -> None:
    """Given: Wallet contexts with various transaction statuses
       When: Query outputs by transaction status
       Then: Returns output counts and totals for each status

    This test reviews available change outputs grouped by transaction status:
    - completed: Confirmed transactions
    - nosend: Not yet sent
    - unproven: Sent but not proven
    - failed: Failed transactions
    - sending: Currently being sent
    - unprocessed: Not yet processed
    - unsigned: Not yet signed

    Reference: wallet-toolbox/test/Wallet/live/walletLive.man.test.ts
               test('2 review available change')
    """

    # Note: ctxs should be initialized in beforeAll
    ctxs = []  # List of wallet contexts

    for ctx in ctxs:
        ctx["wallet"]
        storage = ctx["activeStorage"]
        ctx["services"]
        user_id = ctx["userId"]

        # Find default basket
        baskets = await storage.find_output_baskets({"partial": {"userId": user_id, "name": "default"}})
        basket_id = verify_one(baskets)["basketId"]

        # Query outputs by status
        result = {}
        for status_info in [
            {"name": "completed", "txStatus": ["completed"]},
            {"name": "nosend", "txStatus": ["nosend"]},
            {"name": "unproven", "txStatus": ["unproven"]},
            {"name": "failed", "txStatus": ["failed"]},
            {"name": "sending", "txStatus": ["sending"]},
            {"name": "unprocessed", "txStatus": ["unprocessed"]},
            {"name": "unsigned", "txStatus": ["unsigned"]},
        ]:
            outputs = await storage.find_outputs(
                {"partial": {"basketId": basket_id, "spendable": True}, "txStatus": status_info["txStatus"]}
            )

            total = sum(o["satoshis"] for o in outputs)
            output_count = len(outputs)

            result[status_info["name"]] = {
                "txStatus": status_info["txStatus"],
                "outputCount": output_count,
                "total": total,
                "outputs": [],  # Empty for logging
            }

        # Log results
        log = ""
        for k, v in result.items():
            if v["outputCount"] > 0:
                log += f"{k} count={v['outputCount']} total={v['total']}\n"
        logger.info(log)


@pytest.mark.skip(reason="Waiting for Wallet.abortAction implementation")
@pytest.mark.asyncio
async def test_abort_incomplete_transactions() -> None:
    """Given: Wallet with unsigned transactions
       When: Call abortAction for each unsigned transaction
       Then: Transactions are aborted and outputs released

    Note: TypeScript marks this as test.skip

    Reference: wallet-toolbox/test/Wallet/live/walletLive.man.test.ts
               test.skip('3 abort incomplete transactions')
    """
    # Note: ctxs should be initialized in beforeAll
    ctxs = []  # List of wallet contexts

    for ctx in ctxs:
        wallet = ctx["wallet"]
        storage = ctx["activeStorage"]
        user_id = ctx["userId"]

        # Find unsigned transactions
        txs = await storage.find_transactions({"partial": {"userId": user_id}, "status": ["unsigned"]})

        total = sum(tx["satoshis"] for tx in txs)

        # Manual review point (TypeScript has debugger here)
        logger.info(f"Found {len(txs)} unsigned transactions, total: {total} sats")

        # Abort each transaction
        for tx in txs:
            await wallet.abort_action({"reference": tx["reference"]})


@pytest.mark.skip(reason="Waiting for createWalletPaymentAction implementation")
@pytest.mark.asyncio
async def test_create_a_wallet_payment_output() -> None:
    """Given: Wallet with key deriver
       When: Create wallet payment action to another identity
       Then: Wallet payment output is created successfully

    Note: TypeScript marks this as test.skip

    Reference: wallet-toolbox/test/Wallet/live/walletLive.man.test.ts
               test.skip('4 create a wallet payment output')
    """

    # Note: myCtx should be initialized in beforeAll
    my_ctx = {}  # Primary wallet context

    result = await create_wallet_payment_action(
        {
            "toIdentityKey": "02bec52b12b8575f981cf38f3739ffbbfe4f6c6dbe4310d6384b6e97b122f0d087",
            "outputSatoshis": 100 * 1000,
            "keyDeriver": my_ctx["keyDeriver"],
            "wallet": my_ctx["wallet"],
            "logResult": True,
        }
    )

    logger.info(f"Created wallet payment: {result}")


@pytest.mark.skip(reason="Waiting for Beef, Utils implementation")
@pytest.mark.asyncio
async def test_pull_out_txid_from_beef() -> None:
    """Given: BEEF hex string with multiple transactions
       When: Parse BEEF and find specific txid
       Then: Transaction is extracted with raw bytes

    This test demonstrates BEEF parsing and transaction extraction.

    Reference: wallet-toolbox/test/Wallet/live/walletLive.man.test.ts
               test('5 pull out txid from BEEF')
    """

    beef_hex = "010101015c574f48257202b9bff1b14baaa31cea24b9132555216900c277566d440250c50200beef01fee100190003020602f1fdbfa55c7227d2d9f93b7c2b83596a8e336ced483c1616dd98e8a32054dc6307010102009602f0b0959d085cbfda1a0958f65882b1a2829d66853582c0a530586dd00e930100002a7f27bd83b7d490f6641bbd3a8bdeff31490c14430597302ba579392be33f730201000100000001faba5977e9d7894778490ad3d3cf3ff0144da2920f6b31869dbcc026b693061b000000006a473044022050b2a300cad0e4b4c5ecaf93445937f21f6ec61d0c1726ac46bfb5bc2419af2102205d53e70fbdb0d1181a3cb1ef437ae27a73320367fdb78e8cadbfcbf82054e696412102480166f272ee9b639317c16ee60a2254ece67d0c7190fedbd26d57ac30f69d65ffffffff1da861000000000000c421029b09fdddfae493e309d3d97b919f6ab2902a789158f6f78489ad903b7a14baeaac2131546f446f44744b7265457a6248594b466a6d6f42756475466d53585855475a4735840423b7e26b5fd304a88f2ea28c9cf04d6c0a6c52a3174b69ea097039a355dbc6d95e702ac325c3f07518c9b4370796f90ad74e1c46304402206cd8228dd5102f7d8bd781e71dbf60df6559e90df9b79ed1c2b51d0316432f5502207a8713e899232190322dd4fdac6384f6b416ffa10b4196cdc7edbaf751b4a1156d7502000000000000001976a914ee8f77d351270123065a30a13e30394cbb4a6a2b88ace8030000000000001976a9147c8d0d51b07812872049e60e65a28d1041affc1f88ace8030000000000001976a914494c42ae91ebb8d4df662b0c2c98acfcbf14aff388ac93070000000000001976a9149619d3a2c3669335175d6fbd1d785719418cd69588acef030000000000001976a91435aabdafdc475012b7e2b7ab42e8f0fd9e8b665588ac59da0000000000001976a914c05b882ce290b3c19fbb0fca21e416f204d855a188acf3030000000000001976a9146ccff9f5e40844b784f1a68269afe30f5ec84c5d88accb340d00000000001976a914baf2186a8228a9581e0af744e28424343c6a464d88ace9030000000000001976a914a9c3b08f698df167c352f56aad483c907a0e64f488ac61140000000000001976a914f391b03543456ca68f3953b5ef4883f1299b4a2c88ac44c10500000000001976a914e6631bf6d96f93db48fb51daeace803ad805c09788ace9030000000000001976a9148cac2669fc696f5fb39aa59360a2cd20a6daffac88ac49b00400000000001976a9142c16b8a63604c66aa51f47f499024e327657ab5388acd7d50100000000001976a914ca5b56f03f796f55583c7cdd612c02f8d232669388ac42050000000000001976a914175a6812dbf2a550b1bf0d21594b96f9daf60d7988ac15040000000000001976a9147422a7237bb0fa77691047abf930e0274d193fe788ace9030000000000001976a9141a32c1c07dd4f9c632ce6b43dd28c8b27a37d81588ace8030000000000001976a914d9433de1883950578e9a29013aedb1e66d900bdc88ac39190000000000001976a9149fcdbc118b0114d2cc086a75eb14d880e3e25a9e88ac55390200000000001976a914cccf036ec7ae05690461c9d1be10193b6427055588ac1d010000000000001976a9148578396af7a6783824ff680315cc0a1375d9586e88acb3090000000000001976a9147c63cace8600f5400c8678cb2c843400c0c8ac2788acc55d0000000000001976a9148bf6991866b525f36dda54f7ca393c3a56cfff7188acc9100b00000000001976a914af41bf9bbf9d345f6b7cb37958d4cf43e88b17ef88acda040000000000001976a914ad818fcb671cc5b85dc22056d97a9b31aede4f3288ace8030000000000001976a91403ae9f7e41baee27ab7e66a323e73ee6801b5e1688ac59040000000000001976a9149f19356274a53ffdfb755bd81d40a97fe79b5e9b88ac10340000000000001976a914504dff507fccce4005f2d374cbdb6d5d493ceda288ac00000000000100000001f1fdbfa55c7227d2d9f93b7c2b83596a8e336ced483c1616dd98e8a32054dc63060000006b4830450221009bb61b5ec65cbcee0705cf757eba43e1716bfebf3ef976a09ffc926edee9ce6c022060606f5b5e59a6210067633a1263c23156d426feb1912cea480789beef62568741210208132e357b0d061848e779700eae5d69e5240a2503dd753a00e6cb3a8a920255ffffffff06e8030000000000001976a9149cedb88029c24f8bb9824628dfa0a023c1db5edc88acb40a0000000000001976a914da9b117c6880799eb3a0d0ccca252d7f11be240588ac35290000000000001976a914a8f814d3e2a2112bfe2f158f0596314a4379d45088ac54600000000000001976a91476f6f9a9ede3b7e496c921e6730be0af8d3fdfda88ac0e040000000000001976a91419a4615e24931e0e3b25e150fb362b56c5f4e89688ac253e0000000000001976a91435f0dcc5f8c47821a9d24d456b09995981cdb03f88ac00000000"

    beef = Beef.from_string(beef_hex)
    btx = beef.find_txid("5c574f48257202b9bff1b14baaa31cea24b9132555216900c277566d440250c5")

    logger.info(f"tx: '{Utils.to_hex(btx.raw_tx)}'")
    logger.info(f"\n{beef.to_log_string()}\n")


@pytest.mark.skip(reason="Waiting for createWalletPaymentAction, Wallet.internalizeAction implementation")
@pytest.mark.asyncio
async def test_send_wallet_payment_from_myctx_to_second_wallet_tauri() -> None:
    """Given: Two wallet instances (sender and receiver)
       When: Create wallet payment from sender and internalize in receiver
       Then: Payment is accepted and receiver has new output

    This test uses a hardcoded tauri wallet root key for testing.

    Reference: wallet-toolbox/test/Wallet/live/walletLive.man.test.ts
               test('5z send a wallet payment from myCtx to second wallet')
    """

    # Note: myCtx should be initialized in beforeAll
    my_ctx = {}  # Primary wallet context

    # Tauri test wallet
    tauri_root_key = "1363ef9b14531a52648e1e7e7f430a10ceda1df8d514a2a75d8404094f14a649"
    tauri_identity_key = PrivateKey.from_hex(tauri_root_key).to_public_key().to_string()

    # Create wallet payment
    r = await create_wallet_payment_action(
        {
            "toIdentityKey": tauri_identity_key,
            "outputSatoshis": 1000 * 1000,
            "keyDeriver": my_ctx["keyDeriver"],
            "wallet": my_ctx["wallet"],
            "logResult": True,
        }
    )

    # Create receiver wallet
    to_ctx = await create_test_wallet_with_storage_client(
        {"rootKeyHex": tauri_root_key, "chain": "test"}  # Note: env.chain should be used
    )

    # Internalize payment in receiver wallet
    args = {
        "tx": Utils.to_array(r["atomicBEEF"], "hex"),
        "outputs": [
            {
                "outputIndex": r["vout"],
                "protocol": "wallet payment",
                "paymentRemittance": {
                    "derivationPrefix": r["derivationPrefix"],
                    "derivationSuffix": r["derivationSuffix"],
                    "senderIdentityKey": r["senderIdentityKey"],
                },
            }
        ],
        "description": "from tone wallet",
    }

    rw = await to_ctx["wallet"].internalize_action(args)
    assert rw["accepted"] is True


@pytest.mark.skip(reason="Waiting for createWalletPaymentAction, Wallet.internalizeAction implementation")
@pytest.mark.asyncio
async def test_send_wallet_payment_from_myctx_to_second_wallet() -> None:
    """Given: Two wallet instances (myCtx and myCtx2)
       When: Create wallet payment from myCtx and internalize in myCtx2
       Then: Payment is accepted and notify contains 2 transaction IDs

    This test verifies wallet-to-wallet payment with notification tracking.

    Reference: wallet-toolbox/test/Wallet/live/walletLive.man.test.ts
               test('6 send a wallet payment from myCtx to second wallet')
    """

    # Note: myCtx, myCtx2, stagingStorage should be initialized in beforeAll
    my_ctx = {}  # Primary wallet context
    my_ctx2 = {}  # Secondary wallet context
    staging_storage = None  # MySQL staging storage
    my_identity_key2 = ""  # Second identity key

    # Create wallet payment with random amount
    r = await create_wallet_payment_action(
        {
            "toIdentityKey": my_identity_key2,
            "outputSatoshis": random_bytes(1)[0] + 10,
            "keyDeriver": my_ctx["keyDeriver"],
            "wallet": my_ctx["wallet"],
            "logResult": True,
        }
    )

    # Internalize payment in second wallet
    args = {
        "tx": Utils.to_array(r["atomicBEEF"], "hex"),
        "outputs": [
            {
                "outputIndex": r["vout"],
                "protocol": "wallet payment",
                "paymentRemittance": {
                    "derivationPrefix": r["derivationPrefix"],
                    "derivationSuffix": r["derivationSuffix"],
                    "senderIdentityKey": r["senderIdentityKey"],
                },
            }
        ],
        "description": "from live wallet",
    }

    rw = await my_ctx2["wallet"].internalize_action(args)
    assert rw["accepted"] is True

    # Verify ProvenTxReq has 2 notification transaction IDs
    beef = Beef.from_string(r["atomicBEEF"])
    btx = beef.txs[-1]
    txid = btx.txid

    req = await EntityProvenTxReq.from_storage_txid(staging_storage, txid)
    assert len(req["notify"]["transactionIds"]) == 2


@pytest.mark.skip(reason="Helper function for manual wallet setup")
@pytest.mark.asyncio
async def test_help_setup_my_own_wallet() -> None:
    """Given: Random private key generation
       When: Generate identity key and root key
       Then: Outputs .env file configuration for manual setup

    This is a helper test to generate new wallet credentials.

    Reference: wallet-toolbox/test/Wallet/live/walletLive.man.test.ts
               test('6a help setup my own wallet')
    """

    priv_key = PrivateKey.from_random()
    identity_key = priv_key.to_public_key().to_string()

    log = f"""
    // Add the following to .env file:
    MY_TEST_IDENTITY = '{identity_key}'
    DEV_KEYS = '{{
        "{identity_key}": "{priv_key.to_string()}"
    }}'
    """
    logger.info(log)


@pytest.mark.skip(reason="Waiting for Monitor implementation")
@pytest.mark.asyncio
async def test_run_live_wallet_monitor_once() -> None:
    """Given: Live wallet context with monitor
       When: Call monitor.runOnce()
       Then: Monitor executes all tasks successfully

    Reference: wallet-toolbox/test/Wallet/live/walletLive.man.test.ts
               test('6b run liveWallet Monitor once')
    """
    # Note: ctxs should be initialized in beforeAll
    ctxs = []  # List of wallet contexts
    live_ctx = ctxs[0]

    await live_ctx["monitor"].run_once()
    assert True  # TypeScript just checks 1 === 1


@pytest.mark.skip(reason="Helper function - outputs wallet payment details")
@pytest.mark.asyncio
async def test_send_wallet_payment_to_your_own_wallet() -> None:
    """Given: Environment identity key and root key
       When: Create wallet payment output to specific identity
       Then: Outputs payment details for manual use

    This is a helper test to create payment outputs for external use.

    Reference: wallet-toolbox/test/Wallet/live/walletLive.man.test.ts
               test('6c send a wallet payment from live to your own wallet')
    """

    env = get_env("test")
    my_identity_key = env["identityKey"]
    my_root_key_hex = env["devKeys"][my_identity_key]

    if not my_identity_key or not my_root_key_hex:
        raise ValueError("Requires a .env file with MY_TEST_IDENTITY and corresponding DEV_KEYS entries.")

    to_identity_key = "02947542cf31c8d91c303bba8f981ee9595c414e63c185d495a97c558aa7b2e522"
    r = create_wallet_payment_output(
        {"toIdentityKey": to_identity_key, "fromRootKeyHex": my_root_key_hex, "logResult": True}
    )

    logger.info(f"\n{json.dumps(r)}\n")


@pytest.mark.skip(reason="Waiting for Beef implementation")
@pytest.mark.asyncio
async def test_make_atomic_beef_for_known_txid() -> None:
    """Given: Known transaction ID
       When: Create BEEF with txid only
       Then: AtomicBEEF is generated for the txid

    Reference: wallet-toolbox/test/Wallet/live/walletLive.man.test.ts
               test('6d make atomicBEEF for known txid')
    """

    txid = "6b9e8ed767ed6e6366527ddf8707637f3aaee1093085985c1dd04f347a3c25be"

    beef = Beef()
    beef.merge_txid_only(txid)

    atomic_beef = Utils.to_hex(beef.to_binary_atomic(txid))
    logger.info(
        f"""
BEEF for known txid {txid}

{atomic_beef}

"""
    )


@pytest.mark.skip(reason="Waiting for Storage.getBeefForTransaction implementation")
@pytest.mark.asyncio
async def test_make_atomic_beef_for_txid_from_staging_dojo() -> None:
    """Given: Staging dojo storage and known txid
       When: Get BEEF for transaction from storage
       Then: AtomicBEEF is generated with full transaction data

    Reference: wallet-toolbox/test/Wallet/live/walletLive.man.test.ts
               test('6e make atomicBEEF for txid from staging-dojo')
    """

    # Note: stagingStorage should be initialized in beforeAll
    staging_storage = None  # MySQL staging storage

    txid = "6b9e8ed767ed6e6366527ddf8707637f3aaee1093085985c1dd04f347a3c25be"

    beef = await staging_storage.get_beef_for_transaction(txid, {})

    logger.info(
        f"""
{beef.to_log_string()}

AtomicBEEF for known txid {txid}

{Utils.to_hex(beef.to_binary_atomic(txid))}

"""
    )


@pytest.mark.skip(reason="Waiting for Storage.findOrInsertUser implementation")
@pytest.mark.asyncio
async def test_two_client_wallets() -> None:
    """Given: Two wallet client instances with different identities
       When: Create and destroy wallets multiple times
       Then: Each wallet maintains separate user IDs

    This test verifies that multiple wallet instances can coexist
    and maintain separate user identities.

    Reference: wallet-toolbox/test/Wallet/live/walletLive.man.test.ts
               test('7 test two client wallets')
    """

    # Note: These should be from env
    my_identity_key = ""
    my_identity_key2 = ""
    my_root_key_hex = ""
    my_root_key_hex2 = ""

    # First wallet
    my_ctx = await create_test_wallet_with_storage_client({"rootKeyHex": my_root_key_hex, "chain": "test"})

    u1 = await my_ctx["storage"].find_or_insert_user(my_identity_key)
    await my_ctx["storage"].destroy()

    # Second wallet
    my_ctx2 = await create_test_wallet_with_storage_client({"rootKeyHex": my_root_key_hex2, "chain": "test"})

    u2 = await my_ctx2["storage"].find_or_insert_user(my_identity_key2)
    await my_ctx2["storage"].destroy()

    # Both wallets again
    my_ctx = await create_test_wallet_with_storage_client({"rootKeyHex": my_root_key_hex, "chain": "test"})
    my_ctx2 = await create_test_wallet_with_storage_client({"rootKeyHex": my_root_key_hex2, "chain": "test"})

    u1 = await my_ctx["storage"].find_or_insert_user(my_identity_key)
    u2 = await my_ctx2["storage"].find_or_insert_user(my_identity_key2)

    # Verify different user IDs
    assert u1["user"]["userId"] != u2["user"]["userId"]
