"""Unit tests for BRC29 address functionality.

Ported from Go implementation to ensure compatibility.

Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go

Note: All tests are currently skipped as the BRC29 API is not yet implemented.
"""

import pytest


# Test data
SENDER_PUBLIC_KEY_HEX = "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
SENDER_PRIVATE_KEY_HEX = "0000000000000000000000000000000000000000000000000000000000000001"
SENDER_WIF_STRING = "KwDiBf89QgGbjEhKnhXJuH7LrciVrZi3qYjgd9M7rFU73sVHnoWn"
RECIPIENT_PUBLIC_KEY_HEX = "02c6047f9441ed7d6d3045406e95c07cd85c778e4b8cef3ca7abac09b95c709ee5"
RECIPIENT_PRIVATE_KEY_HEX = "0000000000000000000000000000000000000000000000000000000000000002"
KEY_ID = {"derivation_prefix": "test", "derivation_suffix": "123"}
EXPECTED_ADDRESS = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"  # Example address
EXPECTED_TESTNET_ADDRESS = "mrLC19Je2BuWQDkWSTriGYPyQJXKkkBmCx"  # Example testnet address
INVALID_KEY_HEX = "invalid"


class TestBRC29AddressByRecipientCreation:
    """Test suite for BRC29 address creation by recipient.
    
    Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
               TestBRC29AddressByRecipientCreation
    """
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_valid_address_with_hex_string_as_sender_public_key_source(self) -> None:
        """Given: Sender public key as hex string, key ID, recipient private key as hex
           When: Call address_for_self
           Then: Returns valid BRC29 address
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientCreation
                   t.Run("return valid address with hex string as sender public key source")
        """
        # Given / When
        # from bsv_wallet_toolbox.brc29 import address_for_self
        # address = address_for_self(
        #     sender_pub_key=SENDER_PUBLIC_KEY_HEX,
        #     key_id=KEY_ID,
        #     recipient_priv_key=RECIPIENT_PRIVATE_KEY_HEX
        # )
        
        # Then
        # assert address is not None
        # assert address["address_string"] == EXPECTED_ADDRESS
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_valid_address_with_ec_publickey_as_sender_public_key_source(self) -> None:
        """Given: Sender public key as ec.PublicKey object, key ID, recipient private key
           When: Call address_for_self
           Then: Returns valid BRC29 address
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientCreation
                   t.Run("return valid address with ec.PublicKey as sender public key source")
        """
        # Given
        # from bsv_wallet_toolbox.primitives.ec import PublicKey
        # pub = PublicKey.from_string(SENDER_PUBLIC_KEY_HEX)
        
        # When
        # from bsv_wallet_toolbox.brc29 import address_for_self
        # address = address_for_self(
        #     sender_pub_key=pub,
        #     key_id=KEY_ID,
        #     recipient_priv_key=RECIPIENT_PRIVATE_KEY_HEX
        # )
        
        # Then
        # assert address is not None
        # assert address["address_string"] == EXPECTED_ADDRESS
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_valid_address_with_sender_key_deriver_as_sender_public_key_source(self) -> None:
        """Given: Sender key deriver, key ID, recipient private key
           When: Call address_for_self
           Then: Returns valid BRC29 address
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientCreation
                   t.Run("return valid address with sender key deriver as sender public key source")
        """
        # Given
        # from bsv_wallet_toolbox.primitives.ec import PrivateKey
        # from bsv_wallet_toolbox.wallet import KeyDeriver
        # priv = PrivateKey.from_hex(SENDER_PRIVATE_KEY_HEX)
        # key_deriver = KeyDeriver(priv)
        
        # When
        # from bsv_wallet_toolbox.brc29 import address_for_self
        # address = address_for_self(
        #     sender_pub_key=key_deriver,
        #     key_id=KEY_ID,
        #     recipient_priv_key=RECIPIENT_PRIVATE_KEY_HEX
        # )
        
        # Then
        # assert address is not None
        # assert address["address_string"] == EXPECTED_ADDRESS
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_valid_address_with_ec_privatekey_as_recipient_private_key_source(self) -> None:
        """Given: Sender public key, key ID, recipient private key as ec.PrivateKey object
           When: Call address_for_self
           Then: Returns valid BRC29 address
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientCreation
                   t.Run("return valid address with ec.PrivateKey as recipient private key source")
        """
        # Given
        # from bsv_wallet_toolbox.primitives.ec import PrivateKey
        # priv = PrivateKey.from_hex(RECIPIENT_PRIVATE_KEY_HEX)
        
        # When
        # from bsv_wallet_toolbox.brc29 import address_for_self
        # address = address_for_self(
        #     sender_pub_key=SENDER_PUBLIC_KEY_HEX,
        #     key_id=KEY_ID,
        #     recipient_priv_key=priv
        # )
        
        # Then
        # assert address is not None
        # assert address["address_string"] == EXPECTED_ADDRESS
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_testnet_address_created_with_brc29_by_recipient(self) -> None:
        """Given: Sender public key, key ID, recipient private key, testnet option
           When: Call address_for_self with testnet=True
           Then: Returns valid BRC29 testnet address
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientCreation
                   t.Run("return testnet address created with brc29 by recipient")
        """
        # Given / When
        # from bsv_wallet_toolbox.brc29 import address_for_self
        # address = address_for_self(
        #     sender_pub_key=SENDER_PUBLIC_KEY_HEX,
        #     key_id=KEY_ID,
        #     recipient_priv_key=RECIPIENT_PRIVATE_KEY_HEX,
        #     testnet=True
        # )
        
        # Then
        # assert address is not None
        # assert address["address_string"] == EXPECTED_TESTNET_ADDRESS
        pass


