#!/usr/bin/env python3
"""BRC-100 全28メソッドの網羅的テスト"""

import os
import sys
from pathlib import Path

os.chdir(Path(__file__).parent)

from dotenv import load_dotenv
load_dotenv()

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.services import Services, create_default_options

from src.config import get_key_deriver, get_network, get_storage_provider


def test_method(name: str, func, *args, **kwargs):
    """テストメソッドを実行し、結果を表示"""
    try:
        result = func(*args, **kwargs)
        print(f"  ✅ {name}")
        return result, True
    except Exception as e:
        error_msg = str(e)[:60]
        print(f"  ⚠️  {name}: {error_msg}")
        return None, False


def main():
    print("=" * 70)
    print("🔍 BRC-100 全28メソッド テスト")
    print("=" * 70)
    
    # Initialize wallet
    network = get_network()
    key_deriver = get_key_deriver()
    storage_provider = get_storage_provider(network)
    options = create_default_options(network)
    services = Services(options)
    
    wallet = Wallet(
        chain=network,
        services=services,
        key_deriver=key_deriver,
        storage_provider=storage_provider,
    )
    
    print(f"\n🟢 ネットワーク: {network}")
    print("\n" + "-" * 70)
    
    results = {}
    
    # =========================================================================
    # カテゴリ 1: 基本情報 (4メソッド)
    # =========================================================================
    print("\n📋 カテゴリ 1: 基本情報")
    print("-" * 40)
    
    # 1. get_network
    results['get_network'], _ = test_method(
        "1. get_network",
        wallet.get_network, {}
    )
    
    # 2. get_version
    results['get_version'], _ = test_method(
        "2. get_version",
        wallet.get_version, {}
    )
    
    # 3. is_authenticated
    results['is_authenticated'], _ = test_method(
        "3. is_authenticated",
        wallet.is_authenticated, {}
    )
    
    # 4. wait_for_authentication
    results['wait_for_authentication'], _ = test_method(
        "4. wait_for_authentication",
        wallet.wait_for_authentication, {}
    )
    
    # =========================================================================
    # カテゴリ 2: ブロックチェーン情報 (2メソッド)
    # =========================================================================
    print("\n📋 カテゴリ 2: ブロックチェーン情報")
    print("-" * 40)
    
    # 5. get_height
    results['get_height'], _ = test_method(
        "5. get_height",
        wallet.get_height, {}
    )
    
    # 6. get_header_for_height
    results['get_header_for_height'], _ = test_method(
        "6. get_header_for_height",
        wallet.get_header_for_height, {"height": 1}
    )
    
    # =========================================================================
    # カテゴリ 3: 鍵管理 (3メソッド)
    # =========================================================================
    print("\n📋 カテゴリ 3: 鍵管理")
    print("-" * 40)
    
    # 7. get_public_key
    results['get_public_key'], _ = test_method(
        "7. get_public_key",
        wallet.get_public_key, {"identityKey": True}
    )
    
    # 8. reveal_counterparty_key_linkage
    # counterpartyは実際の公開鍵が必要
    pub_key = results.get('get_public_key', {})
    if pub_key and 'publicKey' in pub_key:
        results['reveal_counterparty_key_linkage'], _ = test_method(
            "8. reveal_counterparty_key_linkage",
            wallet.reveal_counterparty_key_linkage, {
                "counterparty": pub_key['publicKey'],
                "verifier": pub_key['publicKey'],
                "protocolID": [0, "test"],
                "keyID": "1",
            }
        )
    else:
        print("  ⏭️  8. reveal_counterparty_key_linkage (公開鍵取得失敗)")
    
    # 9. reveal_specific_key_linkage
    results['reveal_specific_key_linkage'], _ = test_method(
        "9. reveal_specific_key_linkage",
        wallet.reveal_specific_key_linkage, {
            "counterparty": "self",
            "verifier": "self",
            "protocolID": [0, "test"],
            "keyID": "1",
        }
    )
    
    # =========================================================================
    # カテゴリ 4: 署名 (2メソッド)
    # =========================================================================
    print("\n📋 カテゴリ 4: 署名")
    print("-" * 40)
    
    test_data = list("Hello, BRC-100!".encode())
    
    # 10. create_signature
    sig_result, sig_ok = test_method(
        "10. create_signature",
        wallet.create_signature, {
            "data": test_data,
            "protocolID": [0, "test"],
            "keyID": "1",
            "counterparty": "self",
        }
    )
    results['create_signature'] = sig_result
    
    # 11. verify_signature
    if sig_ok and sig_result:
        results['verify_signature'], _ = test_method(
            "11. verify_signature",
            wallet.verify_signature, {
                "data": test_data,
                "signature": sig_result['signature'],
                "protocolID": [0, "test"],
                "keyID": "1",
                "counterparty": "self",
            }
        )
    else:
        print("  ⏭️  11. verify_signature (署名失敗のためスキップ)")
    
    # =========================================================================
    # カテゴリ 5: HMAC (2メソッド)
    # =========================================================================
    print("\n📋 カテゴリ 5: HMAC")
    print("-" * 40)
    
    # 12. create_hmac
    hmac_result, hmac_ok = test_method(
        "12. create_hmac",
        wallet.create_hmac, {
            "data": test_data,
            "protocolID": [0, "test"],
            "keyID": "1",
            "counterparty": "self",
        }
    )
    results['create_hmac'] = hmac_result
    
    # 13. verify_hmac
    if hmac_ok and hmac_result:
        results['verify_hmac'], _ = test_method(
            "13. verify_hmac",
            wallet.verify_hmac, {
                "data": test_data,
                "hmac": hmac_result['hmac'],
                "protocolID": [0, "test"],
                "keyID": "1",
                "counterparty": "self",
            }
        )
    else:
        print("  ⏭️  13. verify_hmac (HMAC作成失敗のためスキップ)")
    
    # =========================================================================
    # カテゴリ 6: 暗号化 (2メソッド)
    # =========================================================================
    print("\n📋 カテゴリ 6: 暗号化")
    print("-" * 40)
    
    plaintext = list("Secret message!".encode())
    
    # 14. encrypt
    encrypt_result, encrypt_ok = test_method(
        "14. encrypt",
        wallet.encrypt, {
            "plaintext": plaintext,
            "protocolID": [0, "test"],
            "keyID": "1",
            "counterparty": "self",
        }
    )
    results['encrypt'] = encrypt_result
    
    # 15. decrypt
    if encrypt_ok and encrypt_result:
        results['decrypt'], _ = test_method(
            "15. decrypt",
            wallet.decrypt, {
                "ciphertext": encrypt_result['ciphertext'],
                "protocolID": [0, "test"],
                "keyID": "1",
                "counterparty": "self",
            }
        )
    else:
        print("  ⏭️  15. decrypt (暗号化失敗のためスキップ)")
    
    # =========================================================================
    # カテゴリ 7: アクション管理 (5メソッド)
    # =========================================================================
    print("\n📋 カテゴリ 7: アクション管理")
    print("-" * 40)
    
    # 16. list_actions
    results['list_actions'], _ = test_method(
        "16. list_actions",
        wallet.list_actions, {"labels": [], "limit": 10}
    )
    
    # 17. create_action (資金必要)
    results['create_action'], _ = test_method(
        "17. create_action",
        wallet.create_action, {
            "description": "Test action for BRC-100 method test",
            "outputs": [{
                "lockingScript": "006a0568656c6c6f",  # OP_RETURN "hello"
                "satoshis": 0,
                "outputDescription": "Test OP_RETURN output for BRC-100 method verification",
            }],
        }
    )
    
    # 18. sign_action
    # sign_action はカスタムスクリプトを使う場合に必要
    # signAndProcess=False で create_action を呼び、返された reference を使う
    # 
    # 簡単なテストケース: OP_RETURN出力のみ（入力はウォレットが自動選択）の場合
    # sign_action は不要（ウォレットが署名）なので、カスタム入力ケースをテスト
    try:
        # Step 1: signAndProcess=False で create_action
        # これにより signableTransaction が返される
        signable_result = wallet.create_action({
            "description": "Test for sign_action - signable transaction",
            "outputs": [{
                "lockingScript": "006a0b7369676e5f616374696f6e",  # OP_RETURN "sign_action"
                "satoshis": 0,
                "outputDescription": "Test output for sign_action",
            }],
            "options": {
                "signAndProcess": False,  # ← これで signableTransaction が返る
            }
        })
        
        if signable_result and signable_result.get("signableTransaction"):
            st = signable_result["signableTransaction"]
            reference = st.get("reference")
            
            if reference:
                # Step 2: sign_action を呼ぶ
                # この場合、ウォレットの入力なので spends は空でOK
                results['sign_action'], sign_ok = test_method(
                    "18. sign_action",
                    wallet.sign_action, {
                        "reference": reference,
                        "spends": {},  # ウォレット入力は自動署名
                        "options": {"acceptDelayedBroadcast": True}
                    }
                )
            else:
                print("  ⚠️  18. sign_action: signableTransaction に reference がありません")
        else:
            print("  ⚠️  18. sign_action: signAndProcess=False でも signableTransaction が返されませんでした")
    except Exception as e:
        print(f"  ⚠️  18. sign_action: {str(e)[:60]}")
    
    # 19. abort_action
    # abort_action をテストするには unsigned 状態のアクションが必要
    # signAndProcess=False で create_action を呼び、sign_action を呼ばずに abort
    try:
        # Step 1: abort_action テスト用に新しい unsigned アクションを作成
        abort_test_result = wallet.create_action({
            "description": "Test for abort_action - will be aborted",
            "outputs": [{
                "lockingScript": "006a0c61626f72745f616374696f6e",  # OP_RETURN "abort_action"
                "satoshis": 0,
                "outputDescription": "Test output for abort_action",
            }],
            "options": {
                "signAndProcess": False,  # ← unsigned 状態で止める
            }
        })
        
        if abort_test_result and abort_test_result.get("signableTransaction"):
            abort_reference = abort_test_result["signableTransaction"].get("reference")
            
            if abort_reference:
                # Step 2: この unsigned アクションを abort
                results['abort_action'], _ = test_method(
                    "19. abort_action",
                    wallet.abort_action, {"reference": abort_reference}
                )
            else:
                print("  ⚠️  19. abort_action: signableTransaction に reference がありません")
        else:
            # signableTransaction がない場合、list_actions から unsigned を探す
            actions_for_abort = wallet.list_actions({"labels": [], "limit": 10})
            unsigned_for_abort = [a for a in actions_for_abort.get('actions', []) if a.get('status') == 'unsigned']
            if unsigned_for_abort and unsigned_for_abort[0].get('reference'):
                results['abort_action'], _ = test_method(
                    "19. abort_action",
                    wallet.abort_action, {"reference": unsigned_for_abort[0]['reference']}
                )
            else:
                print("  ⏭️  19. abort_action (unsignedアクションが作成できませんでした)")
    except Exception as e:
        print(f"  ⚠️  19. abort_action: {str(e)[:60]}")
    
    # 20. internalize_action
    # 既にinternalizeされたtxを使用してテスト（重複internalizeはエラーになるが、メソッド自体は動作確認）
    from src.transaction_management import _build_atomic_beef_for_txid
    test_txid = "8e609cd401cdec648c71f6a5ec09a395f87567e71421b04fe6389adf6552bde7"
    try:
        atomic_beef = _build_atomic_beef_for_txid(network, test_txid)
        results['internalize_action'], _ = test_method(
            "20. internalize_action",
            wallet.internalize_action, {
                "tx": atomic_beef,
                "outputs": [{
                    "outputIndex": 0,
                    "protocol": "basket insertion",
                    "insertionRemittance": {"basket": "default"},
                }],
                "description": "Test internalize action",
            }
        )
    except Exception as e:
        print(f"  ⚠️  20. internalize_action: {str(e)[:60]}")
    
    # =========================================================================
    # カテゴリ 8: アウトプット管理 (3メソッド)
    # =========================================================================
    print("\n📋 カテゴリ 8: アウトプット管理")
    print("-" * 40)
    
    # 21. list_outputs
    results['list_outputs'], _ = test_method(
        "21. list_outputs",
        wallet.list_outputs, {"basket": "default", "limit": 10}
    )
    
    # 21b. balance (specOpWalletBalance を使用)
    results['balance'], _ = test_method(
        "21b. balance (残高取得)",
        wallet.balance
    )
    
    # 22. relinquish_output
    results['relinquish_output'], _ = test_method(
        "22. relinquish_output",
        wallet.relinquish_output, {
            "basket": "default",
            "output": "0000000000000000000000000000000000000000000000000000000000000000.0"
        }
    )
    
    # =========================================================================
    # カテゴリ 9: 証明書管理 (4メソッド)
    # =========================================================================
    print("\n📋 カテゴリ 9: 証明書管理")
    print("-" * 40)
    
    # 23. list_certificates
    results['list_certificates'], _ = test_method(
        "23. list_certificates",
        wallet.list_certificates, {"certifiers": [], "types": [], "limit": 10}
    )
    
    # 24. acquire_certificate
    # certifierは公開鍵が必要
    if pub_key and 'publicKey' in pub_key:
        results['acquire_certificate'], _ = test_method(
            "24. acquire_certificate",
            wallet.acquire_certificate, {
                "type": "dGVzdC1jZXJ0aWZpY2F0ZQ==",  # base64 of "test-certificate"
                "certifier": pub_key['publicKey'],
                "acquisitionProtocol": "direct",
                "fields": {"name": "Test"},
            }
        )
    else:
        print("  ⏭️  24. acquire_certificate (公開鍵取得失敗)")
    
    # 25. prove_certificate (有効な証明書必要)
    print("  ⏭️  25. prove_certificate (有効な証明書必要)")
    
    # 26. relinquish_certificate
    if pub_key and 'publicKey' in pub_key:
        results['relinquish_certificate'], _ = test_method(
            "26. relinquish_certificate",
            wallet.relinquish_certificate, {
                "type": "dGVzdC1jZXJ0aWZpY2F0ZQ==",  # base64 of "test-certificate"
                "certifier": pub_key['publicKey'],
                "serialNumber": "ZHVtbXktc2VyaWFs"  # base64 of "dummy-serial"
            }
        )
    else:
        print("  ⏭️  26. relinquish_certificate (公開鍵取得失敗)")
    
    # =========================================================================
    # カテゴリ 10: ディスカバリー (2メソッド)
    # =========================================================================
    print("\n📋 カテゴリ 10: ディスカバリー")
    print("-" * 40)
    
    # 27. discover_by_identity_key
    results['discover_by_identity_key'], _ = test_method(
        "27. discover_by_identity_key",
        wallet.discover_by_identity_key, {
            "identityKey": "0250d7462e60bcf4523b0e783c9bac2300000000000000000000000000000000",
            "limit": 5,
        }
    )
    
    # 28. discover_by_attributes
    results['discover_by_attributes'], _ = test_method(
        "28. discover_by_attributes",
        wallet.discover_by_attributes, {
            "attributes": {"name": "Test"},
            "limit": 5,
        }
    )
    
    # =========================================================================
    # 結果サマリー
    # =========================================================================
    print("\n" + "=" * 70)
    print("📊 結果サマリー")
    print("=" * 70)
    
    # Count results
    tested = 0
    passed = 0
    skipped = 0
    
    method_names = [
        "get_network", "get_version", "is_authenticated", "wait_for_authentication",
        "get_height", "get_header_for_height",
        "get_public_key", "reveal_counterparty_key_linkage", "reveal_specific_key_linkage",
        "create_signature", "verify_signature",
        "create_hmac", "verify_hmac",
        "encrypt", "decrypt",
        "list_actions", "create_action", "sign_action", "abort_action", "internalize_action",
        "list_outputs", "relinquish_output",
        "list_certificates", "acquire_certificate", "prove_certificate", "relinquish_certificate",
        "discover_by_identity_key", "discover_by_attributes"
    ]
    
    for name in method_names:
        if name in results:
            tested += 1
            if results[name] is not None:
                passed += 1
        else:
            skipped += 1
    
    print(f"\n  テスト実行: {tested}/28")
    print(f"  成功: {passed}")
    print(f"  スキップ: {skipped} (資金/有効データ必要)")
    print(f"  エラー: {tested - passed}")
    
    print("\n" + "=" * 70)
    print("✅ BRC-100 メソッドテスト完了")
    print("=" * 70)


if __name__ == "__main__":
    main()

