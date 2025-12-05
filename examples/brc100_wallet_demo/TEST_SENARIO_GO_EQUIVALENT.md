# Testing Guide for Go's `wallet_examples` equivalent step by step testing


Python's `brc100_wallet_example` provides comprehensive and interactive way to examine our BRC100-complient `py-wallet-toolbox`.
Please following instruction for Go's [`wallet_examples`](https://github.com/bsv-blockchain/go-wallet-toolbox/tree/main/examples) equivalent test senarios.

## Tool Usage Overview
You will see following menu screen after launching demo.

```
======================================================================
🎉 Welcome to the BRC-100 Wallet Demo
======================================================================

All 28 BRC-100 methods are wired into this menu.
Select any option to trigger the corresponding call.

💡 TESTNET MODE: safe sandbox for experimentation.

======================================================================
🎮 BSV Wallet Toolbox - BRC-100 Demo
======================================================================

[Basics]
  1. Initialize wallet (setup helper)
  2. Show wallet basics -> isAuthenticated / getNetwork / getVersion
  3. Wait for authentication -> waitForAuthentication

[Wallet info]
  4. Show receive address & balance -> getPublicKey (+ balance helper)

[Keys & signatures]
  5. Get public key -> getPublicKey
  6. Sign data -> createSignature
  7. Verify signature -> verifySignature
  8. Create HMAC -> createHmac
  9. Verify HMAC -> verifyHmac
 10. Encrypt / decrypt data -> encrypt / decrypt
 11. Reveal counterparty key linkage -> revealCounterpartyKeyLinkage
 12. Reveal specific key linkage -> revealSpecificKeyLinkage

[Actions]
 13. Create action -> createAction (+ signAction)
 14. -- signAction (handled inside option 13)
 15. List actions -> listActions
 16. Abort action -> abortAction

[Outputs]
17. List outputs -> listOutputs
18. Relinquish output -> relinquishOutput

[Certificates]
19. Acquire certificate -> acquireCertificate (+ proveCertificate)
20. List certificates -> listCertificates
21. Relinquish certificate -> relinquishCertificate
22. -- proveCertificate (handled inside option 19)

[Identity discovery]
23. Discover by identity key -> discoverByIdentityKey
24. Discover by attributes -> discoverByAttributes

[Transactions]
25. Internalize external transaction -> internalizeAction

[Blockchain info]
26. Get block height -> getHeight
27. Get block header for height -> getHeaderForHeight

  0. Exit demo
======================================================================
📊 Implemented: 28 / 28 BRC-100 methods
======================================================================

Select a menu option (0-27):
```

##  Run Faucet Examples (Get Test Funds)
Get some testnet BSV from Faucet for initial funding.

### Show Address For Tx From Faucet
First type `1` to initialize the wallet.
After initialization is done you will see following message.

```
📝 Initializing wallet...
🟢 Network: Testnet (safe)

✅ Wallet initialized.

   Authenticated : True
   Network       : testnet
   Wallet version: 1.0.0

Press Enter to continue...
```

Then show the address with typing `4` on  the menu.
You will see message like this.

```
======================================================================
💰 Wallet information
======================================================================

📍 Receive address:
   n1SjM4TBbvrZVcmjjELDjPC16z56cjtdf9

💰 Current balance:
   0 sats (0.00000000 BSV)

💳 Payment URI (0.001 BSV):
   bitcoin:n1SjM4TBbvrZVcmjjELDjPC16z56cjtdf9?amount=0.001

======================================================================
📋 Explorer
======================================================================

🔍 Testnet explorer:
   https://test.whatsonchain.com/address/n1SjM4TBbvrZVcmjjELDjPC16z56cjtdf9

💡 Need testnet coins? Use this faucet:
   https://scrypt.io/faucet/

======================================================================
```

Copy the "Receive address" into your clipboard.

### Internalize Tx From Faucet
Visit https://scrypt.io/faucet/ to get your initial balance.
Paste your testnet receive address and get your balance.
Then you will see the link to What's On Chan below.
Follow that link to find out your balance's TxID.

At the moment I will use `17c4573105cb237d10033927480cc48b87f3fe48ecafbe4018e9982253ad6c1d` as example.

Next, back to our `brc100_wallet_demo`, type **25** to launch the new *Internalize external transaction -> internalizeAction* flow:

1. When prompted for Atomic BEEF, simply press **Enter** and the demo will download the raw transaction + Merkle path via Wallet Services.
2. Paste the faucet TXID when requested.
3. Accept the default output index `0` (unless the faucet paid a different vout).
4. Keep basket `default`, enter a short description (minimum 5 characters), and optionally add labels/tags.
5. The demo calls `wallet.internalize_action(...)` and reports the resulting TXID/state.

Afterwards, select menu **17** to verify that the output now lives inside the default basket, matching Go's `internalize_tx_from_faucet` scenario.

## Check Your Balance
### Get Balance
Type **4** on the menu. You will see valid balance is there.

```
======================================================================
💰 Wallet information
======================================================================

📍 Receive address:
   n1SjM4TBbvrZVcmjjELDjPC16z56cjtdf9

💰 Current balance:
   99,904 sats (0.00099904 BSV)

💳 Payment URI (0.001 BSV):
   bitcoin:n1SjM4TBbvrZVcmjjELDjPC16z56cjtdf9?amount=0.001
```

## Send Data Transactions
### Create Data Transaction
Type **13** on the menu.
You will be asked to enter message to embed on transaction.

## Additional Wallet Operations
### Craete P2PKH Transaction
### Decrypt
### Encrypt
### List Actions
### List Outputs
### Internalize Wallet Payment
### NoSend + SendWith (Batch Broadcast)