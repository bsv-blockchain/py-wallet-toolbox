"""AuthFetch - Authenticated HTTP client for BSV wallet operations.

Provides BRC-104 compliant authenticated HTTP requests using wallet-based authentication.
This module wraps py-sdk's AuthFetch implementation.

Reference:
  - py-sdk/bsv/auth/clients/auth_fetch.py
  - wallet-toolbox/src/storage/remoting/StorageClient.ts
"""

from __future__ import annotations

import inspect
import json
import logging
import traceback
from collections.abc import Mapping
from contextlib import contextmanager
from typing import Any
from urllib.parse import urlparse

# Re-export from py-sdk for full BRC-104 authentication
from bsv.auth.clients.auth_fetch import (
    AuthFetch as _AuthFetch,
)
from bsv.auth.clients.auth_fetch import (
    AuthPeer,
    SimplifiedFetchRequestOptions,
    p2pkh_locking_script_from_pubkey,
)
from bsv.auth.requested_certificate_set import RequestedCertificateSet
from bsv.auth.session_manager import DefaultSessionManager
from bsv.keys import PublicKey

logger = logging.getLogger(__name__)


def _short(value: Any, keep: int = 16) -> str:
    """Short, low-risk string for logs (avoid dumping secrets)."""
    if value is None:
        return "None"
    try:
        s = str(value)
    except Exception:
        return "<unprintable>"
    if len(s) <= keep:
        return s
    return f"{s[:keep]}…({len(s)})"


def _short_bytes(data: Any, keep: int = 32) -> str:
    if not data:
        return ""
    if isinstance(data, (bytes, bytearray)):
        b = bytes(data)
        hx = b.hex()
        return _short(hx, keep=keep)
    return _short(data, keep=keep)


