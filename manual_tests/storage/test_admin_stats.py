"""Manual tests for storage admin statistics.

These tests verify storage admin statistics functionality for both
StorageKnex (MySQL) and StorageServer (RPC) backends.

Implementation Intent:
- Test adminStats() method for StorageKnex
- Test adminStats() via StorageServer RPC
- Verify statistics data structure and content

Why Manual Test:
1. Requires live MySQL database connection (StorageKnex)
2. Requires live StorageServer endpoint (RPC)
3. Needs actual wallet authentication
4. Tests real storage backend statistics

Reference: wallet-toolbox/src/storage/__test/adminStats.man.test.ts
"""

import json
import logging

import pytest
from bsv_wallet_toolbox.auth_fetch import AuthFetch
from bsv_wallet_toolbox.test_utils import create_test_wallet_with_storage_client, get_env

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="Waiting for StorageKnex (MySQL) implementation - Node.js/Knex specific")
@pytest.mark.asyncio
async def test_adminstats_storageknex() -> None:
    """Given: StorageKnex (MySQL) with live data
       When: Call adminStats()
       Then: Statistics are returned with correct structure

    Note: This test is Node.js/Knex specific and should be skipped in Python.
          Python uses StorageMySQL instead of StorageKnex.
          If Python equivalent is needed, create test_adminstats_storagemysql.

    Reference: wallet-toolbox/src/storage/__test/adminStats.man.test.ts
               test('0 adminStats StorageKnex')
    """
    # This test is Node.js/Knex specific - not applicable to Python
    pytest.skip("StorageKnex is Node.js/Knex specific - Python uses StorageMySQL")


# Test enabled - AuthFetch implementation available
@pytest.mark.asyncio
async def test_adminstats_storageserver_via_rpc() -> None:
    """Given: StorageServer endpoint and authenticated wallet
       When: Call adminStats via RPC
       Then: Statistics are returned with correct structure

    Implementation Notes:
    - Uses AuthFetch for authenticated RPC calls
    - Sends JSON-RPC request with method='adminStats'
    - Parses JSON-RPC response and validates result
    - Verifies requestedBy and usersTotal fields

    Reference: wallet-toolbox/src/storage/__test/adminStats.man.test.ts
               test('1 adminStats StorageServer via RPC')
    """

    # Get environment
    env = get_env("main")
    identity_key = env["identityKey"]

    # Create wallet with StorageClient

    setup = await create_test_wallet_with_storage_client({"chain": "main", "rootKeyHex": env["devKeys"][identity_key]})

    # Create AuthFetch
    auth_fetch = AuthFetch(setup["wallet"])
    endpoint_url = (
        "https://storage.babbage.systems" if setup["chain"] == "main" else "https://staging-storage.babbage.systems"
    )

    # Prepare JSON-RPC request
    body = {"jsonrpc": "2.0", "method": "adminStats", "params": [identity_key], "id": 0}

    # Make RPC call
    try:
        response = await auth_fetch.fetch(
            endpoint_url, {"method": "POST", "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}
        )
    except Exception as e:
        logger.error(f"AuthFetch error: {e}")
        raise

    # Check response status
    if not response.ok:
        raise Exception(f"WalletStorageClient rpcCall: network error {response.status} {response.status_text}")

    # Parse JSON-RPC response
    json_data = await response.json()

    if "error" in json_data:
        error = json_data["error"]
        code = error.get("code")
        message = error.get("message")
        data = error.get("data")
        raise Exception(f"RPC Error: {message} (code: {code}, data: {data})")

    # Validate result
    result = json_data["result"]
    logger.info(f"Admin stats: {result}")

    assert result["requestedBy"] == identity_key
    assert result["usersTotal"] > 0

    logger.info("AdminStats via RPC test passed!")

    await setup["wallet"].destroy()
