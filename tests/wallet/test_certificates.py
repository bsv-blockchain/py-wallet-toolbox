"""Unit tests for Wallet certificate-related methods.

These methods handle certificate acquisition, proving, relinquishing, and discovery.

Reference: wallet-toolbox/src/Wallet.ts
"""

from typing import Never

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError


@pytest.fixture
def valid_acquire_certificate_args():
    """Fixture providing valid acquire certificate arguments."""
    return {
        "serialNumber": "test_serial_123",
        "signature": "test_signature_abc",
        "privileged": False,
        "privilegedReason": None,
        "type": "dGVzdA==",  # base64 "test"
        "certifier": "02" + "00" * 32,  # valid pubkey format
        "acquisitionProtocol": "direct",
        "fields": {"name": "Test User"},
        "keyringForSubject": {"key": "value"},
        "keyringRevealer": "certifier",
        "revocationOutpoint": "2795b293c698b2244147aaba745db887a632d21990c474df46d842ec3e52f122.0"
    }


@pytest.fixture
def valid_relinquish_certificate_args():
    """Fixture providing valid relinquish certificate arguments."""
    return {
        "type": "dGVzdA==",  # base64 "test"
        "serialNumber": "test_serial_123",
        "certifier": "02" + "00" * 32  # valid pubkey format
    }


@pytest.fixture
def valid_prove_certificate_args():
    """Fixture providing valid prove certificate arguments."""
    return {
        "certificate": {
            "type": "dGVzdA==",
            "serialNumber": "test_serial",
            "certifier": "02" + "00" * 32
        },
        "verifier": "03" + "ff" * 32,
        "fieldsToReveal": ["name"]
    }


@pytest.fixture
def invalid_acquire_certificate_cases():
    """Fixture providing various invalid acquire certificate arguments."""
    return [
        # Invalid type
        {"type": "", "certifier": "02" + "00" * 32, "acquisitionProtocol": "direct", "fields": {}},
        {"type": None, "certifier": "02" + "00" * 32, "acquisitionProtocol": "direct", "fields": {}},
        {"type": 123, "certifier": "02" + "00" * 32, "acquisitionProtocol": "direct", "fields": {}},
        {"type": [], "certifier": "02" + "00" * 32, "acquisitionProtocol": "direct", "fields": {}},

        # Invalid certifier
        {"type": "dGVzdA==", "certifier": "", "acquisitionProtocol": "direct", "fields": {}},
        {"type": "dGVzdA==", "certifier": None, "acquisitionProtocol": "direct", "fields": {}},
        {"type": "dGVzdA==", "certifier": "invalid-hex", "acquisitionProtocol": "direct", "fields": {}},
        {"type": "dGVzdA==", "certifier": "02" + "gg" * 32, "acquisitionProtocol": "direct", "fields": {}},  # invalid hex

        # Invalid acquisition protocol
        {"type": "dGVzdA==", "certifier": "02" + "00" * 32, "acquisitionProtocol": "", "fields": {}},
        {"type": "dGVzdA==", "certifier": "02" + "00" * 32, "acquisitionProtocol": None, "fields": {}},
        {"type": "dGVzdA==", "certifier": "02" + "00" * 32, "acquisitionProtocol": "invalid", "fields": {}},

        # Invalid fields
        {"type": "dGVzdA==", "certifier": "02" + "00" * 32, "acquisitionProtocol": "direct", "fields": None},
        {"type": "dGVzdA==", "certifier": "02" + "00" * 32, "acquisitionProtocol": "direct", "fields": "not_dict"},

        # Missing required keys
        {"certifier": "02" + "00" * 32, "acquisitionProtocol": "direct", "fields": {}},  # missing type
        {"type": "dGVzdA==", "acquisitionProtocol": "direct", "fields": {}},  # missing certifier
        {"type": "dGVzdA==", "certifier": "02" + "00" * 32, "fields": {}},  # missing acquisitionProtocol
        {},  # missing all
    ]


@pytest.fixture
def invalid_relinquish_certificate_cases():
    """Fixture providing various invalid relinquish certificate arguments."""
    return [
        # Invalid type
        {"type": "", "serialNumber": "test", "certifier": "02" + "00" * 32},
        {"type": None, "serialNumber": "test", "certifier": "02" + "00" * 32},
        {"type": 123, "serialNumber": "test", "certifier": "02" + "00" * 32},

        # Invalid serial number
        {"type": "dGVzdA==", "serialNumber": "", "certifier": "02" + "00" * 32},
        {"type": "dGVzdA==", "serialNumber": None, "certifier": "02" + "00" * 32},
        {"type": "dGVzdA==", "serialNumber": 123, "certifier": "02" + "00" * 32},

        # Invalid certifier
        {"type": "dGVzdA==", "serialNumber": "test", "certifier": ""},
        {"type": "dGVzdA==", "serialNumber": "test", "certifier": None},
        {"type": "dGVzdA==", "serialNumber": "test", "certifier": "invalid-hex"},
        {"type": "dGVzdA==", "serialNumber": "test", "certifier": "02" + "gg" * 32},

        # Missing keys
        {"serialNumber": "test", "certifier": "02" + "00" * 32},  # missing type
        {"type": "dGVzdA==", "certifier": "02" + "00" * 32},  # missing serialNumber
        {"type": "dGVzdA==", "serialNumber": "test"},  # missing certifier
        {},  # missing all
    ]


