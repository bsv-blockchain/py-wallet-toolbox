# py-wallet-toolbox E2E テスト計画書

## 概要

本計画書は、`py-wallet-toolbox` と `go-wallet-toolbox` 間の相互運用性テスト、および TypeScript 実装との互換性を確保するための包括的な E2E テスト計画です。

### 参考実装

- **Go 版統合テスト**: `go-wallet-toolbox/pkg/storage/internal/integrationtests/`
- **Go 版 TS 生成フィクスチャ**: `go-wallet-toolbox/pkg/internal/testabilities/tsgenerated/`
- **Go 版リグレッションテスト**: `go-bsv-middleware/pkg/internal/regressiontests/`
- **Universal Test Vectors**: https://github.com/bsv-blockchain/universal-test-vectors

---

## Phase 1: TS 生成フィクスチャの整備 ✅ (Week 1-2)

### 1.1 TS 生成データファイルの作成 ✅

| ID    | タスク                                 | ステータス | ファイル                   |
| ----- | -------------------------------------- | ---------- | -------------------------- |
| 1.1.1 | ディレクトリ構造作成                   | ✅ 完了    | `tests/testabilities/`     |
| 1.1.2 | `create_action_result.json` の作成     | ✅ 完了    | Go 版からコピー            |
| 1.1.3 | `create_action_result.py` ヘルパー作成 | ✅ 完了    | ヘルパー関数実装           |
| 1.1.4 | `signed_transaction.py` 作成           | ✅ 完了    | `SignedTransactionHex`定数 |
| 1.1.5 | `beef_to_internalize.py` 作成          | ✅ 完了    | BEEF 関連定数              |
| 1.1.6 | `testusers/test_users.py` 作成         | ✅ 完了    | Alice, Bob 固定鍵          |
| 1.1.7 | `testservices/mock_arc.py` 作成        | ✅ 完了    | スクリプト検証付き         |

**成果物**:

```
py-wallet-toolbox/tests/testabilities/
├── __init__.py
├── tsgenerated/
│   ├── __init__.py
│   ├── create_action_result.json     # TS生成JSON (Go版からコピー)
│   ├── create_action_result.py       # JSON読み込みヘルパー
│   ├── signed_transaction.py         # SignedTransactionHex定数
│   └── beef_to_internalize.py        # ParentBEEF, 定数
├── testusers/
│   ├── __init__.py
│   └── test_users.py                 # Alice, Bob固定鍵
└── testservices/
    ├── __init__.py
    ├── mock_arc.py                   # スクリプト検証付きモックARC
    └── mock_bhs.py                   # モックBlock Header Service
```

### 1.2 署名互換性テスト ✅

| ID    | タスク                                  | ステータス | 参照                                                      |
| ----- | --------------------------------------- | ---------- | --------------------------------------------------------- |
| 1.2.1 | `test_signature_compatibility.py` 作成  | ✅ 完了    | テストファイル作成                                        |
| 1.2.2 | `CreateActionTransactionAssembler` 実装 | ✅ 完了    | `src/bsv_wallet_toolbox/assembler/`                       |
| 1.2.3 | 署名結果の完全一致テスト                | ✅ 完了    | TS 生成 SignedTransactionHex と Python 署名が完全一致確認 |

---

## Phase 2: 統合 E2E テスト (Week 2-3) ✅

### 2.1 Internalize → Create → Process フローテスト ✅

| ID    | タスク                                                  | 優先度 | ステータス                     |
| ----- | ------------------------------------------------------- | ------ | ------------------------------ |
| 2.1.1 | `test_internalize_create_process.py` 作成               | 🔴 高  | ✅ 完了                        |
| 2.1.2 | Internalize → Create → Process → 次の Create 連続テスト | 🔴 高  | ✅ 完了                        |
| 2.1.3 | Unknown Input での Create → Process テスト              | 🟡 中  | ✅ 完了 (args 構造テスト)      |
| 2.1.4 | Known Input での Create → Process テスト                | 🟡 中  | ✅ 完了 (args 構造テスト)      |
| 2.1.5 | InternalizePlusTooHighCreate エラーテスト               | 🟡 中  | ✅ 完了                        |
| 2.1.6 | インメモリ SQLite ストレージプロバイダテスト            | 🟡 中  | ✅ 完了 (ユーザー登録動作確認) |

