"""Deprecated: Arcade was renamed to BSV Broadcaster.

Use :mod:`bsv_wallet_toolbox.services.providers.bsv_broadcaster_sse`
(``BsvBroadcasterSSEClient``). Constructing :class:`ArcadeSSEClient` emits a
:class:`DeprecationWarning`.
"""

from __future__ import annotations

import warnings
from typing import Any

from .bsv_broadcaster_sse import BsvBroadcasterSSEClient

__all__ = ["ArcadeSSEClient"]


class ArcadeSSEClient(BsvBroadcasterSSEClient):
    """Deprecated alias of :class:`.bsv_broadcaster_sse.BsvBroadcasterSSEClient`."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        warnings.warn(
            "ArcadeSSEClient is deprecated. Use BsvBroadcasterSSEClient; Arcade was renamed to BSV Broadcaster.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
