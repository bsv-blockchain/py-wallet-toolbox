"""Aggregate action processing results.

Consolidate transaction send results with network posting results into unified output.

Reference: toolbox/ts-wallet-toolbox/src/utility/aggregateResults.ts
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict

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
                # TODO: Implement BEEF merging for competing transactions
                # ar_ndr["competingBeef"] = await create_merged_beef_of_txids(
                #     detail.get("competingTxs"), storage
                # )
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