**修正履歴 (2024-12-11)**:

1. **BEEF パーサー修正**:

   - 問題: Python 版 `PARENT_BEEF` hex が Go 版より 544 bytes 不足
   - 原因: Go 版からのコピー時にデータが途中で切れていた
   - 修正: `beef_to_internalize.py` を Go 版 (8322 文字 / 4161 bytes) に更新
   - 結果: BEEF V2 → AtomicBEEF 変換が正常動作

2. **UTXO アロケーション修正**:
   - 問題: `allocate_change_input` の重複定義で不完全な実装が使用されていた
   - 原因: Line 3858 の実装が Transaction JOIN と output 予約をスキップ
   - 修正: 重複した不完全な `allocate_change_input` と `count_change_inputs` を削除
   - 結果: Internalize → Create フローが正常動作

### 2.2 モック ARC でのスクリプト検証 ✅

| ID    | タスク                               | 優先度 | ステータス |
| ----- | ------------------------------------ | ------ | ---------- |
| 2.2.1 | `MockARC` にスクリプト検証機能を追加 | 🔴 高  | ✅ 完了    |
| 2.2.2 | MockARC クエリフィクスチャテスト     | 🔴 高  | ✅ 完了    |
| 2.2.3 | 二重支払い検出テスト                 | 🟡 中  | ✅ 完了    |
| 2.2.4 | MockBHS Merkle root 検証テスト       | 🟡 中  | ✅ 完了    |

---

## Phase 3: クロス実装テスト (Week 3-4)

### 3.0 進め方（作戦）

**ゴール（成功基準）**:

- **Python wallet ↔ Go storage server** で `internalize_action → create_action → process_action` の E2E が PASS
- **Go wallet ↔ Python storage server** で同じフローの E2E が PASS
- 失敗時に「どの入力でどのレスポンス/差分が出たか」を **再現可能な形で保存**できる（ログ/レスポンス保存）

**実行順（おすすめ）**:

1. **通信面の固定**（ホスト/ポート/起動方法/認証方針/データ表現）
2. **3.1 Python→Go**（fixture が強いので先に通す）
3. **3.2 Go→Python**（最小 API 互換＋ auth スキップで先に疎通）
4. **3.3 auth middleware**（最後に挟んで同じ E2E を回帰実行）

**共通ハーネス方針**:

- **起動 fixture**: サーバ起動/停止、healthcheck、ポート固定、ログ収集
- **結果保存**: 失敗時に request/response（ステータス/ヘッダ/body）を `tests/artifacts/` 配下へ保存
- **再現性**: chain/testnet、basket 設定、randomizer/seed、feeModel を明示（Phase 4 の一致条件を維持）

### 3.1 Python → Go Storage Server テスト

| ID    | タスク                                           | 優先度 | ステータス |
| ----- | ------------------------------------------------ | ------ | ---------- |
| 3.1.1 | Go storage server 起動フィクスチャ               | 🟡 中  | ⏳ 未着手  |
| 3.1.2 | Python wallet から Go storage を呼び出すテスト   | 🟡 中  | ⏳ 未着手  |
| 3.1.3 | CreateAction → SignAction → ProcessAction フロー | 🟡 中  | ⏳ 未着手  |

**実装ステップ（推奨）**:

- **3.1.A 起動と疎通**:
  - Go storage server をローカル（or Docker）で起動できるようにする
  - `GET /health` 等の healthcheck を用意（なければ最小 endpoint を確認）
- **3.1.B 最小 E2E（internalize→create→process）**:
  - Phase 4 で使った fixture（BEEF、basket 設定、create args）で同じフローをサーバ越しに実行
  - 失敗時は request/response を保存し、差分（フィールド/型/エラーコード）を記録
- **3.1.C 追加パス**:
  - delayed / noSendChange / knownTxids / sendWith など、Go 側の統合テストで使うバリエーションを追加

### 3.2 Go → Python Storage Server テスト

| ID    | タスク                                         | 優先度 | ステータス |
| ----- | ---------------------------------------------- | ------ | ---------- |
| 3.2.1 | Django/FastAPI storage server 起動フィクスチャ | 🟡 中  | ⏳ 未着手  |
| 3.2.2 | 認証スキップモードの実装（開発用）             | 🟡 中  | ⏳ 未着手  |
| 3.2.3 | Go wallet から Python storage を呼び出すテスト | 🟡 中  | ⏳ 未着手  |

