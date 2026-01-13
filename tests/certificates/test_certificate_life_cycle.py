"""Unit tests for certificate lifecycle operations.

This module tests complete flows for MasterCertificate and VerifiableCertificate.

Reference: wallet-toolbox/src/sdk/__test/CertificateLifeCycle.test.ts
"""

import base64

try:
    from bsv.keys import PrivateKey as SDKPrivateKey

    from bsv_wallet_toolbox.certificate import Certificate, MasterCertificate, VerifiableCertificate
    from bsv_wallet_toolbox.private_key import PrivateKey
    from bsv_wallet_toolbox.wallet import ProtoWallet

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


def to_base64(data) -> str:
    """Convert data to base64 string."""
    if isinstance(data, list):
        data = bytes(data)
    return base64.b64encode(data).decode("ascii")


class PrivateKeyWrapper:
    """Wrapper for SDK's PrivateKey to add publicKey() method for ProtoWallet compatibility."""

    def __init__(self, sdk_private_key: SDKPrivateKey):
        """Initialize with SDK's PrivateKey."""
        self._private_key = sdk_private_key

    def publicKey(self):
        """Return public key (camelCase method for ProtoWallet compatibility)."""
        return self._private_key.public_key

    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped PrivateKey."""
        return getattr(self._private_key, name)


def to_sdk_private_key(stub_private_key: PrivateKey) -> PrivateKeyWrapper:
    """Convert stub PrivateKey to SDK's PrivateKey wrapped for ProtoWallet compatibility.

    Args:
        stub_private_key: The stub PrivateKey from bsv_wallet_toolbox.private_key

    Returns:
        Wrapped SDK's PrivateKey object with publicKey() method
    """
    # Handle random keys by generating a valid hex string
    if stub_private_key.key_hex == "random_key_hex_placeholder":
        # Generate a valid random 32-byte hex string (64 hex characters)
        import secrets

        random_hex = secrets.token_hex(32)
        sdk_key = SDKPrivateKey.from_hex(random_hex)
    else:
        # Use the hex string from the stub key
        sdk_key = SDKPrivateKey.from_hex(stub_private_key.key_hex)

    return PrivateKeyWrapper(sdk_key)


def make_sample_cert(subject_root_key_hex: str = None, certifier_key_hex: str = None, verifier_key_hex: str = None):
    """Create sample certificate for testing.

    Reference: wallet-toolbox/src/sdk/__test/CertificateLifeCycle.test.ts
               function makeSampleCert()
    """
    subject = PrivateKey.from_string(subject_root_key_hex) if subject_root_key_hex else PrivateKey.from_random()
    certifier = PrivateKey.from_string(certifier_key_hex) if certifier_key_hex else PrivateKey.from_random()
    PrivateKey.from_string(verifier_key_hex) if verifier_key_hex else PrivateKey.from_random()

    cert = {
        "type": to_base64([1] * 32),
        "serialNumber": to_base64([2] * 32),
        "revocationOutpoint": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef.1",
        "subject": subject.to_public_key().to_string(),
        "certifier": certifier.to_public_key().to_string(),
        "fields": {"name": "Alice", "email": "alice@example.com", "organization": "Example Corp"},
        "signature": "",
    }

    return {"cert": cert, "subject": subject, "certifier": certifier}


class TestCertificateLifeCycle:
    """Test suite for certificate lifecycle operations.

    Reference: wallet-toolbox/src/sdk/__test/CertificateLifeCycle.test.ts
               describe('CertificateLifeCycle tests')
    """

    # @pytest.mark.skip(reason="Requires full Certificate subsystem implementation")
    def test_complete_flow_mastercertificate_and_verifiablecertificate(self) -> None:
        """Given: Certifier, subject, and verifier wallets with sample certificate
           When: Certifier encrypts fields, signs certificate, subject decrypts, creates keyring for verifier
           Then: Signed certificate verifies, subject decrypts all fields, verifier decrypts only 'name' and 'email'

        Reference: wallet-toolbox/src/sdk/__test/CertificateLifeCycle.test.ts
                   test('2a complete flow MasterCertificate and VerifiableCertificate')
        """
        # Given - Issuer begins with an un-encrypted (decrypted) raw certificate template:
        # The public keys of both the certifier (the authority issuing the certificate),
        # and the subject (who the certificate pertains to) are included in the certificate.
        sample = make_sample_cert("1" * 64, "2" * 64, "3" * 64)
        wcert = sample["cert"]
        certifier = sample["certifier"]
        subject = sample["subject"]

        cert = Certificate(
            wcert["type"],
            wcert["serialNumber"],
            wcert["subject"],
            wcert["certifier"],
            wcert["revocationOutpoint"],
            wcert["fields"],
        )

        # Next the certifier must encrypt the field values for privacy and sign the certificate
        # such that the values it contains can be attributed to the certifier through its public key.
        # Encryption is done with random symmetric keys and the keys are then encrypted by the certifier
        # such that each key can also be decrypted by the subject:
        certifier_wallet = ProtoWallet(to_sdk_private_key(certifier))

        # encrypt the fields as the certifier for the subject
        r1 = MasterCertificate.create_certificate_fields(
            certifier_wallet, subject.to_public_key().to_string(), cert.fields
        )

        # sign the certificate with encrypted fields as the certifier
        signed_cert = Certificate(
            wcert["type"],
            wcert["serialNumber"],
            wcert["subject"],
            wcert["certifier"],
            wcert["revocationOutpoint"],
            r1["certificateFields"],
        )
        signed_cert.sign(certifier_wallet)

        # The subject imports their copy of the new certificate:
        subject_wallet = ProtoWallet(to_sdk_private_key(subject))

        # The subject's imported certificate should verify
        assert signed_cert.verify() is True

        # Confirm subject can decrypt the certifier's copy of the cert:
        MasterCertificate.decrypt_fields(subject_wallet, r1["masterKeyring"], signed_cert.fields, signed_cert.certifier)

        # Prepare to send certificate to third party verifier of the 'name' and 'email' fields.
        # The verifier must be able to confirm the signature on the original certificate's encrypted values.
        # And then use a keyRing that their public key will work to reveal decrypted values for 'name' and 'email' only.
        verifier = PrivateKey.from_random()

        # subject makes a keyring for the verifier
        r3 = MasterCertificate.create_keyring_for_verifier(
            subject_wallet,
            certifier.to_public_key().to_string(),
            verifier.to_public_key().to_string(),
            signed_cert.fields,
            ["name", "email"],
            r1["masterKeyring"],
            signed_cert.serial_number,
        )

        # The verifier uses their own wallet to import the certificate, verify it, and decrypt their designated fields.
        verifier_wallet = ProtoWallet(to_sdk_private_key(verifier))

        veri_cert = VerifiableCertificate(
            signed_cert.type,
            signed_cert.serial_number,
            signed_cert.subject,
            signed_cert.certifier,
            signed_cert.revocation_outpoint,
            signed_cert.fields,
            r3,
            signed_cert.signature,
        )

        # When
        r4 = veri_cert.decrypt_fields(verifier_wallet)

        # Then - verifier can decrypt 'name' and 'email' but not 'organization'
        assert r4["name"] == "Alice"
        assert r4["email"] == "alice@example.com"
        assert r4.get("organization") != "Example Corp"  # Not disclosed to verifier
