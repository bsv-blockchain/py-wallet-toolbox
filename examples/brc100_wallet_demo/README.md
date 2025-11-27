# Wallet Demo - BRC-100 完全版デモアプリケーション

BSV Wallet Toolbox for Python を使った、**BRC-100 仕様の全28メソッド**を網羅したデモアプリケーションです。

## 🎯 このサンプルでできること

このデモアプリは、BRC-100 仕様で定義されている**全28メソッド**を試すことができます：

### 基本情報 (3メソッド)
1. ✅ `is_authenticated` - 認証状態の確認
2. ✅ `wait_for_authentication` - 認証の待機
3. ✅ `get_network` - ネットワーク情報の取得
4. ✅ `get_version` - バージョン情報の取得

### 鍵管理・署名 (7メソッド)
5. ✅ `get_public_key` - 公開鍵の取得（BRC-42）
6. ✅ `create_signature` - データへの署名（BRC-3）
7. ✅ `verify_signature` - 署名の検証
8. ✅ `create_hmac` - HMAC の生成
9. ✅ `verify_hmac` - HMAC の検証
10. ✅ `encrypt` - データの暗号化
11. ✅ `decrypt` - データの復号化

### 鍵リンケージ開示 (2メソッド)
12. ✅ `reveal_counterparty_key_linkage` - Counterparty Key Linkage の開示
13. ✅ `reveal_specific_key_linkage` - Specific Key Linkage の開示

### アクション管理 (4メソッド)
14. ✅ `create_action` - アクションの作成（BRC-100）
15. ✅ `sign_action` - アクションへの署名
16. ✅ `list_actions` - アクション一覧の表示
17. ✅ `abort_action` - アクションの中止

### 出力管理 (2メソッド)
18. ✅ `list_outputs` - 出力一覧の表示
19. ✅ `relinquish_output` - 出力の破棄

### 証明書管理 (4メソッド)
20. ✅ `acquire_certificate` - 証明書の取得（BRC-52）
21. ✅ `list_certificates` - 証明書一覧の表示
22. ✅ `prove_certificate` - 証明書の所有証明
23. ✅ `relinquish_certificate` - 証明書の破棄

### ID 検索 (2メソッド)
24. ✅ `discover_by_identity_key` - Identity Key による検索（BRC-31/56）
25. ✅ `discover_by_attributes` - 属性による検索

### ブロックチェーン情報 (2メソッド)
26. ✅ `get_height` - 現在のブロック高の取得
27. ✅ `get_header_for_height` - ブロックヘッダーの取得

### トランザクション (1メソッド)
28. ✅ `internalize_action` - トランザクションの内部化

**🎊 合計: 28/28 メソッド (100%) 実装完了！**

## 📋 必要要件

- Python 3.10 以上
- BSV Wallet Toolbox (`bsv-wallet-toolbox`)
- BSV SDK (`bsv-sdk`)

## 🚀 インストール

```bash
# デモディレクトリに移動
cd toolbox/py-wallet-toolbox/examples/brc100_wallet_demo

# 仮想環境を作成
python3 -m venv .venv

# 仮想環境をアクティベート
source .venv/bin/activate  # Linux/Mac
# または
.venv\Scripts\activate  # Windows

# 依存パッケージをインストール（これだけ！）
pip install -r requirements.txt
```

### requirements.txt について

`requirements.txt` には以下が含まれています：
- `bsv-wallet-toolbox` (ローカルの `../../` から開発モードでインストール)
- `python-dotenv` (環境変数管理)
- その他の依存関係は自動的にインストールされます

### インストールされる内容

`pip install -r requirements.txt` を実行すると、以下が自動的にインストールされます：
1. **bsv-wallet-toolbox** (ローカルから開発モード)
2. **bsv-sdk** (wallet-toolbox の依存関係)
3. **python-dotenv** (環境変数管理)
4. **requests** (HTTP クライアント)
5. **sqlalchemy** (データベース ORM)
6. その他の依存関係

## 💡 使い方

### デモアプリの起動

```bash
# これだけ！
python wallet_demo.py
```

### メニュー画面

```
🎮 BSV Wallet Toolbox - BRC-100 完全版デモ

【基本情報】(3メソッド)
  1. ウォレットを初期化
  2. 基本情報を表示 (is_authenticated, get_network, get_version)
  3. 認証を待機 (wait_for_authentication)

【ウォレット管理】(1メソッド)
  4. ウォレット情報を表示（アドレス、残高確認）

【鍵管理・署名】(7メソッド)
  5. 公開鍵を取得 (get_public_key)
  6. データに署名 (create_signature)
  7. 署名を検証 (verify_signature)
  8. HMAC を生成 (create_hmac)
  9. HMAC を検証 (verify_hmac)
 10. データを暗号化・復号化 (encrypt, decrypt)
 11. Counterparty Key Linkage を開示 (reveal_counterparty_key_linkage)
 12. Specific Key Linkage を開示 (reveal_specific_key_linkage)

【アクション管理】(4メソッド)
 13. アクションを作成 (create_action)
 14. アクションに署名 (sign_action) ※create_action に含む
 15. アクション一覧を表示 (list_actions)
 16. アクションを中止 (abort_action)

【出力管理】(2メソッド)
 17. 出力一覧を表示 (list_outputs)
 18. 出力を破棄 (relinquish_output)

【証明書管理】(4メソッド)
 19. 証明書を取得 (acquire_certificate)
 20. 証明書一覧を表示 (list_certificates)
 21. 証明書を破棄 (relinquish_certificate)
 22. 証明書の所有を証明 (prove_certificate) ※acquire に含む

【ID 検索】(2メソッド)
 23. Identity Key で検索 (discover_by_identity_key)
 24. 属性で検索 (discover_by_attributes)

【ブロックチェーン情報】(2メソッド)
 25. 現在のブロック高を取得 (get_height)
 26. ブロックヘッダーを取得 (get_header_for_height)

  0. 終了

📊 実装済み: 28/28 メソッド (100%)
```

