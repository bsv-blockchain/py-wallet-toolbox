"""Arcade broadcaster for transaction submission.

Arcade (bsv-blockchain/arcade) is the Teranode-native, ARC-compatible
broadcaster. Arcade is intentionally a separate, self-contained class (not a
subclass of ARC) so the ARC transport is never altered — mirroring the TS
design. It shares ARC's wire-contract types (ArcConfig, ArcMinerGetTxData,
PostTxResultForTxid, PostBeefResult) but differs where it must:

- Endpoints are served at the root: ``POST /tx`` and ``GET /tx/{txid}``
  (no ``/v1`` prefix).
- A submit returns HTTP 202 with ``{"txid", "status": 202, "txStatus"}``;
  HTTP 400 ``{"error": "transaction failed validation"}`` is terminal (the
  tx itself is invalid, so failing over to another provider won't help),
  except when the reason is Arcade's operator-configured minimum fee.
  That and other 400s (e.g. an invalid X-CallbackUrl) remain service errors.
- Submission encoding is Extended Format (EF) only: Arcade's ``/tx`` parser
  rejects BEEF, and a raw tx fails validation because it lacks the
  per-input source data that EF carries inline. When EF cannot be built,
  nothing is posted and the result is a service error.
- Error bodies are flat ``{"error": ..., "reason": ...}``, not RFC 7807.

Reference Implementation: ts-wallet-toolbox/src/services/providers/Arcade.ts
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import requests
from bsv.merkle_path import MerklePath

from bsv_wallet_toolbox.utils.random_utils import double_sha256_be

from .arc import (
    ArcConfig,
    ArcMinerGetTxData,
    PostBeefResult,
    PostTxResultForTxid,
    PostTxResultForTxidError,
    default_deployment_id,
)

logger = logging.getLogger(__name__)

# POST /tx txStatus values meaning the transaction can never succeed.
ARCADE_TERMINAL_TX_STATUSES = frozenset({"REJECTED", "DOUBLE_SPEND_ATTEMPTED"})

# POST /tx HTTP 400 error text for a transaction that failed validation (terminal).
ARCADE_VALIDATION_FAILED_ERROR = "transaction failed validation"

# GET /tx/{txid} txStatus values meaning the transaction is included in a block.
ARCADE_MINED_TX_STATUSES = frozenset({"MINED", "IMMUTABLE"})


def is_fee_policy_rejection(reason: Any) -> bool:
    """True when an Arcade rejection reason is its minimum-fee policy.

    The fee floor is operator-configured, so another broadcaster may accept the
    transaction. Teranode reports it as "transaction fee is too low: ...".
    """
    return isinstance(reason, str) and "fee is too low" in reason.lower()


def _arcade_error_detail(data: Any) -> str | None:
    """Extract a human-readable message from Arcade's flat {"error", "reason"} body."""
    if not isinstance(data, dict):
        return None
    error = str(data.get("error") or "").strip()
    reason = str(data.get("reason") or "").strip()
    if error and reason:
        return f"{error}: {reason}"
    return error or reason or None


