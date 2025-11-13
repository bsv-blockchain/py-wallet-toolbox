"""
Bitails provider for blockchain data retrieval and transaction broadcasting.

This module implements the Bitails service provider for wallet-toolbox,
enabling transaction broadcasting via the Bitails API and merkle path retrieval.

Key Features:
    - Transaction broadcasting via BEEF format
    - Raw transaction batch broadcasting
    - Merkle path retrieval with block header integration

Typical Usage:
    from bsv_wallet_toolbox.services.providers.bitails import Bitails

    # Create a Bitails provider instance
    bitails = Bitails(chain='main', config={'api_key': 'your-api-key'})

    # Broadcast transactions
    result = bitails.post_raws(['tx1_hex', 'tx2_hex'], ['txid1', 'txid2'])

Reference Implementation: ts-wallet-toolbox/src/services/providers/Bitails.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import requests

from bsv_wallet_toolbox.utils.random_utils import double_sha256_be


@dataclass
class BitailsConfig:
    """Configuration options for the Bitails provider."""

    api_key: str | None = None
    """Authentication token for Bitails API."""
    headers: dict[str, str] | None = None
    """Additional HTTP headers."""


@dataclass
class BitailsPostRawsResult:
    """Response entry from Bitails broadcast endpoint."""

    txid: str | None = None
    """Transaction ID (may be populated by response or inferred from raw)."""
    error: dict[str, Any] | None = None
    """Error details if broadcast failed (contains 'code' and 'message')."""


@dataclass
class BitailsMerkleProof:
    """Merkle proof response from Bitails."""

    index: int
    """Position in merkle tree."""
    tx_or_id: str
    """Transaction or ID reference."""
    target: str
    """Block hash (root of merkle tree)."""
    nodes: list[str] = field(default_factory=list)
    """Merkle path nodes."""


@dataclass
class ReqHistoryNote:
    """History note entry for tracking operations."""

    name: str
    when: str
    what: str
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class TxidResult:
    """Result entry for individual transaction broadcast."""

    txid: str
    status: str  # 'success' or 'error'
    double_spend: bool = False
    competing_txs: list[str] | None = None
    notes: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PostBeefResult:
    """Result from BEEF broadcasting operation."""

    name: str
    status: str  # 'success' or 'error'
    txid_results: list[TxidResult] = field(default_factory=list)
    notes: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class GetMerklePathResult:
    """Result from merkle path retrieval."""

    name: str
    notes: list[dict[str, Any]] = field(default_factory=list)
    merkle_path: Any | None = None
    header: Any | None = None
    error: Exception | None = None


class Bitails:
    """Bitails blockchain service provider.

    Implements transaction broadcasting and merkle path retrieval via the Bitails API.
    Provides TS-compatible interfaces for wallet-toolbox integration.

    Attributes:
        chain: Blockchain chain ('main' or 'test').
        api_key: API key for Bitails authentication.
        url: API endpoint URL (chain-dependent).
        headers: HTTP headers for requests (includes Accept and Authorization).
    """

    def __init__(
        self,
        chain: str = "main",
        config: BitailsConfig | None = None,
    ) -> None:
        """Initialize Bitails provider.

        Args:
            chain: Blockchain chain ('main' or 'test'). Defaults to 'main'.
            config: Configuration options (api_key, headers).
        """
        self.chain = chain
        config = config or BitailsConfig()

        self.api_key = config.api_key or ""
        self.url = "https://api.bitails.io/" if chain == "main" else "https://test-api.bitails.io/"
        self._default_headers = config.headers or {}

    def get_http_headers(self) -> dict[str, str]:
        """Get HTTP headers for requests.

        Returns headers including Accept and Authorization (if api_key set).

        Returns:
            HTTP headers dictionary.
        """
        headers: dict[str, str] = {
            "Accept": "application/json",
            **self._default_headers,
        }

        if isinstance(self.api_key, str) and self.api_key.strip():
            headers["Authorization"] = self.api_key

        return headers

    def post_beef(self, beef: Any, txids: list[str]) -> PostBeefResult:
        """Broadcast a BEEF (Atomic BEEF or standard BEEF) via Bitails.

        Bitails does not natively support multiple txids of interest in BEEF format.
        This method extracts raw transactions in the requested txid order and broadcasts
        them via the postRaws endpoint.

        Args:
            beef: BEEF object with find_transaction() method.
            txids: List of transaction IDs to broadcast.

        Returns:
            PostBeefResult containing broadcast status and per-txid results.

        Reference: Bitails.ts (postBeef)
        """

        def make_note(name: str, when: str) -> dict[str, str]:
            return {"name": name, "when": when}

        def make_note_extended(name: str, when: str, beef_hex: str, txids_str: str) -> dict[str, Any]:
            return {"name": name, "when": when, "beef": beef_hex, "txids": txids_str}

        now = datetime.utcnow().isoformat()
        nn = make_note("BitailsPostBeef", now)
        beef_hex = beef.to_hex() if hasattr(beef, "to_hex") else ""
        txids_str = ",".join(txids)
        nne = make_note_extended("BitailsPostBeef", now, beef_hex, txids_str)

        note: dict[str, Any] = {**nn, "what": "postBeef"}

        # Extract raw transactions from BEEF in txids order
        raws: list[str] = []
        for txid in txids:
            beef_tx = beef.find_transaction(txid)
            if beef_tx and hasattr(beef_tx, "tx_bytes"):
                raw_tx = beef_tx.tx_bytes.hex() if isinstance(beef_tx.tx_bytes, bytes) else beef_tx.tx_bytes
                raws.append(raw_tx)

        # Delegate to postRaws
        result = self.post_raws(raws, txids)

        # Prepend postBeef note to results
        result.notes.insert(0, note)
        if result.status != "success":
            result.notes.append({**nne, "what": "postBeefError"})
        else:
            result.notes.append({**nn, "what": "postBeefSuccess"})

        return result

    def post_raws(
        self,
        raws: list[str],
        txids: list[str] | None = None,
    ) -> PostBeefResult:
        """Broadcast raw transactions via Bitails.

        Args:
            raws: Array of raw transactions as hex strings.
            txids: Array of txids for which results are requested.
                   Remaining raws are treated as supporting transactions only.

        Returns:
            PostBeefResult with per-txid status.

        Reference: Bitails.ts (postRaws)
        """
        result = PostBeefResult(
            name="BitailsPostRaws",
            status="success",
            txid_results=[],
            notes=[],
        )

        raw_txids: list[str] = []

        # Pre-compute txids from raw transactions
        for raw in raws:
            # Decode hex to bytes and compute SHA256(SHA256)
            raw_bytes = bytes.fromhex(raw)
            txid = double_sha256_be(raw_bytes).hex()
            raw_txids.append(txid)

            # Pre-populate results for requested txids
            if not txids or txid in txids:
                result.txid_results.append(TxidResult(txid=txid, status="success", notes=[]))

        # Prepare HTTP request
        headers = self.get_http_headers()
        headers["Content-Type"] = "application/json"

        data = {"raws": raws}
        url = f"{self.url}tx/broadcast/multi"

        now = datetime.utcnow().isoformat()

        def make_note_post(name: str, when: str) -> dict[str, str]:
            return {"name": name, "when": when}

        def make_note_extended_post(name: str, when: str) -> dict[str, Any]:
            return {
                "name": name,
                "when": when,
                "raws": ",".join(raws),
                "txids": ",".join(rt.txid for rt in result.txid_results),
                "url": url,
            }

        nn_post = make_note_post("BitailsPostRawTx", now)
        nne_post = make_note_extended_post("BitailsPostRawTx", now)

        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)

            if response.status_code in (200, 201):
                # Parse response as list of BitailsPostRawsResult
                btrs_data = response.json()
                if not isinstance(btrs_data, list):
                    btrs_data = [btrs_data]

                if len(btrs_data) != len(raws):
                    result.status = "error"
                    result.notes.append({**nne_post, "what": "postRawsErrorResultsCount"})
                else:
                    # Check txid matching
                    for i, btr_data in enumerate(btrs_data):
                        btr = BitailsPostRawsResult(**btr_data) if isinstance(btr_data, dict) else btr_data
                        if not btr.txid:
                            btr.txid = raw_txids[i]
                            result.notes.append(
                                {
                                    **nn_post,
                                    "what": "postRawsResultMissingTxids",
                                    "i": i,
                                    "rawsTxid": raw_txids[i],
                                }
                            )
                        elif btr.txid != raw_txids[i]:
                            result.status = "error"
                            result.notes.append(
                                {
                                    **nn_post,
                                    "what": "postRawsResultTxids",
                                    "i": i,
                                    "txid": btr.txid,
                                    "rawsTxid": raw_txids[i],
                                }
                            )

                    if result.status == "success":
                        # Process results for requested txids
                        for rt in result.txid_results:
                            btr = next(
                                (
                                    BitailsPostRawsResult(**b) if isinstance(b, dict) else b
                                    for b in btrs_data
                                    if (isinstance(b, dict) and b.get("txid") == rt.txid)
                                    or (hasattr(b, "txid") and b.txid == rt.txid)
                                ),
                                None,
                            )
                            if not btr:
                                continue

                            if btr.error:
                                code = btr.error.get("code")
                                message = btr.error.get("message")
                                if code == -27:  # already-in-mempool
                                    rt.notes.append(
                                        {
                                            **nne_post,
                                            "what": "postRawsSuccessAlreadyInMempool",
                                        }
                                    )
                                else:
                                    rt.status = "error"
                                    if code == -25:  # missing-inputs
                                        rt.double_spend = True
                                        rt.competing_txs = None
                                        rt.notes.append(
                                            {
                                                **nne_post,
                                                "what": "postRawsErrorMissingInputs",
                                            }
                                        )
                                    elif isinstance(code, str) and code == "ECONNRESET":
                                        rt.notes.append(
                                            {
                                                **nne_post,
                                                "what": "postRawsErrorECONNRESET",
                                                "txid": rt.txid,
                                                "message": message,
                                            }
                                        )
                                    else:
                                        rt.notes.append(
                                            {
                                                **nne_post,
                                                "what": "postRawsError",
                                                "txid": rt.txid,
                                                "code": code,
                                                "message": message,
                                            }
                                        )
                            else:
                                rt.notes.append({**nn_post, "what": "postRawsSuccess"})

                            if rt.status != "success" and result.status == "success":
                                result.status = "error"
            else:
                result.status = "error"
                result.notes.append({**nne_post, "what": "postRawsError", "status": response.status_code})

        except Exception as e:
            result.status = "error"
            result.notes.append(
                {
                    **nne_post,
                    "what": "postRawsCatch",
                    "error": str(e),
                }
            )

        return result

    def get_merkle_path(self, txid: str, services: Any) -> GetMerklePathResult:
        """Retrieve merkle path for a transaction.

        Queries Bitails for a TSC (Transaction Space Commitment) proof and converts
        it to a MerklePath using wallet-toolbox utilities.

        Args:
            txid: Transaction ID to retrieve merkle path for.
            services: WalletServices instance for header lookup.

        Returns:
            GetMerklePathResult with merkle path and header information.

        Reference: Bitails.ts (getMerklePath)
        """
        result = GetMerklePathResult(name="BitailsTsc", notes=[])

        url = f"{self.url}tx/{txid}/proof/tsc"
        now = datetime.utcnow().isoformat()

        def make_note_merkle(name: str, when: str, txid_val: str, url_val: str) -> dict[str, Any]:
            return {"name": name, "when": when, "txid": txid_val, "url": url_val}

        nn_merkle = make_note_merkle("BitailsProofTsc", now, txid, url)

        headers = self.get_http_headers()

        try:
            response = requests.get(url, headers=headers, timeout=30)

            def make_note_extended_merkle() -> dict[str, Any]:
                return {
                    **nn_merkle,
                    "txid": txid,
                    "url": url,
                    "status": response.status_code,
                    "statusText": response.reason,
                }

            nne_merkle = make_note_extended_merkle()

            if response.status_code == 404:
                result.notes.append({**nn_merkle, "what": "getMerklePathNotFound"})
            elif response.status_code != 200:
                result.notes.append({**nne_merkle, "what": "getMerklePathBadStatus"})
            elif not response.content:
                result.notes.append({**nne_merkle, "what": "getMerklePathNoData"})
            else:
                proof_data = response.json()
                proof = BitailsMerkleProof(
                    index=proof_data.get("index"),
                    tx_or_id=proof_data.get("txOrId"),
                    target=proof_data.get("target"),
                    nodes=proof_data.get("nodes", []),
                )

                # Get header from services
                header = services.hash_to_header(proof.target) if hasattr(services, "hash_to_header") else None
                if header:
                    # Note: Full merkle path conversion via convert_proof_to_merkle_path()
                    # is pending py-sdk MerklePath integration. Current implementation
                    # provides compatible structure with core fields (index, nodes, height).
                    result.merkle_path = {
                        "index": proof.index,
                        "nodes": proof.nodes,
                        "height": header.get("height") if isinstance(header, dict) else getattr(header, "height", None),
                    }
                    result.header = header
                    result.notes.append({**nne_merkle, "what": "getMerklePathSuccess"})
                else:
                    result.notes.append({**nne_merkle, "what": "getMerklePathNoHeader", "target": proof.target})

        except Exception as e:
            result.error = e
            result.notes.append(
                {
                    **nn_merkle,
                    "what": "getMerklePathCatch",
                    "error": str(e),
                }
            )

        return result
