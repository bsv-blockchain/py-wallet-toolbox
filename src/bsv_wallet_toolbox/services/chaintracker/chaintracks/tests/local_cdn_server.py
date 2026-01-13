"""Local CDN server for testing.

Provides a mock CDN server for serving test block headers.

Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/LocalCdnServer.ts
"""

from typing import Any


class LocalCdnServer:
    """Mock CDN server for testing.

    Serves block headers from local filesystem for integration tests.

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/LocalCdnServer.ts
    """

    def __init__(self, port: int, root_path: str):
        """Initialize server.

        Args:
            port: Port to listen on
            root_path: Root directory for serving files
        """
        self.port = port
        self.root_path = root_path
        self._server: Any = None

    async def start(self) -> None:
        """Start the server."""
        # Stub - in production would start an HTTP server

    async def stop(self) -> None:
        """Stop the server."""
        # Stub - in production would stop the HTTP server

    def get_url(self) -> str:
        """Get the server URL.

        Returns:
            Server URL
        """
        return f"http://localhost:{self.port}"
