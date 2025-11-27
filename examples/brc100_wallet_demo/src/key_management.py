"""鍵管理機能（公開鍵取得、署名生成）"""

from bsv_wallet_toolbox import Wallet


def demo_get_public_key(wallet: Wallet) -> None:
    """公開鍵取得のデモを実行します。"""
    print("\n🔑 プロトコル固有の鍵を取得します")
    print()

    # ユーザー入力を取得
    protocol_name = input("プロトコル名（例: 'test protocol'）[Enter=デフォルト]: ").strip() or "test protocol"
    key_id = input("キー ID（例: '1'）[Enter=デフォルト]: ").strip() or "1"
    counterparty = input("Counterparty（self/anyone）[Enter=self]: ").strip() or "self"

    try:
        result = wallet.get_public_key(
            {
                "identityKey": True,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "counterparty": counterparty,
                "reason": f"{protocol_name} 用の鍵",
            }
        )
        print(f"\n✅ 公開鍵を取得しました！")
        print(f"   プロトコル: {protocol_name}")
        print(f"   キー ID: {key_id}")
        print(f"   Counterparty: {counterparty}")
        print(f"   公開鍵: {result['publicKey']}")
    except Exception as e:
        print(f"❌ エラー: {e}")


def demo_sign_data(wallet: Wallet) -> None:
    """データへの署名デモを実行します。"""
    print("\n✍️  データに署名します")
    print()

    # ユーザー入力を取得
    message = input("署名するメッセージ [Enter=デフォルト]: ").strip() or "Hello, BSV!"
    protocol_name = input("プロトコル名（例: 'test protocol'）[Enter=デフォルト]: ").strip() or "test protocol"
    key_id = input("キー ID（例: '1'）[Enter=デフォルト]: ").strip() or "1"

    try:
        data = list(message.encode())
        result = wallet.create_signature(
            {
                "data": data,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "counterparty": "self",
                "reason": "メッセージへの署名",
            }
        )
        print(f"\n✅ 署名が生成されました！")
        print(f"   メッセージ: {message}")
        print(f"   署名: {result['signature'][:64]}...")
        print(f"   公開鍵: {result['publicKey']}")
    except Exception as e:
        print(f"❌ エラー: {e}")

