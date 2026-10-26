"""Deprecated: Arcade was renamed to BSV Broadcaster.

Use :mod:`bsv_wallet_toolbox.monitor.tasks.task_bsv_broadcaster_sse`
(``TaskBsvBroadcasterSSE``). Constructing :class:`TaskArcadeSSE` emits a
:class:`DeprecationWarning`.
"""

import warnings
from typing import Any

from .task_bsv_broadcaster_sse import MAX_EVENT_ATTEMPTS, PROVEN_TX_REQ_TERMINAL_STATUSES, TaskBsvBroadcasterSSE

__all__ = ["MAX_EVENT_ATTEMPTS", "PROVEN_TX_REQ_TERMINAL_STATUSES", "TaskArcadeSSE"]


class TaskArcadeSSE(TaskBsvBroadcasterSSE):
    """Deprecated alias of :class:`~bsv_wallet_toolbox.monitor.tasks.task_bsv_broadcaster_sse.TaskBsvBroadcasterSSE`."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        warnings.warn(
            "TaskArcadeSSE is deprecated. Use TaskBsvBroadcasterSSE; Arcade was renamed to BSV Broadcaster.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
