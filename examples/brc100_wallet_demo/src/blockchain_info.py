"""ブロックチェーン情報取得機能"""

from bsv_wallet_toolbox import Wallet


def demo_get_height(wallet: Wallet) -> None:
    """現在のブロック高を取得します。"""
    print("\n📊 現在のブロック高を取得しています...")
    print()
    
    try:
        result = wallet.get_height({})
        
        print(f"✅ ブロック高: {result['height']}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        print("   （Services が設定されていない場合、このエラーは正常です）")


def demo_get_header_for_height(wallet: Wallet) -> None:
    """指定したブロック高のヘッダーを取得します。"""
    print("\n📊 ブロックヘッダーを取得します")
    print()
    
    # ユーザー入力を取得
    height_input = input("ブロック高 [Enter=1]: ").strip() or "1"
    
    try:
        height = int(height_input)
        result = wallet.get_header_for_height({"height": height})
        
        print(f"\n✅ ブロック高 {height} のヘッダーを取得しました！")
        print(f"   ハッシュ: {result.get('hash', 'N/A')}")
        print(f"   バージョン: {result.get('version', 'N/A')}")
        print(f"   前ブロックハッシュ: {result.get('previousHash', 'N/A')}")
        print(f"   マークルルート: {result.get('merkleRoot', 'N/A')}")
        print(f"   タイムスタンプ: {result.get('time', 'N/A')}")
        print(f"   難易度: {result.get('bits', 'N/A')}")
        print(f"   Nonce: {result.get('nonce', 'N/A')}")
        
    except ValueError:
        print("❌ 無効なブロック高です")
    except Exception as e:
        print(f"❌ エラー: {e}")
        print("   （Services が設定されていない場合、このエラーは正常です）")


def demo_wait_for_authentication(wallet: Wallet) -> None:
    """認証を待機します（即座に完了）。"""
    print("\n⏳ 認証を待機しています...")
    print()
    
    try:
        result = wallet.wait_for_authentication({})
        
        print(f"✅ 認証完了: {result['authenticated']}")
        print("   （base Wallet 実装では即座に認証されます）")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

