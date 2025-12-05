"""
ARC (Arbitrary Resilient Cryptocurrency) broadcaster for transaction submission.

This module implements the ARC provider for wallet-toolbox, enabling high-performance
transaction broadcasting with deployment tracking, callback notifications, and
custom headers support.

Key Features:
    - High-performance transaction broadcasting via ARC API
    - Deployment ID tracking for transaction analytics
    - Callback URL and token support for webhook notifications
    - Custom header injection for request customization
    - Double spend and competing transaction detection
    - Per-txid result tracking for BEEF broadcasting

Typical Usage:
    from bsv_wallet_toolbox.services.providers.arc import ARC, ArcConfig

    # Create an ARC broadcaster instance
    config = ArcConfig(api_key='your-api-key', deployment_id='my-app-v1')
    arc = ARC('https://api.taal.com/arc', config=config)

    # Broadcast a raw transaction
    result = arc.post_raw_tx('01000000...')

    # Broadcast a BEEF with multiple txids
    result = arc.post_beef(beef, ['txid1', 'txid2'])

Reference Implementation: ts-wallet-toolbox/src/services/providers/ARC.ts
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import requests

from bsv_wallet_toolbox.utils.random_utils import double_sha256_be


@dataclass
class ArcConfig:
    """Configuration options for the ARC broadcaster."""

    api_key: str | None = None
    """Authentication token for the ARC API (Bearer prefix added automatically)."""
    deployment_id: str | None = None
    """Deployment ID for transaction tracking (randomly generated if not set)."""
    callback_url: str | None = None
    """Webhook URL for proof and double spend notifications."""
    callback_token: str | None = None
    """Authorization token for callback notifications."""
    headers: dict[str, str] | None = None
    """Additional HTTP headers to attach to all requests."""


@dataclass
class ArcResponse:
    """Response entry from ARC broadcasting endpoint."""

    txid: str
    """Transaction ID."""
    extra_info: str
    """Additional information about transaction status."""
    tx_status: str
    """Transaction status (SEEN_ON_NETWORK, STORED, DOUBLE_SPEND_ATTEMPTED, etc.)."""
    competing_txs: list[str] | None = None
    """List of competing transaction IDs if double spend detected."""


@dataclass
class ArcMinerGetTxData:
    """Response from ARC /v1/tx/{txid} endpoint."""

    status: int
    title: str
    block_hash: str
    block_height: int
    competing_txs: list[str] | None
    extra_info: str
    merkle_path: str
    timestamp: str
    txid: str
    tx_status: str


@dataclass
class PostTxResultForTxidError:
    """Error details for transaction submission."""

    status: str | None = None
    detail: str | None = None
    more: dict[str, Any] | None = None


@dataclass
class PostTxResultForTxid:
    """Result from individual transaction broadcast."""

    txid: str
    status: str  # 'success' or 'error'
    data: Any | None = None
    double_spend: bool = False
    competing_txs: list[str] | None = None
    service_error: bool = False
    notes: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PostBeefResult:
    """Result from BEEF broadcasting operation."""

    name: str
    status: str  # 'success' or 'error'
    txid_results: list[PostTxResultForTxid] = field(default_factory=list)
    notes: list[dict[str, Any]] = field(default_factory=list)


def default_deployment_id() -> str:
    """Generate a random deployment ID.

    Returns:
        Deployment ID in format 'py-sdk-{hex_uuid}'.
    """
    return f"py-sdk-{uuid.uuid4().hex[:16]}"


class ARC:
    """ARC transaction broadcaster.

    Implements high-performance transaction broadcasting with support for deployment
    tracking, callbacks, and custom headers. Provides TS-compatible interfaces for
    wallet-toolbox integration.

    Attributes:
        name: Service name for logging ('ARC' or custom).
        url: API endpoint URL.
        api_key: Optional API key for authentication.
        deployment_id: Unique deployment identifier.
        callback_url: Optional webhook URL for notifications.
        callback_token: Optional token for webhook authentication.
        headers: Additional HTTP headers.
    """

    def __init__(
        self,
        url: str,
        config: ArcConfig | str | None = None,
        name: str | None = None,
    ) -> None:
        """Initialize ARC broadcaster.

        Args:
            url: ARC API endpoint URL (e.g., 'https://api.taal.com/arc').
            config: Configuration (ArcConfig object or API key string).
            name: Service name for logging (defaults to 'ARC').
        """
        self.name = name or "ARC"
        self.url = url

        if isinstance(config, str):
            # Config as simple API key string
            self.api_key = config
            self.deployment_id = default_deployment_id()
            self.callback_url: str | None = None
            self.callback_token: str | None = None
            self.headers: dict[str, str] | None = None
        else:
            # Config as ArcConfig object
            cfg = config or ArcConfig()
            self.api_key = cfg.api_key
            self.deployment_id = cfg.deployment_id or default_deployment_id()
            self.callback_url = cfg.callback_url
            self.callback_token = cfg.callback_token
            self.headers = cfg.headers

    def request_headers(self) -> dict[str, str]:
        """Construct request headers for ARC API calls.

        Returns headers including Content-Type, XDeployment-ID, and optional
        Authorization, X-CallbackUrl, X-CallbackToken, and custom headers.

        Returns:
            HTTP headers dictionary.
        """
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "XDeployment-ID": self.deployment_id,
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        if self.callback_url:
            headers["X-CallbackUrl"] = self.callback_url

        if self.callback_token:
            headers["X-CallbackToken"] = self.callback_token

        if self.headers:
            headers.update(self.headers)

        return headers

    def broadcast(self, tx: Any) -> PostTxResultForTxid:
        """Broadcast a Transaction object via ARC.

        Args:
            tx: Transaction object with hex() and txid() methods.
            
        Returns:
            PostTxResultForTxid with broadcast result.
        """
        if hasattr(tx, "hex") and hasattr(tx, "txid"):
            return self.post_raw_tx(tx.hex(), [tx.txid()])
        # Non-Transaction payloads (e.g., raw hex or BEEF) are not supported for ARC broadcast
        raise ValueError("ARC broadcast expects a Transaction object")

    def post_raw_tx(
        self,
        raw_tx: str,
        txids: list[str] | None = None,
    ) -> PostTxResultForTxid:
        """Broadcast a raw transaction via ARC.

        ARC /v1/tx endpoint supports:
        - Single serialized raw transaction
        - Single EF serialized raw transaction (untested)
        - V1 serialized BEEF (results reflect only the last transaction)

        Does NOT support:
        - V2 serialized BEEF

        Args:
            raw_tx: Raw transaction as hex string.
            txids: List of txids (uses last if multiple; if not provided, computes from raw_tx).

        Returns:
            PostTxResultForTxid with broadcast result.

        Reference: ARC.ts (postRawTx)
        """
        # Compute or extract txid
        if txids:
            txid = txids[-1]  # Use last txid if list provided
        else:
            raw_bytes = bytes.fromhex(raw_tx)
            txid = bytes(double_sha256_be(raw_bytes)).hex()
            txids = [txid]

        result = PostTxResultForTxid(txid=txid, status="success", notes=[])

        headers = self.request_headers()
        url = f"{self.url}/v1/tx"
        now = datetime.now(timezone.utc).isoformat()

        def make_note(name: str, when: str) -> dict[str, str]:
            return {"name": name, "when": when}

        def make_note_extended(name: str, when: str) -> dict[str, Any]:
            return {
                "name": name,
                "when": when,
                "rawTx": raw_tx,
                "txids": ",".join(txids or []),
                "url": url,
            }

        nn = make_note(self.name, now)
        nne = make_note_extended(self.name, now)

        try:
            response = requests.post(
                url,
                json={"rawTx": raw_tx},
                headers=headers,
                timeout=30,
            )

            if response.status_code in (200, 201):
                arc_response_data = response.json()
                response_txid = arc_response_data.get("txid")
                extra_info = arc_response_data.get("extraInfo", "")
                tx_status = arc_response_data.get("txStatus", "")
                competing_txs = arc_response_data.get("competingTxs")

                nnr = {
                    "txid": response_txid,
                    "extraInfo": extra_info,
                    "txStatus": tx_status,
                    "competingTxs": ",".join(competing_txs) if competing_txs else None,
                }

                result.data = f"{tx_status} {extra_info}"
                if result.txid != response_txid:
                    result.data += f" txid altered from {result.txid} to {response_txid}"
                result.txid = response_txid

                if tx_status in ("DOUBLE_SPEND_ATTEMPTED", "SEEN_IN_ORPHAN_MEMPOOL"):
                    result.status = "error"
                    result.double_spend = True
                    result.competing_txs = competing_txs
                    result.notes.append({**nne, **nnr, "what": "postRawTxDoubleSpend"})
                else:
                    result.notes.append({**nn, **nnr, "what": "postRawTxSuccess"})
            else:
                # Check for rate limiting specifically
                if response.status_code == 429:
                    result.status = "rate_limited"
                    result.rate_limited = True
                else:
                    result.status = "error"
                result.service_error = True

                nnr = {}
                try:
                    arc_response_data = response.json()
                    nnr["txid"] = arc_response_data.get("txid")
                    nnr["extraInfo"] = arc_response_data.get("extraInfo")
                    nnr["txStatus"] = arc_response_data.get("txStatus")
                except Exception:
                    pass

                error_data = PostTxResultForTxidError(status=str(response.status_code))
                result.data = error_data

                note: dict[str, Any] = {
                    **nn,
                    **nne,
                    **nnr,
                    "what": "postRawTxError",
                    "status": response.status_code,
                }

                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
                        error_data.more = response_data
                        error_data.detail = response_data.get("detail")
                        if error_data.detail:
                            note["detail"] = error_data.detail
                except Exception:
                    response_text = response.text
                    if response_text:
                        note["data"] = response_text[:128]

                result.notes.append(note)

        except Exception as e:
            result.status = "error"
            result.service_error = True
            result.data = f"ERROR: {e!s}"
            result.notes.append(
                {
                    **nne,
                    "what": "postRawTxCatch",
                    "error": str(e),
                }
            )

        return result

    def post_beef(self, beef: Any, txids: list[str]) -> PostBeefResult:
        """Broadcast a BEEF via ARC.

        ARC does not natively support multiple txids in BEEF format, but processes
        multiple transactions. Results for all txids are collected via the /v1/tx/{txid}
        endpoint.

        Args:
            beef: BEEF object with to_hex() method.
            txids: List of transaction IDs to track results for.

        Returns:
            PostBeefResult with per-txid status.

        Reference: ARC.ts (postBeef)
        """
        result = PostBeefResult(name=self.name, status="success", txid_results=[])

        now = datetime.now(timezone.utc).isoformat()

        def make_note(name: str, when: str) -> dict[str, str]:
            return {"name": name, "when": when}

        nn = make_note(self.name, now)

        # Note: BEEF_V2 to V1 conversion requires py-sdk Beef.to_hex() and BeefTx.is_txid_only
        # (See doc/PY_SDK_ADDITIONAL_BEEF_FEATURES.md)
        # Current implementation uses py-sdk to_hex() when available.
        beef_hex = beef.to_hex() if hasattr(beef, "to_hex") else str(beef)

        # Broadcast BEEF (treated as raw tx)
        prtr = self.post_raw_tx(beef_hex, txids)

        result.status = prtr.status
        result.txid_results = [prtr]

        # For additional txids, replicate results and query status
        for txid in txids:
            if prtr.txid == txid:
                continue

            tr = PostTxResultForTxid(txid=txid, status="success", notes=[])

            # Query transaction status
            dr = self.get_tx_data(txid)
            if dr and dr.txid != txid:
                tr.status = "error"
                tr.data = "internal error"
                tr.notes.append(
                    {
                        **nn,
                        "what": "postBeefGetTxDataInternal",
                        "txid": txid,
                        "returnedTxid": dr.txid if dr else None,
                    }
                )
            elif dr and dr.tx_status in ("SEEN_ON_NETWORK", "STORED"):
                tr.data = dr.tx_status
                tr.notes.append(
                    {
                        **nn,
                        "what": "postBeefGetTxDataSuccess",
                        "txid": txid,
                        "txStatus": dr.tx_status,
                    }
                )
            else:
                tr.status = "error"
                tr.data = dr if dr else {"error": "no data"}
                tr.notes.append(
                    {
                        **nn,
                        "what": "postBeefGetTxDataError",
                        "txid": txid,
                        "txStatus": dr.tx_status if dr else "unknown",
                    }
                )

            result.txid_results.append(tr)
            if result.status == "success" and tr.status == "error":
                result.status = "error"

        return result

    def get_tx_data(self, txid: str) -> ArcMinerGetTxData | None:
        """Query transaction status from ARC.

        Retrieves detailed transaction data including block hash, height, merkle path,
        and competing transactions. This is used to verify transactions broadcast
        via BEEF after the initial broadcast.

        Args:
            txid: Transaction ID to query.

        Returns:
            ArcMinerGetTxData with transaction details, or None on error.

        Reference: ARC.ts (getTxData)
        """
        headers = self.request_headers()
        url = f"{self.url}/v1/tx/{txid}"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return ArcMinerGetTxData(
                    status=data.get("status"),
                    title=data.get("title"),
                    block_hash=data.get("blockHash"),
                    block_height=data.get("blockHeight"),
                    competing_txs=data.get("competingTxs"),
                    extra_info=data.get("extraInfo"),
                    merkle_path=data.get("merklePath"),
                    timestamp=data.get("timestamp"),
                    txid=data.get("txid"),
                    tx_status=data.get("txStatus"),
                )
        except Exception:
            pass

        return None

    def get_transaction_status(self, txid: str, use_next: bool | None = None) -> dict[str, Any]:  # noqa: ARG002
        """Get transaction status for a given txid (TS-compatible response shape).

        Args:
            txid: Transaction ID (hex, big-endian)
            use_next: Provider selection hint (ignored; kept for parity with TS)

        Returns:
            dict: A dictionary describing the transaction status with "name" and "status" fields.

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getTransactionStatus
        """
        headers = self.request_headers()
        url = f"{self.url}/v1/tx/{txid}"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                status = data.get("txStatus", "unknown")
                return {
                    "name": "ARC",
                    "status": status,
                    "txid": txid,
                    "blockHeight": data.get("blockHeight"),
                    "blockHash": data.get("blockHash"),
                    "timestamp": data.get("timestamp"),
                }
            elif response.status_code == 404:
                return {
                    "name": "ARC",
                    "status": "not_found",
                    "txid": txid,
                }
            elif response.status_code == 500:
                raise RuntimeError("ARC server error (500)")
            elif response.status_code == 429:
                raise RuntimeError("ARC rate limit exceeded (429)")
            else:
                raise RuntimeError(f"ARC HTTP error {response.status_code}")
        except requests.exceptions.Timeout:
            raise RuntimeError("ARC request timeout")
        except requests.exceptions.ConnectionError:
            raise RuntimeError("ARC connection error")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"ARC network error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"ARC error: {str(e)}")
