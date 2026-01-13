"""Unit tests for BRC29 address functionality.

Ported from Go implementation to ensure compatibility.

Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
"""

import pytest

from bsv_wallet_toolbox.brc29 import KeyID, address_for_counterparty, address_for_self

# Test data (matches Go implementation fixtures from go-wallet-toolbox/pkg/brc29/fixtures_test.go)
SENDER_PUBLIC_KEY_HEX = "0320bbfb879bbd6761ecd2962badbb41ba9d60ca88327d78b07ae7141af6b6c810"
SENDER_PRIVATE_KEY_HEX = "143ab18a84d3b25e1a13cefa90038411e5d2014590a2a4a57263d1593c8dee1c"
SENDER_WIF_STRING = "Kwu2vS6fqkd5WnRgB9VXd4vYpL9mwkXePZWtG9Nr5s6JmfHcLsQr"
RECIPIENT_PUBLIC_KEY_HEX = "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
RECIPIENT_PRIVATE_KEY_HEX = "0000000000000000000000000000000000000000000000000000000000000001"
KEY_ID = KeyID(derivation_prefix="Pr==", derivation_suffix="Su==")
# Updated to match Go-SDK test vectors (go-wallet-toolbox/pkg/brc29/fixtures_test.go)
EXPECTED_ADDRESS = "19bxE1pRYYtjZeQm7P8e2Ws5zMkm8NNuxx"
EXPECTED_TESTNET_ADDRESS = "mp7uX4uQMaKzLktNpx71rS5QrMMTzDP12u"
INVALID_KEY_HEX = "invalid"


class TestBRC29AddressByRecipientCreation:
    """Test suite for BRC29 address creation by recipient.

    Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
               TestBRC29AddressByRecipientCreation
    """

    def test_return_valid_address_with_hex_string_as_sender_public_key_source(self) -> None:
        """Given: Sender public key as hex string, key ID, recipient private key as hex
           When: Call address_for_self
           Then: Returns valid BRC29 address

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientCreation
                   t.Run("return valid address with hex string as sender public key source")
        """
        # Given / When
        address = address_for_self(
            sender_public_key=SENDER_PUBLIC_KEY_HEX, key_id=KEY_ID, recipient_private_key=RECIPIENT_PRIVATE_KEY_HEX
        )

        # Then
        assert address is not None
        assert address["addressString"] == EXPECTED_ADDRESS

    def test_return_valid_address_with_ec_publickey_as_sender_public_key_source(self) -> None:
        """Given: Sender public key as ec.PublicKey object, key ID, recipient private key
           When: Call address_for_self
           Then: Returns valid BRC29 address

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientCreation
                   t.Run("return valid address with ec.PublicKey as sender public key source")
        """
        # Given
        from bsv.keys import PublicKey

        pub = PublicKey(SENDER_PUBLIC_KEY_HEX)

        # When
        address = address_for_self(
            sender_public_key=pub, key_id=KEY_ID, recipient_private_key=RECIPIENT_PRIVATE_KEY_HEX
        )

        # Then
        assert address is not None
        assert address["addressString"] == EXPECTED_ADDRESS

    def test_return_valid_address_with_sender_key_deriver_as_sender_public_key_source(self) -> None:
        """Given: Sender key deriver, key ID, recipient private key
           When: Call address_for_self
           Then: Returns valid BRC29 address

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientCreation
                   t.Run("return valid address with sender key deriver as sender public key source")
        """
        # Given
        from bsv.keys import PrivateKey
        from bsv.wallet import KeyDeriver

        priv = PrivateKey.from_hex(SENDER_PRIVATE_KEY_HEX)
        key_deriver = KeyDeriver(priv)

        # When
        address = address_for_self(
            sender_public_key=key_deriver, key_id=KEY_ID, recipient_private_key=RECIPIENT_PRIVATE_KEY_HEX
        )

        # Then
        assert address is not None
        assert address["addressString"] == EXPECTED_ADDRESS

    def test_return_valid_address_with_ec_privatekey_as_recipient_private_key_source(self) -> None:
        """Given: Sender public key, key ID, recipient private key as ec.PrivateKey object
           When: Call address_for_self
           Then: Returns valid BRC29 address

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientCreation
                   t.Run("return valid address with ec.PrivateKey as recipient private key source")
        """
        # Given
        from bsv.keys import PrivateKey

        priv = PrivateKey.from_hex(RECIPIENT_PRIVATE_KEY_HEX)

        # When
        address = address_for_self(sender_public_key=SENDER_PUBLIC_KEY_HEX, key_id=KEY_ID, recipient_private_key=priv)

        # Then
        assert address is not None
        assert address["addressString"] == EXPECTED_ADDRESS

    def test_return_testnet_address_created_with_brc29_by_recipient(self) -> None:
        """Given: Sender public key, key ID, recipient private key, testnet option
           When: Call address_for_self with testnet=True
           Then: Returns valid BRC29 testnet address

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientCreation
                   t.Run("return testnet address created with brc29 by recipient")
        """
        # Given / When
        address = address_for_self(
            sender_public_key=SENDER_PUBLIC_KEY_HEX,
            key_id=KEY_ID,
            recipient_private_key=RECIPIENT_PRIVATE_KEY_HEX,
            testnet=True,
        )

        # Then
        assert address is not None
        assert address["addressString"] == EXPECTED_TESTNET_ADDRESS


