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

from .services import get_storage_server, get_server_wallet

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
    if hasattr(request, 'auth') and hasattr(request.auth, 'identity_key'):
        identity_key = request.auth.identity_key
        if identity_key and identity_key != 'unknown':
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
        auth = params.get('auth', {})
        if isinstance(auth, dict):
            return auth.get('identityKey') or auth.get('identity_key', '')
    elif isinstance(params, list) and len(params) > 0:
        auth = params[0]
        if isinstance(auth, dict):
            return auth.get('identityKey') or auth.get('identity_key', '')
    return ''


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
    
    When py-middleware is enabled:
    - Authentication is handled by BSVAuthMiddleware
    - Identity key in params is verified against authenticated identity
    - Payment is handled by BSVPaymentMiddleware (if enabled)

    Request format:
    {
        "jsonrpc": "2.0",
        "method": "createAction",
        "params": {"auth": {...}, "args": {...}},
        "id": 1
    }

    Response format:
    {
        "jsonrpc": "2.0",
        "result": {...},
        "id": 1
    }
    """
    # Handle OPTIONS for CORS preflight
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = '*'
        return response

    request_id = None

    try:
        # Parse JSON request body
        try:
            request_data = json.loads(request.body)
            request_id = request_data.get("id")
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in request: {e}")
            return JsonResponse({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                },
                "id": None
            }, status=400)

        # Verify authentication matches params (like Go's verifyAuthID)
        # This is only enforced when py-middleware authentication is enabled
        params = request_data.get('params', {})
        auth_valid, auth_error = _verify_identity_key(request, params)
        if not auth_valid:
            logger.warning(f"Auth verification failed: {auth_error}")
            return JsonResponse({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": auth_error
                },
                "id": request_id
            }, status=401)

        # Get StorageServer instance
        server = get_storage_server()

        # Process JSON-RPC request
        response_data = server.handle_json_rpc_request(request_data)

        # Return JSON response with custom encoder for bytes
        response = JsonResponse(response_data, status=200, encoder=BytesEncoder)
        
        # Add CORS headers
        response['Access-Control-Allow-Origin'] = '*'
        
        return response

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Unexpected error in JSON-RPC endpoint: {e}\n{error_detail}")
        return JsonResponse({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            },
            "id": request_id
        }, status=500)


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
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response.status_code = 204
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = '*'
        return response

    try:
        # Parse the incoming AuthMessage
        try:
            message_data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in auth request: {e}")
            return JsonResponse({
                'status': 'error',
                'code': 'ERR_INVALID_JSON',
                'description': str(e)
            }, status=400)

        logger.info(f"[AUTH] Received message: {message_data.get('messageType', 'unknown')}")
        
        message_type = message_data.get('messageType') or message_data.get('message_type', '')
        
        if message_type == 'initialRequest':
            return _handle_initial_request(request, message_data)
        else:
            logger.warning(f"[AUTH] Unknown message type: {message_type}")
            return JsonResponse({
                'status': 'error',
                'code': 'ERR_UNKNOWN_MESSAGE_TYPE',
                'description': f'Unknown message type: {message_type}'
            }, status=400)

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Error in auth endpoint: {e}\n{error_detail}")
        return JsonResponse({
            'status': 'error',
            'code': 'ERR_AUTH_FAILED',
            'description': str(e)
        }, status=500)


def _handle_initial_request(request: HttpRequest, message_data: dict) -> JsonResponse:
    """
    Handle initialRequest message and generate initialResponse.
    
    Reference: go-sdk/auth/peer.go handleInitialRequest()
    """
    import os
    import base64
    from bsv.keys import PrivateKey
    from bsv.hash import sha256
    
    try:
        # Get server wallet
        server_wallet = get_server_wallet()
        
        # Extract client's identity key and nonce
        client_identity_key = message_data.get('identityKey') or message_data.get('identity_key', '')
        client_nonce = message_data.get('nonce') or message_data.get('initialNonce') or message_data.get('initial_nonce', '')
        version = message_data.get('version', '0.1')
        
        logger.info(f"[AUTH] Client identity: {client_identity_key[:20]}... nonce: {client_nonce[:20]}...")
        
        # Generate server's nonce
        server_nonce = base64.b64encode(os.urandom(32)).decode('utf-8')
        
        # Get server's identity key
        server_identity_key = server_wallet.get_public_key({
            'identityKey': True
        })
        if isinstance(server_identity_key, dict):
            server_identity_key = server_identity_key.get('publicKey', '')
        
        logger.info(f"[AUTH] Server identity: {server_identity_key[:20]}...")
        
        # Create signature over the message
        # Reference: go-sdk/auth/peer.go signMessage()
        # Sign: version + messageType + yourNonce + nonce
        message_to_sign = f"{version}initialResponse{client_nonce}{server_nonce}"
        message_bytes = message_to_sign.encode('utf-8')
        message_hash = sha256(message_bytes)
        
        # Sign using wallet
        signature_result = server_wallet.create_signature({
            'data': list(message_hash),
            'protocolID': [2, 'auth'],
            'keyID': '1',
            'counterparty': client_identity_key
        })
        
        signature_hex = ''
        if isinstance(signature_result, dict):
            sig = signature_result.get('signature', b'')
            if isinstance(sig, bytes):
                signature_hex = sig.hex()
            elif isinstance(sig, list):
                signature_hex = bytes(sig).hex()
            else:
                signature_hex = str(sig)
        
        # Build initialResponse
        response_data = {
            'status': 'success',
            'version': version,
            'messageType': 'initialResponse',
            'identityKey': server_identity_key,
            'nonce': server_nonce,
            'yourNonce': client_nonce,
            'initialNonce': client_nonce,
            'certificates': [],
            'signature': signature_hex
        }
        
        logger.info(f"[AUTH] Sending initialResponse with signature: {signature_hex[:40]}...")
        
        response = JsonResponse(response_data)
        response['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        import traceback
        logger.error(f"[AUTH] Error handling initialRequest: {e}\n{traceback.format_exc()}")
        return JsonResponse({
            'status': 'error',
            'code': 'ERR_INITIAL_REQUEST_FAILED',
            'description': str(e)
        }, status=500)
