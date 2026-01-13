# E2E Simple Example: 2-Wallet Roundtrip Payment Test

An end-to-end test to confirm that two wallets (Alice and Bob) can send and receive payments to each other.

## Overview

This script executes tests in the following flow:

1. **Wallet Initialization**: Create two independent wallets for Alice and Bob
2. **Faucet Receipt**: Display Alice's wallet address and have user receive funds from Faucet
3. **Transaction Internalize** (Optional): Incorporate Faucet transaction using BRC-29 wallet payment protocol
4. **Bidirectional Payments**:
   - Alice: Send 80% of balance to Bob via P2PKH
   - Bob: Send 80% of received funds back to Alice via P2PKH
5. **Result Display**: Display final balances and transaction IDs

## Setup

### 1. Prepare Environment File

```bash
# Navigate to script directory
cd examples/e2e_simple_example

# Create .env file
cp env.example .env
```

### 2. Configure .env

Set the following values in the `.env` file copied from `env.example`:

```env
# Network selection (testnet recommended)
BSV_NETWORK=test

# Taal ARC API key (required)
TAAL_ARC_API_KEY=your_taal_arc_api_key_here

# Storage options (choose one of the following)

# Option A: Local SQLite storage (default)
# In this case, wallet_alice.db and wallet_bob.db will be created locally
# No USE_STORAGE_SERVER setting

# Option B: Remote storage server (BRC-104 authentication required)
# USE_STORAGE_SERVER=true
# STORAGE_SERVER_URL=http://localhost:8080
```

**Note**: `TAAL_ARC_API_KEY` is required. For testnet, obtain it from:
- Create an account at https://www.taal.com/ to get an API key

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Or, if developing the project locally:

```bash
pip install -e ../../
python-dotenv
```

## How to Run

```bash
python e2e_two_party_roundtrip.py
```

### Execution Flow

1. **Script Startup**
   - Load environment variables
   - Initialize wallets for Alice and Bob
   - Confirm storage connections

2. **Alice's Address Display**
   ```
   Alice's receive address: <address>
   ```
   Please confirm this output.

3. **Wait for Faucet Deposit**
   - The script will instruct you to deposit from one of the following:
     - Testnet: https://testnet-faucet.bsv.dev/
     - Mainnet: https://faucet.bsv.dev/
   - After confirming in block explorer, press `Enter` to continue

4. **Transaction ID Input (Optional)**
   - Enter faucet transaction txid (64-character hexadecimal)
   - Or leave empty and press `Enter` to skip internalize
   - If skipped, subsequent payments will not execute

5. **Alice → Bob Payment**
   - Alice sends 80% of balance to Bob
   - Transaction ID will be displayed after success

6. **Bob → Alice Payment**
   - Bob sends 80% of received funds back to Alice
   - Transaction ID will be displayed after success

7. **Result Display**
   - Display final balances and transaction IDs
   - Provide information for verification in block explorer

## Troubleshooting

### `TAAL_ARC_API_KEY not set` Error

**Cause**: `TAAL_ARC_API_KEY` is not set in `.env` file

**Solution**:
```bash
# Check .env file
cat .env

# Set TAAL_ARC_API_KEY if not found
echo "TAAL_ARC_API_KEY=your_key_here" >> .env
```

### Storage Connection Error

**For Local Storage**:
- `wallet_alice.db` and `wallet_bob.db` will be created in the same directory as the script
- Already registered in `.gitignore`, so no worries

**For Remote Storage**:
```
Error: Unable to connect to storage server
```

**Solution**:
1. Confirm `STORAGE_SERVER_URL` is correct
2. Confirm storage server is running
3. Switch to local storage execution (comment out `USE_STORAGE_SERVER`)

### Faucet Deposit Timeout

**Cause**: Slow reflection to blockchain

**Solution**:
1. Confirm deposit in block explorer
2. For testnet, wait a few minutes
3. Re-run script and internalize with same txid

### If Payment Fails

**Cause**: Insufficient balance or network error

**Solution**:
1. Confirm sufficient balance (send adequate amount when depositing from faucet)
2. Confirm network connection
3. Confirm `TAAL_ARC_API_KEY` is valid

## Verification Method

Transactions are **definitely broadcast** during testing. Verify in block explorer:

### Testnet
- https://whatsonchain.com/ (select testnet)
- Enter transaction ID in search field

### Mainnet
- https://www.bsvexplorer.io/
- Enter transaction ID in search field

## About Storage

### Local Storage (Default)

- Alice: `wallet_alice.db`
- Bob: `wallet_bob.db`
- SQLite format
- Automatically registered in `.gitignore`

### Remote Storage

- BRC-104 authentication required
- Uses server specified by `STORAGE_SERVER_URL`
- Can share wallet state across multiple applications

## Notes

### Security

- ✅ Do not save private keys or seeds in `.env` file (testing use only)
- ✅ `.env` file is already registered in `.gitignore` so won't be committed to Git
- ✅ In production, manage securely using environment variables or AWS Secrets Manager

### Testnet Recommended

- Please test sufficiently on testnet before using mainnet
- Mainnet testing requires real funds

### ARC Broadcasting

- This test broadcasts using Taal ARC API in the script
- Bitails and GorillaPool are disabled for this test
- Set with sufficient fees for reliable broadcasting

## Implementation Details

### Storage Switching

The script selects storage with the following priority:

1. When `USE_STORAGE_SERVER=true` is set → Remote storage
2. Otherwise → Local SQLite

### Services Initialization

- Inject Taal ARC API key from `TAAL_ARC_API_KEY`
- Bitails and GorillaPool are disabled
- Retry logic and caching mechanism are enabled

### P2PKH Payment

- Standard Pay-to-Public-Key-Hash (P2PKH) format
- Locking using `bsv.script.P2PKH` class

### BRC-29 Wallet Payment Protocol

Faucet receipts are processed using BRC-29 wallet payment protocol:

- `senderIdentityKey`: Faucet's public key (PrivateKey(1).public_key())
- `derivationPrefix/Suffix`: Fixed test values (base64 encoded)

## License

This test script is included in wallet-toolbox.

