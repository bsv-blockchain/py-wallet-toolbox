"""TaskNewHeader implementation."""

import time
from typing import TYPE_CHECKING, Any

from ..wallet_monitor_task import WalletMonitorTask

if TYPE_CHECKING:
    from ..monitor import Monitor


class TaskNewHeader(WalletMonitorTask):
    """Poll the chain tip and feed new block headers to the monitor.

    New headers drive TaskCheckForProofs, and their height caps which proofs are
    accepted. A new header is queued for one cycle; only when a cycle passes without
    a newer header is Monitor.process_new_block_header called. This skips most of
    the work for blocks that are orphaned almost immediately.

    Reference: ts-wallet-toolbox/src/monitor/tasks/TaskNewHeader.ts
    """

    header: dict[str, Any] | None
    queued_header: dict[str, Any] | None
    queued_header_when: float | None

    def __init__(self, monitor: "Monitor", trigger_msecs: int = 60 * 1000) -> None:
        """Initialize TaskNewHeader.

        Args:
            monitor: Monitor instance.
            trigger_msecs: Chain tip polling interval in milliseconds.
        """
        super().__init__(monitor, "NewHeader")
        self.trigger_msecs = trigger_msecs
        self.header = None
        self.queued_header = None
        self.queued_header_when = None

    def trigger(self, now: int) -> dict[str, bool]:
        """Run once per polling interval."""
        return {"run": now - self.last_run_msecs_since_epoch > self.trigger_msecs}

    def run_task(self) -> str:
        """Fetch the chain tip and process a header that stayed the tip for a full cycle."""
        log = ""
        old_header = self.header
        self.header = self.monitor.services.find_chain_tip_header()
        height = self.header.get("height")
        block_hash = self.header.get("hash")
        is_new = True
        if old_header is None:
            log = f"first header: {height} {block_hash}"
        elif old_header.get("height") > height:
            log = f"old header: {height} vs {old_header.get('height')}"
            self.header = old_header  # Keep the higher header
            is_new = False
        elif old_header.get("height") < height:
            skip = height - old_header.get("height") - 1
            skipped = f" SKIPPED {skip}" if skip > 0 else ""
            log = f"new header: {height} {block_hash}{skipped}"
        elif old_header.get("hash") != block_hash:
            log = f"reorg header: {height} {block_hash}"
        else:
            is_new = False

        if is_new:
            self.queued_header = self.header
            self.queued_header_when = time.time()
        elif self.queued_header is not None:
            delay = time.time() - (self.queued_header_when or time.time())
            queued = self.queued_header
            log = f"process header: {queued.get('height')} {queued.get('hash')} delayed {delay:.1f} secs"
            self.monitor.process_new_block_header(queued)
            self.queued_header = None
        return log
