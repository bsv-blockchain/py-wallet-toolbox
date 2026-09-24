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
- When enabled, `arcade` is registered **first** in both `post_beef_services` and `get_merkle_path_services` (same priority as TS).
- `Services.post_beef` tries Arcade first, posting only the subject transaction as EF. A service error (EF cannot be built, rate limit, 5xx, network error, non-validation 400) falls over to the existing providers (TAAL, GorillaPool, then Bitails). A terminal validation failure or a double spend is returned without trying the others.

## Differences from ARC (wire contract)

Verified against the arcade server implementation (Go, in the sibling `arcade/` repository):

| | ARC | Arcade |
|---|---|---|
| Submit endpoint | `POST {url}/v1/tx` | `POST {url}/tx` (no `/v1` prefix) |
| Status endpoint | `GET {url}/v1/tx/{txid}` | `GET {url}/tx/{txid}` |
| Submission encoding | raw / BEEF V1 | **EF (Extended Format) only.** BEEF is rejected, and a raw tx fails validation (no per-input source data), both with 400 |
| Success response | 200 | **202** `{"txid", "status": 202, "txStatus": "RECEIVED"}` |
| Duplicate submit | — | 202 echoing the current status; a resubmitted `REJECTED` tx re-enters the pipeline (`RECEIVED`) |
| Meaning of 400 | various | `{"error": "transaction failed validation", "reason"}` is a **terminal validation failure** (including non-final nLockTime). Other 400s (`invalid callback url`, `invalid request`, ...) are request/config errors |
| Error format | RFC 7807-style | flat `{"error": ..., "reason": ...}` |
| DOUBLE_SPEND_ATTEMPTED | may still resolve | defined, but not emitted by current Arcade: double spends arrive as `REJECTED` |
| SSE | none | `GET /events?callbackToken=...` (separate SSE service/port) |

### txStatus values

`UNKNOWN, RECEIVED, SENT_TO_NETWORK, ACCEPTED_BY_NETWORK, SEEN_ON_NETWORK, SEEN_MULTIPLE_NODES, DOUBLE_SPEND_ATTEMPTED, REJECTED, PENDING_RETRY, STUMP_PROCESSING, MINED, IMMUTABLE`

Treated as final by the wallet: `REJECTED` / `DOUBLE_SPEND_ATTEMPTED` / `MINED` / `IMMUTABLE`. (Arcade's status lattice can still move `REJECTED` / `DOUBLE_SPEND_ATTEMPTED` forward, e.g. to `MINED`; like TS, the wallet does not follow that.)

### Honored headers

Only `X-CallbackUrl` / `X-CallbackToken` / `X-FullStatusUpdates`. `Authorization` and `XDeployment-ID` are not read by `POST /tx` (harmless to send; still sent for proxied deployments).

## EF construction in post_beef

Arcade does not accept BEEF, so `Arcade.post_beef(beef, txids)` does the following per txid:

1. Get the linked transaction: the subject tx returned when parsing a BEEF V1 / Atomic BEEF hex string, otherwise `beef.find_transaction_for_signing(txid)`
2. Build EF hex with `tx.to_ef()` (inlines each input's satoshis + locking script)
3. Submit `{"rawTx": efHex}` to `POST /tx`

When EF cannot be built (the BEEF does not carry a parent's bytes, e.g. txidOnly entries, or the input is a bare raw tx), nothing is posted. That txid is recorded with `service_error=True` (non-terminal) so cross-provider aggregation falls through to another broadcaster (ARC / Bitails). `Arcade.broadcast(tx)` behaves the same way.

## Error classification (failover control)

Results of `post_raw_tx`:

| Condition | status | service_error | Meaning |
|---|---|---|---|
| 202 + non-terminal txStatus | `success` | — | accepted |
| 202 + `REJECTED` / `DOUBLE_SPEND_ATTEMPTED` | `error` | False | terminal (double spend sets `double_spend=True`); defensive, current Arcade does not return these |
| 400 `transaction failed validation` | `error` | **False** | the transaction itself is invalid; other providers will fail too |
| other 400 (e.g. `invalid callback url`) | `error` | True | request/config error → fail over |
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
| `DOUBLE_SPEND_ATTEMPTED` | → `doubleSpend` | → `failed` (allocated inputs released) |
| `REJECTED` | → `invalid` | → `failed` (allocated inputs released) |

Transactions are resolved by txid (every user's transaction row for it).

\* TS fetches the proof inline in the task; the Python port reuses the existing `TaskCheckForProofs` (via `Services.get_merkle_path` — Arcade is queried first when configured), so the default tasks `TaskCheckForProofs` and `TaskNewHeader` must be installed. The proof's root is checked against the block header before it is persisted.

### Reconnection and catch-up

- No automatic reconnection (same lifecycle as TS). Call `ArcadeSSEClient.fetch_events()` on demand (app open, balance refresh, etc.); if disconnected it reconnects with `Last-Event-ID` and replays missed events
- A first connect sends no `Last-Event-ID`; Arcade then replays the current non-terminal statuses for the token. A reconnect sends the last event id (a nanosecond timestamp) minus 1ns, and Arcade replays every status newer than it, terminal ones included. Stepping back 1ns re-delivers events that share the last id's timestamp; processing them again is harmless
- `TaskArcadeSSE` does not persist `last_event_id`, so a process restart is a first connect. Terminal statuses reached while the process was down are picked up by the polling tasks. `ArcadeSSEClient` users can persist it via `on_last_event_id_changed`
- Connection errors reported to `on_error` have the callback token redacted

## Proof retrieval (get_merkle_path)

`Arcade.get_merkle_path(txid, services)` queries `GET /tx/{txid}` and:

- Returns a proof only when `txStatus` is `MINED` / `IMMUTABLE`, the `merklePath` BUMP hex parses, the block header resolves via `services.hash_to_header(blockHash)`, and the proof's root matches the header's `merkleRoot` (same checks as TS)
- The proof is returned as `{"blockHeight", "path"}`, the same shape as the other providers
- Otherwise (unmined / untracked / 404 / unknown header / root mismatch) returns empty with notes, so `Services.get_merkle_path` falls through to the next providers (WhatsOnChain / Bitails)

## Tests

```
pytest tests/services/test_arcade_provider.py   # provider + Services.post_beef routing
pytest tests/services/test_arcade_sse.py        # SSE client + monitor task
```

Neither requires network access (requests is mocked).

## Relationship to py-sdk

py-sdk also has an independent `Arcade` broadcaster (`bsv/broadcasters/arcade.py`). That one is the low-level API implementing the `Broadcaster` interface for `Transaction.broadcast()`, separate from this package's provider. Wallet flows in wallet-toolbox use this package's `services/providers/arcade.py`.