class TestBRC29AddressByRecipientErrors:
    """Test suite for BRC29 address creation errors (recipient side).

    Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
               TestBRC29AddressByRecipientErrors
    """

    def test_return_error_when_sender_key_is_empty(self) -> None:
        """Given: Empty sender key
           When: Call address_for_self
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientErrors
                   errorTestCases "return error when sender key is empty"
        """
        # Given / When / Then
        with pytest.raises(Exception):
            address_for_self(sender_public_key="", key_id=KEY_ID, recipient_private_key=INVALID_KEY_HEX)

    def test_return_error_when_sender_key_parsing_fails(self) -> None:
        """Given: Invalid sender key
           When: Call address_for_self
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientErrors
                   errorTestCases "return error when sender key parsing fails"
        """
        # Given / When / Then
        with pytest.raises(Exception):
            address_for_self(
                sender_public_key=INVALID_KEY_HEX, key_id=KEY_ID, recipient_private_key=RECIPIENT_PRIVATE_KEY_HEX
            )

    def test_return_error_when_keyid_is_invalid(self) -> None:
        """Given: Invalid key ID
           When: Call address_for_self
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientErrors
                   errorTestCases "return error when KeyID is invalid"
        """
        # Given / When / Then
        with pytest.raises(Exception):
            address_for_self(
                sender_public_key=SENDER_PUBLIC_KEY_HEX,
                key_id=KeyID(derivation_prefix="", derivation_suffix=""),
                recipient_private_key=RECIPIENT_PRIVATE_KEY_HEX,
            )

    def test_return_error_when_recipient_key_is_empty(self) -> None:
        """Given: Empty recipient key
           When: Call address_for_self
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientErrors
                   errorTestCases "return error when recipient key is empty"
        """
        # Given / When / Then
        with pytest.raises(Exception):
            address_for_self(sender_public_key=SENDER_PUBLIC_KEY_HEX, key_id=KEY_ID, recipient_private_key="")

    def test_return_error_when_recipient_key_parsing_fails(self) -> None:
        """Given: Invalid recipient key
           When: Call address_for_self
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientErrors
                   errorTestCases "return error when recipient key parsing fails"
        """
        # Given / When / Then
        with pytest.raises(Exception):
            address_for_self(
                sender_public_key=SENDER_PUBLIC_KEY_HEX, key_id=KEY_ID, recipient_private_key=INVALID_KEY_HEX
            )

    def test_return_error_when_nil_is_passed_as_sender_public_key_deriver(self) -> None:
        """Given: None as sender public key deriver
           When: Call address_for_self
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientErrors
                   t.Run("return error when nil is passed as sender public key deriver")
        """
        # Given / When / Then
        with pytest.raises(Exception):
            address_for_self(
                sender_public_key=None, key_id=KEY_ID, recipient_private_key=RECIPIENT_PRIVATE_KEY_HEX  # KeyDeriver
            )

    def test_return_error_when_nil_is_passed_as_sender_public_key(self) -> None:
        """Given: None as sender public key
           When: Call address_for_self
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientErrors
                   t.Run("return error when nil is passed as sender public key")
        """
        # Given / When / Then
        with pytest.raises(Exception):
            address_for_self(
                sender_public_key=None, key_id=KEY_ID, recipient_private_key=RECIPIENT_PRIVATE_KEY_HEX  # PublicKey
            )

    def test_return_error_when_nil_is_passed_as_recipient_private_key_deriver(self) -> None:
        """Given: None as recipient private key deriver
           When: Call address_for_self
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientErrors
                   t.Run("return error when nil is passed as recipient private key deriver")
        """
        # Given / When / Then
        with pytest.raises(Exception):
            address_for_self(
                sender_public_key=SENDER_PUBLIC_KEY_HEX, key_id=KEY_ID, recipient_private_key=None  # KeyDeriver
            )

    def test_return_error_when_nil_is_passed_as_recipient_private_key(self) -> None:
        """Given: None as recipient private key
           When: Call address_for_self
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientErrors
                   t.Run("return error when nil is passed as recipient private key")
        """
        # Given / When / Then
        with pytest.raises(Exception):
            address_for_self(
                sender_public_key=SENDER_PUBLIC_KEY_HEX, key_id=KEY_ID, recipient_private_key=None  # PrivateKey
            )


