"""Client for Arcade transaction status updates via Server-Sent Events (SSE).

Connects to Arcade's ``GET /events?callbackToken=<token>`` endpoint for
real-time transaction status updates. The wire format is::

    id: <unix-nanosecond timestamp>
    event: status
    data: {"txid": "...", "txStatus": "...", "timestamp": "..."}

Keepalive comment lines (starting with ``:``) are sent every 15 seconds.
On a first connect (no ``Last-Event-ID``) Arcade replays the current
non-terminal statuses for the token. With ``Last-Event-ID`` (a nanosecond
timestamp) it replays every status newer than that timestamp, terminal
ones included.

The stream is read on a daemon thread; ``on_event`` is invoked from that
thread, so callbacks must be thread-safe. Lifecycle mirrors the TS
``ArcSSEClient``: no automatic reconnect — call :meth:`fetch_events` to
(re)connect on demand (app open, balance refresh, etc.).

Reference: ts-wallet-toolbox/src/services/providers/ArcSSEClient.ts
Reference: arcade/services/sse/manager.go
"""

from __future__ import annotations

import json
import logging
import threading
from collections.abc import Callable
from typing import Any
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)


def _resume_event_id(last_event_id: str) -> str:
    """Last-Event-ID to resume from after ``last_event_id``.

    Event ids are status timestamps, and several events can share one when
    Arcade stamps a batch at once. Arcade replays only events strictly newer
    than the id, so step back 1ns to also get the rest of a batch interrupted
    mid-way; the few events redelivered are processed idempotently.
    """
    try:
        return str(int(last_event_id) - 1)
    except ValueError:
        return last_event_id


class ArcadeSSEClient:
    """SSE client for Arcade transaction status events.

    Attributes:
        last_event_id: The most recently received event id (nanosecond
            timestamp string), used as ``Last-Event-ID`` for catch-up on
            reconnect. Persist it via ``on_last_event_id_changed``.
    """

    def __init__(
        self,
        base_url: str,
        callback_token: str,
        on_event: Callable[[dict[str, Any]], None],
        api_key: str | None = None,
        on_error: Callable[[Exception], None] | None = None,
        last_event_id: str | None = None,
        on_last_event_id_changed: Callable[[str], None] | None = None,
        read_timeout: float = 60.0,
    ) -> None:
        """Initialize the SSE client.

        Args:
            base_url: Base URL of the Arcade instance. Note: Arcade serves
                ``/events`` from its SSE service, which may run on a separate
                port from the submit API.
            callback_token: Stable per-wallet token matching the
                X-CallbackToken sent on broadcast; scopes which transaction
                status events are routed to this stream.
            on_event: Called for each status event, with the parsed
                ``{"txid", "txStatus", "timestamp"}`` dict. Invoked from the
                reader thread — must be thread-safe.
            api_key: Optional server-level API key (Authorization: Bearer).
            on_error: Called when a connection error occurs or the stream ends.
            last_event_id: Initial Last-Event-ID for catch-up.
            on_last_event_id_changed: Called whenever last_event_id advances,
                for persistence to storage.
            read_timeout: Socket read timeout in seconds. Must be longer than
                Arcade's 15-second keepalive interval.
        """
        self.last_event_id = last_event_id
        self._on_event = on_event
        self._on_error = on_error
        self._on_last_event_id_changed = on_last_event_id_changed
        self._api_key = api_key
        self._read_timeout = read_timeout

        base = base_url.rstrip("/")
        self._url = f"{base}/events?callbackToken={quote(callback_token)}"
        self._display_url = f"{base}/events?callbackToken=<redacted>"
        # Connection errors quote the request URL; keep the token out of on_error.
        self._secrets = {s for s in (callback_token, quote(callback_token)) if s}

        self._thread: threading.Thread | None = None
        self._response: requests.Response | None = None
        self._closing = False

    @property
    def connected(self) -> bool:
        """True while the reader thread is alive."""
        return self._thread is not None and self._thread.is_alive()

    def connect(self) -> None:
        """Open the SSE connection on a daemon thread.

        Events are dispatched via ``on_event`` as they arrive. If already
        connected, this is a no-op.
        """
        if self.connected:
            logger.debug("ArcadeSSE already connected")
            return

        self._closing = False
        self._thread = threading.Thread(target=self._run, name="ArcadeSSE", daemon=True)
        self._thread.start()

    def close(self) -> None:
        """Close the connection and stop the reader thread."""
        self._closing = True
        response = self._response
        if response is not None:
            try:
                response.close()
            except Exception:
                pass
        thread = self._thread
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=5)
        self._thread = None

    def fetch_events(self) -> None:
        """Ensure the connection is open, reconnecting after a failure.

        Returns immediately — events arrive asynchronously via ``on_event``.
        Call on demand (app open, balance refresh, transaction list view).
        """
        if not self.connected:
            self.close()
            self.connect()

    # --- reader thread ---

    def _run(self) -> None:
        headers = {
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
        }
        if self.last_event_id:
            headers["Last-Event-ID"] = _resume_event_id(self.last_event_id)
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        logger.debug(f"ArcadeSSE connecting to {self._display_url} (Last-Event-ID: {headers.get('Last-Event-ID')})")

        try:
            response = requests.get(self._url, headers=headers, stream=True, timeout=(10, self._read_timeout))
            self._response = response
            if response.status_code != 200:
                raise RuntimeError(f"SSE connect failed: HTTP {response.status_code}")
            self._read_stream(response)
            if not self._closing and self._on_error:
                self._on_error(RuntimeError("SSE stream ended"))
        except Exception as e:
            if not self._closing and self._on_error:
                message = str(e)
                for secret in self._secrets:
                    message = message.replace(secret, "<redacted>")
                self._on_error(RuntimeError(message))
        finally:
            self._response = None

    def _read_stream(self, response: requests.Response) -> None:
        event_id: str | None = None
        event_name: str | None = None
        data_lines: list[str] = []

        for raw_line in response.iter_lines(decode_unicode=True):
            if self._closing:
                return
            line = raw_line if isinstance(raw_line, str) else raw_line.decode("utf-8", errors="replace")

            if line == "":
                # Blank line = dispatch the accumulated event.
                if data_lines:
                    self._dispatch(event_id, event_name, "\n".join(data_lines))
                event_id = None
                event_name = None
                data_lines = []
            elif line.startswith(":"):
                # Keepalive comment.
                continue
            elif line.startswith("id:"):
                event_id = line[3:].strip()
            elif line.startswith("event:"):
                event_name = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].strip())

    def _dispatch(self, event_id: str | None, event_name: str | None, data: str) -> None:
        if event_name != "status":
            return
        try:
            event = json.loads(data)
        except ValueError:
            logger.debug(f"ArcadeSSE malformed event: {data[:200]}")
            return

        if event_id:
            self.last_event_id = event_id
            if self._on_last_event_id_changed:
                try:
                    self._on_last_event_id_changed(event_id)
                except Exception as e:
                    logger.debug(f"ArcadeSSE on_last_event_id_changed failed: {e}")

        logger.debug(f"ArcadeSSE event: txid={event.get('txid')} status={event.get('txStatus')}")
        self._on_event(event)
