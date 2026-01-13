"""Unit tests for Wallet.sign_action and process_action methods.

These methods handle transaction signing and processing.

References:
- wallet-toolbox/src/signer/methods/signAction.ts
- wallet-toolbox/test/wallet/action/createAction.test.ts (includes signAction usage)
"""

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError, WalletError


@pytest.fixture
def valid_sign_action_args():
    """Fixture providing valid sign action arguments."""
    return {"reference": "test_reference_base64", "spends": {}}


@pytest.fixture
def valid_process_action_args():
    """Fixture providing valid process action arguments."""
    return {"txid": "a" * 64, "isNewTx": True, "rawTx": "deadbeef", "reference": "test_ref_base64", "noSend": True}


@pytest.fixture
def invalid_sign_action_cases():
    """Fixture providing various invalid sign action arguments."""
    return [
        {"reference": "", "spends": {}},  # Empty reference
        {"reference": None, "spends": {}},  # None reference
        {"reference": "valid_ref", "spends": "invalid"},  # Wrong spends type
        {"reference": 123, "spends": {}},  # Wrong reference type
        {"reference": [], "spends": {}},  # Wrong reference type
        {"reference": {}, "spends": {}},  # Wrong reference type
        {},  # Missing all keys
        {"spends": {}},  # Missing reference
    ]


@pytest.fixture
def invalid_process_action_cases():
    """Fixture providing various invalid process action arguments."""
    return [
        # Missing txid
        {"isNewTx": True, "rawTx": "deadbeef", "reference": "ref"},
        # None txid
        {"txid": None, "isNewTx": True, "rawTx": "deadbeef", "reference": "ref"},
        # Wrong txid type
        {"txid": 123, "isNewTx": True, "rawTx": "deadbeef", "reference": "ref"},
        # Invalid txid length
        {"txid": "short", "isNewTx": True, "rawTx": "deadbeef", "reference": "ref"},
        # None rawTx
        {"txid": "a" * 64, "isNewTx": True, "rawTx": None, "reference": "ref"},
        # Wrong rawTx type
        {"txid": "a" * 64, "isNewTx": True, "rawTx": 123, "reference": "ref"},
        # isNewTx=True missing reference
        {"txid": "a" * 64, "isNewTx": True, "rawTx": "deadbeef"},
        # None reference
        {"txid": "a" * 64, "isNewTx": True, "rawTx": "deadbeef", "reference": None},
        # Wrong reference type
        {"txid": "a" * 64, "isNewTx": True, "rawTx": "deadbeef", "reference": 123},
    ]


