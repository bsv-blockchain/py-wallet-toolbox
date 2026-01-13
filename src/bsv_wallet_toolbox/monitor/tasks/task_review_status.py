"""TaskReviewStatus implementation."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from ..wallet_monitor_task import WalletMonitorTask

if TYPE_CHECKING:
    from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..monitor import Monitor


class TaskReviewStatus(WalletMonitorTask):
    """Notify Transaction records of changes in ProvenTxReq records they may have missed.

    The `notified` property flags reqs that do not need to be checked.
    Looks for aged Transactions with provenTxId with status != 'completed', sets status to 'completed'.
    Looks for reqs with 'invalid' status that have corresonding transactions with status other than 'failed'.

    Reference: ts-wallet-toolbox/src/monitor/tasks/TaskReviewStatus.ts
    """

    aged_msecs: int
    trigger_msecs: int

    def __init__(
        self,
        monitor: "Monitor",
        trigger_msecs: int = 15 * 60 * 1000,
        aged_msecs: int = 5 * 60 * 1000,
    ) -> None:
        """Initialize TaskReviewStatus."""
        super().__init__(monitor, "ReviewStatus")
        self.trigger_msecs = trigger_msecs
        self.aged_msecs = aged_msecs

    def trigger(self, now: int) -> dict[str, bool]:
        """Run periodically."""
        should_run = now - self.last_run_msecs_since_epoch > self.trigger_msecs
        return {"run": should_run}

    def run_task(self) -> str:
        """Review status."""
        log = ""
        now = datetime.now(UTC)
        aged_limit = now - timedelta(milliseconds=self.aged_msecs)

        try:
            # review_status in provider expects 'agedLimit' as a key
            res = self.monitor.storage.review_status({"agedLimit": aged_limit})
            if res.get("log"):
                log += res["log"]
        except Exception as e:
            log += f"Error running reviewStatus: {e!s}"

        return log
