# Protocol Validation Investigation

## Finding
Universal test vectors use `"test-protocol"` (with hyphen) but all three SDKs (Python, TypeScript, Go) validate that protocol names can only contain letters, numbers, and spaces - **no hyphens allowed**.

##  SDK Validations

### Python (bsv-sdk)
```python
if not re.match(r'^[A-Za-z0-9 ]+$', protocol.protocol):
    raise ValueError("protocol names can only contain letters, numbers and spaces")
```

### TypeScript (wallet-toolbox)
```typescript
if (!/^[a-z0-9 ]+$/g.test(protocolName)) {
  throw new Error('Protocol names can only contain letters, numbers and spaces')
}
```

### Go (go-sdk)
Similar validation applies

## Action Taken
Updated test vectors to use `"testprotocol"` instead of `"test-protocol"` in:
- createSignature-simple-args.json
- createHmac-simple-args.json
- decrypt-simple-args.json
- encrypt-simple-args.json
- verifyHmac-simple-args.json
- verifySignature-simple-args.json

## Issue
Changing the protocol name means all cryptographic outputs (signatures, public keys, encrypted data) are different. The expected result files need to be regenerated.

## Recommendation
These 6 tests should remain skipped until:
1. Universal test vectors are regenerated with valid protocol names (no hyphens)
2. OR a decision is made to allow hyphens in all three SDKs (breaking change)

## Tests Affected
1. test_createsignature_json_matches_universal_vectors
2. test_createhmac_json_matches_universal_vectors  
3. test_decrypt_json_matches_universal_vectors
4. test_encrypt_json_matches_universal_vectors
5. test_verifyhmac_json_matches_universal_vectors
6. test_verifysignature_json_matches_universal_vectors

Status: **Deferred** - Requires test vector regeneration