## ⚙️ 設定（環境変数）

### 設定ファイルの作成

```bash
# env.example を .env にコピー
cp env.example .env

# .env ファイルを編集
nano .env
```

### 環境変数

```bash
# ネットワーク設定（デフォルト: test）
BSV_NETWORK=test  # 'test' または 'main'

# オプション: ニーモニックフレーズ
# BSV_MNEMONIC=your twelve word mnemonic phrase here...
```

## 📚 ファイル構成

```
wallet_demo/
├── README.md              # このファイル
├── MAINNET_GUIDE.md       # メインネット送受金ガイド
├── env.example            # 環境変数設定例
├── wallet_demo.py         # ✨ メインアプリ（BRC-100 全28メソッド対応）
└── src/                   # 機能モジュール
    ├── __init__.py                # モジュールエクスポート
    ├── config.py                  # 設定ヘルパー
    ├── address_management.py      # アドレス・残高管理
    ├── key_management.py          # 鍵管理（公開鍵、署名）
    ├── action_management.py       # アクション管理
    ├── certificate_management.py  # 証明書管理
    ├── identity_discovery.py      # ID 検索
    ├── crypto_operations.py       # 🆕 暗号化機能
    ├── key_linkage.py             # 🆕 鍵リンケージ開示
    ├── advanced_management.py     # 🆕 高度な管理機能
    └── blockchain_info.py         # 🆕 ブロックチェーン情報
```

## 🔑 自動ニーモニック生成

初回実行時、ニーモニックが設定されていない場合は自動的に生成されます：

```
⚠️  ニーモニックが設定されていません。新しいウォレットを生成します...

📋 ニーモニックフレーズ（12単語）:
   coffee primary dumb soon two ski ship add burst fly pigeon spare

💡 このニーモニックを使い続けるには、.env ファイルに追加してください:
   BSV_MNEMONIC=coffee primary dumb soon two ski ship add burst fly pigeon spare
```

## 🧪 テストネットでの実行

デフォルトでは **testnet** で動作します。実際の資金を使わずに安全にテストできます。

### Testnet Faucet から BSV を取得

1. `wallet_demo.py` を実行
2. メニューから「4. ウォレット情報を表示」を選択
3. 表示されたアドレスをコピー
4. Testnet Faucet: https://faucet.bitcoincloud.net/
5. エクスプローラーで確認: https://test.whatsonchain.com/

## 💰 メインネットでの実行

⚠️ **警告**: メインネットでは**実際の資金**が使用されます！

詳細は [`MAINNET_GUIDE.md`](MAINNET_GUIDE.md) を参照してください。

## 🎓 BRC-100 メソッド詳細

### 基本情報グループ

- **is_authenticated**: 常に `true` を返します（base 実装）
- **wait_for_authentication**: 即座に認証完了します
- **get_network**: 現在のネットワーク（mainnet/testnet）を返します
- **get_version**: ウォレットのバージョン番号を返します

### 鍵管理・署名グループ

- **get_public_key**: BRC-42 準拠の鍵導出
- **create_signature**: BRC-3 準拠の署名生成
- **verify_signature**: 署名の検証
- **create_hmac**: HMAC-SHA256 ベースの認証コード生成
- **verify_hmac**: HMAC の検証
- **encrypt**: ECIES による暗号化
- **decrypt**: ECIES による復号化

### アクショングループ

- **create_action**: トランザクションアクションの作成
- **sign_action**: アクションへの署名（ユーザー承認）
- **list_actions**: 作成されたアクションの一覧
- **abort_action**: アクションのキャンセル

### 証明書グループ

- **acquire_certificate**: BRC-52 準拠の証明書取得
- **list_certificates**: 保有証明書の一覧
- **prove_certificate**: 証明書の所有証明
- **relinquish_certificate**: 証明書の破棄

## 🛡️ セキュリティに関する注意

⚠️ **重要**: このサンプルコードは教育目的です。

1. **ニーモニックの保管**: 絶対に安全に保管してください
2. **秘密鍵の管理**: ファイルやログに出力しないでください
3. **権限管理**: Privileged Mode は慎重に使用してください
4. **テスト**: 最初はテストネットで十分にテストしてください
5. **少額から**: メインネットでは少額から始めてください

## 📖 参考資料

- [BRC-100 仕様](https://github.com/bitcoin-sv/BRCs/blob/master/transactions/0100.md)
- [BSV Wallet Toolbox ドキュメント](../../README.md)
- [メインネット送受金ガイド](MAINNET_GUIDE.md)
- [BSV SDK ドキュメント](https://github.com/bitcoin-sv/py-sdk)
- [BSV Block Explorer](https://whatsonchain.com/)

## 🤝 サポート

質問や問題がある場合は：

- GitHub Issues: [wallet-toolbox issues](https://github.com/bitcoin-sv/py-wallet-toolbox/issues)
- BSV 公式ドキュメント: https://docs.bsvblockchain.org/

## 📄 ライセンス

このサンプルコードは、BSV Wallet Toolbox と同じライセンスで提供されています。
