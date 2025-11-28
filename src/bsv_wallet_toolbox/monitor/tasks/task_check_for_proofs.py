"""TaskCheckForProofs implementation."""

from typing import TYPE_CHECKING, Any, cast

from bsv.merkle_path import MerklePath

from ..wallet_monitor_task import WalletMonitorTask

if TYPE_CHECKING:
    from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..monitor import Monitor


class TaskCheckForProofs(WalletMonitorTask):
    """Task to check for transaction proofs (BUMP).

    Retrieves merkle proofs for transactions that are in unconfirmed states.
    If a valid proof is found, updates the transaction status to 'proven'.

    Reference: ts-wallet-toolbox/src/monitor/tasks/TaskCheckForProofs.ts
    """

    check_now: bool = False
    trigger_msecs: int

    def __init__(self, monitor: "Monitor", trigger_msecs: int = 0) -> None:
        """Initialize TaskCheckForProofs.

        Args:
            monitor: "Monitor" instance.
            trigger_msecs: Periodic trigger interval in milliseconds.
        """
        super().__init__(monitor, "CheckForProofs")
        self.trigger_msecs = trigger_msecs

    def trigger(self, now: int) -> dict[str, bool]:
        """Trigger based on check_now flag or time interval."""
        should_run = self.check_now or (
            self.trigger_msecs > 0 and now - self.last_run_msecs_since_epoch > self.trigger_msecs
        )
        return {"run": should_run}

    def run_task(self) -> str:
        """Process unproven requests."""
        self.check_now = False
        log_lines: list[str] = []

        # Get current chain tip height to avoid reorg-prone blocks
        try:
            chain_tip = self.monitor.services.find_chain_tip_header()
            max_acceptable_height = chain_tip.get("height")
        except Exception as e:
            return f"Failed to get chain tip header: {e!s}"

        if max_acceptable_height is None:
            return "Chain tip height unavailable"

        limit = 100
        offset = 0
        total_processed = 0

        while True:
            # Find requests with relevant statuses
            statuses = ["callback", "unmined", "sending", "unknown", "unconfirmed"]
            # Note: Provider's find_proven_tx_reqs implementation supports list for IN clause
            # pass limit/offset via query if supported, otherwise we get all.
            # Since we can't rely on limit/offset support in current provider,
            # we fetch all and paginate in memory if needed, or just process all.
            # Ideally provider supports pagination.
            reqs = self.monitor.storage.find_proven_tx_reqs({"status": statuses})

            if not reqs:
                break

            # Manual pagination since find_proven_tx_reqs ignores limit/offset in current provider
            current_batch = reqs[offset : offset + limit]
            if not current_batch:
                break

            log_lines.append(f"Processing {len(current_batch)} reqs (offset {offset})...")

            for req in current_batch:
                self._process_req(req, max_acceptable_height, log_lines)
                total_processed += 1

            if len(current_batch) < limit:
                break
            offset += limit

        return "\n".join(log_lines) if log_lines else ""

    def _process_req(self, req: dict[str, Any], max_acceptable_height: int, log_lines: list[str]) -> None:
        txid = req.get("txid")
        proven_tx_req_id = req.get("proven_tx_req_id")

        if not txid or not proven_tx_req_id:
            return

        attempts = req.get("attempts", 0)
        # TODO: Check attempts limit (TS: unprovenAttemptsLimitMain/Test)

        try:
            # 1. Get Merkle Path from Services
            res = self.monitor.services.get_merkle_path_for_transaction(txid)
        except Exception as e:
            log_lines.append(f"Error getting proof for {txid}: {e!s}")
            self._increment_attempts(proven_tx_req_id, attempts)
            return

        merkle_path_data = res.get("merklePath")
        header = res.get("header")

        if not merkle_path_data or not header:
            # Proof not ready yet
            self._increment_attempts(proven_tx_req_id, attempts)
            return

        height = header.get("height")
        if height is not None and height > max_acceptable_height:
            log_lines.append(f"Ignoring proof from future/bleeding edge block {height} for {txid}")
            return

        # 2. Validate Proof
        # Need to convert merkle_path_data to BUMP bytes for storage and validation
        bump_bytes: bytes
        merkle_path_obj: MerklePath | None = None

        try:
            if isinstance(merkle_path_data, bytes):
                bump_bytes = merkle_path_data
                merkle_path_obj = MerklePath.from_binary(bump_bytes)
            elif isinstance(merkle_path_data, str):
                # Hex string
                bump_bytes = bytes.fromhex(merkle_path_data)
                merkle_path_obj = MerklePath.from_binary(bump_bytes)
            elif isinstance(merkle_path_data, dict):
                # Dictionary structure (from TS-like response)
                # Not supported by py-sdk MerklePath.from_dict yet.
                # Would need manual construction.
                # For now, assume services returns hex or bytes as is common in py-wallet-toolbox.
                log_lines.append(f"Unsupported MerklePath format (dict) for {txid}")
                return
            else:
                log_lines.append(f"Unsupported MerklePath type {type(merkle_path_data)} for {txid}")
                return

            # Validate root matches header
            if merkle_path_obj:
                calculated_root = merkle_path_obj.compute_root(txid)
                header_root = header.get("merkleRoot")
                if header_root and calculated_root != header_root:
                    log_lines.append(f"Merkle root mismatch for {txid}: {calculated_root} != {header_root}")
                    # Mark as invalid? TS marks as invalid.
                    # self.monitor.storage.update_proven_tx_req(proven_tx_req_id, {"status": "invalid"})
                    return

        except Exception as e:
            log_lines.append(f"Proof validation failed for {txid}: {e!s}")
            return

        # 3. Update Storage (ProvenTx)
        try:
            update_args = {
                "provenTxReqId": proven_tx_req_id,
                "status": "notifying",  # or completed? TS: status becomes 'completed' inside update method
                "txid": txid,
                "attempts": attempts,
                "history": req.get("history", []),
                "index": 0,  # Extract from BUMP if possible, otherwise 0
                "height": height,
                "blockHash": header.get("hash"),
                "merklePath": bump_bytes,
                "merkleRoot": header.get("merkleRoot"),
            }

            # Use provider's update logic
            result = self.monitor.storage.update_proven_tx_req_with_new_proven_tx(update_args)
            status = result.get("status", "unknown")
            log_lines.append(f"Proven {txid} at height {height} (status: {status})")

            # Hook
            # Pass simplified status object
            tx_status = {"txid": txid, "status": "proven", "height": height}
            self.monitor.call_on_proven_transaction(tx_status)

        except Exception as e:
            log_lines.append(f"Failed to update proven tx {txid}: {e!s}")

    def _increment_attempts(self, req_id: int, current_attempts: int) -> None:
        try:
            self.monitor.storage.update_proven_tx_req(req_id, {"attempts": current_attempts + 1})
        except Exception:
            pass

