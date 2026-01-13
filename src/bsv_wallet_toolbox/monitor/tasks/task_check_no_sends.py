"""TaskCheckNoSends implementation."""

from typing import TYPE_CHECKING

from .task_check_for_proofs import TaskCheckForProofs

if TYPE_CHECKING:
    from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..monitor import Monitor


class TaskCheckNoSends(TaskCheckForProofs):
    """Task to check for 'nosend' transactions that may have been broadcast externally.

    Unlike intentionally processed transactions, 'nosend' transactions are fully valid
    transactions which have not been processed by the wallet.

    Reference: ts-wallet-toolbox/src/monitor/tasks/TaskCheckNoSends.ts
    """

    ONE_DAY: int = 24 * 60 * 60 * 1000

    def __init__(self, monitor: "Monitor", trigger_msecs: int = ONE_DAY) -> None:
        """Initialize TaskCheckNoSends."""
        super().__init__(monitor, trigger_msecs)
        self.name = "CheckNoSends"

    def run_task(self) -> str:
        """Process 'nosend' requests."""
        self.check_now = False
        log_lines: list[str] = []

        # Get current chain tip height
        try:
            chain_tip = self.monitor.services.find_chain_tip_header()
            max_acceptable_height = chain_tip.get("height")
        except Exception as e:
            return f"Failed to get chain tip header: {e!s}"

        if max_acceptable_height is None:
            return "Chain tip height unavailable"

        # Process only 'nosend' status
        reqs = self.monitor.storage.find_proven_tx_reqs({"status": ["nosend"]})

        if not reqs:
            return ""

        log_lines.append(f"Processing {len(reqs)} nosend reqs...")

        for req in reqs:
            # Reuse logic from TaskCheckForProofs
            self._process_req(req, max_acceptable_height, log_lines)

        return "\n".join(log_lines)
