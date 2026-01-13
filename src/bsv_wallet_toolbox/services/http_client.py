"""Custom HTTP client for toolbox providers.

This client wraps aiohttp to provide a response format that matches
py-sdk's HttpClient expectations while tolerating non-JSON payloads
such as WhatsOnChain's raw hex responses.
"""

from __future__ import annotations

from typing import Any

import aiohttp
from bsv.http_client import HttpClient, HttpResponse


class ToolboxHttpClient(HttpClient):
    """HTTP client that gracefully handles non-JSON responses."""

    def __init__(self, default_timeout: float | None = None) -> None:
        self.default_timeout = default_timeout

    async def fetch(self, url: str, options: dict[str, Any]) -> HttpResponse:
        method = options.get("method", "GET")
        headers = options.get("headers") or {}
        timeout_value = options.get("timeout", self.default_timeout)
        data = options.get("data")

        request_timeout = aiohttp.ClientTimeout(total=timeout_value) if timeout_value is not None else None

        async with (
            aiohttp.ClientSession(timeout=request_timeout) as session,
            session.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=request_timeout,
            ) as response,
        ):
            status = response.status
            ok = 200 <= status <= 299

            try:
                payload = await response.json()
                body = {"data": payload}
            except Exception:
                text_payload = await response.text()
                body = {"data": text_payload}

            return HttpResponse(ok=ok, status_code=status, json_data=body)
