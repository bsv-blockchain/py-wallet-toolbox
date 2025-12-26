"""Aggregate action processing results.

Consolidate transaction send results with network posting results into unified output.

Reference: toolbox/ts-wallet-toolbox/src/utility/aggregateResults.ts
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict

from bsv.transaction.beef import Beef

if TYPE_CHECKING:
    from bsv_wallet_toolbox.storage import StorageProvider


class PostReqDetail(TypedDict, total=False):
    """Network posting detail for a transaction."""

    txid: str
    status: str
    competing_txs: list[str] | None


class AggregateActionResults(TypedDict):
    """Aggregated action results with unified status."""

    swr: list[dict[str, str]]
    rar: list[dict[str, Any]]


async def aggregate_action_results(
    storage: StorageProvider | None,  # type: ignore
    send_with_result_reqs: list[dict[str, Any]],
    post_to_network_result: dict[str, Any],
) -> AggregateActionResults:
    """Aggregate transaction results from sending and network posting.

    Combines SendWithResult[] and PostReqsToNetworkResult into unified output.

    Args:
        storage: StorageProvider for BEEF merging (optional)
        send_with_result_reqs: List of SendWithResult objects
        post_to_network_result: PostReqsToNetworkResult with posting details

    Returns:
        Dictionary with 'swr' (SendWithResult) and 'rar' (ReviewActionResult) lists

    Reference: toolbox/ts-wallet-toolbox/src/utility/aggregateResults.ts:6-56
    """
    swr: list[dict[str, str]] = []
    rar: list[dict[str, Any]] = []

    for ar in send_with_result_reqs:
        txid = ar.get("txid", "")

        # Find corresponding posting detail
        details = post_to_network_result.get("details", [])
        detail = None
        for d in details:
            if d.get("txid") == txid:
                detail = d
                break

        if not detail:
            raise RuntimeError(f"missing details for {txid}")

        ar_ndr: dict[str, Any] = {
            "txid": detail.get("txid"),
            "status": "success",
            "competingTxs": detail.get("competingTxs"),
        }

        status = detail.get("status")

        if status == "success":
            # Network has accepted this transaction
            ar["status"] = "unproven"
        elif status == "doubleSpend":
            # Confirmed double spend
            ar["status"] = "failed"
            ar_ndr["status"] = "doubleSpend"
            if detail.get("competingTxs") and storage:
                # Merge competing transactions into BEEF
                competing_txs = detail.get("competingTxs", [])
                if competing_txs:
                    try:
                        beef = Beef()
                        for competing_txid in competing_txs:
                            # Find and merge competing transaction
                            competing_tx = storage.find_transaction(competing_txid)
                            if competing_tx:
                                tx_data = competing_tx.get("rawtx") or competing_tx.get("rawTx")
                                if tx_data:
                                    beef.merge_raw_tx(bytes.fromhex(tx_data) if isinstance(tx_data, str) else tx_data)
                        ar_ndr["competingBeef"] = beef.to_binary()
                    except Exception:
                        # Skip BEEF merging if unsuccessful
                        pass
        elif status == "serviceError":
            # Services might improve
            ar["status"] = "sending"
            ar_ndr["status"] = "serviceError"
        elif status == "invalidTx":
            # Nothing will fix this transaction
            ar["status"] = "failed"
            ar_ndr["status"] = "invalidTx"
        elif status in ("unknown", "invalid"):
            raise RuntimeError(f"processAction with notDelayed status {status} should not occur.")
        else:
            raise RuntimeError(f"Unknown status {status} for transaction {txid}")

        swr.append({"txid": txid, "status": ar.get("status", "")})
        rar.append(ar_ndr)

    return {"swr": swr, "rar": rar}


def aggregate_results(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Aggregate a list of results into a summary.

    Simple utility function to combine multiple result dictionaries.

    Args:
        results: List of result dictionaries to aggregate

    Returns:
        Aggregated result dictionary or None if no results

    Example:
        >>> results = [{"value": 100, "status": "success"}]
        >>> aggregate_results(results)  # {"count": 1, "total_value": 100, "statuses": ["success"]}
    """
    if not results:
        return None

    aggregated = {
        "count": len(results),
        "statuses": [r.get("status") for r in results if "status" in r],
        "values": [r.get("value") for r in results if "value" in r],
    }

    # Add summary statistics
    if aggregated["values"]:
        aggregated["totalValue"] = sum(aggregated["values"])
        aggregated["avgValue"] = aggregated["totalValue"] / len(aggregated["values"])

    return aggregated


def combine_results(*results: dict[str, Any]) -> dict[str, Any]:
    """Combine multiple result dictionaries into a single result.

    Args:
        *results: Variable number of result dicts to combine

    Returns:
        Combined result dictionary

    Example:
        >>> combine_results({"a": 1}, {"b": 2})  # {"a": 1, "b": 2}
    """
    combined = {}
    for result in results:
        if isinstance(result, dict):
            combined.update(result)
    return combined


def merge_result_arrays(arrays: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Merge multiple arrays of results into a single array.

    Args:
        arrays: List of result arrays to merge

    Returns:
        Single merged array of results

    Example:
        >>> merge_result_arrays([[{"a": 1}], [{"b": 2}]])  # [{"a": 1}, {"b": 2}]
    """
    merged = []
    for array in arrays:
        merged.extend(array)
    return merged
