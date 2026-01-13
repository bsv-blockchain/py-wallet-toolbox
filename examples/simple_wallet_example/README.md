# BRC-100 Wallet Demo

This project demonstrates how to exercise **all 28 methods defined by the BRC-100 wallet specification** using the Python BSV Wallet Toolbox. Every prompt, log line, and document is written in English so you can easily share the demo with English-speaking teammates.

---

## 🎯 Capabilities

| Category | Methods |
| --- | --- |
| Authentication & Network | `is_authenticated`, `wait_for_authentication`, `get_network`, `get_version` |
| Keys & Signatures | `get_public_key`, `create_signature`, `verify_signature`, `create_hmac`, `verify_hmac`, `encrypt`, `decrypt` |
| Key Linkage | `reveal_counterparty_key_linkage`, `reveal_specific_key_linkage` |
| Actions | `create_action`, `sign_action`, `list_actions`, `abort_action` |
| Outputs | `list_outputs`, `relinquish_output` |
| Certificates | `acquire_certificate`, `list_certificates`, `prove_certificate`, `relinquish_certificate` |
| Identity Discovery | `discover_by_identity_key`, `discover_by_attributes` |
| Blockchain Info | `get_height`, `get_header_for_height` |
| Transactions | `internalize_action` |

✅ **28 / 28 methods implemented**

---

## 📋 Requirements

- Python **3.10 or later**
- Local checkout of this repository
- Dependencies listed in `requirements.txt`

---

## 🚀 Installation

```bash
cd toolbox/py-wallet-toolbox/examples/brc100_wallet_demo
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt` installs the toolbox in editable mode (`-e ../../`), `python-dotenv`, and all transitive dependencies (`bsv-sdk`, `sqlalchemy`, `requests`, etc.).

---

## 💡 Usage

```bash
python wallet_demo.py
```

You will see an interactive menu similar to this:

```
[Basics]            [Wallet]           [Keys]
1. Init wallet      4. Show info ->    5. Get public key -> getPublicKey
   (setup only)        getPublicKey    6. Sign data -> createSignature
2. Show basics ->                      7. Verify signature -> verifySignature
   isAuthenticated /                   8. Create HMAC -> createHmac
   getNetwork / getVersion             9. Verify HMAC -> verifyHmac
3. Wait auth ->                        10. Encrypt / decrypt -> encrypt / decrypt
   waitForAuthentication               11. Reveal counterparty linkage -> revealCounterpartyKeyLinkage
                                       12. Reveal specific linkage -> revealSpecificKeyLinkage

[Actions]          [Outputs]          [Certificates]
13. Create action -> createAction      17. List outputs -> listOutputs
    (+ signAction)                     18. Relinquish output -> relinquishOutput
14. -- signAction is inside 13         19. Acquire cert -> acquireCertificate (+ proveCertificate)
15. List actions -> listActions        20. List certs -> listCertificates
16. Abort action -> abortAction        21. Relinquish cert -> relinquishCertificate
                                       22. -- proveCertificate handled in 19

[Identity]         [Transactions]      [Blockchain]
23. Discover by key -> discoverByIdentityKey  25. Internalize action -> internalizeAction
24. Discover attr -> discoverByAttributes     26. Get height -> getHeight
                                               27. Get header -> getHeaderForHeight

0. Exit
```

---

## ⚙️ Environment Variables

```bash
cp env.example .env
nano .env
```

```env
BSV_NETWORK=test         # 'test' or 'main'
# Optional: never store production mnemonics in plain text
# BSV_MNEMONIC=your twelve word mnemonic phrase here
```

---

## 📁 Project Layout

```
brc100_wallet_demo/
├── README.md
├── MAINNET_GUIDE.md
├── STORAGE_GUIDE.md
├── env.example
├── requirements.txt
├── wallet_demo.py
└── src/
    ├── __init__.py
    ├── config.py
    ├── address_management.py
    ├── key_management.py
    ├── action_management.py
    ├── certificate_management.py
    ├── identity_discovery.py
    ├── crypto_operations.py
    ├── key_linkage.py
    ├── advanced_management.py
    ├── blockchain_info.py
    └── transaction_management.py
```

---

## 🔑 Automatic Mnemonic Generation

If you do not specify `BSV_MNEMONIC`, the demo generates a 12-word mnemonic and prints it once during startup:

```
⚠️  No mnemonic configured. Creating a new wallet...
🔑 Mnemonic: coffee primary dumb soon two ski ship add burst fly pigeon spare
💡 Add this to .env if you want to reuse the wallet:
   BSV_MNEMONIC=coffee primary dumb soon two ski ship add burst fly pigeon spare
```

---

## 💾 Storage & Persistence

- SQLite storage is **enabled by default**.
- Testnet data → `wallet_test.db`  
  Mainnet data → `wallet_main.db`
- All StorageProvider-dependent flows (actions, outputs, certificates, `internalize_action`, etc.) work immediately.
- Database files are ignored by git. Back them up manually if needed.