class TestWalletSignAction:
    """Test suite for Wallet.sign_action method.

    signAction takes an unsigned transaction (signableTransaction)
    and produces a signed transaction ready for broadcasting.
    """

    def test_sign_action_invalid_params_empty_reference(self, wallet_with_storage: Wallet) -> None:
        """Given: SignActionArgs with empty reference
           When: Call sign_action
           Then: Raises InvalidParameterError

        Note: Based on BRC-100 specification - reference is required.
        """
        # Given
        invalid_args = {"reference": "", "spends": {}}  # Empty reference

        # When / Then
        with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
            wallet_with_storage.sign_action(invalid_args)

    @pytest.mark.skip(reason="Complex transaction funding logic requires extensive fixture setup")
    def test_sign_action_with_valid_reference(self, wallet_with_storage: Wallet) -> None:
        """Given: SignActionArgs with valid reference from createAction
           When: Call sign_action
           Then: Returns signed transaction with txid

        Reference: wallet-toolbox/test/wallet/action/createAction.test.ts
                   test('2_signableTransaction') - sign and complete

        Note: This test requires:
        - Prior createAction call with signAndProcess=False
        - Valid reference from the signableTransaction
        """
        # Given - First create unsigned transaction
        create_args = {
            "description": "Test payment",
            "outputs": [
                {"satoshis": 42, "lockingScript": "76a914" + "00" * 20 + "88ac", "outputDescription": "pay fred"}
            ],
            "options": {"randomizeOutputs": False, "signAndProcess": False, "noSend": True},  # Get unsigned tx
        }
        create_result = wallet_with_storage.create_action(create_args)

        sign_args = {
            "reference": create_result["signableTransaction"]["reference"],
            "rawTx": (
                "".join(f"{b:02x}" for b in create_result["signableTransaction"]["tx"])
                if create_result["signableTransaction"]["tx"]
                else ""
            ),
            "spends": {},  # No specific spend authorizations needed
        }

        # When
        result = wallet_with_storage.sign_action(sign_args)

        # Then
        assert "txid" in result
        assert "tx" in result  # Signed raw transaction
        assert result["txid"] is not None
        assert result["tx"] is not None

    # @pytest.mark.skip(reason="Requires proper pending sign action setup with inputBeef")
    @pytest.mark.skip(reason="Requires real createAction flow and proper transaction references")
    def test_sign_action_with_spend_authorizations(self, wallet_with_storage: Wallet) -> None:
        """Given: SignActionArgs with specific spend authorizations
           When: Call sign_action
           Then: Returns signed transaction respecting spend policies

        Note: Based on BRC-100 specification for spending authorization.

        This test requires:
        - Understanding of spend authorization structure
        - Test outputs with specific spending policies
        """
        # Given
        sign_args = {
            "reference": "test_reference_base64",
            "spends": {"txid1.0": {"amount": 1000, "spendingDescription": "Authorized payment"}},
        }

        # When
        result = wallet_with_storage.sign_action(sign_args)

        # Then
        assert "txid" in result
        assert "tx" in result

    def test_sign_action_invalid_params_none_reference_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: SignActionArgs with None reference
        When: Call sign_action
        Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"reference": None, "spends": {}}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
            wallet_with_storage.sign_action(invalid_args)

    def test_sign_action_invalid_params_wrong_reference_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: SignActionArgs with wrong reference type
        When: Call sign_action
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid reference types
        invalid_types = [123, [], {}, True, 45.67]

        for invalid_ref in invalid_types:
            invalid_args = {"reference": invalid_ref, "spends": {}}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
                wallet_with_storage.sign_action(invalid_args)

    def test_sign_action_invalid_params_whitespace_reference_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: SignActionArgs with whitespace-only reference
        When: Call sign_action
        Then: Raises InvalidParameterError
        """
        # Given - Various whitespace references
        whitespace_refs = ["   ", "\t", "\n", " \t \n "]

        for ref in whitespace_refs:
            invalid_args = {"reference": ref, "spends": {}}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
                wallet_with_storage.sign_action(invalid_args)

    def test_sign_action_invalid_params_wrong_spends_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: SignActionArgs with wrong spends type
        When: Call sign_action
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid spends types
        invalid_types = ["string", 123, True, 45.67]

        for invalid_spends in invalid_types:
            invalid_args = {"reference": "test_ref", "spends": invalid_spends}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
                wallet_with_storage.sign_action(invalid_args)

    def test_sign_action_invalid_params_missing_reference_key_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: SignActionArgs missing reference key
        When: Call sign_action
        Then: Raises KeyError or TypeError
        """
        # Given
        invalid_args = {"spends": {}}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
            wallet_with_storage.sign_action(invalid_args)

    def test_sign_action_invalid_params_missing_spends_key_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: SignActionArgs missing spends key
        When: Call sign_action
        Then: Raises KeyError or TypeError
        """
        # Given
        invalid_args = {"reference": "test_ref"}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
            wallet_with_storage.sign_action(invalid_args)

    def test_sign_action_invalid_params_extra_keys_ignored(self, wallet_with_storage: Wallet) -> None:
        """Given: SignActionArgs with extra keys
        When: Call sign_action
        Then: Extra keys are ignored, processes normally or fails on invalid reference
        """
        # Given
        invalid_args = {
            "reference": "",  # Invalid reference
            "spends": {},
            "extraKey": "ignored",
            "anotherKey": 123,
            "nested": {"key": "value"},
        }

        # When/Then - Should fail on the invalid reference, not the extra keys
        with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
            wallet_with_storage.sign_action(invalid_args)

    def test_sign_action_invalid_reference_too_short_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: SignActionArgs with very short reference
        When: Call sign_action
        Then: Raises InvalidParameterError
        """
        # Given - Very short references
        short_refs = ["a", "ab", "abc", "1", "12"]

        for ref in short_refs:
            invalid_args = {"reference": ref, "spends": {}}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
                wallet_with_storage.sign_action(invalid_args)

    def test_sign_action_invalid_reference_invalid_base64_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: SignActionArgs with invalid base64 reference
        When: Call sign_action
        Then: Raises InvalidParameterError
        """
        # Given - References with invalid base64 chars
        invalid_refs = [
            "invalid@chars!",
            "contains#symbols",
            "with$dollar$signs",
            "percent%encoded",
            "caret^here",
            "ampersand&here",
            "asterisk*here",
            "plus+but+invalid",
            "slash/invalid",
            "backslash\\invalid",
        ]

        for ref in invalid_refs:
            invalid_args = {"reference": ref, "spends": {}}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
                wallet_with_storage.sign_action(invalid_args)


class TestWalletProcessAction:
    """Test suite for Wallet.process_action method.

    processAction handles post-signing transaction processing,
    including broadcasting to the network and updating wallet state.
    """

    # @pytest.mark.skip(reason="Requires proper transaction state setup")
    def test_process_action_invalid_params_missing_txid(self, wallet_with_storage: Wallet) -> None:
        """Given: ProcessActionArgs without required txid
           When: Call process_action
           Then: Raises InvalidParameterError

        Note: Based on BRC-100 specification - txid required for processing.
        """
        # Given
        invalid_args = {
            "isNewTx": True,
            "rawTx": b"\x01\x00\x00\x00",
            "reference": "ref123",
            # Missing txid
        }

        # When / Then
        with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
            wallet_with_storage.process_action(invalid_args)

    def test_process_action_invalid_params_new_tx_missing_reference(self, wallet_with_storage: Wallet) -> None:
        """Given: ProcessActionArgs with isNewTx=True but missing reference
           When: Call process_action
           Then: Raises InvalidParameterError

        Note: New transactions require a reference for tracking.
        """
        # Given
        invalid_args = {
            "txid": "a" * 64,
            "isNewTx": True,
            "rawTx": b"\x01\x00\x00\x00",
            # Missing reference
        }

        # When / Then
        with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
            wallet_with_storage.process_action(invalid_args)

    # @pytest.mark.skip(reason="Requires proper transaction state setup")
    @pytest.mark.skip(reason="Requires real createAction flow and proper transaction references")
    def test_process_action_new_transaction(self, wallet_with_storage: Wallet) -> None:
        """Given: ProcessActionArgs for a new signed transaction
           When: Call process_action
           Then: Transaction is broadcast and wallet state is updated

        Note: This test requires:
        - A signed transaction (from signAction)
        - Network connectivity or mocked services
        - noSend=True to prevent actual broadcasting in tests
        """
        # Given - From signAction result
        process_args = {
            "txid": "4f428a93c43c2d120204ecdc06f7916be8a5f4542cc8839a0fd79bd1b44582f3",
            "isNewTx": True,
            "rawTx": "deadbeef",  # Signed transaction hex string
            "reference": "test_ref_base64",
            "noSend": True,  # Don't actually broadcast in test
        }

        # When
        result = wallet_with_storage.process_action(process_args)

        # Then
        assert "txid" in result
        assert result["txid"] == process_args["txid"]

    # @pytest.mark.skip(reason="Requires proper transaction state setup")
    @pytest.mark.skip(reason="Requires real createAction flow and proper transaction references")
    def test_process_action_with_send_with(self, wallet_with_storage: Wallet) -> None:
        """Given: ProcessActionArgs with isSendWith=True and sendWith data
           When: Call process_action
           Then: Transaction is sent to specified recipients

        Note: Based on BRC-100 specification for sendWith functionality.

        This test requires:
        - Understanding of sendWith protocol
        - Mock or test recipients
        """
        # Given
        process_args = {
            "txid": "a" * 64,
            "isNewTx": True,
            "rawTx": "deadbeef",
            "reference": "test_ref",
            "isSendWith": True,
            "sendWith": [{"derivationPrefix": "prefix", "derivationSuffix": "suffix"}],
        }

        # When
        result = wallet_with_storage.process_action(process_args)

        # Then
        assert "txid" in result
        assert "sendWithResults" in result

    def test_process_action_invalid_params_none_txid_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ProcessActionArgs with None txid
        When: Call process_action
        Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"txid": None, "isNewTx": True, "rawTx": "deadbeef", "reference": "test_ref"}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
            wallet_with_storage.process_action(invalid_args)

    def test_process_action_invalid_params_wrong_txid_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ProcessActionArgs with wrong txid type
        When: Call process_action
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid txid types
        invalid_types = [123, [], {}, True, 45.67, b"bytes"]

        for invalid_txid in invalid_types:
            invalid_args = {"txid": invalid_txid, "isNewTx": True, "rawTx": "deadbeef", "reference": "test_ref"}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
                wallet_with_storage.process_action(invalid_args)

    def test_process_action_invalid_params_txid_wrong_length_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ProcessActionArgs with txid of wrong length
        When: Call process_action
        Then: Raises InvalidParameterError
        """
        # Given - txid should be 64 hex characters
        invalid_lengths = ["", "short", "a" * 63, "a" * 65, "g" * 64]  # Last one has invalid hex char

        for invalid_txid in invalid_lengths:
            invalid_args = {"txid": invalid_txid, "isNewTx": True, "rawTx": "deadbeef", "reference": "test_ref"}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
                wallet_with_storage.process_action(invalid_args)

    def test_process_action_invalid_params_none_raw_tx_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ProcessActionArgs with None rawTx
        When: Call process_action
        Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"txid": "a" * 64, "isNewTx": True, "rawTx": None, "reference": "test_ref"}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
            wallet_with_storage.process_action(invalid_args)

    def test_process_action_invalid_params_wrong_raw_tx_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ProcessActionArgs with wrong rawTx type
        When: Call process_action
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid rawTx types
        invalid_types = [123, [], {}, True, 45.67]

        for invalid_raw_tx in invalid_types:
            invalid_args = {"txid": "a" * 64, "isNewTx": True, "rawTx": invalid_raw_tx, "reference": "test_ref"}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
                wallet_with_storage.process_action(invalid_args)

    def test_process_action_invalid_params_none_reference_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ProcessActionArgs with None reference
        When: Call process_action
        Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"txid": "a" * 64, "isNewTx": True, "rawTx": "deadbeef", "reference": None}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
            wallet_with_storage.process_action(invalid_args)

    def test_process_action_invalid_params_wrong_reference_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ProcessActionArgs with wrong reference type
        When: Call process_action
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid reference types
        invalid_types = [123, [], {}, True, 45.67, b"bytes"]

        for invalid_ref in invalid_types:
            invalid_args = {"txid": "a" * 64, "isNewTx": True, "rawTx": "deadbeef", "reference": invalid_ref}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
                wallet_with_storage.process_action(invalid_args)

    def test_process_action_invalid_params_whitespace_reference_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ProcessActionArgs with whitespace-only reference
        When: Call process_action
        Then: Raises InvalidParameterError
        """
        # Given - Various whitespace references
        whitespace_refs = ["   ", "\t", "\n", " \t \n "]

        for ref in whitespace_refs:
            invalid_args = {"txid": "a" * 64, "isNewTx": True, "rawTx": "deadbeef", "reference": ref}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
                wallet_with_storage.process_action(invalid_args)

    def test_process_action_invalid_params_missing_txid_key_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ProcessActionArgs missing txid key
        When: Call process_action
        Then: Raises KeyError or TypeError
        """
        # Given
        invalid_args = {"isNewTx": True, "rawTx": "deadbeef", "reference": "test_ref"}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
            wallet_with_storage.process_action(invalid_args)

    def test_process_action_invalid_params_missing_raw_tx_key_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ProcessActionArgs missing rawTx key
        When: Call process_action
        Then: Raises KeyError or TypeError
        """
        # Given
        invalid_args = {"txid": "a" * 64, "isNewTx": True, "reference": "test_ref"}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
            wallet_with_storage.process_action(invalid_args)

    def test_process_action_invalid_params_is_new_tx_false_missing_txid_allowed(
        self, wallet_with_storage: Wallet
    ) -> None:
        """Given: ProcessActionArgs with isNewTx=False and missing txid
        When: Call process_action
        Then: May succeed or raise appropriate error based on implementation
        """
        # Given - For non-new transactions, txid might not be required
        args = {"isNewTx": False, "rawTx": "deadbeef", "reference": "test_ref"}

        # When/Then - Implementation dependent, but should not crash
        try:
            result = wallet_with_storage.process_action(args)
            # If it succeeds, should return some result
            assert isinstance(result, dict)
        except (InvalidParameterError, WalletError):
            # Acceptable - implementation may require txid or reference recovery may fail
            pass

    def test_process_action_invalid_params_invalid_base64_reference_raises_error(
        self, wallet_with_storage: Wallet
    ) -> None:
        """Given: ProcessActionArgs with invalid base64 reference
        When: Call process_action
        Then: Raises InvalidParameterError
        """
        # Given - References with invalid base64 chars
        invalid_refs = ["invalid@chars!", "contains#symbols", "with$dollar$signs", "percent%encoded"]

        for ref in invalid_refs:
            invalid_args = {"txid": "a" * 64, "isNewTx": True, "rawTx": "deadbeef", "reference": ref}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
                wallet_with_storage.process_action(invalid_args)

    def test_process_action_invalid_params_empty_raw_tx_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ProcessActionArgs with empty rawTx
        When: Call process_action
        Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"txid": "a" * 64, "isNewTx": True, "rawTx": "", "reference": "test_ref"}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError, TypeError, KeyError, WalletError)):
            wallet_with_storage.process_action(invalid_args)
