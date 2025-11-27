"""ウォレットアドレスと残高管理"""

from bsv.keys import PublicKey
from bsv_wallet_toolbox import Wallet


def get_wallet_address(wallet: Wallet) -> str:
    """ウォレットの受信用アドレスを取得します。
    
    Args:
        wallet: Wallet インスタンス
        
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
    address = public_key.address()
    
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
        address = get_wallet_address(wallet)
        
        print(f"📍 受信用アドレス:")
        print(f"   {address}")
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
            print(f"   https://faucet.bitcoincloud.net/")
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

