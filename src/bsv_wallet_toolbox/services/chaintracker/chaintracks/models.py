"""Models for Chaintracks service DTOs.

This module contains data transfer objects used by the Chaintracks service.

Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/models/
"""

from datetime import datetime
from typing import TypedDict

from .util.height_range import HeightRange


class FiatExchangeRates(TypedDict):
    """Fiat currency exchange rate data at a specific timestamp.

    This represents fiat currency exchange rates retrieved from the Chaintracks service.
    It includes the base currency, a mapping of currency codes to rates, and the time
    of the rates' validity.

    Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/models/FiatExchangeRates.ts
    """

    timestamp: str  # ISO 8601 timestamp string
    rates: dict[str, float]  # Currency code -> exchange rate
    base: str  # Base currency code (e.g., "USD")


class HeightRanges:
    """Represents height ranges for bulk and live storage.

    Reference: toolbox/go-wallet-toolbox/pkg/services/chaintracks/models/height_ranges.go
    """

    def __init__(self, bulk: HeightRange | None = None, live: HeightRange | None = None):
        """Initialize height ranges.

        Args:
            bulk: Bulk storage height range
            live: Live storage height range
        """
        self.bulk = bulk or HeightRange(0, -1)  # Empty range
        self.live = live or HeightRange(0, -1)  # Empty range

    def __repr__(self) -> str:
        return f"HeightRanges(bulk={self.bulk}, live={self.live})"


class ReorgEvent:
    """Represents a chain reorganization event.

    Contains the old and new chain tips when a reorganization occurs.

    Reference: toolbox/go-wallet-toolbox/pkg/services/chaintracks/models/reorg_event.go
    """

    def __init__(self, old_tip: dict[str, any], new_tip: dict[str, any]):
        """Initialize reorg event.

        Args:
            old_tip: The old chain tip block header
            new_tip: The new chain tip block header
        """
        self.old_tip = old_tip
        self.new_tip = new_tip

    def __repr__(self) -> str:
        return f"ReorgEvent(old_tip={self.old_tip}, new_tip={self.new_tip})"
