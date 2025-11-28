# Storage Provider Guide

This demo relies on the **StorageProvider** layer from the wallet toolbox to persist wallet data. Below is a quick reference on what gets saved, where it lives, and how to configure it.

---

## 📊 What does StorageProvider track?

- **Transactions** – raw hex, labels, status, broadcast info.
- **Actions** – references, descriptions, related transactions, abort status.
- **Outputs (UTXOs)** – outpoints, satoshis, scripts, basket/tags, spendability.
- **Certificates** – type, certifier, serial, custom fields, expiry.
- **Metadata** – users, sync state, settings, output tags, tx labels, ProvenTx rows, etc.

All entities are modeled via SQLAlchemy, so you can point StorageProvider to any database engine supported by SQLAlchemy.

---

## 💾 Configuration Modes

| Mode | Example | Persistence | Notes |
| --- | --- | --- | --- |
| No storage | `Wallet(chain="test", key_deriver=...)` | None | `wallet.storage` is `None`. Calls like `list_actions()` raise `RuntimeError`. |
| SQLite (memory) | `sqlite:///:memory:` | In-memory only | Perfect for unit tests; data disappears on exit. |
| SQLite (file) | `sqlite:///wallet.db` | Local file | Simple persistent store. Files such as `wallet_test.db` and `wallet_main.db` live next to the demo. |
| PostgreSQL | `postgresql://user:pass@host/db` | Server-backed | Recommended for production; supports backups and multiple clients. |

Example initializer (already baked into `src/config.py`):

```python
from sqlalchemy import create_engine
from bsv_wallet_toolbox.storage import StorageProvider

def get_storage_provider(network: str) -> StorageProvider:
    db_file = f"wallet_{network}.db"
    engine = create_engine(f"sqlite:///{db_file}")
    storage = StorageProvider(
        engine=engine,
        chain=network,
        storage_identity_key=f"{network}-wallet",
    )
    storage.make_available()
    return storage
```

`wallet_demo.py` passes this provider into `Wallet(...)`, so all storage-dependent methods work out of the box.

---

## ✅ Methods That Need Storage

- `list_actions`, `abort_action`, `internalize_action`
- `list_outputs`, `relinquish_output`
- `list_certificates`, `relinquish_certificate`

Without a storage provider, these raise `RuntimeError`. With the built-in SQLite files (`wallet_test.db`, `wallet_main.db`) they function exactly like the TypeScript reference implementation.

---

## 🗂️ Schema Overview

StorageProvider automatically creates tables such as:

`users`, `transactions`, `outputs`, `output_baskets`, `output_tags`, `tx_labels`, `certificates`, `certificate_fields`, `proven_tx`, `proven_tx_req`, `sync_state`, `monitor_events`, `commissions`, `settings`, and assorted mapping tables.

You rarely need to touch these manually, but it is helpful to know where data lands when debugging.

---

## 📍 File Locations

```
brc100_wallet_demo/
├── wallet_test.db   # Testnet data
├── wallet_main.db   # Mainnet data
└── ...
```

For PostgreSQL deployments, the same tables live inside your `wallet_db` (or any name you choose).

---

## TL;DR

1. **No storage provider** → purely ephemeral demo; several methods unavailable.
2. **SQLite in-memory** (`sqlite:///:memory:`) → great for disposable tests.
3. **SQLite file** (`sqlite:///wallet_main.db`) → default choice in this repo.
4. **PostgreSQL** (`postgresql://...`) → recommended for real deployments.

The current demo already ships with SQLite-backed persistence enabled, so every BRC-100 method—including actions, outputs, certificates, and `internalize_action`—works without additional setup. Switch to PostgreSQL when you need horizontal scalability or tighter operational controls.

Need a different backend? Just update `get_storage_provider()` and you’re done.

