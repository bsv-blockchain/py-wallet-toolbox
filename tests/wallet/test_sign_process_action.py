"""Unit tests for Wallet.sign_action and process_action methods.

These methods handle transaction signing and processing.

References:
- wallet-toolbox/src/signer/methods/signAction.ts
- wallet-toolbox/test/wallet/action/createAction.test.ts (includes signAction usage)
"""

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError


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
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.sign_action(invalid_args)

    @pytest.mark.skip(reason="Requires transaction building infrastructure (input selection, BEEF generation)")
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
            "rawTx": "".join(f"{b:02x}" for b in create_result["signableTransaction"]["tx"]) if create_result["signableTransaction"]["tx"] else "",
            "spends": {},  # No specific spend authorizations needed
        }

        # When
        result = wallet_with_storage.sign_action(sign_args)

        # Then
        assert "txid" in result
        assert "tx" in result  # Signed raw transaction
        assert result["txid"] is not None
        assert result["tx"] is not None

    @pytest.mark.skip(reason="Requires proper pending sign action setup with inputBeef")
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


class TestWalletProcessAction:
    """Test suite for Wallet.process_action method.

    processAction handles post-signing transaction processing,
    including broadcasting to the network and updating wallet state.
    """

    @pytest.mark.skip(reason="Requires proper transaction state setup")
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
        with pytest.raises(InvalidParameterError):
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
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.process_action(invalid_args)

    @pytest.mark.skip(reason="Requires proper transaction state setup")
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

    @pytest.mark.skip(reason="Requires proper transaction state setup")
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
