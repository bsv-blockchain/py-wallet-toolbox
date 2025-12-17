#!/usr/bin/env python3
"""Faucet からの受金を internalize して create_action で使うシンプルなデモ.

2 段構えの「ステップ 2」用スクリプトです。

- ステップ 1: test_all_28_methods.py でウォレットを初期化し、
  そこで表示される「受取用アドレス」に Faucet から少額の BSV を送る
- ステップ 2: このスクリプトを実行し、ブロックエクスプローラで確認した
  txid を入力すると:
    1) そのトランザクションをウォレットに internalize（バスケット登録）
    2) その資金を使ってシンプルな OP_RETURN 付き create_action を 1 回実行

高度なオプションやカスタム BRC-29 設定は行わず、
「Faucet 受金 → internalizeAction → createAction」という最小限の流れだけを扱います。
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

from dotenv import load_dotenv

from bsv.keys import PrivateKey
from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.services import Services, create_default_options

from src.config import (
    bypass_wallet_infra_auth,
    get_key_deriver,
    get_network,
    get_remote_storage_client,
    get_remote_storage_url,
    get_storage_provider,
    get_wallet_infra_client,
    get_wallet_infra_url,
    use_remote_storage,
    use_wallet_infra,
)
from src.transaction_management import _build_atomic_beef_for_txid


# Faucet 用 BRC-29 派生情報（test_all_28_methods.py と同じ値）
FAUCET_DERIVATION_PREFIX = "faucet-prefix-01"
FAUCET_DERIVATION_SUFFIX = "faucet-suffix-01"


def main() -> None:
    # examples ディレクトリをカレントディレクトリに
    os.chdir(Path(__file__).parent)
    load_dotenv()

    print("=" * 70)
    print("💧 Faucet 受金 → internalizeAction → create_action デモ")
    print("=" * 70)
    print(
        "\n前提:\n"
        "  1. 先に test_all_28_methods.py を実行し、表示された受取用アドレスに\n"
        "     Faucet から少額の BSV を送金しておいてください。\n"
        "  2. ブロックエクスプローラ（WhatsOnChain など）から、そのトランザクション ID(txid)\n"
        "     を控えておいてください。\n"
    )

    # ---- ウォレット初期化（test_all_28_methods.py と同等のストレージ切り替え） ----
    chain = get_network()
    key_deriver = get_key_deriver()
    options = create_default_options(chain)
    services = Services(options)

    # ストレージモード判定（優先度: wallet-infra > remote > local）
    wallet_infra_mode = use_wallet_infra()
    bypass_auth = bypass_wallet_infra_auth()
    remote_storage_mode = use_remote_storage()

    if wallet_infra_mode:
        print(f"\n🏗️  wallet-infraモード: {get_wallet_infra_url()}")
        print("⚠️  wallet-infraはBRC-104認証が必要です")
        print("-" * 70)

        # まずローカルストレージでウォレットを作成（StorageClient 認証用）
        local_storage = get_storage_provider(chain)
        wallet = Wallet(
            chain=chain,
            services=services,
            key_deriver=key_deriver,
            storage_provider=local_storage,
        )

        infra_client = get_wallet_infra_client(wallet)

        if bypass_auth:
            print("\n🔄 wallet-infra認証をバイパスして直接接続...")
            print("   注意: これはテスト目的のみです。本番環境では使用しないでください。")

            print("\n🔄 wallet-infraストレージを使用したwalletインスタンスを作成中...")
            wallet = Wallet(
                chain=chain,
                services=services,
                key_deriver=key_deriver,
                storage_provider=infra_client,
            )
            print("✅ wallet-infra walletインスタンス作成成功 (認証バイパス)!")
        else:
            try:
                print("\n🔄 wallet-infraに接続中...")
                infra_settings = infra_client.make_available()
                print("✅ wallet-infra接続成功!")
                print(f"   Storage Identity Key: {infra_settings.get('storageIdentityKey', 'N/A')}")
                print(f"   Chain: {infra_settings.get('chain', 'N/A')}")

                print("\n🔄 wallet-infraストレージを使用したwalletインスタンスを作成中...")
                wallet = Wallet(
                    chain=chain,
                    services=services,
                    key_deriver=key_deriver,
                    storage_provider=infra_client,
                )
                print("✅ wallet-infra walletインスタンス作成成功!")
            except Exception as err:  # noqa: BLE001
                print(f"⚠️  wallet-infra認証失敗: {err}")
                print("   これはPython SDKの既知の問題です。ローカルストレージで処理を続行します...")
                print("   注意: wallet-infra認証はPythonでは現在サポートされていません。")
                print("   テスト用に BYPASS_WALLET_INFRA_AUTH=true を設定して認証をバイパスできます。")
                wallet_infra_mode = False

    if not wallet_infra_mode and remote_storage_mode:
        print(f"\n🌐 リモートストレージモード: {get_remote_storage_url(chain)}")
        print("⚠️  リモートストレージはBRC-104認証が必要です")
        print("-" * 70)

        # まずローカルストレージでウォレットを作成（StorageClient 認証用）
        local_storage = get_storage_provider(chain)
        wallet = Wallet(
            chain=chain,
            services=services,
            key_deriver=key_deriver,
            storage_provider=local_storage,
        )

        remote_client = get_remote_storage_client(wallet, chain)

        try:
            print("\n🔄 リモートストレージに接続中...")
            remote_settings = remote_client.make_available()
            print("✅ リモートストレージ接続成功!")
            print(f"   Storage Identity Key: {remote_settings.get('storageIdentityKey', 'N/A')}")
            print(f"   Chain: {remote_settings.get('chain', 'N/A')}")

            print("\n🔄 リモートストレージを使用したwalletインスタンスを作成中...")
            wallet = Wallet(
                chain=chain,
                services=services,
                key_deriver=key_deriver,
                storage_provider=remote_client,
            )
            print("✅ リモートストレージ walletインスタンス作成成功!")
        except Exception as err:  # noqa: BLE001
            print(f"❌ リモートストレージ接続失敗: {err}")
            print("   ローカルストレージで処理を続行します...")
            remote_storage_mode = False

    if not wallet_infra_mode and not remote_storage_mode:
        print("\n💾 ローカルストレージモード")
        storage_provider = get_storage_provider(chain)
        wallet = Wallet(
            chain=chain,
            services=services,
            key_deriver=key_deriver,
            storage_provider=storage_provider,
        )

    print(f"\n🟢 ネットワーク: {chain}")

    # ---- 1) Faucet からのトランザクションを internalize ---------------------------
    txid = input(
        "\n🔎 internalize したいトランザクション ID(txid) を入力してください\n"
        "    （例: 64 文字の 16 進数。キャンセルするには空のまま Enter）\n"
        "txid: "
    ).strip()

    if not txid:
        print("\n⏹ txid が指定されなかったため、処理を中止します。")
        return

    if len(txid) != 64:
        print("\n❌ txid は 64 文字の 16 進数である必要があります。")
        return

    try:
        int(txid, 16)
    except ValueError:
        print("\n❌ txid が 16 進数として不正です。")
        return

    try:
        atomic_beef = _build_atomic_beef_for_txid(chain, txid)
    except Exception as err:  # noqa: BLE001
        print(f"\n❌ Atomic BEEF の取得に失敗しました: {err}")
        return

    # Faucet デモでは BRC-29 の「wallet payment」プロトコルで internalize し、
    # その UTXO を create_action の資金として使えるようにする。
    #
    # - senderIdentityKey: Faucet 側 AnyoneKey (= PrivateKey(1).public_key())
    # - derivationPrefix / derivationSuffix: テスト用固定文字列（BRC-29 仕様に従い base64 で渡す）
    anyone_key = PrivateKey(1).public_key()
    derivation_prefix_b64 = base64.b64encode(FAUCET_DERIVATION_PREFIX.encode("utf-8")).decode("ascii")
    derivation_suffix_b64 = base64.b64encode(FAUCET_DERIVATION_SUFFIX.encode("utf-8")).decode("ascii")

    print("\n🚀 internalizeAction を実行します...")
    internalize_args = {
        "tx": atomic_beef,
        "outputs": [
            {
                # もっとも単純なケースとして「最初のアウトプット(0) が自分宛て」の
                # BRC-29 wallet payment であると仮定する。
                "outputIndex": 0,
                "protocol": "wallet payment",
                "paymentRemittance": {
                    "senderIdentityKey": anyone_key.hex(),
                    "derivationPrefix": derivation_prefix_b64,
                    "derivationSuffix": derivation_suffix_b64,
                },
            }
        ],
        "description": "Internalize faucet transaction into default basket",
        "labels": [f"txid:{txid}", "faucet"],
    }

    try:
        internalize_result = wallet.internalize_action(internalize_args)
    except Exception as err:  # noqa: BLE001
        print(f"\n❌ internalize_action でエラーが発生しました: {err}")
        return

    print("\n✅ トランザクションを internalize しました。")
    print(f"   state : {internalize_result.get('state', 'unknown')}")
    print(f"   txid  : {internalize_result.get('txid', 'n/a')}")

    # ---- 2) internalize した資金を使って create_action を 1 回実行 ----------------
    answer = input(
        "\n💡 internalize した資金を使って、シンプルな OP_RETURN アクション\n"
        "   （0 sat の OP_RETURN 出力のみ）を 1 回作成してみますか？ [y/N]: "
    ).strip().lower()

    if not answer.startswith("y"):
        print("\n⏹ create_action は実行せずに終了します。")
        return

    print("\n🚀 create_action を実行します（funded by faucet）...")
    try:
        action_result = wallet.create_action(
            {
                "description": "Faucet-funded demo action",
                "outputs": [
                    {
                        # OP_RETURN "faucet_demo"
                        "lockingScript": "006a0b6661756365745f64656d6f",
                        "satoshis": 0,
                        "outputDescription": "Faucet-funded demo OP_RETURN output",
                    }
                ],
            }
        )
    except Exception as err:  # noqa: BLE001
        print(f"\n❌ create_action でエラーが発生しました: {err}")
        return

    print("\n✅ create_action が成功しました。結果の概要:")
    txid_created = action_result.get("txid") or action_result.get("txID") or "(txid not returned)"
    print(f"   txid : {txid_created}")
    print(f"   state: {action_result.get('state', 'unknown')}")

    print("\n🎉 Faucet からの受金を internalize → create_action で利用するデモが完了しました。")


if __name__ == "__main__":
    main()