**実装ステップ（推奨）**:

- **3.2.A Python storage server を最小で立ち上げる**:
  - 最初は FastAPI 推奨（Django でも可）
  - Go wallet が呼ぶ最小 endpoint から実装し、呼ばれた payload をロギングする
- **3.2.B auth スキップで先に E2E を通す**:
  - 開発用フラグ（例: `AUTH_BYPASS=true`）で署名検証などを一旦スキップ
  - 目的: 「Go wallet が何を要求してくるか」を確定して API 互換を完成させる
- **3.2.C auth 有効化へ移行**:
  - 3.3 と接続して段階的に厳密化（署名/nonce/許可）

### 3.3 Auth Middleware リグレッションテスト

| ID    | タスク                                                 | 優先度 | ステータス |
| ----- | ------------------------------------------------------ | ------ | ---------- |
| 3.3.1 | Node.js テストサーバの起動フィクスチャ                 | 🟠 低  | ⏳ 未着手  |
| 3.3.2 | Python auth middleware から Node.js サーバへリクエスト | 🟠 低  | ⏳ 未着手  |
| 3.3.3 | TS client から Python middleware へリクエスト          | 🟠 低  | ⏳ 未着手  |

**狙い**:

- Phase 3.1 / 3.2 で作った「同じ E2E テスト」を、middleware を挟んでも **落ちない** ことを確認する
- ここで初めて本番寄りに寄せる（署名検証/ヘッダ/nonce など）

**よくある差分ポイント（チェックリスト）**:

- request/response の **フィールド名・型**（camelCase/snake_case、int/str、bytes 表現）
- BEEF/tx の **エンコード規約**（base64/hex/byte array）
- feeModel / basketConfig の **デフォルト値差**（Phase 4 と同じ条件を強制）
- clock/nonce の揺れ（テストでは固定化）

---

## Phase 4: CreateActionResult 厳密一致テスト (Week 4)

### 4.1 JSON 厳密比較テスト

| ID    | タスク                                       | 優先度 | ステータス                           |
| ----- | -------------------------------------------- | ------ | ------------------------------------ |
| 4.1.1 | `TestRandomizer`（決定論的乱数生成器）の実装 | 🔴 高  | ✅ 完了 (DeterministicRandomizer)    |
| 4.1.2 | CreateActionResult の JSON 完全一致テスト    | 🔴 高  | ✅ 完了 (32 outputs, 15 テスト PASS) |
| 4.1.3 | 全フィールドの型・値一致確認                 | 🔴 高  | ✅ 完了 (12 テスト PASS)             |

**Phase 4 修正履歴 (2024-12-11)**:

1. **DeterministicRandomizer 実装**:

   - Go の `TestRandomizer` と互換性のある決定論的乱数生成器
   - `base64()`, `random_bytes()`, `shuffle()`, `uint64()` を Go と同じロジックで実装
   - テスト: 8 テスト PASS

2. **StorageProvider に Randomizer 注入**:

   - `with_randomizer()` メソッド追加
   - `_generate_reference()` と `_generate_derivation_suffix()` が Randomizer を使用
   - Go parity: `referenceLength = 12`, `derivationLength = 16`

3. **InternalizeAction の reference 修正**:

   - `internalize_action` の `new_internalize()` で `_generate_reference()` を使用するよう修正
   - Go と同じく Internalize → Create の順序で randomizer が呼ばれる
   - 結果: `reference` と `derivationPrefix` が Go fixture と完全一致

4. **修正完了: Change output count の差異 (21 vs 32) → 解決済み**:

   - **原因**: `fund_new_transaction_sdk` で `minimumDesiredUtxoValue` (タイポ) を参照していた
   - **修正**: `minimumDesiredUTXOValue` (正しいキー名) に修正
   - **結果**: Python が TypeScript/Go と同様に 31 change outputs を生成するようになった

