"""
Views for wallet_app.

This module provides JSON-RPC endpoints for BRC-100 wallet operations.

Equivalent to TypeScript: ts-wallet-toolbox/src/storage/remoting/StorageServer.ts

When BSV authentication is enabled via py-middleware, the identity key
verification is handled automatically by the middleware. The views can
access authenticated identity via request.auth.identity_key.

BRC-104 Authentication:
- /.well-known/auth endpoint handles initialRequest/initialResponse handshake
- General messages use x-bsv-auth-* headers for authentication
"""

import json
import logging

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .services import get_server_wallet, get_storage_server

logger = logging.getLogger(__name__)


class BytesEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles bytes objects."""

    def default(self, obj):
        if isinstance(obj, bytes):
            # Convert bytes to list of integers (matching TypeScript behavior)
            return list(obj)
        return super().default(obj)


def _get_authenticated_identity(request: HttpRequest) -> str | None:
    """
    Get authenticated identity key from request.

    When py-middleware BSVAuthMiddleware is enabled, it sets request.auth
    with the authenticated identity information.

    Returns:
        Identity key string if authenticated, None otherwise
    """
    if hasattr(request, "auth") and hasattr(request.auth, "identity_key"):
        identity_key = request.auth.identity_key
        if identity_key and identity_key != "unknown":
            return identity_key
    return None


def _extract_identity_key_from_params(params) -> str:
    """
    Extract identity key from JSON-RPC params.

    Params can be either:
    - dict: {"auth": {"identityKey": "..."}, "args": {...}}
    - list: [auth_dict, args_dict, ...]
    """
    if isinstance(params, dict):
        auth = params.get("auth", {})
        if isinstance(auth, dict):
            return auth.get("identityKey") or auth.get("identity_key", "")
    elif isinstance(params, list) and len(params) > 0:
        auth = params[0]
        if isinstance(auth, dict):
            return auth.get("identityKey") or auth.get("identity_key", "")
    return ""


def _is_brc104_general_message(request: HttpRequest) -> bool:
    """
    Check if the request is a BRC-104 general message.

    BRC-104 general messages have x-bsv-auth-* headers indicating
    they contain authenticated HTTP requests as binary payloads.
    """
    version_header = request.headers.get("x-bsv-auth-version")
    message_type_header = request.headers.get("x-bsv-auth-message-type")
    return version_header is not None and message_type_header == "general"


def _deserialize_http_request_from_payload(payload: bytes) -> tuple[bytes, str, str, str, dict, bytes]:
    """
    Deserialize HTTP request from BRC-104 binary payload.

    Reference:
    - ts-sdk/src/auth/transports/SimplifiedFetchTransport.ts:deserializeRequestPayload
    - go-sdk/auth/authpayload/http.go:ToHTTPRequest
    - py-sdk/bsv/auth/transports/simplified_http_transport.py:_deserialize_request_payload

    Returns: (request_id_bytes, method, path, search, headers, body)
    """
    from bsv.utils.reader import Reader

    reader = Reader(payload)

    # Read request ID (32 bytes)
    request_id_bytes = reader.read_bytes(32)
    if len(request_id_bytes) != 32:
        raise ValueError(f"Invalid request ID length: {len(request_id_bytes)}, expected 32")

    NEG_ONE = 0xFFFFFFFFFFFFFFFF

    # Read method
    method_length = reader.read_var_int_num()
    if method_length is None or method_length == 0 or method_length == NEG_ONE:
        method = "GET"
    else:
        method_bytes = reader.read_bytes(method_length)
        if not method_bytes:
            method = "GET"
        else:
            method = method_bytes.decode("utf-8")

    # Read path
    path_length = reader.read_var_int_num()
    if path_length is None or path_length == 0 or path_length == NEG_ONE:
        path = "/"
    else:
        path_bytes = reader.read_bytes(path_length)
        if not path_bytes:
            path = "/"
        else:
            path = path_bytes.decode("utf-8")

    # Read search (query string)
    search_length = reader.read_var_int_num()
    if search_length is None or search_length == 0 or search_length == NEG_ONE:
        search = ""
    else:
        search_bytes = reader.read_bytes(search_length)
        if not search_bytes:
            search = ""
        else:
            search = search_bytes.decode("utf-8")

    # Read headers
    headers = {}
    n_headers = reader.read_var_int_num()
    if n_headers is not None and n_headers > 0:
        for _ in range(n_headers):
            key_length = reader.read_var_int_num()
            if key_length is not None and key_length > 0:
                key_bytes = reader.read_bytes(key_length)
                if key_bytes:
                    key = key_bytes.decode("utf-8")

                    value_length = reader.read_var_int_num()
                    if value_length is not None and value_length > 0:
                        value_bytes = reader.read_bytes(value_length)
                        if value_bytes:
                            value = value_bytes.decode("utf-8")
                            headers[key] = value

    # Read body
    body_length = reader.read_var_int_num()
    if body_length is None or body_length == 0 or body_length == NEG_ONE:
        body = b""
    else:
        body = reader.read_bytes(body_length)
        if not body:
            body = b""

    return request_id_bytes, method, path, search, headers, body


def _serialize_http_response_to_payload(request_id_bytes: bytes, status_code: int, headers: dict, body: bytes) -> bytes:
    """
    Serialize HTTP response to BRC-104 binary payload.

    Reference:
    - ts-sdk/src/auth/transports/SimplifiedFetchTransport.ts:serializeResponsePayload
    - go-sdk/auth/authpayload/http.go:FromHTTPResponse
    - py-sdk/bsv/auth/transports/simplified_http_transport.py:_serialize_response_payload

    Returns: Binary payload bytes
    """
    from bsv.utils.writer import Writer

    writer = Writer()

    # Write request ID
    writer.write(request_id_bytes)

    # Write status code
    writer.write_var_int_num(status_code)

    # Filter and write headers
    # Include: x-bsv-* (excluding x-bsv-auth-*), authorization
    included_headers = []
    for key, value in headers.items():
        key_lower = key.lower()
        if (key_lower.startswith("x-bsv-") and not key_lower.startswith("x-bsv-auth-")) or key_lower == "authorization":
            included_headers.append((key_lower, value))

    # Sort headers
    included_headers.sort(key=lambda x: x[0])

    # Write number of headers
    writer.write_var_int_num(len(included_headers))

    # Write each header
    for key, value in included_headers:
        key_bytes = key.encode("utf-8")
        writer.write_var_int_num(len(key_bytes))
        writer.write(key_bytes)

        value_bytes = value.encode("utf-8")
        writer.write_var_int_num(len(value_bytes))
        writer.write(value_bytes)

    # Write body
    if body and len(body) > 0:
        writer.write_var_int_num(len(body))
        writer.write(body)
    else:
        # -1 indicates no body (0xFFFFFFFFFFFFFFFF)
        writer.write_var_int_num(0xFFFFFFFFFFFFFFFF)

    return writer.to_bytes()


def _handle_brc104_general_message(request: HttpRequest) -> HttpResponse:
    """
    Handle BRC-104 general message containing HTTP request as binary payload.

    Process:
    1. Extract BRC-104 headers
    2. Deserialize HTTP request from binary payload
    3. Extract JSON-RPC request from HTTP body
    4. Process JSON-RPC request
    5. Serialize JSON-RPC response to HTTP response
    6. Create BRC-104 response with binary payload and headers
    7. Sign response
    """
    import base64
    import os

    try:
        # Extract BRC-104 headers
        version = request.headers.get("x-bsv-auth-version", "0.1")
        client_identity_key = request.headers.get("x-bsv-auth-identity-key", "")
        client_nonce = request.headers.get("x-bsv-auth-nonce", "")
        server_nonce = request.headers.get("x-bsv-auth-your-nonce", "")  # This is our nonce echoed back
        request_id_header = request.headers.get("x-bsv-auth-request-id", "")

        logger.info(f"[BRC104] General message from {client_identity_key[:20]}...")

        # Deserialize HTTP request from binary payload
        try:
            request_id_bytes, method, path, search, headers, body = _deserialize_http_request_from_payload(request.body)
            request_id = base64.b64encode(request_id_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"[BRC104] Failed to deserialize request payload: {e}")
            return JsonResponse(
                {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Failed to parse BRC-104 payload"}, "id": None},
                status=400,
            )

        # Verify request ID matches header
        if request_id != request_id_header:
            logger.warning(
                f"[BRC104] Request ID mismatch: header={request_id_header[:20]}..., payload={request_id[:20]}..."
            )

        # Parse JSON-RPC request from HTTP body
        try:
            request_data = json.loads(body.decode("utf-8"))
            request_id_json = request_data.get("id")
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"[BRC104] Invalid JSON in request body: {e}")
            return JsonResponse(
                {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}, status=400
            )

        # Verify authentication matches params
        params = request_data.get("params", {})
        auth_valid, auth_error = _verify_identity_key(request, params)
        if not auth_valid:
            logger.warning(f"[BRC104] Auth verification failed: {auth_error}")
            # Still need to return BRC-104 response
            error_response_data = {
                "jsonrpc": "2.0",
                "error": {"code": -32600, "message": auth_error},
                "id": request_id_json,
            }
            return _create_brc104_response(request, request_id_bytes, error_response_data, 401)

        # Get StorageServer instance and process JSON-RPC request
        server = get_storage_server()
        response_data = server.handle_json_rpc_request(request_data)

        # Sanitize response to ensure no sensitive exception details are exposed
        if isinstance(response_data, dict) and "error" in response_data:
            error_obj = response_data["error"]
            if isinstance(error_obj, dict) and "message" in error_obj:
                # Ensure error message doesn't contain exception details
                message = error_obj["message"]
                if isinstance(message, str) and (
                    "Traceback" in message or "Exception" in message or " at 0x" in message
                ):
                    # Replace potentially sensitive error message with generic one
                    response_data["error"]["message"] = "Internal error"

        # Create BRC-104 response
        return _create_brc104_response(request, request_id_bytes, response_data, 200)

    except Exception as e:
        import traceback

        error_detail = traceback.format_exc()
        logger.error(f"[BRC104] Unexpected error: {e}\n{error_detail}")

        # Try to get request_id from JSON if available
        request_id_json = None
        try:
            if request.body:
                _, _, _, _, _, body = _deserialize_http_request_from_payload(request.body)
                if body:
                    request_data = json.loads(body.decode("utf-8"))
                    request_id_json = request_data.get("id")
        except Exception:
            pass

        error_response_data = {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": "Internal error"},
            "id": request_id_json,
        }

        try:
            request_id_bytes = base64.b64decode(request.headers.get("x-bsv-auth-request-id", ""))
            if len(request_id_bytes) != 32:
                request_id_bytes = os.urandom(32)
        except Exception:
            request_id_bytes = os.urandom(32)

        return _create_brc104_response(request, request_id_bytes, error_response_data, 500)


def _create_brc104_response(
    request: HttpRequest, request_id_bytes: bytes, json_rpc_response: dict, http_status_code: int
) -> HttpResponse:
    """
    Create BRC-104 general message response.

    Wraps JSON-RPC response in binary payload and adds BRC-104 headers.
    """
    import base64
    import os

    try:
        # Get server wallet for signing
        server_wallet = get_server_wallet()

        # Get server identity key
        server_identity_key = server_wallet.get_public_key({"identityKey": True})
        if isinstance(server_identity_key, dict):
            server_identity_key = server_identity_key.get("publicKey", "")

        # Extract client info from request headers
        client_identity_key = request.headers.get("x-bsv-auth-identity-key", "")
        client_nonce = request.headers.get("x-bsv-auth-nonce", "")
        server_nonce = request.headers.get("x-bsv-auth-your-nonce", "")

        # If we don't have server_nonce from header, generate a new one
        # (This shouldn't happen in normal flow, but handle gracefully)
        if not server_nonce:
            server_nonce = base64.b64encode(os.urandom(32)).decode("utf-8")
            logger.warning("[BRC104] Missing server nonce in request, generated new one")

        # Serialize JSON-RPC response to HTTP response
        response_body = json.dumps(json_rpc_response, cls=BytesEncoder).encode("utf-8")
        response_headers = {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}

        # Serialize HTTP response to binary payload
        response_payload = _serialize_http_response_to_payload(
            request_id_bytes, http_status_code, response_headers, response_body
        )

        # Create response nonce for signing
        response_nonce = base64.b64encode(os.urandom(32)).decode("utf-8")

        # Sign the response payload
        # Reference: py-sdk/bsv/auth/peer.py:toPeer (general message signing)
        signature_result = server_wallet.create_signature(
            {
                "data": response_payload,
                "protocolID": [2, "auth message signature"],
                "keyID": f"{response_nonce} {server_nonce}",
                "counterparty": client_identity_key,
            }
        )

        # Extract signature
        if isinstance(signature_result, dict):
            signature = signature_result.get("signature", b"")
        elif hasattr(signature_result, "signature"):
            signature = signature_result.signature
        else:
            signature = bytes(signature_result) if signature_result else b""

        # Convert signature to hex string
        if isinstance(signature, bytes):
            signature_hex = signature.hex()
        elif isinstance(signature, list):
            signature_hex = bytes(signature).hex()
        else:
            signature_hex = ""

        # Create HTTP response with BRC-104 headers
        response = HttpResponse(response_payload, status=200, content_type="application/octet-stream")

        # Set BRC-104 headers
        response["x-bsv-auth-version"] = "0.1"
        response["x-bsv-auth-message-type"] = "general"
        response["x-bsv-auth-identity-key"] = server_identity_key
        response["x-bsv-auth-nonce"] = response_nonce
        response["x-bsv-auth-your-nonce"] = client_nonce
        response["x-bsv-auth-signature"] = signature_hex
        response["x-bsv-auth-request-id"] = base64.b64encode(request_id_bytes).decode("utf-8")
        response["Access-Control-Allow-Origin"] = "*"

        logger.info(f"[BRC104] Sending general response with signature length: {len(signature)}")

        return response

    except Exception as e:
        import traceback

        logger.error(f"[BRC104] Failed to create BRC-104 response: {e}\n{traceback.format_exc()}")
        # Fallback to plain JSON response with generic error.
        # Do not reuse potentially tainted json_rpc_response; return a fully generic error.
        return JsonResponse(
            {"jsonrpc": "2.0", "error": {"code": -32603, "message": "Internal error"}, "id": None},
            status=500,
            encoder=BytesEncoder,
        )


def _handle_plain_json_rpc(request: HttpRequest) -> JsonResponse:
    """
    Handle plain JSON-RPC request (non-BRC-104).

    This is the original implementation for backward compatibility.
    """
    request_id = None

    try:
        # Parse JSON request body
        try:
            request_data = json.loads(request.body)
            request_id = request_data.get("id")
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in request: {e}")
            return JsonResponse(
                {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}, status=400
            )

        # Verify authentication matches params (like Go's verifyAuthID)
        # This is only enforced when py-middleware authentication is enabled
        params = request_data.get("params", {})
        auth_valid, auth_error = _verify_identity_key(request, params)
        if not auth_valid:
            logger.warning(f"Auth verification failed: {auth_error}")
            return JsonResponse(
                {"jsonrpc": "2.0", "error": {"code": -32600, "message": auth_error}, "id": request_id}, status=401
            )

        # Get StorageServer instance
        server = get_storage_server()

        # Process JSON-RPC request
        response_data = server.handle_json_rpc_request(request_data)

        # Sanitize response to ensure no sensitive exception details are exposed
        if isinstance(response_data, dict) and "error" in response_data:
            error_obj = response_data["error"]
            if isinstance(error_obj, dict) and "message" in error_obj:
                # Ensure error message doesn't contain exception details
                message = error_obj["message"]
                if isinstance(message, str) and (
                    "Traceback" in message or "Exception" in message or " at 0x" in message
                ):
                    # Replace potentially sensitive error message with generic one
                    response_data["error"]["message"] = "Internal error"

        # Return JSON response with custom encoder for bytes
        response = JsonResponse(response_data, status=200, encoder=BytesEncoder)

        # Add CORS headers
        response["Access-Control-Allow-Origin"] = "*"

        return response

    except Exception as e:
        import traceback

        error_detail = traceback.format_exc()
        logger.error(f"Unexpected error in JSON-RPC endpoint: {e}\n{error_detail}")
        return JsonResponse(
            {"jsonrpc": "2.0", "error": {"code": -32603, "message": "Internal error"}, "id": request_id}, status=500
        )


def _verify_identity_key(request: HttpRequest, params) -> tuple[bool, str]:
    """
    Verify that the identity key in JSON-RPC params matches the authenticated identity.

    Reference: go-wallet-toolbox/pkg/storage/internal/server/rpc_storage_provider.go:verifyAuthID

    This security check ensures that when BRC-104 authentication is enabled,
    a client cannot access another client's data by spoofing identity keys.

    Args:
        request: Django HttpRequest (may have request.auth from py-middleware)
        params: JSON-RPC params (dict or list)

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Get authenticated identity from py-middleware
    authenticated_key = _get_authenticated_identity(request)

    # If no authentication was performed (middleware not enabled or allow_unauthenticated),
    # skip verification
    if authenticated_key is None:
        return True, ""

    # Extract identity key from params
    params_identity_key = _extract_identity_key_from_params(params)

    # If no identity key in params, allow (some methods don't require it)
    if not params_identity_key:
        return True, ""

    # Verify identity keys match
    if authenticated_key != params_identity_key:
        logger.warning(
            f"Identity key mismatch: params={params_identity_key[:16]}..., "
            f"authenticated={authenticated_key[:16]}..."
        )
        return False, "identityKey does not match authentication"

    return True, ""


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def json_rpc_endpoint(request: HttpRequest):
    """
    JSON-RPC 2.0 endpoint for wallet operations.

    Accepts JSON-RPC requests and forwards them to the StorageServer.

    Supports two modes:
    1. Plain JSON-RPC: Direct JSON-RPC request in body
    2. BRC-104 General Message: HTTP request wrapped in BRC-104 binary payload

    When py-middleware is enabled:
    - Authentication is handled by BSVAuthMiddleware
    - Identity key in params is verified against authenticated identity
    - Payment is handled by BSVPaymentMiddleware (if enabled)

    Request format (plain JSON-RPC):
    {
        "jsonrpc": "2.0",
        "method": "createAction",
        "params": {"auth": {...}, "args": {...}},
        "id": 1
    }

    Request format (BRC-104 general message):
    - Headers: x-bsv-auth-version, x-bsv-auth-message-type, x-bsv-auth-identity-key,
               x-bsv-auth-nonce, x-bsv-auth-your-nonce, x-bsv-auth-signature, x-bsv-auth-request-id
    - Body: Binary payload containing serialized HTTP request with JSON-RPC in body

    Response format:
    {
        "jsonrpc": "2.0",
        "result": {...},
        "id": 1
    }

    For BRC-104 general messages, response is wrapped in binary payload with BRC-104 headers.
    """
    # Handle OPTIONS for CORS preflight
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "*"
        return response

    # The middleware handles BRC-104 general messages
    # Our view just processes JSON-RPC requests (the middleware extracts the body from the payload)
    return _handle_plain_json_rpc(request)


