"""ID 検索機能（Identity Key、属性ベース検索）"""

from bsv_wallet_toolbox import Wallet


def demo_discover_by_identity_key(wallet: Wallet) -> None:
    """Identity Key による検索のデモを実行します。"""
    print("\n🔍 Identity Key で検索します")
    print()
    
    # 自分の Identity Key を使用するかどうか
    use_own = input("自分の Identity Key で検索しますか？ (y/n) [Enter=y]: ").strip().lower()
    
    try:
        if use_own != 'n':
            # 自分の Identity Key を取得
            my_key = wallet.get_public_key(
                {
                    "identityKey": True,
                    "reason": "自分の Identity Key を取得",
                }
            )
            identity_key = my_key["publicKey"]
            print(f"🔑 使用する Identity Key: {identity_key[:32]}...")
        else:
            # ユーザーが指定
            identity_key = input("検索する Identity Key を入力: ").strip()
        
        print()
        print("🔍 検索中...")
        
        results = wallet.discover_by_identity_key(
            {
                "identityKey": identity_key,
                "limit": 10,
                "offset": 0,
                "seekPermission": True,
            }
        )

        print(f"\n✅ 検索結果: {len(results['certificates'])} 件")
        print()

        for i, cert in enumerate(results["certificates"], 1):
            print(f"   {i}. {cert['type']}")
            if "fields" in cert:
                print(f"      フィールド: {list(cert['fields'].keys())}")
            if "certifier" in cert:
                print(f"      発行者: {cert['certifier'][:32]}...")
            print()

    except Exception as e:
        print(f"❌ 検索エラー: {e}")


def demo_discover_by_attributes(wallet: Wallet) -> None:
    """属性ベース検索のデモを実行します。"""
    print("\n🔍 属性で検索します")
    print()
    print("検索パターンを選択してください:")
    print("  1. 国で検索（例: country='Japan'）")
    print("  2. 年齢範囲で検索（例: age >= 20）")
    print("  3. カスタム検索")
    
    choice = input("\n選択 (1-3) [Enter=1]: ").strip() or "1"
    
    try:
        if choice == "1":
            country = input("国名 [Enter=Japan]: ").strip() or "Japan"
            attributes = {"country": country}
            print(f"\n🔍 {country} で検索中...")
            
        elif choice == "2":
            min_age = input("最小年齢 [Enter=20]: ").strip() or "20"
            attributes = {"age": {"$gte": int(min_age)}}
            print(f"\n🔍 年齢 >= {min_age} で検索中...")
            
        else:
            # カスタム検索（簡易版）
            print("カスタム検索は開発中です。デフォルト検索を実行します。")
            attributes = {"verified": True}
            print("\n🔍 verified=true で検索中...")
        
        results = wallet.discover_by_attributes(
            {
                "attributes": attributes,
                "limit": 10,
                "offset": 0,
                "seekPermission": True,
            }
        )

        print(f"\n✅ 検索結果: {len(results['certificates'])} 件")
        print()

        for i, cert in enumerate(results["certificates"], 1):
            print(f"   {i}. {cert['type']}")
            if "fields" in cert:
                for key, value in cert["fields"].items():
                    print(f"      {key}: {value}")
            print()

    except Exception as e:
        print(f"❌ 検索エラー: {e}")

