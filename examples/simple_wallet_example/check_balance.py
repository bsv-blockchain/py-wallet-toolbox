#!/usr/bin/env python3
"""ウォレットの残高とUTXOを確認するスクリプト"""

import os
from pathlib import Path
from pprint import pprint

from dotenv import load_dotenv
from bsv.keys import PrivateKey
from bsv.constants import Network
from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.brc29 import KeyID, address_for_self
from bsv_wallet_toolbox.services import Services, create_default_options
from src.config import (
    bypass_wallet_infra_auth,
    get_key_deriver,
    get_network,
    get_remote_storage_client,
    get_remote_storage_url,
    get_storage_provider,
    get_wallet_infra_client,
    get_wallet_infra_url,
    use_remote_storage,
    use_wallet_infra,
)

FAUCET_DERIVATION_PREFIX = "faucet-prefix-01"
FAUCET_DERIVATION_SUFFIX = "faucet-suffix-01"

def main():
    # スクリプトのあるディレクトリに移動
    os.chdir(Path(__file__).parent)
    load_dotenv()
    
    print("=" * 70)
    print("💰 ウォレット残高チェッカー")
    print("=" * 70)

    # ウォレット初期化
    chain = get_network()
    key_deriver = get_key_deriver()
    options = create_default_options(chain)
    services = Services(options)
    
    # ストレージモード判定（優先度: wallet-infra > remote > local）
    wallet_infra_mode = use_wallet_infra()
    bypass_auth = bypass_wallet_infra_auth()
    remote_storage_mode = use_remote_storage()

    wallet = None

    if wallet_infra_mode:
        print(f"\n🏗️  wallet-infraモード: {get_wallet_infra_url()}")
        local_storage = get_storage_provider(chain)
        wallet = Wallet(chain=chain, services=services, key_deriver=key_deriver, storage_provider=local_storage)
        infra_client = get_wallet_infra_client(wallet)
        if bypass_auth:
            print("🔄 wallet-infra (認証バイパス)")
            wallet = Wallet(chain=chain, services=services, key_deriver=key_deriver, storage_provider=infra_client)
        else:
            try:
                infra_client.make_available()
                print("✅ wallet-infra接続成功")
                wallet = Wallet(chain=chain, services=services, key_deriver=key_deriver, storage_provider=infra_client)
            except Exception as e:
                print(f"⚠️  wallet-infra接続失敗: {e}")
                wallet_infra_mode = False

    if not wallet_infra_mode and remote_storage_mode:
        print(f"\n🌐 リモートストレージモード: {get_remote_storage_url(chain)}")
        local_storage = get_storage_provider(chain)
        wallet = Wallet(chain=chain, services=services, key_deriver=key_deriver, storage_provider=local_storage)
        remote_client = get_remote_storage_client(wallet, chain)
        try:
            remote_client.make_available()
            print("✅ リモートストレージ接続成功")
            wallet = Wallet(chain=chain, services=services, key_deriver=key_deriver, storage_provider=remote_client)
        except Exception as e:
            print(f"❌ リモートストレージ接続失敗: {e}")
            remote_storage_mode = False

    if not wallet_infra_mode and not remote_storage_mode:
        print("\n💾 ローカルストレージモード")
        storage = get_storage_provider(chain)
        wallet = Wallet(chain=chain, services=services, key_deriver=key_deriver, storage_provider=storage)

    print(f"🟢 ネットワーク: {chain}")
    try:
        identity_key = key_deriver.identity_key().hex()
    except Exception:
        identity_key = "(unknown)"
    print(f"🔑 Identity Key (hex): {identity_key}")

    network = Network.TESTNET if chain == "test" else Network.MAINNET
    root_priv = getattr(key_deriver, "_root_private_key", None)
    try:
        if root_priv:
            addr = root_priv.public_key().address(network=network)
            print(f"📬 Default root address ({chain}): {addr}")
    except Exception:
        pass

    # Faucet デモと同じ BRC-29 派生アドレスを表示
    try:
        if root_priv:
            key_id = KeyID(
                derivation_prefix=FAUCET_DERIVATION_PREFIX,
                derivation_suffix=FAUCET_DERIVATION_SUFFIX,
            )
            faucet_sender = PrivateKey(1).public_key().hex()
            brc29_addr = address_for_self(
                sender_public_key=faucet_sender,
                key_id=key_id,
                recipient_private_key=root_priv,
                testnet=(chain == "test"),
            )
            print(f"📥 Faucet demo address (BRC-29): {brc29_addr.get('address_string')}")
    except Exception:
        pass
    
    # 1. 残高確認
    try:
        balance_result = wallet.balance()
        total_sats = balance_result.get("total") or balance_result.get("total_satoshis", 0)
        print(f"\n💵 現在の残高: {total_sats} satoshis")
    except Exception as e:
        print(f"\n❌ 残高取得エラー: {e}")

    # 2. UTXO一覧確認
    print("\n🔍 有効なUTXO一覧 (spendable):")
    try:
        outputs_result = wallet.list_outputs({
            "basket": "default",
            "limit": 100,
        })
        
        outputs = outputs_result.get("outputs", [])
        spendable_outputs = [o for o in outputs if not o.get("spent") and o.get("spendable") is not False]
        
        if not spendable_outputs:
            print("   (なし)")
        else:
            for i, out in enumerate(spendable_outputs):
                # デバッグ用に全フィールドを表示
                print(f"   --- Output {i+1} ---")
                pprint(out)
                
    except Exception as e:
        print(f"❌ UTXO一覧取得エラー: {e}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