def _to_debug_str(value: Any) -> Any:
    """Best-effort JSON-safe conversion for debug logging."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (bytes, bytearray)):
        b = bytes(value)
        return {"type": "bytes", "len": len(b), "hex": b.hex()}
    if isinstance(value, list):
        return [_to_debug_str(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _to_debug_str(v) for k, v in value.items()}
    if hasattr(value, "hex") and callable(value.hex):
        try:
            return {"type": type(value).__name__, "hex": value.hex()}
        except Exception:
            pass
    return {"type": type(value).__name__, "repr": repr(value)}


def _auth_trace(event: str, **fields: Any) -> None:
    """One-line JSON debug logs to diagnose auth in a single run."""
    if not logger.isEnabledFor(logging.DEBUG):
        return
    payload = {"event": event, **{k: _to_debug_str(v) for k, v in fields.items()}}
    logger.debug("AUTH_TRACE %s", json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True))


def _headers_to_dict(headers: Any) -> dict[str, Any]:
    """Best-effort conversion of headers to a plain dict for tracing/logging."""
    if headers is None:
        return {}
    if isinstance(headers, dict):
        return dict(headers)
    if isinstance(headers, Mapping):
        return {str(k): v for k, v in headers.items()}
    if hasattr(headers, "items"):
        try:
            return {str(k): v for k, v in headers.items()}
        except Exception:  # pragma: no cover - defensive fallback
            pass
    try:
        return dict(headers)
    except Exception:  # pragma: no cover - defensive fallback
        return {}


def _normalize_requested_certificates(requested: Any) -> dict[str, Any]:
    """Normalize requestedCertificates into a JSON-serializable dict.

    Go expects requestedCertificates to be an object (utils.RequestedCertificateSet),
    but py-sdk transport serializes using json.dumps(..., default=str). If we pass a
    non-JSON-serializable Python object, it can silently become a string and cause
    Go unmarshaling to fail (exactly the 400 you saw).
    """
    if requested is None:
        return {"certifiers": [], "certificateTypes": {}}

    if isinstance(requested, RequestedCertificateSet):
        return requested.to_json_dict()

    if isinstance(requested, dict):
        certifiers = requested.get("certifiers") or []
        certificate_types = (
            requested.get("certificateTypes") or requested.get("certificateTypes") or requested.get("types") or {}
        )
        return {"certifiers": certifiers, "certificateTypes": certificate_types}

    # Avoid passing unknown objects through to py-sdk (they would become a string).
    return {"certifiers": [], "certificateTypes": {}}


@contextmanager
def _patch_requests_for_auth_interop(debug: bool) -> Any:
    """Monkey-patch requests for BRC-104 auth interop without modifying py-sdk.

    - Adds DEBUG logs for `/.well-known/auth` when debug=True
    - Normalizes Go server JSON response fields when they differ from py-sdk expectations

    This is scoped to a single fetch call.
    """
    import requests

    original_request = requests.sessions.Session.request
    last_client_nonce_by_base_url: dict[str, str] = {}

    def wrapped_request(self, method: str, url: str, **kwargs: Any):  # type: ignore[no-untyped-def]
        # NOTE: Avoid dumping sensitive values by default.
        parsed = urlparse(url)
        is_auth = parsed.path.rstrip("/") == "/.well-known/auth"
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        headers = kwargs.get("headers") or {}
        is_general_auth = bool(headers) and any(str(k).lower().startswith("x-bsv-auth-") for k in headers)

        if is_auth:
            data = kwargs.get("data")
            if debug:
                logger.debug(
                    "AuthHTTP -> %s %s headers_count=%s body_size=%s",
                    method,
                    url,
                    len(headers),
                    (
                        len(data or b"")
                        if isinstance(data, (bytes, bytearray))
                        else (len(str(data)) if data is not None else 0)
                    ),
                )
            _auth_trace("http.auth.request", method=method, url=url, headers=headers, body=data)

            try:
                # Try decode JSON keys only; avoid printing full values.
                if isinstance(data, (bytes, bytearray)):
                    payload = json.loads(bytes(data).decode("utf-8"))
                elif isinstance(data, str):
                    payload = json.loads(data)
                else:
                    payload = None
                if isinstance(payload, dict):
                    msg_type = payload.get("messageType")
                    # Track client nonce for interop fixups. py-sdk uses initialNonce for initialRequest.
                    if msg_type == "initialRequest":
                        client_nonce = payload.get("initialNonce") or payload.get("nonce")
                        if isinstance(client_nonce, str) and client_nonce:
                            last_client_nonce_by_base_url[base_url] = client_nonce

                    if debug:
                        logger.debug("AuthHTTP request json keys=%s", sorted(payload.keys()))
                        # Show minimal identityKey hint (public) and nonce lengths (not values)
                        ik = payload.get("identityKey")
                        nonce = payload.get("nonce")
                        init_nonce = payload.get("initialNonce")
                        logger.debug(
                            "AuthHTTP request hints: identityKey=%s nonce_len=%s initialNonce_len=%s msgType=%s version=%s",
                            _short(ik),
                            len(nonce) if isinstance(nonce, str) else None,
                            len(init_nonce) if isinstance(init_nonce, str) else None,
                            msg_type,
                            payload.get("version"),
                        )
                    _auth_trace(
                        "auth.message.request",
                        url=url,
                        messageType=payload.get("messageType"),
                        payload=payload,
                    )
            except Exception:
                if debug:
                    logger.debug("AuthHTTP request decode failed:\n%s", traceback.format_exc())
                _auth_trace("auth.message.request.decode_error", url=url, error=traceback.format_exc())

        resp = original_request(self, method, url, **kwargs)

        if is_auth:
            # Try to normalize response fields for py-sdk compatibility:
            # py-sdk Peer.handle_initial_response requires yourNonce and initialNonce.
            # Some Go servers may respond with only nonce + signature + identityKey.
            try:
                raw_text = resp.text or ""
                obj = json.loads(raw_text) if raw_text else None
                if isinstance(obj, dict):
                    msg_type = obj.get("messageType")
                    if msg_type == "initialResponse":
                        # If missing, infer:
                        # - yourNonce should be the client's initial nonce from initialRequest
                        # - initialNonce should be the server session nonce (often provided as `nonce`)
                        if not obj.get("yourNonce"):
                            client_nonce = last_client_nonce_by_base_url.get(base_url, "")
                            if client_nonce:
                                obj["yourNonce"] = client_nonce
                        if not obj.get("initialNonce") and obj.get("nonce"):
                            obj["initialNonce"] = obj.get("nonce")
                        # Re-encode into response content so py-sdk sees the normalized shape.
                        resp._content = json.dumps(obj).encode("utf-8")

                    if debug:
                        logger.debug(
                            "AuthHTTP <- %s %s status=%s content_type=%s json_keys=%s msgType=%s",
                            method,
                            url,
                            resp.status_code,
                            resp.headers.get("Content-Type"),
                            sorted(obj.keys()),
                            msg_type,
                        )
                    _auth_trace(
                        "http.auth.response",
                        method=method,
                        url=url,
                        status=resp.status_code,
                        headers=dict(resp.headers),
                        body=obj,
                    )
            except Exception:
                if debug:
                    text = ""
                    try:
                        text = resp.text or ""
                    except Exception:
                        text = ""
                    logger.debug(
                        "AuthHTTP <- %s %s status=%s content_type=%s body=%s",
                        method,
                        url,
                        resp.status_code,
                        resp.headers.get("Content-Type"),
                        _short(text, keep=400),
                    )
                _auth_trace(
                    "http.auth.response.decode_error",
                    method=method,
                    url=url,
                    status=getattr(resp, "status_code", None),
                    headers=dict(getattr(resp, "headers", {}) or {}),
                    body=getattr(resp, "text", None),
                    error=traceback.format_exc(),
                )
        elif is_general_auth and debug:
            # Log outgoing auth headers for signature debugging (truncate sensitive values).
            sig = headers.get("x-bsv-auth-signature") or headers.get("X-Bsv-Auth-Signature")
            nonce = headers.get("x-bsv-auth-nonce") or headers.get("X-Bsv-Auth-Nonce")
            your_nonce = headers.get("x-bsv-auth-your-nonce") or headers.get("X-Bsv-Auth-Your-Nonce")
            ident = headers.get("x-bsv-auth-identity-key") or headers.get("X-Bsv-Auth-Identity-Key")
            req_id = headers.get("x-bsv-auth-request-id") or headers.get("X-Bsv-Auth-Request-Id")
            body_bytes = kwargs.get("data")
            body_size = len(body_bytes) if isinstance(body_bytes, (bytes, bytearray)) else None
            logger.debug(
                "AuthHTTP(general) -> %s %s identityKey=%s nonce_len=%s yourNonce_len=%s requestId=%s signature=%s body_size=%s",
                method,
                url,
                _short(ident),
                len(nonce) if isinstance(nonce, str) else None,
                len(your_nonce) if isinstance(your_nonce, str) else None,
                _short(req_id),
                _short(sig, keep=24),
                body_size,
            )
            _auth_trace("http.general.request", method=method, url=url, headers=headers, body=kwargs.get("data"))
        return resp

    requests.sessions.Session.request = wrapped_request  # type: ignore[assignment]
    try:
        yield
    finally:
        requests.sessions.Session.request = original_request  # type: ignore[assignment]


class WalletAdapter:
    """Adapter to convert py-wallet-toolbox Wallet to py-sdk compatible interface.

    py-sdk's Peer expects wallet methods to return objects with specific attributes,
    while py-wallet-toolbox's Wallet returns dictionaries.

    This adapter converts:
    - get_public_key: dict -> object with public_key attribute
    - create_signature: dict -> object with signature attribute
    """

    def __init__(self, wallet: Any):
        self._wallet = wallet

    def get_public_key(self, args: dict[str, Any], originator: str = "") -> Any:
        """Convert dict response to object with public_key attribute."""
        _auth_trace("wallet.get_public_key.call", originator=originator, args=args)
        result = self._wallet.get_public_key(args, originator)
        _auth_trace("wallet.get_public_key.result", originator=originator, result=result)

        if isinstance(result, dict):
            pub_key_hex = result.get("publicKey")
            if pub_key_hex:
                # Create an object with the expected attributes
                class PublicKeyResult:
                    def __init__(self, hex_key: str):
                        self.publicKey = hex_key
                        self.public_key = PublicKey(hex_key)
                        self.hex = hex_key

                return PublicKeyResult(pub_key_hex)

        return result

    def create_signature(self, args: dict[str, Any], originator: str = "") -> Any:
        """Convert dict response to object with signature attribute.

        Also transforms py-sdk's encryption_args format to py-wallet-toolbox's flat format.
        """
        _auth_trace("wallet.create_signature.call", originator=originator, args=args)
        # Transform encryption_args to flat format
        enc_args = args.get("encryptionArgs", {})
        if enc_args:
            # Extract protocolID using standardized key
            protocol_id = enc_args.get("protocolID", {})
            if isinstance(protocol_id, dict):
                security_level = protocol_id.get("securityLevel", 2)
                protocol = protocol_id.get("protocol", "auth")
                protocol_id_list = [security_level, protocol]
            else:
                protocol_id_list = protocol_id

            # Extract counterparty
            counterparty_arg = enc_args.get("counterparty")
            counterparty_hex = None
            if isinstance(counterparty_arg, dict):
                cp_value = counterparty_arg.get("counterparty")
                if cp_value:
                    if hasattr(cp_value, "hex"):
                        counterparty_hex = cp_value.hex()
                    elif isinstance(cp_value, str):
                        counterparty_hex = cp_value
            elif counterparty_arg:
                if hasattr(counterparty_arg, "hex"):
                    counterparty_hex = counterparty_arg.hex()
                else:
                    counterparty_hex = str(counterparty_arg)

            # Build flat args for py-wallet-toolbox
            args = {
                "protocolID": protocol_id_list,
                "keyID": enc_args.get("keyID", "1"),
                "counterparty": counterparty_hex,
                "data": args.get("data"),
            }

        result = self._wallet.create_signature(args, originator)
        _auth_trace("wallet.create_signature.result", originator=originator, result=result)

        if isinstance(result, dict):
            signature = result.get("signature")
            if signature:

                class SignatureResult:
                    def __init__(self, sig: bytes):
                        self.signature = sig

                return SignatureResult(signature)

        return result

    def create_action(self, args: dict[str, Any], originator: str = "") -> Any:
        """Pass through to wallet's create_action."""
        return self._wallet.create_action(args, originator)

    def create_hmac(self, args: dict[str, Any], originator: str = "") -> Any:
        """Convert encryption_args format for create_hmac.

        py-sdk uses:
            encryption_args.protocol_id OR encryption_args.protocolID
              = {securityLevel: 1, protocol: 'server hmac'}
            encryption_args.key_id OR encryption_args.keyID = string
            encryption_args.counterparty = {type: 1}  (ANYONE)  etc.

        py-wallet-toolbox expects:
            protocolID = [securityLevel, protocol]
            keyID = string
            counterparty = 'anyone' or hex_string
        """
        _auth_trace("wallet.create_hmac.call", originator=originator, args=args)
        enc_args = args.get("encryptionArgs", {})
        data = args.get("data")

        if enc_args:
            # Extract protocolID
            protocol_id = enc_args.get("protocolID", {})
            if isinstance(protocol_id, dict):
                security_level = protocol_id.get("securityLevel", 1)
                protocol = protocol_id.get("protocol", "server hmac")
                protocol_id_list = [security_level, protocol]
            else:
                protocol_id_list = protocol_id

            # Extract counterparty - for create_nonce it's {type: 1} which means ANYONE
            counterparty_arg = enc_args.get("counterparty")
            if isinstance(counterparty_arg, dict):
                cp_type = counterparty_arg.get("type", 1)
                if cp_type == 1:  # ANYONE
                    counterparty = "anyone"
                else:
                    cp_value = counterparty_arg.get("counterparty")
                    if hasattr(cp_value, "hex"):
                        counterparty = cp_value.hex()
                    else:
                        counterparty = cp_value
            else:
                counterparty = counterparty_arg

            # Build flat args for py-wallet-toolbox Wallet (BRC-100)
            args = {
                "protocolID": protocol_id_list,
                "keyID": enc_args.get("keyID", ""),
                "counterparty": counterparty,
                # Wallet.create_hmac accepts bytes/bytearray; keep bytes as-is.
                "data": data,
            }

        result = self._wallet.create_hmac(args, originator)
        _auth_trace("wallet.create_hmac.result", originator=originator, result=result)

        # Convert hmac list back to bytes for py-sdk compatibility
        if isinstance(result, dict) and "hmac" in result:
            hmac_value = result["hmac"]
            if isinstance(hmac_value, list):
                result["hmac"] = bytes(hmac_value)

        return result

    def verify_hmac(self, args: dict[str, Any], originator: str = "") -> Any:
        """Convert encryption_args format for verify_hmac."""
        _auth_trace("wallet.verify_hmac.call", originator=originator, args=args)
        enc_args = args.get("encryptionArgs", {})
        data = args.get("data")
        hmac_value = args.get("hmac")

        if enc_args:
            protocol_id = enc_args.get("protocolID", {})
            if isinstance(protocol_id, dict):
                security_level = protocol_id.get("securityLevel", 1)
                protocol = protocol_id.get("protocol", "server hmac")
                protocol_id_list = [security_level, protocol]
            else:
                protocol_id_list = protocol_id

            counterparty_arg = enc_args.get("counterparty")
            if isinstance(counterparty_arg, dict):
                cp_type = counterparty_arg.get("type", 1)
                if cp_type == 1:
                    counterparty = "anyone"
                else:
                    cp_value = counterparty_arg.get("counterparty")
                    if hasattr(cp_value, "hex"):
                        counterparty = cp_value.hex()
                    else:
                        counterparty = cp_value
            else:
                counterparty = counterparty_arg

            args = {
                "protocolID": protocol_id_list,
                "keyID": enc_args.get("keyID", ""),
                "counterparty": counterparty,
                # Wallet.verify_hmac accepts bytes/bytearray; keep bytes as-is.
                "data": data,
                "hmac": hmac_value,
            }

        result = self._wallet.verify_hmac(args, originator)
        _auth_trace("wallet.verify_hmac.result", originator=originator, result=result)
        return result

    def verify_signature(self, args: dict[str, Any], originator: str = "") -> Any:
        """Convert encryption_args format for verify_signature.

        py-sdk uses:
            encryption_args.protocol_id = {securityLevel: 2, protocol: 'auth'}
            encryption_args.key_id = 'nonce1 nonce2'
            encryption_args.counterparty = {type: 3, counterparty: PublicKey}

        py-wallet-toolbox expects:
            protocolID = [securityLevel, protocol]
            keyID = 'nonce1 nonce2'
            counterparty = hex_string
        """
        _auth_trace("wallet.verify_signature.call", originator=originator, args=args)
        enc_args = args.get("encryptionArgs", {})
        data = args.get("data")
        signature = args.get("signature")

        if enc_args:
            protocol_id = enc_args.get("protocolID", {})
            if isinstance(protocol_id, dict):
                security_level = protocol_id.get("securityLevel", 2)
                protocol = protocol_id.get("protocol", "auth")
                protocol_id_list = [security_level, protocol]
            else:
                protocol_id_list = protocol_id

            counterparty_arg = enc_args.get("counterparty")
            counterparty_hex = None
            if isinstance(counterparty_arg, dict):
                cp_value = counterparty_arg.get("counterparty")
                if cp_value:
                    if hasattr(cp_value, "hex"):
                        counterparty_hex = cp_value.hex()
                    elif isinstance(cp_value, str):
                        counterparty_hex = cp_value
            elif counterparty_arg:
                if hasattr(counterparty_arg, "hex"):
                    counterparty_hex = counterparty_arg.hex()
                else:
                    counterparty_hex = str(counterparty_arg)

            # Convert signature to list if needed
            if isinstance(signature, bytes):
                signature = list(signature)

            args = {
                "protocolID": protocol_id_list,
                "keyID": enc_args.get("keyID", "1"),
                "counterparty": counterparty_hex,
                "data": list(data) if isinstance(data, bytes) else data,
                "signature": signature,
            }

        result = self._wallet.verify_signature(args, originator)
        _auth_trace("wallet.verify_signature.result", originator=originator, result=result)

        # Convert result to object with valid attribute
        if isinstance(result, dict):

            class VerifyResult:
                def __init__(self, valid: bool):
                    self.valid = valid

            return VerifyResult(result.get("valid", False))

        return result

    def __getattr__(self, name: str) -> Any:
        """Forward any other attribute access to the underlying wallet."""
        return getattr(self._wallet, name)


