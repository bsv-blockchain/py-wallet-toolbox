"""ChaintracksService - HTTP server reference implementation for Chaintracks API.

⚠️ IMPORTANT DESIGN NOTE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
wallet-toolbox is a LIBRARY, not a standalone server application.

ChaintracksService provides:
1. ✅ Endpoint specifications for Chaintracks API
2. ✅ Configuration and initialization logic
3. ✅ Reference implementation for porting

ChaintracksService does NOT provide:
1. ❌ Full HTTP server implementation (users should use Flask/FastAPI)
2. ❌ CORS/routing/middleware (user's choice of framework)
3. ❌ WebSocket implementation (out of scope for library)

RECOMMENDED USAGE:
→ Users should create their own HTTP server using Flask/FastAPI
→ Import ChaintracksService for configuration reference
→ Implement endpoints based on this class's method signatures

Example:
    from flask import Flask
    from bsv_wallet_toolbox.services.chaintracker import ChaintracksService, ChaintracksStorage

    app = Flask(__name__)
    storage = ChaintracksStorage(...)
    service = ChaintracksService(...)

    @app.get('/getHeight')
    def get_height():
        return storage.get_height()
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Provides REST API endpoints for blockchain data access (headers, heights, status).
Implements synchronous design for consistency with Python wallet-toolbox.

Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksService.ts
"""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any, TypedDict

from bsv_wallet_toolbox.errors import WalletError

from ..wallet_services import Chain, WalletServices


class ChaintracksServiceOptions(TypedDict, total=False):
    """Configuration for ChaintracksService."""

    chain: Chain
    routing_prefix: str
    port: int | None


