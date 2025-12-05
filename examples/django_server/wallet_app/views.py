"""
Views for wallet_app.

This module provides JSON-RPC endpoints for BRC-100 wallet operations.

Equivalent to TypeScript: ts-wallet-toolbox/src/storage/remoting/StorageServer.ts
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import BadRequest

from .services import get_storage_server

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def json_rpc_endpoint(request):
    """
    JSON-RPC 2.0 endpoint for wallet operations.

    Accepts JSON-RPC requests and forwards them to the StorageServer.

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
    try:
        # Parse JSON request body
        try:
            request_data = json.loads(request.body)
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

        # Get StorageServer instance
        server = get_storage_server()

        # Process JSON-RPC request
        response_data = server.handle_json_rpc_request(request_data)

        # Return JSON response
        return JsonResponse(response_data, status=200)

    except Exception as e:
        logger.error(f"Unexpected error in JSON-RPC endpoint: {e}", exc_info=True)
        return JsonResponse({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": "Internal error"
            },
            "id": None
        }, status=500)
