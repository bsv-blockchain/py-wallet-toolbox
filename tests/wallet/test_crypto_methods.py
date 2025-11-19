"""Unit tests for Wallet cryptographic methods.

These methods handle key derivation, encryption, decryption, and linkage revelation.

References:
- wallet-toolbox/src/sdk/CertOpsWallet.ts
- wallet-toolbox/src/Wallet.ts
"""

from bsv_wallet_toolbox import Wallet


class TestWalletGetPublicKey:
    """Test suite for Wallet.get_public_key method."""

    def test_get_public_key_identity_key(self, wallet_with_storage: Wallet) -> None:
        """Given: GetPublicKeyArgs with identity key request
           When: Call get_public_key
           Then: Returns wallet's identity public key

        Note: Based on BRC-100 specification for getPublicKey method.
        """
        # Given
        args = {"identityKey": True}

        # When
        result = wallet_with_storage.get_public_key(args)

        # Then
        assert "publicKey" in result
        assert isinstance(result["publicKey"], str)
        assert len(result["publicKey"]) == 66  # Compressed public key hex

    def test_get_public_key_with_protocol_id(self, wallet_with_storage: Wallet) -> None:
        """Given: GetPublicKeyArgs with protocolID and keyID
           When: Call get_public_key
           Then: Returns derived public key for that protocol/key

        Note: Based on BRC-100 specification for protocol-specific key derivation.
        """
        # Given
        args = {"protocolID": [0, "test"], "keyID": "test_key_1"}

        # When
        result = wallet_with_storage.get_public_key(args)

        # Then
        assert "publicKey" in result
        assert isinstance(result["publicKey"], str)


class TestWalletEncrypt:
    """Test suite for Wallet.encrypt method."""

    def test_encrypt_with_counterparty(self, wallet_with_storage: Wallet) -> None:
        """Given: WalletEncryptArgs with plaintext and counterparty public key
           When: Call encrypt
           Then: Returns encrypted ciphertext

        Note: Based on BRC-100 specification for wallet encryption.
        """
        # Given
        args = {
            "plaintext": b"Hello, World!",
            "protocolID": [0, "test"],
            "keyID": "encryption_key_1",
            "counterparty": "025ad43a22ac38d0bc1f8bacaabb323b5d634703b7a774c4268f6a09e4ddf79097",  # Valid compressed pubkey from test vectors
        }

        # When
        result = wallet_with_storage.encrypt(args)

        # Then
        assert "ciphertext" in result
        assert isinstance(result["ciphertext"], list)
        assert all(isinstance(b, int) and 0 <= b <= 255 for b in result["ciphertext"])
        assert len(result["ciphertext"]) > len(args["plaintext"])  # Encrypted is longer


class TestWalletDecrypt:
    """Test suite for Wallet.decrypt method."""

    def test_decrypt_with_counterparty(self, wallet_with_storage: Wallet) -> None:
        """Given: WalletDecryptArgs with ciphertext and counterparty public key
           When: Call decrypt
           Then: Returns decrypted plaintext

        Note: Based on BRC-100 specification for wallet decryption.
        """
        # Given
        # First encrypt something
        encrypt_args = {
            "plaintext": b"Hello, World!",
            "protocolID": [0, "test"],
            "keyID": "encryption_key_1",
            "counterparty": "025ad43a22ac38d0bc1f8bacaabb323b5d634703b7a774c4268f6a09e4ddf79097",
        }
        encrypt_result = wallet_with_storage.encrypt(encrypt_args)

        decrypt_args = {
            "ciphertext": encrypt_result["ciphertext"],
            "protocolID": [0, "test"],
            "keyID": "encryption_key_1",
            "counterparty": "025ad43a22ac38d0bc1f8bacaabb323b5d634703b7a774c4268f6a09e4ddf79097",
        }

        # When
        result = wallet_with_storage.decrypt(decrypt_args)

        # Then
        assert "plaintext" in result
        assert result["plaintext"] == list(b"Hello, World!")  # Returned as list of ints


class TestWalletRevealCounterpartyKeyLinkage:
    """Test suite for Wallet.reveal_counterparty_key_linkage method."""

    def test_reveal_counterparty_key_linkage(self, wallet_with_storage: Wallet) -> None:
        """Given: RevealCounterpartyKeyLinkageArgs with counterparty and protocols
           When: Call reveal_counterparty_key_linkage
           Then: Returns linkage revelation for the counterparty

        Note: Based on BRC-100 specification for key linkage revelation.
        """
        # Given
        args = {
            "counterparty": "025ad43a22ac38d0bc1f8bacaabb323b5d634703b7a774c4268f6a09e4ddf79097",  # Valid counterparty public key
            "verifier": "03ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",  # Verifier public key (compressed)
        }

        # When
        result = wallet_with_storage.reveal_counterparty_key_linkage(args)

        # Then
        assert "revelation" in result
        assert isinstance(result["revelation"], dict)


class TestWalletRevealSpecificKeyLinkage:
    """Test suite for Wallet.reveal_specific_key_linkage method."""

    def test_reveal_specific_key_linkage(self, wallet_with_storage: Wallet) -> None:
        """Given: RevealSpecificKeyLinkageArgs with specific protocol and key
           When: Call reveal_specific_key_linkage
           Then: Returns linkage revelation for that specific key

        Note: Based on BRC-100 specification for specific key linkage revelation.
        """
        # Given
        args = {
            "counterparty": "025ad43a22ac38d0bc1f8bacaabb323b5d634703b7a774c4268f6a09e4ddf79097",
            "verifier": "03ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "protocolID": [0, "test"],
            "keyID": "test_key_1",
        }

        # When
        result = wallet_with_storage.reveal_specific_key_linkage(args)

        # Then
        assert "revelation" in result
        assert isinstance(result["revelation"], dict)