class ChaintracksService:
    """HTTP server providing Chaintracks API endpoints.

    Synchronous, blocking design for consistency with Python implementation.

    DESIGN PRINCIPLE:
    This class serves as a REFERENCE IMPLEMENTATION for library users.
    It provides:
    - Configuration options for ChaintracksService
    - Initialization and setup logic
    - Method signatures for REST endpoints

    Users should NOT use this class directly as a production server.
    Instead, they should:
    1. Create their own HTTP server (Flask, FastAPI, etc.)
    2. Use ChaintracksStorage and ChaintracksServiceClient for data operations
    3. Implement endpoints based on this class's structure

    Phase 4-B TODO:
    - Complete endpoint documentation
    - Add parameter validation examples
    - Provide more usage examples

    Phase 5+ TODO (User Implementation):
    - Implement HTTP middleware (CORS, authentication)
    - Add WebSocket endpoints for real-time updates
    - Implement rate limiting and caching

    Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksService.ts
    """

    @staticmethod
    def create_chaintracks_service_options(chain: Chain) -> ChaintracksServiceOptions:
        """Create default options for ChaintracksService.

        Args:
            chain: Blockchain network ('main' or 'test')

        Returns:
            Default service options

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksService.ts
        """
        options: ChaintracksServiceOptions = {
            "chain": chain,
            "routingPrefix": "",
        }
        return options

    def __init__(
        self,
        options: ChaintracksServiceOptions,
        chaintracks: Any | None = None,
        services: WalletServices | None = None,
    ) -> None:
        """Initialize ChaintracksService.

        Args:
            options: Service configuration
            chaintracks: Chaintracks instance (optional)
            services: WalletServices instance (optional)

        Raises:
            WalletError: If chain mismatch in components

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksService.ts
        """
        self.options: ChaintracksServiceOptions = {**options}
        self.chain: Chain = options.get("chain", "main")
        self.port: int | None = options.get("port")
        self.routing_prefix: str = options.get("routingPrefix", "")

        # TODO: Phase 4 - Implement Chaintracks instance creation
        # TODO: Phase 4 - Implement default NoDb storage
        self.chaintracks: Any = chaintracks

        # TODO: Phase 4 - Implement Services instance creation
        self.services: WalletServices | None = services

        # Validate chain consistency
        if self.chaintracks and hasattr(self.chaintracks, "chain"):
            if self.chaintracks.chain != self.chain:
                raise WalletError(f"Chaintracks chain mismatch: {self.chaintracks.chain} != {self.chain}")

        if self.services and hasattr(self.services, "chain"):
            if self.services.chain != self.chain:
                raise WalletError(f"Services chain mismatch: {self.services.chain} != {self.chain}")

    def start_json_rpc_server(self, port: int | None = None) -> None:
        """Start HTTP server for Chaintracks API.

        Args:
            port: Server port (defaults to 3011 or configured port)

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksService.ts
        """
        port = port or self.port or 3011
        self.port = port

        # Initialize chaintracks if not available
        if self.chaintracks and hasattr(self.chaintracks, "make_available"):
            # Note: make_available is async in TypeScript, sync here for simplicity
            pass

        # Create FastAPI app for reference implementation
        try:
            import uvicorn
            from fastapi import FastAPI
            from fastapi.middleware.cors import CORSMiddleware
        except ImportError:
            raise RuntimeError(
                "FastAPI and uvicorn required for HTTP server. Install with: pip install fastapi uvicorn"
            )

        app = FastAPI(title="ChainTracks API", version="1.0.0")

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure as needed
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Health check endpoint
        @app.get("/health")
        async def health_check():
            return {"status": "ok", "timestamp": int(time.time() * 1000)}

        # Block header endpoints
        @app.get("/header/height/{height}")
        async def get_header_for_height(height: int):
            """Get block header for specific height."""
            try:
                header = self.chaintracks.find_header_for_height(height) if self.chaintracks else None
                return header or {"error": "Header not found"}
            except Exception:
                logging.exception("Error in /header/height/{height} endpoint")
                return {"error": "An internal server error occurred."}

        # Transaction endpoints
        @app.get("/tx/{txid}")
        async def get_transaction(txid: str):
            """Get transaction data."""
            try:
                # Placeholder - would need actual transaction storage
                return {"txid": txid, "status": "not_implemented"}
            except Exception as e:
                return {"error": str(e)}

        # Merkle path endpoints
        @app.get("/merkle/{txid}")
        async def get_merkle_path(txid: str):
            """Get Merkle path for transaction."""
            try:
                # Placeholder - would need actual merkle path storage
                return {"txid": txid, "status": "not_implemented"}
            except Exception as e:
                return {"error": str(e)}

        # Start server in background thread
        def run_server() -> None:
            uvicorn.run(app, host="0.0.0.0", port=port)

        self._server_thread = threading.Thread(target=run_server, daemon=True)
        self._server_thread.start()

        # Store app reference for cleanup
        self._fastapi_app = app

    def stop_json_rpc_server(self) -> None:
        """Stop HTTP server.

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksService.ts
        """
        # Stop FastAPI server if running
        if hasattr(self, "_server_thread") and self._server_thread.is_alive():
            # Note: uvicorn doesn't provide clean shutdown from thread
            # In production, use proper server lifecycle management
            pass

        # Clean up chaintracks resources
        if self.chaintracks and hasattr(self.chaintracks, "destroy"):
            self.chaintracks.destroy()

    def _handle_robots(self) -> tuple[str, int]:
        """Handle /robots.txt request.

        Returns:
            robots.txt content

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksService.ts
        """
        return "User-agent: *\nDisallow: /", 200

    def _handle_index(self) -> tuple[str, int]:
        """Handle root / request.

        Returns:
            Service information

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksService.ts
        """
        chain_name = "mainNet" if self.chain == "main" else "testNet"
        return f"Chaintracks {chain_name} Block Header Service", 200

    def _handle_error(self, error: Exception) -> tuple[str, int]:
        """Format error response.

        Args:
            error: Exception to format

        Returns:
            JSON error response with status 500

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksService.ts
        """
        response: dict[str, Any] = {
            "status": "error",
            "message": str(error),
        }
        return json.dumps(response), 500

    def _handle_success(self, data: Any) -> tuple[str, int]:
        """Format success response.

        Args:
            data: Response data

        Returns:
            JSON success response with status 200

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksService.ts
        """
        response: dict[str, Any] = {
            "status": "success",
            "value": data,
        }
        return json.dumps(response), 200

    def destroy(self) -> None:
        """Shut down service and clean up resources.

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksService.ts
        """
        self.stop_json_rpc_server()
