"""Manual tests for ProvenTxReq error review.

These tests analyze ProvenTxReq history to identify and fix inconsistencies
in transaction status transitions (completed ↔ doubleSpend ↔ invalid ↔ unmined).

Implementation Intent:
- Review ProvenTxReq records with error statuses (doubleSpend, invalid)
- Analyze history notes to understand status transition patterns
- Identify false positives where transactions were incorrectly marked as errors
- Provide tools to correct database state based on actual blockchain status

Why Manual Test:
1. Requires live database connection (MySQL with production data)
2. Performs actual database updates to fix incorrect statuses
3. Needs human review of analysis results before applying fixes
4. Uses real blockchain services to verify current transaction status

Background:
ProvenTxReq tracks transaction proof requests with statuses:
- nosend: Not sent yet
- unsent: Ready to send
- sending: Currently being sent
- unconfirmed: Sent but not confirmed
- unmined: Not yet mined into a block
- completed: Successfully mined and proven
- doubleSpend: Detected double-spend (may be false positive)
- invalid: Invalid transaction (may be false positive)

The history notes field contains JSON array tracking all status changes,
which this test analyzes to find problematic transition patterns.

Reference: wallet-toolbox/test/Wallet/support/reqErrorReview.2025.05.06.man.test.ts
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

import pytest
from bsv_wallet_toolbox.beef import Beef
from bsv_wallet_toolbox.transaction import Transaction
from bsv_wallet_toolbox.utility import Format

logger = logging.getLogger(__name__)


async def create_main_review_setup() -> dict[str, Any]:
    """Create setup for mainnet review operations.

    Returns:
        Setup dict with storage, services, env

    Reference: wallet-toolbox/test/utils/TestUtilsWalletStorage.ts
               createMainReviewSetup()
    """
    try:
        from bsv_wallet_toolbox.storage import StorageMySQL

        from bsv_wallet_toolbox.services import Services
    except ImportError:
        logger.warning("Required modules not yet implemented")
        raise NotImplementedError("Manual test setup requires StorageMySQL, Services implementation.")

    # Get MySQL connection from environment
    cloud_mysql_connection = os.getenv("CLOUD_MYSQL_CONNECTION")
    if not cloud_mysql_connection:
        raise ValueError("CLOUD_MYSQL_CONNECTION environment variable must be set")

    connection = json.loads(cloud_mysql_connection)

    # Create storage and services
    storage = StorageMySQL(connection=connection, chain="main")
    await storage.make_available()
    services = Services(chain="main")

    return {"storage": storage, "services": services, "env": {}}  # Environment config placeholder


async def create_wallet_only(
    chain: str | None = None, root_key_hex: str | None = None, priv_key_hex: str | None = None
) -> dict[str, Any]:
    """Create wallet-only setup (no storage yet).

    Args:
        chain: 'main' or 'test', defaults to 'main'
        root_key_hex: Root key in hex format (64 chars)
        priv_key_hex: Private key in hex format (alternative to root_key)

    Returns:
        Dict with wallet, storage manager, identityKey, chain, rootKey

    Reference: wallet-toolbox/test/utils/TestUtilsWalletStorage.ts
               createWalletOnly()
    """
    try:
        from bsv_wallet_toolbox.key_derivation import PrivateKey
        from bsv_wallet_toolbox.storage import WalletStorageManager

        from bsv_wallet_toolbox.wallet import Wallet
    except ImportError:
        raise NotImplementedError("Manual test setup requires Wallet, WalletStorageManager, PrivateKey implementation.")

    # Defaults
    if chain is None:
        chain = "main"

    # Generate or use provided root key
    if root_key_hex:
        root_key = PrivateKey.from_hex(root_key_hex)
    elif priv_key_hex:
        root_key = PrivateKey.from_hex(priv_key_hex)
    else:
        root_key = PrivateKey.from_random()

    # Derive identity key (BRC-43 master key)
    identity_key = root_key.derive_child("m/0").to_public_key().to_hex()

    # Create wallet storage manager
    storage = WalletStorageManager()

    # Create wallet (but don't add storage provider yet)
    wallet = Wallet(chain=chain, storage=storage)

    return {"wallet": wallet, "storage": storage, "identityKey": identity_key, "chain": chain, "rootKey": root_key}


async def create_sqlite_test_wallet(
    file_path: str, database_name: str, chain: str, root_key_hex: str, drop_all: bool = False
) -> dict[str, Any]:
    """Create SQLite test wallet with full setup.

    This function:
    1. Creates wallet-only setup (identityKey, rootKey)
    2. Creates SQLite storage (StorageSQLite for Python, not Knex)
    3. Optionally drops all existing data
    4. Runs database migrations
    5. Makes storage available
    6. Creates empty setup (no mock data)
    7. Adds storage provider to wallet
    8. Finds or inserts user by identityKey

    Args:
        file_path: Path to SQLite file
        database_name: Database name
        chain: 'main' or 'test'
        root_key_hex: Root key in hex format
        drop_all: Whether to drop all tables

    Returns:
        TestWalletNoSetup dict with:
            - wallet: Wallet instance
            - storage: WalletStorageManager
            - activeStorage: SQLite storage provider (SQLAlchemy-based)
            - identityKey: Identity public key
            - chain: Chain ('main' or 'test')
            - rootKey: Root private key
            - userId: User ID from database
            - setup: Empty setup dict

    Reference: wallet-toolbox/test/utils/TestUtilsWalletStorage.ts
               createSQLiteTestWallet() -> createKnexTestWallet() -> createKnexTestWalletWithSetup()

    Note: Python uses StorageSQLite (SQLAlchemy) instead of TypeScript's StorageKnex.
    """
    try:
        from bsv_wallet_toolbox.storage import StorageSQLite
        from bsv_wallet_toolbox.utility import random_bytes_hex
    except ImportError:
        logger.warning("StorageSQLite not yet implemented")
        raise NotImplementedError("Manual test setup requires StorageSQLite, random_bytes_hex implementation.")

    # Step 1: Create wallet-only setup
    wallet_only = await create_wallet_only(chain=chain, root_key_hex=root_key_hex)

    # Step 2: Create SQLite storage (Python's StorageSQLite, not Knex)
    active_storage = StorageSQLite(
        chain=wallet_only["chain"],
        file_path=file_path,
        database_name=database_name,
        commission_satoshis=0,
        commission_pub_key_hex=None,
        fee_model={"model": "sat/kb", "value": 1},
    )

    # Step 3: Drop all data if requested
    if drop_all:
        await active_storage.drop_all_data()

    # Step 4: Run database migrations (SQLAlchemy migrations)
    migration_key = random_bytes_hex(33)
    await active_storage.migrate(database_name, migration_key)

    # Step 5: Make storage available
    await active_storage.make_available()

    # Step 6: Create empty setup (insertEmptySetup)
    setup = {}  # Empty setup, no mock data

    # Step 7: Add storage provider to wallet
    await wallet_only["storage"].add_wallet_storage_provider(active_storage)

    # Step 8: Find or insert user
    user_result = await active_storage.find_or_insert_user(wallet_only["identityKey"])
    user = user_result["user"]
    user_id = user["userId"]

    # Return complete test wallet
    return {**wallet_only, "activeStorage": active_storage, "setup": setup, "userId": user_id}


def review_history_notes(req_api: dict[str, Any]) -> dict[str, Any] | None:
    """Review ProvenTxReq history notes and extract status transitions.

    Analyzes history to find:
    - Status transitions (doubleSpend ↔ invalid ↔ completed ↔ unmined)
    - Broadcast results (ARC, WhatsOnChain, Bitails)
    - Aggregate results (success/error counts)

    Args:
        req_api: ProvenTxReq entity dict

    Returns:
        History review info dict or None

    Reference: wallet-toolbox/test/Wallet/support/reqErrorReview.2025.05.06.man.test.ts
               reviewHistoryNotes()
    """
    try:
        from bsv_wallet_toolbox.storage.models import ProvenTxReq
    except ImportError:
        return None

    req = ProvenTxReq(req_api)

    result = {
        "req": req,
        "wasDoubleSpend": False,
        "wasInvalid": False,
        "wasCompleted": False,
        "wasUnmined": False,
        "wasInternalize": False,
        "isDoubleSpend": False,
        "isInvalid": False,
        "isCompleted": False,
        "aggSum": 0,
        "aggregate": None,
        "brArc": None,
        "brWoC": None,
        "brBitails": None,
        "doubleReview": None,
    }

    if not req.history or "notes" not in req.history:
        return None

    notes = req.history["notes"]

    for note in notes:
        what = note.get("what")

        # Status transitions
        if what == "status":
            status_now = note.get("status_now")

            if status_now == "doubleSpend":
                result["isDoubleSpend"] = result["wasDoubleSpend"] = True
                result["isInvalid"] = False
                result["isCompleted"] = False
            elif status_now == "invalid":
                result["isDoubleSpend"] = False
                result["isInvalid"] = result["wasInvalid"] = True
                result["isCompleted"] = False
            elif status_now == "completed":
                result["isDoubleSpend"] = False
                result["isInvalid"] = False
                result["isCompleted"] = result["wasCompleted"] = True
            elif status_now == "unmined":
                result["isDoubleSpend"] = False
                result["isInvalid"] = False
                result["wasUnmined"] = True

        # Aggregate results
        elif what == "aggregateResults":
            result["aggregate"] = {
                "successCount": note.get("successCount", 0),
                "doubleSpendCount": note.get("doubleSpendCount", 0),
                "statusErrorCount": note.get("statusErrorCount", 0),
                "serviceErrorCount": note.get("serviceErrorCount", 0),
                "newReqStatus": note.get("newReqStatus"),
            }
            agg = result["aggregate"]
            result["aggSum"] = (
                agg["doubleSpendCount"] + agg["statusErrorCount"] + agg["serviceErrorCount"] + agg["successCount"]
            )

        # Double spend confirmation
        elif what == "confirmDoubleSpend":
            result["doubleReview"] = {
                "status0": note.get("getStatus0"),
                "status1": note.get("getStatus1"),
                "status2": note.get("getStatus2"),
                "competingTxs": note.get("competingTxs"),
            }

        # Internalize action
        elif what == "internalizeAction":
            result["wasInternalize"] = True

        # Broadcast result parsing
        name = note.get("name")

        if name == "WoCpostRawTx":
            if what == "postRawTxErrorMissingInputs":
                result["brWoC"] = "missingInputs"
            elif what == "postRawTxError":
                if note.get("status") == 504:
                    result["brWoC"] = "serviceError"

        elif name == "WoCpostBeef":
            if what == "postBeefSuccess":
                result["brWoC"] = "success"
            elif what == "postBeefError" and result["brWoC"] is None:
                result["brWoC"] = "invalidTx"

        elif name == "ARCpostBeef":
            if what == "postBeefGetTxDataSuccess":
                if note.get("txStatus") == "STORED":
                    result["brArc"] = "success"

        elif name == "ARCv1tx":
            if what == "postRawTxDoubleSpend":
                if note.get("txStatus") == "DOUBLE_SPEND_ATTEMPTED":
                    result["brArc"] = "doubleSpend"
            elif what == "postRawTxError":
                status_code = note.get("status")
                if status_code == 469:
                    result["brArc"] = "badRoots"
                elif status_code == 463:
                    result["brArc"] = "badBump"
            elif what == "postRawTxSuccess":
                tx_status = note.get("txStatus")
                if tx_status in ["ANNOUNCED_TO_NETWORK", "SEEN_ON_NETWORK", "REQUESTED_BY_NETWORK"]:
                    result["brArc"] = "success"

        elif name == "BitailsPostRawTx":
            if what == "postRawsSuccess" or what == "postRawsSuccessAlreadyInMempool":
                result["brBitails"] = "success"
            elif what == "postRawsErrorMissingInputs":
                result["brBitails"] = "invalidTx"
            elif what == "postRawsError":
                code = note.get("code")
                if code == -26:
                    result["brBitails"] = "invalidTx"
                elif code in [-1, "ESOCKETTIMEDOUT"]:
                    result["brBitails"] = "serviceError"

    return result


class TestReqErrorReview:
    """Test suite for ProvenTxReq error review (manual tests).

    These tests analyze transaction request history to identify and fix
    inconsistencies in status transitions.

    Reference: wallet-toolbox/test/Wallet/support/reqErrorReview.2025.05.06.man.test.ts
               describe('reqErrorReview.2025.05.06.man tests')
    """

    @pytest.mark.asyncio
    async def test_review_reqs_history_and_final_outcome(self) -> None:
        """Given: SQLite database with ProvenTxReq history
           When: Review all request histories and status transitions
           Then: Identify inconsistent status transitions

        This test:
        1. Loads ProvenTxReq history from SQLite file
        2. Analyzes each request's status transition history
        3. Identifies inconsistencies:
           - undouble: completed → doubleSpend (should not happen)
           - uninvalid: completed → invalid (should not happen)
           - uncompleted: doubleSpend/invalid → completed (incorrect transition)
           - deunmined: doubleSpend/invalid → unmined (needs review)
           - noSuccessCompleted: completed with 0 success broadcasts
           - successDouble: doubleSpend with successful broadcasts
           - successInvalid: invalid with successful broadcasts

        Reference: wallet-toolbox/test/Wallet/support/reqErrorReview.2025.05.06.man.test.ts
                   test('1 review reqs history and final outcome')
        """
        # Lists to track inconsistencies
        undouble = []
        uninvalid = []
        uncompleted = []
        deunmined = []
        no_success_completed = []
        success_double = []
        internalize_double = []
        success_invalid = []

        # Load SQLite database with request history
        req_history_path = Path(__file__).parent / "reqhistory.sqlite"

        if not req_history_path.exists():
            logger.warning(f"Request history file not found: {req_history_path}")
            logger.warning("Run test 0 (grab reqs history) first to create the file")
            return

        setup = await create_sqlite_test_wallet(
            file_path=str(req_history_path),
            database_name="reqhistory",
            chain="main",
            root_key_hex="1" * 64,
            drop_all=False,
        )
        storage = setup["activeStorage"]

        try:
            limit = 100
            offset = 0
            agg_sum = -1
            log_output = ""

            # Iterate through all requests
            while True:
                reqs = await storage.find_proven_tx_reqs(
                    partial={}, status=None, paged={"limit": limit, "offset": offset}
                )

                for req_api in reqs:
                    # Skip old requests
                    if req_api["provenTxReqId"] < 11312:
                        continue

                    # Review history
                    review = review_history_notes(req_api)
                    if not review:
                        continue

                    # Check for inconsistencies
                    req_id = req_api["provenTxReqId"]

                    # Completed → DoubleSpend transition
                    if review["isCompleted"] and review["wasDoubleSpend"]:
                        undouble.append(req_id)

                    # Completed → Invalid transition
                    if review["isCompleted"] and review["wasInvalid"]:
                        uninvalid.append(req_id)

                    # DoubleSpend/Invalid → Completed transition
                    if (review["isDoubleSpend"] or review["isInvalid"]) and review["wasCompleted"]:
                        uncompleted.append(req_id)

                    # DoubleSpend/Invalid → Unmined transition
                    if (review["isDoubleSpend"] or review["isInvalid"]) and review["wasUnmined"]:
                        if review["wasInternalize"]:
                            internalize_double.append(req_id)
                        else:
                            deunmined.append(req_id)
                            log_output += (
                                f"deunmined {req_id} "
                                f"arc:{review['brArc']} "
                                f"woc:{review['brWoC']} "
                                f"bit:{review['brBitails']}\n"
                            )

                    # Completed with 0 successful broadcasts
                    if review["aggregate"] and review["aggregate"]["successCount"] == 0 and review["isCompleted"]:
                        no_success_completed.append(req_id)

                    # DoubleSpend with successful broadcasts
                    if review["aggregate"] and review["aggregate"]["successCount"] > 0 and review["isDoubleSpend"]:
                        success_double.append(req_id)

                    # Invalid with successful broadcasts
                    if review["aggregate"] and review["aggregate"]["successCount"] > 0 and review["isInvalid"]:
                        success_invalid.append(req_id)

                    # Track aggregate sum changes
                    if review["aggregate"] and review["aggSum"] != agg_sum:
                        log_output += f"aggSum changed {agg_sum} to {review['aggSum']} reqId={req_id}\n"
                        agg_sum = review["aggSum"]

                if len(reqs) < limit:
                    break
                offset += limit

            # Log results
            if undouble:
                log_output += f"undouble: {json.dumps(undouble)}\n"
            if uninvalid:
                log_output += f"uninvalid: {json.dumps(uninvalid)}\n"
            if uncompleted:
                log_output += f"uncompleted: {json.dumps(uncompleted)}\n"
            if deunmined:
                log_output += f"deunmined: {json.dumps(deunmined)}\n"
            if internalize_double:
                log_output += f"internalizeDouble: {json.dumps(internalize_double)}\n"
            if no_success_completed:
                log_output += f"noSuccessCompleted: {json.dumps(no_success_completed)}\n"
            if success_double:
                log_output += f"successDouble: {json.dumps(success_double)}\n"
            if success_invalid:
                log_output += f"successInvalid: {json.dumps(success_invalid)}\n"

            logger.info(log_output)

        finally:
            await storage.destroy()

    @pytest.mark.asyncio
    async def test_review_deunmined_reqs(self) -> None:
        """Given: Production database and list of deunmined ProvenTxReq IDs
           When: Review transaction validity by reconstructing BEEF and verifying
           Then: Log verification results for each transaction

        This test:
        1. Gets ProvenTxReq by ID from production database
        2. Reconstructs BEEF from rawTx and inputBEEF
        3. Finds missing inputs from storage
        4. Verifies transaction scripts
        5. Logs results: OK, FAIL, or error messages

        Reference: wallet-toolbox/test/Wallet/support/reqErrorReview.2025.05.06.man.test.ts
                   test('2 review deunmined reqs')
        """
        # List of deunmined request IDs from TypeScript test
        deunmined = [
            12304,
            12305,
            12306,
            12307,
            12480,
            12483,
            12484,
            12488,
            12489,
            12490,
            12497,
            14085,
            14086,
            14087,
            14814,
            14816,
            14821,
            14953,
            15170,
        ]

        setup = await create_main_review_setup()
        storage = setup["storage"]
        setup["services"]

        try:
            log_output = ""

            for req_id in deunmined:
                # Find request by ID
                req_api = await storage.find_proven_tx_req_by_id(req_id)
                if not req_api:
                    continue

                try:
                    pass
                except ImportError:
                    logger.warning("Required modules not yet implemented")
                    continue

                # Reconstruct BEEF
                beef = Beef()
                if req_api.get("rawTx"):
                    beef.merge_raw_tx(req_api["rawTx"])
                if req_api.get("inputBEEF"):
                    beef.merge_beef(req_api["inputBEEF"])

                tx = beef.find_txid(req_api["txid"])
                if not tx or not tx.tx:
                    continue

                all_inputs_found = True
                input_log = ""

                # Find missing inputs
                for tx_input in tx.tx.inputs:
                    source_txid = tx_input.source_txid
                    if not source_txid:
                        continue

                    if beef.find_txid(source_txid):
                        continue

                    try:
                        input_beef = await storage.get_beef_for_transaction(source_txid, {})
                        if input_beef:
                            beef.merge_beef(input_beef)
                    except Exception:
                        # Try to find in ProvenTxReq
                        input_reqs = await storage.find_proven_tx_reqs(partial={"txid": source_txid})
                        if input_reqs and input_reqs[0].get("rawTx"):
                            input_tx = Transaction.from_binary(input_reqs[0]["rawTx"])
                            input_log += f"missing input {Format.to_log_string_transaction(input_tx)}"

                        all_inputs_found = False

                # Verify transaction
                if all_inputs_found:
                    tx = beef.find_atomic_transaction(req_api["txid"])
                    try:
                        ok = await tx.verify("scripts only")
                        log_output += f"{req_id} {req_api['txid']} {'OK' if ok else 'FAIL'}\n"
                    except Exception as e:
                        log_output += f"{req_id} {req_api['txid']} {e!s}\n"
                else:
                    log_output += f"{req_id} FAILED {Format.to_log_string_beef_txid(beef, req_api['txid'])}"
                    log_output += input_log

            logger.info(log_output)

        finally:
            await storage.destroy()