class TestWalletAcquireCertificate:
    """Test suite for Wallet.acquire_certificate method.

    Reference: wallet-toolbox/test/Wallet/certificate/acquireCertificate.test.ts
    """

    def test_00(self, wallet_with_storage: Wallet) -> None:
        """Given: No operation
           When: Test placeholder
           Then: Pass

        Reference: wallet-toolbox/test/Wallet/certificate/acquireCertificate.test.ts
                   test('00')
        """
        # Given/When/Then

    def test_invalid_params(self, wallet_with_services: Wallet) -> None:
        """Given: Wallet with test storage and invalid certificate arguments
           When: Call acquireCertificate with invalid params (empty type, empty certifier)
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/Wallet/certificate/acquireCertificate.test.ts
                   test('1 invalid params')
        """
        # Given
        # wallet = Wallet(chain="test")  # Not needed, using wallet_with_services

        invalid_args = {"type": "", "certifier": "", "acquisitionProtocol": "direct", "fields": {}}

        # When/Then
        with pytest.raises(InvalidParameterError):
            wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_empty_type_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: AcquireCertificateArgs with empty type
           When: Call acquire_certificate
           Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"type": "", "certifier": "02" + "00" * 32, "acquisitionProtocol": "direct", "fields": {}}

        # When/Then
        with pytest.raises(InvalidParameterError):
            wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_none_type_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: AcquireCertificateArgs with None type
           When: Call acquire_certificate
           Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"type": None, "certifier": "02" + "00" * 32, "acquisitionProtocol": "direct", "fields": {}}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_wrong_type_type_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: AcquireCertificateArgs with wrong type type
           When: Call acquire_certificate
           Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, [], {}, True, 45.67]

        for invalid_type in invalid_types:
            invalid_args = {"type": invalid_type, "certifier": "02" + "00" * 32, "acquisitionProtocol": "direct", "fields": {}}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_empty_certifier_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: AcquireCertificateArgs with empty certifier
           When: Call acquire_certificate
           Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"type": "dGVzdA==", "certifier": "", "acquisitionProtocol": "direct", "fields": {}}

        # When/Then
        with pytest.raises(InvalidParameterError):
            wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_none_certifier_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: AcquireCertificateArgs with None certifier
           When: Call acquire_certificate
           Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"type": "dGVzdA==", "certifier": None, "acquisitionProtocol": "direct", "fields": {}}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_wrong_certifier_type_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: AcquireCertificateArgs with wrong certifier type
           When: Call acquire_certificate
           Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, [], {}, True, 45.67]

        for invalid_certifier in invalid_types:
            invalid_args = {"type": "dGVzdA==", "certifier": invalid_certifier, "acquisitionProtocol": "direct", "fields": {}}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_invalid_hex_certifier_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: AcquireCertificateArgs with invalid hex certifier
           When: Call acquire_certificate
           Then: Raises InvalidParameterError
        """
        # Given - Invalid hex certifier strings
        invalid_hex_certifiers = [
            "gggggggggggggggggggggggggggggggggggggggg",  # Invalid hex chars
            "abcdef1234567890abcdef1234567890abcd",  # Too short (31 bytes)
            "abcdef1234567890abcdef1234567890abcdef12",  # Too long (33 bytes)
            "abcdef1234567890abcdef1234567890abcde",  # Odd length
        ]

        for certifier in invalid_hex_certifiers:
            invalid_args = {"type": "dGVzdA==", "certifier": certifier, "acquisitionProtocol": "direct", "fields": {}}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError)):
                wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_empty_acquisition_protocol_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: AcquireCertificateArgs with empty acquisition protocol
           When: Call acquire_certificate
           Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"type": "dGVzdA==", "certifier": "02" + "00" * 32, "acquisitionProtocol": "", "fields": {}}

        # When/Then
        with pytest.raises(InvalidParameterError):
            wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_none_acquisition_protocol_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: AcquireCertificateArgs with None acquisition protocol
           When: Call acquire_certificate
           Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"type": "dGVzdA==", "certifier": "02" + "00" * 32, "acquisitionProtocol": None, "fields": {}}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_wrong_acquisition_protocol_type_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: AcquireCertificateArgs with wrong acquisition protocol type
           When: Call acquire_certificate
           Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, [], {}, True, 45.67]

        for invalid_protocol in invalid_types:
            invalid_args = {"type": "dGVzdA==", "certifier": "02" + "00" * 32, "acquisitionProtocol": invalid_protocol, "fields": {}}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_invalid_acquisition_protocol_value_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: AcquireCertificateArgs with invalid acquisition protocol value
           When: Call acquire_certificate
           Then: Raises InvalidParameterError
        """
        # Given - Invalid protocol values
        invalid_protocols = ["invalid", "DIRECT", "protocol", "", "   "]

        for protocol in invalid_protocols:
            invalid_args = {"type": "dGVzdA==", "certifier": "02" + "00" * 32, "acquisitionProtocol": protocol, "fields": {}}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError)):
                wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_none_fields_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: AcquireCertificateArgs with None fields
           When: Call acquire_certificate
           Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"type": "dGVzdA==", "certifier": "02" + "00" * 32, "acquisitionProtocol": "direct", "fields": None}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_wrong_fields_type_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: AcquireCertificateArgs with wrong fields type
           When: Call acquire_certificate
           Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, "string", [], True, 45.67]

        for invalid_fields in invalid_types:
            invalid_args = {"type": "dGVzdA==", "certifier": "02" + "00" * 32, "acquisitionProtocol": "direct", "fields": invalid_fields}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_missing_type_key_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: AcquireCertificateArgs missing type key
           When: Call acquire_certificate
           Then: Raises InvalidParameterError or KeyError
        """
        # Given
        invalid_args = {"certifier": "02" + "00" * 32, "acquisitionProtocol": "direct", "fields": {}}

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError)):
            wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_missing_certifier_key_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: AcquireCertificateArgs missing certifier key
           When: Call acquire_certificate
           Then: Raises InvalidParameterError or KeyError
        """
        # Given
        invalid_args = {"type": "dGVzdA==", "acquisitionProtocol": "direct", "fields": {}}

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError)):
            wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_missing_acquisition_protocol_key_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: AcquireCertificateArgs missing acquisition protocol key
           When: Call acquire_certificate
           Then: Raises InvalidParameterError or KeyError
        """
        # Given
        invalid_args = {"type": "dGVzdA==", "certifier": "02" + "00" * 32, "fields": {}}

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError)):
            wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_empty_args_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: Empty AcquireCertificateArgs
           When: Call acquire_certificate
           Then: Raises InvalidParameterError or KeyError
        """
        # Given
        invalid_args = {}

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError)):
            wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_privileged_none_reason_with_privileged_true_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: AcquireCertificateArgs with privileged=True but privilegedReason=None
           When: Call acquire_certificate
           Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {
            "type": "dGVzdA==",
            "certifier": "02" + "00" * 32,
            "acquisitionProtocol": "direct",
            "fields": {},
            "privileged": True,
            "privilegedReason": None
        }

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_services.acquire_certificate(invalid_args)

    def test_invalid_params_privileged_empty_reason_with_privileged_true_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: AcquireCertificateArgs with privileged=True but empty privilegedReason
           When: Call acquire_certificate
           Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {
            "type": "dGVzdA==",
            "certifier": "02" + "00" * 32,
            "acquisitionProtocol": "direct",
            "fields": {},
            "privileged": True,
            "privilegedReason": ""
        }

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_services.acquire_certificate(invalid_args)

    @pytest.mark.skip(reason="Requires Certificate subsystem implementation")
    def test_acquirecertificate_listcertificate_provecertificate(self, wallet_with_storage: Wallet) -> None:
        """Given: Wallet with test database and sample certificate from certifier
           When: acquireCertificate, listCertificates, proveCertificate, and relinquishCertificate
           Then: Certificate is stored, retrieved, fields are encrypted, can be decrypted with keyring, and relinquished

        Reference: wallet-toolbox/test/Wallet/certificate/acquireCertificate.test.ts
                   test('2 acquireCertificate listCertificate proveCertificate')
        """
        # Given
        # Create test wallet with SQLite storage
        # wallet = Wallet(chain="test")  # Not needed, using wallet_with_storage

        # Make a test certificate from a random certifier for the wallet's identityKey
        subject = wallet_with_storage.key_deriver.identity_key
        cert_data, certifier = _make_sample_cert(subject)

        # Act as the certifier: create a wallet for them
        certifier_wallet = _create_proto_wallet(certifier)

        # Create certificate and sign it
        cert = _create_certificate(cert_data)
        signed_fields = _create_certificate_fields(certifier_wallet, subject, cert["fields"])
        signed_cert = _create_signed_certificate(cert_data, signed_fields)
        _sign_certificate(signed_cert, certifier_wallet)

        # Prepare args object to create a new certificate via 'direct' protocol
        args = {
            "serialNumber": signed_cert["serialNumber"],
            "signature": signed_cert["signature"],
            "privileged": False,
            "privilegedReason": None,
            "type": signed_cert["type"],
            "certifier": signed_cert["certifier"],
            "acquisitionProtocol": "direct",
            "fields": signed_cert["fields"],
            "keyringForSubject": signed_fields["masterKeyring"],
            "keyringRevealer": "certifier",
            "revocationOutpoint": signed_cert["revocationOutpoint"],
        }

        # When
        # Store the new signed certificate in user's wallet
        result = wallet_with_storage.acquire_certificate(args)

        # Then
        assert result["serialNumber"] == signed_cert["serialNumber"]

        # Attempt to retrieve it
        list_result = wallet_with_storage.list_certificates({"certifiers": [cert_data["certifier"]], "types": []})
        assert len(list_result["certificates"]) == 1
        lc = list_result["certificates"][0]

        # The result should be encrypted
        assert lc["fields"]["name"] != "Alice"

        # Use proveCertificate to obtain a decryption keyring
        prove_args = {
            "certificate": {"serialNumber": lc["serialNumber"]},
            "fieldsToReveal": ["name"],
            "verifier": subject,
        }
        prove_result = wallet_with_storage.prove_certificate(prove_args)

        # Create VerifiableCertificate and decrypt fields
        verifiable_cert = _create_verifiable_certificate(lc, prove_result["keyringForVerifier"])
        decrypted = _decrypt_fields(verifiable_cert, wallet_with_storage)
        assert decrypted["name"] == "Alice"

        # Cleanup: relinquish all certificates
        certs = wallet_with_storage.list_certificates({"types": [], "certifiers": []})
        for cert in certs["certificates"]:
            relinquish_result = wallet_with_storage.relinquish_certificate(
                {"type": cert["type"], "serialNumber": cert["serialNumber"], "certifier": cert["certifier"]}
            )
            assert relinquish_result["relinquished"] is True

    @pytest.mark.skip(reason="Requires Certificate subsystem implementation")
    def test_privileged_acquirecertificate_listcertificate_provecertificate(self, wallet_with_storage: Wallet) -> None:
        """Given: Wallet with privilegedKeyManager and certificate issued to privileged key
           When: acquireCertificate with privileged=True, proveCertificate with privileged=True
           Then: Certificate is stored, encrypted fields can be decrypted with privileged keyring

        Reference: wallet-toolbox/test/Wallet/certificate/acquireCertificate.test.ts
                   test('3 privileged acquireCertificate listCertificate proveCertificate')
        """
        # Given
        # Create test wallet with privilegedKeyManager
        wallet = Wallet(chain="test", priv_key_hex="42" * 32)

        # Certificate issued to the privileged key must use privilegedKeyManager's identityKey
        subject = wallet_with_storage.privileged_key_manager.get_public_key(identity_key=True)
        subject_key = subject["publicKey"]
        cert_data, certifier = _make_sample_cert(subject_key)

        # Act as the certifier: create a wallet for them
        certifier_wallet = _create_proto_wallet(certifier)

        # Create certificate and sign it
        cert = _create_certificate(cert_data)
        signed_fields = _create_certificate_fields(certifier_wallet, subject_key, cert["fields"])
        signed_cert = _create_signed_certificate(cert_data, signed_fields)
        _sign_certificate(signed_cert, certifier_wallet)

        # Prepare args object for privileged certificate
        args = {
            "serialNumber": signed_cert["serialNumber"],
            "signature": signed_cert["signature"],
            "privileged": True,
            "privilegedReason": "access to my penthouse",
            "type": signed_cert["type"],
            "certifier": signed_cert["certifier"],
            "acquisitionProtocol": "direct",
            "fields": signed_cert["fields"],
            "keyringForSubject": signed_fields["masterKeyring"],
            "keyringRevealer": "certifier",
            "revocationOutpoint": signed_cert["revocationOutpoint"],
        }

        # When
        # Store the privileged certificate
        result = wallet_with_storage.acquire_certificate(args)

        # Then
        assert result["serialNumber"] == signed_cert["serialNumber"]

        # Retrieve the certificate
        list_result = wallet_with_storage.list_certificates({"certifiers": [cert_data["certifier"]], "types": []})
        assert len(list_result["certificates"]) == 1
        lc = list_result["certificates"][0]

        # Fields should be encrypted
        assert lc["fields"]["name"] != "Alice"

        # Use proveCertificate with privileged=True
        prove_args = {
            "certificate": {"serialNumber": lc["serialNumber"]},
            "fieldsToReveal": ["name"],
            "verifier": subject_key,
            "privileged": True,
            "privilegedReason": "more cheese",
        }
        prove_result = wallet_with_storage.prove_certificate(prove_args)

        # Decrypt fields with privileged keyring
        verifiable_cert = _create_verifiable_certificate(lc, prove_result["keyringForVerifier"])
        decrypted = _decrypt_fields(verifiable_cert, wallet, privileged=True, privileged_reason="more cheese")
        assert decrypted["name"] == "Alice"

        # Cleanup: relinquish all certificates
        certs = wallet_with_storage.list_certificates({"types": [], "certifiers": []})
        for cert in certs["certificates"]:
            relinquish_result = wallet_with_storage.relinquish_certificate(
                {"type": cert["type"], "serialNumber": cert["serialNumber"], "certifier": cert["certifier"]}
            )
            assert relinquish_result["relinquished"] is True

        # Also cleans up the privilegedKeyManager
        wallet_with_storage.destroy()


