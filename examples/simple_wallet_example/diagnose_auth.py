#!/usr/bin/env python3
"""Diagnostic script for wallet-infra authentication issues.

This script isolates the authentication problem and provides detailed debugging
to compare with TypeScript implementation.
"""

import logging
import os
import sys
from pathlib import Path

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Change to demo directory
os.chdir(Path(__file__).parent)

from dotenv import load_dotenv

load_dotenv()

from bsv.keys import PrivateKey
from bsv.wallet import KeyDeriver

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.rpc import StorageClient
from bsv_wallet_toolbox.services import Services, create_default_options


def test_authentication_diagnostics():
    """Run comprehensive authentication diagnostics."""

    print("=" * 80)
    print("🔍 Wallet-Infra Authentication Diagnostics")
    print("=" * 80)

    # Test 1: Basic wallet creation
    print("\n1️⃣ Testing wallet creation...")
    try:
        root_private_key = PrivateKey()
        key_deriver = KeyDeriver(root_private_key=root_private_key)
        network = "test"
        options = create_default_options(network)
        services = Services(options)

        # Create wallet with local storage first
        from src.config import get_storage_provider

        local_storage = get_storage_provider(network)
        wallet = Wallet(chain=network, services=services, key_deriver=key_deriver, storage_provider=local_storage)

        print("✅ Wallet created successfully")
        # Get identity key from the wallet
        try:
            identity_key_result = wallet.get_public_key({"identityKey": True})
            print(f"   Identity Key: {identity_key_result['publicKey']}")
        except Exception as e:
            print(f"   Could not get identity key: {e}")

    except Exception as e:
        print(f"❌ Wallet creation failed: {e}")
        import traceback

        traceback.print_exc()
        return

    # Test 2: StorageClient creation with different URL formats
    print("\n2️⃣ Testing StorageClient creation with different URL formats...")

    # Test different URL formats
    url_formats = [
        ("localhost:8080", "http://localhost:8080"),
        ("127.0.0.1:8080", "http://127.0.0.1:8080"),
        ("localhost:8080/", "http://localhost:8080/"),
        ("127.0.0.1:8080/", "http://127.0.0.1:8080/"),
    ]

    clients = {}
    for url_name, endpoint_url in url_formats:
        try:
            client = StorageClient(wallet, endpoint_url)
            clients[url_name] = client
            print(f"✅ StorageClient created successfully ({url_name})")
        except Exception as e:
            print(f"❌ StorageClient creation failed ({url_name}): {e}")

    if not clients:
        print("❌ No StorageClient URL formats worked")
        return

    # Use the first working client for further tests
    client = list(clients.values())[0]
    print(f"\n   Using client with URL format: {list(clients.keys())[0]}")

    # Test 3: Authentication handshake
    print("\n3️⃣ Testing authentication handshake...")
    try:
        print("   Calling make_available()...")
        result = client.make_available()
        print("✅ Authentication successful!")
        print(f"   Server response: {result}")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print(f"   Error type: {type(e).__name__}")

        # Try to get more details from the exception
        if hasattr(e, "__cause__") and e.__cause__:
            print(f"   Caused by: {e.__cause__}")
        if hasattr(e, "__context__") and e.__context__:
            print(f"   Context: {e.__context__}")

        # Check if it's a network error vs auth error
        import requests

        if isinstance(e, requests.RequestException):
            print("   This appears to be a network-level error")
        else:
            print("   This appears to be an authentication error")

        # Print full traceback for debugging
        import traceback

        print("\n   Full traceback:")
        traceback.print_exc()

    # Test 4: Compare with direct HTTP/HTTPS requests
    print("\n4️⃣ Testing direct HTTP/HTTPS connections...")

    urls_to_test = [
        ("HTTP localhost:8080", "http://localhost:8080"),
        ("HTTP 127.0.0.1:8080", "http://127.0.0.1:8080"),
    ]

    import requests

    for name, url in urls_to_test:
        try:
            response = requests.post(
                url,
                json={"jsonrpc": "2.0", "method": "makeAvailable", "params": [], "id": 1},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            print(f"✅ {name}: status={response.status_code}")
            if response.status_code == 401:
                print(f"   Auth error: {response.text[:100]}...")
            elif response.status_code >= 200 and response.status_code < 300:
                print(f"   Success: {response.text[:100]}...")
        except Exception as e:
            print(f"❌ {name}: failed - {e}")

    # Test 4b: Check if server supports HTTPS
    print("\n4️⃣b Testing HTTPS connection...")
    try:
        # Try HTTPS even though server might not support it
        response = requests.post(
            "https://localhost:8080",
            json={"jsonrpc": "2.0", "method": "makeAvailable", "params": [], "id": 1},
            headers={"Content-Type": "application/json"},
            timeout=10,
            verify=False,  # Skip SSL verification for localhost
        )
        print(f"✅ HTTPS: status={response.status_code}")
    except Exception as e:
        print(f"❌ HTTPS: failed - {e}")

    # Test 5: Check wallet interface methods in detail
    print("\n5️⃣ Testing wallet interface methods in detail...")
    required_methods = ["get_public_key", "create_signature", "verify_signature", "create_action"]

    for method_name in required_methods:
        try:
            method = getattr(wallet, method_name, None)
            if method:
                print(f"   ✅ {method_name}: implemented")

                # Test calling the method to verify it works
                if method_name == "get_public_key":
                    try:
                        result = wallet.get_public_key({"identityKey": True})
                        print(
                            f"      Returns: {type(result)} with keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}"
                        )
                    except Exception as e:
                        print(f"      ❌ Call failed: {e}")

                elif method_name == "create_signature":
                    try:
                        # Test with minimal data
                        result = wallet.create_signature(
                            {
                                "data": [72, 101, 108, 108, 111],  # "Hello"
                                "protocolID": [0, "test"],
                                "keyID": "1",
                                "counterparty": "self",
                            }
                        )
                        print(
                            f"      Returns: {type(result)} with keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}"
                        )
                    except Exception as e:
                        print(f"      ❌ Call failed: {e}")

                elif method_name == "verify_signature":
                    try:
                        # First create a signature to verify
                        sig_result = wallet.create_signature(
                            {
                                "data": [72, 101, 108, 108, 111],  # "Hello"
                                "protocolID": [0, "test"],
                                "keyID": "1",
                                "counterparty": "self",
                            }
                        )
                        if "signature" in sig_result:
                            result = wallet.verify_signature(
                                {
                                    "data": [72, 101, 108, 108, 111],  # "Hello"
                                    "signature": sig_result["signature"],
                                    "protocolID": [0, "test"],
                                    "keyID": "1",
                                    "counterparty": "self",
                                }
                            )
                            print(f"      Returns: {type(result)} = {result}")
                        else:
                            print("      ❌ Could not create signature to test verification")
                    except Exception as e:
                        print(f"      ❌ Call failed: {e}")

                elif method_name == "create_action":
                    try:
                        # Test with minimal OP_RETURN action
                        result = wallet.create_action(
                            {
                                "description": "Test action",
                                "outputs": [
                                    {
                                        "lockingScript": "006a0568656c6c6f",  # OP_RETURN "hello"
                                        "satoshis": 0,
                                        "outputDescription": "Test output",
                                    }
                                ],
                            }
                        )
                        print(
                            f"      Returns: {type(result)} with keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}"
                        )
                    except Exception as e:
                        print(f"      ❌ Call failed: {e}")

            else:
                print(f"   ❌ {method_name}: missing")
        except Exception as e:
            print(f"   ⚠️  {method_name}: error checking - {e}")

    print("\n" + "=" * 80)
    print("🏁 Diagnostics complete")
    print("=" * 80)


if __name__ == "__main__":
    test_authentication_diagnostics()
