"""暗号化機能（HMAC、暗号化、復号化、署名検証）"""

from bsv_wallet_toolbox import Wallet


def demo_create_hmac(wallet: Wallet) -> None:
    """HMAC 生成のデモを実行します。"""
    print("\n🔐 HMAC を生成します")
    print()

    # ユーザー入力を取得
    message = input("HMAC を生成するメッセージ [Enter=デフォルト]: ").strip() or "Hello, HMAC!"
    protocol_name = input("プロトコル名 [Enter=デフォルト]: ").strip() or "test protocol"
    key_id = input("キー ID [Enter=デフォルト]: ").strip() or "1"

    try:
        data = list(message.encode())
        result = wallet.create_hmac(
            {
                "data": data,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "counterparty": "self",
                "reason": "HMAC の生成",
            }
        )
        print(f"\n✅ HMAC が生成されました！")
        print(f"   メッセージ: {message}")
        print(f"   HMAC: {result['hmac']}")
    except Exception as e:
        print(f"❌ エラー: {e}")


def demo_verify_hmac(wallet: Wallet) -> None:
    """HMAC 検証のデモを実行します。"""
    print("\n🔍 HMAC を検証します")
    print()
    print("まず HMAC を生成してから検証します...")
    print()

    message = "Test HMAC Verification"
    protocol_name = "test protocol"
    key_id = "1"

    try:
        # HMAC を生成
        data = list(message.encode())
        create_result = wallet.create_hmac(
            {
                "data": data,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "counterparty": "self",
                "reason": "HMAC 検証テスト",
            }
        )
        
        hmac_value = create_result["hmac"]
        print(f"生成された HMAC: {hmac_value[:32]}...")
        print()

        # HMAC を検証
        verify_result = wallet.verify_hmac(
            {
                "data": data,
                "hmac": hmac_value,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "counterparty": "self",
                "reason": "HMAC の検証",
            }
        )
        
        print(f"✅ HMAC 検証結果: {verify_result['valid']}")
    except Exception as e:
        print(f"❌ エラー: {e}")


def demo_verify_signature(wallet: Wallet) -> None:
    """署名検証のデモを実行します。"""
    print("\n🔍 署名を検証します")
    print()
    print("まず署名を生成してから検証します...")
    print()

    message = "Test Signature Verification"
    protocol_name = "test protocol"
    key_id = "1"

    try:
        # 署名を生成
        data = list(message.encode())
        create_result = wallet.create_signature(
            {
                "data": data,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "counterparty": "self",
                "reason": "署名検証テスト",
            }
        )
        
        signature = create_result["signature"]
        public_key = create_result["publicKey"]
        print(f"生成された署名: {signature[:32]}...")
        print(f"公開鍵: {public_key[:32]}...")
        print()

        # 署名を検証
        verify_result = wallet.verify_signature(
            {
                "data": data,
                "signature": signature,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "counterparty": "self",
                "reason": "署名の検証",
            }
        )
        
        print(f"✅ 署名検証結果: {verify_result['valid']}")
    except Exception as e:
        print(f"❌ エラー: {e}")


def demo_encrypt_decrypt(wallet: Wallet) -> None:
    """暗号化・復号化のデモを実行します。"""
    print("\n🔐 データを暗号化・復号化します")
    print()

    # ユーザー入力を取得
    message = input("暗号化するメッセージ [Enter=デフォルト]: ").strip() or "Secret Message!"
    protocol_name = input("プロトコル名 [Enter=デフォルト]: ").strip() or "encryption protocol"
    key_id = input("キー ID [Enter=デフォルト]: ").strip() or "1"

    try:
        # 暗号化
        plaintext = list(message.encode())
        encrypt_result = wallet.encrypt(
            {
                "plaintext": plaintext,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "counterparty": "self",
                "reason": "データの暗号化",
            }
        )
        
        ciphertext = encrypt_result["ciphertext"]
        print(f"\n✅ データが暗号化されました！")
        print(f"   元のメッセージ: {message}")
        print(f"   暗号化データ: {ciphertext[:64] if isinstance(ciphertext, str) else ciphertext[:32]}...")
        print()

        # 復号化
        decrypt_result = wallet.decrypt(
            {
                "ciphertext": ciphertext,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "counterparty": "self",
                "reason": "データの復号化",
            }
        )
        
        decrypted = bytes(decrypt_result["plaintext"]).decode()
        print(f"✅ データが復号化されました！")
        print(f"   復号化メッセージ: {decrypted}")
        print(f"   元のメッセージと一致: {decrypted == message}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

