#!/usr/bin/env python3
"""Comprehensive test of all 28 BRC-100 methods

Usage:
    # Use local SQLite storage (default)
    python test_all_28_methods.py

    # Use Babbage remote storage
    USE_REMOTE_STORAGE=true python test_all_28_methods.py

    # Use wallet-infra server
    USE_WALLET_INFRA=true python test_all_28_methods.py

    # Use wallet-infra server (auth bypass - testing only)
    USE_WALLET_INFRA=true BYPASS_WALLET_INFRA_AUTH=true python test_all_28_methods.py
"""

import os
from pathlib import Path

os.chdir(Path(__file__).parent)

from dotenv import load_dotenv

load_dotenv()

from bsv.keys import PrivateKey
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

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.brc29 import KeyID, address_for_self
from bsv_wallet_toolbox.services import Services, create_default_options


def test_method(name: str, func, *args, **kwargs):
    """Execute test method and display results"""
    try:
        result = func(*args, **kwargs)
        print(f"  ✅ {name}")
        return result, True
    except Exception as e:
        error_msg = str(e)[:60]
        print(f"  ⚠️  {name}: {error_msg}")
        return None, False


FAUCET_DERIVATION_PREFIX = "faucet-prefix-01"
FAUCET_DERIVATION_SUFFIX = "faucet-suffix-01"