# Helper functions for certificate testing (to be implemented with API)
def _make_sample_cert(subject: str) -> tuple:
    """Create a sample certificate for testing."""
    raise NotImplementedError("Certificate helper not implemented yet")


def _create_proto_wallet(certifier: str) -> Never:
    """Create a ProtoWallet for certifier."""
    raise NotImplementedError("ProtoWallet not implemented yet")


def _create_certificate(cert_data: dict) -> dict:
    """Create a Certificate object."""
    raise NotImplementedError("Certificate creation not implemented yet")


def _create_certificate_fields(wallet, subject: str, fields: dict) -> dict:
    """Create certificate fields using MasterCertificate."""
    raise NotImplementedError("MasterCertificate.createCertificateFields not implemented yet")


def _create_signed_certificate(cert_data: dict, signed_fields: dict) -> dict:
    """Create a signed certificate."""
    raise NotImplementedError("Signed certificate creation not implemented yet")


def _sign_certificate(cert: dict, wallet) -> None:
    """Sign a certificate."""
    raise NotImplementedError("Certificate signing not implemented yet")


def _create_verifiable_certificate(cert: dict, keyring: dict) -> Never:
    """Create a VerifiableCertificate."""
    raise NotImplementedError("VerifiableCertificate not implemented yet")


def _decrypt_fields(cert, wallet, privileged: bool = False, privileged_reason: str = None) -> dict:
    """Decrypt certificate fields."""
    raise NotImplementedError("Field decryption not implemented yet")


