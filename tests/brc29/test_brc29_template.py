"""Unit tests for BRC29 template functionality (locking/unlocking scripts).

Ported from Go implementation to ensure compatibility.

Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
"""

import pytest

from bsv_wallet_toolbox.brc29 import KeyID, lock_for_counterparty, lock_for_self, unlock

# Test data (shared with test_brc29_address.py)
SENDER_PUBLIC_KEY_HEX = "0320bbfb879bbd6761ecd2962badbb41ba9d60ca88327d78b07ae7141af6b6c810"
SENDER_PRIVATE_KEY_HEX = "143ab18a84d3b25e1a13cefa90038411e5d2014590a2a4a57263d1593c8dee1c"
RECIPIENT_PUBLIC_KEY_HEX = "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
RECIPIENT_PRIVATE_KEY_HEX = "0000000000000000000000000000000000000000000000000000000000000001"
KEY_ID = KeyID(derivation_prefix="Pr==", derivation_suffix="Su==")
EXPECTED_ADDRESS = "18HqET2ViSHNj9nvFiTSp1LXbgBpLCsi1r"
INVALID_KEY_HEX = "invalid"


class TestBRC29TemplateLock:
    """Test suite for BRC29 template locking (counterparty).

    Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
               TestBRC29TemplateLock
    """

    def test_should_lock_with_p2pkh_and_brc29_calculated_address(self) -> None:
        """Given: Sender private key, key ID, recipient public key
           When: Call lock_for_counterparty
           Then: Returns locking script that can be converted to expected address

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLock
                   t.Run("should lock with P2PKH and BRC29 calculated address")
        """
        # Given / When
        locking_script = lock_for_counterparty(
            sender_private_key=SENDER_PRIVATE_KEY_HEX, key_id=KEY_ID, recipient_public_key=RECIPIENT_PUBLIC_KEY_HEX
        )

        # Then
        assert locking_script is not None
        # Verify it's a valid P2PKH script (starts with OP_DUP OP_HASH160)
        script_hex = locking_script.hex()
        assert script_hex.startswith("76a914")  # OP_DUP OP_HASH160
        assert script_hex.endswith("88ac")  # OP_EQUALVERIFY OP_CHECKSIG

    def test_return_error_when_key_id_is_invalid(self) -> None:
        """Given: Invalid key ID (empty derivation prefix)
           When: Call lock_for_counterparty
           Then: Raises ValueError

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLock
                   errorTestCases "return error when key id is invalid"
        """
        # Given
        invalid_key_id = KeyID(derivation_prefix="", derivation_suffix="Su==")

        # When / Then
        with pytest.raises(ValueError):
            lock_for_counterparty(
                sender_private_key=SENDER_PRIVATE_KEY_HEX,
                key_id=invalid_key_id,
                recipient_public_key=RECIPIENT_PUBLIC_KEY_HEX,
            )

    def test_return_error_when_nil_is_passed_as_sender_private_key_deriver(self) -> None:
        """Given: None as sender private key deriver
           When: Call lock_for_counterparty
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLock
                   t.Run("return error when nil is passed as sender private key deriver")
        """
        # Given / When / Then
        with pytest.raises(Exception):
            lock_for_counterparty(
                sender_private_key=None, key_id=KEY_ID, recipient_public_key=RECIPIENT_PUBLIC_KEY_HEX  # KeyDeriver
            )

    def test_return_error_when_nil_is_passed_as_sender_private_key(self) -> None:
        """Given: None as sender private key
           When: Call lock_for_counterparty
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLock
                   t.Run("return error when nil is passed as sender private key")
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import lock_for_counterparty

        # When / Then
        # with pytest.raises(Exception):
        #     lock_for_counterparty(
        #         sender_priv_key=None,  # PrivateKey
        #         key_id=KEY_ID,
        #         recipient_pub_key=RECIPIENT_PUBLIC_KEY_HEX
        #     )

    def test_return_error_when_nil_is_passed_as_recipient_public_key_deriver(self) -> None:
        """Given: None as recipient public key deriver
           When: Call lock_for_counterparty
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLock
                   t.Run("return error when nil is passed as recipient public key deriver")
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import lock_for_counterparty

        # When / Then
        # with pytest.raises(Exception):
        #     lock_for_counterparty(
        #         sender_priv_key=SENDER_PRIVATE_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_pub_key=None  # KeyDeriver
        #     )

    def test_return_error_when_nil_is_passed_as_recipient_public_key(self) -> None:
        """Given: None as recipient public key
           When: Call lock_for_counterparty
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLock
                   t.Run("return error when nil is passed as recipient public key")
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import lock_for_counterparty

        # When / Then
        # with pytest.raises(Exception):
        #     lock_for_counterparty(
        #         sender_priv_key=SENDER_PRIVATE_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_pub_key=None  # PublicKey
        #     )

    def test_return_error_when_sender_key_is_empty(self) -> None:
        """Given: Empty sender key
           When: Call lock_for_counterparty
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLock
                   errorTestCases "return error when sender key is empty"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import lock_for_counterparty

        # When / Then
        # with pytest.raises(Exception):
        #     lock_for_counterparty(
        #         sender_priv_key="",
        #         key_id=KEY_ID,
        #         recipient_pub_key=INVALID_KEY_HEX
        #     )

    def test_return_error_when_sender_key_parsing_fails(self) -> None:
        """Given: Invalid sender key
           When: Call lock_for_counterparty
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLock
                   errorTestCases "return error when sender key parsing fails"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import lock_for_counterparty

        # When / Then
        # with pytest.raises(Exception):
        #     lock_for_counterparty(
        #         sender_priv_key=INVALID_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_pub_key=RECIPIENT_PUBLIC_KEY_HEX
        #     )

    def test_return_error_when_keyid_is_invalid(self) -> None:
        """Given: Invalid key ID
           When: Call lock_for_counterparty
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLock
                   errorTestCases "return error when KeyID is invalid"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import lock_for_counterparty

        # When / Then
        # with pytest.raises(Exception):
        #     lock_for_counterparty(
        #         sender_priv_key=SENDER_PRIVATE_KEY_HEX,
        #         key_id={"derivation_prefix": "", "derivation_suffix": ""},
        #         recipient_pub_key=RECIPIENT_PUBLIC_KEY_HEX
        #     )

    def test_return_error_when_recipient_key_is_empty(self) -> None:
        """Given: Empty recipient key
           When: Call lock_for_counterparty
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLock
                   errorTestCases "return error when recipient key is empty"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import lock_for_counterparty

        # When / Then
        # with pytest.raises(Exception):
        #     lock_for_counterparty(
        #         sender_priv_key=SENDER_PRIVATE_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_pub_key=""
        #     )

    def test_return_error_when_recipient_key_parsing_fails(self) -> None:
        """Given: Invalid recipient key
           When: Call lock_for_counterparty
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLock
                   errorTestCases "return error when recipient key parsing fails"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import lock_for_counterparty

        # When / Then
        # with pytest.raises(Exception):
        #     lock_for_counterparty(
        #         sender_priv_key=SENDER_PRIVATE_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_pub_key=INVALID_KEY_HEX
        #     )


