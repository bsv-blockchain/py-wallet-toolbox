# create_action() UTXO Issue - Root Cause Found

## Problem

Test `test_createaction_1out_json_matches_universal_vectors` creates transaction with:
- **Actual:** 0 inputs, 1 output (19 bytes)
- **Expected:** 1 input with signature, 1 output (194 bytes)

## Root Cause

**Storage has no UTXOs to spend!**

1. Test vector args have `inputs: []` (user not providing inputs)
2. Wallet/storage should automatically select UTXOs to fund the output
3. `wallet_with_services` fixture creates empty in-memory database
4. Storage has no UTXOs available
5. Transaction created with 0 inputs → can't fund the 999 satoshi output

## Evidence

```python
# Test vector input
{
  "inputs": [],  # Empty - expects wallet to add inputs
  "outputs": [{"satoshis": 999, "lockingScript": "..."}]
}

# wallet_with_services fixture (conftest.py:193)
engine = create_engine_from_url("sqlite:///:memory:")  # Fresh empty DB
storage = StorageProvider(engine=engine, ...)  # No UTXOs!
```

## Solution

Pre-seed storage with a UTXO in the test fixture:

```python
@pytest.fixture
def wallet_with_services(test_key_deriver: KeyDeriver) -> Wallet:
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    storage = StorageProvider(engine=engine, chain="main", ...)
    
    # TODO: Add UTXO seeding matching universal test vectors
    # Expected input from test vector result:
    # txid: "7cd347a6a099f82cde68faec941e888ebc3489b25403e3ffedd3280f3fa4cc03"
    # vout: 0
    # satoshis: ~1000+ (enough to fund 999 sat output + fees)
    # Need to:
    # 1. Create a transaction record in storage
    # 2. Create an output record with correct script/satoshis
    # 3. Mark as spendable
    
    services = MockWalletServices(chain="main", height=850000)
    
    return Wallet(chain="main", key_deriver=test_key_deriver, 
                  storage_provider=storage, services=services)
```

## TypeScript Comparison Needed

Check how TypeScript universal tests handle this:
- Do they pre-seed storage?
- Do they mock storage.createAction()?
- Does storage layer create synthetic inputs?

## Next Steps

1. ✅ **Root cause identified** - No UTXOs in storage
2. ⏳ **Solution known** - Pre-seed UTXO in fixture
3. ⏳ **Implementation** - Add seeding logic (10-15 tool calls)
4. ⏳ **Verify** - Check if seeded UTXO matches test vector expectations

## Impact

This is NOT an architecture or format issue - those are solved!  
This is a test fixture setup issue. Once fixed, create_action() should pass completely.

**Confidence:** High ✅  
**Complexity:** Low (test fixture enhancement)  
**Priority:** Can be fixed independently while working on other methods

