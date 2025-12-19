# E2E Simple Example: 2ウォレット往復送金テスト

Alice と Bob の 2 つのウォレット間で相互に送受金できることを確認するエンドツーエンドテストです。

## 概要

このスクリプトは以下の流れでテストを実行します：

1. **ウォレット初期化**: Alice と Bob の独立した 2 つのウォレットを作成
2. **Faucet 受金**: Alice のウォレットアドレスを表示し、ユーザーが Faucet から入金
3. **Transaction Internalize** (オプション): Faucet トランザクションを BRC-29 wallet payment プロトコルで取り込み
4. **双方向送金**:
   - Alice: 残高の 80% を Bob に P2PKH 送金
   - Bob: 受け取った資金から 80% を Alice に P2PKH 送金
5. **結果表示**: 最終残高とトランザクション ID を表示

## セットアップ

### 1. 環境ファイルの準備

```bash
# スクリプトディレクトリに移動
cd examples/e2e_simple_example

# .env ファイルを作成
cp env.example .env
```

### 2. .env の設定

`env.example` をコピーした `.env` ファイルに以下の値を設定します：

```env
# ネットワーク選択（testnet 推奨）
BSV_NETWORK=test

# Taal ARC API キー（必須）
TAAL_ARC_API_KEY=your_taal_arc_api_key_here

# ストレージオプション（次のいずれかを選択）

# オプション A: ローカル SQLite ストレージ（デフォルト）
# この場合、wallet_alice.db と wallet_bob.db がローカルに作成されます
# USE_STORAGE_SERVER の設定なし

# オプション B: リモートストレージサーバー（BRC-104 認証必須）
# USE_STORAGE_SERVER=true
# STORAGE_SERVER_URL=http://localhost:8080
```

**注意**: `TAAL_ARC_API_KEY` は必須です。テストネットの場合は以下から取得できます：
- https://www.taal.com/ でアカウントを作成して API キーを取得

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

または、プロジェクトをローカルで開発している場合：

```bash
pip install -e ../../
python-dotenv
```

## 実行方法

```bash
python e2e_two_party_roundtrip.py
```

### 実行の流れ

1. **スクリプト起動**
   - 環境変数を読み込み
   - Alice と Bob のウォレットを初期化
   - ストレージ接続を確認

2. **Alice のアドレス表示**
   ```
   Alice's receive address: <address>
   ```
   この出力を確認してください。

3. **Faucet からの入金を待機**
   - スクリプトは以下のいずれかから入金するよう指示します：
     - テストネット: https://testnet-faucet.bsv.dev/
     - メインネット: https://faucet.bsv.dev/
   - ブロックエクスプローラで確認後、`Enter` キーを押して続行

4. **トランザクション ID の入力（オプション）**
   - Faucet トランザクションの txid を入力（64 文字の 16 進数）
   - または空のまま `Enter` を押して internalize をスキップ
   - スキップした場合、後続の送金も実行されません

5. **Alice → Bob 送金**
   - Alice の残高の 80% を Bob に送金
   - 成功後、トランザクション ID が表示されます

6. **Bob → Alice 送金**
   - Bob が受け取った資金から 80% を Alice に返送
   - 成功後、トランザクション ID が表示されます

7. **結果表示**
   - 最終残高とトランザクション ID を表示
   - ブロックエクスプローラで検証するための情報を提供

## トラブルシューティング

### `TAAL_ARC_API_KEY not set` エラー

**原因**: `.env` ファイルに `TAAL_ARC_API_KEY` が設定されていません

**対策**:
```bash
# .env ファイルを確認
cat .env

# TAAL_ARC_API_KEY が見つからない場合は設定
echo "TAAL_ARC_API_KEY=your_key_here" >> .env
```

### ストレージ接続エラー

**ローカルストレージの場合**:
- `wallet_alice.db` と `wallet_bob.db` がスクリプトと同じディレクトリに作成されます
- `.gitignore` に登録済みなので心配なし

**リモートストレージの場合**:
```
Error: Unable to connect to storage server
```

**対策**:
1. `STORAGE_SERVER_URL` が正しいか確認
2. ストレージサーバーが起動しているか確認
3. ローカルストレージでの実行に切り替え（`USE_STORAGE_SERVER` をコメントアウト）

### Faucet 入金タイムアウト

**原因**: ブロックチェーンへの反映が遅い

**対策**:
1. ブロックエクスプローラで入金を確認
2. テストネットの場合、数分待つ
3. スクリプトを再実行し、同じ txid で internalize

### 送金に失敗する場合

**原因**: 残高不足またはネットワークエラー

**対策**:
1. 十分な残高があるか確認（`Faucet 入金の際に十分な額を送る`）
2. ネットワーク接続を確認
3. `TAAL_ARC_API_KEY` が有効か確認

## 検証方法

トランザクションはテスト時に **確実にブロードキャスト** されます。ブロックエクスプローラで検証：

### テストネット
- https://whatsonchain.com/ (testnet を選択)
- 検索フィールドにトランザクション ID を入力

### メインネット
- https://www.bsvexplorer.io/
- 検索フィールドにトランザクション ID を入力

## ストレージについて

### ローカルストレージ（デフォルト）

- Alice: `wallet_alice.db`
- Bob: `wallet_bob.db`
- SQLite 形式
- 自動的に `.gitignore` に登録済み

### リモートストレージ

- BRC-104 認証が必須
- `STORAGE_SERVER_URL` で指定したサーバーを使用
- 複数のアプリケーション間でウォレット状態を共有可能

## 注意事項

### セキュリティ

- ✅ `.env` ファイルに秘密鍵やシードを保存しないでください（テストのみの使用）
- ✅ `.env` ファイルは `.gitignore` に登録済みなので Git でコミットされません
- ✅ 本番環境では環境変数や AWS Secrets Manager など安全な方法で管理してください

### テストネット推奨

- テストネットで十分にテストしてからメインネットを使用してください
- メインネットでのテストには実資金が必要です

### ARC ブロードキャスト

- このテストはスクリプトで Taal ARC API を使用してブロードキャストします
- Bitails と GorillaPool はこのテストでは無効化されています
- 確実なブロードキャストのため、十分な手数料で設定されています

## 実装詳細

### ストレージ切り替え

スクリプトは以下の優先度でストレージを選択します：

1. `USE_STORAGE_SERVER=true` が設定されている場合 → リモートストレージ
2. それ以外の場合 → ローカル SQLite

### Services の初期化

- `TAAL_ARC_API_KEY` から Taal ARC API キーを注入
- Bitails と GorillaPool は無効化
- リトライロジックとキャッシング機構は有効

### P2PKH 送金

- 標準的な Pay-to-Public-Key-Hash（P2PKH）の形式
- `bsv.script.P2PKH` クラスを使用したロック

### BRC-29 Wallet Payment Protocol

Faucet からの受け入れは BRC-29 wallet payment プロトコルで処理：

- `senderIdentityKey`: Faucet の公開鍵（PrivateKey(1).public_key()）
- `derivationPrefix/Suffix`: テスト用固定値（base64 エンコード）

## ライセンス

このテストスクリプトは wallet-toolbox に含まれます。

