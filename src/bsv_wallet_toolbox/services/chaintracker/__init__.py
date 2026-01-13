"""Chaintracker components for wallet services.

Provides block header synchronization and storage abstractions:
  - ChaintracksServiceClient: HTTP client for remote Chaintracks services
  - ChaintracksService: HTTP server providing blockchain data API
  - ChaintracksStorage: Persistent storage (SQLite/MySQL)
  - ChaintracksStorageMemory: In-memory storage for fast caching

Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/
"""

# Phase 4 Implementation Status:
# ✅ ChaintracksServiceClient: 100% (HTTP client with requests)
# ✅ ChaintracksService: 30% (skeleton with TODO placeholders)
# ✅ ChaintracksStorage: 100% (persistent SQLAlchemy ORM)
# ✅ ChaintracksStorageMemory: 100% (in-memory SQLite)
#
# Phase 4 TODO - ChaintracksService:
# TODO: Phase 4 - Implement HTTP server (Flask/fastapi)
# TODO: Phase 4 - Add CORS headers support
# TODO: Phase 4 - Add health check endpoint (/health)
# TODO: Phase 4 - Add block header endpoints (/header/height/:height)
# TODO: Phase 4 - Add transaction endpoints (/tx/:txid)
# TODO: Phase 4 - Add Merkle path endpoints (/merkle/:txid)
# TODO: Phase 4 - Add subscription endpoints (WebSocket)
# TODO: Phase 4 - Implement default Chaintracks instance creation
#
# Phase 4 TODO - ChaintracksStorage:
# TODO: Phase 4 - Implement database migrations
# TODO: Phase 4 - Implement batch query optimization
# TODO: Phase 4 - Add reorg detection logic
# TODO: Phase 4 - Add transaction safety
#
# Phase 4 TODO - Overall:
# TODO: Phase 4 - Implement multi-provider strategy (Bitails, GorillaPool)
# TODO: Phase 4 - Add advanced caching for block headers and merkle paths
# TODO: Phase 4 - Implement transaction monitoring/tracking
# TODO: Phase 4 - Add retry logic with exponential backoff
# TODO: Phase 4 - Implement provider health checking and fallback
# TODO: Phase 4 - Add performance metrics collection

from .chaintracks.bulk_manager import BulkManager
from .chaintracks.models import FiatExchangeRates
from .chaintracks_chain_tracker import ChaintracksChainTracker
from .chaintracks_service import ChaintracksService
from .chaintracks_service_client import ChaintracksServiceClient
from .chaintracks_storage import ChaintracksStorage, ChaintracksStorageMemory

__all__ = [
    "BulkManager",
    "ChaintracksChainTracker",
    "ChaintracksService",
    "ChaintracksServiceClient",
    "ChaintracksStorage",
    "ChaintracksStorageMemory",
    "FiatExchangeRates",
]