def main():
    print("=" * 70)
    print("🔍 BRC-100 All 28 Methods Test")
    print("=" * 70)

    # Initialize wallet
    network = get_network()
    key_deriver = get_key_deriver()
    options = create_default_options(network)
    services = Services(options)

    # Check storage mode (priority: wallet-infra > remote > local)
    wallet_infra_mode = use_wallet_infra()
    bypass_auth = bypass_wallet_infra_auth()
    remote_storage_mode = use_remote_storage()

    if wallet_infra_mode:
        print(f"\n🏗️  wallet-infra mode: {get_wallet_infra_url()}")
        print("⚠️  wallet-infra requires BRC-104 authentication")
        print("-" * 70)

        # First create wallet with local storage (required for StorageClient auth)
        local_storage = get_storage_provider(network)
        wallet = Wallet(
            chain=network,
            services=services,
            key_deriver=key_deriver,
            storage_provider=local_storage,
        )

        # Create wallet-infra client
        infra_client = get_wallet_infra_client(wallet)

        # Test wallet-infra connection
        if bypass_auth:
            print("\n🔄 Bypassing wallet-infra authentication for direct connection...")
            print("   Note: This is for testing purposes only. Do not use in production.")

            # Create new wallet instance using StorageClient as storage provider (bypass auth)
            print("\n🔄 Creating wallet instance using wallet-infra storage...")
            wallet = Wallet(
                chain=network,
                services=services,
                key_deriver=key_deriver,
                storage_provider=infra_client,
            )
            print("✅ wallet-infra wallet instance created successfully (auth bypass)!")
        else:
            try:
                print("\n🔄 Connecting to wallet-infra...")
                infra_settings = infra_client.make_available()
                print("✅ wallet-infra connection successful!")
                print(f"   Storage Identity Key: {infra_settings.get('storageIdentityKey', 'N/A')}")
                print(f"   Chain: {infra_settings.get('chain', 'N/A')}")

                # Create new wallet instance using StorageClient as storage provider
                print("\n🔄 Creating wallet instance using wallet-infra storage...")
                wallet = Wallet(
                    chain=network,
                    services=services,
                    key_deriver=key_deriver,
                    storage_provider=infra_client,
                )
                print("✅ wallet-infra wallet instance created successfully!")

            except Exception as e:
                print(f"⚠️  wallet-infra authentication failed: {e}")
                print("   This is a known issue with Python SDK. Continuing tests with local storage...")
                print("   Note: wallet-infra authentication is not currently supported in Python.")
                print("   For testing, you can set BYPASS_WALLET_INFRA_AUTH=true to bypass authentication.")
                wallet_infra_mode = False  # Fall back to local

    if not wallet_infra_mode and remote_storage_mode:
        print(f"\n🌐 Remote storage mode: {get_remote_storage_url(network)}")
        print("⚠️  Remote storage requires BRC-104 authentication")
        print("-" * 70)

        # First create wallet with local storage (required for StorageClient auth)
        local_storage = get_storage_provider(network)
        wallet = Wallet(
            chain=network,
            services=services,
            key_deriver=key_deriver,
            storage_provider=local_storage,
        )

        # Create remote storage client
        remote_client = get_remote_storage_client(wallet, network)

        # Test remote connection
        try:
            print("\n🔄 Connecting to remote storage...")
            remote_settings = remote_client.make_available()
            print("✅ Remote storage connection successful!")
            print(f"   Storage Identity Key: {remote_settings.get('storageIdentityKey', 'N/A')}")
            print(f"   Chain: {remote_settings.get('chain', 'N/A')}")

            # Create new wallet instance using StorageClient as storage provider
            print("\n🔄 Creating wallet instance using remote storage...")
            wallet = Wallet(
                chain=network,
                services=services,
                key_deriver=key_deriver,
                storage_provider=remote_client,
            )
            print("✅ Remote storage wallet instance created successfully!")

        except Exception as e:
            print(f"❌ Remote storage connection failed: {e}")
            print("   Continuing with local storage...")
            remote_storage_mode = False  # Fall back to local

    if not wallet_infra_mode and not remote_storage_mode:
        print("\n💾 Local storage mode")
        storage_provider = get_storage_provider(network)
        wallet = Wallet(
            chain=network,
            services=services,
            key_deriver=key_deriver,
            storage_provider=storage_provider,
        )

    # -------------------------------------------------------------------------
    # Demo addition: Display faucet BRC-29 receiving address
    # -------------------------------------------------------------------------
    try:
        # In this demo, use the same BRC-29 pattern as the Go/TS faucet example:
        # - senderIdentityKey as AnyoneKey (= PrivateKey(1).public_key())
        # - derivationPrefix / derivationSuffix are fixed strings

        # Root private key (directly referenced from KeyDeriver for demo)
        root_priv = getattr(key_deriver, "_root_private_key", None)
        if root_priv is None:
            raise RuntimeError("Could not retrieve root_private_key from KeyDeriver.")

        # sender (faucet side) is treated as AnyoneKey
        anyone_key = PrivateKey(1).public_key()
        print(f"anyone_key: {anyone_key.hex()}")

        key_id = KeyID(
            derivation_prefix=FAUCET_DERIVATION_PREFIX,
            derivation_suffix=FAUCET_DERIVATION_SUFFIX,
        )

        # Generate receiver (self) address using BRC-29
        is_testnet = network == "test"
        addr_info = address_for_self(
            sender_public_key=anyone_key.hex(),
            key_id=key_id,
            recipient_private_key=root_priv,
            testnet=is_testnet,
        )
        addr = addr_info["address_string"]

        print("\n" + "-" * 70)
        print("📥  Faucet receiving address (BRC-29)")
        print("-" * 70)
        print("Try sending a small amount of BSV from a Faucet to this address.")
        print("※ This script alone does not consume UTXOs.")
        print("   When combined with `faucet_internalize_and_create_action.py`,")
        print("   it becomes a demo of using received coins in internalize → create_action.")
        print(f"\n   Address: {addr}")
        if is_testnet:
            print("\n   Testnet faucet examples:")
            print("     - https://scrypt.io/faucet")
            print("     - https://witnessonchain.com/faucet/tbsv")

        input("\n⏸ Press Enter to continue tests after sending from faucet...")
    except Exception as e:
        print(f"\n⚠️  Error occurred while displaying receiving address: {str(e)[:60]}")

    print(f"\n🟢 Network: {network}")
    print("\n" + "-" * 70)

    results = {}

    # =========================================================================
    # Category 1: Basic Information (4 methods)
    # =========================================================================
    print("\n📋 Category 1: Basic Information")
    print("-" * 40)

    # 1. get_network
    results["get_network"], _ = test_method("1. get_network", wallet.get_network, {})

    # 2. get_version
    results["get_version"], _ = test_method("2. get_version", wallet.get_version, {})

    # 3. is_authenticated
    results["is_authenticated"], _ = test_method("3. is_authenticated", wallet.is_authenticated, {})

    # 4. wait_for_authentication
    results["wait_for_authentication"], _ = test_method(
        "4. wait_for_authentication", wallet.wait_for_authentication, {}
    )

    # =========================================================================
    # Category 2: Blockchain Information (2 methods)
    # =========================================================================
    print("\n📋 Category 2: Blockchain Information")
    print("-" * 40)

    # 5. get_height
    results["get_height"], _ = test_method("5. get_height", wallet.get_height, {})

    # 6. get_header_for_height
    results["get_header_for_height"], _ = test_method(
        "6. get_header_for_height", wallet.get_header_for_height, {"height": 1}
    )

    # =========================================================================
    # Category 3: Key Management (3 methods)
    # =========================================================================
    print("\n📋 Category 3: Key Management")
    print("-" * 40)

    # 7. get_public_key
    results["get_public_key"], _ = test_method("7. get_public_key", wallet.get_public_key, {"identityKey": True})

    # 8. reveal_counterparty_key_linkage
    # counterparty requires an actual public key
    pub_key = results.get("get_public_key", {})
    if pub_key and "publicKey" in pub_key:
        results["reveal_counterparty_key_linkage"], _ = test_method(
            "8. reveal_counterparty_key_linkage",
            wallet.reveal_counterparty_key_linkage,
            {
                "counterparty": pub_key["publicKey"],
                "verifier": pub_key["publicKey"],
                "protocolID": [0, "test"],
                "keyID": "1",
            },
        )
    else:
        print("  ⏭️  8. reveal_counterparty_key_linkage (failed to get public key)")

    # 9. reveal_specific_key_linkage
    results["reveal_specific_key_linkage"], _ = test_method(
        "9. reveal_specific_key_linkage",
        wallet.reveal_specific_key_linkage,
        {
            "counterparty": "self",
            "verifier": "self",
            "protocolID": [0, "test"],
            "keyID": "1",
        },
    )

    # =========================================================================
    # Category 4: Signatures (2 methods)
    # =========================================================================
    print("\n📋 Category 4: Signatures")
    print("-" * 40)

    test_data = list(b"Hello, BRC-100!")

    # 10. create_signature
    sig_result, sig_ok = test_method(
        "10. create_signature",
        wallet.create_signature,
        {
            "data": test_data,
            "protocolID": [0, "test"],
            "keyID": "1",
            "counterparty": "self",
        },
    )
    results["create_signature"] = sig_result

    # 11. verify_signature
    if sig_ok and sig_result:
        results["verify_signature"], _ = test_method(
            "11. verify_signature",
            wallet.verify_signature,
            {
                "data": test_data,
                "signature": sig_result["signature"],
                "protocolID": [0, "test"],
                "keyID": "1",
                "counterparty": "self",
            },
        )
    else:
        print("  ⏭️  11. verify_signature (skipped due to signature failure)")

    # =========================================================================
    # Category 5: HMAC (2 methods)
    # =========================================================================
    print("\n📋 Category 5: HMAC")
    print("-" * 40)

    # 12. create_hmac
    hmac_result, hmac_ok = test_method(
        "12. create_hmac",
        wallet.create_hmac,
        {
            "data": test_data,
            "protocolID": [0, "test"],
            "keyID": "1",
            "counterparty": "self",
        },
    )
    results["create_hmac"] = hmac_result

    # 13. verify_hmac
    if hmac_ok and hmac_result:
        results["verify_hmac"], _ = test_method(
            "13. verify_hmac",
            wallet.verify_hmac,
            {
                "data": test_data,
                "hmac": hmac_result["hmac"],
                "protocolID": [0, "test"],
                "keyID": "1",
                "counterparty": "self",
            },
        )
    else:
        print("  ⏭️  13. verify_hmac (skipped due to HMAC creation failure)")

    # =========================================================================
    # Category 6: Encryption (2 methods)
    # =========================================================================
    print("\n📋 Category 6: Encryption")
    print("-" * 40)

    plaintext = list(b"Secret message!")

    # 14. encrypt
    encrypt_result, encrypt_ok = test_method(
        "14. encrypt",
        wallet.encrypt,
        {
            "plaintext": plaintext,
            "protocolID": [0, "test"],
            "keyID": "1",
            "counterparty": "self",
        },
    )
    results["encrypt"] = encrypt_result

    # 15. decrypt
    if encrypt_ok and encrypt_result:
        results["decrypt"], _ = test_method(
            "15. decrypt",
            wallet.decrypt,
            {
                "ciphertext": encrypt_result["ciphertext"],
                "protocolID": [0, "test"],
                "keyID": "1",
                "counterparty": "self",
            },
        )
    else:
        print("  ⏭️  15. decrypt (skipped due to encryption failure)")

    # =========================================================================
    # Category 7: Action Management (5 methods)
    # =========================================================================
    print("\n📋 Category 7: Action Management")
    print("-" * 40)

    # 16. list_actions
    results["list_actions"], _ = test_method("16. list_actions", wallet.list_actions, {"labels": [], "limit": 10})

    # 17. create_action (funds required)
    results["create_action"], _ = test_method(
        "17. create_action",
        wallet.create_action,
        {
            "description": "Test action for BRC-100 method test",
            "outputs": [
                {
                    "lockingScript": "006a0568656c6c6f",  # OP_RETURN "hello"
                    "satoshis": 0,
                    "outputDescription": "Test OP_RETURN output for BRC-100 method verification",
                }
            ],
        },
    )

    # 18. sign_action
    # sign_action is needed when using custom scripts
    # Call create_action with signAndProcess=False and use the returned reference
    #
    # Simple test case: Only OP_RETURN output (wallet auto-selects inputs)
    # sign_action is not needed (wallet signs automatically), so test custom input case
    try:
        # Step 1: create_action with signAndProcess=False
        # This returns signableTransaction
        signable_result = wallet.create_action(
            {
                "description": "Test for sign_action - signable transaction",
                "outputs": [
                    {
                        "lockingScript": "006a0b7369676e5f616374696f6e",  # OP_RETURN "sign_action"
                        "satoshis": 0,
                        "outputDescription": "Test output for sign_action",
                    }
                ],
                "options": {
                    "signAndProcess": False,  # ← This returns signableTransaction
                },
            }
        )

        if signable_result and signable_result.get("signableTransaction"):
            st = signable_result["signableTransaction"]
            reference = st.get("reference")

            if reference:
                # Step 2: Call sign_action
                # In this case, spends can be empty since wallet provides inputs
                results["sign_action"], sign_ok = test_method(
                    "18. sign_action",
                    wallet.sign_action,
                    {
                        "reference": reference,
                        "spends": {},  # Wallet inputs are auto-signed
                        "options": {"acceptDelayedBroadcast": True},
                    },
                )
            else:
                print("  ⚠️  18. sign_action: signableTransaction has no reference")
        else:
            print("  ⚠️  18. sign_action: signableTransaction not returned even with signAndProcess=False")
    except Exception as e:
        print(f"  ⚠️  18. sign_action: {str(e)[:60]}")

    # 19. abort_action
    # abort_action needs an unsigned action to test
    # Call create_action with signAndProcess=False, then abort without calling sign_action
    try:
        # Step 1: Create a new unsigned action for abort_action testing
        abort_test_result = wallet.create_action(
            {
                "description": "Test for abort_action - will be aborted",
                "outputs": [
                    {
                        "lockingScript": "006a0c61626f72745f616374696f6e",  # OP_RETURN "abort_action"
                        "satoshis": 0,
                        "outputDescription": "Test output for abort_action",
                    }
                ],
                "options": {
                    "signAndProcess": False,  # ← Stop in unsigned state
                },
            }
        )

        if abort_test_result and abort_test_result.get("signableTransaction"):
            abort_reference = abort_test_result["signableTransaction"].get("reference")

            if abort_reference:
                # Step 2: Abort this unsigned action
                results["abort_action"], _ = test_method(
                    "19. abort_action", wallet.abort_action, {"reference": abort_reference}
                )
            else:
                print("  ⚠️  19. abort_action: signableTransaction has no reference")
        else:
            # If no signableTransaction, look for unsigned actions from list_actions
            actions_for_abort = wallet.list_actions({"labels": [], "limit": 10})
            unsigned_for_abort = [a for a in actions_for_abort.get("actions", []) if a.get("status") == "unsigned"]
            if unsigned_for_abort and unsigned_for_abort[0].get("reference"):
                results["abort_action"], _ = test_method(
                    "19. abort_action", wallet.abort_action, {"reference": unsigned_for_abort[0]["reference"]}
                )
            else:
                print("  ⏭️  19. abort_action (could not create unsigned action)")
    except Exception as e:
        print(f"  ⚠️  19. abort_action: {str(e)[:60]}")

    # 20. internalize_action
    # Test using already internalized tx (duplicate internalize causes error, but method itself works)
    from src.transaction_management import _build_atomic_beef_for_txid

    test_txid = "8e609cd401cdec648c71f6a5ec09a395f87567e71421b04fe6389adf6552bde7"
    try:
        atomic_beef = _build_atomic_beef_for_txid(network, test_txid)
        results["internalize_action"], _ = test_method(
            "20. internalize_action",
            wallet.internalize_action,
            {
                "tx": atomic_beef,
                "outputs": [
                    {
                        "outputIndex": 0,
                        "protocol": "basket insertion",
                        "insertionRemittance": {"basket": "default"},
                    }
                ],
                "description": "Test internalize action",
            },
        )
    except Exception as e:
        print(f"  ⚠️  20. internalize_action: {str(e)[:60]}")

    # =========================================================================
    # Category 8: Output Management (3 methods)
    # =========================================================================
    print("\n📋 Category 8: Output Management")
    print("-" * 40)

    # 21. list_outputs
    results["list_outputs"], _ = test_method(
        "21. list_outputs", wallet.list_outputs, {"basket": "default", "limit": 10}
    )

    # 21b. balance (using specOpWalletBalance)
    results["balance"], _ = test_method("21b. balance (get balance)", wallet.balance)

    # 22. relinquish_output
    results["relinquish_output"], _ = test_method(
        "22. relinquish_output",
        wallet.relinquish_output,
        {"basket": "default", "output": "0000000000000000000000000000000000000000000000000000000000000000.0"},
    )

    # =========================================================================
    # Category 9: Certificate Management (4 methods)
    # =========================================================================
    print("\n📋 Category 9: Certificate Management")
    print("-" * 40)

    # 23. list_certificates
    results["list_certificates"], _ = test_method(
        "23. list_certificates", wallet.list_certificates, {"certifiers": [], "types": [], "limit": 10}
    )

    # 24. acquire_certificate
    # Direct acquisition requires a complete pre-signed certificate
    # For testing, we create a self-signed certificate using the wallet's own key
    if pub_key and "publicKey" in pub_key:
        import base64
        import os

        # Generate test certificate data
        test_serial = base64.b64encode(os.urandom(32)).decode("utf-8")
        test_type = "dGVzdC1jZXJ0aWZpY2F0ZQ=="  # base64 of "test-certificate"

        # For direct acquisition, we need:
        # - type, certifier, subject, serialNumber (required)
        # - revocationOutpoint, signature, fields, keyringForSubject (optional but recommended)
        # Since we don't have a real certifier, we use placeholder values
        # Note: This will skip signature verification since signature is not valid
        results["acquire_certificate"], _ = test_method(
            "24. acquire_certificate",
            wallet.acquire_certificate,
            {
                "type": test_type,
                "certifier": pub_key["publicKey"],  # Self-signed for testing
                "subject": pub_key["publicKey"],
                "serialNumber": test_serial,
                "revocationOutpoint": "0000000000000000000000000000000000000000000000000000000000000000.0",
                "signature": "",  # Empty signature - verification will be skipped
                "fields": {"name": "VGVzdA=="},  # base64 encrypted "Test"
                "keyringForSubject": {},
                "keyringRevealer": "certifier",
                "acquisitionProtocol": "direct",
            },
        )
    else:
        print("  ⏭️  24. acquire_certificate (failed to get public key)")

    # 25. prove_certificate
    # prove_certificate requires stored certificate, verifier public key, and valid keyring
    # Note: prove_certificate requires a certificate with valid keyring to decrypt/re-encrypt
    # Since our test certificate has empty keyring, this will fail
    # In production, certificates would be acquired from a real certifier with proper encryption
    if results.get("acquire_certificate") and pub_key and "publicKey" in pub_key:
        cert_data = results["acquire_certificate"]
        # Check if certificate has valid keyring (fields and keyring must match)
        has_valid_keyring = bool(cert_data.get("fields")) and len(cert_data.get("fields", {})) > 0

        if has_valid_keyring:
            try:
                results["prove_certificate"], _ = test_method(
                    "25. prove_certificate",
                    wallet.prove_certificate,
                    {
                        "certificate": {
                            "type": cert_data.get("type"),
                            "serialNumber": cert_data.get("serialNumber"),
                            "certifier": cert_data.get("certifier"),
                            "subject": cert_data.get("subject"),
                            "revocationOutpoint": cert_data.get("revocationOutpoint"),
                            "signature": cert_data.get("signature"),
                            "fields": cert_data.get("fields", {}),
                        },
                        "verifier": pub_key["publicKey"],
                        "fieldsToReveal": list(cert_data.get("fields", {}).keys()),
                    },
                )
            except Exception as e:
                print(f"  ⚠️  25. prove_certificate: {str(e)[:60]}")
        else:
            print(
                "  ⏭️  25. prove_certificate (valid keyring required - use certificate obtained via issuance protocol)"
            )
    else:
        print("  ⏭️  25. prove_certificate (valid certificate required)")

    # 26. relinquish_certificate
    if pub_key and "publicKey" in pub_key:
        results["relinquish_certificate"], _ = test_method(
            "26. relinquish_certificate",
            wallet.relinquish_certificate,
            {
                "type": "dGVzdC1jZXJ0aWZpY2F0ZQ==",  # base64 of "test-certificate"
                "certifier": pub_key["publicKey"],
                "serialNumber": "ZHVtbXktc2VyaWFs",  # base64 of "dummy-serial"
            },
        )
    else:
        print("  ⏭️  26. relinquish_certificate (failed to get public key)")

    # =========================================================================
    # Category 10: Discovery (2 methods)
    # =========================================================================
    print("\n📋 Category 10: Discovery")
    print("-" * 40)

    # 27. discover_by_identity_key
    results["discover_by_identity_key"], _ = test_method(
        "27. discover_by_identity_key",
        wallet.discover_by_identity_key,
        {
            "identityKey": "0250d7462e60bcf4523b0e783c9bac2300000000000000000000000000000000",
            "limit": 5,
        },
    )

    # 28. discover_by_attributes
    results["discover_by_attributes"], _ = test_method(
        "28. discover_by_attributes",
        wallet.discover_by_attributes,
        {
            "attributes": {"name": "Test"},
            "limit": 5,
        },
    )

    # =========================================================================
    # Results Summary
    # =========================================================================
    print("\n" + "=" * 70)
    print("📊 Results Summary")
    print("=" * 70)

    # Count results
    tested = 0
    passed = 0
    skipped = 0

    method_names = [
        "get_network",
        "get_version",
        "is_authenticated",
        "wait_for_authentication",
        "get_height",
        "get_header_for_height",
        "get_public_key",
        "reveal_counterparty_key_linkage",
        "reveal_specific_key_linkage",
        "create_signature",
        "verify_signature",
        "create_hmac",
        "verify_hmac",
        "encrypt",
        "decrypt",
        "list_actions",
        "create_action",
        "sign_action",
        "abort_action",
        "internalize_action",
        "list_outputs",
        "relinquish_output",
        "list_certificates",
        "acquire_certificate",
        "prove_certificate",
        "relinquish_certificate",
        "discover_by_identity_key",
        "discover_by_attributes",
    ]

    for name in method_names:
        if name in results:
            tested += 1
            if results[name] is not None:
                passed += 1
        else:
            skipped += 1

    print(f"\n  Tests run: {tested}/28")
    print(f"  Successful: {passed}")
    print(f"  Skipped: {skipped} (funds/valid data required)")
    print(f"  Errors: {tested - passed}")

    print("\n" + "=" * 70)
    print("✅ BRC-100 Method Tests Completed")
    print("=" * 70)


if __name__ == "__main__":
    main()
