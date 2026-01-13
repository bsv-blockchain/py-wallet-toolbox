"""Certificate acquisition and listing demos."""

from bsv_wallet_toolbox import Wallet


def demo_acquire_certificate(wallet: Wallet) -> None:
    """Acquire a demo certificate using direct acquisition."""
    print("\n📜 Acquiring certificate\n")

    cert_type = input("Certificate type (e.g. test-certificate) [Enter=default]: ").strip() or "test-certificate"
    name = input("Name [Enter=Test User]: ").strip() or "Test User"
    email = input("Email [Enter=test@example.com]: ").strip() or "test@example.com"

    try:
        result = wallet.acquire_certificate(
            {
                "type": cert_type,
                "certifier": "self",
                "acquisitionProtocol": "direct",
                "fields": {"name": name, "email": email},
                "privilegedReason": "Demo acquisition",
            }
        )
        print("\n✅ Certificate acquired")
        print(f"   Type   : {result['type']}")
        cert_str = result["serializedCertificate"]
        preview = cert_str[:64] + "..." if len(cert_str) > 64 else cert_str
        print(f"   Payload: {preview}")
    except Exception as err:
        print(f"❌ Failed to acquire certificate: {err}")
        import traceback

        traceback.print_exc()


def demo_list_certificates(wallet: Wallet) -> None:
    """List stored certificates."""
    print("\n📜 Listing certificates...\n")

    try:
        certs = wallet.list_certificates(
            {
                "certifiers": [],
                "types": [],
                "limit": 10,
                "offset": 0,
                "privileged": False,
                "privilegedReason": "List certificates",
            }
        )
        print(f"✅ Count: {len(certs['certificates'])}\n")

        if not certs["certificates"]:
            print("   (no certificates yet)")
        else:
            for i, cert in enumerate(certs["certificates"], 1):
                print(f"   {i}. {cert['type']}")
                print(f"      Certificate ID: {cert.get('certificateId', 'N/A')}")
                if "subject" in cert:
                    print(f"      Subject       : {cert['subject']}")
                print()
    except Exception as err:
        print(f"❌ Failed to list certificates: {err}")