# Mark this view to bypass BSV middleware authentication
# Since py-middleware and TypeScript SDK have incompatible signature formats
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def well_known_auth_endpoint(request: HttpRequest):
    """
    BRC-104 Authentication endpoint for mutual authentication handshake.

    This endpoint handles:
    - initialRequest: Client sends initial authentication request
    - initialResponse: Server responds with its identity and signature

    Reference:
    - go-sdk/auth/transports/simplified_http_transport.go
    - ts-sdk/src/auth/transports/SimplifiedFetchTransport.ts
    """
    # Handle OPTIONS for CORS preflight
    if request.method == "OPTIONS":
        response = HttpResponse()
        response.status_code = 204
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "*"
        return response

    try:
        # Parse the incoming AuthMessage
        try:
            message_data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in auth request: {e}")
            return JsonResponse(
                {"status": "error", "code": "ERR_INVALID_JSON", "description": "Invalid JSON format"}, status=400
            )

        logger.info(f"[AUTH] Received message: {message_data.get('messageType', 'unknown')}")

        message_type = message_data.get("messageType") or message_data.get("message_type", "")

        if message_type == "initialRequest":
            return _handle_initial_request(request, message_data)
        else:
            logger.warning(f"[AUTH] Unknown message type: {message_type}")
            return JsonResponse(
                {
                    "status": "error",
                    "code": "ERR_UNKNOWN_MESSAGE_TYPE",
                    "description": f"Unknown message type: {message_type}",
                },
                status=400,
            )

    except Exception as e:
        import traceback

        error_detail = traceback.format_exc()
        logger.error(f"Error in auth endpoint: {e}\n{error_detail}")
        return JsonResponse(
            {"status": "error", "code": "ERR_AUTH_FAILED", "description": "Authentication failed"}, status=500
        )