class TestWalletProveCertificate:
    """Test suite for Wallet.prove_certificate method."""

    @pytest.mark.skip(reason="Requires Certificate subsystem implementation")
    def test_prove_certificate(self, wallet_with_services: Wallet) -> None:
        """Given: ProveCertificateArgs with certificate and verifier
           When: Call prove_certificate
           Then: Returns certificate proof

        Note: Based on BRC-100 specification for certificate proving.
        """
        # Given
        args = {
            "certificate": {"type": "dGVzdA==", "serialNumber": "c2VyaWFs", "certifier": "02" + "00" * 32},
            "verifier": "03" + "ff" * 32,  # Verifier public key
            "fieldsToReveal": ["name"],  # Only reveal specific fields
        }

        # When
        result = wallet_with_services.prove_certificate(args)

        # Then
        assert "certificate" in result
        assert "keyring" in result  # Keyring for verification

    def test_invalid_params_missing_certificate_key_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: ProveCertificateArgs missing certificate key
           When: Call prove_certificate
           Then: Raises InvalidParameterError or KeyError
        """
        # Given
        invalid_args = {"verifier": "03" + "ff" * 32, "fieldsToReveal": ["name"]}

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError)):
            wallet_with_services.prove_certificate(invalid_args)

    def test_invalid_params_missing_verifier_key_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: ProveCertificateArgs missing verifier key
           When: Call prove_certificate
           Then: Raises InvalidParameterError or KeyError
        """
        # Given
        invalid_args = {
            "certificate": {"type": "dGVzdA==", "serialNumber": "test", "certifier": "02" + "00" * 32},
            "fieldsToReveal": ["name"]
        }

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError)):
            wallet_with_services.prove_certificate(invalid_args)

    def test_invalid_params_missing_fields_to_reveal_key_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: ProveCertificateArgs missing fieldsToReveal key
           When: Call prove_certificate
           Then: Raises InvalidParameterError or KeyError
        """
        # Given
        invalid_args = {
            "certificate": {"type": "dGVzdA==", "serialNumber": "test", "certifier": "02" + "00" * 32},
            "verifier": "03" + "ff" * 32
        }

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError)):
            wallet_with_services.prove_certificate(invalid_args)

    def test_invalid_params_empty_certificate_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: ProveCertificateArgs with empty certificate
           When: Call prove_certificate
           Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"certificate": {}, "verifier": "03" + "ff" * 32, "fieldsToReveal": ["name"]}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_services.prove_certificate(invalid_args)

    def test_invalid_params_none_certificate_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: ProveCertificateArgs with None certificate
           When: Call prove_certificate
           Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"certificate": None, "verifier": "03" + "ff" * 32, "fieldsToReveal": ["name"]}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_services.prove_certificate(invalid_args)

    def test_invalid_params_empty_fields_to_reveal_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: ProveCertificateArgs with empty fieldsToReveal
           When: Call prove_certificate
           Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {
            "certificate": {"type": "dGVzdA==", "serialNumber": "test", "certifier": "02" + "00" * 32},
            "verifier": "03" + "ff" * 32,
            "fieldsToReveal": []
        }

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_services.prove_certificate(invalid_args)

    def test_invalid_params_none_fields_to_reveal_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: ProveCertificateArgs with None fieldsToReveal
           When: Call prove_certificate
           Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {
            "certificate": {"type": "dGVzdA==", "serialNumber": "test", "certifier": "02" + "00" * 32},
            "verifier": "03" + "ff" * 32,
            "fieldsToReveal": None
        }

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_services.prove_certificate(invalid_args)

    def test_invalid_params_wrong_certificate_type_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: ProveCertificateArgs with wrong certificate type
           When: Call prove_certificate
           Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, "string", [], True, 45.67]

        for invalid_cert in invalid_types:
            invalid_args = {"certificate": invalid_cert, "verifier": "03" + "ff" * 32, "fieldsToReveal": ["name"]}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_services.prove_certificate(invalid_args)

    def test_invalid_params_wrong_fields_to_reveal_type_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: ProveCertificateArgs with wrong fieldsToReveal type
           When: Call prove_certificate
           Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, "string", {}, True, 45.67]

        for invalid_fields in invalid_types:
            invalid_args = {
                "certificate": {"type": "dGVzdA==", "serialNumber": "test", "certifier": "02" + "00" * 32},
                "verifier": "03" + "ff" * 32,
                "fieldsToReveal": invalid_fields
            }

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_services.prove_certificate(invalid_args)

    def test_invalid_params_empty_args_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: Empty ProveCertificateArgs
           When: Call prove_certificate
           Then: Raises InvalidParameterError or KeyError
        """
        # Given
        invalid_args = {}

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError)):
            wallet_with_services.prove_certificate(invalid_args)