class TestBRC29AddressCreation:
    """Test suite for BRC29 address creation (counterparty).

    Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
               TestBRC29AddressCreation
    """

    def test_return_valid_address_created_with_brc28_with_hex_string_as_sender_private_key_source(self) -> None:
        """Given: Sender private key as hex string, key ID, recipient public key
           When: Call address_for_counterparty
           Then: Returns valid BRC29 address

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressCreation
                   t.Run("return valid address created with brc28 with hex string as sender private key source")
        """
        # Given / When
        address = address_for_counterparty(
            sender_private_key=SENDER_PRIVATE_KEY_HEX, key_id=KEY_ID, recipient_public_key=RECIPIENT_PUBLIC_KEY_HEX
        )

        # Then
        assert address is not None
        assert address["addressString"] == EXPECTED_ADDRESS

    def test_return_valid_address_created_with_brc28_with_wif_as_sender_private_key_source(self) -> None:
        """Given: Sender private key as WIF string, key ID, recipient public key
           When: Call address_for_counterparty
           Then: Returns valid BRC29 address

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressCreation
                   t.Run("return valid address created with brc28 with wif as sender private key source")
        """
        # Given / When
        address = address_for_counterparty(
            sender_private_key=SENDER_WIF_STRING, key_id=KEY_ID, recipient_public_key=RECIPIENT_PUBLIC_KEY_HEX
        )

        # Then
        assert address is not None
        assert address["addressString"] == EXPECTED_ADDRESS

    def test_return_valid_address_created_with_brc28_with_ec_privatekey_as_sender_private_key_source(self) -> None:
        """Given: Sender private key as ec.PrivateKey object, key ID, recipient public key
           When: Call address_for_counterparty
           Then: Returns valid BRC29 address

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressCreation
                   t.Run("return valid address created with brc28 with ec.PrivateKey as sender private key source")
        """
        # Given
        from bsv.keys import PrivateKey

        priv = PrivateKey.from_hex(SENDER_PRIVATE_KEY_HEX)

        # When
        address = address_for_counterparty(
            sender_private_key=priv, key_id=KEY_ID, recipient_public_key=RECIPIENT_PUBLIC_KEY_HEX
        )

        # Then
        assert address is not None
        assert address["addressString"] == EXPECTED_ADDRESS

    def test_return_valid_address_created_with_brc28_with_key_deriver_as_sender_private_key_source(self) -> None:
        """Given: Sender key deriver, key ID, recipient public key
           When: Call address_for_counterparty
           Then: Returns valid BRC29 address

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressCreation
                   t.Run("return valid address created with brc28 with key deriver as sender private key source")
        """
        # Given
        from bsv.keys import PrivateKey
        from bsv.wallet import KeyDeriver

        priv = PrivateKey.from_hex(SENDER_PRIVATE_KEY_HEX)
        key_deriver = KeyDeriver(priv)

        # When
        address = address_for_counterparty(
            sender_private_key=key_deriver, key_id=KEY_ID, recipient_public_key=RECIPIENT_PUBLIC_KEY_HEX
        )

        # Then
        assert address is not None
        assert address["addressString"] == EXPECTED_ADDRESS

    def test_return_valid_address_created_with_brc28_with_ec_publickey_as_receiver_public_key_source(self) -> None:
        """Given: Sender private key, key ID, recipient public key as ec.PublicKey object
           When: Call address_for_counterparty
           Then: Returns valid BRC29 address

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressCreation
                   t.Run("return valid address created with brc28 with ec.PublicKey as receiver public key source")
        """
        # Given
        from bsv.keys import PublicKey

        pub = PublicKey(RECIPIENT_PUBLIC_KEY_HEX)

        # When
        address = address_for_counterparty(
            sender_private_key=SENDER_PRIVATE_KEY_HEX, key_id=KEY_ID, recipient_public_key=pub
        )

        # Then
        assert address is not None
        assert address["addressString"] == EXPECTED_ADDRESS

    def test_return_testnet_address_created_with_brc29(self) -> None:
        """Given: Sender private key, key ID, recipient public key, testnet option
           When: Call address_for_counterparty with testnet=True
           Then: Returns valid BRC29 testnet address

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressCreation
                   t.Run("return testnet address created with brc29")
        """
        # Given
        from bsv.keys import PublicKey

        pub = PublicKey(RECIPIENT_PUBLIC_KEY_HEX)

        # When
        address = address_for_counterparty(
            sender_private_key=SENDER_PRIVATE_KEY_HEX, key_id=KEY_ID, recipient_public_key=pub, testnet=True
        )

        # Then
        assert address is not None
        assert address["addressString"] == EXPECTED_TESTNET_ADDRESS


