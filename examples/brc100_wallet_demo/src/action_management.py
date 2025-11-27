"""アクション管理機能（作成、署名、一覧表示）"""

from bsv_wallet_toolbox import Wallet


def demo_create_action(wallet: Wallet) -> None:
    """アクション作成のデモを実行します。"""
    print("\n📋 アクションを作成します（OP_RETURN メッセージ）")
    print()

    # ユーザー入力を取得
    message = input("記録するメッセージ [Enter=デフォルト]: ").strip() or "Hello, World!"

    try:
        # メッセージを OP_RETURN スクリプトに変換
        message_bytes = message.encode()
        hex_data = message_bytes.hex()
        length = len(message_bytes)
        script = f"006a{length:02x}{hex_data}"

        action = wallet.create_action(
            {
                "description": f"メッセージの記録: {message}",
                "inputs": {},
                "outputs": [
                    {
                        "script": script,
                        "satoshis": 0,
                        "description": "メッセージ出力",
                    }
                ],
            }
        )

        print(f"\n✅ アクションが作成されました！")
        print(f"   参照: {action['reference']}")
        print(f"   説明: {action['description']}")
        print(f"   署名が必要: {action['signActionRequired']}")

        # 署名が必要な場合、自動的に署名
        if action["signActionRequired"]:
            print("\n✍️  アクションに署名しています...")
            signed = wallet.sign_action(
                {
                    "reference": action["reference"],
                    "accept": True,
                }
            )
            print(f"✅ アクションが署名されました！")

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()


def demo_list_actions(wallet: Wallet) -> None:
    """作成されたアクションを一覧表示します。"""
    print("\n📋 アクションのリストを取得しています...")
    
    try:
        actions = wallet.list_actions({"labels": [], "limit": 10})
        print(f"\n✅ アクション数: {len(actions['actions'])}")
        print()

        if not actions["actions"]:
            print("   （アクションがありません）")
        else:
            for i, act in enumerate(actions["actions"], 1):
                print(f"   {i}. {act['description']}")
                print(f"      参照: {act['reference']}")
                print(f"      ステータス: {act.get('status', 'unknown')}")
                print()
    except Exception as e:
        print(f"❌ エラー: {e}")