class TestBRC29AddressByRecipientErrors:
    """Test suite for BRC29 address creation errors (recipient side).
    
    Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
               TestBRC29AddressByRecipientErrors
    """
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_error_when_sender_key_is_empty(self) -> None:
        """Given: Empty sender key
           When: Call address_for_self
           Then: Raises error
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientErrors
                   errorTestCases "return error when sender key is empty"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import address_for_self
        
        # When / Then
        # with pytest.raises(Exception):
        #     address_for_self(
        #         sender_pub_key="",
        #         key_id=KEY_ID,
        #         recipient_priv_key=INVALID_KEY_HEX
        #     )
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_error_when_sender_key_parsing_fails(self) -> None:
        """Given: Invalid sender key
           When: Call address_for_self
           Then: Raises error
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientErrors
                   errorTestCases "return error when sender key parsing fails"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import address_for_self
        
        # When / Then
        # with pytest.raises(Exception):
        #     address_for_self(
        #         sender_pub_key=INVALID_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_priv_key=RECIPIENT_PRIVATE_KEY_HEX
        #     )
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_error_when_keyid_is_invalid(self) -> None:
        """Given: Invalid key ID
           When: Call address_for_self
           Then: Raises error
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientErrors
                   errorTestCases "return error when KeyID is invalid"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import address_for_self
        
        # When / Then
        # with pytest.raises(Exception):
        #     address_for_self(
        #         sender_pub_key=SENDER_PUBLIC_KEY_HEX,
        #         key_id={"derivation_prefix": "", "derivation_suffix": ""},
        #         recipient_priv_key=RECIPIENT_PRIVATE_KEY_HEX
        #     )
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_error_when_recipient_key_is_empty(self) -> None:
        """Given: Empty recipient key
           When: Call address_for_self
           Then: Raises error
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientErrors
                   errorTestCases "return error when recipient key is empty"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import address_for_self
        
        # When / Then
        # with pytest.raises(Exception):
        #     address_for_self(
        #         sender_pub_key=SENDER_PUBLIC_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_priv_key=""
        #     )
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_error_when_recipient_key_parsing_fails(self) -> None:
        """Given: Invalid recipient key
           When: Call address_for_self
           Then: Raises error
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientErrors
                   errorTestCases "return error when recipient key parsing fails"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import address_for_self
        
        # When / Then
        # with pytest.raises(Exception):
        #     address_for_self(
        #         sender_pub_key=SENDER_PUBLIC_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_priv_key=INVALID_KEY_HEX
        #     )
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_error_when_nil_is_passed_as_sender_public_key_deriver(self) -> None:
        """Given: None as sender public key deriver
           When: Call address_for_self
           Then: Raises error
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientErrors
                   t.Run("return error when nil is passed as sender public key deriver")
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import address_for_self
        
        # When / Then
        # with pytest.raises(Exception):
        #     address_for_self(
        #         sender_pub_key=None,  # KeyDeriver
        #         key_id=KEY_ID,
        #         recipient_priv_key=RECIPIENT_PRIVATE_KEY_HEX
        #     )
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_error_when_nil_is_passed_as_sender_public_key(self) -> None:
        """Given: None as sender public key
           When: Call address_for_self
           Then: Raises error
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientErrors
                   t.Run("return error when nil is passed as sender public key")
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import address_for_self
        
        # When / Then
        # with pytest.raises(Exception):
        #     address_for_self(
        #         sender_pub_key=None,  # PublicKey
        #         key_id=KEY_ID,
        #         recipient_priv_key=RECIPIENT_PRIVATE_KEY_HEX
        #     )
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_error_when_nil_is_passed_as_recipient_private_key_deriver(self) -> None:
        """Given: None as recipient private key deriver
           When: Call address_for_self
           Then: Raises error
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientErrors
                   t.Run("return error when nil is passed as recipient private key deriver")
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import address_for_self
        
        # When / Then
        # with pytest.raises(Exception):
        #     address_for_self(
        #         sender_pub_key=SENDER_PUBLIC_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_priv_key=None  # KeyDeriver
        #     )
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_error_when_nil_is_passed_as_recipient_private_key(self) -> None:
        """Given: None as recipient private key
           When: Call address_for_self
           Then: Raises error
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressByRecipientErrors
                   t.Run("return error when nil is passed as recipient private key")
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import address_for_self
        
        # When / Then
        # with pytest.raises(Exception):
        #     address_for_self(
        #         sender_pub_key=SENDER_PUBLIC_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_priv_key=None  # PrivateKey
        #     )
        pass


class TestBRC29AddressCreation:
    """Test suite for BRC29 address creation (counterparty).
    
    Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
               TestBRC29AddressCreation
    """
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_valid_address_created_with_brc28_with_hex_string_as_sender_private_key_source(self) -> None:
        """Given: Sender private key as hex string, key ID, recipient public key
           When: Call address_for_counterparty
           Then: Returns valid BRC29 address
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressCreation
                   t.Run("return valid address created with brc28 with hex string as sender private key source")
        """
        # Given / When
        # from bsv_wallet_toolbox.brc29 import address_for_counterparty
        # address = address_for_counterparty(
        #     sender_priv_key=SENDER_PRIVATE_KEY_HEX,
        #     key_id=KEY_ID,
        #     recipient_pub_key=RECIPIENT_PUBLIC_KEY_HEX
        # )
        
        # Then
        # assert address is not None
        # assert address["address_string"] == EXPECTED_ADDRESS
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_valid_address_created_with_brc28_with_wif_as_sender_private_key_source(self) -> None:
        """Given: Sender private key as WIF string, key ID, recipient public key
           When: Call address_for_counterparty
           Then: Returns valid BRC29 address
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressCreation
                   t.Run("return valid address created with brc28 with wif as sender private key source")
        """
        # Given / When
        # from bsv_wallet_toolbox.brc29 import address_for_counterparty
        # address = address_for_counterparty(
        #     sender_priv_key=SENDER_WIF_STRING,
        #     key_id=KEY_ID,
        #     recipient_pub_key=RECIPIENT_PUBLIC_KEY_HEX
        # )
        
        # Then
        # assert address is not None
        # assert address["address_string"] == EXPECTED_ADDRESS
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_valid_address_created_with_brc28_with_ec_privatekey_as_sender_private_key_source(self) -> None:
        """Given: Sender private key as ec.PrivateKey object, key ID, recipient public key
           When: Call address_for_counterparty
           Then: Returns valid BRC29 address
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressCreation
                   t.Run("return valid address created with brc28 with ec.PrivateKey as sender private key source")
        """
        # Given
        # from bsv_wallet_toolbox.primitives.ec import PrivateKey
        # priv = PrivateKey.from_hex(SENDER_PRIVATE_KEY_HEX)
        
        # When
        # from bsv_wallet_toolbox.brc29 import address_for_counterparty
        # address = address_for_counterparty(
        #     sender_priv_key=priv,
        #     key_id=KEY_ID,
        #     recipient_pub_key=RECIPIENT_PUBLIC_KEY_HEX
        # )
        
        # Then
        # assert address is not None
        # assert address["address_string"] == EXPECTED_ADDRESS
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_valid_address_created_with_brc28_with_key_deriver_as_sender_private_key_source(self) -> None:
        """Given: Sender key deriver, key ID, recipient public key
           When: Call address_for_counterparty
           Then: Returns valid BRC29 address
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressCreation
                   t.Run("return valid address created with brc28 with key deriver as sender private key source")
        """
        # Given
        # from bsv_wallet_toolbox.primitives.ec import PrivateKey
        # from bsv_wallet_toolbox.wallet import KeyDeriver
        # priv = PrivateKey.from_hex(SENDER_PRIVATE_KEY_HEX)
        # key_deriver = KeyDeriver(priv)
        
        # When
        # from bsv_wallet_toolbox.brc29 import address_for_counterparty
        # address = address_for_counterparty(
        #     sender_priv_key=key_deriver,
        #     key_id=KEY_ID,
        #     recipient_pub_key=RECIPIENT_PUBLIC_KEY_HEX
        # )
        
        # Then
        # assert address is not None
        # assert address["address_string"] == EXPECTED_ADDRESS
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_valid_address_created_with_brc28_with_ec_publickey_as_receiver_public_key_source(self) -> None:
        """Given: Sender private key, key ID, recipient public key as ec.PublicKey object
           When: Call address_for_counterparty
           Then: Returns valid BRC29 address
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressCreation
                   t.Run("return valid address created with brc28 with ec.PublicKey as receiver public key source")
        """
        # Given
        # from bsv_wallet_toolbox.primitives.ec import PublicKey
        # pub = PublicKey.from_string(RECIPIENT_PUBLIC_KEY_HEX)
        
        # When
        # from bsv_wallet_toolbox.brc29 import address_for_counterparty
        # address = address_for_counterparty(
        #     sender_priv_key=SENDER_PRIVATE_KEY_HEX,
        #     key_id=KEY_ID,
        #     recipient_pub_key=pub
        # )
        
        # Then
        # assert address is not None
        # assert address["address_string"] == EXPECTED_ADDRESS
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_testnet_address_created_with_brc29(self) -> None:
        """Given: Sender private key, key ID, recipient public key, testnet option
           When: Call address_for_counterparty with testnet=True
           Then: Returns valid BRC29 testnet address
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressCreation
                   t.Run("return testnet address created with brc29")
        """
        # Given
        # from bsv_wallet_toolbox.primitives.ec import PublicKey
        # pub = PublicKey.from_string(RECIPIENT_PUBLIC_KEY_HEX)
        
        # When
        # from bsv_wallet_toolbox.brc29 import address_for_counterparty
        # address = address_for_counterparty(
        #     sender_priv_key=SENDER_PRIVATE_KEY_HEX,
        #     key_id=KEY_ID,
        #     recipient_pub_key=pub,
        #     testnet=True
        # )
        
        # Then
        # assert address is not None
        # assert address["address_string"] == EXPECTED_TESTNET_ADDRESS
        pass


class TestBRC29AddressErrors:
    """Test suite for BRC29 address creation errors (counterparty side).
    
    Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
               TestBRC29AddressErrors
    """
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_error_when_sender_key_is_empty(self) -> None:
        """Given: Empty sender key
           When: Call address_for_counterparty
           Then: Raises error
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressErrors
                   errorTestCases "return error when sender key is empty"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import address_for_counterparty
        
        # When / Then
        # with pytest.raises(Exception):
        #     address_for_counterparty(
        #         sender_priv_key="",
        #         key_id=KEY_ID,
        #         recipient_pub_key=INVALID_KEY_HEX
        #     )
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_error_when_sender_key_parsing_fails(self) -> None:
        """Given: Invalid sender key
           When: Call address_for_counterparty
           Then: Raises error
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressErrors
                   errorTestCases "return error when sender key parsing fails"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import address_for_counterparty
        
        # When / Then
        # with pytest.raises(Exception):
        #     address_for_counterparty(
        #         sender_priv_key=INVALID_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_pub_key=RECIPIENT_PUBLIC_KEY_HEX
        #     )
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_error_when_keyid_is_invalid(self) -> None:
        """Given: Invalid key ID
           When: Call address_for_counterparty
           Then: Raises error
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressErrors
                   errorTestCases "return error when KeyID is invalid"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import address_for_counterparty
        
        # When / Then
        # with pytest.raises(Exception):
        #     address_for_counterparty(
        #         sender_priv_key=SENDER_PRIVATE_KEY_HEX,
        #         key_id={"derivation_prefix": "", "derivation_suffix": ""},
        #         recipient_pub_key=RECIPIENT_PUBLIC_KEY_HEX
        #     )
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_error_when_recipient_key_is_empty(self) -> None:
        """Given: Empty recipient key
           When: Call address_for_counterparty
           Then: Raises error
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressErrors
                   errorTestCases "return error when recipient key is empty"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import address_for_counterparty
        
        # When / Then
        # with pytest.raises(Exception):
        #     address_for_counterparty(
        #         sender_priv_key=SENDER_PRIVATE_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_pub_key=""
        #     )
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_error_when_recipient_key_parsing_fails(self) -> None:
        """Given: Invalid recipient key
           When: Call address_for_counterparty
           Then: Raises error
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressErrors
                   errorTestCases "return error when recipient key parsing fails"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import address_for_counterparty
        
        # When / Then
        # with pytest.raises(Exception):
        #     address_for_counterparty(
        #         sender_priv_key=SENDER_PRIVATE_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_pub_key=INVALID_KEY_HEX
        #     )
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_error_when_nil_is_passed_as_sender_private_key_deriver(self) -> None:
        """Given: None as sender private key deriver
           When: Call address_for_counterparty
           Then: Raises error
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressErrors
                   t.Run("return error when nil is passed as sender private key deriver")
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import address_for_counterparty
        
        # When / Then
        # with pytest.raises(Exception):
        #     address_for_counterparty(
        #         sender_priv_key=None,  # KeyDeriver
        #         key_id=KEY_ID,
        #         recipient_pub_key=RECIPIENT_PUBLIC_KEY_HEX
        #     )
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_error_when_nil_is_passed_as_sender_private_key(self) -> None:
        """Given: None as sender private key
           When: Call address_for_counterparty
           Then: Raises error
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressErrors
                   t.Run("return error when nil is passed as sender private key")
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import address_for_counterparty
        
        # When / Then
        # with pytest.raises(Exception):
        #     address_for_counterparty(
        #         sender_priv_key=None,  # PrivateKey
        #         key_id=KEY_ID,
        #         recipient_pub_key=RECIPIENT_PUBLIC_KEY_HEX
        #     )
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_error_when_nil_is_passed_as_recipient_public_key_deriver(self) -> None:
        """Given: None as recipient public key deriver
           When: Call address_for_counterparty
           Then: Raises error
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressErrors
                   t.Run("return error when nil is passed as recipient public key deriver")
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import address_for_counterparty
        
        # When / Then
        # with pytest.raises(Exception):
        #     address_for_counterparty(
        #         sender_priv_key=SENDER_PRIVATE_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_pub_key=None  # KeyDeriver
        #     )
        pass
    
    @pytest.mark.skip(reason="Waiting for BRC29 API implementation")
    def test_return_error_when_nil_is_passed_as_recipient_public_key(self) -> None:
        """Given: None as recipient public key
           When: Call address_for_counterparty
           Then: Raises error
           
        Reference: toolbox/go-wallet-toolbox/pkg/brc29/brc29_address_test.go
                   TestBRC29AddressErrors
                   t.Run("return error when nil is passed as recipient public key")
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import address_for_counterparty
        
        # When / Then
        # with pytest.raises(Exception):
        #     address_for_counterparty(
        #         sender_priv_key=SENDER_PRIVATE_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_pub_key=None  # PublicKey
        #     )
        pass

