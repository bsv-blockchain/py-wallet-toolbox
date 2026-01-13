"""Factory for creating bulk ingestors.

Provides functions to create configured bulk ingestors for different sources.

Reference: go-wallet-toolbox/pkg/services/chaintracks/create_ingestors.go
"""

from ...wallet_services import Chain
from .bulk_ingestor_cdn import BulkIngestorCDN
from .bulk_ingestor_interface import NamedBulkIngestor
from .bulk_ingestor_woc import BulkIngestorWOC
from .cdn_reader import CDNReader


def create_bulk_ingestors(chain: Chain, api_key: str | None = None) -> list[NamedBulkIngestor]:
    """Create configured bulk ingestors.

    Args:
        chain: Blockchain network
        api_key: Optional WhatsOnChain API key

    Returns:
        List of named bulk ingestors
    """
    ingestors = []

    # Create CDN bulk ingestor (Project Babbage)
    cdn_ingestor = BulkIngestorCDN(chain, CDNReader.BABBAGE_CDN_BASE_URL)
    ingestors.append(NamedBulkIngestor(name="chaintracks_cdn", ingestor=cdn_ingestor))

    # Create WhatsOnChain bulk ingestor
    woc_ingestor = BulkIngestorWOC(chain, api_key)
    ingestors.append(NamedBulkIngestor(name="whats_on_chain_cdn", ingestor=woc_ingestor))

    return ingestors
