# Authentication Bug Investigation Report

## Summary

The Python `bsv-sdk`'s `Peer.initiate_handshake()` method has a bug where it calls `transport.send()` with incorrect parameters, causing authentication to fail when connecting to `wallet-infra` server.

**Affected Version:** `bsv-sdk` version **1.0.12** (installed from `develop-port` branch)

## Root Cause

**File:** `bsv/auth/peer.py` (in py-sdk package)  
**Method:** `Peer.initiate_handshake()`  
**Line:** ~1273

### The Bug

The `SimplifiedHTTPTransport.send()` method signature is:
```python
def send(self, ctx: Any, message: AuthMessage) -> Optional[Exception]:
```

But in `Peer.initiate_handshake()`, it's called as:
```python
err = self.transport.send(initial_request)  # ❌ Missing ctx parameter!
```

This should be:
```python
err = self.transport.send(None, initial_request)  # ✅ Correct
```

### Why This Causes Failure

1. The transport's `send()` method expects `(ctx, message)` but receives only `message`
2. This causes the `ctx` parameter to be set to the `AuthMessage` object
3. The `message` parameter becomes `None` or incorrect
4. The transport fails to send the message properly
5. The handshake times out waiting for a response that never arrives
6. `initiate_handshake()` returns `None`
7. `get_authenticated_session()` returns `None`
8. `Peer.to_peer()` returns `Exception("failed to get authenticated session")`

## Evidence

1. **Server responds correctly:** When manually sending a properly formatted auth message to `http://localhost:8080/.well-known/auth`, the server responds with a valid `initialResponse` (status 200).

2. **Version is correct:** The Python SDK uses `AUTH_VERSION = "0.1"` which matches what the server expects.

3. **Transport has handlers:** The transport correctly registers handlers via `Peer.start()`.

4. **Handshake times out:** The `initiate_handshake()` method waits for a response event that never fires because the message was never sent correctly.

## Verification

Test that shows the server works:
```bash
curl -X POST http://localhost:8080/.well-known/auth \
  -H "Content-Type: application/json" \
  -d '{
    "version": "0.1",
    "messageType": "initialRequest",
    "identityKey": "03ab9245fdff0f05863fffbbd84c9560070a9e3e116ba4dc5cd23aa509362fe0f1",
    "initialNonce": "testnonce123456789012345678901234567890"
  }'
```

Response: `200 OK` with valid `initialResponse` JSON.

## Fix

The fix needs to be applied in the `bsv-sdk` package (not in `py-wallet-toolbox`). **All** `transport.send()` calls in the `Peer` class need to be updated to include the `ctx` parameter.

### All Locations That Need Fixing

1. **Line 496** in `Peer._send_initial_response()`:
   ```python
   # Current (broken):
   err = self.transport.send(response)
   
   # Should be:
   err = self.transport.send(None, response)
   ```

2. **Line 1273** in `Peer.initiate_handshake()` (inside `on_initial_response` callback):
   ```python
   # Current (broken):
   err = self.transport.send(initial_request)
   
   # Should be:
   err = self.transport.send(None, initial_request)
   ```

3. **Line 1354** in `Peer.to_peer()`:
   ```python
   # Current (broken):
   err = self.transport.send(general_message)
   
   # Should be:
   err = self.transport.send(None, general_message)
   ```

4. **Line 1404** in `Peer.request_certificates()`:
   ```python
   # Current (broken):
   err = self.transport.send(cert_request)
   
   # Should be:
   err = self.transport.send(None, cert_request)
   ```

5. **Line 1460** in `Peer.send_certificate_response()`:
   ```python
   # Current (broken):
   err = self.transport.send(cert_response)
   
   # Should be:
   err = self.transport.send(None, cert_response)
   ```

**Note:** All of these are in `bsv/auth/peer.py` in the `bsv-sdk` package. The `ctx` parameter can be `None` for all these cases, or a proper context object if needed for future extensibility.

## Workaround

Currently, the `BYPASS_AUTH` option uses `SimpleStorageClient` which bypasses BRC-104 authentication entirely. This allows testing the BRC-100 wallet methods against `wallet-infra` but without proper authentication.

## Impact

- **Affected:** All Python applications using `bsv-sdk`'s `AuthFetch` or `Peer` classes for BRC-104 authentication
- **Severity:** High - Authentication completely fails
- **Scope:** Any Python client trying to authenticate with a BRC-104 compliant server (like `wallet-infra`)

## Version Information

- **Package:** `bsv-sdk`
- **Installed Version:** 1.0.12
- **Source:** `git+https://github.com/bsv-blockchain/py-sdk.git@develop-port`
- **Location:** `/home/sneakyfox/.local/lib/python3.12/site-packages/bsv/auth/peer.py`
- **Repository:** https://github.com/bitcoin-sv/py-sdk (or https://github.com/bsv-blockchain/py-sdk)

## Next Steps

1. Report this bug to the `bsv-sdk` Python package maintainers (GitHub: bitcoin-sv/py-sdk or bsv-blockchain/py-sdk)
2. Apply the fix in `bsv/auth/peer.py` (all 5 locations listed above)
3. Verify the fix works with `wallet-infra` server
4. Remove the `BYPASS_AUTH` workaround once fixed
5. Update `pyproject.toml` dependency once a fixed version is released

