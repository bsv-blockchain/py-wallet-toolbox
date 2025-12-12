# SDK Naming Convention Alignment

## Problem Summary

The `py-sdk` auth module (e.g., `bsv/auth/utils.py`, `bsv/auth/peer.py`) uses a **different argument format** than what `py-wallet-toolbox`'s `Wallet` class expects. This causes authentication to fail because the wallet methods reject the incorrectly formatted arguments.

## Naming Convention Mismatches

### 1. Argument Structure: Nested vs Flat

| py-sdk auth (WRONG) | py-wallet-toolbox Wallet (CORRECT) |
|---------------------|-------------------------------------|
| `args['encryption_args']['protocol_id']` | `args['protocolID']` |
| `args['encryption_args']['key_id']` | `args['keyID']` |
| `args['encryption_args']['counterparty']` | `args['counterparty']` |

**py-sdk sends:**
```python
args = {
    'encryption_args': {
        'protocol_id': {...},
        'key_id': '...',
        'counterparty': {...}
    },
    'data': ...
}
```

**py-wallet-toolbox expects:**
```python
args = {
    'protocolID': [security_level, protocol_name],
    'keyID': '...',
    'counterparty': '...',
    'data': ...
}
```

### 2. Key Name Casing: snake_case vs camelCase

| py-sdk auth (snake_case) | TypeScript/Go/py-wallet-toolbox (camelCase) |
|--------------------------|---------------------------------------------|
| `protocol_id` | `protocolID` |
| `key_id` | `keyID` |
| `public_key` | `publicKey` |
| `identity_key` | `identityKey` |
| `message_type` | `messageType` |
| `initial_nonce` | `initialNonce` |
| `your_nonce` | `yourNonce` |
| `security_level` | `securityLevel` |
| `protocol` | `protocol` (same) |

### 3. ProtocolID Format Differences

| py-sdk auth (WRONG) | TypeScript/Go/py-wallet-toolbox (CORRECT) |
|---------------------|-------------------------------------------|
| `{'securityLevel': 1, 'protocol': 'name'}` (dict) | `[1, 'name']` (tuple/array) |

### 4. Return Value Format: Attribute vs Dict

| py-sdk expects | py-wallet-toolbox returns |
|----------------|---------------------------|
| `result.public_key` | `result['publicKey']` |
| `result.hmac` | `result['hmac']` |
| `result.valid` | `result['valid']` |

## Files That Need Fixing in py-sdk

All in `../SDK/py-sdk/bsv/auth/`:

1. **utils.py** - `create_nonce()` and `verify_nonce()`
   - Lines 18-31, 48-60: Change nested `encryption_args` to flat top-level args
   - Change `protocol_id` to `protocolID` as `[level, name]` tuple
   - Change `key_id` to `keyID`

2. **peer.py** - Multiple wallet method calls
   - Line 1282: `get_public_key()` returns dict with `publicKey`, not object with `public_key`
   - Line 1357: Same issue
   - Lines 1370-1384: `create_signature()` uses wrong arg format
   - Lines 741-755: `verify_signature()` uses wrong arg format
   - All `wallet.create_signature()`, `wallet.verify_signature()` calls

## Complete Mismatch Table

```
+---------------------+---------------------------+--------------------------------+
| Concept             | py-sdk auth uses          | py-wallet-toolbox expects      |
+---------------------+---------------------------+--------------------------------+
| Arg structure       | encryption_args.X         | top-level X                    |
| Protocol ID key     | protocol_id               | protocolID                     |
| Protocol ID format  | {securityLevel, protocol} | [level, protocol]              |
| Key ID key          | key_id                    | keyID                          |
| Public key attr     | result.public_key         | result['publicKey']            |
| Identity key attr   | identity_key              | identityKey                    |
| Message type        | message_type              | messageType                    |
| Initial nonce       | initial_nonce             | initialNonce                   |
| Your nonce          | your_nonce                | yourNonce                      |
+---------------------+---------------------------+--------------------------------+
```

## Go SDK Reference (Correct Format)

From `go-wallet-toolbox/pkg/wallet/internal/utils/create_nonce.go`:

```go
createHMACResult, err := wallet.CreateHMAC(ctx, sdk.CreateHMACArgs{
    EncryptionArgs: sdk.EncryptionArgs{
        ProtocolID: sdk.Protocol{
            SecurityLevel: sdk.SecurityLevelEveryAppAndCounterparty,
            Protocol:      "server hmac",
        },
        KeyID: string(firstHalf),
        Counterparty: sdk.Counterparty{
            Type:         sdk.CounterpartyTypeOther,
            Counterparty: certifier,
        },
    },
    Data: firstHalf,
}, originator)
```

Note: Go uses structs with `EncryptionArgs` wrapper, but the **key names are PascalCase** (`ProtocolID`, `KeyID`, etc.).

## py-wallet-toolbox Wallet Interface (Correct Format)

From `py-wallet-toolbox/src/bsv_wallet_toolbox/wallet.py`:

```python
# create_hmac expects:
args = {
    'data': bytes,
    'protocolID': [security_level, protocol_name],  # tuple/list
    'keyID': str,
    'counterparty': 'self' | 'anyone' | hex_pubkey
}

# get_public_key returns:
{'publicKey': '02abc...'}  # dict with camelCase key

# create_signature returns:
{'signature': bytes}  # dict with camelCase key
```

## Recommended Fix Strategy

Fix the py-sdk auth module to use the correct format for py-wallet-toolbox:

1. **create_nonce/verify_nonce** - Use flat args with camelCase keys
2. **peer.py wallet calls** - Handle dict returns with camelCase keys
3. **All signature/encryption calls** - Use `protocolID` as `[level, name]` tuple

## Fixes Already Applied

1. ✅ `transport.send()` calls - Added missing `ctx` parameter (5 locations)
2. ✅ `Peer.start()` handler - Fixed `on_data(message)` to `on_data(ctx, message)`
3. ✅ `initiate_handshake()` identity key - Handle dict response with `publicKey`

## Fixes Still Needed

1. ❌ `create_nonce()` - Change to flat args with `protocolID`/`keyID`
2. ❌ `verify_nonce()` - Change to flat args with `protocolID`/`keyID`
3. ❌ All `create_signature()` calls in peer.py - Fix arg format
4. ❌ All `verify_signature()` calls in peer.py - Fix arg format


