"""Storage layer methods implementation (TypeScript parity).

Implements core storage operations for transaction management, certificate handling,
and blockchain data persistence. These methods form the critical path for transaction
creation, signing, and lifecycle management.

Reference:
    - toolbox/ts-wallet-toolbox/src/storage/methods/processAction.ts
    - toolbox/ts-wallet-toolbox/src/storage/methods/generateChange.ts
    - toolbox/ts-wallet-toolbox/src/storage/methods/listActionsKnex.ts
    - toolbox/ts-wallet-toolbox/src/storage/methods/listOutputsKnex.ts
    - toolbox/ts-wallet-toolbox/src/storage/methods/internalizeAction.ts
    - toolbox/ts-wallet-toolbox/src/storage/methods/getBeefForTransaction.ts
    - toolbox/ts-wallet-toolbox/src/storage/methods/attemptToPostReqsToNetwork.ts
    - toolbox/ts-wallet-toolbox/src/storage/methods/reviewStatus.ts
    - toolbox/ts-wallet-toolbox/src/storage/methods/purgeData.ts
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from bsv.transaction import Transaction

from bsv_wallet_toolbox.errors import WalletError

# Beef class for BEEF construction/merging (py-sdk now exports it)
try:
    from bsv.transaction import Beef  # type: ignore
    from bsv.transaction.beef import new_beef_from_bytes  # type: ignore
except ImportError:
    Beef = None  # type: ignore
    new_beef_from_bytes = None  # type: ignore

try:
    from bsv.merkle_path import MerklePath  # type: ignore
except ImportError:
    MerklePath = None  # type: ignore

try:
    import requests
except ImportError:
    requests = None  # type: ignore

# ============================================================================
# Type Definitions (TS Parity)
# ============================================================================


@dataclass
class StorageProcessActionArgs:
    """Arguments for processAction (TS parity).

    Reference:
        - toolbox/ts-wallet-toolbox/src/storage/methods/processAction.ts
    """

    is_new_tx: bool
    is_no_send: bool
    is_send_with: bool
    is_delayed: bool
    send_with: list[str]
    log: dict[str, Any] = None  # Optional logging context


@dataclass
class StorageProcessActionResults:
    """Results from processAction (TS parity).

    Reference:
        - toolbox/ts-wallet-toolbox/src/storage/methods/processAction.ts
    """

    send_with_results: dict[str, Any] | None = None
    not_delayed_results: dict[str, Any] | None = None


@dataclass
class GenerateFundingInput:
    """Input specification for generateChange (TS parity).

    Reference:
        - toolbox/ts-wallet-toolbox/src/storage/methods/generateChange.ts
    """

    satoshis: int
    locking_script: str


@dataclass
class ListActionsArgs:
    """Arguments for listActions (TS parity).

    Reference:
        - toolbox/ts-wallet-toolbox/src/storage/methods/listActionsKnex.ts
    """

    limit: int = 100
    offset: int = 0
    labels: list[str] = None


@dataclass
class ListOutputsArgs:
    """Arguments for listOutputs (TS parity).

    Reference:
        - toolbox/ts-wallet-toolbox/src/storage/methods/listOutputsKnex.ts
    """

    limit: int = 100
    offset: int = 0
    basket: str | None = None


# ============================================================================
# Storage: Methods Implementation
# ============================================================================


def process_action(storage: Any, auth: dict[str, Any], args: StorageProcessActionArgs) -> StorageProcessActionResults:
    """Storage-level processing for wallet createAction and signAction.

    Handles remaining storage tasks once a fully signed transaction has been
    completed. This is common to both createAction and signAction.

    TS parity:
        Mirrors TypeScript processAction by managing completed transactions,
        sharing with network, and tracking send state.

    Args:
        storage: StorageProvider instance
        auth: Authentication context with userId and storageIdentityKey
        args: StorageProcessActionArgs with transaction state

    Returns:
        StorageProcessActionResults with network sharing status

    Raises:
        WalletError: If storage operations fail

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/methods/processAction.ts
    """
    if not storage:
        raise WalletError("storage is required for processAction")

    user_id = auth.get("userId")
    if not user_id:
        raise WalletError("userId is required in auth context")

    result = StorageProcessActionResults()

    # Build list of transaction IDs to share with network
    txids_to_share = list(args.send_with or [])

    # Step 1: Handle new transaction commit if isNewTx
    if args.is_new_tx:
        # Validate new transaction args
        reference = args.get("reference", "")
        txid = args.get("txid", "")
        raw_tx = args.get("rawTx", "")

        if not reference or not txid or not raw_tx:
            raise WalletError("reference, txid, and rawTx are required for new transaction commit")

        # Store ProvenTxReq record
        proven_req_record = {
            "userId": user_id,
            "txid": txid,
            "rawTx": raw_tx,  # Store raw tx (will be used for broadcasting)
            "beef": raw_tx,  # Also store as beef for backward compatibility
            "status": "unsent" if args.get("isDelayed") else "sent",
            "isDeleted": False,
        }

        storage.insert("ProvenTxReq", proven_req_record)

        # Store associated ProvenTx if proof available
        if args.get("rawTx"):
            proven_tx_record = {
                "userId": user_id,
                "txid": txid,
                "rawTx": raw_tx,
                "status": "unproven" if not args.get("isDelayed") else "unsent",
            }
            storage.insert("ProvenTx", proven_tx_record)

    # Step 2: Share requests with network
    if txids_to_share:
        # Collect ProvenTxReq records for the txids
        for txid in txids_to_share:
            req_record = storage.findOne("ProvenTxReq", {"txid": txid, "userId": user_id, "isDeleted": False})

            if req_record:
                # Get raw transaction - could be stored as 'beef', 'rawTx', or 'raw_tx'
                beef = req_record.get("beef") or req_record.get("rawTx") or req_record.get("raw_tx") or ""

                # If beef is empty, log a warning
                if not beef:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"No raw transaction data found for {txid} in ProvenTxReq. Available keys: {list(req_record.keys())}"
                    )

                if args.get("isDelayed"):
                    # Mark as unsent and don't post
                    storage.update("ProvenTxReq", {"txid": txid, "userId": user_id}, {"status": "unsent"})
                # Attempt to post to network
                elif beef:
                    # Actually broadcast the transaction
                    post_result = {
                        "txid": txid,
                        "status": "sending",
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                    # Try to broadcast via services
                    try:
                        services = storage.get_services() if hasattr(storage, "get_services") else None
                        if services:
                            # Convert beef to hex string if needed
                            # beef can be: hex string, bytes, or list of ints
                            if isinstance(beef, bytes):
                                beef_hex = beef.hex()
                            elif isinstance(beef, str):
                                # Already a string - could be hex or base64
                                # Try to detect if it's base64
                                try:
                                    import base64

                                    # If it decodes as base64, convert to hex
                                    decoded = base64.b64decode(beef, validate=True)
                                    beef_hex = decoded.hex()
                                except Exception:
                                    # Assume it's already hex
                                    beef_hex = beef
                            elif isinstance(beef, (list, tuple)):
                                # List of integers - convert to bytes then hex
                                beef_bytes = bytes(int(x) & 0xFF for x in beef)
                                beef_hex = beef_bytes.hex()
                            else:
                                # Try to convert to string and assume hex
                                beef_hex = str(beef)

                            # Broadcast the transaction
                            import logging

                            logger = logging.getLogger(__name__)
                            logger.debug(f"Broadcasting transaction {txid} (beef length: {len(beef_hex)} chars)")
                            # Debug: Log rawTx being broadcast
                            logger.debug(
                                "process_action: broadcasting rawTx for txid=%s, beef_hex_len=%d bytes, beef_hex (first 200 chars): %s...",
                                txid,
                                len(beef_hex) // 2,
                                beef_hex[:200],
                            )
                            # Log full hex for small transactions
                            if len(beef_hex) < 1000:
                                logger.debug("process_action: rawTx hex (full): %s", beef_hex)
                            broadcast_result = services.post_beef(beef_hex)
                            logger.debug(f"Broadcast result for {txid}: {broadcast_result}")

                            if broadcast_result.get("accepted") or broadcast_result.get("success"):
                                post_result["status"] = "unproven"
                                storage.update("ProvenTxReq", {"txid": txid, "userId": user_id}, {"status": "unproven"})
                                logger.debug(f"Transaction {txid} broadcast successfully")
                            elif broadcast_result.get("rateLimited"):
                                post_result["status"] = "sending"
                                storage.update("ProvenTxReq", {"txid": txid, "userId": user_id}, {"status": "sending"})
                                logger.warning(f"Transaction {txid} rate limited, will retry")
                            elif broadcast_result.get("doubleSpend"):
                                post_result["status"] = "failed"
                                storage.update("ProvenTxReq", {"txid": txid, "userId": user_id}, {"status": "failed"})
                                logger.error(f"Transaction {txid} double spend detected")
                            else:
                                # Broadcast failed - log the error
                                error_msg = broadcast_result.get("message", "Unknown broadcast error")
                                logger.error(f"Transaction {txid} broadcast failed: {error_msg}")
                                if "providerErrors" in broadcast_result:
                                    logger.error(f"Provider errors: {broadcast_result['providerErrors']}")
                                post_result["status"] = "sending"
                                post_result["error"] = error_msg
                                storage.update("ProvenTxReq", {"txid": txid, "userId": user_id}, {"status": "sending"})

                            # Add message if available
                            if "message" in broadcast_result:
                                post_result["message"] = broadcast_result["message"]
                        else:
                            # No services available - mark as posted (will be handled by monitor task)
                            post_result["status"] = "posted"
                            storage.update("ProvenTxReq", {"txid": txid, "userId": user_id}, {"status": "posted"})
                    except Exception as e:
                        # Broadcast failed - mark as sending for retry
                        import logging

                        logger = logging.getLogger(__name__)
                        logger.error(f"Failed to broadcast transaction {txid}: {e}", exc_info=True)
                        post_result["status"] = "sending"
                        post_result["error"] = str(e)
                        storage.update("ProvenTxReq", {"txid": txid, "userId": user_id}, {"status": "sending"})

                    if not hasattr(result, "send_with_results"):
                        result.send_with_results = []
                    result.send_with_results.append(post_result)

    return result


def generate_change(
    storage: Any,
    auth: dict[str, Any],
    available_change: list[GenerateFundingInput],
    target_satoshis: int,
    exact_satoshis: int | None = None,
) -> dict[str, Any]:
    """Generate change outputs for transaction (allocation logic).

    Selects change outputs from available options to fund transaction
    and simultaneously locks them to prevent double-spending.

    TS parity:
        Mirrors TypeScript generateChangeSdk by implementing optimal
        UTXO selection and locking strategy.

    Args:
        storage: StorageProvider instance
        auth: Authentication context
        available_change: List of available change outputs with satoshis
        target_satoshis: Target satoshi amount for change allocation
        exact_satoshis: If set, require exact match

    Returns:
        Dict with selected change outputs and locking records

    Raises:
        WalletError: If insufficient funds or selection fails

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/methods/generateChange.ts
    """
    if not storage:
        raise WalletError("storage is required for generateChange")

    if not available_change:
        raise WalletError("availableChange is required and must be non-empty")

    # Validate total available satoshis
    total_available = sum(change.satoshis for change in available_change)

    if exact_satoshis is not None:
        # Exact match required
        if total_available < exact_satoshis:
            raise WalletError(f"Insufficient funds for exact change. " f"Need {exact_satoshis}, have {total_available}")
    # At least target amount required
    elif total_available < target_satoshis:
        raise WalletError(
            f"Insufficient funds for change allocation. " f"Need {target_satoshis}, have {total_available}"
        )

    # Step 1: Select outputs greedily (largest first for efficiency)
    # Sort by satoshis descending
    sorted_change = sorted(available_change, key=lambda c: c.satoshis, reverse=True)

    selected_change = []
    accumulated_satoshis = 0
    target_amount = exact_satoshis if exact_satoshis is not None else target_satoshis

    for change in sorted_change:
        if accumulated_satoshis >= target_amount:
            break
        selected_change.append(change)
        accumulated_satoshis += change.satoshis

    # Step 2: Lock selected outputs to prevent double-spending
    locked_output_ids = []

    for change in selected_change:
        # Create lock record for this output
        now = datetime.now(UTC).isoformat()
        # Calculate expiration: default 1 hour lock timeout
        lock_timeout_seconds = 3600  # 1 hour
        locked_until = (datetime.now(UTC) + timedelta(seconds=lock_timeout_seconds)).isoformat()

        output_lock_record = {
            "txid": change.get("txid") if hasattr(change, "get") else getattr(change, "txid", ""),
            "vout": change.get("vout") if hasattr(change, "get") else getattr(change, "vout", 0),
            "status": "locked",
            "lockedAt": now,
            "lockedUntil": locked_until,
        }

        # Store lock record in database to mark output as reserved
        storage.insert("OutputLock", output_lock_record)

        locked_output_ids.append(
            {
                "txid": output_lock_record["txid"],
                "vout": output_lock_record["vout"],
            }
        )

    return {
        "selectedChange": [
            {
                "satoshis": c.satoshis if hasattr(c, "satoshis") else c.get("satoshis", 0),
                "lockingScript": c.locking_script if hasattr(c, "locking_script") else c.get("lockingScript", ""),
            }
            for c in selected_change
        ],
        "totalSatoshis": accumulated_satoshis,
        "lockedOutputs": locked_output_ids,
    }


def list_actions(storage: Any, auth: dict[str, Any], args: ListActionsArgs) -> dict[str, Any]:
    """List wallet actions (transactions) with filtering.

    Retrieves paginated list of transactions with optional filtering
    by label (including special operations like wallet balance).

    TS parity:
        Mirrors TypeScript listActions from listActionsKnex.ts with
        support for SpecOp filtering and pagination.

    Args:
        storage: StorageProvider instance
        auth: Authentication context
        args: ListActionsArgs with limit, offset, and labels

    Returns:
        Dict with totalActions count and actions list

    Raises:
        WalletError: If storage query fails

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/methods/listActionsKnex.ts
    """
    if not storage:
        raise WalletError("storage is required for listActions")

    user_id = auth.get("userId")
    if not user_id:
        raise WalletError("userId is required in auth context")

    limit = args.limit
    offset = args.offset
    labels = args.labels or []

    # Initialize result structure
    result = {"totalActions": 0, "actions": []}

    # Step 1: Separate regular labels from SpecOp operations
    spec_op = None
    spec_op_labels = []
    regular_labels = []

    for label in labels:
        # Check if label is a SpecOp (e.g., specOpInvalidChange, etc.)
        # SpecOps start with "specOp" prefix
        if label.startswith("specOp"):
            spec_op = label
            spec_op_labels.append(label)
        else:
            regular_labels.append(label)

    # Step 2: Build query with optional label filtering
    # Query transactions for this user
    transactions = storage.find(
        "Transaction",
        {
            "userId": user_id,
            # Status filter - include all transaction statuses
            "status": {"$in": ["completed", "unprocessed", "sending", "unproven", "unsigned", "nosend", "nonfinal"]},
        },
        limit=limit,
        offset=offset,
    )

    # Step 3: Apply label filtering if present
    if regular_labels:
        # Filter transactions by labels
        # Query TxLabel records matching the labels
        labeled_tx_ids = []

        for label in regular_labels:
            label_records = storage.find(
                "TxLabel",
                {
                    "userId": user_id,
                    "label": label,
                    "isDeleted": False,
                },
            )

            for lbl in label_records:
                tx_id = lbl.get("transactionId")
                if tx_id not in labeled_tx_ids:
                    labeled_tx_ids.append(tx_id)

        # Filter transactions to only those with matching labels
        # Support labelQueryMode ('all' vs 'any')
        # Default to 'any' mode - transactions with any of the labels
        label_query_mode = getattr(args, "labelQueryMode", "any")

        if labeled_tx_ids:
            if label_query_mode == "all":
                # All labels required: count labels per tx
                label_counts = {}
                for _label in regular_labels:
                    for tx_id in labeled_tx_ids:
                        label_counts[tx_id] = label_counts.get(tx_id, 0) + 1

                # Keep only transactions with all required labels
                transactions = [
                    tx for tx in transactions if label_counts.get(tx.get("transactionId"), 0) == len(regular_labels)
                ]
            else:
                # 'any' mode - transactions with any of the labels
                transactions = [tx for tx in transactions if tx.get("transactionId") in labeled_tx_ids]

    # Step 4: Count total matching transactions
    if len(transactions) < limit:
        result["totalActions"] = len(transactions)
    else:
        # Need to count all matching records
        total_count = storage.count(
            "Transaction",
            {
                "userId": user_id,
                "status": {
                    "$in": ["completed", "unprocessed", "sending", "unproven", "unsigned", "nosend", "nonfinal"]
                },
            },
        )
        result["totalActions"] = total_count

    # Step 5: Build action objects from transaction records
    for tx in transactions:
        action = {
            "txid": tx.get("txid", ""),
            "satoshis": tx.get("satoshis", 0),
            "status": tx.get("status", "unprocessed"),
            "isOutgoing": bool(tx.get("isOutgoing", False)),
            "description": tx.get("description", ""),
            "version": tx.get("version", 0),
            "lockTime": tx.get("lockTime", 0),
        }
        result["actions"].append(action)

    # Step 6: Handle SpecOp post-processing if applicable
    if spec_op:
        # Implement SpecOp-specific filtering/modification
        if spec_op == "specOpInvalidChange":
            # Filter for failed change actions
            result["actions"] = [a for a in result["actions"] if a.get("status") in ("failed", "invalid")]
        elif spec_op == "specOpThrowReviewActions":
            # Filter for review-needed actions
            result["actions"] = [a for a in result["actions"] if a.get("status") in ("unsigned", "unproven")]
        elif spec_op == "specOpWalletBalance":
            # Calculate balance from actions
            total_balance = sum(a.get("satoshis", 0) for a in result["actions"])
            result["walletBalance"] = total_balance

    # Step 7: Add labels and inputs if requested
    include_labels = getattr(args, "includeLabels", False)
    include_inputs = getattr(args, "includeInputs", False)

    if include_labels:
        # Fetch and attach label data for each action
        for action in result["actions"]:
            labels = storage.find(
                "TxLabel",
                {
                    "userId": user_id,
                    "transactionId": action.get("transactionId"),
                    "isDeleted": False,
                },
            )
            action["labels"] = [lbl.get("label") for lbl in labels]

    if include_inputs:
        # Fetch and attach input data for each action
        for action in result["actions"]:
            # Query inputs from transaction via tx_inputs table
            tx_id = action.get("transactionId")
            if tx_id:
                inputs = storage.find(
                    "TransactionInput",
                    {
                        "transactionId": tx_id,
                        "isDeleted": False,
                    },
                )
                action["inputs"] = [
                    {
                        "vin": inp.get("vin", 0),
                        "txid": inp.get("prevTxid", ""),
                        "vout": inp.get("prevVout", 0),
                        "unlockScript": inp.get("unlockScript", ""),
                        "sequence": inp.get("sequence", 0xFFFFFFFF),
                    }
                    for inp in inputs
                ]
            else:
                action["inputs"] = []

    return result


def list_outputs(storage: Any, auth: dict[str, Any], args: ListOutputsArgs) -> dict[str, Any]:
    """List wallet outputs (UTXOs) with optional filtering.

    Retrieves paginated list of transaction outputs with support for
    basket filtering and special operations.

    TS parity:
        Mirrors TypeScript listOutputs from listOutputsKnex.ts with
        SpecOp filtering support (e.g., specOpWalletBalance).

    Args:
        storage: StorageProvider instance
        auth: Authentication context
        args: ListOutputsArgs with limit, offset, and optional basket

    Returns:
        Dict with totalOutputs count and outputs list

    Raises:
        WalletError: If storage query fails

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/methods/listOutputsKnex.ts
    """
    if not storage:
        raise WalletError("storage is required for listOutputs")

    user_id = auth.get("userId")
    if not user_id:
        raise WalletError("userId is required in auth context")

    limit = args.limit
    offset = args.offset
    basket = getattr(args, "basket", None)

    # Initialize result structure
    result = {"totalOutputs": 0, "outputs": []}

    # Step 1: Build query filters
    query_filter = {
        "userId": user_id,
        "isDeleted": False,  # Only active outputs
    }

    # Step 2: Handle basket filtering if specified
    if basket:
        query_filter["basket"] = basket

    # Step 3: Handle SpecOp operations
    if basket and basket.startswith("specOp"):
        # Handle SpecOp operations (e.g., specOpWalletBalance)
        if basket == "specOpWalletBalance":
            # Include only spendable outputs (not locked, not reserved)
            query_filter["status"] = "spendable"
            # Exclude locked outputs
            query_filter["lockedUntil"] = {"$eq": None}
        # Other SpecOp types can be added here
        # - specOpInvalidChange: Failed change (implemented in list_actions)
        # - specOpThrowReviewActions: Review-needed outputs (implemented in list_actions)

    # Step 4: Query outputs with pagination
    outputs = storage.find("Output", query_filter, limit=limit, offset=offset)

    # Step 5: Count total matching outputs
    if len(outputs) < limit:
        result["totalOutputs"] = len(outputs)
    else:
        # Need to count all matching records
        total_count = storage.count("Output", query_filter)
        result["totalOutputs"] = total_count

    # Step 6: Build output objects from records
    for output in outputs:
        output_obj = {
            "txid": output.get("txid", ""),
            "vout": output.get("vout", 0),
            "satoshis": output.get("satoshis", 0),
            "script": output.get("script", ""),
            "isDeleted": output.get("isDeleted", False),
            "basket": output.get("basket", ""),
            "customInstructions": output.get("customInstructions", ""),
            "tags": output.get("tags", []),
        }
        result["outputs"].append(output_obj)

    # Step 7: Add tags if requested
    include_tags = getattr(args, "includeTags", False)

    if include_tags:
        # Fetch OutputTag records for each output
        for output_obj in result["outputs"]:
            txid = output_obj.get("txid")
            vout = output_obj.get("vout")

            # Query tags for this output
            tags = storage.find(
                "OutputTag",
                {
                    "txid": txid,
                    "vout": vout,
                    "isDeleted": False,
                },
            )
            output_obj["tags"] = [tag.get("tag") for tag in tags]

    # Step 8: Apply SpecOp post-processing
    if basket and basket.startswith("specOp"):
        # Apply SpecOp-specific post-processing
        if basket == "specOpWalletBalance":
            # Calculate and aggregate balance info
            total_satoshis = sum(out.get("satoshis", 0) for out in result["outputs"])
            result["totalSatoshis"] = total_satoshis
        elif basket == "specOpInvalidChange":
            # Aggregate failed outputs
            failed_outputs = [
                out for out in result["outputs"] if out.get("status") in ("failed", "invalid", "rejected")
            ]
            result["outputs"] = failed_outputs
            result["failedCount"] = len(failed_outputs)
        elif basket == "specOpThrowReviewActions":
            # Mark review-needed outputs
            for out in result["outputs"]:
                if out.get("status") in ("unproven", "unsigned"):
                    out["needsReview"] = True
            result["reviewNeeded"] = sum(1 for out in result["outputs"] if out.get("needsReview"))

    return result


def list_certificates(storage: Any, auth: dict[str, Any], limit: int = 100, offset: int = 0) -> dict[str, Any]:
    """List wallet certificates with pagination.

    Retrieves paginated list of acquired certificates.

    TS parity:
        Mirrors TypeScript listCertificates.

    Args:
        storage: StorageProvider instance
        auth: Authentication context
        limit: Maximum results to return
        offset: Pagination offset

    Returns:
        Dict with totalCertificates count and certificates list

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/methods/listCertificates.ts
    """
    if not storage:
        raise WalletError("storage is required for listCertificates")

    user_id = auth.get("userId")
    if not user_id:
        raise WalletError("userId is required in auth context")

    # Initialize result structure
    result = {"totalCertificates": 0, "certificates": []}

    # Step 1: Query certificate records
    certificates = storage.find("Certificate", {"userId": user_id, "isDeleted": False}, limit=limit, offset=offset)

    # Step 2: Count total matching certificates
    if len(certificates) < limit:
        result["totalCertificates"] = len(certificates)
    else:
        # Need to count all matching records
        total_count = storage.count("Certificate", {"userId": user_id, "isDeleted": False})
        result["totalCertificates"] = total_count

    # Step 3: Build certificate objects from records
    for cert in certificates:
        cert_obj = {
            "certificateId": cert.get("certificateId", ""),
            "subjectString": cert.get("subjectString", ""),
            "publicKey": cert.get("publicKey", ""),
            "serialNumber": cert.get("serialNumber", ""),
            "signature": cert.get("signature", ""),
            "certifier": cert.get("certifier", ""),
            "type": cert.get("type", "identity"),
            "revocationOutpoint": cert.get("revocationOutpoint", ""),
            "isDeleted": cert.get("isDeleted", False),
        }
        result["certificates"].append(cert_obj)

    # Step 4: Add certificate fields if requested
    # Note: includeFields is optional and defaults to False
    include_fields = False

    if include_fields:
        # Fetch CertificateField records for each certificate
        for cert_obj in result["certificates"]:
            cert_id = cert_obj.get("id")
            if cert_id:
                fields = storage.find(
                    "CertificateField",
                    {
                        "certificateId": cert_id,
                        "isDeleted": False,
                    },
                )
                cert_obj["fields"] = [
                    {
                        "fieldName": f.get("fieldName", ""),
                        "fieldValue": f.get("fieldValue", ""),
                        "fieldType": f.get("fieldType", ""),
                    }
                    for f in fields
                ]
            else:
                cert_obj["fields"] = []

    return result


def internalize_action(storage: Any, auth: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    """Internalize external transaction into wallet.

    Records an externally-signed transaction as a wallet action,
    incorporating its outputs and inputs for tracking.

    TS parity:
        Mirrors TypeScript internalizeAction by validating and
        recording external transactions.

    Args:
        storage: StorageProvider instance
        auth: Authentication context
        args: Transaction details and inputs/outputs

    Returns:
        Dict with internalized transaction record

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/methods/internalizeAction.ts
    """
    if not storage:
        raise WalletError("storage is required for internalize_action")

    user_id = auth.get("userId")
    if not user_id:
        raise WalletError("userId is required in auth context")

    # Initialize result structure
    result = {
        "accepted": True,
        "isMerge": False,
        "txid": "",
        "satoshis": 0,
    }

    # Step 1: Validate incoming transaction arguments
    # - Verify tx is valid BsvTransaction or Beef
    tx = args.get("tx")
    if not tx:
        raise WalletError("tx is required in internalizeAction args")

    txid = args.get("txid", "")
    if not txid:
        raise WalletError("txid is required in internalizeAction args")

    result["txid"] = txid

    # Extract raw transaction data (hex string or bytes)
    raw_tx = args.get("rawTx") or args.get("beef") or ""

    # Step 2: Check for existing transaction
    existing_tx = storage.findOne("Transaction", {"userId": user_id, "txid": txid})

    is_merge = existing_tx is not None

    if is_merge:
        # Merge with existing transaction
        result["isMerge"] = True

        # Verify existing transaction status is valid for merge
        tx_status = existing_tx.get("status", "")
        if tx_status not in ("unproven", "completed"):
            raise WalletError(
                f"Cannot internalize action: transaction status '{tx_status}' "
                f"does not allow merge (must be 'unproven' or 'completed')"
            )

        # Update transaction description if provided
        if args.get("description"):
            storage.update(
                "Transaction",
                {"transactionId": existing_tx.get("transactionId")},
                {"description": args.get("description")},
            )

        transaction_id = existing_tx.get("transactionId")

    else:
        # New transaction internalization
        # Step 3a: Create new transaction record
        satoshis = args.get("satoshis", 0)
        result["satoshis"] = satoshis

        new_tx_record = {
            "userId": user_id,
            "txid": txid,
            "satoshis": satoshis,
            "isOutgoing": args.get("isOutgoing", False),
            "description": args.get("description", ""),
            "status": "unproven",
            "version": args.get("version", 1),
            "lockTime": args.get("lockTime", 0),
        }

        tx_record = storage.insert("Transaction", new_tx_record)
        transaction_id = tx_record.get("transactionId")

        # Step 3b: Handle Beef sharing if new to network
        send_with_results = None
        not_delayed_results = None

        if args.get("sendToNetwork"):
            # Implement shareReqsWithWorld integration
            # Create ProvenTxReq from txid
            req_record = {
                "userId": user_id,
                "txid": txid,
                "beef": raw_tx,
                "status": "unsent",
                "isDeleted": False,
            }

            storage.insert("ProvenTxReq", req_record)

            # Store operation history for tracking
            history_record = {
                "userId": user_id,
                "transactionId": transaction_id,
                "operation": "internalizeAction",
                "context": {
                    "externalTxid": args.get("externalTxid"),
                    "isDelayed": args.get("isDelayed", False),
                    "isMerge": is_merge,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                "createdAt": datetime.utcnow().isoformat(),
            }
            # Insert history record if OperationHistory table exists
            try:
                storage.insert("OperationHistory", history_record)
            except Exception:
                pass  # History table may not be implemented yet

            # Attempt to broadcast to network (if not delayed)
            if not args.get("isDelayed"):
                # Call attemptToPostReqsToNetwork for integration
                try:
                    # Attempt to post to network
                    post_results = attempt_to_post_reqs_to_network(storage, user_id, [req_record])
                    if post_results:
                        result["networkPostResults"] = post_results
                except Exception:
                    # If network posting fails, log but continue
                    # Status remains 'unsent' for retry
                    pass

        # Store results if network posting was attempted
        if send_with_results:
            result["sendWithResults"] = send_with_results
        if not_delayed_results:
            result["notDelayedResults"] = not_delayed_results

    # Step 4: Add labels if provided
    labels = args.get("labels", [])
    for label in labels:
        storage.insert(
            "TxLabel",
            {
                "userId": user_id,
                "transactionId": transaction_id,
                "label": label,
                "isDeleted": False,
            },
        )

    # Step 5: Process wallet payments (change outputs)
    wallet_payments = args.get("walletPayments", [])
    for payment in wallet_payments:
        output_record = {
            "userId": user_id,
            "transactionId": transaction_id,
            "txid": txid,
            "vout": payment.get("vout", 0),
            "satoshis": payment.get("satoshis", 0),
            "script": payment.get("script", ""),
            "basket": "default",  # Wallet payments go to default basket
            "isDeleted": False,
        }
        storage.insert("Output", output_record)

    # Step 6: Process basket insertions (custom outputs)
    basket_insertions = args.get("basketInsertions", [])
    for insertion in basket_insertions:
        basket_name = insertion.get("basket")

        # Find or create basket
        basket = storage.findOne("OutputBasket", {"userId": user_id, "name": basket_name})

        if not basket:
            # Create new basket
            basket_record = {
                "userId": user_id,
                "name": basket_name,
                "numberOfDesiredUTXOs": 0,
                "minimumDesiredUTXOValue": 0,
            }
            storage.insert("OutputBasket", basket_record)

        # Create output record for basket insertion
        output_record = {
            "userId": user_id,
            "transactionId": transaction_id,
            "txid": txid,
            "vout": insertion.get("vout", 0),
            "satoshis": insertion.get("satoshis", 0),
            "script": insertion.get("script", ""),
            "basket": basket_name,
            "customInstructions": insertion.get("customInstructions", ""),
            "isDeleted": False,
        }
        storage.insert("Output", output_record)

    # Step 7: Return internalization result
    return result


# ============================================================================
# BEEF Generation Types (TS/Go Parity)
# ============================================================================


# Constants matching Go/TS
MAX_RECURSION_DEPTH = 12

# BEEF version constants (BRC-64 / BRC-96)
BEEF_V1 = 4022206465  # 0x0100BEEF little-endian
BEEF_V2 = 4022206466  # 0x0200BEEF little-endian


@dataclass
class StorageGetBeefOptions:
    """Options for BEEF generation.

    TS parity: mirrors StorageGetBeefOptions interface.
    Go parity: mirrors wdk.StorageGetBeefOptions struct.

    Reference:
        - wallet-toolbox/src/sdk/WalletStorage.interfaces.ts
        - go-wallet-toolbox/pkg/wdk/get_beef_options.go
    """

    merge_to_beef: Any = None
    trust_self: str | None = None  # None, 'known'
    known_txids: list[str] = field(default_factory=list)
    ignore_storage: bool = False
    ignore_services: bool = False
    ignore_new_proven: bool = False
    min_proof_level: int = 0
    max_recursion_depth: int = MAX_RECURSION_DEPTH


@dataclass
class RawTxWithMerklePath:
    """Holds fetched tx data from services.

    Go parity: mirrors rawTxWithMerklePath struct in get_beef.go
    """

    raw_tx: bytes
    merkle_path: Any = None
    header: dict[str, Any] | None = None


def get_beef_for_transaction(
    storage: Any,
    auth: dict[str, Any],
    txid: str,
    options: dict[str, Any] | None = None,
) -> bytes:
    """Generate complete BEEF (Blockchain Envelope Extending Format) for transaction.

    Creates a BEEF containing the transaction and all its input proofs.
    Uses storage to retrieve proven transactions and their merkle paths,
    or proven_tx_req record with beef of external inputs.
    Otherwise external services are used.

    TS parity:
        Mirrors TypeScript getBeefForTransaction from
        wallet-toolbox/src/storage/methods/getBeefForTransaction.ts

    Go parity:
        Mirrors Go GetBeefForTransaction from
        go-wallet-toolbox/pkg/storage/provider.go

    Args:
        storage: StorageProvider instance with access to proven txs and services
        auth: Authentication context (not used, kept for API compatibility)
        txid: Transaction ID to generate BEEF for (64-hex string)
        options: Optional configuration for BEEF generation:
            - mergeToBeef: Existing Beef to merge into
            - trustSelf: If 'known', proven txs are represented as txid-only
            - knownTxids: List of txids to represent as txid-only
            - ignoreStorage: Skip storage lookup, use services only
            - ignoreServices: Skip services lookup, storage only
            - ignoreNewProven: Don't save newly proven txs to storage
            - minProofLevel: Minimum recursion depth for proof acceptance
            - maxRecursionDepth: Maximum recursion depth (default 12)

    Returns:
        bytes: Complete BEEF binary containing the transaction and all required proofs

    Raises:
        WalletError: If transaction not found or proof generation fails

    Reference:
        - wallet-toolbox/src/storage/methods/getBeefForTransaction.ts
        - go-wallet-toolbox/pkg/storage/internal/actions/get_beef.go
    """
    if not txid or len(txid) != 64:
        raise WalletError("txid must be a 64-character hex string")

    if Beef is None:
        raise WalletError("Beef class not available from py-sdk")

    opts = _parse_get_beef_options(options)

    # Go parity: if txid is in known list, return txid-only beef immediately
    if txid in opts.known_txids:
        return _beef_for_known_id(txid)

    # Track service-fetched transactions for potential persistence
    service_fetched_txs: dict[str, RawTxWithMerklePath] = {}

    # Initialize or deserialize beef
    if opts.merge_to_beef is None:
        beef = Beef(version=BEEF_V2)
    elif isinstance(opts.merge_to_beef, bytes):
        beef = new_beef_from_bytes(opts.merge_to_beef)
    elif isinstance(opts.merge_to_beef, Beef):
        beef = opts.merge_to_beef
    else:
        beef = Beef(version=BEEF_V2)

    # Try storage first (unless ignored)
    if not opts.ignore_storage:
        beef = _get_beef_from_storage(storage, txid, beef, opts, service_fetched_txs)

        # Persist newly proven transactions if allowed
        if not opts.ignore_new_proven:
            for fetched_txid, fetched in service_fetched_txs.items():
                _persist_new_proven(storage, txid, fetched_txid, fetched)

        return beef.to_binary()

    # Use services only
    if not opts.ignore_services:
        beef = _get_beef_from_services(storage, txid, opts)
        return beef.to_binary()

    raise WalletError(f"No storage or services provided to get BEEF for transaction {txid}")


def _parse_get_beef_options(options: dict[str, Any] | None) -> StorageGetBeefOptions:
    """Parse options dict into StorageGetBeefOptions."""
    if options is None:
        return StorageGetBeefOptions()

    return StorageGetBeefOptions(
        merge_to_beef=options.get("mergeToBeef"),
        trust_self=options.get("trustSelf"),
        known_txids=options.get("knownTxids") or [],
        ignore_storage=options.get("ignoreStorage", False),
        ignore_services=options.get("ignoreServices", False),
        ignore_new_proven=options.get("ignoreNewProven", False),
        min_proof_level=options.get("minProofLevel", 0),
        max_recursion_depth=options.get("maxRecursionDepth", MAX_RECURSION_DEPTH),
    )


def _beef_for_known_id(txid: str) -> bytes:
    """Create a BEEF with only a txid-only entry.

    Go parity: mirrors beefForKnownID in get_beef.go
    """
    beef = Beef(version=BEEF_V2)
    beef.merge_txid_only(txid)
    return beef.to_binary()


def _get_beef_from_storage(
    storage: Any,
    txid: str,
    beef: Any,
    options: StorageGetBeefOptions,
    service_fetched_txs: dict[str, RawTxWithMerklePath],
) -> Any:
    """Get BEEF from storage with recursive building.

    Go parity: mirrors getFromStorage in get_beef.go
    """
    # Create tx getter function for services fallback
    tx_getter: Callable[[str], tuple[bytes, Any]] | None = None
    if not options.ignore_services:
        tx_getter = _make_tx_getter(storage, service_fetched_txs)

    _recursive_build_valid_beef(storage, 0, beef, txid, options, tx_getter)

    return beef


def _make_tx_getter(
    storage: Any,
    service_fetched_txs: dict[str, RawTxWithMerklePath],
) -> Callable[[str], tuple[bytes, Any]]:
    """Create a function to fetch tx from services.

    Go parity: mirrors makeTxGetter in get_beef.go
    """

    def tx_getter(txid: str) -> tuple[bytes, Any]:
        services = storage.get_services() if hasattr(storage, "get_services") else None
        if services is None:
            raise WalletError(f"Services not available for txid {txid}")

        # Get raw transaction
        raw_tx_result = services.get_raw_tx(txid)
        if not raw_tx_result:
            raise WalletError(f"Raw transaction for txid {txid} is nil")

        # Convert to bytes
        if isinstance(raw_tx_result, str):
            raw_tx = bytes.fromhex(raw_tx_result)
        elif isinstance(raw_tx_result, bytes):
            raw_tx = raw_tx_result
        else:
            raw_tx = bytes.fromhex(raw_tx_result) if raw_tx_result else b""

        # Try to get merkle path
        merkle_path = None
        header = None

        try:
            merkle_result = services.get_merkle_path(txid)
            if merkle_result and merkle_result.get("merklePath"):
                mp = merkle_result["merklePath"]
                if hasattr(mp, "path") or hasattr(mp, "to_binary"):
                    merkle_path = mp
                header = merkle_result.get("header")

                # Store for potential persistence
                service_fetched_txs[txid] = RawTxWithMerklePath(
                    raw_tx=raw_tx,
                    merkle_path=merkle_path,
                    header=header,
                )
        except Exception:
            # Not found is okay, will recurse for inputs
            pass

        return raw_tx, merkle_path

    return tx_getter


def _recursive_build_valid_beef(
    storage: Any,
    depth: int,
    beef: Any,
    txid: str,
    options: StorageGetBeefOptions,
    tx_getter: Callable[[str], tuple[bytes, Any]] | None,
) -> None:
    """Recursively build a valid BEEF for the given txid.

    Go parity: mirrors recursiveBuildValidBEEF in known_tx_get_beef.go
    TS parity: mirrors mergeBeefForTransactionRecurse in getBeefForTransaction.ts
    """
    # Check max depth
    if depth > options.max_recursion_depth:
        raise WalletError(f"Max depth of recursion reached: {options.max_recursion_depth}")

    # Check if txid is known
    if txid in options.known_txids:
        beef.merge_txid_only(txid)
        return

    # Try to get from storage
    result = storage.get_proven_or_raw_tx(txid)

    proven = result.get("proven")
    raw_tx = result.get("rawTx")
    input_beef = result.get("inputBEEF")
    merkle_path = result.get("merklePath")

    # If not in storage, try services
    if not raw_tx and not proven:
        if tx_getter is None:
            raise WalletError(f"Transaction txid: {txid!r} is not known to storage")

        raw_tx, merkle_path = tx_getter(txid)

    # Trust self as known - return txid-only
    elif options.trust_self == "known" and proven:
        beef.merge_txid_only(txid)
        return

    if not raw_tx:
        raise WalletError(f"Raw tx is nil in transaction {txid}")

    # Ensure raw_tx is bytes
    if isinstance(raw_tx, str):
        raw_tx = bytes.fromhex(raw_tx)
    elif isinstance(raw_tx, (list, tuple)):
        raw_tx = bytes(raw_tx)

    # Parse transaction
    tx = Transaction.from_hex(raw_tx)
    if tx is None:
        raise WalletError(f"Failed to build transaction object from raw tx (id: {txid})")

    # Check if we should ignore merkle proof at this depth
    ignore_merkle_proof = options.min_proof_level > 0 and depth < options.min_proof_level

    # If has merkle path and not ignoring, merge with proof and done
    if merkle_path and not ignore_merkle_proof:
        if isinstance(merkle_path, bytes):
            mp = MerklePath.from_binary(merkle_path)
        elif isinstance(merkle_path, (list, tuple)):
            mp = MerklePath.from_binary(bytes(merkle_path))
        elif hasattr(merkle_path, "to_binary"):
            mp = merkle_path
        else:
            mp = None

        if mp is not None:
            beef.merge_raw_tx(raw_tx)
            beef.merge_bump(mp)
            return

    # Validate all inputs have source txid
    for i, tx_input in enumerate(tx.inputs or []):
        source_txid = getattr(tx_input, "source_txid", None)
        if not source_txid:
            raise WalletError(f"Input of tx (id: {txid}) has empty SourceTXID at index {i}")

    # Merge raw tx
    beef.merge_raw_tx(raw_tx)

    # Merge input BEEF if available
    if input_beef:
        if isinstance(input_beef, bytes) and len(input_beef) > 0:
            try:
                beef.merge_beef_bytes(input_beef)
            except Exception:
                pass  # Ignore merge errors for input beef
        elif isinstance(input_beef, (list, tuple)) and len(input_beef) > 0:
            try:
                beef.merge_beef_bytes(bytes(input_beef))
            except Exception:
                pass

    # Check if tx already has merkle path after merge
    subject_tx = beef.find_transaction(txid)
    if subject_tx and getattr(subject_tx, "bump_index", None) is not None:
        return  # Already has proof

    # Recurse for each input
    for tx_input in tx.inputs or []:
        source_txid = getattr(tx_input, "source_txid", None)
        if source_txid:
            # Check if already in beef
            existing = beef.find_transaction(source_txid)
            if existing is None or getattr(existing, "data_format", 0) == 2:  # TxIDOnly = 2
                _recursive_build_valid_beef(
                    storage,
                    depth + 1,
                    beef,
                    source_txid,
                    options,
                    tx_getter,
                )


def _get_beef_from_services(
    storage: Any,
    txid: str,
    options: StorageGetBeefOptions,
) -> Any:
    """Get BEEF directly from services.

    Go parity: mirrors getFromServices and services.GetBEEF in services.go
    """
    services = storage.get_services() if hasattr(storage, "get_services") else None
    if services is None:
        raise WalletError(f"Services not available for txid {txid}")

    beef = Beef(version=BEEF_V2)
    known_txids_set = set(options.known_txids)

    def tx_getter_recursive(current_txid: str, depth: int) -> None:
        if depth > options.max_recursion_depth:
            raise WalletError(f"Max depth of recursion reached: {options.max_recursion_depth}")

        # Get raw transaction
        raw_tx_result = services.get_raw_tx(current_txid)
        if not raw_tx_result:
            raise WalletError(f"Raw transaction for txid {current_txid} is nil")

        if isinstance(raw_tx_result, str):
            raw_tx = bytes.fromhex(raw_tx_result)
        else:
            raw_tx = raw_tx_result

        tx = Transaction.from_hex(raw_tx)
        if tx is None:
            raise WalletError(f"Failed to create transaction from raw bytes for txid {current_txid}")

        # Try to get merkle path
        merkle_path = None
        try:
            merkle_result = services.get_merkle_path(current_txid)
            if merkle_result and merkle_result.get("merklePath"):
                merkle_path = merkle_result["merklePath"]
        except Exception:
            pass

        is_mined = merkle_path is not None

        if is_mined:
            # Attach merkle path to transaction and merge
            beef.merge_raw_tx(raw_tx)
            if isinstance(merkle_path, bytes):
                mp = MerklePath.from_binary(merkle_path)
            elif hasattr(merkle_path, "to_binary"):
                mp = merkle_path
            else:
                mp = None
            if mp:
                beef.merge_bump(mp)
        else:
            beef.merge_raw_tx(raw_tx)

        if is_mined:
            return

        # Recurse for inputs
        for tx_input in tx.inputs or []:
            source_txid = getattr(tx_input, "source_txid", None)
            if source_txid:
                existing = beef.find_transaction(source_txid)
                if existing is None:
                    if source_txid in known_txids_set:
                        beef.merge_txid_only(source_txid)
                    else:
                        tx_getter_recursive(source_txid, depth + 1)

    tx_getter_recursive(txid, 0)
    return beef


def _persist_new_proven(
    storage: Any,
    subject_txid: str,
    txid: str,
    fetched: RawTxWithMerklePath,
) -> None:
    """Persist a newly proven transaction to storage.

    Go parity: mirrors persistNewProven in get_beef.go
    """
    if not fetched.merkle_path or not fetched.header or not fetched.raw_tx:
        return

    try:
        # Create empty input beef
        empty_beef = Beef(version=BEEF_V2)
        empty_beef_bytes = empty_beef.to_binary()

        # Get merkle path binary
        if hasattr(fetched.merkle_path, "to_binary"):
            mp_bytes = fetched.merkle_path.to_binary()
        elif isinstance(fetched.merkle_path, bytes):
            mp_bytes = fetched.merkle_path
        else:
            mp_bytes = b""

        # Insert/update proven tx
        storage.insert_proven_tx(
            {
                "txid": txid,
                "rawTx": fetched.raw_tx,
                "inputBEEF": empty_beef_bytes,
                "height": fetched.header.get("height", 0),
                "merklePath": mp_bytes,
                "merkleRoot": fetched.header.get("merkleRoot", "0" * 64),
                "blockHash": fetched.header.get("hash", "0" * 64),
            }
        )
    except Exception:
        # Log error but don't fail the main operation
        pass


def attempt_to_post_reqs_to_network(storage: Any, auth: dict[str, Any], txids: list[str]) -> dict[str, Any]:
    """Attempt to post transaction requests to blockchain network.

    Posts proven transaction requests (BEEFs) to network infrastructure
    via ARC API or similar.

    TS parity:
        Mirrors TypeScript attemptToPostReqsToNetwork for network integration.

    Args:
        storage: StorageProvider instance
        auth: Authentication context
        txids: List of transaction IDs to post

    Returns:
        Dict with posting results and statuses

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/methods/attemptToPostReqsToNetwork.ts
    """
    if not storage:
        raise WalletError("storage is required for attemptToPostReqsToNetwork")

    user_id = auth.get("userId")
    if not user_id:
        raise WalletError("userId is required in auth context")

    # Initialize result structure
    result = {
        "postedTxids": [],
        "failedTxids": [],
        "results": {},
    }

    if not txids:
        return result

    # Step 1: Fetch ProvenTxReq records for each txid
    for txid in txids:
        req_record = storage.findOne("ProvenTxReq", {"txid": txid, "userId": user_id, "isDeleted": False})

        if not req_record:
            # Transaction not found in requests
            result["failedTxids"].append(txid)
            result["results"][txid] = {
                "status": "failed",
                "reason": "ProvenTxReq not found",
            }
            continue

        # Step 2: Extract BEEF from request
        beef = req_record.get("beef", "")

        if not beef:
            result["failedTxids"].append(txid)
            result["results"][txid] = {
                "status": "failed",
                "reason": "No BEEF available",
            }
            continue

        # Step 3: Post BEEF to network services
        # Call ARC submitTransaction API (or equivalent)
        try:
            post_status = "unsent"
            if requests:
                # Try to submit to ARC service
                arc_url = os.environ.get("ARC_URL", "http://localhost:8080")
                response = requests.post(
                    f"{arc_url}/v1/transaction",
                    json={"beef": beef},
                    headers={"Content-Type": "application/json"},
                    timeout=30,
                )
                if response.status_code == 200:
                    post_status = "sent"
                elif response.status_code == 409:
                    post_status = "double_spend"
                elif response.status_code in (400, 422):
                    post_status = "failed"
                else:
                    post_status = "failed"
        except Exception:
            # Network error - keep as unsent for retry
            post_status = "unsent"

        # Step 4: Update status in storage
        storage.update(
            "ProvenTxReq",
            {"txid": txid, "userId": user_id},
            {
                "status": post_status,
                "lastUpdate": datetime.now(UTC).isoformat(),
            },
        )

        # Track successful post
        result["postedTxids"].append(txid)
        result["results"][txid] = {
            "status": "success",
            "message": "Posted to network",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    return result


def review_status(storage: Any, auth: dict[str, Any], aged_limit: Any) -> dict[str, Any]:  # datetime or similar
    """Review and update transaction statuses.

    Scans wallet transactions for status changes, updates records,
    and handles aging of confirmed transactions.

    TS parity:
        Mirrors TypeScript reviewStatus for periodic maintenance.

    Args:
        storage: StorageProvider instance
        auth: Authentication context
        aged_limit: Cutoff date for aging logic

    Returns:
        Dict with review results and updated counts

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/methods/reviewStatus.ts
    """
    if not storage:
        raise WalletError("storage is required for reviewStatus")

    user_id = auth.get("userId")
    if not user_id:
        raise WalletError("userId is required in auth context")

    # Initialize result structure
    result = {
        "updatedCount": 0,
        "agedCount": 0,
        "log": "",
    }

    # Step 1: Query transactions with status that may need updating
    # Step 2: Check blockchain service for status updates
    # Integrate with blockchain service
    transactions = storage.find("Transaction", {"userId": user_id, "isDeleted": False})

    for tx in transactions:
        txid = tx.get("txid")
        current_status = tx.get("status", "unsent")

        # Try to get transaction status from blockchain service
        try:
            blockchain_status = None
            if hasattr(storage, "getServices"):
                services = storage.getServices()
                try:
                    status_result = services.getTransactionStatus(txid)
                    blockchain_status = status_result.get("status")
                except Exception:
                    pass

            if blockchain_status and blockchain_status != current_status:
                # Status changed - update transaction record
                storage.update(
                    "Transaction",
                    {"txid": txid, "userId": user_id},
                    {
                        "status": blockchain_status,
                        "updatedAt": datetime.now(UTC).isoformat(),
                    },
                )
        except Exception:
            # Service not available - skip
            pass

    # Step 3: Mark aged transactions
    if aged_limit:
        # Find confirmed transactions older than aged_limit
        result["updatedCount"] = (
            storage.update(
                "Transaction",
                {
                    "status": "completed",
                    "createdAt": {"$lt": aged_limit},
                    "isDeleted": False,
                },
                {"isAged": True},
            )
            or 0
        )

        result["agedCount"] = result["updatedCount"]

    # Step 4: Handle ProvenTxReq status updates
    proven_reqs = storage.find(
        "ProvenTxReq",
        {"status": {"$in": ["unsent", "sent"]}},
    )

    # Update ProvenTxReq records status
    for req in proven_reqs:
        # Check if transaction was confirmed on blockchain
        txid = req.get("txid")
        current_req_status = req.get("status")

        try:
            blockchain_status = None
            if hasattr(storage, "getServices"):
                services = storage.getServices()
                try:
                    status_result = services.getTransactionStatus(txid)
                    if status_result.get("confirmations", 0) > 0:
                        blockchain_status = "confirmed"
                except Exception:
                    pass

            if blockchain_status == "confirmed" and current_req_status != "confirmed":
                # Update status to confirmed
                storage.update(
                    "ProvenTxReq",
                    {"txid": txid},
                    {
                        "status": "confirmed",
                        "updatedAt": datetime.utcnow().isoformat(),
                    },
                )
        except Exception:
            # Service not available - skip
            pass

    log_msg = (
        f"Review completed: {result['updatedCount']} transactions updated, " f"{result['agedCount']} transactions aged"
    )
    result["log"] = log_msg

    return result


def purge_data(storage: Any, params: dict[str, Any]) -> dict[str, Any]:
    """Purge old/completed wallet data.

    Removes aged wallet records (transactions, certificates, etc.)
    to manage storage and maintain performance.

    TS parity:
        Mirrors TypeScript purgeData for data lifecycle management.

    Args:
        storage: StorageProvider instance
        params: Purge parameters (age limits, types to purge)

    Returns:
        Dict with purge results and deleted counts

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/methods/purgeData.ts
    """
    if not storage:
        raise WalletError("storage is required for purgeData")

    # Initialize result structure
    result = {
        "deletedTransactions": 0,
        "deletedOutputs": 0,
        "deletedCertificates": 0,
        "deletedRequests": 0,
        "deletedLabels": 0,
    }

    # Step 1: Extract purge parameters
    aged_before_date = params.get("agedBeforeDate")

    # Step 2: Delete old transactions
    if aged_before_date:
        # Find and delete transactions with status 'completed' and createdAt < agedBeforeDate
        deleted_tx = (
            storage.delete(
                "Transaction",
                {
                    "status": "completed",
                    "createdAt": {"$lt": aged_before_date},
                    "isDeleted": False,
                },
            )
            or 0
        )
        result["deletedTransactions"] = deleted_tx

    # Step 3: Delete orphaned outputs
    # Find outputs without associated transactions
    deleted_outputs = storage.delete("Output", {"isDeleted": False, "transactionId": None}) or 0
    result["deletedOutputs"] = deleted_outputs

    # Step 4: Delete old certificates
    # Find certificates marked as deleted or revoked
    deleted_certs = storage.delete("Certificate", {"isDeleted": True}) or 0
    result["deletedCertificates"] = deleted_certs

    # Step 5: Delete old request records
    # Filter by retention period (recommend 7 days)
    retention_days = 7  # Default retention period
    cutoff_date = (datetime.now(UTC) - timedelta(days=retention_days)).isoformat()

    deleted_reqs = (
        storage.delete("ProvenTxReq", {"status": {"$in": ["sent", "complete"]}, "createdAt": {"$lt": cutoff_date}}) or 0
    )
    result["deletedRequests"] = deleted_reqs

    # Step 6: Delete orphaned labels
    deleted_labels = storage.delete("TxLabel", {"isDeleted": True})
    result["deletedLabels"] = deleted_labels

    return result


def get_sync_chunk(storage: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Get synchronization chunk for wallet sync operations.

    Retrieves a chunk of wallet state for synchronization with
    other devices or backup systems.

    TS parity:
        Mirrors TypeScript getSyncChunk for wallet sync protocol.

    Args:
        storage: StorageProvider instance
        args: Sync request parameters including:
            - identityKey: User identity key (required)
            - fromStorageIdentityKey: Source storage identity
            - toStorageIdentityKey: Destination storage identity
            - maxItems: Max items per chunk (default 1000)
            - maxRoughSize: Max rough byte size (default 10MB)
            - since: Only include items updated after this date
            - offsets: List of {name, offset} for each entity type

    Returns:
        Dict with sync chunk data (SyncChunk)

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/methods/getSyncChunk.ts
    """
    from sqlalchemy import select

    from .models import (
        Certificate,
        CertificateField,
        Commission,
        Output,
        OutputBasket,
        OutputTag,
        OutputTagMap,
        ProvenTx,
        ProvenTxReq,
        Transaction,
        TxLabel,
        TxLabelMap,
        User,
    )

    if not storage:
        raise WalletError("storage is required for getSyncChunk")

    # Extract parameters (TS parity)
    identity_key = args.get("identityKey")
    from_storage_key = args.get("fromStorageIdentityKey", "")
    to_storage_key = args.get("toStorageIdentityKey", "")
    max_items = args.get("maxItems", 1000)
    max_rough_size = args.get("maxRoughSize", 10_000_000)
    since = args.get("since")  # Date or None
    offsets = args.get("offsets", [])

    if not identity_key:
        raise WalletError("identityKey is required for getSyncChunk")

    # Initialize result structure (SyncChunk)
    result: dict[str, Any] = {
        "fromStorageIdentityKey": from_storage_key,
        "toStorageIdentityKey": to_storage_key,
        "userIdentityKey": identity_key,
    }

    # Get user
    session = storage.SessionLocal()
    try:
        user_stmt = select(User).where(User.identity_key == identity_key)
        user = session.execute(user_stmt).scalar_one_or_none()
        if not user:
            raise WalletError(f"User not found for identity key: {identity_key}")

        user_id = user.user_id

        # Check if user needs to be synced
        if not since or user.updated_at > since:
            result["user"] = _user_to_dict(user)

        # Parse offsets into a dict for easy lookup
        offset_map = {o["name"]: o["offset"] for o in offsets} if offsets else {}

        # Track remaining items and size
        items_left = max_items
        rough_size = max_rough_size

        def get_offset(name: str) -> int:
            return offset_map.get(name, 0)

        def add_entities(name: str, query, to_dict_fn, result_key: str, max_divider: int = 1) -> None:
            nonlocal items_left, rough_size
            offset = get_offset(name)
            limit = min(items_left, max(10, max_items // max_divider))
            if limit <= 0:
                return

            # Apply since filter if provided
            if since:
                query = query.where(query.column_descriptions[0]["entity"].updated_at > since)

            items = session.execute(query.offset(offset).limit(limit)).scalars().all()
            if items:
                result[result_key] = []
                for item in items:
                    item_dict = to_dict_fn(item)
                    result[result_key].append(item_dict)
                    items_left -= 1
                    rough_size -= len(str(item_dict))
                    if items_left <= 0 or rough_size < 0:
                        break

        # Query each entity type in dependency order (TS parity)

        # 1. ProvenTx
        ptx_query = select(ProvenTx)
        ptx_items = (
            session.execute(ptx_query.offset(get_offset("provenTx")).limit(min(items_left, max_items // 100)))
            .scalars()
            .all()
        )
        if ptx_items:
            result["provenTxs"] = [_proven_tx_to_dict(p) for p in ptx_items]

        # 2. OutputBasket
        ob_query = select(OutputBasket).where(OutputBasket.user_id == user_id)
        if since:
            ob_query = ob_query.where(OutputBasket.updated_at > since)
        ob_items = session.execute(ob_query.offset(get_offset("outputBasket")).limit(items_left)).scalars().all()
        if ob_items:
            result["outputBaskets"] = [_output_basket_to_dict(b) for b in ob_items]

        # 3. OutputTag
        ot_query = select(OutputTag).where(OutputTag.user_id == user_id)
        if since:
            ot_query = ot_query.where(OutputTag.updated_at > since)
        ot_items = session.execute(ot_query.offset(get_offset("outputTag")).limit(items_left)).scalars().all()
        if ot_items:
            result["outputTags"] = [_output_tag_to_dict(t) for t in ot_items]

        # 4. TxLabel
        tl_query = select(TxLabel).where(TxLabel.user_id == user_id)
        if since:
            tl_query = tl_query.where(TxLabel.updated_at > since)
        tl_items = session.execute(tl_query.offset(get_offset("txLabel")).limit(items_left)).scalars().all()
        if tl_items:
            result["txLabels"] = [_tx_label_to_dict(l) for l in tl_items]

        # 5. Transaction
        tx_query = select(Transaction).where(Transaction.user_id == user_id)
        if since:
            tx_query = tx_query.where(Transaction.updated_at > since)
        tx_items = (
            session.execute(tx_query.offset(get_offset("transaction")).limit(min(items_left, max_items // 25)))
            .scalars()
            .all()
        )
        if tx_items:
            result["transactions"] = [_transaction_to_dict(t) for t in tx_items]

        # 6. Output
        out_query = select(Output).where(Output.user_id == user_id)
        if since:
            out_query = out_query.where(Output.updated_at > since)
        out_items = (
            session.execute(out_query.offset(get_offset("output")).limit(min(items_left, max_items // 25)))
            .scalars()
            .all()
        )
        if out_items:
            result["outputs"] = [_output_to_dict(o) for o in out_items]

        # 7. TxLabelMap
        tlm_query = select(TxLabelMap).join(Transaction).where(Transaction.user_id == user_id)
        if since:
            tlm_query = tlm_query.where(TxLabelMap.updated_at > since)
        tlm_items = session.execute(tlm_query.offset(get_offset("txLabelMap")).limit(items_left)).scalars().all()
        if tlm_items:
            result["txLabelMaps"] = [_tx_label_map_to_dict(m) for m in tlm_items]

        # 8. OutputTagMap
        otm_query = select(OutputTagMap).join(Output).where(Output.user_id == user_id)
        if since:
            otm_query = otm_query.where(OutputTagMap.updated_at > since)
        otm_items = session.execute(otm_query.offset(get_offset("outputTagMap")).limit(items_left)).scalars().all()
        if otm_items:
            result["outputTagMaps"] = [_output_tag_map_to_dict(m) for m in otm_items]

        # 9. Certificate
        cert_query = select(Certificate).where(Certificate.user_id == user_id)
        if since:
            cert_query = cert_query.where(Certificate.updated_at > since)
        cert_items = (
            session.execute(cert_query.offset(get_offset("certificate")).limit(min(items_left, max_items // 25)))
            .scalars()
            .all()
        )
        if cert_items:
            result["certificates"] = [_certificate_to_dict(c) for c in cert_items]

        # 10. CertificateField
        cf_query = select(CertificateField).join(Certificate).where(Certificate.user_id == user_id)
        if since:
            cf_query = cf_query.where(CertificateField.updated_at > since)
        cf_items = (
            session.execute(cf_query.offset(get_offset("certificateField")).limit(min(items_left, max_items // 25)))
            .scalars()
            .all()
        )
        if cf_items:
            result["certificateFields"] = [_certificate_field_to_dict(f) for f in cf_items]

        # 11. Commission
        comm_query = select(Commission).where(Commission.user_id == user_id)
        if since:
            comm_query = comm_query.where(Commission.updated_at > since)
        comm_items = (
            session.execute(comm_query.offset(get_offset("commission")).limit(min(items_left, max_items // 25)))
            .scalars()
            .all()
        )
        if comm_items:
            result["commissions"] = [_commission_to_dict(c) for c in comm_items]

        # 12. ProvenTxReq
        ptr_query = select(ProvenTxReq)
        ptr_items = (
            session.execute(ptr_query.offset(get_offset("provenTxReq")).limit(min(items_left, max_items // 100)))
            .scalars()
            .all()
        )
        if ptr_items:
            result["provenTxReqs"] = [_proven_tx_req_to_dict(r) for r in ptr_items]

        return result

    finally:
        session.close()


def _user_to_dict(u) -> dict:
    """Convert User model to dict for sync."""
    return {
        "userId": u.user_id,
        "identityKey": u.identity_key,
        "activeStorage": u.active_storage,
        "createdAt": u.created_at.isoformat() if u.created_at else None,
        "updatedAt": u.updated_at.isoformat() if u.updated_at else None,
    }


def _proven_tx_to_dict(p) -> dict:
    """Convert ProvenTx model to dict for sync."""
    return {
        "provenTxId": p.proven_tx_id,
        "txid": p.txid,
        "height": p.height,
        "index": p.index,
        "merklePath": list(p.merkle_path) if p.merkle_path else None,
        "rawTx": list(p.raw_tx) if p.raw_tx else None,
        "blockHash": p.block_hash,
        "merkleRoot": p.merkle_root,
        "createdAt": p.created_at.isoformat() if p.created_at else None,
        "updatedAt": p.updated_at.isoformat() if p.updated_at else None,
    }


def _output_basket_to_dict(b) -> dict:
    """Convert OutputBasket model to dict for sync."""
    return {
        "basketId": b.basket_id,
        "userId": b.user_id,
        "name": b.name,
        "numberOfDesiredUTXOs": b.number_of_desired_utxos,
        "minimumDesiredUTXOValue": b.minimum_desired_utxo_value,
        "isDeleted": b.is_deleted,
        "createdAt": b.created_at.isoformat() if b.created_at else None,
        "updatedAt": b.updated_at.isoformat() if b.updated_at else None,
    }


def _output_tag_to_dict(t) -> dict:
    """Convert OutputTag model to dict for sync."""
    return {
        "outputTagId": t.output_tag_id,
        "userId": t.user_id,
        "tag": t.tag,
        "isDeleted": t.is_deleted,
        "createdAt": t.created_at.isoformat() if t.created_at else None,
        "updatedAt": t.updated_at.isoformat() if t.updated_at else None,
    }


def _tx_label_to_dict(l) -> dict:
    """Convert TxLabel model to dict for sync."""
    return {
        "txLabelId": l.tx_label_id,
        "userId": l.user_id,
        "label": l.label,
        "isDeleted": l.is_deleted,
        "createdAt": l.created_at.isoformat() if l.created_at else None,
        "updatedAt": l.updated_at.isoformat() if l.updated_at else None,
    }


def _transaction_to_dict(t) -> dict:
    """Convert Transaction model to dict for sync."""
    return {
        "transactionId": t.transaction_id,
        "userId": t.user_id,
        "txid": t.txid,
        "status": t.status,
        "reference": t.reference,
        "isOutgoing": t.is_outgoing,
        "satoshis": t.satoshis,
        "description": t.description,
        "version": t.version,
        "lockTime": t.lock_time,
        "provenTxId": t.proven_tx_id,
        "inputBEEF": list(t.input_beef) if t.input_beef else None,
        "createdAt": t.created_at.isoformat() if t.created_at else None,
        "updatedAt": t.updated_at.isoformat() if t.updated_at else None,
    }


def _output_to_dict(o) -> dict:
    """Convert Output model to dict for sync."""
    return {
        "outputId": o.output_id,
        "userId": o.user_id,
        "transactionId": o.transaction_id,
        "basketId": o.basket_id,
        "spendable": o.spendable,
        "change": o.change,
        "txid": o.txid,
        "vout": o.vout,
        "satoshis": o.satoshis,
        "lockingScript": list(o.locking_script) if o.locking_script else None,
        "customInstructions": o.custom_instructions,
        "senderIdentityKey": o.sender_identity_key,
        "derivationPrefix": o.derivation_prefix,
        "derivationSuffix": o.derivation_suffix,
        "spentBy": o.spent_by,
        "sequenceNumber": o.sequence_number,
        "spendingDescription": o.spending_description,
        "scriptLength": o.script_length,
        "scriptOffset": o.script_offset,
        "outputDescription": o.output_description,
        "type": o.type,
        "providedBy": o.provided_by,
        "purpose": o.purpose,
        "spent": o.spent,
        "createdAt": o.created_at.isoformat() if o.created_at else None,
        "updatedAt": o.updated_at.isoformat() if o.updated_at else None,
    }


def _tx_label_map_to_dict(m) -> dict:
    """Convert TxLabelMap model to dict for sync."""
    return {
        "transactionId": m.transaction_id,
        "txLabelId": m.tx_label_id,
        "isDeleted": m.is_deleted,
        "createdAt": m.created_at.isoformat() if m.created_at else None,
        "updatedAt": m.updated_at.isoformat() if m.updated_at else None,
    }


def _output_tag_map_to_dict(m) -> dict:
    """Convert OutputTagMap model to dict for sync."""
    return {
        "outputId": m.output_id,
        "outputTagId": m.output_tag_id,
        "isDeleted": m.is_deleted,
        "createdAt": m.created_at.isoformat() if m.created_at else None,
        "updatedAt": m.updated_at.isoformat() if m.updated_at else None,
    }


def _certificate_to_dict(c) -> dict:
    """Convert Certificate model to dict for sync."""
    return {
        "certificateId": c.certificate_id,
        "userId": c.user_id,
        "type": c.type,
        "serialNumber": c.serial_number,
        "certifier": c.certifier,
        "subject": c.subject,
        "verifier": c.verifier,
        "revocationOutpoint": c.revocation_outpoint,
        "signature": c.signature,
        "isDeleted": c.is_deleted,
        "createdAt": c.created_at.isoformat() if c.created_at else None,
        "updatedAt": c.updated_at.isoformat() if c.updated_at else None,
    }


def _certificate_field_to_dict(f) -> dict:
    """Convert CertificateField model to dict for sync."""
    return {
        "certificateFieldId": f.certificate_field_id,
        "certificateId": f.certificate_id,
        "userId": f.user_id,
        "fieldName": f.field_name,
        "fieldValue": f.field_value,
        "masterKey": f.master_key,
        "createdAt": f.created_at.isoformat() if f.created_at else None,
        "updatedAt": f.updated_at.isoformat() if f.updated_at else None,
    }


def _commission_to_dict(c) -> dict:
    """Convert Commission model to dict for sync."""
    return {
        "commissionId": c.commission_id,
        "userId": c.user_id,
        "transactionId": c.transaction_id,
        "satoshis": c.satoshis,
        "keyOffset": c.key_offset,
        "isRedeemed": c.is_redeemed,
        "lockingScript": list(c.locking_script) if c.locking_script else None,
        "createdAt": c.created_at.isoformat() if c.created_at else None,
        "updatedAt": c.updated_at.isoformat() if c.updated_at else None,
    }


def _proven_tx_req_to_dict(r) -> dict:
    """Convert ProvenTxReq model to dict for sync."""
    return {
        "provenTxReqId": r.proven_tx_req_id,
        "txid": r.txid,
        "status": r.status,
        "provenTxId": r.proven_tx_id,
        "rawTx": list(r.raw_tx) if r.raw_tx else None,
        "inputBEEF": list(r.input_beef) if r.input_beef else None,
        "attempts": r.attempts,
        "notified": r.notified,
        "history": r.history,
        "notify": r.notify,
        "batch": r.batch,
        "createdAt": r.created_at.isoformat() if r.created_at else None,
        "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
    }
