# BRC-100 Wallet Interface Comparison

This document provides a comprehensive comparison of the BRC-100 Wallet Interface implementations across three languages: **TypeScript**, **Go**, and **Python**.

## Overview

The BRC-100 standard defines a unified, vendor-neutral wallet-to-application interface for the BSV blockchain. All three implementations follow this specification while adapting to each language's idioms and conventions.

| Repository | Language | Source |
|------------|----------|--------|
| `wallet-toolbox` | TypeScript | `ts-sdk/src/wallet/Wallet.interfaces.ts` |
| `go-wallet-toolbox` | Go | `go-sdk/wallet/interfaces.go` |
| `py-wallet-toolbox` | Python | `bsv_wallet_toolbox/manager/wallet_interface.py` |

---

## BRC-100 Method List (29 Methods)

### Transaction Operations

| # | Method | TypeScript | Go | Python |
|---|--------|------------|-----|--------|
| 1 | createAction | ✅ | ✅ | ✅ |
| 2 | signAction | ✅ | ✅ | ✅ |
| 3 | abortAction | ✅ | ✅ | ✅ |
| 4 | listActions | ✅ | ✅ | ✅ |
| 5 | internalizeAction | ✅ | ✅ | ✅ |
| 6 | listOutputs | ✅ | ✅ | ✅ |
| 7 | relinquishOutput | ✅ | ✅ | ✅ |

### Cryptographic Operations

| # | Method | TypeScript | Go | Python |
|---|--------|------------|-----|--------|
| 8 | getPublicKey | ✅ | ✅ | ✅ |
| 9 | encrypt | ✅ | ✅ | ✅ |
| 10 | decrypt | ✅ | ✅ | ✅ |
| 11 | createHmac | ✅ | ✅ | ✅ |
| 12 | verifyHmac | ✅ | ✅ | ✅ |
| 13 | createSignature | ✅ | ✅ | ✅ |
| 14 | verifySignature | ✅ | ✅ | ✅ |

### Key Linkage Operations

| # | Method | TypeScript | Go | Python |
|---|--------|------------|-----|--------|
| 15 | revealCounterpartyKeyLinkage | ✅ | ✅ | ✅ |
| 16 | revealSpecificKeyLinkage | ✅ | ✅ | ✅ |

### Certificate Operations

| # | Method | TypeScript | Go | Python |
|---|--------|------------|-----|--------|
| 17 | acquireCertificate | ✅ | ✅ | ✅ |
| 18 | listCertificates | ✅ | ✅ | ✅ |
| 19 | proveCertificate | ✅ | ✅ | ✅ |
| 20 | relinquishCertificate | ✅ | ✅ | ✅ |
| 21 | discoverByIdentityKey | ✅ | ✅ | ✅ |
| 22 | discoverByAttributes | ✅ | ✅ | ✅ |

### Authentication & Network

| # | Method | TypeScript | Go | Python |
|---|--------|------------|-----|--------|
| 23 | isAuthenticated | ✅ | ✅ | ✅ |
| 24 | waitForAuthentication | ✅ | ✅ | ✅ |
| 25 | getHeight | ✅ | ✅ | ✅ |
| 26 | getHeaderForHeight | ✅ | ✅ | ✅ |
| 27 | getNetwork | ✅ | ✅ | ✅ |
| 28 | getVersion | ✅ | ✅ | ✅ |

---

## Function Signature Patterns

### TypeScript

```typescript
export interface WalletInterface {
  // Pattern: methodName: (args: TypedArgs, originator?: string) => Promise<TypedResult>
  
  createAction: (
    args: CreateActionArgs,
    originator?: OriginatorDomainNameStringUnder250Bytes
  ) => Promise<CreateActionResult>
  
  listActions: (
    args: ListActionsArgs,
    originator?: OriginatorDomainNameStringUnder250Bytes
  ) => Promise<ListActionsResult>
  
  encrypt: (
    args: WalletEncryptArgs,
    originator?: OriginatorDomainNameStringUnder250Bytes
  ) => Promise<WalletEncryptResult>
}
```

### Go

```go
type Interface interface {
    // Pattern: MethodName(ctx, args SpecificArgs, originator string) (*SpecificResult, error)
    
    CreateAction(ctx context.Context, args CreateActionArgs, originator string) (*CreateActionResult, error)
    ListActions(ctx context.Context, args ListActionsArgs, originator string) (*ListActionsResult, error)
    Encrypt(ctx context.Context, args EncryptArgs, originator string) (*EncryptResult, error)
}
```

### Python

```python
class WalletInterface(Protocol):
    # Pattern: method_name(self, args: dict, originator: str | None = None) -> dict
    
    def create_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]: ...
    def list_actions(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]: ...
    def encrypt(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]: ...
```

---

## Detailed Comparison

