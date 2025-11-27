"""ウォレット設定のヘルパーモジュール

環境変数からウォレットの設定を読み込みます。
"""

import os
from typing import Literal

from bsv.hd.bip32 import bip32_derive_xprv_from_mnemonic
from bsv.hd.bip39 import mnemonic_from_entropy
from bsv.wallet import KeyDeriver
from bsv_wallet_toolbox.storage import StorageProvider
from dotenv import load_dotenv
from sqlalchemy import create_engine

# .env ファイルから環境変数を読み込む
load_dotenv()

# 型定義
Chain = Literal["main", "test"]


def get_network() -> Chain:
    """環境変数からネットワーク設定を取得します。
    
    環境変数 BSV_NETWORK が設定されていない場合は 'test' を返します。
    
    Returns:
        'test' または 'main'
    """
    network = os.getenv("BSV_NETWORK", "test").lower()
    
    if network not in ("test", "main"):
        print(f"⚠️  警告: 無効なネットワーク設定 '{network}' です。'test' を使用します。")
        return "test"
    
    return network  # type: ignore


def get_mnemonic() -> str | None:
    """環境変数からニーモニックを取得します。
    
    Returns:
        ニーモニック文字列、または None
    """
    return os.getenv("BSV_MNEMONIC")


def get_key_deriver() -> KeyDeriver:
    """環境変数からニーモニックを読み取り、KeyDeriver を作成します。
    
    ニーモニックが設定されていない場合は、新しいニーモニックを自動生成します。
    生成されたニーモニックは標準出力に表示されるので、必ず控えてください。
    
    Returns:
        KeyDeriver インスタンス（常に有効な値を返します）
    """
    mnemonic = get_mnemonic()
    
    if not mnemonic:
        # ニーモニックが設定されていない場合は新規生成
        print("⚠️  ニーモニックが設定されていません。新しいウォレットを生成します...")
        print()
        
        # 新しいニーモニックを生成（12単語）
        mnemonic = mnemonic_from_entropy(entropy=None, lang='en')
        
        # ニーモニックを表示
        print("=" * 70)
        print("🔑 新しいウォレットが生成されました！")
        print("=" * 70)
        print()
        print("📋 ニーモニックフレーズ（12単語）:")
        print()
        print(f"   {mnemonic}")
        print()
        print("=" * 70)
        print("⚠️  重要: このニーモニックフレーズを安全な場所に保管してください！")
        print("=" * 70)
        print()
        print("💡 このニーモニックを使い続けるには、.env ファイルに追加してください:")
        print(f"   BSV_MNEMONIC={mnemonic}")
        print()
        print("=" * 70)
        print()
    
    # ニーモニックから BIP32 拡張秘密鍵を導出（m/0 パス）
    xprv = bip32_derive_xprv_from_mnemonic(
        mnemonic=mnemonic,
        lang='en',
        passphrase='',
        prefix='mnemonic',
        path="m/0",  # 標準的な導出パス
    )
    
    # 拡張秘密鍵から PrivateKey を取得して KeyDeriver を作成
    return KeyDeriver(root_private_key=xprv.private_key())


def get_network_display_name(chain: Chain) -> str:
    """ネットワーク名を表示用に変換します。
    
    Args:
        chain: 'test' または 'main'
        
    Returns:
        表示用のネットワーク名
    """
    return "メインネット（本番環境）" if chain == "main" else "テストネット（開発環境）"


def print_network_info(chain: Chain) -> None:
    """現在のネットワーク設定を表示します。
    
    Args:
        chain: 'test' または 'main'
    """
    display_name = get_network_display_name(chain)
    emoji = "🔴" if chain == "main" else "🟢"
    
    print(f"{emoji} ネットワーク: {display_name}")
    
    if chain == "main":
        print("⚠️  警告: メインネットを使用しています。実際の資金が使用されます！")


def get_storage_provider(network: Chain) -> StorageProvider:
    """StorageProvider を作成します（SQLite ファイルベース）。
    
    ネットワークに応じて異なるデータベースファイルを使用します：
    - testnet: wallet_test.db
    - mainnet: wallet_main.db
    
    Args:
        network: 'test' または 'main'
        
    Returns:
        StorageProvider インスタンス
    """
    # ネットワークに応じたデータベースファイル名
    db_file = f"wallet_{network}.db"
    
    print(f"💾 データベース: {db_file}")
    
    # SQLite エンジンを作成
    engine = create_engine(f"sqlite:///{db_file}")
    
    # StorageProvider を作成
    storage = StorageProvider(
        engine=engine,
        chain=network,
        storage_identity_key=f"{network}-wallet",
    )
    
    # データベーステーブルを初期化（存在しない場合は作成）
    try:
        storage.make_available()
        print(f"✅ データベースが初期化されました")
    except Exception as e:
        print(f"⚠️  データベース初期化エラー: {e}")
        # エラーが発生しても続行（既存のDBの場合など）
    
    return storage