class AuthFetch:
    """Authenticated HTTP client using py-sdk BRC-104 implementation.

    This class wraps py-sdk's AuthFetch to provide authenticated HTTP requests
    for BSV wallet operations, following the same pattern as TypeScript StorageClient.

    Reference: wallet-toolbox/src/storage/remoting/StorageClient.ts

    Usage:
        >>> from bsv_wallet_toolbox import AuthFetch, Wallet
        >>> wallet = Wallet(...)
        >>> auth_client = AuthFetch(wallet)
        >>> response = auth_client.fetch("https://api.example.com/data", options)
    """

    def __init__(
        self,
        wallet: Any,
        requested_certificates: RequestedCertificateSet | None = None,
        session_manager: DefaultSessionManager | None = None,
    ):
        """Initialize AuthFetch.

        Args:
            wallet: Wallet instance implementing BRC-100 WalletInterface.
                    Must have get_public_key(), create_signature(), and create_action() methods.
            requested_certificates: Optional certificate requirements for mutual auth.
            session_manager: Optional session manager for auth sessions (defaults to DefaultSessionManager).
        """
        # Wrap wallet in adapter to convert response formats
        adapted_wallet = WalletAdapter(wallet)

        # Ensure Go-compatible shape for requestedCertificates.
        normalized_requested = _normalize_requested_certificates(requested_certificates)

        self._impl = _AuthFetch(
            wallet=adapted_wallet,
            requested_certs=normalized_requested,
            session_manager=session_manager,
        )

    async def fetch(
        self,
        url: str,
        config: SimplifiedFetchRequestOptions | None = None,
    ):
        """Make authenticated HTTP request.

        Handles BRC-104 mutual authentication and 402 Payment Required responses
        automatically when the wallet supports create_action().

        Args:
            url: Request URL
            config: Request options (method, headers, body)

        Returns:
            requests.Response object

        Raises:
            Exception: On request failure or authentication error
        """
        method = config.method if config else "GET"
        headers = getattr(config, "headers", None) if config else None
        body = getattr(config, "body", None) if config else None
        logger.debug(
            "AuthFetch.fetch called: url=%s method=%s headers_count=%s body_size=%s",
            url,
            method,
            len(headers or {}),
            len(body or b""),
        )

        try:
            # Always enable interop shim (logging only when DEBUG).
            with _patch_requests_for_auth_interop(debug=logger.isEnabledFor(logging.DEBUG)):
                # py-sdk AuthFetch.fetch can be sync or async depending on installed version.
                # Support both to avoid "object Response can't be used in 'await' expression".
                maybe = self._impl.fetch(url, config)
                response = await maybe if inspect.isawaitable(maybe) else maybe
            headers_val = getattr(response, "headers", None)
            headers_dict = _headers_to_dict(headers_val)
            _auth_trace(
                "auth_fetch.response",
                url=url,
                status=getattr(response, "status_code", None),
                headers=headers_dict,
                body=getattr(response, "text", None),
            )
            logger.debug("AuthFetch.fetch succeeded: status=%s", response.status_code)
            return response
        except Exception as e:
            # NOTE: the root cause often lives inside py-sdk's Peer/Transport layer.
            logger.error(
                "AuthFetch.fetch failed: %s (%s) url=%s method=%s",
                e,
                type(e).__name__,
                url,
                method,
            )
            _auth_trace("auth_fetch.error", url=url, method=method, error=str(e), exc_type=type(e).__name__)
            logger.debug("AuthFetch.fetch traceback:\n%s", traceback.format_exc())

            # Show peer map keys to confirm base_url parsing and reuse.
            try:
                impl_peers = getattr(self._impl, "peers", {}) or {}
                logger.debug("AuthFetch peers: count=%d keys=%s", len(impl_peers), list(impl_peers.keys()))
                for base_url, auth_peer in impl_peers.items():
                    supports_mutual = getattr(auth_peer, "supports_mutual_auth", None)
                    identity_key = getattr(auth_peer, "identity_key", "")
                    peer_obj = getattr(auth_peer, "peer", None)
                    logger.debug(
                        "AuthFetch peer: base_url=%s supports_mutual_auth=%s identity_key=%s peer_type=%s",
                        base_url,
                        supports_mutual,
                        _short(identity_key),
                        type(peer_obj).__name__ if peer_obj is not None else "None",
                    )
            except Exception:
                logger.debug("AuthFetch peers debug failed:\n%s", traceback.format_exc())
            raise

    def send_certificate_request(
        self,
        base_url: str,
        certificates_to_request: Any,
    ):
        """Request certificates from a peer.

        Args:
            base_url: Base URL of the peer
            certificates_to_request: Certificate requirements

        Returns:
            List of received certificates
        """
        return self._impl.send_certificate_request(base_url, certificates_to_request)

    def consume_received_certificates(self):
        """Consume and return certificates received during fetch operations.

        Returns:
            List of VerifiableCertificate objects received since last call
        """
        return self._impl.consume_received_certificates()

    @property
    def certificates_received(self):
        """Access list of received certificates."""
        return self._impl.certificates_received

    @property
    def peers(self):
        """Access peer connections."""
        return self._impl.peers


# Re-export for convenience
__all__ = [
    "AuthFetch",
    "AuthPeer",
    "DefaultSessionManager",
    "RequestedCertificateSet",
    "SimplifiedFetchRequestOptions",
    "p2pkh_locking_script_from_pubkey",
]