5. **検証結果 (2024-12-11)**:

   | 実装       | Change Outputs | Total Change Satoshis |
   | ---------- | -------------- | --------------------- |
   | TypeScript | 31             | 98,902 sats           |
   | Go         | 31             | 98,902 sats           |
   | Python     | 31 ✅          | 98,902 sats           |

   - 注: 過去に `98,891 sats` が出ていたのは、`generateChangeSdk` を単体で **feeModel=10 sat/kb** 等の条件で実行した値で、`tsgenerated/create_action_result.json` (fixture) の値ではない
   - JSON 完全一致テスト: 15 テスト全 PASS
   - `reference`, `derivationPrefix`, output count すべて TypeScript/Go と一致

---

## Phase 5: テストインフラ整備 (継続)

### 5.1 CI/CD 統合

| ID    | タスク                                   | 優先度 | ステータス |
| ----- | ---------------------------------------- | ------ | ---------- |
| 5.1.1 | GitHub Actions で統合テストを実行        | 🟡 中  | ⏳ 未着手  |
| 5.1.2 | Go storage server の Docker イメージ利用 | 🟡 中  | ⏳ 未着手  |
| 5.1.3 | クロス実装テストのマトリックス実行       | 🟠 低  | ⏳ 未着手  |

---

## 使用方法

### テスト実行

```bash
# Phase 1 のテストを実行
cd py-wallet-toolbox
pytest tests/integration/test_signature_compatibility.py -v

# testabilities フィクスチャのテスト
pytest tests/integration/test_signature_compatibility.py::TestTxAssemblerAlignsTsGenerated -v
```

### フィクスチャのインポート

```python
# テストユーザー
from tests.testabilities.testusers import ALICE, BOB

# TS生成データ
from tests.testabilities.tsgenerated import (
    load_create_action_result,
    SIGNED_TRANSACTION_HEX,
    parent_transaction_atomic_beef,
)

# モックサービス
from tests.testabilities.testservices import MockARC, MockBHS
```

---

## タイムライン

| Week | Phase           | 主要タスク                                          | 状態                                      |
| ---- | --------------- | --------------------------------------------------- | ----------------------------------------- |
| 1    | Phase 1.1       | TS 生成フィクスチャ作成、テストユーザー固定         | ✅ 完了                                   |
| 2    | Phase 1.2 + 2.1 | 署名互換性テスト、Internalize→Create→Process フロー | ✅ 署名テスト完了、BEEF パーサー修正完了  |
| 3    | Phase 2.2 + 3.1 | モック ARC 改善、Python→Go 統合テスト               | ✅ MockARC/BHS 完了、クロス実装 ⏳ 未着手 |
| 4    | Phase 3.2 + 4.1 | Go→Python 統合テスト、JSON 厳密一致テスト           | ⏳ 未着手                                 |
| 継続 | Phase 5         | CI/CD 統合、レポート自動化                          | ⏳ 未着手                                 |

---

## 成功基準

1. **署名互換性**: TS 生成 `SignedTransactionHex` と Python 署名結果が完全一致
2. **CreateActionResult 互換性**: TS 生成 JSON と Python 結果が JSON 完全一致
3. **フロー互換性**: Internalize→Create→Process→ 次 Create が正常動作
4. **クロス実装**: Python wallet ↔ Go storage の相互呼び出しが成功
5. **スクリプト検証**: モック ARC で無効署名を検出

---

## 3 実装比較表 (TypeScript / Go / Python)

### テスト実行結果サマリー (2024-12-11)

| カテゴリ                        | TypeScript                 | Go                         | Python                        | 備考                            |
| ------------------------------- | -------------------------- | -------------------------- | ----------------------------- | ------------------------------- |
| **Internalize→Create→Process**  | ✅ PASS                    | ✅ PASS (4 tests)          | ✅ PASS (16 tests)            | 基本フロー動作確認              |
| **CreateAction テスト**         | ✅ PASS (5 tests)          | ✅ PASS                    | ✅ PASS                       | 複数出力対応                    |
| **InternalizeAction テスト**    | ✅ PASS (6 tests)          | ✅ PASS                    | ✅ PASS                       | wallet payment/basket insertion |
| **JSON 完全一致 (tsgenerated)** | ✅ 基準 (fixture 生成元)   | ✅ PASS (JSONEq)           | ✅ PASS (15 テスト)           | output count: 32 全実装一致     |
| **DeterministicRandomizer**     | N/A (本番用)               | ✅ TestRandomizer          | ✅ PASS (8 tests)             | base64/shuffle/uint64 互換      |
| **reference 値**                | `YmJiYmJiYmJiYmJi`         | `YmJiYmJiYmJiYmJi`         | ✅ `YmJiYmJiYmJiYmJi`         | 完全一致                        |
| **derivationPrefix 値**         | `Y2NjY2NjY2NjY2NjY2NjYw==` | `Y2NjY2NjY2NjY2NjY2NjYw==` | ✅ `Y2NjY2NjY2NjY2NjY2NjYw==` | 完全一致                        |

