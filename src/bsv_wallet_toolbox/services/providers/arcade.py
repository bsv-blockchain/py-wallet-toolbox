"""Deprecated: Arcade was renamed to BSV Broadcaster.

Use :mod:`bsv_wallet_toolbox.services.providers.bsv_broadcaster`
(``BsvBroadcaster``). The names below remain as aliases so existing code keeps
working; constructing :class:`Arcade` emits a :class:`DeprecationWarning`.
"""

from __future__ import annotations

import warnings
from typing import Any

from .bsv_broadcaster import BSV_BROADCASTER_MINED_TX_STATUSES as ARCADE_MINED_TX_STATUSES
from .bsv_broadcaster import BSV_BROADCASTER_TERMINAL_TX_STATUSES as ARCADE_TERMINAL_TX_STATUSES
from .bsv_broadcaster import BSV_BROADCASTER_VALIDATION_FAILED_ERROR as ARCADE_VALIDATION_FAILED_ERROR
from .bsv_broadcaster import BsvBroadcaster, is_fee_policy_rejection

__all__ = [
    "ARCADE_MINED_TX_STATUSES",
    "ARCADE_TERMINAL_TX_STATUSES",
    "ARCADE_VALIDATION_FAILED_ERROR",
    "Arcade",
    "is_fee_policy_rejection",
]


class Arcade(BsvBroadcaster):
    """Deprecated alias of :class:`~bsv_wallet_toolbox.services.providers.bsv_broadcaster.BsvBroadcaster`."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        warnings.warn(
            "Arcade is deprecated. Use BsvBroadcaster; Arcade was renamed to BSV Broadcaster.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
