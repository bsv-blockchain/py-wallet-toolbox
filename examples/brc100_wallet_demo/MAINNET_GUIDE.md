# メインネットでの送受金テストガイド

このガイドでは、Python wallet-toolbox を使って実際に BSV の送受金をテストする方法を説明します。

## ⚠️ 重要な注意事項

**メインネットでは実際の資金が使用されます！**

- テスト目的であれば、少額（0.001 BSV 程度）から始めてください
- ニーモニックフレーズを**絶対に**安全に保管してください
- 失っても問題ない金額でテストしてください

## 📋 準備

### 1. ニーモニックの生成と保管

```bash
cd toolbox/py-wallet-toolbox/examples/simple_wallet
source .venv/bin/activate

# 新しいウォレットを生成（testnet）
python3 wallet_address.py
```

生成されたニーモニックを**安全な場所**に保管してください：
```
📋 ニーモニックフレーズ（12単語）:
   word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12
```

### 2. .env ファイルの作成

```bash
# .env ファイルを作成
cp env.example .env

# エディタで編集
nano .env
```

`.env` ファイルの内容:
```bash
# メインネットを使用
BSV_NETWORK=main

# 先ほど生成したニーモニックを追加
BSV_MNEMONIC=word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12
```

保存して閉じます（nano の場合: Ctrl+X → Y → Enter）

## 💰 ステップ 1: ウォレットアドレスの確認

```bash
# メインネットでウォレットアドレスを表示
python3 wallet_address.py
```

出力例:
```
🔴 ネットワーク: メインネット（本番環境）
⚠️  警告: メインネットを使用しています。実際の資金が使用されます！

📍 受信用アドレス:
   1YourMainnetAddressHere...

🔍 Mainnet Explorer:
   https://whatsonchain.com/address/1YourMainnetAddressHere...
```

アドレスをコピーしてください。

## 💸 ステップ 2: BSV を送金

以下のいずれかの方法で、ウォレットアドレスに BSV を送金します：

### オプション A: 取引所から送金

1. 取引所（Binance, OKX など）にログイン
2. BSV の出金ページに移動
3. 出金先アドレスに、先ほどコピーしたアドレスを入力
4. 少額（0.001 BSV など）を送金

### オプション B: 他のウォレットから送金

既に BSV ウォレットをお持ちの場合、そこから送金できます。

### オプション C: BSV を購入

取引所で BSV を購入してから送金します。

## 🔍 ステップ 3: 送金の確認

### 方法 1: ブロックチェーンエクスプローラー

ブラウザで以下の URL を開きます：
```
https://whatsonchain.com/address/1YourMainnetAddressHere...
```

- トランザクション履歴が表示されます
- 送金後、通常 10 分程度で確認されます
- 1 confirmation 以上あれば安全です

### 方法 2: スクリプトで確認

```bash
python3 wallet_address.py
```

エクスプローラーのリンクが表示されるので、クリックして確認できます。

## 🎉 ステップ 4: 受信完了

エクスプローラーで送金が確認されたら、受信完了です！

```
Balance: 0.001 BSV
Transactions: 1
```

## 🚀 ステップ 5: 送金のテスト（オプション）

### 他のアドレスに送金する場合

現在、送金機能は開発中です。以下の方法で送金できます：

1. **他のウォレットを使用**: HandCash, RelayX などの既存ウォレット
2. **カスタムスクリプト**: `create_action.py` を参考に送金スクリプトを作成

## ❓ よくある質問

### Q: 送金が届かない

A: 以下を確認してください：
- アドレスが正しいか
- ブロックチェーンエクスプローラーでトランザクションが確認できるか
- 十分な confirmation があるか（通常 1 以上）

### Q: ニーモニックを忘れた

A: ニーモニックを紛失すると**資金を永久に失います**。バックアップを必ず取ってください。

### Q: テストネットに戻したい

A: `.env` ファイルを編集:
```bash
BSV_NETWORK=test
```

## 🔒 セキュリティのベストプラクティス

1. **ニーモニックの保管**
   - 紙に書いて金庫に保管
   - パスワードマネージャーで暗号化
   - 複数の場所にバックアップ

2. **絶対にしないこと**
   - ニーモニックをスクリーンショット
   - ニーモニックをクラウドに保存
   - ニーモニックを他人に教える
   - ニーモニックをメールで送信

3. **推奨事項**
   - テスト用と本番用で別のウォレットを使用
   - 少額でテストしてから大きな金額を扱う
   - 定期的にバックアップを確認

## 📚 参考リンク

- BSV Block Explorer: https://whatsonchain.com/
- BSV 公式サイト: https://bitcoinsv.com/
- Wallet Toolbox ドキュメント: ../../README.md

## 🆘 サポート

問題が発生した場合は、GitHub Issues で報告してください。

---

**免責事項**: このガイドは教育目的です。暗号通貨の取り扱いには十分注意し、自己責任で行ってください。

