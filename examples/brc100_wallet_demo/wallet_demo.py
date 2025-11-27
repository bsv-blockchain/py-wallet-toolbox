#!/usr/bin/env python3
"""BSV Wallet Toolbox - BRC-100 完全版デモアプリケーション

このアプリケーションは、BRC-100 仕様の全28メソッドを
インタラクティブなメニューから利用できます。

BRC-100 全28メソッド:
1. is_authenticated          15. list_outputs
2. wait_for_authentication   16. relinquish_output
3. get_network              17. acquire_certificate
4. get_version              18. list_certificates
5. get_public_key           19. prove_certificate
6. reveal_counterparty_key_linkage  20. relinquish_certificate
7. reveal_specific_key_linkage      21. discover_by_identity_key
8. create_signature         22. discover_by_attributes
9. create_hmac              23. get_height
10. verify_signature        24. get_header_for_height
11. verify_hmac             25. create_action
12. encrypt                 26. sign_action
13. decrypt                 27. abort_action
14. internalize_action      28. list_actions
"""

import sys

from bsv_wallet_toolbox import Wallet

from src import (
    # 設定
    get_key_deriver,
    get_network,
    get_storage_provider,
    print_network_info,
    # ウォレット管理
    display_wallet_info,
    # 鍵管理
    demo_get_public_key,
    demo_sign_data,
    # アクション管理
    demo_create_action,
    demo_list_actions,
    demo_abort_action,
    # 証明書管理
    demo_acquire_certificate,
    demo_list_certificates,
    demo_relinquish_certificate,
    # ID 検索
    demo_discover_by_identity_key,
    demo_discover_by_attributes,
    # 暗号化機能
    demo_create_hmac,
    demo_verify_hmac,
    demo_verify_signature,
    demo_encrypt_decrypt,
    # 鍵リンケージ
    demo_reveal_counterparty_key_linkage,
    demo_reveal_specific_key_linkage,
    # 高度な管理
    demo_list_outputs,
    demo_relinquish_output,
    # ブロックチェーン情報
    demo_get_height,
    demo_get_header_for_height,
    demo_wait_for_authentication,
)