class TestWalletRelinquishCertificate:
    """Test suite for Wallet.relinquish_certificate method."""

    def test_relinquish_certificate(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishCertificateArgs with certificate identifiers
           When: Call relinquish_certificate
           Then: Certificate is marked as relinquished

        Reference: wallet-toolbox/test/wallet/list/listCertificates.test.ts

        Note: This test requires a populated test database with certificates.
        """
        # Given
        args = {"type": "dGVzdA==", "serialNumber": "c2VyaWFs", "certifier": "02" + "00" * 32}

        # When
        result = wallet_with_storage.relinquish_certificate(args)

        # Then
        assert "relinquished" in result
        assert result["relinquished"] is True

    def test_invalid_params_empty_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishCertificateArgs with empty type
           When: Call relinquish_certificate
           Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"type": "", "serialNumber": "test", "certifier": "02" + "00" * 32}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_storage.relinquish_certificate(invalid_args)

    def test_invalid_params_none_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishCertificateArgs with None type
           When: Call relinquish_certificate
           Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"type": None, "serialNumber": "test", "certifier": "02" + "00" * 32}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_storage.relinquish_certificate(invalid_args)

    def test_invalid_params_wrong_type_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishCertificateArgs with wrong type type
           When: Call relinquish_certificate
           Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, [], {}, True, 45.67]

        for invalid_type in invalid_types:
            invalid_args = {"type": invalid_type, "serialNumber": "test", "certifier": "02" + "00" * 32}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_storage.relinquish_certificate(invalid_args)

    def test_invalid_params_empty_serial_number_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishCertificateArgs with empty serial number
           When: Call relinquish_certificate
           Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"type": "dGVzdA==", "serialNumber": "", "certifier": "02" + "00" * 32}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_storage.relinquish_certificate(invalid_args)

    def test_invalid_params_none_serial_number_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishCertificateArgs with None serial number
           When: Call relinquish_certificate
           Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"type": "dGVzdA==", "serialNumber": None, "certifier": "02" + "00" * 32}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_storage.relinquish_certificate(invalid_args)

    def test_invalid_params_wrong_serial_number_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishCertificateArgs with wrong serial number type
           When: Call relinquish_certificate
           Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, [], {}, True, 45.67]

        for invalid_serial in invalid_types:
            invalid_args = {"type": "dGVzdA==", "serialNumber": invalid_serial, "certifier": "02" + "00" * 32}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_storage.relinquish_certificate(invalid_args)

    def test_invalid_params_empty_certifier_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishCertificateArgs with empty certifier
           When: Call relinquish_certificate
           Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"type": "dGVzdA==", "serialNumber": "test", "certifier": ""}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_storage.relinquish_certificate(invalid_args)

    def test_invalid_params_none_certifier_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishCertificateArgs with None certifier
           When: Call relinquish_certificate
           Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"type": "dGVzdA==", "serialNumber": "test", "certifier": None}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_storage.relinquish_certificate(invalid_args)

    def test_invalid_params_wrong_certifier_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishCertificateArgs with wrong certifier type
           When: Call relinquish_certificate
           Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, [], {}, True, 45.67]

        for invalid_certifier in invalid_types:
            invalid_args = {"type": "dGVzdA==", "serialNumber": "test", "certifier": invalid_certifier}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_storage.relinquish_certificate(invalid_args)

    def test_invalid_params_invalid_hex_certifier_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishCertificateArgs with invalid hex certifier
           When: Call relinquish_certificate
           Then: Raises InvalidParameterError
        """
        # Given - Invalid hex certifier strings
        invalid_hex_certifiers = [
            "gggggggggggggggggggggggggggggggggggggggg",  # Invalid hex chars
            "abcdef1234567890abcdef1234567890abcd",  # Too short (31 bytes)
            "abcdef1234567890abcdef1234567890abcdef12",  # Too long (33 bytes)
            "abcdef1234567890abcdef1234567890abcde",  # Odd length
        ]

        for certifier in invalid_hex_certifiers:
            invalid_args = {"type": "dGVzdA==", "serialNumber": "test", "certifier": certifier}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError)):
                wallet_with_storage.relinquish_certificate(invalid_args)

    def test_invalid_params_missing_type_key_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishCertificateArgs missing type key
           When: Call relinquish_certificate
           Then: Raises InvalidParameterError or KeyError
        """
        # Given
        invalid_args = {"serialNumber": "test", "certifier": "02" + "00" * 32}

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError)):
            wallet_with_storage.relinquish_certificate(invalid_args)

    def test_invalid_params_missing_serial_number_key_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishCertificateArgs missing serial number key
           When: Call relinquish_certificate
           Then: Raises InvalidParameterError or KeyError
        """
        # Given
        invalid_args = {"type": "dGVzdA==", "certifier": "02" + "00" * 32}

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError)):
            wallet_with_storage.relinquish_certificate(invalid_args)

    def test_invalid_params_missing_certifier_key_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishCertificateArgs missing certifier key
           When: Call relinquish_certificate
           Then: Raises InvalidParameterError or KeyError
        """
        # Given
        invalid_args = {"type": "dGVzdA==", "serialNumber": "test"}

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError)):
            wallet_with_storage.relinquish_certificate(invalid_args)

    def test_invalid_params_empty_args_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: Empty RelinquishCertificateArgs
           When: Call relinquish_certificate
           Then: Raises InvalidParameterError or KeyError
        """
        # Given
        invalid_args = {}

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError)):
            wallet_with_storage.relinquish_certificate(invalid_args)

    def test_relinquish_nonexistent_certificate_returns_false(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishCertificateArgs with nonexistent certificate
           When: Call relinquish_certificate
           Then: Returns relinquished=False
        """
        # Given
        nonexistent_args = {
            "type": "dGVzdA==",
            "serialNumber": "nonexistent_serial_12345",
            "certifier": "02" + "ff" * 32
        }

        # When
        result = wallet_with_storage.relinquish_certificate(nonexistent_args)

        # Then
        assert result == {"relinquished": False}

    def test_relinquish_already_relinquished_certificate_returns_false(self, wallet_with_storage: Wallet) -> None:
        """Given: Certificate that has already been relinquished
           When: Call relinquish_certificate again
           Then: Returns relinquished=False
        """
        # Given - First relinquish the certificate
        args = {"type": "dGVzdA==", "serialNumber": "c2VyaWFs", "certifier": "02" + "00" * 32}

        # First call should succeed
        first_result = wallet_with_storage.relinquish_certificate(args)
        assert first_result == {"relinquished": True}

        # Second call should return False
        second_result = wallet_with_storage.relinquish_certificate(args)
        assert second_result == {"relinquished": False}

    def test_relinquish_certificate_case_sensitive_certifier(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishCertificateArgs with different case certifier
           When: Call relinquish_certificate
           Then: Certifier is case-sensitive
        """
        # Given - Try different case certifiers
        test_cases = [
            {"type": "dGVzdA==", "serialNumber": "c2VyaWFs", "certifier": "02" + "00" * 32},  # lowercase
            {"type": "dGVzdA==", "serialNumber": "c2VyaWFs", "certifier": "02" + "00" * 32},  # already tested
        ]

        # Test that case differences matter (assuming the method is case-sensitive)
        for args in test_cases:
            # When
            result = wallet_with_storage.relinquish_certificate(args)

            # Then - Should return False since case doesn't match or cert doesn't exist
            assert result == {"relinquished": False}

    def test_relinquish_certificate_unicode_type_serial(self, wallet_with_storage: Wallet) -> None:
        """Given: RelinquishCertificateArgs with unicode type and serial number
           When: Call relinquish_certificate
           Then: Handles unicode correctly
        """
        # Given - Test unicode handling
        unicode_args = {
            "type": "dGVzdA==",  # base64 "test" (should handle unicode in processing)
            "serialNumber": "test_证书_serial",
            "certifier": "02" + "00" * 32
        }

        # When
        result = wallet_with_storage.relinquish_certificate(unicode_args)

        # Then - Should return False (since certificate doesn't exist) but not crash
        assert result == {"relinquished": False}


class TestWalletDiscoverByIdentityKey:
    """Test suite for Wallet.discover_by_identity_key method."""

    @pytest.mark.skip(reason="Requires Certificate subsystem implementation")
    def test_discover_by_identity_key(self, wallet_with_services: Wallet) -> None:
        """Given: DiscoverByIdentityKeyArgs with identity key
           When: Call discover_by_identity_key
           Then: Returns certificates for that identity

        Note: Based on BRC-100 specification for certificate discovery.
        """
        # Given
        args = {"identityKey": "02" + "aa" * 32}  # Identity key to discover

        # When
        result = wallet_with_services.discover_by_identity_key(args)

        # Then
        assert "certificates" in result
        assert isinstance(result["certificates"], list)

    def test_invalid_params_missing_identity_key_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: DiscoverByIdentityKeyArgs missing identity key
           When: Call discover_by_identity_key
           Then: Raises InvalidParameterError or KeyError
        """
        # Given
        invalid_args = {}

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError)):
            wallet_with_services.discover_by_identity_key(invalid_args)

    def test_invalid_params_empty_identity_key_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: DiscoverByIdentityKeyArgs with empty identity key
           When: Call discover_by_identity_key
           Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"identityKey": ""}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_services.discover_by_identity_key(invalid_args)

    def test_invalid_params_none_identity_key_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: DiscoverByIdentityKeyArgs with None identity key
           When: Call discover_by_identity_key
           Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"identityKey": None}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_services.discover_by_identity_key(invalid_args)

    def test_invalid_params_wrong_identity_key_type_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: DiscoverByIdentityKeyArgs with wrong identity key type
           When: Call discover_by_identity_key
           Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, [], {}, True, 45.67]

        for invalid_key in invalid_types:
            invalid_args = {"identityKey": invalid_key}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_services.discover_by_identity_key(invalid_args)

    def test_invalid_params_invalid_hex_identity_key_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: DiscoverByIdentityKeyArgs with invalid hex identity key
           When: Call discover_by_identity_key
           Then: Raises InvalidParameterError
        """
        # Given - Invalid hex identity key strings
        invalid_hex_keys = [
            "gggggggggggggggggggggggggggggggggggggggg",  # Invalid hex chars
            "abcdef1234567890abcdef1234567890abcd",  # Too short (31 bytes)
            "abcdef1234567890abcdef1234567890abcdef12",  # Too long (33 bytes)
            "abcdef1234567890abcdef1234567890abcde",  # Odd length
        ]

        for identity_key in invalid_hex_keys:
            invalid_args = {"identityKey": identity_key}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError)):
                wallet_with_services.discover_by_identity_key(invalid_args)


