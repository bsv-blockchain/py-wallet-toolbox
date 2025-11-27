"""証明書管理機能（取得、一覧表示）"""

from bsv_wallet_toolbox import Wallet


def demo_acquire_certificate(wallet: Wallet) -> None:
    """証明書取得のデモを実行します。"""
    print("\n📜 証明書を取得します")
    print()

    # ユーザー入力を取得
    cert_type = input("証明書タイプ（例: 'test-certificate'）[Enter=デフォルト]: ").strip() or "test-certificate"
    name = input("名前（例: 'Test User'）[Enter=デフォルト]: ").strip() or "Test User"
    email = input("メール（例: 'test@example.com'）[Enter=デフォルト]: ").strip() or "test@example.com"

    try:
        result = wallet.acquire_certificate(
            {
                "type": cert_type,
                "certifier": "self",
                "acquisitionProtocol": "direct",
                "fields": {
                    "name": name,
                    "email": email,
                },
                "privilegedReason": "証明書の取得",
            }
        )
        print(f"\n✅ 証明書が取得されました！")
        print(f"   タイプ: {result['type']}")
        cert_str = result['serializedCertificate']
        print(f"   シリアライズ: {cert_str[:64] if len(cert_str) > 64 else cert_str}...")
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()


def demo_list_certificates(wallet: Wallet) -> None:
    """保有している証明書を一覧表示します。"""
    print("\n📜 証明書のリストを取得しています...")
    
    try:
        certs = wallet.list_certificates(
            {
                "certifiers": [],
                "types": [],
                "limit": 10,
                "offset": 0,
                "privileged": False,
                "privilegedReason": "証明書一覧の取得",
            }
        )
        print(f"\n✅ 証明書数: {len(certs['certificates'])}")
        print()

        if not certs["certificates"]:
            print("   （証明書がありません）")
        else:
            for i, cert in enumerate(certs["certificates"], 1):
                print(f"   {i}. {cert['type']}")
                print(f"      証明書 ID: {cert.get('certificateId', 'N/A')}")
                if "subject" in cert:
                    print(f"      主体: {cert['subject']}")
                print()
    except Exception as e:
        print(f"❌ エラー: {e}")

