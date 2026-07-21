# Arcade Broadcaster

Documentation for Arcade ([bsv-blockchain/arcade](https://github.com/bsv-blockchain/arcade)) support in py-wallet-toolbox.
Arcade is the Teranode-native, ARC-compatible broadcaster providing transaction submission, status tracking, merkle proof retrieval, and real-time notifications via SSE.

Ported from the TypeScript implementation (ts-wallet-toolbox `Arcade.ts` / `ArcSSEClient.ts` / `TaskArcSSE.ts`).

## Components

| Component | File | Role |
|---|---|---|
| `Arcade` provider | `services/providers/arcade.py` | Submission (`post_beef` / `post_raw_tx`) and proof retrieval (`get_merkle_path`) |
| `ArcadeSSEClient` | `services/providers/arcade_sse.py` | Client for the `GET /events` SSE stream |
| `TaskArcadeSSE` | `monitor/tasks/task_arcade_sse.py` | Monitor task that updates ProvenTxReq / Transaction statuses from SSE events |

`Arcade` is a self-contained class, not a subclass of `ARC` (same design decision as TS: never alter the audited ARC transport). Configuration and result types (`ArcConfig` / `PostTxResultForTxid` / `PostBeefResult` / `ArcMinerGetTxData`) are shared from `providers/arc.py`.

## Enabling (opt-in)

Arcade is disabled by default. `create_default_options()` never sets `arcadeUrl` (deliberately diverging from TS `arcadeDefaultUrl()`). Enable it by setting `arcadeUrl` explicitly in `WalletServicesOptions`:

```python
from bsv_wallet_toolbox.services import Services

services = Services({
    "chain": "main",
    "arcadeUrl": "https://arcade-v2-us-1.bsvblockchain.tech",  # mainnet public endpoint
    # Optional:
    "arcadeApiKey": "...",            # Authorization: Bearer header
    "arcadeHeaders": {...},           # extra headers
    "arcadeCallbackUrl": "https://your.app/arc-ingest",  # webhook target
    "arcadeCallbackToken": "...",     # stable per-wallet token scoping SSE / webhook events
})
```

- No public testnet endpoint is deployed.
- When enabled, `arcade` is registered **first** in both `post_beef_services` and `get_merkle_path_services` (same priority as TS). On failure, aggregation falls over to the existing ARC providers (GorillaPool / TAAL) and then Bitails.

## Differences from ARC (wire contract)

Verified against the arcade server implementation (Go, in the sibling `arcade/` repository):

| | ARC | Arcade |
|---|---|---|
| Submit endpoint | `POST {url}/v1/tx` | `POST {url}/tx` (no `/v1` prefix) |
| Status endpoint | `GET {url}/v1/tx/{txid}` | `GET {url}/tx/{txid}` |
| Submission encoding | raw / BEEF V1 | **EF (Extended Format) preferred, raw accepted. BEEF is rejected with 400** |
| Success response | 200 | **202** `{"txid", "status": 202, "txStatus": "RECEIVED"}` |
| Duplicate submit | — | 202 echoing the current status (which can be terminal) |
| Meaning of 400 | various | **terminal validation failure** `{"error", "reason"}` — retrying is pointless |
| Error format | RFC 7807-style | flat `{"error": ..., "reason": ...}` |
| DOUBLE_SPEND_ATTEMPTED | may still resolve | **terminal** |
| SSE | none | `GET /events?callbackToken=...` (separate SSE service/port) |

### txStatus values

`UNKNOWN, RECEIVED, SENT_TO_NETWORK, ACCEPTED_BY_NETWORK, SEEN_ON_NETWORK, SEEN_MULTIPLE_NODES, DOUBLE_SPEND_ATTEMPTED, REJECTED, PENDING_RETRY, STUMP_PROCESSING, MINED, IMMUTABLE`

Terminal: `REJECTED` / `DOUBLE_SPEND_ATTEMPTED` / `MINED` / `IMMUTABLE`

### Honored headers

Only `X-CallbackUrl` / `X-CallbackToken` / `X-FullStatusUpdates`. `Authorization` and `XDeployment-ID` are not read by `POST /tx` (harmless to send; still sent for proxied deployments).

## EF construction in post_beef

Arcade does not accept BEEF, so `Arcade.post_beef(beef, txids)` does the following per txid:

1. Link parent transactions with `beef.find_transaction_for_signing(txid)`
2. Build EF hex with `tx.to_ef()` (inlines each input's satoshis + locking script)
3. Submit `{"rawTx": efHex}` to `POST /tx`

When the BEEF does not carry a parent's bytes (e.g. txidOnly entries), EF cannot be built. That txid is recorded with `service_error=True` (non-terminal) so cross-provider aggregation falls through to a BEEF-capable broadcaster (ARC / Bitails).

## Error classification (failover control)

Results of `post_raw_tx`:

| Condition | status | service_error | Meaning |
|---|---|---|---|
| 202 + non-terminal txStatus | `success` | — | accepted |
| 202 + `REJECTED` / `DOUBLE_SPEND_ATTEMPTED` | `error` | False | terminal (double spend sets `double_spend=True`) |
| 400 | `error` | **False** | the transaction itself is invalid; other providers will fail too |
| 429 | `rate_limited` | True | rate limited |
| 503 / 5xx / network exception | `error` | True | transient failure → fail over |

## Real-time status tracking via SSE

### How it works

1. Broadcast with the `X-CallbackToken` header (`arcadeCallbackToken`)
2. `ArcadeSSEClient` connects to `GET {arcadeUrl}/events?callbackToken=<token>`
3. Arcade streams `status` events (`{"txid", "txStatus", "timestamp"}`) for transactions submitted with that token
4. `TaskArcadeSSE` queues the events and processes them on the Monitor cycle

Note: Arcade's SSE runs as a **separate service/port** (default 8082) from the main API. If a reverse proxy does not consolidate them behind one origin, ensure `arcadeUrl` also resolves the SSE endpoint.

### Monitor integration

`TaskArcadeSSE` is not part of the default tasks. Add it explicitly:

```python
from bsv_wallet_toolbox.monitor import Monitor, MonitorOptions
from bsv_wallet_toolbox.monitor.tasks import TaskArcadeSSE

monitor = Monitor(MonitorOptions(chain="main", storage=storage, services=services))
monitor.add_default_tasks()
monitor.add_task(TaskArcadeSSE(monitor))
await monitor.start_tasks()
```

If `arcadeUrl` / `arcadeCallbackToken` are not configured, the task logs "SSE disabled" on its first trigger and stays idle (it does not raise).

### Event processing

| SSE txStatus | ProvenTxReq | Transactions |
|---|---|---|
| `SENT_TO_NETWORK` / `ACCEPTED_BY_NETWORK` / `SEEN_ON_NETWORK` / `SEEN_MULTIPLE_NODES` | `unsent`/`sending`/`callback` → `unmined` | → `unproven` |
| `MINED` / `IMMUTABLE` | sets `TaskCheckForProofs.check_now = True`, delegating to the existing proof machinery* | (updated when the proof is persisted) |
| `DOUBLE_SPEND_ATTEMPTED` | → `doubleSpend` | → `failed` |
| `REJECTED` | → `invalid` | → `failed` |

\* TS fetches the proof inline in the task; the Python port reuses the existing `TaskCheckForProofs` (via `Services.get_merkle_path` — Arcade is queried first when configured). The proof is validated against the wallet's own chaintracker before it is persisted.

### Reconnection and catch-up

- No automatic reconnection (same lifecycle as TS). Call `ArcadeSSEClient.fetch_events()` on demand (app open, balance refresh, etc.); if disconnected it reconnects with `Last-Event-ID` (a nanosecond timestamp) and replays missed events
- Persist `last_event_id` via the `on_last_event_id_changed` callback
- Arcade replays only non-terminal statuses on catch-up. Terminal history remains queryable via `GET /tx/{txid}`

## Proof retrieval (get_merkle_path)

`Arcade.get_merkle_path(txid, services)` queries `GET /tx/{txid}` and:

- Returns a proof only when `txStatus` is `MINED` / `IMMUTABLE` and a `merklePath` (BUMP hex) is present
- Otherwise (unmined / untracked / 404) returns empty with notes, so `Services.get_merkle_path` falls through to the next providers (WhatsOnChain / Bitails)

## Tests

```
pytest tests/services/test_arcade_provider.py   # provider (17 tests)
pytest tests/services/test_arcade_sse.py        # SSE client + monitor task (19 tests)
```

Neither requires network access (requests is mocked).

## Relationship to py-sdk

py-sdk also has an independent `Arcade` broadcaster (`bsv/broadcasters/arcade.py`). That one is the low-level API implementing the `Broadcaster` interface for `Transaction.broadcast()`, separate from this package's provider. Wallet flows in wallet-toolbox use this package's `services/providers/arcade.py`.
