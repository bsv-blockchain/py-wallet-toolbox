"""AuthFetch - Authenticated HTTP client for BSV wallet operations.

Provides authenticated HTTP requests using wallet-based authentication.
Equivalent to Go's AuthFetch from go-sdk/auth/clients/authhttp.

Reference: toolbox/go-wallet-toolbox/pkg/storage/client.go
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import requests

from .wallet import Wallet


class SimplifiedFetchRequestOptions:
    """Options for authenticated HTTP requests.

    Reference: go-sdk/auth/clients/authhttp SimplifiedFetchRequestOptions
    """

    def __init__(
        self,
        method: str = "GET",
        headers: Optional[dict[str, str]] = None,
        body: Optional[bytes | str] = None,
    ):
        """Initialize request options.

        Args:
            method: HTTP method
            headers: HTTP headers
            body: Request body
        """
        self.method = method
        self.headers = headers or {}
        self.body = body


class AuthFetch:
    """Authenticated HTTP client for BSV wallet operations.

    Makes HTTP requests with wallet-based authentication.
    Currently implements basic HTTP client - authentication to be added.

    Reference: go-sdk/auth/clients/authhttp AuthFetch
    """

    def __init__(self, wallet: Wallet, options: Optional[dict[str, Any]] = None):
        """Initialize AuthFetch.

        Args:
            wallet: Wallet instance for authentication
            options: Client options (http_client, logger, etc.)
        """
        self.wallet = wallet
        self.options = options or {}

        # Create HTTP client
        http_client = self.options.get("http_client")
        if http_client:
            self.client = http_client
        else:
            self.client = requests.Session()
            self.client.headers.update({"User-Agent": "bsv-wallet-toolbox"})

    async def fetch(
        self,
        url: str,
        options: SimplifiedFetchRequestOptions,
    ) -> requests.Response:
        """Make authenticated HTTP request.

        Args:
            url: Request URL
            options: Request options

        Returns:
            HTTP response

        Raises:
            Exception: On request failure
        """
        # Prepare request
        method = options.method
        headers = options.headers.copy() if options.headers else {}

        # Add authentication headers (TODO: implement wallet-based auth)
        # For now, this is a basic HTTP client

        # Prepare body
        json_data = None
        data = None

        if options.body:
            if isinstance(options.body, (bytes, str)):
                # Assume JSON string or bytes
                if isinstance(options.body, str):
                    data = options.body
                else:
                    data = options.body.decode('utf-8')
                json_data = data  # requests will handle JSON parsing
            else:
                # Assume dict/object to be JSON serialized
                json_data = options.body

            # Set content-type if not specified
            if 'content-type' not in [h.lower() for h in headers.keys()]:
                headers['Content-Type'] = 'application/json'

        # Make request in thread pool to maintain async interface
        loop = asyncio.get_event_loop()

        def _make_request():
            if json_data is not None and not isinstance(json_data, (str, bytes)):
                return self.client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                )
            else:
                return self.client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=data,
                )

        try:
            response = await loop.run_in_executor(None, _make_request)

            # Raise for HTTP errors
            response.raise_for_status()

            return response

        except requests.RequestException as e:
            raise Exception(f"HTTP request failed: {e}") from e

    async def close(self) -> None:
        """Close the HTTP client."""
        if hasattr(self.client, 'close'):
            self.client.close()

    async def __aenter__(self) -> AuthFetch:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