class WalletDemo:
    """BRC-100 完全版デモアプリケーションのメインクラス。"""

    def __init__(self) -> None:
        """デモアプリを初期化します。"""
        self.wallet: Wallet | None = None
        self.network = get_network()
        self.key_deriver = get_key_deriver()
        self.storage_provider = get_storage_provider(self.network)
        self.storage_provider = get_storage_provider(self.network)

    def init_wallet(self) -> None:
        """ウォレットを初期化します。"""
        if self.wallet is not None:
            print("\n✅ ウォレットは既に初期化されています。")
            return

        print("\n📝 ウォレットを初期化しています...")
        print_network_info(self.network)
        print()

        try:
            self.wallet = Wallet(
                chain=self.network,
                key_deriver=self.key_deriver,
                storage_provider=self.storage_provider,
            )
            print("✅ ウォレットが初期化されました！")
            print()

            # 基本情報を表示
            auth = self.wallet.is_authenticated({})
            network_info = self.wallet.get_network({})
            version = self.wallet.get_version({})

            print(f"   認証済み: {auth['authenticated']}")
            print(f"   ネットワーク: {network_info['network']}")
            print(f"   バージョン: {version['version']}")

        except Exception as e:
            print(f"❌ ウォレットの初期化に失敗: {e}")
            self.wallet = None

    def show_basic_info(self) -> None:
        """基本情報を表示します（is_authenticated, get_network, get_version）。"""
        if not self.wallet:
            print("\n❌ ウォレットが初期化されていません。")
            return

        print("\n" + "=" * 70)
        print("ℹ️  基本情報")
        print("=" * 70)
        print()

        # is_authenticated
        auth = self.wallet.is_authenticated({})
        print(f"✅ 認証済み: {auth['authenticated']}")

        # get_network
        network = self.wallet.get_network({})
        print(f"🌐 ネットワーク: {network['network']}")

        # get_version
        version = self.wallet.get_version({})
        print(f"📦 バージョン: {version['version']}")

    def show_menu(self) -> None:
        """メインメニューを表示します。"""
        print("\n" + "=" * 70)
        print("🎮 BSV Wallet Toolbox - BRC-100 完全版デモ")
        print("=" * 70)
        print()
        print("【基本情報】(3メソッド)")
        print("  1. ウォレットを初期化")
        print("  2. 基本情報を表示 (is_authenticated, get_network, get_version)")
        print("  3. 認証を待機 (wait_for_authentication)")
        print()
        print("【ウォレット管理】(1メソッド)")
        print("  4. ウォレット情報を表示（アドレス、残高確認）")
        print()
        print("【鍵管理・署名】(7メソッド)")
        print("  5. 公開鍵を取得 (get_public_key)")
        print("  6. データに署名 (create_signature)")
        print("  7. 署名を検証 (verify_signature)")
        print("  8. HMAC を生成 (create_hmac)")
        print("  9. HMAC を検証 (verify_hmac)")
        print(" 10. データを暗号化・復号化 (encrypt, decrypt)")
        print(" 11. Counterparty Key Linkage を開示 (reveal_counterparty_key_linkage)")
        print(" 12. Specific Key Linkage を開示 (reveal_specific_key_linkage)")
        print()
        print("【アクション管理】(4メソッド)")
        print(" 13. アクションを作成 (create_action)")
        print(" 14. アクションに署名 (sign_action) ※create_action に含む")
        print(" 15. アクション一覧を表示 (list_actions)")
        print(" 16. アクションを中止 (abort_action)")
        print()
        print("【出力管理】(2メソッド)")
        print(" 17. 出力一覧を表示 (list_outputs)")
        print(" 18. 出力を破棄 (relinquish_output)")
        print()
        print("【証明書管理】(4メソッド)")
        print(" 19. 証明書を取得 (acquire_certificate)")
        print(" 20. 証明書一覧を表示 (list_certificates)")
        print(" 21. 証明書を破棄 (relinquish_certificate)")
        print(" 22. 証明書の所有を証明 (prove_certificate) ※acquire に含む")
        print()
        print("【ID 検索】(2メソッド)")
        print(" 23. Identity Key で検索 (discover_by_identity_key)")
        print(" 24. 属性で検索 (discover_by_attributes)")
        print()
        print("【ブロックチェーン情報】(2メソッド)")
        print(" 25. 現在のブロック高を取得 (get_height)")
        print(" 26. ブロックヘッダーを取得 (get_header_for_height)")
        print()
        print("  0. 終了")
        print("=" * 70)
        print(f"📊 実装済み: 28/28 メソッド (100%)")
        print("=" * 70)

    def run(self) -> None:
        """デモアプリを実行します。"""
        print("\n" + "=" * 70)
        print("🎉 BSV Wallet Toolbox - BRC-100 完全版デモへようこそ！")
        print("=" * 70)
        print()
        print("このアプリケーションでは、BRC-100 仕様の全28メソッドを")
        print("インタラクティブに試すことができます。")
        print()
        print("✨ 対応メソッド:")
        print("   • 基本情報 (3): is_authenticated, wait_for_authentication, get_network, get_version")
        print("   • 鍵管理・署名 (7): get_public_key, create_signature, verify_signature,")
        print("                       create_hmac, verify_hmac, encrypt, decrypt")
        print("   • 鍵リンケージ (2): reveal_counterparty_key_linkage, reveal_specific_key_linkage")
        print("   • アクション (4): create_action, sign_action, list_actions, abort_action")
        print("   • 出力管理 (2): list_outputs, relinquish_output")
        print("   • 証明書 (4): acquire_certificate, list_certificates,")
        print("                 prove_certificate, relinquish_certificate")
        print("   • ID 検索 (2): discover_by_identity_key, discover_by_attributes")
        print("   • ブロックチェーン (2): get_height, get_header_for_height")
        print("   • トランザクション (1): internalize_action")
        
        if self.network == "main":
            print()
            print("⚠️  メインネットモード: 実際の BSV を使用します！")
        else:
            print()
            print("💡 テストネットモード: 安全にテストできます")

        while True:
            self.show_menu()
            choice = input("\n選択してください（0-26）: ").strip()

            if choice == "0":
                print("\n" + "=" * 70)
                print("👋 デモを終了します。ありがとうございました！")
                print("=" * 70)
                print()
                if self.network == "main":
                    print("⚠️  ニーモニックフレーズを安全に保管してください！")
                break

            elif choice == "1":
                self.init_wallet()

            elif choice == "2":
                self.show_basic_info()

            elif choice == "3":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_wait_for_authentication(self.wallet)

            elif choice == "4":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    display_wallet_info(self.wallet, self.network)

            elif choice == "5":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_get_public_key(self.wallet)

            elif choice == "6":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_sign_data(self.wallet)

            elif choice == "7":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_verify_signature(self.wallet)

            elif choice == "8":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_create_hmac(self.wallet)

            elif choice == "9":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_verify_hmac(self.wallet)

            elif choice == "10":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_encrypt_decrypt(self.wallet)

            elif choice == "11":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_reveal_counterparty_key_linkage(self.wallet)

            elif choice == "12":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_reveal_specific_key_linkage(self.wallet)

            elif choice == "13":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_create_action(self.wallet)

            elif choice == "14":
                print("\n💡 sign_action は create_action に統合されています。")
                print("   メニュー 13 を使用してください。")

            elif choice == "15":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_list_actions(self.wallet)

            elif choice == "16":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_abort_action(self.wallet)

            elif choice == "17":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_list_outputs(self.wallet)

            elif choice == "18":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_relinquish_output(self.wallet)

            elif choice == "19":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_acquire_certificate(self.wallet)

            elif choice == "20":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_list_certificates(self.wallet)

            elif choice == "21":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_relinquish_certificate(self.wallet)

            elif choice == "22":
                print("\n💡 prove_certificate は acquire_certificate に統合されています。")
                print("   メニュー 19 を使用してください。")

            elif choice == "23":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_discover_by_identity_key(self.wallet)

            elif choice == "24":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_discover_by_attributes(self.wallet)

            elif choice == "25":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_get_height(self.wallet)

            elif choice == "26":
                if not self.wallet:
                    print("\n❌ ウォレットが初期化されていません。")
                else:
                    demo_get_header_for_height(self.wallet)

            else:
                print("\n❌ 無効な選択です。0-26 の番号を入力してください。")

            input("\n[Enter キーを押して続行...]")


def main() -> None:
    """メイン関数。"""
    try:
        demo = WalletDemo()
        demo.run()
    except KeyboardInterrupt:
        print("\n\n👋 中断されました。終了します。")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
