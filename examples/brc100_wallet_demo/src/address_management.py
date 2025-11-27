"""ウォレットアドレスと残高管理"""

from bsv.constants import Network
from bsv.keys import PublicKey
from bsv_wallet_toolbox import Wallet


def get_wallet_address(wallet: Wallet, network: str) -> str:
    """ウォレットの受信用アドレスを取得します。
    
    Args:
        wallet: Wallet インスタンス
        network: 'main' または 'test'
        
    Returns:
        BSV アドレス（文字列）
    """
    # Identity Key から公開鍵を取得
    result = wallet.get_public_key(
        {
            "identityKey": True,
            "reason": "ウォレットアドレスの取得",
        }
    )
    
    # 公開鍵から BSV アドレスを生成
    public_key = PublicKey(result["publicKey"])
    if network == "test":
        network_enum = Network.TESTNET
    else:
        network_enum = Network.MAINNET
    address = public_key.address(network=network_enum)
    
    return address


def display_wallet_info(wallet: Wallet, network: str) -> None:
    """ウォレットの情報を表示します。
    
    Args:
        wallet: Wallet インスタンス
        network: ネットワーク名
    """
    print("\n" + "=" * 70)
    print("💰 ウォレット情報")
    print("=" * 70)
    print()
    
    try:
        # アドレスを取得
        address = get_wallet_address(wallet, network)
        
        print(f"📍 受信用アドレス:")
        print(f"   {address}")
        print()
        
        # 残高を取得
        try:
            balance_result = wallet.balance()
            balance_sats = balance_result.get("total", 0)
            balance_bsv = balance_sats / 100_000_000
            print("💰 現在の残高:")
            print(f"   {balance_sats:,} sats ({balance_bsv:.8f} BSV)")
            print()
        except KeyError as balance_error:
            message = str(balance_error)
            print(f"⚠️  残高の取得に失敗しました: {message}")
            print("   まだストレージにユーザー情報が作成されていない可能性があります。")
            print("   例: 「5. 公開鍵を取得」や「13. アクションを作成」などを一度実行すると")
            print("       ユーザーが初期化され、残高が参照できるようになります。")
            print()
        except Exception as balance_error:
            print(f"⚠️  残高の取得に失敗しました: {balance_error}")
            print()

        # QR コード用の URI
        amount = 0.001  # デフォルト金額（BSV）
        uri = f"bitcoin:{address}?amount={amount}"
        
        print(f"💳 支払いURI（0.001 BSV）:")
        print(f"   {uri}")
        print()
        
        print("=" * 70)
        print("📋 ブロックチェーンエクスプローラー")
        print("=" * 70)
        print()
        
        if network == "test":
            print(f"🔍 Testnet Explorer:")
            print(f"   https://test.whatsonchain.com/address/{address}")
            print()
            print("💡 Testnet Faucet から BSV を取得:")
            print("   https://scrypt.io/faucet/")
        else:
            print(f"🔍 Mainnet Explorer:")
            print(f"   https://whatsonchain.com/address/{address}")
            print()
            print("⚠️  実際の BSV を使用します！")
        
        print()
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

