"""鍵リンケージ開示機能"""

from bsv_wallet_toolbox import Wallet


def demo_reveal_counterparty_key_linkage(wallet: Wallet) -> None:
    """Counterparty Key Linkage の開示デモを実行します。"""
    print("\n🔗 Counterparty Key Linkage を開示します")
    print()
    
    # ユーザー入力を取得
    counterparty = input("Counterparty（公開鍵の hex）[Enter=self]: ").strip() or "self"
    protocol_name = input("プロトコル名 [Enter=デフォルト]: ").strip() or "test protocol"
    
    try:
        result = wallet.reveal_counterparty_key_linkage(
            {
                "counterparty": counterparty,
                "verifier": "02" + "a" * 64,  # ダミーの検証者公開鍵
                "protocolID": [0, protocol_name],
                "reason": "Counterparty Key Linkage の開示",
                "privilegedReason": "テスト目的",
            }
        )
        
        print(f"\n✅ Counterparty Key Linkage が開示されました！")
        print(f"   プロトコル: {protocol_name}")
        print(f"   プルーフ: {result['prover'][:32] if 'prover' in result else 'N/A'}...")
        print(f"   公開鍵: {result['counterparty'][:32] if 'counterparty' in result else 'N/A'}...")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()


def demo_reveal_specific_key_linkage(wallet: Wallet) -> None:
    """Specific Key Linkage の開示デモを実行します。"""
    print("\n🔗 Specific Key Linkage を開示します")
    print()
    
    # ユーザー入力を取得
    counterparty = input("Counterparty（公開鍵の hex）[Enter=self]: ").strip() or "self"
    protocol_name = input("プロトコル名 [Enter=デフォルト]: ").strip() or "test protocol"
    key_id = input("キー ID [Enter=デフォルト]: ").strip() or "1"
    
    try:
        result = wallet.reveal_specific_key_linkage(
            {
                "counterparty": counterparty,
                "verifier": "02" + "a" * 64,  # ダミーの検証者公開鍵
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "reason": "Specific Key Linkage の開示",
                "privilegedReason": "テスト目的",
            }
        )
        
        print(f"\n✅ Specific Key Linkage が開示されました！")
        print(f"   プロトコル: {protocol_name}")
        print(f"   キー ID: {key_id}")
        print(f"   プルーフ: {result['prover'][:32] if 'prover' in result else 'N/A'}...")
        print(f"   公開鍵: {result['counterparty'][:32] if 'counterparty' in result else 'N/A'}...")
        print(f"   特定鍵: {result['specific'][:32] if 'specific' in result else 'N/A'}...")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

