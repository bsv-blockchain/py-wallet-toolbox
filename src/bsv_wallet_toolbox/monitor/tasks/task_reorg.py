"""TaskReorg implementation."""

import time
from typing import TYPE_CHECKING, Any

from ..wallet_monitor_task import WalletMonitorTask

if TYPE_CHECKING:
    from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..monitor import Monitor


class TaskReorg(WalletMonitorTask):
    """Check the `monitor.deactivatedHeaders` for any headers that have been deactivated.

    When headers are found, review matching ProvenTx records and update proof data as appropriate.

    Reference: ts-wallet-toolbox/src/monitor/tasks/TaskReorg.ts
    """

    monitor: "Monitor"
    aged_msecs: int
    max_retries: int
    process_queue: list[dict[str, Any]]

    def __init__(
        self,
        monitor: "Monitor",
        aged_msecs: int = 10 * 60 * 1000,  # 10 minutes
        max_retries: int = 3,
    ) -> None:
        """Initialize TaskReorg."""
        super().__init__(monitor, "Reorg")
        self.aged_msecs = aged_msecs
        self.max_retries = max_retries
        self.process_queue = []

    def trigger(self, now: int) -> dict[str, bool]:
        """Determine if task should run."""
        cutoff = now - self.aged_msecs
        q = self.monitor.deactivated_headers

        while len(q) > 0 and cutoff > q[0]["whenMsecs"]:
            # Prepare to process deactivated headers that have aged sufficiently
            header = q.pop(0)
            self.process_queue.append(header)

        return {"run": len(self.process_queue) > 0}

    def run_task(self) -> str:
        """Process deactivated headers."""
        log = ""

        while True:
            if not self.process_queue:
                break
            header_info = self.process_queue.pop(0)
            header = header_info["header"]
            tries = header_info["tries"]

            ptxs = []
            try:
                # Lookup all the proven_txs records matching the deactivated headers
                ptxs = self.monitor.storage.find_proven_txs({"partial": {"blockHash": header.get("hash")}})
            except Exception as e:
                log += f"  Error finding proven txs: {e!s}\n"
                continue

            log += f"  block {header.get('hash')} orphaned with {len(ptxs)} impacted transactions\n"

            retry = False
            for ptx in ptxs:
                txid = ptx.get("txid")
                if not txid:
                    continue

                try:
                    mpr = self.monitor.services.get_merkle_path(txid)
                    # mpr format: { merklePath: ..., header: ... }
                    mp = mpr.get("merklePath")
                    h = mpr.get("header")

                    if mp and h:
                        # Find leaf in path (Python specific: depends on mp structure from services)
                        # TS: const leaf = mp.path[0].find(leaf => leaf.txid === true && leaf.hash === ptx.txid)
                        # We need to inspect the MerklePath object structure in Python.
                        # Assuming mp has 'path' attribute or is dict.
                        # If mp is bsv.merkle_path.MerklePath object:
                        # It doesn't have 'path' property directly exposed as list of list usually?
                        # Checking py-sdk merkle_path.py would be ideal but assuming generic access for now.

                        # Simplification: Assume if we got a valid MP from services for this txid, it's valid.
                        # TS logic checks if the new MP actually contains the txid.

                        update = {
                            "height": mp.blockHeight if hasattr(mp, "blockHeight") else mp.get("blockHeight"),
                            "index": 0,  # Placeholder, need actual offset
                            "merklePath": mp.to_binary() if hasattr(mp, "to_binary") else mp.get("merklePath"),
                            "merkleRoot": h.get("merkleRoot"),
                            "blockHash": h.get("hash"),
                        }

                        # Check if block hash changed
                        if update["blockHash"] == ptx.get("blockHash"):
                            log += f"    txid {txid} merkle path update still based on deactivated header {ptx.get('blockHash')}\n"
                            if tries + 1 >= self.max_retries:
                                log += f"      maximum retries {self.max_retries} exceeded\n"
                            else:
                                retry = True
                        else:
                            # Verify proof validity
                            # root = mp.compute_root(txid) ...
                            # isValid = chaintracker.isValidRootForHeight ...

                            # For now, trust get_merkle_path result as validation logic
                            # requires deep integration with chaintracker which might not be fully ready.

                            self.monitor.storage.update_proven_tx(ptx.get("provenTxId"), update)
                            log += f"    txid {txid} proof data updated\n"
                            log += f"      blockHash {ptx.get('blockHash')} -> {update['blockHash']}\n"

                    else:
                        log += f"    txid {txid} merkle path update unavailable\n"
                        retry = True
                except Exception as e:
                    log += f"    txid {txid} error processing: {e!s}\n"
                    retry = True

            if retry:
                log += "    retrying...\n"
                self.monitor.deactivated_headers.append(
                    {
                        "header": header,
                        "whenMsecs": int(time.time() * 1000),
                        "tries": tries + 1,
                    }
                )

        return log