def _handle_initial_request(request: HttpRequest, message_data: dict) -> JsonResponse:
    """
    Handle initialRequest message and generate initialResponse.

    Reference: go-sdk/auth/peer.go handleInitialRequest()
    """
    import base64
    import os


    try:
        # Get server wallet
        server_wallet = get_server_wallet()

        # Extract client's identity key and nonce
        client_identity_key = message_data.get("identityKey") or message_data.get("identity_key", "")
        client_nonce = (
            message_data.get("nonce") or message_data.get("initialNonce") or message_data.get("initial_nonce", "")
        )
        version = message_data.get("version", "0.1")

        logger.info(f"[AUTH] Client identity: {client_identity_key[:20]}... nonce: {client_nonce[:20]}...")

        # Generate server's nonce
        server_nonce = base64.b64encode(os.urandom(32)).decode("utf-8")

        # Get server's identity key
        server_identity_key = server_wallet.get_public_key({"identityKey": True})
        if isinstance(server_identity_key, dict):
            server_identity_key = server_identity_key.get("publicKey", "")

        logger.info(f"[AUTH] Server identity: {server_identity_key[:20]}...")

        # Create signature over the nonces
        # Reference: py-sdk/bsv/auth/peer.py _compute_initial_sig_data()
        # Must match the order used by py-sdk: client_nonce + server_nonce
        try:
            client_nonce_bytes = base64.b64decode(client_nonce)
            server_nonce_bytes = base64.b64decode(server_nonce)
            # py-sdk order: client_nonce + server_nonce
            sig_data = client_nonce_bytes + server_nonce_bytes
        except Exception as e:
            logger.error(f"[AUTH] Failed to decode nonces: {e}")
            return JsonResponse(
                {"status": "error", "code": "ERR_INVALID_NONCE", "description": "Failed to decode nonces"}, status=400
            )

        # Sign using wallet - try different parameters to match Go server
        # The Go server works, so the Python implementation must match exactly
        signature_result = server_wallet.create_signature(
            {
                "data": sig_data,
                "protocolID": [2, "auth message signature"],
                "keyID": f"{client_nonce} {server_nonce}",
                "counterparty": client_identity_key,  # Use client as counterparty like py-middleware
            }
        )

        # Convert signature to array of integers (bytes)
        # TypeScript SDK expects signature as number[] (list of byte values)
        # Signature should be DER-encoded ECDSA signature (starts with 0x30)
        signature_array = []

        # Extract signature from result
        if isinstance(signature_result, dict):
            sig = signature_result.get("signature", b"")
        elif hasattr(signature_result, "signature"):
            sig = signature_result.signature
        else:
            logger.error(f"[AUTH] Invalid signature result type: {type(signature_result)}")
            raise ValueError(f"Invalid signature result type: {type(signature_result)}")

        # Convert signature to list of integers
        if isinstance(sig, bytes):
            signature_array = list(sig)
        elif isinstance(sig, list):
            signature_array = sig
        else:
            # Try to convert to bytes first
            try:
                signature_array = list(bytes(sig))
            except Exception as e:
                logger.error(f"[AUTH] Invalid signature format: {type(sig)}, error: {e}")
                raise ValueError(f"Invalid signature format: {type(sig)}")

        # Verify signature is DER format (starts with 0x30 = 48)
        if not signature_array:
            logger.error("[AUTH] Signature is empty")
            raise ValueError("Signature is empty")

        # Log signature details for debugging (use print for visibility)
        print(
            f"[AUTH DEBUG] Signature details: length={len(signature_array)}, first_byte=0x{signature_array[0]:02x} ({signature_array[0]})"
        )
        print(f"[AUTH DEBUG] First 10 bytes: {[hex(b) for b in signature_array[:10]]}")
        print(f"[AUTH DEBUG] First 10 bytes (decimal): {signature_array[:10]}")
        first_byte_hex = f"0x{signature_array[0]:02x}"
        first_10_hex = [hex(b) for b in signature_array[:10]]
        logger.info(
            f"[AUTH] Signature details: length={len(signature_array)}, first_byte={first_byte_hex}, first_10_bytes={first_10_hex}"
        )

        if signature_array[0] != 48:  # 0x30
            error_msg = f"[AUTH ERROR] Signature does not start with 0x30 (DER format). First byte: 0x{signature_array[0]:02x} ({signature_array[0]})"
            print(error_msg)
            print(f"[AUTH ERROR] Signature (first 20 bytes): {signature_array[:20]}")
            print(f"[AUTH ERROR] Signature (hex): {bytes(signature_array[:20]).hex()}")
            print(f"[AUTH ERROR] Signature result type: {type(signature_result)}, sig type: {type(sig)}")
            logger.error(error_msg)
            logger.error(f"[AUTH] Signature (first 20 bytes): {signature_array[:20]}")
            logger.error(f"[AUTH] Signature (hex): {bytes(signature_array[:20]).hex()}")
            logger.error(f"[AUTH] Signature result type: {type(signature_result)}, sig type: {type(sig)}")
            logger.error(f"[AUTH] Signature result: {signature_result}")
            # Don't send invalid signature - this will help identify the issue
            raise ValueError(
                f"Invalid signature format: does not start with 0x30. First byte: 0x{signature_array[0]:02x}"
            )

        # Build initialResponse
        response_data = {
            "status": "success",
            "version": version,
            "messageType": "initialResponse",
            "identityKey": server_identity_key,
            "nonce": server_nonce,
            "yourNonce": client_nonce,
            "initialNonce": server_nonce,  # FIX: This should be server_nonce, not client_nonce
            "certificates": [],
            "signature": signature_array,
        }

        first_byte_info = f"0x{signature_array[0]:02x}" if signature_array else "N/A"
        print(
            f"[AUTH DEBUG] Sending initialResponse with signature length: {len(signature_array)} bytes, first byte: {first_byte_info}"
        )
        logger.info(
            f"[AUTH] Sending initialResponse with signature length: {len(signature_array)} bytes, first byte: {first_byte_info}"
        )

        # Debug: Log the signature being sent
        print(f"[AUTH DEBUG] Sending signature to client: {signature_array[:10]}... (length: {len(signature_array)})")

        # Use BytesEncoder to ensure proper serialization of byte arrays
        response = JsonResponse(response_data, encoder=BytesEncoder)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    except Exception as e:
        import traceback

        logger.error(f"[AUTH] Error handling initialRequest: {e}\n{traceback.format_exc()}")
        return JsonResponse(
            {"status": "error", "code": "ERR_INITIAL_REQUEST_FAILED", "description": "Initial request failed"},
            status=500,
        )