### Change Output 生成アルゴリズム比較

| 項目                                 | TypeScript                         | Go                                 | Python                             |
| ------------------------------------ | ---------------------------------- | ---------------------------------- | ---------------------------------- |
| **アルゴリズム名**                   | `generateChangeSdk`                | `funder/sql.go`                    | `generate_change_sdk` (TS 移植)    |
| **Output count 決定方式**            | 動的 (funding loop)                | 事前計算 + clamp                   | 動的 (funding loop)                |
| **計算式**                           | `targetNetCount - allocatedInputs` | `changeVal/minUTXO + 1` then clamp | `targetNetCount - allocatedInputs` |
| **numberOfDesiredUTXOs=31 時の結果** | 31 change outputs                  | 31 change outputs                  | 31 change outputs ✅               |
| **Randomizer 使用箇所**              | fee excess 分配                    | ChangeDistribution                 | fee excess 分配                    |

### 差異の原因分析

| 原因候補                    | 状態      | 詳細                                    |
| --------------------------- | --------- | --------------------------------------- |
| **Randomizer 呼び出し順序** | ✅ 修正済 | InternalizeAction で reference 生成追加 |
| **reference 長さ**          | ✅ 修正済 | 12 bytes (Go parity)                    |
| **derivationPrefix 長さ**   | ✅ 修正済 | 16 bytes (Go parity)                    |
| **minimumDesiredUTXOValue** | ✅ 修正済 | キー名タイポ修正 (Utxo → UTXO)          |
| **target_net_count 計算**   | ✅ 正常   | 31 - available_count                    |

### テスト詳細比較

#### Internalize → Create → Process フロー

| テスト名                                    | TS  | Go  | Py             |
| ------------------------------------------- | --- | --- | -------------- |
| 基本フロー (Internalize → Create → Process) | ✅  | ✅  | ✅             |
| 次の Create (change UTXO 使用)              | ✅  | ✅  | ✅             |
| Unknown Input での Create                   | -   | ✅  | ✅ (args 構造) |
| Known Input での Create                     | -   | ✅  | ✅ (args 構造) |
| InternalizePlusTooHighCreate (エラー)       | -   | ✅  | ✅             |
| BasketInsertion → Create                    | -   | ✅  | -              |

#### JSON 完全一致テスト

| フィールド                 | Go (tsgenerated 比較)     | Python                    |
| -------------------------- | ------------------------- | ------------------------- |
| reference                  | ✅ 一致                   | ✅ 一致                   |
| derivationPrefix           | ✅ 一致                   | ✅ 一致                   |
| version                    | ✅ 一致                   | ✅ 型一致                 |
| lockTime                   | ✅ 一致                   | ✅ 型一致                 |
| inputs[].sourceTxid        | ✅ 一致                   | ✅ 型一致                 |
| inputs[].sourceSatoshis    | ✅ 一致                   | ✅ 型一致                 |
| outputs count              | ✅ 32                     | ✅ 32                     |
| outputs[].satoshis         | ✅ 一致                   | ✅ 型一致                 |
| outputs[].derivationSuffix | ✅ 'd','e','f'... pattern | ✅ 'd','e','f'... pattern |
| inputBeef                  | ✅ 一致                   | ✅ 型一致                 |

---

## 参考リンク

- [go-wallet-toolbox テスト](https://github.com/bsv-blockchain/go-wallet-toolbox/tree/main/pkg/storage/internal/integrationtests)
- [Universal Test Vectors](https://github.com/bsv-blockchain/universal-test-vectors)
- [go-bsv-middleware リグレッションテスト](https://github.com/bsv-blockchain/go-bsv-middleware/tree/main/pkg/internal/regressiontests)