| Aspect | TypeScript | Go | Python |
|--------|------------|-----|--------|
| **Method Naming** | camelCase | PascalCase | snake_case |
| **Args Type** | Typed interfaces | Typed structs | `dict[str, Any]` |
| **Originator** | Optional (`?`) | Required (`string`) | Optional (`\| None`) |
| **Context** | None | Required (`context.Context`) | None |
| **Return Type** | `Promise<Result>` | `(*Result, error)` | `dict[str, Any]` |
| **Async Model** | `async/await` | goroutine/sync | sync (basic) |
| **Error Handling** | Exception (throw) | Multiple return | Exception (raise) |

---

## Argument Structure Comparison

### CreateActionArgs

#### TypeScript

```typescript
export interface CreateActionArgs {
  description: DescriptionString5to50Bytes
  inputBEEF?: BEEF
  inputs?: CreateActionInput[]
  outputs?: CreateActionOutput[]
  lockTime?: PositiveIntegerOrZero
  version?: PositiveIntegerOrZero
  labels?: LabelStringUnder300Bytes[]
  options?: CreateActionOptions
}
```

#### Go

```go
type CreateActionArgs struct {
    Description string               `json:"description"`
    InputBEEF   []byte               `json:"inputBEEF,omitempty"`
    Inputs      []CreateActionInput  `json:"inputs,omitempty"`
    Outputs     []CreateActionOutput `json:"outputs,omitempty"`
    LockTime    *uint32              `json:"lockTime,omitempty"`
    Version     *uint32              `json:"version,omitempty"`
    Labels      []string             `json:"labels,omitempty"`
    Options     *CreateActionOptions `json:"options,omitempty"`
}
```

#### Python

```python
args = {
    "description": str,           # 5-50 bytes
    "inputBEEF": bytes | None,
    "inputs": list[dict] | None,
    "outputs": list[dict] | None,
    "lockTime": int | None,
    "version": int | None,
    "labels": list[str] | None,
    "options": dict | None,
}
```

### ListActionsArgs

#### TypeScript

```typescript
export interface ListActionsArgs {
  labels: LabelStringUnder300Bytes[]
  labelQueryMode?: 'any' | 'all'
  includeLabels?: BooleanDefaultFalse
  includeInputs?: BooleanDefaultFalse
  includeInputSourceLockingScripts?: BooleanDefaultFalse
  includeInputUnlockingScripts?: BooleanDefaultFalse
  includeOutputs?: BooleanDefaultFalse
  includeOutputLockingScripts?: BooleanDefaultFalse
  limit?: PositiveIntegerDefault10Max10000
  offset?: PositiveIntegerOrZero
  seekPermission?: BooleanDefaultTrue
}
```

#### Go

```go
type ListActionsArgs struct {
    Labels                           []string  `json:"labels"`
    LabelQueryMode                   QueryMode `json:"labelQueryMode,omitempty"`
    IncludeLabels                    *bool     `json:"includeLabels,omitempty"`
    IncludeInputs                    *bool     `json:"includeInputs,omitempty"`
    IncludeInputSourceLockingScripts *bool     `json:"includeInputSourceLockingScripts,omitempty"`
    IncludeInputUnlockingScripts     *bool     `json:"includeInputUnlockingScripts,omitempty"`
    IncludeOutputs                   *bool     `json:"includeOutputs,omitempty"`
    IncludeOutputLockingScripts      *bool     `json:"includeOutputLockingScripts,omitempty"`
    Limit                            *uint32   `json:"limit,omitempty"`
    Offset                           *uint32   `json:"offset,omitempty"`
    SeekPermission                   *bool     `json:"seekPermission,omitempty"`
}
```

#### Python

```python
args = {
    "labels": list[str],
    "labelQueryMode": "any" | "all",
    "includeLabels": bool | None,
    "includeInputs": bool | None,
    "includeOutputs": bool | None,
    "limit": int | None,         # default 10, max 10000
    "offset": int | None,
    "seekPermission": bool | None,
}
```

### EncryptArgs

#### TypeScript

```typescript
export interface WalletEncryptArgs {
  plaintext: Byte[]
  protocolID: WalletProtocol
  keyID: KeyIDStringUnder800Bytes
  counterparty?: WalletCounterparty
  privileged?: BooleanDefaultFalse
  privilegedReason?: DescriptionString5to50Bytes
  seekPermission?: BooleanDefaultTrue
}
```

#### Go

```go
type EncryptArgs struct {
    EncryptionArgs        // Embedded struct
    Plaintext BytesList `json:"plaintext"`
}

type EncryptionArgs struct {
    ProtocolID       Protocol     `json:"protocolID,omitempty"`
    KeyID            string       `json:"keyID,omitempty"`
    Counterparty     Counterparty `json:"counterparty,omitempty"`
    Privileged       bool         `json:"privileged,omitempty"`
    PrivilegedReason string       `json:"privilegedReason,omitempty"`
    SeekPermission   bool         `json:"seekPermission,omitempty"`
}
```

#### Python

```python
args = {
    "encryptionArgs": {
        "protocolID": {"securityLevel": int, "protocol": str},
        "keyID": str,
        "counterparty": dict | str,
        "privileged": bool | None,
        "privilegedReason": str | None,
    },
    "plaintext": bytes,
}
```

---

## Usage Examples

