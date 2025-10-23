"""Unit tests for Wallet.create_action method.

Reference: wallet-toolbox/test/wallet/action/createAction.test.ts
"""

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError


class TestWalletCreateAction:
    """Test suite for Wallet.create_action method.

    createAction is the core method for creating Bitcoin transactions.
    It handles UTXO selection, transaction construction, and change management.
    """

    @pytest.mark.skip(reason="Waiting for create_action implementation")
    @pytest.mark.asyncio
    async def test_invalid_params_empty_description(self, wallet: Wallet) -> None:
        """Given: CreateActionArgs with empty description
           When: Call create_action
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/action/createAction.test.ts
                   test('0_invalid_params') - description is too short
        """
        # Given
        invalid_args = {"description": ""}  # Empty description

        # When / Then
        with pytest.raises(InvalidParameterError):
            await wallet.create_action(invalid_args)

    @pytest.mark.skip(reason="Waiting for create_action implementation")
    @pytest.mark.asyncio
    async def test_invalid_params_locking_script_not_hex(self, wallet: Wallet) -> None:
        """Given: CreateActionArgs with non-hexadecimal lockingScript
           When: Call create_action
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/action/createAction.test.ts
                   test('0_invalid_params') - lockingScript must be hexadecimal
        """
        # Given
        invalid_args = {
            "description": "12345",
            "outputs": [{"satoshis": 42, "lockingScript": "fred", "outputDescription": "pay fred"}],  # Not hex
        }

        # When / Then
        with pytest.raises(InvalidParameterError):
            await wallet.create_action(invalid_args)

    @pytest.mark.skip(reason="Waiting for create_action implementation")
    @pytest.mark.asyncio
    async def test_invalid_params_locking_script_odd_length(self, wallet: Wallet) -> None:
        """Given: CreateActionArgs with odd-length lockingScript
           When: Call create_action
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/action/createAction.test.ts
                   test('0_invalid_params') - lockingScript must be even length
        """
        # Given
        invalid_args = {
            "description": "12345",
            "outputs": [{"satoshis": 42, "lockingScript": "abc", "outputDescription": "pay fred"}],  # Odd length
        }

        # When / Then
        with pytest.raises(InvalidParameterError):
            await wallet.create_action(invalid_args)

    @pytest.mark.skip(reason="Waiting for create_action implementation with test database")
    @pytest.mark.asyncio
    async def test_repeatable_txid(self, wallet: Wallet) -> None:
        """Given: CreateActionArgs with deterministic settings (randomize_outputs=False)
           When: Call create_action with same args
           Then: Produces repeatable transaction ID

        Reference: wallet-toolbox/test/wallet/action/createAction.test.ts
                   test('1_repeatable txid')

        Note: This test requires:
        - Test wallet with known UTXOs
        - Deterministic random values for testing
        - signAndProcess=True, noSend=True options
        """
        # Given
        create_args = {
            "description": "repeatable",
            "outputs": [
                {
                    "satoshis": 45,
                    "lockingScript": "76a914" + "00" * 20 + "88ac",  # P2PKH script
                    "outputDescription": "pay echo",
                }
            ],
            "options": {"randomizeOutputs": False, "signAndProcess": True, "noSend": True},
        }
        expected_txid = "4f428a93c43c2d120204ecdc06f7916be8a5f4542cc8839a0fd79bd1b44582f3"

        # When
        result = await wallet.create_action(create_args)

        # Then
        assert result["txid"] == expected_txid

    @pytest.mark.skip(reason="Waiting for create_action implementation with test database")
    @pytest.mark.asyncio
    async def test_signable_transaction(self, wallet: Wallet) -> None:
        """Given: CreateActionArgs with signAndProcess=False
           When: Call create_action
           Then: Returns signableTransaction for external signing

        Reference: wallet-toolbox/test/wallet/action/createAction.test.ts
                   test('2_signableTransaction')

        Note: This test requires:
        - Test wallet with UTXOs
        - Ability to create unsigned transactions
        - noSend=True to prevent broadcasting
        """
        # Given
        create_args = {
            "description": "Test payment",
            "outputs": [
                {"satoshis": 42, "lockingScript": "76a914" + "00" * 20 + "88ac", "outputDescription": "pay fred"}
            ],
            "options": {"randomizeOutputs": False, "signAndProcess": False, "noSend": True},  # Return unsigned tx
        }

        # When
        result = await wallet.create_action(create_args)

        # Then
        assert "noSendChange" in result
        assert result["noSendChange"] is not None
        assert "sendWithResults" not in result or result["sendWithResults"] is None
        assert "tx" not in result or result["tx"] is None
        assert "txid" not in result or result["txid"] is None
        assert "signableTransaction" in result
        assert result["signableTransaction"] is not None
        assert "reference" in result["signableTransaction"]
        assert "tx" in result["signableTransaction"]  # AtomicBEEF format