To use a different database, override `get_storage_provider()` in `src/config.py`:

| Engine | URI | Notes |
| --- | --- | --- |
| SQLite (memory) | `sqlite:///:memory:` | Perfect for temporary tests |
| SQLite (file) | `sqlite:////absolute/path/demo.db` | Simple single-node setup |
| PostgreSQL | `postgresql://user:pass@host/db` | Production-ready option |

See [`STORAGE_GUIDE.md`](STORAGE_GUIDE.md) for deep details.

---

## 🔄 Internalize External Transactions

1. Fund the wallet (option **4** shows the receive address; faucets like <https://scrypt.io/faucet/> work great on testnet).
2. After the faucet broadcasts its TX, copy the TXID from an explorer (e.g., Whatsonchain).
3. Choose menu option **25. Internalize external transaction -> internalizeAction**.
4. Either paste Atomic BEEF hex (from another tool) or press Enter so the demo downloads the BEEF via Wallet Services.
5. Provide the output indexes that belong to you (comma-separated). By default, index `0` is selected.
6. Finish the prompts to tag/basket the outputs and run `internalize_action`.

The helper automatically builds the Atomic BEEF using the multi-provider `Services` layer, so no extra scripting is required. For advanced payment remittance flows, refer to the `from_go/wallet_examples/internalize_*` samples.

---

## 🧪 Testnet Workflow

1. Run `wallet_demo.py`
2. Choose menu option **4. Show wallet info**
3. Copy the testnet address
4. Request coins: <https://scrypt.io/faucet/>
5. Track confirmations: <https://test.whatsonchain.com/>

---

## 💰 Mainnet Workflow

> ⚠️ Real BSV is at risk—start small and double-check every step.

1. Set `BSV_NETWORK=main` in `.env`
2. Provide a secure mnemonic (`BSV_MNEMONIC=...`)
3. Run `python wallet_demo.py`
4. Use menu option **4** to display the receive address and balance
5. Follow the in-depth checklist in [`MAINNET_GUIDE.md`](MAINNET_GUIDE.md)

---

## 🔒 Security Checklist

1. Protect mnemonics (paper backup or password manager; no screenshots/cloud)
2. Never log secrets in production
3. Guard privileged flows (certificates, key linkage) carefully
4. Use production-grade databases (e.g., PostgreSQL) for real deployments
5. Always test on testnet first
6. Start with very small mainnet transfers (e.g., 0.001 BSV)

---

## 📖 Additional Guides

- [`MAINNET_GUIDE.md`](MAINNET_GUIDE.md) – how to send/receive on mainnet safely
- [`STORAGE_GUIDE.md`](STORAGE_GUIDE.md) – how the storage layer works
- [BRC-100 specification](https://github.com/bitcoin-sv/BRCs/blob/master/transactions/0100.md)
- [BSV SDK](https://github.com/bitcoin-sv/py-sdk)
- [Wallet toolbox root README](../../README.md)
- [Whatsonchain Explorer](https://whatsonchain.com/)

---

## 🤝 Support

- GitHub Issues: <https://github.com/bitcoin-sv/py-wallet-toolbox/issues>
- Official docs: <https://docs.bsvblockchain.org/>

---

## 📄 License

This demo inherits the license of the BSV Wallet Toolbox repository.
<<<<<<< Updated README
# BRC-100 Wallet Demo

This sample shows how to exercise **all 28 BRC-100 wallet methods** using the Python BSV Wallet Toolbox. Every prompt, message, and document in this demo is written in English so you can hand it to English-speaking teammates without extra work.

---

## 🎯 Capabilities

| Group | Methods |
| --- | --- |
| Authentication & network | `is_authenticated`, `wait_for_authentication`, `get_network`, `get_version` |
| Key & signature management | `get_public_key`, `create_signature`, `verify_signature`, `create_hmac`, `verify_hmac`, `encrypt`, `decrypt` |
| Key linkage | `reveal_counterparty_key_linkage`, `reveal_specific_key_linkage` |
| Actions | `create_action`, `sign_action`, `list_actions`, `abort_action` |
| Outputs | `list_outputs`, `relinquish_output` |
| Certificates | `acquire_certificate`, `list_certificates`, `prove_certificate`, `relinquish_certificate` |
| Identity discovery | `discover_by_identity_key`, `discover_by_attributes` |
| Blockchain info | `get_height`, `get_header_for_height` |
| Transactions | `internalize_action` |

✅ **28 / 28 methods are fully implemented.**

---

## 📋 Requirements

- Python **3.10+**
- Local checkout of this repository
- Dependencies listed in `requirements.txt`

---

## 🚀 Installation

```bash
cd toolbox/py-wallet-toolbox/examples/brc100_wallet_demo
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt` installs the wallet toolbox in editable mode, `python-dotenv`, and all transitive dependencies (BSV SDK, SQLAlchemy, requests, etc.).

---

## 💡 Usage

```bash
python wallet_demo.py
```

The interactive menu exposes every BRC-100 method. Example:

```
[Basics]            [Wallet]              [Keys]
1. Init wallet      4. Show info          5. Get public key
2. Show basics                            6. Sign data
3. Wait auth                             7. Verify signature
                                         8. Create HMAC
[Actions]                                 9. Verify HMAC
13. Create action                        10. Encrypt / decrypt
15. List actions                         11. Reveal counterparty linkage
16. Abort action                         12. Reveal specific linkage

[Outputs]           [Certificates]        [Identity]         [Blockchain]
17. List outputs    19. Acquire cert      23. Discover by key 25. Get height
18. Relinquish      20. List certs        24. Discover attr   26. Get header
                    21. Relinquish
                    22. Prove

0. Exit
```

---

## ⚙️ Environment Variables

```bash
cp env.example .env
nano .env
```

```env
BSV_NETWORK=test         # 'test' or 'main'
# Optional: never store production mnemonics in plain text!
# BSV_MNEMONIC=your twelve word mnemonic phrase here
```

---

## 📁 Project Layout

```
brc100_wallet_demo/
├── README.md
├── MAINNET_GUIDE.md
├── STORAGE_GUIDE.md
├── env.example
├── requirements.txt
├── wallet_demo.py
└── src/
    ├── __init__.py
    ├── config.py
    ├── address_management.py
    ├── key_management.py
    ├── action_management.py
    ├── certificate_management.py
    ├── identity_discovery.py
    ├── crypto_operations.py
    ├── key_linkage.py
    ├── advanced_management.py
    └── blockchain_info.py
```

---

## 🔑 Automatic Mnemonic Generation

When no mnemonic is defined, the demo generates a fresh 12-word phrase and prints it once:

```
⚠️  No mnemonic configured. Creating a new wallet...
🔑 Mnemonic: coffee primary dumb soon two ski ship add burst fly pigeon spare
💡 Add this to .env if you want to reuse the wallet:
   BSV_MNEMONIC=coffee primary dumb soon two ski ship add burst fly pigeon spare
```

---

## 💾 Storage & Persistence

- SQLite is enabled **by default**.
- Testnet data lives in `wallet_test.db`.  
  Mainnet data lives in `wallet_main.db`.
- All StorageProvider-dependent flows (actions, outputs, certificates, `internalize_action`, etc.) work immediately.
- DB files are ignored by git. Back them up manually if needed.

Switching to another database? Just customize `get_storage_provider()` in `src/config.py`. Examples:

| Engine | URI | Notes |
| --- | --- | --- |
| SQLite (memory) | `sqlite:///:memory:` | Perfect for ephemeral tests |
| SQLite (file) | `sqlite:////path/to/custom.db` | Single-node deployments |
| PostgreSQL | `postgresql://user:pass@host/db` | Production-ready |

See [`STORAGE_GUIDE.md`](STORAGE_GUIDE.md) for deep details.

---

## 🧪 Testnet Workflow

1. Run `wallet_demo.py`
2. Pick menu option **4. Show wallet info**
3. Copy the testnet address
4. Request coins: <https://scrypt.io/faucet/>
5. Track confirmations: <https://test.whatsonchain.com/>

---

## 💰 Mainnet Workflow

> ⚠️ Real BSV is at risk—start small and double-check everything.

1. Set `BSV_NETWORK=main` inside `.env`
2. Provide a secure mnemonic (`BSV_MNEMONIC=...`)
3. Run `python wallet_demo.py`
4. Use menu option **4** to view the receive address and balance
5. Follow the detailed checklist in [`MAINNET_GUIDE.md`](MAINNET_GUIDE.md)

---

## 🔒 Security Checklist

1. Protect the mnemonic (paper backup, password manager, no screenshots)
2. Never log secrets in production
3. Guard privileged flows (certificates, key linkage) carefully
4. Use production-grade databases (e.g., PostgreSQL) for real deployments
5. Always test on testnet first
6. Start with tiny mainnet amounts (e.g., 0.001 BSV)

---

## 📖 Additional Guides

- [`MAINNET_GUIDE.md`](MAINNET_GUIDE.md) – sending and receiving on mainnet
- [`STORAGE_GUIDE.md`](STORAGE_GUIDE.md) – how the SQLite storage layer works
- [BRC-100 spec](https://github.com/bitcoin-sv/BRCs/blob/master/transactions/0100.md)
- [BSV SDK](https://github.com/bitcoin-sv/py-sdk)
- [Wallet toolbox root README](../../README.md)
- [BSV Explorer](https://whatsonchain.com/)

---

## 🤝 Support

- GitHub Issues: <https://github.com/bitcoin-sv/py-wallet-toolbox/issues>
- Official docs: <https://docs.bsvblockchain.org/>

---

## 📄 License

This demo inherits the license of the BSV Wallet Toolbox repository.
