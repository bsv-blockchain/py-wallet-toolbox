"""Unit tests for Wallet HMAC and signature methods.

These methods handle HMAC creation/verification and digital signatures.

Reference: wallet-toolbox/src/Wallet.ts
"""

import pytest

from bsv_wallet_toolbox import Wallet


class TestWalletCreateHmac:
    """Test suite for Wallet.create_hmac method."""

    @pytest.mark.skip(reason="Waiting for create_hmac implementation")
    def test_create_hmac(self, wallet: Wallet) -> None:
        """Given: CreateHmacArgs with data and protocol/key
           When: Call create_hmac
           Then: Returns HMAC of the data

        Note: Based on BRC-100 specification for HMAC creation.
        """
        # Given
        args = {"data": b"Test data for HMAC", "protocolID": [0, "test protocol"], "keyID": "hmac_key_1"}

        # When
        result = wallet.create_hmac(args)

        # Then
        assert "hmac" in result
        assert isinstance(result["hmac"], bytes)
        assert len(result["hmac"]) == 32  # HMAC-SHA256 produces 32 bytes


class TestWalletVerifyHmac:
    """Test suite for Wallet.verify_hmac method."""

    @pytest.mark.skip(reason="Waiting for verify_hmac implementation")
    def test_verify_hmac_valid(self, wallet: Wallet) -> None:
        """Given: VerifyHmacArgs with data, HMAC, and protocol/key
           When: Call verify_hmac with correct HMAC
           Then: Returns valid=True

        Note: Based on BRC-100 specification for HMAC verification.
        """
        # Given - First create an HMAC
        create_args = {"data": b"Test data for HMAC", "protocolID": [0, "test protocol"], "keyID": "hmac_key_1"}
        create_result = wallet.create_hmac(create_args)

        verify_args = {
            "data": b"Test data for HMAC",
            "hmac": create_result["hmac"],
            "protocolID": [0, "test protocol"],
            "keyID": "hmac_key_1",
        }

        # When
        result = wallet.verify_hmac(verify_args)

        # Then
        assert "valid" in result
        assert result["valid"] is True

    @pytest.mark.skip(reason="Waiting for verify_hmac implementation")
    def test_verify_hmac_invalid(self, wallet: Wallet) -> None:
        """Given: VerifyHmacArgs with incorrect HMAC
           When: Call verify_hmac
           Then: Returns valid=False

        Note: Based on BRC-100 specification for HMAC verification.
        """
        # Given
        verify_args = {
            "data": b"Test data for HMAC",
            "hmac": b"incorrect_hmac_value_32bytes!!",  # Wrong HMAC
            "protocolID": [0, "test protocol"],
            "keyID": "hmac_key_1",
        }

        # When
        result = wallet.verify_hmac(verify_args)

        # Then
        assert "valid" in result
        assert result["valid"] is False


class TestWalletCreateSignature:
    """Test suite for Wallet.create_signature method."""

    @pytest.mark.skip(reason="Waiting for create_signature implementation")
    def test_create_signature(self, wallet: Wallet) -> None:
        """Given: CreateSignatureArgs with data and protocol/key
           When: Call create_signature
           Then: Returns digital signature of the data

        Note: Based on BRC-100 specification for signature creation.
        """
        # Given
        args = {"data": b"Data to sign", "protocolID": [0, "test protocol"], "keyID": "signing_key_1"}

        # When
        result = wallet.create_signature(args)

        # Then
        assert "signature" in result
        assert isinstance(result["signature"], bytes)
        assert len(result["signature"]) >= 70  # DER signatures are typically 70-72 bytes


class TestWalletVerifySignature:
    """Test suite for Wallet.verify_signature method."""

    @pytest.mark.skip(reason="Waiting for verify_signature implementation")
    def test_verify_signature_valid(self, wallet: Wallet) -> None:
        """Given: VerifySignatureArgs with data, signature, and public key
           When: Call verify_signature with correct signature
           Then: Returns valid=True

        Note: Based on BRC-100 specification for signature verification.
        """
        # Given - First create a signature
        create_args = {"data": b"Data to sign", "protocolID": [0, "test protocol"], "keyID": "signing_key_1"}
        create_result = wallet.create_signature(create_args)

        # Get public key for verification
        pubkey_result = wallet.get_public_key({"protocolID": [0, "test protocol"], "keyID": "signing_key_1"})

        verify_args = {
            "data": b"Data to sign",
            "signature": create_result["signature"],
            "publicKey": pubkey_result["publicKey"],
        }

        # When
        result = wallet.verify_signature(verify_args)

        # Then
        assert "valid" in result
        assert result["valid"] is True

    @pytest.mark.skip(reason="Waiting for verify_signature implementation")
    def test_verify_signature_invalid(self, wallet: Wallet) -> None:
        """Given: VerifySignatureArgs with incorrect signature
           When: Call verify_signature
           Then: Returns valid=False

        Note: Based on BRC-100 specification for signature verification.
        """
        # Given
        verify_args = {
            "data": b"Data to sign",
            "signature": b"invalid_signature_bytes" + b"\x00" * 50,  # Wrong signature
            "publicKey": "02" + "00" * 32,  # Some public key
        }

        # When
        result = wallet.verify_signature(verify_args)

        # Then
        assert "valid" in result
        assert result["valid"] is False