class Arcade:
    """Arcade transaction broadcaster (Teranode-native, ARC-compatible).

    Attributes:
        name: Service name for logging (defaults to 'arcade').
        url: Arcade endpoint base URL.
        api_key: Optional API key for authentication.
        deployment_id: Unique deployment identifier.
        callback_url: Optional webhook URL for notifications.
        callback_token: Optional token scoping SSE/webhook status events.
        headers: Additional HTTP headers.
    """

    def __init__(
        self,
        url: str,
        config: ArcConfig | str | None = None,
        name: str | None = None,
    ) -> None:
        """Initialize Arcade broadcaster.

        Args:
            url: Arcade endpoint base URL (e.g., 'https://arcade-v2-us-1.bsvblockchain.tech').
            config: Configuration (shares ARC's ArcConfig shape, or API key string).
            name: Service name for logging (defaults to 'arcade').
        """
        self.name = name or "arcade"
        self.url = url.rstrip("/")

        if isinstance(config, str):
            self.api_key: str | None = config.strip()
            self.deployment_id = default_deployment_id()
            self.callback_url: str | None = None
            self.callback_token: str | None = None
            self.headers: dict[str, str] | None = None
        else:
            cfg = config or ArcConfig()
            self.api_key = cfg.api_key.strip() if isinstance(cfg.api_key, str) else cfg.api_key
            self.deployment_id = cfg.deployment_id or default_deployment_id()
            self.callback_url = cfg.callback_url
            self.callback_token = cfg.callback_token
            self.headers = cfg.headers

    def request_headers(self) -> dict[str, str]:
        """Construct request headers for Arcade API calls."""
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
        """Broadcast a Transaction object via Arcade.

        Arcade needs Extended Format (EF), which carries the per-input source
        data its fee/script validation requires. When EF cannot be built
        (inputs without source transactions) nothing is posted and a service
        error is returned so aggregation falls through to another provider.

        Args:
            tx: Transaction object with hex()/txid() (and optionally to_ef()) methods.

        Returns:
            PostTxResultForTxid with broadcast result.
        """
        if not (hasattr(tx, "hex") and hasattr(tx, "txid")):
            raise ValueError("Arcade broadcast expects a Transaction object")
        txid = tx.txid()
        try:
            ef_hex = tx.to_ef().hex()
        except Exception as e:
            return self._ef_build_failed(txid, e)
        return self.post_raw_tx(ef_hex, [txid])

    def _ef_build_failed(self, txid: str, error: Exception) -> PostTxResultForTxid:
        """Non-terminal result for a tx that cannot be encoded as EF (nothing is posted)."""
        return PostTxResultForTxid(
            txid=txid,
            status="error",
            service_error=True,
            notes=[
                {
                    "name": self.name,
                    "when": datetime.now(UTC).isoformat(),
                    "what": "arcadeEfBuildFailed",
                    "txid": txid,
                    "error": str(error),
                }
            ],
        )

    def post_raw_tx(
        self,
        raw_tx: str,
        txids: list[str] | None = None,
    ) -> PostTxResultForTxid:
        """Submit a single transaction to Arcade's ``POST /tx`` endpoint.

        ``raw_tx`` must be a single (raw or Extended Format) transaction hex —
        NOT BEEF.

        Args:
            raw_tx: Raw or EF transaction as hex string.
            txids: List of txids (uses last if multiple; computed from raw_tx if omitted).

        Returns:
            PostTxResultForTxid with broadcast result.

        Reference: Arcade.ts (postRawTx)
        """
        if txids:
            txid = txids[-1]
        else:
            txid = bytes(double_sha256_be(bytes.fromhex(raw_tx))).hex()
            txids = [txid]

        result = PostTxResultForTxid(txid=txid, status="success", notes=[])

        headers = self.request_headers()
        url = f"{self.url}/tx"
        now = datetime.now(UTC).isoformat()

        nn = {"name": self.name, "when": now}
        nne = {**nn, "rawTx": raw_tx, "txids": ",".join(txids), "url": url}

        try:
            response = requests.post(url, json={"rawTx": raw_tx}, headers=headers, timeout=30)
            logger.debug(f"Arcade {self.name} HTTP response status: {response.status_code}")

            if response.status_code in (200, 201, 202):
                data = response.json()
                response_txid = data.get("txid") or txid
                tx_status = data.get("txStatus", "")
                extra_info = data.get("extraInfo", "")
                competing_txs = data.get("competingTxs")

                nnr = {
                    "txid": response_txid,
                    "extraInfo": extra_info,
                    "txStatus": tx_status,
                    "competingTxs": ",".join(competing_txs) if competing_txs else None,
                }

                # Arcade's 202 submit response omits extraInfo; avoid a trailing space.
                result.data = f"{tx_status} {extra_info}".strip()
                if result.txid != response_txid:
                    result.data += f" txid altered from {result.txid} to {response_txid}"
                result.txid = response_txid

                if tx_status in ARCADE_TERMINAL_TX_STATUSES:
                    # An idempotent re-submit returns 202 with the current status,
                    # which can be terminal even though the HTTP status is a success.
                    result.status = "error"
                    if tx_status == "DOUBLE_SPEND_ATTEMPTED":
                        result.double_spend = True
                        result.competing_txs = competing_txs
                    result.notes.append({**nne, **nnr, "what": "postRawTxTerminalStatus"})
                else:
                    result.notes.append({**nn, **nnr, "what": "postRawTxSuccess"})
            else:
                if response.status_code == 429:
                    result.status = "rate_limited"
                    result.rate_limited = True
                else:
                    result.status = "error"

                error_data = PostTxResultForTxidError(status=str(response.status_code))
                result.data = error_data

                note: dict[str, Any] = {**nne, "what": "postRawTxError", "status": response.status_code}
                body: Any = None
                try:
                    body = response.json()
                    if isinstance(body, dict):
                        error_data.more = body
                        error_data.detail = _arcade_error_detail(body)
                        if error_data.detail:
                            note["detail"] = error_data.detail
                except Exception:
                    if response.text:
                        note["data"] = response.text[:128]

                # A 400 "transaction failed validation" is terminal — the tx
                # itself is invalid, so retrying with another provider won't
                # help — unless it only failed Arcade's minimum-fee policy.
                # That, other 400s (invalid callback URL, malformed request),
                # rate limits, backpressure (503) and unknown failures remain
                # service errors so aggregation falls through.
                result.service_error = not (
                    response.status_code == 400
                    and isinstance(body, dict)
                    and body.get("error") == ARCADE_VALIDATION_FAILED_ERROR
                    and not is_fee_policy_rejection(body.get("reason"))
                )

                result.notes.append(note)

        except Exception as e:
            result.status = "error"
            result.service_error = True
            result.data = f"ERROR: {e!s}"
            result.notes.append({**nne, "what": "postRawTxCatch", "error": str(e)})

        return result

    def post_beef(self, beef: Any, txids: list[str]) -> PostBeefResult:
        """Post each txid of interest as Extended Format (EF).

        EF needs each input's source output (satoshis + locking script). A BEEF
        is not guaranteed to contain that data (txidOnly / pruned entries), so
        when EF cannot be built for a txid it is recorded as a (non-terminal)
        service error and cross-provider aggregation falls through to a
        BEEF-capable broadcaster. A hex string that is not BEEF (a bare raw
        tx) cannot provide EF either and is handled the same way.

        Args:
            beef: Beef object, or BEEF / Atomic BEEF hex string (will be parsed).
            txids: Transaction IDs to submit.

        Returns:
            PostBeefResult with per-txid status.

        Reference: Arcade.ts (postBeef)
        """
        result = PostBeefResult(name=self.name, status="success", txid_results=[])

        # BEEF V1 and Atomic BEEF parsing also return the linked subject tx;
        # V1 entries carry no tx_obj, so the subject tx is the only way to EF.
        subject_tx: Any = None
        if isinstance(beef, str):
            from bsv.transaction.beef import parse_beef_ex

            try:
                beef, _, subject_tx = parse_beef_ex(bytes.fromhex(beef))
            except Exception as e:
                # Not BEEF (e.g. a bare raw tx): no source data for EF.
                if not txids:
                    raise
                result.status = "error"
                result.txid_results = [self._ef_build_failed(txid, e) for txid in txids]
                return result

        for txid in txids:
            try:
                if subject_tx is not None and subject_tx.txid() == txid:
                    tx_obj = subject_tx
                else:
                    btx = beef.find_transaction_for_signing(txid)
                    tx_obj = btx.tx_obj if btx is not None else None
                if tx_obj is None:
                    raise ValueError(f"transaction {txid} not found in BEEF")
                ef_hex = tx_obj.to_ef().hex()
            except Exception as e:
                result.status = "error"
                result.txid_results.append(self._ef_build_failed(txid, e))
                continue

            prtr = self.post_raw_tx(ef_hex, [txid])
            result.txid_results.append(prtr)
            if prtr.status != "success":
                result.status = "error"

        return result

    def get_tx_data(self, txid: str) -> ArcMinerGetTxData | None:
        """Query transaction status via ``GET /tx/{txid}``.

        Returns:
            ArcMinerGetTxData with transaction details, or None on error.
        """
        url = f"{self.url}/tx/{txid}"

        try:
            response = requests.get(url, headers=self.request_headers(), timeout=30)
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

    def get_merkle_path(self, txid: str, services: Any) -> dict[str, Any]:
        """Fetch a merkle proof for a mined transaction via ``GET /tx/{txid}``.

        Arcade only has a proof for transactions it tracked that have been
        mined while tracked; for anything else it reports a non-mined status
        (or 404) and this returns no merklePath, so Services.get_merkle_path
        falls through to the other providers.

        Arcade returns the proof as BUMP hex. It is only returned after the
        block header is resolved via ``services.hash_to_header`` and the
        proof's root matches the header's merkle root; otherwise no
        merklePath is returned so the next provider is tried.

        Returns the same shape as other providers:
          {"header": {...}, "merklePath": {"blockHeight", "path"}, "name": "...", "notes": [...]}
        """
        now = datetime.now(UTC).isoformat()
        result: dict[str, Any] = {"name": self.name, "notes": []}

        dr = self.get_tx_data(txid)
        if dr is None:
            result["notes"].append({"name": self.name, "when": now, "what": "getMerklePathNoData"})
            return result

        mined = dr.tx_status in ARCADE_MINED_TX_STATUSES
        if not mined or not dr.merkle_path:
            result["notes"].append(
                {"name": self.name, "when": now, "what": "getMerklePathNoProof", "txStatus": dr.tx_status}
            )
            return result

        try:
            merkle_path = MerklePath.from_hex(dr.merkle_path)
            header = services.hash_to_header(dr.block_hash)
            root = merkle_path.compute_root(txid)
        except Exception as exc:
            result["notes"].append({"name": self.name, "when": now, "what": "getMerklePathNoData", "error": str(exc)})
            return result

        if root != header.get("merkleRoot"):
            result["notes"].append(
                {
                    "name": self.name,
                    "when": now,
                    "what": "getMerklePathRootMismatch",
                    "root": root,
                    "merkleRoot": header.get("merkleRoot"),
                }
            )
            return result

        result["merklePath"] = {"blockHeight": merkle_path.block_height, "path": merkle_path.path}
        result["header"] = header
        result["notes"].append({"name": self.name, "when": now, "what": "getMerklePathSuccess"})
        return result
