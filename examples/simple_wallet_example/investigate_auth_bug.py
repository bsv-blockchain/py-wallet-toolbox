#!/usr/bin/env python3
"""Deep investigation of the authentication bug."""

import logging
import os
import sys
import traceback
from pathlib import Path

# Enable detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

os.chdir(Path(__file__).parent)

from dotenv import load_dotenv

load_dotenv()

from bsv.keys import PrivateKey
from bsv.wallet import KeyDeriver
from src.config import get_storage_provider

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.rpc import StorageClient
from bsv_wallet_toolbox.services import Services, create_default_options


def investigate_auth_bug():
    """Deep dive into the authentication bug."""

    print("=" * 80)
    print("🔬 Deep Authentication Bug Investigation")
    print("=" * 80)

    # Create wallet
    print("\n1️⃣ Creating wallet...")
    root_private_key = PrivateKey()
    key_deriver = KeyDeriver(root_private_key=root_private_key)
    network = "test"
    options = create_default_options(network)
    services = Services(options)
    local_storage = get_storage_provider(network)
    wallet = Wallet(chain=network, services=services, key_deriver=key_deriver, storage_provider=local_storage)
    print("✅ Wallet created")

    # Create StorageClient
    print("\n2️⃣ Creating StorageClient...")
    endpoint_url = "http://localhost:8080"
    client = StorageClient(wallet, endpoint_url)
    print("✅ StorageClient created")

    # Access the internal AuthFetch implementation
    print("\n3️⃣ Inspecting AuthFetch internals...")
    auth_fetch_impl = client.auth_client._impl
    print(f"   AuthFetch type: {type(auth_fetch_impl)}")
    print(f"   Wallet type: {type(auth_fetch_impl.wallet)}")
    print(f"   Peers: {list(auth_fetch_impl.peers.keys())}")

    # Try to make a request and catch the exact error
    print("\n4️⃣ Attempting make_available() call...")
    try:
        # Monkey-patch to capture more details
        original_fetch = auth_fetch_impl.fetch

        def debug_fetch(url_str, config=None):
            print("\n   📡 AuthFetch.fetch called:")
            print(f"      URL: {url_str}")
            print(f"      Config: {config}")

            # Get peer before call
            parsed_url = __import__("urllib.parse").urlparse(url_str)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            peer_to_use = auth_fetch_impl._get_or_create_peer(base_url)
            print(f"      Peer: {peer_to_use}")
            print(f"      Peer.identity_key: {peer_to_use.identity_key}")
            print(f"      Peer.supports_mutual_auth: {peer_to_use.supports_mutual_auth}")

            try:
                result = original_fetch(url_str, config)
                print(f"      ✅ Fetch succeeded: {result}")
                return result
            except Exception as e:
                print(f"      ❌ Fetch failed: {type(e).__name__}: {e}")
                print(f"      Error details: {e!r}")

                # Try to get more info from the peer
                if hasattr(peer_to_use, "peer") and peer_to_use.peer:
                    print(f"      Peer object: {peer_to_use.peer}")
                    if hasattr(peer_to_use.peer, "transport"):
                        print(f"      Transport: {peer_to_use.peer.transport}")

                raise

        # Temporarily replace fetch method
        auth_fetch_impl.fetch = debug_fetch

        result = client.make_available()
        print(f"\n✅ Success! Result: {result}")

    except Exception as e:
        print("\n❌ Error occurred:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {e!s}")
        print(f"   Repr: {e!r}")

        # Check if it's a RuntimeError with specific message
        if isinstance(e, RuntimeError) and "failed to get authenticated session" in str(e):
            print("\n   🔍 This is the 'failed to get authenticated session' error!")
            print("   Let's investigate what's happening in the peer...")

            # Try to access peer internals
            try:
                parsed_url = __import__("urllib.parse").urlparse(endpoint_url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                peer = auth_fetch_impl.peers.get(base_url)
                if peer:
                    print(f"\n   Peer found: {peer}")
                    print(f"   Peer identity_key: {peer.identity_key}")
                    print(f"   Peer supports_mutual_auth: {peer.supports_mutual_auth}")
                    if hasattr(peer, "peer") and peer.peer:
                        print(f"   Peer.peer: {peer.peer}")
                        # Try to see if there's session info
                        if hasattr(peer.peer, "session_manager"):
                            print(f"   Session manager: {peer.peer.session_manager}")
            except Exception as peer_err:
                print(f"   Could not inspect peer: {peer_err}")

        print("\n   Full traceback:")
        traceback.print_exc()

    # Test 5: Compare with TypeScript behavior
    print("\n5️⃣ Testing direct peer connection...")
    try:
        # Try to manually create a peer and see what happens
        from bsv.auth.peer import Peer, PeerOptions
        from bsv.auth.session_manager import DefaultSessionManager
        from bsv.auth.transports.simplified_http_transport import SimplifiedHTTPTransport

        transport = SimplifiedHTTPTransport(endpoint_url)
        session_manager = DefaultSessionManager()

        peer_options = PeerOptions(
            wallet=wallet, transport=transport, certificates_to_request=None, session_manager=session_manager
        )

        peer = Peer(peer_options)
        print(f"   ✅ Peer created: {peer}")
        print(f"   Transport: {transport}")
        print(f"   Session manager: {session_manager}")

        # Try to send a test message
        print("\n   Attempting to send test message...")
        test_data = b"test"
        err = peer.to_peer(test_data, None, 30000)
        if err:
            print(f"   ❌ Peer.to_peer returned error: {err}")
            print(f"   Error type: {type(err)}")
            print(f"   Error message: {err!s}")
        else:
            print("   ✅ Peer.to_peer succeeded")

    except Exception as e:
        print(f"   ❌ Direct peer test failed: {e}")
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("🏁 Investigation complete")
    print("=" * 80)


if __name__ == "__main__":
    import os

    investigate_auth_bug()
