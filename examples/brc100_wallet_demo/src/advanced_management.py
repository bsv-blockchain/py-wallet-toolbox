"""出力管理機能（リスト、破棄）"""

from bsv_wallet_toolbox import Wallet


def demo_list_outputs(wallet: Wallet) -> None:
    """出力のリストを表示します。"""
    print("\n📋 出力のリストを取得しています...")
    print()
    
    try:
        outputs = wallet.list_outputs(
            {
                "basket": "default",  # バスケット名（オプション）
                "limit": 10,
                "offset": 0,
            }
        )
        
        print(f"✅ 出力数: {outputs.get('totalOutputs', 0)}")
        print()
        
        if outputs.get("outputs"):
            for i, output in enumerate(outputs["outputs"][:10], 1):
                print(f"   {i}. Outpoint: {output.get('outpoint', 'N/A')}")
                print(f"      Satoshis: {output.get('satoshis', 0)}")
                print(f"      Spent: {output.get('spendable', True)}")
                print()
        else:
            print("   （出力がありません）")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()


def demo_relinquish_output(wallet: Wallet) -> None:
    """出力を破棄します。"""
    print("\n🗑️  出力を破棄します")
    print()
    print("⚠️  この機能は実際の出力が存在する場合に使用できます。")
    print("   デモ用のダミー出力で試します...")
    print()
    
    # ダミーの outpoint
    outpoint = "0000000000000000000000000000000000000000000000000000000000000000:0"
    
    try:
        result = wallet.relinquish_output(
            {
                "basket": "default",
                "output": outpoint,
            }
        )
        
        print(f"✅ 出力が破棄されました！")
        print(f"   Outpoint: {outpoint}")
        print(f"   破棄数: {result.get('relinquished', 0)}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        print("   （実際の出力が存在しない場合、このエラーは正常です）")


def demo_abort_action(wallet: Wallet) -> None:
    """アクションを中止します。"""
    print("\n🚫 アクションを中止します")
    print()
    
    # アクション一覧を表示
    try:
        actions = wallet.list_actions({"labels": [], "limit": 10})
        
        if not actions["actions"]:
            print("中止可能なアクションがありません。")
            print("先にアクションを作成してください（メニュー 5）。")
            return
            
        print("中止可能なアクション:")
        for i, act in enumerate(actions["actions"], 1):
            print(f"   {i}. {act['description']}")
            print(f"      参照: {act['reference']}")
            print()
        
        # ユーザー選択
        choice = input("中止するアクションの番号 [Enter=1]: ").strip() or "1"
        idx = int(choice) - 1
        
        if 0 <= idx < len(actions["actions"]):
            reference = actions["actions"][idx]["reference"]
            
            result = wallet.abort_action(
                {
                    "reference": reference,
                }
            )
            
            print(f"\n✅ アクションが中止されました！")
            print(f"   参照: {reference}")
            print(f"   中止されたアクション数: {result.get('aborted', 0)}")
        else:
            print("❌ 無効な選択です")
            
    except Exception as e:
        print(f"❌ エラー: {e}")


def demo_relinquish_certificate(wallet: Wallet) -> None:
    """証明書を破棄します。"""
    print("\n🗑️  証明書を破棄します")
    print()
    
    # 証明書一覧を表示
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
        
        if not certs["certificates"]:
            print("破棄可能な証明書がありません。")
            print("先に証明書を取得してください（メニュー 7）。")
            return
            
        print("破棄可能な証明書:")
        for i, cert in enumerate(certs["certificates"], 1):
            print(f"   {i}. {cert['type']}")
            print(f"      証明書 ID: {cert.get('certificateId', 'N/A')}")
            print()
        
        # ユーザー選択
        choice = input("破棄する証明書の番号 [Enter=1]: ").strip() or "1"
        idx = int(choice) - 1
        
        if 0 <= idx < len(certs["certificates"]):
            cert = certs["certificates"][idx]
            cert_type = cert["type"]
            certifier = cert.get("certifier", "self")
            serial = cert.get("serialNumber", "")
            
            result = wallet.relinquish_certificate(
                {
                    "type": cert_type,
                    "certifier": certifier,
                    "serialNumber": serial,
                }
            )
            
            print(f"\n✅ 証明書が破棄されました！")
            print(f"   タイプ: {cert_type}")
            print(f"   発行者: {certifier}")
        else:
            print("❌ 無効な選択です")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