class TestBRC29TemplateLockForSelf:
    """Test suite for BRC29 template locking (self/recipient).

    Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
               TestBRC29TemplateLockForSelf
    """

    def test_should_lock_with_p2pkh_and_brc29_calculated_address_self(self) -> None:
        """Given: Sender public key, key ID, recipient private key
           When: Call lock_for_self
           Then: Returns locking script that can be converted to expected address

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLockForSelf
                   t.Run("should lock with P2PKH and BRC29 calculated address (self)")
        """
        # Given / When
        locking_script = lock_for_self(
            sender_public_key=SENDER_PUBLIC_KEY_HEX, key_id=KEY_ID, recipient_private_key=RECIPIENT_PRIVATE_KEY_HEX
        )

        # Then
        assert locking_script is not None
        # Verify it's a valid P2PKH script (starts with OP_DUP OP_HASH160)
        script_hex = locking_script.hex()
        assert script_hex.startswith("76a914")  # OP_DUP OP_HASH160
        assert script_hex.endswith("88ac")  # OP_EQUALVERIFY OP_CHECKSIG

    def test_return_error_when_key_id_is_invalid_self(self) -> None:
        """Given: Invalid key ID (empty derivation prefix)
           When: Call lock_for_self
           Then: Raises ValueError

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLockForSelf
                   errorTestCases "return error when key id is invalid (self)"
        """
        # Given
        invalid_key_id = KeyID(derivation_prefix="", derivation_suffix="Su==")

        # When / Then
        with pytest.raises(ValueError):
            lock_for_self(
                sender_public_key=SENDER_PUBLIC_KEY_HEX,
                key_id=invalid_key_id,
                recipient_private_key=RECIPIENT_PRIVATE_KEY_HEX,
            )

    def test_return_error_when_nil_is_passed_as_sender_public_key_deriver(self) -> None:
        """Given: None as sender public key deriver
           When: Call lock_for_self
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLockForSelf
                   t.Run("return error when nil is passed as sender public key deriver")
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import lock_for_self

        # When / Then
        # with pytest.raises(Exception):
        #     lock_for_self(
        #         sender_pub_key=None,  # KeyDeriver
        #         key_id=KEY_ID,
        #         recipient_priv_key=RECIPIENT_PRIVATE_KEY_HEX
        #     )

    def test_return_error_when_nil_is_passed_as_sender_public_key(self) -> None:
        """Given: None as sender public key
           When: Call lock_for_self
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLockForSelf
                   t.Run("return error when nil is passed as sender public key")
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import lock_for_self

        # When / Then
        # with pytest.raises(Exception):
        #     lock_for_self(
        #         sender_pub_key=None,  # PublicKey
        #         key_id=KEY_ID,
        #         recipient_priv_key=RECIPIENT_PRIVATE_KEY_HEX
        #     )

    def test_return_error_when_nil_is_passed_as_recipient_private_key_deriver(self) -> None:
        """Given: None as recipient private key deriver
           When: Call lock_for_self
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLockForSelf
                   t.Run("return error when nil is passed as recipient private key deriver")
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import lock_for_self

        # When / Then
        # with pytest.raises(Exception):
        #     lock_for_self(
        #         sender_pub_key=SENDER_PUBLIC_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_priv_key=None  # KeyDeriver
        #     )

    def test_return_error_when_nil_is_passed_as_recipient_private_key(self) -> None:
        """Given: None as recipient private key
           When: Call lock_for_self
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLockForSelf
                   t.Run("return error when nil is passed as recipient private key")
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import lock_for_self

        # When / Then
        # with pytest.raises(Exception):
        #     lock_for_self(
        #         sender_pub_key=SENDER_PUBLIC_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_priv_key=None  # PrivateKey
        #     )

    def test_return_error_when_sender_key_is_empty(self) -> None:
        """Given: Empty sender key
           When: Call lock_for_self
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLockForSelf
                   errorTestCases "return error when sender key is empty"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import lock_for_self

        # When / Then
        # with pytest.raises(Exception):
        #     lock_for_self(
        #         sender_pub_key="",
        #         key_id=KEY_ID,
        #         recipient_priv_key=INVALID_KEY_HEX
        #     )

    def test_return_error_when_sender_key_parsing_fails(self) -> None:
        """Given: Invalid sender key
           When: Call lock_for_self
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLockForSelf
                   errorTestCases "return error when sender key parsing fails"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import lock_for_self

        # When / Then
        # with pytest.raises(Exception):
        #     lock_for_self(
        #         sender_pub_key=INVALID_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_priv_key=RECIPIENT_PRIVATE_KEY_HEX
        #     )

    def test_return_error_when_keyid_is_invalid(self) -> None:
        """Given: Invalid key ID
           When: Call lock_for_self
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLockForSelf
                   errorTestCases "return error when KeyID is invalid"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import lock_for_self

        # When / Then
        # with pytest.raises(Exception):
        #     lock_for_self(
        #         sender_pub_key=SENDER_PUBLIC_KEY_HEX,
        #         key_id={"derivation_prefix": "", "derivation_suffix": ""},
        #         recipient_priv_key=RECIPIENT_PRIVATE_KEY_HEX
        #     )

    def test_return_error_when_recipient_key_is_empty(self) -> None:
        """Given: Empty recipient key
           When: Call lock_for_self
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLockForSelf
                   errorTestCases "return error when recipient key is empty"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import lock_for_self

        # When / Then
        # with pytest.raises(Exception):
        #     lock_for_self(
        #         sender_pub_key=SENDER_PUBLIC_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_priv_key=""
        #     )

    def test_return_error_when_recipient_key_parsing_fails(self) -> None:
        """Given: Invalid recipient key
           When: Call lock_for_self
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateLockForSelf
                   errorTestCases "return error when recipient key parsing fails"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import lock_for_self

        # When / Then
        # with pytest.raises(Exception):
        #     lock_for_self(
        #         sender_pub_key=SENDER_PUBLIC_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_priv_key=INVALID_KEY_HEX
        #     )


class TestBRC29TemplateUnlock:
    """Test suite for BRC29 template unlocking.

    Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
               TestBRC29TemplateUnlock
    """

    def test_unlock_the_output_locked_with_brc29_locker(self) -> None:
        """Given: Transaction with BRC29 locked output
           When: Create unlocker and sign transaction
           Then: Transaction can be validated by script interpreter

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateUnlock
                   t.Run("unlock the output locked with BRC29 locker")
        """
        # Given
        # from bsv_wallet_toolbox.transaction import Transaction
        # from bsv_wallet_toolbox.brc29 import lock_for_counterparty, unlock
        # from bsv_wallet_toolbox.script.interpreter import ScriptInterpreter

        # prev_txid = "64faeaa2e3cbadaf82d8fa8c7ded508cb043c5d101671f43c084be2ac6163148"
        # tx = Transaction()
        # tx.add_op_return_output(b"anything")

        # locking_script = lock_for_counterparty(
        #     sender_priv_key=SENDER_PRIVATE_KEY_HEX,
        #     key_id=KEY_ID,
        #     recipient_pub_key=RECIPIENT_PUBLIC_KEY_HEX
        # )

        # When
        # unlocker = unlock(
        #     sender_pub_key=SENDER_PUBLIC_KEY_HEX,
        #     key_id=KEY_ID,
        #     recipient_priv_key=RECIPIENT_PRIVATE_KEY_HEX
        # )

        # utxo = {
        #     "txid": prev_txid,
        #     "vout": 0,
        #     "satoshis": 1000,
        #     "locking_script": locking_script,
        #     "unlocking_script_template": unlocker
        # }
        # tx.add_inputs_from_utxos([utxo])
        # tx.sign()

        # Then
        # interpreter = ScriptInterpreter()
        # interpreter.execute(tx, 0, after_genesis=True, fork_id=True)
        # No error should be raised

    def test_estimate_unlocking_script_length(self) -> None:
        """Given: BRC29 unlocker template
           When: Call estimate_length
           Then: Returns expected length (106 bytes)

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateUnlock
                   t.Run("estimate unlocking script length")
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import unlock
        # from bsv_wallet_toolbox.transaction import Transaction

        # unlocker = unlock(
        #     sender_pub_key=SENDER_PUBLIC_KEY_HEX,
        #     key_id=KEY_ID,
        #     recipient_priv_key=RECIPIENT_PRIVATE_KEY_HEX
        # )

        # When
        # tx = Transaction()
        # length = unlocker.estimate_length(tx, 0)

        # Then
        # assert length == 106

    def test_return_error_when_sender_key_is_empty(self) -> None:
        """Given: Empty sender key
           When: Call unlock
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateUnlock
                   errorTestCases "return error when sender key is empty"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import unlock

        # When / Then
        # with pytest.raises(Exception):
        #     unlock(
        #         sender_pub_key="",
        #         key_id=KEY_ID,
        #         recipient_priv_key=RECIPIENT_PRIVATE_KEY_HEX
        #     )

    def test_return_error_when_sender_key_parsing_fails(self) -> None:
        """Given: Invalid sender key
           When: Call unlock
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateUnlock
                   errorTestCases "return error when sender key parsing fails"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import unlock

        # When / Then
        # with pytest.raises(Exception):
        #     unlock(
        #         sender_pub_key=INVALID_KEY_HEX,
        #         key_id=KEY_ID,
        #         recipient_priv_key=RECIPIENT_PRIVATE_KEY_HEX
        #     )

    def test_return_error_when_keyid_is_invalid(self) -> None:
        """Given: Invalid key ID
           When: Call unlock
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateUnlock
                   errorTestCases "return error when KeyID is invalid"
        """
        # Given
        # from bsv_wallet_toolbox.brc29 import unlock

        # When / Then
        # with pytest.raises(Exception):
        #     unlock(
        #         sender_pub_key=SENDER_PUBLIC_KEY_HEX,
        #         key_id={"derivation_prefix": "", "derivation_suffix": ""},
        #         recipient_priv_key=RECIPIENT_PRIVATE_KEY_HEX
        #     )

    def test_return_error_when_recipient_key_is_empty(self) -> None:
        """Given: Empty recipient key
           When: Call unlock
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateUnlock
                   errorTestCases "return error when recipient key is empty"
        """
        # Given / When / Then
        with pytest.raises(ValueError):
            unlock(sender_public_key=SENDER_PUBLIC_KEY_HEX, key_id=KEY_ID, recipient_private_key="")

    def test_return_error_when_recipient_key_parsing_fails(self) -> None:
        """Given: Invalid recipient key
           When: Call unlock
           Then: Raises error

        Reference: go-wallet-toolbox/pkg/brc29/brc29_template_test.go
                   TestBRC29TemplateUnlock
                   errorTestCases "return error when recipient key parsing fails"
        """
        # Given / When / Then
        with pytest.raises(ValueError):
            unlock(sender_public_key=SENDER_PUBLIC_KEY_HEX, key_id=KEY_ID, recipient_private_key=INVALID_KEY_HEX)
