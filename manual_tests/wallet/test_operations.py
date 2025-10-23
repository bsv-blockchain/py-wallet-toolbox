"""Manual tests for wallet operations (database review and maintenance).

These tests require a configured database connection and test data.
Run manually, not in automated CI/CD.

Reference: wallet-toolbox/test/Wallet/support/operations.man.test.ts
"""

import json
import logging
import os
from typing import Any

import pytest
from bsv.merkle_path import MerklePath
from bsv.transaction import Transaction
from bsv_wallet_toolbox.beef import Beef
from bsv_wallet_toolbox.sdk import spec_op_invalid_change
from bsv_wallet_toolbox.utility import Format

logger = logging.getLogger(__name__)

# Manual test - requires environment setup
pytestmark = pytest.mark.manual


async def create_main_review_setup():
    """Create setup for reviewing main chain database.

    Returns:
        Dict with env, storage, and services objects

    Reference: wallet-toolbox/test/utils/TestUtilsWalletStorage.ts
               _tu.createMainReviewSetup()
    """
    try:
        from bsv_wallet_toolbox.storage import StorageMySQL

        from bsv_wallet_toolbox.services import Services
    except ImportError as e:
        raise NotImplementedError("createMainReviewSetup requires StorageMySQL and Services implementation") from e

    # Get environment configuration for main chain
    chain = "main"
    cloud_mysql_connection = os.getenv("CLOUD_MYSQL_CONNECTION")
    if not cloud_mysql_connection:
        raise ValueError("CLOUD_MYSQL_CONNECTION environment variable must be set")

    connection = json.loads(cloud_mysql_connection)

    # Create storage with MySQL connection
    storage = StorageMySQL(connection=connection, chain=chain)
    await storage.make_available()

    # Create services for blockchain queries
    services = Services(chain)

    return {"env": {"chain": chain}, "storage": storage, "services": services}


