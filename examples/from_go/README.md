## Python Wallet Toolbox Examples (Go-port set)

This `examples/from_go` directory contains Python ports of the examples from the Go wallet toolbox.  
All examples are intended to be executed **with this directory as the current working directory**.

### 1. Virtual environment and dependencies

```bash
cd toolbox/py-wallet-toolbox/examples/from_go

python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Make this directory importable as the root for examples
```

`requirements.txt` contains the libraries required to run the examples, plus the toolbox package itself via `-e ../..`.

### 2. How to run examples (script mode as default)

All examples are expected to be run **from `examples/from_go`**.

#### 2-1. Run as scripts (recommended)

```bash
cd toolbox/py-wallet-toolbox/examples/from_go
source .venv/bin/activate

# Example: create a data transaction (OP_RETURN)
python wallet_examples/create_data_tx/create_data_tx.py

# Example: check wallet balance
python wallet_examples/get_balance/get_balance.py

# Example: show faucet receive address
python wallet_examples/show_address_for_tx_from_faucet/show_address_for_tx_from_faucet.py
```

> Note: You can also run them as modules, e.g. `python -m wallet_examples.create_data_tx`,  
> but for day-to-day usage the simple “run the script file” pattern above is usually enough.

Every script uses `from internal import setup, show` to share common setup and logging helpers from `internal/`.

---

### 3. Recommended execution order (scenario-based)

There are many samples under `wallet_examples/`.  
If you want a guided path, **start with the following order**:

> Assumption: You have already done  
> `cd toolbox/py-wallet-toolbox/examples/from_go` and activated `.venv`.

#### 3-1. Get test funds from a faucet

1. **Show faucet address**

   ```bash
   python wallet_examples/show_address_for_tx_from_faucet/show_address_for_tx_from_faucet.py
   ```

   - Copy the address printed to the console.
   - Use a testnet faucet (e.g. a public web faucet for BSV testnet) to **manually send** coins to that address.

2. **Internalize the faucet transaction into the wallet**

   ```bash
   python wallet_examples/internalize_tx_from_faucet/internalize_tx_from_faucet.py
   ```

   - Before running, edit the script and set `TX_ID` at the top to the transaction ID of the faucet payment  
     (as seen in your block explorer).

#### 3-2. Inspect balance and UTXOs

3. **Check balance**

   ```bash
   python wallet_examples/get_balance/get_balance.py
   ```

4. **List UTXOs (outputs)**

   ```bash
   python wallet_examples/list_outputs/list_outputs.py
   ```

5. **Inspect action history**

   ```bash
   python wallet_examples/list_actions/list_actions.py
   python wallet_examples/list_failed_actions/list_failed_actions.py
   ```

#### 3-3. Create and broadcast transactions

6. **Create a data transaction (OP_RETURN)**

   ```bash
   python wallet_examples/create_data_tx/create_data_tx.py
   ```

   - This requires that the wallet already has funds (from the faucet step).
   - You can change `DATA_TO_EMBED` in the script to embed arbitrary text.

7. **Create a P2PKH payment**

   ```bash
   # Edit the script first: set RECIPIENT_ADDRESS and SATOSHIS_TO_SEND
   python wallet_examples/create_p2pkh_tx/create_p2pkh_tx.py
   ```

   - Set `RECIPIENT_ADDRESS` to the destination address and `SATOSHIS_TO_SEND` to the amount you want to send.

#### 3-4. Encryption / decryption samples

8. **Encrypt / Decrypt**

   ```bash
   # Encryption sample
   python wallet_examples/encrypt/encrypt.py

   # Decryption sample
   # -> First, take the ciphertext produced by the encrypt example
   #    and paste it into the CIPHERTEXT variable in decrypt.py
   python wallet_examples/decrypt/decrypt.py
   ```

#### 3-5. Advanced samples (optional)

9. **Internalize a wallet payment (BRC-29 style)**

   ```bash
   # Fill in ATOMIC_BEEF_HEX / PREFIX / SUFFIX / IDENTITY_KEY
   # according to your actual BRC-29 payment flow before running
   python wallet_examples/internalize_wallet_payment/internalize_wallet_payment.py
   ```

10. **Batch send using NoSend + SendWith**

   ```bash
   python wallet_examples/no_send_send_with/no_send_send_with.py
   ```

   - This demonstrates creating multiple transactions with the `noSend` option  
     and then broadcasting them together with `sendWith`.
   - You will again need sufficient wallet balance for all the mints and redeems.


