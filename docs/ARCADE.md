# Arcade ブロードキャスター

py-wallet-toolbox における Arcade（[bsv-blockchain/arcade](https://github.com/bsv-blockchain/arcade)）対応のドキュメント。
Arcade は Teranode ネイティブの ARC 互換ブロードキャスターで、トランザクションの送信・ステータス追跡・マークルプルーフ取得・SSE によるリアルタイム通知を提供する。

TypeScript 実装（ts-wallet-toolbox の `Arcade.ts` / `ArcSSEClient.ts` / `TaskArcSSE.ts`）の移植。

## 構成

| コンポーネント | ファイル | 役割 |
|---|---|---|
| `Arcade` プロバイダー | `services/providers/arcade.py` | 送信（`post_beef` / `post_raw_tx`）とプルーフ取得（`get_merkle_path`） |
| `ArcadeSSEClient` | `services/providers/arcade_sse.py` | `GET /events` SSE ストリームのクライアント |
| `TaskArcadeSSE` | `monitor/tasks/task_arcade_sse.py` | SSE イベントを受けて ProvenTxReq / Transaction のステータスを更新する Monitor タスク |

`Arcade` は `ARC` のサブクラスではなく独立クラス（TS と同じ設計判断：監査済みの ARC トランスポートに手を入れない）。設定・結果型（`ArcConfig` / `PostTxResultForTxid` / `PostBeefResult` / `ArcMinerGetTxData`）は `providers/arc.py` から共有している。

## 有効化（opt-in）

Arcade はデフォルトでは無効。`create_default_options()` は `arcadeUrl` を設定しない（TS の `arcadeDefaultUrl()` とは意図的に非パリティ）。`WalletServicesOptions` に `arcadeUrl` を明示指定すると有効になる:

```python
from bsv_wallet_toolbox.services import Services

services = Services({
    "chain": "main",
    "arcadeUrl": "https://arcade-v2-us-1.bsvblockchain.tech",  # mainnet 公開エンドポイント
    # 任意:
    "arcadeApiKey": "...",            # Authorization: Bearer ヘッダー
    "arcadeHeaders": {...},           # 追加ヘッダー
    "arcadeCallbackUrl": "https://your.app/arc-ingest",  # Webhook 通知先
    "arcadeCallbackToken": "...",     # SSE / Webhook のスコープトークン（安定したウォレット単位の値）
})
```

- testnet の公開エンドポイントは未提供。
- 有効時、`arcade` は `post_beef_services` と `get_merkle_path_services` の**先頭**に登録される（TS と同じ優先順位）。失敗時は既存の ARC（GorillaPool / TAAL）→ Bitails にフォールオーバーする。

## ARC との差異（ワイヤ契約）

arcade サーバー実装（Go、本リポジトリ隣の `arcade/`）で確認済みの契約:

| | ARC | Arcade |
|---|---|---|
| 送信エンドポイント | `POST {url}/v1/tx` | `POST {url}/tx`（`/v1` なし） |
| ステータス取得 | `GET {url}/v1/tx/{txid}` | `GET {url}/tx/{txid}` |
| 送信エンコーディング | raw / BEEF V1 | **EF（Extended Format）推奨、raw 可。BEEF は 400 で拒否** |
| 成功レスポンス | 200 | **202** `{"txid", "status": 202, "txStatus": "RECEIVED"}` |
| 重複送信 | — | 202 で現在のステータスを返す（終端ステータスのこともある） |
| 400 の意味 | 各種 | **終端的な検証失敗** `{"error", "reason"}`。リトライ無意味 |
| エラー形式 | RFC 7807 風 | フラットな `{"error": ..., "reason": ...}` |
| DOUBLE_SPEND_ATTEMPTED | 回復の可能性あり | **終端** |
| SSE | なし | `GET /events?callbackToken=...`（別ポートの SSE サービス） |

### txStatus 値

`UNKNOWN, RECEIVED, SENT_TO_NETWORK, ACCEPTED_BY_NETWORK, SEEN_ON_NETWORK, SEEN_MULTIPLE_NODES, DOUBLE_SPEND_ATTEMPTED, REJECTED, PENDING_RETRY, STUMP_PROCESSING, MINED, IMMUTABLE`

終端: `REJECTED` / `DOUBLE_SPEND_ATTEMPTED` / `MINED` / `IMMUTABLE`

### 尊重されるヘッダー

`X-CallbackUrl` / `X-CallbackToken` / `X-FullStatusUpdates` のみ。`Authorization` と `XDeployment-ID` は `POST /tx` では読まれない（送っても無害。プロキシ配下の構成向けに送信は維持）。

## post_beef の EF 構築

Arcade は BEEF を受け付けないため、`Arcade.post_beef(beef, txids)` は txid ごとに:

1. `beef.find_transaction_for_signing(txid)` で親トランザクションをリンク
2. `tx.to_ef()` で EF hex を構築（各入力の satoshis + locking script をインライン化）
3. `POST /tx` に `{"rawTx": efHex}` を送信

BEEF が txidOnly エントリ等で親のバイト列を含まない場合は EF を構築できない。そのときは該当 txid を `service_error=True`（非終端）にして、集約側が BEEF 対応プロバイダー（ARC / Bitails）へフォールスルーできるようにする。

## エラー分類（フェイルオーバー制御）

`post_raw_tx` の結果:

| 条件 | status | service_error | 意味 |
|---|---|---|---|
| 202 + 非終端 txStatus | `success` | — | 受理 |
| 202 + `REJECTED` / `DOUBLE_SPEND_ATTEMPTED` | `error` | False | 終端（double spend は `double_spend=True`） |
| 400 | `error` | **False** | トランザクション自体が無効。他プロバイダーでも失敗する |
| 429 | `rate_limited` | True | レート制限 |
| 503 / 5xx / ネットワーク例外 | `error` | True | 一時的障害 → フォールオーバー |

## SSE によるリアルタイムステータス追跡

### 仕組み

1. ブロードキャスト時に `X-CallbackToken` ヘッダー（`arcadeCallbackToken`）を送る
2. `ArcadeSSEClient` が `GET {arcadeUrl}/events?callbackToken=<token>` に接続
3. Arcade が該当トークンのトランザクションの `status` イベント（`{"txid", "txStatus", "timestamp"}`）を配信
4. `TaskArcadeSSE` がイベントをキューし、Monitor サイクルで処理

注意: Arcade の SSE はメイン API とは**別サービス/別ポート**（デフォルト 8082）で動く。リバースプロキシで同一オリジンに集約されていない構成では、`arcadeUrl` が SSE も解決できることを確認すること。

### Monitor への組み込み

`TaskArcadeSSE` はデフォルトタスクには含まれない。明示的に追加する:

```python
from bsv_wallet_toolbox.monitor import Monitor, MonitorOptions
from bsv_wallet_toolbox.monitor.tasks import TaskArcadeSSE

monitor = Monitor(MonitorOptions(chain="main", storage=storage, services=services))
monitor.add_default_tasks()
monitor.add_task(TaskArcadeSSE(monitor))
await monitor.start_tasks()
```

`arcadeUrl` / `arcadeCallbackToken` が未設定の場合、タスクは初回 trigger 時に「SSE disabled」をログして待機状態のままになる（エラーにはならない）。

### イベント処理

| SSE txStatus | ProvenTxReq | Transactions |
|---|---|---|
| `SENT_TO_NETWORK` / `ACCEPTED_BY_NETWORK` / `SEEN_ON_NETWORK` / `SEEN_MULTIPLE_NODES` | `unsent`/`sending`/`callback` → `unmined` | → `unproven` |
| `MINED` / `IMMUTABLE` | `TaskCheckForProofs.check_now = True` を立てて既存のプルーフ取得機構に委譲※ | （プルーフ確定時に更新） |
| `DOUBLE_SPEND_ATTEMPTED` | → `doubleSpend` | → `failed` |
| `REJECTED` | → `invalid` | → `failed` |

※ TS はタスク内で直接プルーフを取得するが、Python 版は既存の `TaskCheckForProofs`（`Services.get_merkle_path` 経由 — arcade 設定時は arcade が最初に照会される）を再利用する。プルーフはウォレット自身のチェーントラッカーで検証されてから永続化される。

### 再接続とキャッチアップ

- 自動再接続はしない（TS と同じライフサイクル）。`ArcadeSSEClient.fetch_events()` を必要時（アプリ起動、残高更新など）に呼ぶと、切断されていれば `Last-Event-ID`（ナノ秒タイムスタンプ）付きで再接続し、未受信分を再生する
- `last_event_id` の永続化は `on_last_event_id_changed` コールバックで行う
- Arcade は非終端ステータスのみキャッチアップ再生する。終端履歴は `GET /tx/{txid}` で照会できる

## プルーフ取得（get_merkle_path）

`Arcade.get_merkle_path(txid, services)` は `GET /tx/{txid}` を照会し:

- `txStatus` が `MINED` / `IMMUTABLE` かつ `merklePath`（BUMP hex）がある場合のみプルーフを返す
- それ以外（未マイン / 未追跡 / 404）は notes を付けて空を返し、`Services.get_merkle_path` が次のプロバイダー（WhatsOnChain / Bitails）へフォールスルーする

## テスト

```
pytest tests/services/test_arcade_provider.py   # プロバイダー（17件）
pytest tests/services/test_arcade_sse.py        # SSE クライアント + Monitor タスク（19件）
```

いずれもネットワーク不要（requests をモック）。

## py-sdk との関係

py-sdk（`bsv/broadcasters/arcade.py`）にも独立した `Arcade` ブロードキャスターがある。そちらは `Transaction.broadcast()` 用の低レベル API（`Broadcaster` インターフェース実装）で、本パッケージのプロバイダーとは別物。wallet-toolbox のウォレットフローは本パッケージの `services/providers/arcade.py` を使う。
