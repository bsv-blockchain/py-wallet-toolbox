# ウォレットデータの保存場所について

## 📊 データ保存の仕組み

BSV Wallet Toolbox では、ウォレットのデータは **StorageProvider** によって管理されます。

### 🗄️ StorageProvider とは

`StorageProvider` は SQLAlchemy ORM を使用したデータベースバックエンドです。

#### 保存されるデータ

以下のデータが StorageProvider に保存されます：

1. **トランザクション** (`Transaction`)
   - トランザクション ID
   - トランザクションデータ（hex）
   - ラベル、説明
   - ステータス（未署名、署名済み、ブロードキャスト済み）

2. **アクション** (`Action`)
   - アクション参照（reference）
   - 説明
   - ステータス（保留中、署名済み、中止済み）
   - 関連トランザクション

3. **出力** (`Output`)
   - UTXO (Unspent Transaction Output)
   - Outpoint（txid:index）
   - Satoshis（金額）
   - スクリプト
   - バスケット（カテゴリ分け）
   - 使用可能/使用済みのステータス

4. **証明書** (`Certificate`)
   - 証明書タイプ
   - 発行者（certifier）
   - シリアル番号
   - フィールド（key-value）
   - 有効期限

5. **その他**
   - ユーザー情報 (`User`)
   - 設定 (`Settings`)
   - 同期状態 (`SyncState`)
   - 出力タグ (`OutputTag`, `OutputTagMap`)
   - トランザクションラベル (`TxLabel`, `TxLabelMap`)

### 💾 デフォルトの保存場所

#### ケース 1: StorageProvider を指定しない場合（デフォルト）

```python
# storage_provider を指定しない
wallet = Wallet(chain="test", key_deriver=key_deriver)
```

**→ データは保存されません！**
- `wallet.storage` は `None`
- `list_actions()`, `list_outputs()` などを呼ぶと `RuntimeError: storage provider is not configured` が発生
- アクションは作成できますが、永続化されません

#### ケース 2: SQLite StorageProvider を使用（インメモリ）

```python
from sqlalchemy import create_engine
from bsv_wallet_toolbox.storage import StorageProvider

# インメモリ SQLite データベース
engine = create_engine("sqlite:///:memory:")
storage = StorageProvider(
    engine=engine,
    chain="test",
    storage_identity_key="test-wallet",
)

# ストレージを設定してウォレットを初期化
wallet = Wallet(
    chain="test",
    key_deriver=key_deriver,
    storage_provider=storage,
)
```

**→ データはメモリに保存されます**
- アプリ終了時にすべてのデータが消える
- テスト用途に最適

#### ケース 3: SQLite StorageProvider を使用（ファイル）

```python
from sqlalchemy import create_engine
from bsv_wallet_toolbox.storage import StorageProvider

# ファイルベースの SQLite データベース
engine = create_engine("sqlite:///wallet.db")
storage = StorageProvider(
    engine=engine,
    chain="test",
    storage_identity_key="my-wallet",
)

wallet = Wallet(
    chain="test",
    key_deriver=key_deriver,
    storage_provider=storage,
)
```

**→ データは `wallet.db` ファイルに保存されます**
- 永続化されます（アプリを再起動しても残る）
- ファイルパス: `./wallet.db`（実行ディレクトリ）

#### ケース 4: PostgreSQL を使用（本番環境推奨）

```python
from sqlalchemy import create_engine
from bsv_wallet_toolbox.storage import StorageProvider

# PostgreSQL データベース
engine = create_engine("postgresql://user:password@localhost/wallet_db")
storage = StorageProvider(
    engine=engine,
    chain="main",
    storage_identity_key="production-wallet",
)

wallet = Wallet(
    chain="main",
    key_deriver=key_deriver,
    storage_provider=storage,
)
```

**→ データは PostgreSQL データベースに保存されます**
- 本番環境に最適
- 複数のウォレットインスタンスで共有可能
- トランザクション、バックアップ、レプリケーション対応

### 📋 現在のデモアプリの状態

**brc100_wallet_demo** では：

```python
# wallet_demo.py
wallet = Wallet(chain=network, key_deriver=key_deriver)
```

**→ StorageProvider を指定していません**

そのため：
- ✅ 動作するメソッド：
  - `is_authenticated`, `get_network`, `get_version`
  - `get_public_key`, `create_signature`, `verify_signature`
  - `create_hmac`, `verify_hmac`, `encrypt`, `decrypt`
  - `reveal_*_linkage`
  - `acquire_certificate`, `prove_certificate` (Privileged Mode)
  - `discover_by_*`

- ❌ エラーになるメソッド（storage 必須）：
  - `list_actions`, `abort_action`
  - `list_outputs`, `relinquish_output`
  - `list_certificates`, `relinquish_certificate`
  - `internalize_action`

### 🔧 デモアプリに StorageProvider を追加する方法

`src/config.py` に StorageProvider 初期化関数を追加すれば、すべてのメソッドが動作します：

```python
from sqlalchemy import create_engine
from bsv_wallet_toolbox.storage import StorageProvider

def get_storage_provider(network: str) -> StorageProvider:
    """StorageProvider を作成します。"""
    # SQLite ファイルにデータを保存
    db_file = f"wallet_{network}.db"
    engine = create_engine(f"sqlite:///{db_file}")
    
    storage = StorageProvider(
        engine=engine,
        chain=network,
        storage_identity_key=f"{network}-wallet",
    )
    
    # データベーステーブルを初期化
    storage.make_available()
    
    return storage
```

そして `wallet_demo.py` で使用：

```python
storage = get_storage_provider(self.network)
self.wallet = Wallet(
    chain=self.network,
    key_deriver=self.key_deriver,
    storage_provider=storage,
)
```

### 🗂️ データベーススキーマ

StorageProvider は以下のテーブルを作成します：

- `users` - ユーザー情報
- `transactions` - トランザクション
- `outputs` - UTXO
- `output_baskets` - 出力のグループ化
- `output_tags` - 出力のタグ
- `output_tag_map` - 出力とタグのマッピング
- `tx_labels` - トランザクションラベル
- `tx_label_map` - トランザクションとラベルのマッピング
- `certificates` - 証明書
- `certificate_fields` - 証明書フィールド
- `proven_tx` - 証明済みトランザクション
- `proven_tx_req` - トランザクション証明リクエスト
- `sync_state` - 同期状態
- `monitor_events` - モニタリングイベント
- `commissions` - 手数料情報
- `settings` - ウォレット設定

### 📍 ファイル保存場所の例

#### SQLite の場合

```
brc100_wallet_demo/
├── wallet_test.db    # テストネット用データベース
├── wallet_main.db    # メインネット用データベース
└── ...
```

#### PostgreSQL の場合

```
PostgreSQL サーバー
└── wallet_db データベース
    ├── users テーブル
    ├── transactions テーブル
    ├── outputs テーブル
    └── ...（15個のテーブル）
```

### 💡 まとめ

1. **デフォルト**: StorageProvider なし → データは保存されない（一部メソッドが使えない）
2. **インメモリ SQLite**: `sqlite:///:memory:` → メモリ内（終了で消える）
3. **ファイルベース SQLite**: `sqlite:///wallet.db` → ファイルに保存
4. **PostgreSQL**: `postgresql://...` → サーバーに保存（本番推奨）

現在のデモアプリは StorageProvider を使用していないため、鍵管理や署名などの基本機能は動作しますが、アクション・出力・証明書の永続化機能は使えません。

必要であれば、StorageProvider 対応版のデモアプリも作成できますので、お知らせください！