### listActions

#### TypeScript

```typescript
const result = await wallet.listActions({
  labels: ['payment'],
  limit: 100,
  includeLabels: true,
}, 'example.com')  // originator is optional

console.log(result.totalActions)
console.log(result.actions)
```

#### Go

```go
ctx := context.Background()
args := sdk.ListActionsArgs{
    Labels:        []string{"payment"},
    Limit:         to.Ptr(uint32(100)),
    IncludeLabels: to.Ptr(true),
}
result, err := wallet.ListActions(ctx, args, "example.com")  // originator is required
if err != nil {
    panic(err)
}
fmt.Println(result.TotalActions)
fmt.Println(result.Actions)
```

#### Python

```python
args = {
    "labels": ["payment"],
    "limit": 100,
    "includeLabels": True,
}
result = wallet.list_actions(args, "example.com")  # originator is optional

print(result["totalActions"])
print(result["actions"])
```

### createAction

#### TypeScript

```typescript
const result = await wallet.createAction({
  description: 'Create P2PKH Transaction',
  outputs: [{
    lockingScript: lockingScript.toHex(),
    satoshis: 100,
    outputDescription: 'Payment',
    tags: ['payment'],
  }],
  labels: ['example'],
  options: {
    acceptDelayedBroadcast: false,
  },
})
```

#### Go

```go
createArgs := sdk.CreateActionArgs{
    Description: "Create P2PKH Transaction",
    Outputs: []sdk.CreateActionOutput{{
        LockingScript:     lockingScript.Bytes(),
        Satoshis:          100,
        OutputDescription: "Payment",
        Tags:              []string{"payment"},
    }},
    Labels: []string{"example"},
    Options: &sdk.CreateActionOptions{
        AcceptDelayedBroadcast: to.Ptr(false),
    },
}
result, err := wallet.CreateAction(ctx, createArgs, "example.com")
```

#### Python

```python
create_args = {
    "description": "Create P2PKH Transaction",
    "outputs": [{
        "lockingScript": locking_script.hex(),
        "satoshis": 100,
        "outputDescription": "Payment",
        "tags": ["payment"],
    }],
    "labels": ["example"],
    "options": {
        "acceptDelayedBroadcast": False,
    },
}
result = wallet.create_action(create_args, "example.com")
```

---

## Type System Comparison

| Feature | TypeScript | Go | Python |
|---------|------------|-----|--------|
| **Validation Timing** | Compile-time | Compile-time | Runtime |
| **Optional Values** | `?` (undefined) | Pointer `*T` | `\| None` or omit key |
| **Enum Types** | Union type `'any' \| 'all'` | Custom type `QueryMode` | String literal |
| **Binary Data** | `Uint8Array` / `number[]` | `[]byte` | `bytes` |
| **Generic Types** | `Promise<T>` | `(*T, error)` | None (dict) |
| **Semantic Type Names** | Yes (`DescriptionString5to50Bytes`) | Simple (`string`) | None |

---

## Originator Parameter

The `originator` parameter is defined in the [BRC-100 specification](https://bsv.brc.dev/wallet/0100) as:

> **Originator Domain Name String**: The fully qualified domain name (FQDN) of the application that originated the request, used to authenticate and authorize requests in the Wallet Interface.

### Handling by Language

| Language | Required | Default | Usage |
|----------|----------|---------|-------|
| TypeScript | No | `undefined` | Validation only in base Wallet |
| Go | Yes | N/A | Passed to all methods |
| Python | No | `None` | Validation only in base Wallet |

### Where Originator is Actually Used

The `originator` is actively used in the **WalletPermissionsManager** layer for:

1. **Admin vs Non-Admin Distinction**
2. **Basket Permission Checks**
3. **Label Permission Checks**
4. **Automatic Label Addition** (e.g., `"admin originator example.com"`)
5. **Spending Authorization**

---

## JSON Interoperability

All three implementations use the same JSON schema, ensuring network compatibility:

```json
{
  "labels": ["payment"],
  "labelQueryMode": "any",
  "includeLabels": true,
  "limit": 100,
  "offset": 0
}
```

| Language | JSON Conversion |
|----------|-----------------|
| TypeScript | Automatic (object literal = JSON compatible) |
| Go | `json.Marshal/Unmarshal` + struct tags |
| Python | `json.dumps/loads` or dict directly |

---

## Summary

| Language | Key Characteristics |
|----------|---------------------|
| **TypeScript** | Most detailed type definitions (semantic type names), async/await, rich JSDoc comments |
| **Go** | Context required, multi-value error handling, pointer-based optional values |
| **Python** | Dynamic typing (dict), runtime validation, snake_case naming convention |

All three implementations are fully BRC-100 compliant and can interoperate via JSON-based communication protocols.

---

## References

- [BRC-100 Specification](https://bsv.brc.dev/wallet/0100)
- [TypeScript SDK](https://github.com/bsv-blockchain/ts-sdk)
- [Go SDK](https://github.com/bsv-blockchain/go-sdk)
- [Python Wallet Toolbox](../README.md)

