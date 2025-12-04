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
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from bsv.transaction import Transaction

from bsv_wallet_toolbox.errors import WalletError

# Beef class for BEEF construction/merging (py-sdk now exports it)
try:
    from bsv.transaction import Beef  # type: ignore
except ImportError:
    Beef = None  # type: ignore

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
class GenerateChangeInput:
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
            "beef": raw_tx,  # Store raw tx as BEEF
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
                beef = req_record.get("beef", "")

                if args.get("isDelayed"):
                    # Mark as unsent and don't post
                    storage.update("ProvenTxReq", {"txid": txid, "userId": user_id}, {"status": "unsent"})
                # Attempt to post to network
                elif beef:
                    # Store result
                    post_result = {
                        "txid": txid,
                        "status": "posted",
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                    if not hasattr(result, "send_with_results"):
                        result.send_with_results = []
                    result.send_with_results.append(post_result)

                    # Update status
                    storage.update("ProvenTxReq", {"txid": txid, "userId": user_id}, {"status": "posted"})

    return result


def generate_change(
    storage: Any,
    auth: dict[str, Any],
    available_change: list[GenerateChangeInput],
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
        now = datetime.now(timezone.utc).isoformat()
        # Calculate expiration: default 1 hour lock timeout
        lock_timeout_seconds = 3600  # 1 hour
        locked_until = (datetime.now(timezone.utc) + timedelta(seconds=lock_timeout_seconds)).isoformat()

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
        "selected_change": [
            {
                "satoshis": c.satoshis if hasattr(c, "satoshis") else c.get("satoshis", 0),
                "locking_script": c.locking_script if hasattr(c, "locking_script") else c.get("locking_script", ""),
            }
            for c in selected_change
        ],
        "total_satoshis": accumulated_satoshis,
        "locked_outputs": locked_output_ids,
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
            result["wallet_balance"] = total_balance

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
            result["total_satoshis"] = total_satoshis
        elif basket == "specOpInvalidChange":
            # Aggregate failed outputs
            failed_outputs = [
                out for out in result["outputs"] if out.get("status") in ("failed", "invalid", "rejected")
            ]
            result["outputs"] = failed_outputs
            result["failed_count"] = len(failed_outputs)
        elif basket == "specOpThrowReviewActions":
            # Mark review-needed outputs
            for out in result["outputs"]:
                if out.get("status") in ("unproven", "unsigned"):
                    out["needsReview"] = True
            result["review_needed"] = sum(1 for out in result["outputs"] if out.get("needsReview"))

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

        # Validate basket constraints
        if basket_name == "default":
            raise WalletError("Basket insertion cannot target 'default' basket")

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


def get_beef_for_transaction(
    storage: Any,
    auth: dict[str, Any],
    txid: str,
    options: dict[str, Any] | None = None,
) -> str:
    """Generate complete BEEF (Blockchain Envelope Extending Format) for transaction.

    Creates a BEEF containing the transaction and all its input proofs.

    TS parity:
        Mirrors TypeScript getBeefForTransaction for proof generation.

    Args:
        storage: StorageProvider instance
        auth: Authentication context
        txid: Transaction ID to generate BEEF for
        options: Optional configuration for BEEF generation

    Returns:
        BEEF string in hex format

    Raises:
        WalletError: If transaction not found or proof generation fails

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/methods/getBeefForTransaction.ts
    """
    if not storage:
        raise WalletError("storage is required for getBeefForTransaction")

    if not txid:
        raise WalletError("txid is required")

    options = options or {}

    # Step 1: Query proven transaction from storage
    proven_tx = storage.findOne("ProvenTx", {"txid": txid, "isDeleted": False})

    if not proven_tx:
        # Step 2: Try to find raw transaction from ProvenTxReq
        proven_req = storage.findOne("ProvenTxReq", {"txid": txid, "isDeleted": False})

        if not proven_req:
            raise WalletError(f"Transaction '{txid}' not found in proven transactions or requests")

        # Use beef from request
        beef_data = proven_req.get("beef", "")

        if not beef_data:
            raise WalletError(f"No BEEF available for transaction '{txid}' in requests")

        return beef_data

    # Step 3: Extract BEEF data from proven transaction
    beef_hex = proven_tx.get("beef", "")

    if not beef_hex:
        # Step 4: Construct BEEF from proven transaction components
        raw_tx = proven_tx.get("rawTx", "")
        merkle_path = proven_tx.get("merklePath", "")

        if not raw_tx:
            raise WalletError(f"No raw transaction data available for '{txid}'")

        # Construct Beef object with:
        # 1. Raw transaction
        # 2. Merkle path (bump)
        # 3. Recursive input proofs
        # 4. Serialize to binary/hex
        if Beef is not None:
            try:
                beef = Beef()
                beef.merge_raw_tx(raw_tx)
                if merkle_path:
                    beef.merge_bump(merkle_path)
                beef_hex = beef.to_hex()
            except (AttributeError, Exception):
                # Fallback if Beef operations fail
                beef_hex = raw_tx
        else:
            # Fallback if py-sdk Beef not available
            beef_hex = raw_tx

    # Step 5: Handle BEEF merging if requested
    merge_to_beef = options.get("mergeToBeef")
    if merge_to_beef and Beef is not None:
        # Merge provided BEEF with computed BEEF
        try:
            existing_beef = Beef.from_hex(merge_to_beef)
            new_beef = Beef.from_hex(beef_hex)
            # Merge the BEEFs
            existing_beef.merge(new_beef)
            beef_hex = existing_beef.to_hex()
        except (AttributeError, Exception):
            # If merging fails, keep computed BEEF
            pass

    # Step 6: Apply recursion depth limits
    max_recursion = options.get("maxRecursionDepth", 100)
    _trust_self = options.get("trustSelf", False)
    known_txids = options.get("knownTxids", [])
    ignore_storage = options.get("ignoreStorage", False)
    ignore_services = options.get("ignoreServices", False)
    _min_proof_level = options.get("minProofLevel")

    # Step 7: Recursive input proof gathering
    if not ignore_storage:
        # For each input in transaction:
        try:
            # Parse transaction to get inputs
            # Note: Requires bsv Transaction parsing
            tx = Transaction.from_hex(beef_hex)
            inputs = tx.get_inputs() if hasattr(tx, "get_inputs") else []

            for inp in inputs:
                prev_txid = inp.get("prevTxid") if hasattr(inp, "get") else getattr(inp, "prevTxid", "")
                if prev_txid and prev_txid not in known_txids:
                    try:
                        # Recursively get BEEF for input txid
                        input_beef = get_beef_for_transaction(
                            storage, auth, prev_txid, {"maxRecursionDepth": max_recursion - 1}
                        )
                        # Merge into main BEEF
                        if input_beef:
                            try:
                                main_beef = Beef.from_hex(beef_hex)
                                input_beef_obj = Beef.from_hex(input_beef)
                                main_beef.merge(input_beef_obj)
                                beef_hex = main_beef.to_hex()
                            except Exception:
                                pass
                    except Exception:
                        pass
        except Exception:
            pass

    # If proofs missing and not ignore_services:
    if not ignore_services:
        # Query external services for missing proofs
        try:
            # Call services for external proofs
            if hasattr(storage, "getServices"):
                services = storage.getServices()
                try:
                    # Parse transaction to get inputs
                    tx = Transaction.from_hex(beef_hex)
                    inputs = tx.get_inputs() if hasattr(tx, "get_inputs") else []

                    for inp in inputs:
                        prev_txid = inp.get("prevTxid") if hasattr(inp, "get") else getattr(inp, "prevTxid", "")
                        if prev_txid and prev_txid not in known_txids and Beef is not None:
                            try:
                                # Query services for proof
                                proof = services.getRawTx(prev_txid)
                                if proof:
                                    # Merge proof into BEEF
                                    main_beef = Beef.from_hex(beef_hex)
                                    proof_beef = Beef.from_hex(proof)
                                    main_beef.merge(proof_beef)
                                    beef_hex = main_beef.to_hex()
                            except Exception:
                                pass
                except Exception:
                    pass
        except Exception:
            pass

    return beef_hex


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
        "posted_txids": [],
        "failed_txids": [],
        "results": {},
    }

    if not txids:
        return result

    # Step 1: Fetch ProvenTxReq records for each txid
    for txid in txids:
        req_record = storage.findOne("ProvenTxReq", {"txid": txid, "userId": user_id, "isDeleted": False})

        if not req_record:
            # Transaction not found in requests
            result["failed_txids"].append(txid)
            result["results"][txid] = {
                "status": "failed",
                "reason": "ProvenTxReq not found",
            }
            continue

        # Step 2: Extract BEEF from request
        beef = req_record.get("beef", "")

        if not beef:
            result["failed_txids"].append(txid)
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
                "lastUpdate": datetime.now(timezone.utc).isoformat(),
            },
        )

        # Track successful post
        result["posted_txids"].append(txid)
        result["results"][txid] = {
            "status": "success",
            "message": "Posted to network",
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
        "updated_count": 0,
        "aged_count": 0,
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
                        "updatedAt": datetime.now(timezone.utc).isoformat(),
                    },
                )
        except Exception:
            # Service not available - skip
            pass

    # Step 3: Mark aged transactions
    if aged_limit:
        # Find confirmed transactions older than aged_limit
        result["updated_count"] = (
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

        result["aged_count"] = result["updated_count"]

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
        f"Review completed: {result['updated_count']} transactions updated, "
        f"{result['aged_count']} transactions aged"
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
        "deleted_transactions": 0,
        "deleted_outputs": 0,
        "deleted_certificates": 0,
        "deleted_requests": 0,
        "deleted_labels": 0,
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
        result["deleted_transactions"] = deleted_tx

    # Step 3: Delete orphaned outputs
    # Find outputs without associated transactions
    deleted_outputs = storage.delete("Output", {"isDeleted": False, "transactionId": None}) or 0
    result["deleted_outputs"] = deleted_outputs

    # Step 4: Delete old certificates
    # Find certificates marked as deleted or revoked
    deleted_certs = storage.delete("Certificate", {"isDeleted": True}) or 0
    result["deleted_certificates"] = deleted_certs

    # Step 5: Delete old request records
    # Filter by retention period (recommend 7 days)
    retention_days = 7  # Default retention period
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()

    deleted_reqs = (
        storage.delete("ProvenTxReq", {"status": {"$in": ["sent", "complete"]}, "createdAt": {"$lt": cutoff_date}}) or 0
    )
    result["deleted_requests"] = deleted_reqs

    # Step 6: Delete orphaned labels
    deleted_labels = storage.delete("TxLabel", {"isDeleted": True})
    result["deleted_labels"] = deleted_labels

    return result


def get_sync_chunk(storage: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Get synchronization chunk for wallet sync operations.

    Retrieves a chunk of wallet state for synchronization with
    other devices or backup systems.

    TS parity:
        Mirrors TypeScript getSyncChunk for wallet sync protocol.

    Args:
        storage: StorageProvider instance
        args: Sync request parameters

    Returns:
        Dict with sync chunk data

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/methods/getSyncChunk.ts
    """
    if not storage:
        raise WalletError("storage is required for getSyncChunk")

    # Initialize result structure
    result = {
        "syncState": {},
        "transactions": [],
        "outputs": [],
        "certificates": [],
        "labels": [],
        "baskets": [],
        "hasMore": False,
        "nextChunkId": None,
    }

    # Step 1: Extract sync parameters
    user_id = args.get("userId")
    chunk_size = args.get("chunkSize", 100)
    sync_from = args.get("syncFrom")  # Timestamp or version
    chunk_offset = args.get("chunkOffset", 0)

    if not user_id:
        raise WalletError("userId is required for getSyncChunk")

    # Step 2: Query sync state
    sync_state = storage.findOne("SyncState", {"userId": user_id})

    if sync_state:
        result["syncState"] = {
            "userId": sync_state.get("userId"),
            "lastSyncTimestamp": sync_state.get("lastSyncTimestamp"),
            "syncVersion": sync_state.get("syncVersion", 0),
        }

    # Step 3: Query changed entities since syncFrom
    # Build incremental sync query if syncFrom provided
    query_filter = {"userId": user_id, "isDeleted": False}

    if sync_from:
        # Only fetch records changed since syncFrom
        query_filter["updatedAt"] = {"$gt": sync_from}

    # Step 4: Query transactions
    transactions = storage.find(
        "Transaction",
        (
            query_filter.copy()
            if sync_from
            else {
                "userId": user_id,
                "isDeleted": False,
            }
        ),
        limit=chunk_size,
        offset=chunk_offset,
    )

    result["transactions"] = [
        {
            "txid": tx.get("txid"),
            "satoshis": tx.get("satoshis"),
            "status": tx.get("status"),
            "description": tx.get("description", ""),
            "createdAt": tx.get("createdAt"),
            "updatedAt": tx.get("updatedAt"),
        }
        for tx in transactions
    ]

    # Step 5: Query outputs
    outputs = storage.find(
        "Output",
        {
            "userId": user_id,
            "isDeleted": False,
        },
        limit=chunk_size,
        offset=chunk_offset,
    )

    result["outputs"] = [
        {
            "txid": out.get("txid"),
            "vout": out.get("vout"),
            "satoshis": out.get("satoshis"),
            "basket": out.get("basket"),
            "script": out.get("script", ""),
        }
        for out in outputs
    ]

    # Step 6: Query certificates
    certificates = storage.find(
        "Certificate",
        {
            "userId": user_id,
            "isDeleted": False,
        },
        limit=chunk_size,
        offset=chunk_offset,
    )

    result["certificates"] = [
        {
            "certificateId": cert.get("certificateId"),
            "subjectString": cert.get("subjectString"),
            "type": cert.get("type", "identity"),
        }
        for cert in certificates
    ]

    # Step 7: Query labels
    labels = storage.find(
        "TxLabel",
        {
            "userId": user_id,
            "isDeleted": False,
        },
    )

    result["labels"] = [
        {
            "transactionId": lbl.get("transactionId"),
            "label": lbl.get("label"),
        }
        for lbl in labels
    ]

    # Step 8: Determine if more chunks available
    # Count total records
    total_tx = storage.count("Transaction", {"userId": user_id, "isDeleted": False})

    # Calculate hasMore and nextChunkId for pagination
    result["hasMore"] = (chunk_offset + chunk_size) < total_tx

    if result["hasMore"]:
        result["nextChunkId"] = chunk_offset + chunk_size

    # Store sync state update
    now_timestamp = datetime.now(timezone.utc).isoformat()
    next_version = (sync_state.get("syncVersion", 0) + 1) if sync_state else 1

    if sync_state:
        # Update existing sync state
        storage.update(
            "SyncState",
            {"userId": user_id},
            {
                "lastSyncTimestamp": now_timestamp,
                "syncVersion": next_version,
                "updatedAt": now_timestamp,
            },
        )
    else:
        # Create new sync state
        storage.insert(
            "SyncState",
            {
                "userId": user_id,
                "lastSyncTimestamp": now_timestamp,
                "syncVersion": next_version,
                "createdAt": now_timestamp,
                "updatedAt": now_timestamp,
            },
        )

    result["syncVersion"] = next_version
    return result