class TestOperations:
    """Test suite for wallet operations (manual tests).

    These tests perform database review and maintenance operations
    on production databases to identify and fix issues.

    Reference: wallet-toolbox/test/Wallet/support/operations.man.test.ts
               describe('operations.man tests')
    """

    @pytest.mark.asyncio
    async def test_review_and_release_all_production_invalid_change_utxos(self) -> None:
        """Given: Production database with users
           When: Review invalid change UTXOs with 'release' tag
           Then: Identify and list all users with invalid change outputs

        This test:
        1. Connects to production MySQL database
        2. Iterates through all users
        3. Lists outputs in specOpInvalidChange basket with 'release' tag
        4. Logs users who have invalid change UTXOs

        Reference: wallet-toolbox/test/Wallet/support/operations.man.test.ts
                   test('0 review and release all production invalid change utxos')
        """
        try:
            pass
        except ImportError:
            logger.warning("specOpInvalidChange not yet implemented, skipping test")
            return

        setup = await create_main_review_setup()
        storage = setup["storage"]

        try:
            # Get all users
            users = await storage.find_users(partial={})

            # Prepare list outputs args
            v_args = {
                "basket": spec_op_invalid_change,
                "tags": ["release"],
                "tagQueryMode": "all",
                "includeLockingScripts": False,
                "includeTransactions": False,
                "includeCustomInstructions": False,
                "includeTags": False,
                "includeLabels": False,
                "limit": 0,
                "offset": 0,
                "seekPermission": False,
                "knownTxids": [],
            }

            log_output = ""
            with_invalid: dict[int, dict[str, Any]] = {}

            # Check each user for invalid change outputs
            for user in users:
                user_id = user["userId"]
                auth = {"userId": user_id, "identityKey": ""}

                result = await storage.list_outputs(auth, v_args)

                if result["totalOutputs"] > 0:
                    total = sum(o["satoshis"] for o in result["outputs"])
                    log_line = f"userId {user_id}: {result['totalOutputs']} utxos updated, total {total}, {user['identityKey']}\n"

                    for output in result["outputs"]:
                        spendable_status = "spendable" if output.get("spendable") else "spent"
                        log_line += f"  {output['outpoint']} {output['satoshis']} now {spendable_status}\n"

                    logger.info(log_line)
                    log_output += log_line

                    with_invalid[user_id] = {"user": user, "outputs": result["outputs"], "total": total}

            if log_output:
                logger.info(log_output)
            else:
                logger.info("Found zero invalid change outputs.")

        finally:
            await storage.destroy()

    @pytest.mark.asyncio
    async def test_review_and_unfail_false_doublespends(self) -> None:
        """Given: Production database with proven tx reqs marked as doubleSpend
           When: Check actual blockchain status of these transactions
           Then: Identify and unfail transactions that are not actually double spends

        This test:
        1. Finds all ProvenTxReqs with status='doubleSpend'
        2. Checks their actual status on the blockchain
        3. If status is not 'unknown', marks them for unfailing
        4. Updates their status to 'unfail'

        Reference: wallet-toolbox/test/Wallet/support/operations.man.test.ts
                   test('1 review and unfail false doubleSpends')
        """
        setup = await create_main_review_setup()
        storage = setup["storage"]
        services = setup["services"]

        try:
            offset = 0
            limit = 100
            all_unfails: list[int] = []
            reviewed = 0

            # Process in batches
            while True:
                log_output = ""
                unfails: list[int] = []

                # Find double spend reqs
                reqs = await storage.find_proven_tx_reqs(
                    partial={"status": "doubleSpend"}, paged={"limit": limit, "offset": offset}, order_descending=True
                )

                # Check each req against blockchain
                for req in reqs:
                    gsr = await services.get_status_for_txids([req["txid"]])

                    if gsr["results"][0]["status"] != "unknown":
                        log_output += f"unfail {req['provenTxReqId']} {req['txid']}\n"
                        unfails.append(req["provenTxReqId"])

                    reviewed += 1

                logger.info(f"DoubleSpends OFFSET: {offset} {reviewed} {len(unfails)} unfails\n{log_output}")
                all_unfails.extend(unfails)

                if len(reqs) < limit:
                    break

                offset += len(reqs)

            # Update all identified false double spends
            for req_id in all_unfails:
                await storage.update_proven_tx_req(req_id, {"status": "unfail"})

        finally:
            await storage.destroy()

    @pytest.mark.asyncio
    async def test_review_and_unfail_false_invalids(self) -> None:
        """Given: Production database with proven tx reqs marked as invalid
           When: Check actual blockchain status of these transactions
           Then: Identify and unfail transactions that are not actually invalid

        This test:
        1. Finds all ProvenTxReqs with status='invalid'
        2. Checks their actual status on the blockchain
        3. If status is not 'unknown', marks them for unfailing
        4. Updates their status to 'unfail'

        Reference: wallet-toolbox/test/Wallet/support/operations.man.test.ts
                   test('2 review and unfail false invalids')
        """
        setup = await create_main_review_setup()
        storage = setup["storage"]
        services = setup["services"]

        try:
            offset = 0
            limit = 100
            all_unfails: list[int] = []
            reviewed = 0

            # Process in batches
            while True:
                log_output = ""
                unfails: list[int] = []

                # Find invalid reqs
                reqs = await storage.find_proven_tx_reqs(
                    partial={"status": "invalid"}, paged={"limit": limit, "offset": offset}, order_descending=True
                )

                # Check each req against blockchain
                for req in reqs:
                    if not req.get("txid") or not req.get("rawTx"):
                        continue

                    gsr = await services.get_status_for_txids([req["txid"]])

                    if gsr["results"][0]["status"] != "unknown":
                        log_output += f"unfail {req['provenTxReqId']} {req['txid']}\n"
                        unfails.append(req["provenTxReqId"])

                    reviewed += 1

                logger.info(f"Failed OFFSET: {offset} {reviewed} {len(unfails)} unfails\n{log_output}")
                all_unfails.extend(unfails)

                if len(reqs) < limit:
                    break

                offset += len(reqs)

            # Update all identified false invalids
            for req_id in all_unfails:
                await storage.update_proven_tx_req(req_id, {"status": "unfail"})

        finally:
            await storage.destroy()

    @pytest.mark.asyncio
    async def test_review_use_of_outputs_in_all_following_transactions(self) -> None:
        """Given: Production database and specific txids to review
           When: Find transactions that use outputs from specified txids
           Then: Log the transaction chain showing output usage

        This test:
        1. Finds all transactions for a specific userId
        2. Builds BEEF from proven tx reqs
        3. Traces usage of specified outputs through subsequent transactions
        4. Logs the transaction chain

        Reference: wallet-toolbox/test/Wallet/support/operations.man.test.ts
                   test('13 review use of outputs in all following transactions')
        """
        try:
            pass
        except ImportError:
            logger.warning("Beef or Format not yet implemented, skipping test")
            return

        setup = await create_main_review_setup()
        storage = setup["storage"]

        try:
            # Example txids and userId from TypeScript test
            txids = ["2df7b5059112a42fc40adb54ee36244cee0dd216c35ad6c4b6ef4631c14a0e83"]
            user_id = 111

            # Find recent transactions for user
            txs = await storage.find_transactions(
                partial={"userId": user_id},
                status=["completed", "unproven", "failed"],
                order_descending=True,
                paged={"limit": 50},
            )

            all_txids = [tx["txid"] for tx in txs if tx.get("txid")]

            # Get proven tx reqs and build BEEF
            reqs = await storage.find_proven_tx_reqs(partial={}, txids=all_txids)

            beef = Beef()
            for req in reqs:
                if req.get("rawTx"):
                    beef.merge_raw_tx(req["rawTx"])

            # Trace output usage
            for txid in txids:
                outputs = await storage.find_outputs(partial={"txid": txid, "userId": user_id})
                tx_records = await storage.find_transactions(partial={"txid": txid, "userId": user_id})

                if outputs and tx_records:
                    ltx = await Format.to_log_string_table_transaction(tx_records[0], storage)
                    logger.info(ltx)

                    # Find transactions that spend these outputs
                    for beef_tx in beef.txs:
                        tx = beef_tx.tx
                        for input_obj in tx.inputs:
                            if input_obj.source_txid == txid and input_obj.source_output_index == 0:
                                sltx = Format.to_log_string_beef_txid(beef, beef_tx.txid)
                                logger.info(sltx)

        finally:
            await storage.destroy()

    @pytest.mark.asyncio
    async def test_review_inputs_of_tx_utxo_status(self) -> None:
        """Given: Transaction hex with multiple inputs
           When: Check UTXO status of all input sources
           Then: Log UTXO status for each input

        This test:
        1. Parses a transaction from hex
        2. Fetches source transactions for all inputs
        3. Checks UTXO status of each input's source output
        4. Logs the results

        Reference: wallet-toolbox/test/Wallet/support/operations.man.test.ts
                   test('14 review inputs of tx utxo status')
        """
        try:
            pass
        except ImportError:
            logger.warning("Transaction class not yet implemented, skipping test")
            return

        setup = await create_main_review_setup()
        storage = setup["storage"]
        services = setup["services"]

        try:
            # Test transaction hex from TypeScript test (truncated for brevity)
            test_tx_hex = (
                "010000003E63EAF142160AD52F3172D75305D0D495A99AD9F17A693017EF8630C86F37A200000000006A47304402..."
            )

            tx = Transaction.from_hex(test_tx_hex)

            # Fetch all input source transactions
            input_txs: dict[str, Transaction] = {}

            for input_obj in tx.inputs:
                if input_obj.source_txid and input_obj.source_txid not in input_txs:
                    source_result = await services.get_raw_tx(input_obj.source_txid)

                    if not source_result.get("rawTx"):
                        raise ValueError(f"Source transaction {input_obj.source_txid} not found")

                    input_txs[input_obj.source_txid] = Transaction.from_binary(source_result["rawTx"])

            # Check UTXO status for each input
            log_output = ""
            for input_obj in tx.inputs:
                stx = input_txs[input_obj.source_txid]
                output = stx.outputs[input_obj.source_output_index]

                hash_value = services.hash_output_script(output.locking_script.to_hex())
                outpoint = f"{input_obj.source_txid}.{input_obj.source_output_index}"

                utxo_result = await services.get_utxo_status(hash_value, None, outpoint)

                log_output += f"{outpoint} {utxo_result['isUtxo']} {utxo_result['status']}\n"

            logger.info(log_output)

        finally:
            await storage.destroy()

    @pytest.mark.skip(reason="Skipped in TypeScript - review proven_txs by height range")
    @pytest.mark.asyncio
    async def test_review_proven_txs(self) -> None:
        """Given: Production database with proven transactions
           When: Review proven txs by height range and verify Merkle paths
           Then: Update incorrect Merkle path data

        This test:
        1. Iterates through height range (e.g., 895000-895026)
        2. For each proven tx, gets Merkle path from services
        3. Verifies Merkle root and other fields match
        4. Updates proven tx if data is incorrect

        Reference: wallet-toolbox/test/Wallet/support/operations.man.test.ts
                   test.skip('3 review proven_txs')

        Note: Skipped in TypeScript - for detailed Merkle path verification.
        """
        try:
            pass
        except ImportError:
            logger.warning("MerklePath not yet implemented, skipping test")
            return

        setup = await create_main_review_setup()
        storage = setup["storage"]
        services = setup["services"]

        try:
            offset = 0
            limit = 100

            # Review specific height range
            for height in range(895000, 895026):
                log_output = ""

                # Find proven txs at this height
                txs = await storage.find_proven_txs(
                    partial={"height": height}, paged={"limit": limit, "offset": offset}
                )

                for tx in txs:
                    # Get Merkle path from services
                    gmpr = await services.get_merkle_path(tx["txid"])

                    if gmpr and gmpr.get("header") and gmpr.get("merklePath"):
                        mp = gmpr["merklePath"]
                        h = gmpr["header"]
                        mr = mp.compute_root(tx["txid"])

                        # Find index in Merkle path
                        index = None
                        for leaf in mp.path[0]:
                            if leaf.get("hash") == tx["txid"]:
                                index = leaf.get("offset")
                                break

                        # Parse existing Merkle path
                        mp2 = MerklePath.from_binary(tx["merklePath"])
                        mr2 = mp2.compute_root()

                        # Check for mismatches
                        if h["height"] != mp.block_height or h["merkleRoot"] != mr:
                            logger.warning(f"Merkle root mismatch for {tx['txid']} {h['merkleRoot']} != {mr}")
                        else:
                            # Check if update is needed
                            needs_update = (
                                tx["merkleRoot"] != mr
                                or tx["height"] != mp.block_height
                                or tx["blockHash"] != h["hash"]
                                or tx.get("index") != index
                                or mp2.block_height != tx["height"]
                                or mr2 != tx["merkleRoot"]
                                or tx["merklePath"] != mp.to_binary()
                            )

                            if needs_update:
                                await storage.update_proven_tx(
                                    tx["provenTxId"],
                                    {
                                        "merklePath": mp.to_binary(),
                                        "merkleRoot": mr,
                                        "height": mp.block_height,
                                        "blockHash": h["hash"],
                                        "index": index,
                                    },
                                )
                                log_output += f"updated {tx['provenTxId']}\n"

                if log_output:
                    logger.info(log_output)

        finally:
            await storage.destroy()

    @pytest.mark.skip(reason="Skipped in TypeScript - re-internalize failed WUI exports")
    @pytest.mark.asyncio
    async def test_reinternalize_failed_wui_exports(self) -> None:
        """Given: Failed WUI export transactions between users
           When: Re-internalize these transactions into recipient wallets
           Then: Recipients receive the exported funds

        This test:
        1. Finds outputs from user 2 with customInstructions (payee)
        2. Checks if recipient users have received these outputs
        3. For missing outputs, gets BEEF and internalizes into recipient wallet

        Reference: wallet-toolbox/test/Wallet/support/operations.man.test.ts
                   test.skip('10 re-internalize failed WUI exports')

        Note: Skipped in TypeScript - for WUI export recovery.
        """
        setup = await create_main_review_setup()
        storage = setup["storage"]

        try:
            # Source user
            user0_results = await storage.find_users(partial={"userId": 2})
            if not user0_results:
                logger.warning("Source user (userId=2) not found")
                return
            user0 = user0_results[0]

            # Target users
            users = await storage.find_users(partial={"userId": 141})  # 111, 141

            for user in users:
                user_id = user["userId"]
                identity_key = user["identityKey"]

                # Find outputs from user0 to this user that are not yet in recipient's wallet
                # Note: TypeScript uses raw SQL query, Python equivalent
                outputs_from_user0 = await storage.find_outputs(partial={"userId": 2})

                # Filter for outputs with customInstructions matching this user's identityKey
                outputs_to_reinternalize = []
                for output in outputs_from_user0:
                    if output.get("customInstructions"):
                        try:
                            custom_instructions = json.loads(output["customInstructions"])
                            if custom_instructions.get("payee") == identity_key:
                                # Check if output already exists in recipient's wallet
                                existing = await storage.find_outputs(
                                    partial={"userId": user_id, "txid": output["txid"]}
                                )
                                if not existing:
                                    outputs_to_reinternalize.append(output)
                        except json.JSONDecodeError:
                            continue

                if outputs_to_reinternalize:
                    logger.info(f"userId {user_id} {identity_key} {len(outputs_to_reinternalize)} outputs")

                # Re-internalize each output
                for output in outputs_to_reinternalize:
                    # Find completed proven tx req
                    reqs = await storage.find_proven_tx_reqs(partial={"txid": output["txid"], "status": "completed"})
                    if not reqs:
                        continue
                    req = reqs[0]

                    custom_instructions = json.loads(output["customInstructions"])
                    tx_type = custom_instructions.get("type")
                    derivation_prefix = custom_instructions.get("derivationPrefix")
                    derivation_suffix = custom_instructions.get("derivationSuffix")

                    if req and tx_type == "BRC29" and derivation_prefix and derivation_suffix:
                        # Get BEEF for transaction
                        beef = await storage.get_beef_for_transaction(req["txid"], {})

                        # Internalize into recipient wallet
                        await storage.internalize_action(
                            {"userId": user_id, "identityKey": user["identityKey"]},
                            {
                                "tx": beef.to_binary_atomic(req["txid"]),
                                "outputs": [
                                    {
                                        "outputIndex": 0,
                                        "protocol": "wallet payment",
                                        "paymentRemittance": {
                                            "derivationPrefix": derivation_prefix,
                                            "derivationSuffix": derivation_suffix,
                                            "senderIdentityKey": user0["identityKey"],
                                        },
                                    }
                                ],
                                "description": "Internalizing export funds tx into foreign wallet",
                            },
                        )
                        logger.info(f"internalize {user_id} {output['txid']}")

        finally:
            await storage.destroy()

    @pytest.mark.skip(reason="Skipped in TypeScript - review recent transaction change use")
    @pytest.mark.asyncio
    async def test_review_recent_transaction_change_use_for_specific_userid(self) -> None:
        """Given: Specific userId with recent transactions
           When: Review recent transactions and their change outputs
           Then: Log transaction details for review

        This test:
        1. Gets count and finds recent transactions for specific userId
        2. Logs transaction details using Format utility
        3. Also reviews recent proven tx reqs

        Reference: wallet-toolbox/test/Wallet/support/operations.man.test.ts
                   test.skip('11 review recent transaction change use for specific userId')

        Note: Skipped in TypeScript - for reviewing specific user transactions.
        """
        try:
            pass
        except ImportError:
            logger.warning("Format utility not yet implemented, skipping test")
            return

        setup = await create_main_review_setup()
        storage = setup["storage"]

        try:
            user_id = 311  # Specific user from TypeScript test

            # Count transactions
            count_txs = await storage.count_transactions(
                partial={"userId": user_id}, status=["completed", "unproven", "failed"]
            )

            # Get recent 100 transactions
            txs = await storage.find_transactions(
                partial={"userId": user_id},
                status=["unproven", "completed", "failed"],
                paged={"limit": 100, "offset": max(0, count_txs - 100)},
            )

            # Log each transaction
            for tx in txs:
                ls = await Format.to_log_string_table_transaction(tx, storage)
                logger.info(ls)

            # Review recent proven tx reqs
            count_reqs = await storage.count_proven_tx_reqs(partial={}, status=["completed", "unmined"])

            reqs = await storage.find_proven_tx_reqs(
                partial={}, status=["unmined", "completed"], paged={"limit": 100, "offset": count_reqs - 100}
            )

            logger.info(f"Reviewed {len(txs)} transactions and {len(reqs)} proven tx reqs")

        finally:
            await storage.destroy()

    @pytest.mark.skip(reason="Skipped in TypeScript - check storage merged BEEF")
    @pytest.mark.asyncio
    async def test_check_storage_merged_beef(self) -> None:
        """Given: Specific txid and userId
           When: Get proven tx and BEEF for sharing
           Then: Verify Merkle path matches proven tx data

        This test:
        1. Finds proven tx by txid
        2. Verifies Merkle path block height matches
        3. Gets BEEF for sharing specific txids

        Reference: wallet-toolbox/test/Wallet/support/operations.man.test.ts
                   test.skip('12 check storage merged BEEF')

        Note: Skipped in TypeScript - for BEEF verification.
        """
        try:
            pass
        except ImportError:
            logger.warning("MerklePath not yet implemented, skipping test")
            return

        setup = await create_main_review_setup()
        storage = setup["storage"]

        try:
            # Test data from TypeScript
            txid = "efba8b92a22c3308f432b292b5ec7efb3869ecd50c62cb3ddfb83871bc7be194"

            # Find proven tx
            ptx_results = await storage.find_proven_txs(partial={"txid": txid})
            if not ptx_results:
                logger.warning(f"Proven tx {txid} not found")
                return
            ptx = ptx_results[0]

            # Verify Merkle path
            mp = MerklePath.from_binary(ptx["merklePath"])
            assert mp.block_height == ptx["height"], "Merkle path height mismatch"

            # Get BEEF for sharing
            txids_to_share = ["24b19a5179c1f146e825643df4c6dc2ba21674828c20fc2948e105cb1ca91eae"]

            await storage.get_reqs_and_beef_to_share_with_world(txids_to_share, [])

            logger.info(f"BEEF check completed for {txid}")

        finally:
            await storage.destroy()