class TestBRC29AddressErrors:
    """Test suite for BRC29 address creation errors (counterparty side).

    Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
               TestBRC29AddressErrors
    """

    def test_return_error_when_sender_key_is_empty(self) -> None:
        """Given: Empty sender key
           When: Call address_for_counterparty
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressErrors
                   errorTestCases "return error when sender key is empty"
        """
        # Given / When / Then
        with pytest.raises(Exception):
            address_for_counterparty(sender_private_key="", key_id=KEY_ID, recipient_public_key=INVALID_KEY_HEX)

    def test_return_error_when_sender_key_parsing_fails(self) -> None:
        """Given: Invalid sender key
           When: Call address_for_counterparty
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressErrors
                   errorTestCases "return error when sender key parsing fails"
        """
        # Given / When / Then
        with pytest.raises(Exception):
            address_for_counterparty(
                sender_private_key=INVALID_KEY_HEX, key_id=KEY_ID, recipient_public_key=RECIPIENT_PUBLIC_KEY_HEX
            )

    def test_return_error_when_keyid_is_invalid(self) -> None:
        """Given: Invalid key ID
           When: Call address_for_counterparty
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressErrors
                   errorTestCases "return error when KeyID is invalid"
        """
        # Given / When / Then
        with pytest.raises(Exception):
            address_for_counterparty(
                sender_private_key=SENDER_PRIVATE_KEY_HEX,
                key_id=KeyID(derivation_prefix="", derivation_suffix=""),
                recipient_public_key=RECIPIENT_PUBLIC_KEY_HEX,
            )

    def test_return_error_when_recipient_key_is_empty(self) -> None:
        """Given: Empty recipient key
           When: Call address_for_counterparty
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressErrors
                   errorTestCases "return error when recipient key is empty"
        """
        # Given / When / Then
        with pytest.raises(Exception):
            address_for_counterparty(sender_private_key=SENDER_PRIVATE_KEY_HEX, key_id=KEY_ID, recipient_public_key="")

    def test_return_error_when_recipient_key_parsing_fails(self) -> None:
        """Given: Invalid recipient key
           When: Call address_for_counterparty
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressErrors
                   errorTestCases "return error when recipient key parsing fails"
        """
        # Given / When / Then
        with pytest.raises(Exception):
            address_for_counterparty(
                sender_private_key=SENDER_PRIVATE_KEY_HEX, key_id=KEY_ID, recipient_public_key=INVALID_KEY_HEX
            )

    def test_return_error_when_nil_is_passed_as_sender_private_key_deriver(self) -> None:
        """Given: None as sender private key deriver
           When: Call address_for_counterparty
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressErrors
                   t.Run("return error when nil is passed as sender private key deriver")
        """
        # Given / When / Then
        with pytest.raises(Exception):
            address_for_counterparty(
                sender_private_key=None, key_id=KEY_ID, recipient_public_key=RECIPIENT_PUBLIC_KEY_HEX  # KeyDeriver
            )

    def test_return_error_when_nil_is_passed_as_sender_private_key(self) -> None:
        """Given: None as sender private key
           When: Call address_for_counterparty
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressErrors
                   t.Run("return error when nil is passed as sender private key")
        """
        # Given / When / Then
        with pytest.raises(Exception):
            address_for_counterparty(
                sender_private_key=None, key_id=KEY_ID, recipient_public_key=RECIPIENT_PUBLIC_KEY_HEX  # PrivateKey
            )

    def test_return_error_when_nil_is_passed_as_recipient_public_key_deriver(self) -> None:
        """Given: None as recipient public key deriver
           When: Call address_for_counterparty
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressErrors
                   t.Run("return error when nil is passed as recipient public key deriver")
        """
        # Given / When / Then
        with pytest.raises(Exception):
            address_for_counterparty(
                sender_private_key=SENDER_PRIVATE_KEY_HEX, key_id=KEY_ID, recipient_public_key=None  # KeyDeriver
            )

    def test_return_error_when_nil_is_passed_as_recipient_public_key(self) -> None:
        """Given: None as recipient public key
           When: Call address_for_counterparty
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressErrors
                   t.Run("return error when nil is passed as recipient public key")
        """
        # Given / When / Then
        with pytest.raises(Exception):
            address_for_counterparty(
                sender_private_key=SENDER_PRIVATE_KEY_HEX, key_id=KEY_ID, recipient_public_key=None  # PublicKey
            )
