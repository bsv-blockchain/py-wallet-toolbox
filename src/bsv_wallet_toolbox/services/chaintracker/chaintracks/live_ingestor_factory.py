"""Factory for creating live ingestors.

Provides functions to create configured live ingestors for different sources.

Reference: go-wallet-toolbox/pkg/services/chaintracks/create_ingestors.go
"""

from ...wallet_services import Chain
from .live_ingestor_interface import NamedLiveIngestor
from .live_ingestor_woc_poll import LiveIngestorWocPoll


def create_live_ingestors(chain: Chain, api_key: str | None = None) -> list[NamedLiveIngestor]:
    """Create configured live ingestors.

    Args:
        chain: Blockchain network
        api_key: Optional WhatsOnChain API key

    Returns:
        List of named live ingestors
    """
    ingestors = []

    # Create WhatsOnChain polling ingestor
    woc_ingestor = LiveIngestorWocPoll(chain=chain, sync_period=60.0, api_key=api_key)  # 60 seconds like Go default

    ingestors.append(NamedLiveIngestor(name="woc_poll", ingestor=woc_ingestor))

    return ingestors