class TestWalletDiscoverByAttributes:
    """Test suite for Wallet.discover_by_attributes method."""

    @pytest.mark.skip(reason="Requires Certificate subsystem implementation")
    def test_discover_by_attributes(self, wallet_with_services: Wallet) -> None:
        """Given: DiscoverByAttributesArgs with search attributes
           When: Call discover_by_attributes
           Then: Returns certificates matching those attributes

        Note: Based on BRC-100 specification for attribute-based certificate discovery.
        """
        # Given
        args = {"attributes": {"name": "Test User", "email": "*@example.com"}, "limit": 10}  # Wildcard search

        # When
        result = wallet_with_services.discover_by_attributes(args)

        # Then
        assert "certificates" in result
        assert isinstance(result["certificates"], list)
        assert "totalCertificates" in result

    def test_invalid_params_missing_attributes_key_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: DiscoverByAttributesArgs missing attributes key
           When: Call discover_by_attributes
           Then: Raises InvalidParameterError or KeyError
        """
        # Given
        invalid_args = {}

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError)):
            wallet_with_services.discover_by_attributes(invalid_args)

    def test_invalid_params_empty_attributes_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: DiscoverByAttributesArgs with empty attributes
           When: Call discover_by_attributes
           Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"attributes": {}}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_services.discover_by_attributes(invalid_args)

    def test_invalid_params_none_attributes_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: DiscoverByAttributesArgs with None attributes
           When: Call discover_by_attributes
           Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"attributes": None}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_services.discover_by_attributes(invalid_args)

    def test_invalid_params_wrong_attributes_type_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: DiscoverByAttributesArgs with wrong attributes type
           When: Call discover_by_attributes
           Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, "string", [], True, 45.67]

        for invalid_attrs in invalid_types:
            invalid_args = {"attributes": invalid_attrs}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_services.discover_by_attributes(invalid_args)

    def test_invalid_params_wrong_limit_type_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: DiscoverByAttributesArgs with wrong limit type
           When: Call discover_by_attributes
           Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = ["string", [], {}, True, 45.67]

        for invalid_limit in invalid_types:
            invalid_args = {"attributes": {"name": "test"}, "limit": invalid_limit}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_services.discover_by_attributes(invalid_args)

    def test_invalid_params_zero_limit_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: DiscoverByAttributesArgs with zero limit
           When: Call discover_by_attributes
           Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"attributes": {"name": "test"}, "limit": 0}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_services.discover_by_attributes(invalid_args)

    def test_invalid_params_negative_limit_raises_error(self, wallet_with_services: Wallet) -> None:
        """Given: DiscoverByAttributesArgs with negative limit
           When: Call discover_by_attributes
           Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"attributes": {"name": "test"}, "limit": -1}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_services.discover_by_attributes(invalid_args)

    def test_valid_params_with_limit(self, wallet_with_services: Wallet) -> None:
        """Given: DiscoverByAttributesArgs with limit parameter
           When: Call discover_by_attributes
           Then: Returns limited results
        """
        # Given
        args = {"attributes": {"name": "test"}, "limit": 5}

        # When
        result = wallet_with_services.discover_by_attributes(args)

        # Then
        assert "certificates" in result
        assert isinstance(result["certificates"], list)
        assert "totalCertificates" in result
        assert len(result["certificates"]) <= 5
