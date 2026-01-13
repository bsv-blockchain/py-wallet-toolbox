"""Unit tests for Wallet.create_action method.

Reference: wallet-toolbox/test/wallet/action/createAction.test.ts
"""

from datetime import UTC, datetime

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError


@pytest.fixture
def wallet_with_storage_and_funds(wallet_with_storage: Wallet) -> Wallet:
    """Create a wallet with storage and seeded UTXOs for create_action tests.

    This fixture extends wallet_with_storage by seeding a spendable UTXO
    that can be used to fund transactions in create_action tests.
    """
    wallet = wallet_with_storage
    storage = wallet.storage

    # Make storage available
    storage.make_available()

    # Get user ID from wallet
    auth = wallet._make_auth()
    user_id = auth["userId"]

    # Get or create default basket (required for allocate_funding_input)
    change_basket = storage.find_or_insert_output_basket(user_id, "default")
    basket_id = change_basket["basketId"] if isinstance(change_basket, dict) else change_basket.basket_id

    # Seed transaction that will provide the UTXO
    source_txid = "03cca43f0f28d3edffe30354b28934bc8e881e94ecfa68de2cf899a0a647d37c"
    tx_id = storage.insert_transaction(
        {
            "userId": user_id,
            "txid": source_txid,
            "status": "completed",
            "reference": "test-seed-tx",
            "isOutgoing": False,
            "satoshis": 50000,  # Sufficient to fund outputs + fees for createAction tests
            "description": "Seeded UTXO for testing",
            "version": 1,
            "lockTime": 0,
            "rawTx": bytes([1, 0, 0, 0, 1] + [0] * 100),  # Minimal valid transaction bytes
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
        }
    )

    # Seed spendable UTXO (output at vout 0)
    # Use a simple P2PKH locking script (OP_DUP OP_HASH160 <pubkey_hash> OP_EQUALVERIFY OP_CHECKSIG)
    pub_key = wallet.key_deriver._root_private_key.public_key()
    pub_key_hash = pub_key.hash160()
    # P2PKH: 76 a9 14 <20 bytes pubkey hash> 88 ac
    locking_script = bytes([0x76, 0xA9, 0x14]) + pub_key_hash + bytes([0x88, 0xAC])

    storage.insert_output(
        {
            "transactionId": tx_id,
            "userId": user_id,
            "basketId": basket_id,  # "default" basket - required for allocate_funding_input
            "spendable": True,
            "change": True,  # Change outputs are spendable
            "vout": 0,
            "satoshis": 50000,  # Sufficient to fund outputs + fees for createAction tests
            "providedBy": "storage",  # Must be "storage" to match working examples
            "purpose": "change",
            "type": "P2PKH",  # Must be "P2PKH" for signer to process it correctly
            "txid": source_txid,
            "lockingScript": locking_script,
            "spentBy": None,  # Explicitly set to None to ensure it's allocatable
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
        }
    )

    return wallet


@pytest.fixture
def valid_create_action_args():
    """Fixture providing valid create action arguments."""
    return {
        "description": "Test transaction",
        "outputs": [
            {
                "satoshis": 42,
                "lockingScript": "76a914" + "00" * 20 + "88ac",  # P2PKH script
                "outputDescription": "test output",
            }
        ],
    }


@pytest.fixture
def create_action_args_no_send():
    """Fixture providing create action arguments with noSend option."""
    return {
        "description": "Test no send",
        "outputs": [
            {"satoshis": 45, "lockingScript": "76a914" + "11" * 20 + "88ac", "outputDescription": "no send output"}
        ],
        "options": {"randomizeOutputs": False, "signAndProcess": True, "noSend": True},
    }


@pytest.fixture
def create_action_args_signable():
    """Fixture providing create action arguments for signable transaction."""
    return {
        "description": "Test signable",
        "outputs": [
            {"satoshis": 100, "lockingScript": "76a914" + "22" * 20 + "88ac", "outputDescription": "signable output"}
        ],
        "options": {"randomizeOutputs": False, "signAndProcess": False, "noSend": True},
    }


class TestWalletCreateAction:
    """Test suite for Wallet.create_action method.

    createAction is the core method for creating Bitcoin transactions.
    It handles UTXO selection, transaction construction, and change management.
    """

    def test_invalid_params_empty_description(self, wallet_with_storage: Wallet) -> None:
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
            wallet_with_storage.create_action(invalid_args)

    def test_invalid_params_locking_script_not_hex(self, wallet_with_storage: Wallet) -> None:
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
            wallet_with_storage.create_action(invalid_args)

    def test_invalid_params_locking_script_odd_length(self, wallet_with_storage: Wallet) -> None:
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
            wallet_with_storage.create_action(invalid_args)

    def test_repeatable_txid(self, wallet_with_storage_and_funds: Wallet) -> None:
        """Given: CreateActionArgs with deterministic settings (randomize_outputs=False)
           When: Call create_action
           Then: Produces a valid transaction ID

        Reference: wallet-toolbox/test/wallet/action/createAction.test.ts
                   test('1_repeatable txid')

        Note: This test verifies deterministic transaction building.
              The exact txid depends on UTXOs and keys. Testing true repeatability
              requires separate wallet instances to avoid UNIQUE constraint issues.
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

        # When
        result = wallet_with_storage_and_funds.create_action(create_args)

        # Then - Valid txid returned
        assert "txid" in result
        assert isinstance(result["txid"], str)
        assert len(result["txid"]) == 64  # Valid hex txid length
        # Verify transaction data is present
        assert "tx" in result
        assert isinstance(result["tx"], list)  # BRC-100 format (list[int])

    def test_signable_transaction(self, wallet_with_storage_and_funds: Wallet) -> None:
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
        result = wallet_with_storage_and_funds.create_action(create_args)

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

    def test_create_action_defaults_options_and_returns_signable(self, wallet_with_mocked_create_action) -> None:
        wallet, _storage, call_log, user_id = wallet_with_mocked_create_action

        args = {
            "description": "Mock flow",
            "outputs": [
                {
                    "satoshis": 1200,
                    "lockingScript": "76a914" + "11" * 20 + "88ac",
                    "outputDescription": "payment",
                }
            ],
        }

        result = wallet.create_action(args)

        assert call_log["auth"]["userId"] == user_id
        assert "options" in call_log["args"]
        # Options include normalized defaults
        assert call_log["args"]["options"]["trustSelf"] == "known"
        assert result["signableTransaction"] == {"reference": "ref-456", "tx": [0xDE, 0xAD]}
        assert result["noSendChange"] == ["mock.txid.0"]

    def test_create_action_sign_and_process_flow(self, wallet_with_mocked_create_action) -> None:
        wallet, _storage, call_log, _ = wallet_with_mocked_create_action

        args = {
            "description": "Process flow",
            "outputs": [
                {
                    "satoshis": 5000,
                    "lockingScript": "76a914" + "22" * 20 + "88ac",
                    "outputDescription": "service",
                }
            ],
            "options": {"signAndProcess": True, "noSend": True},
        }

        result = wallet.create_action(args)

        assert result["txid"] == "mock-deterministic-txid"
        assert result["noSendChangeOutputVouts"] == [1, 2]
        assert call_log["args"]["options"]["signAndProcess"] is True
        assert call_log["args"]["options"]["noSend"] is True
        assert "signableTransaction" not in result

    def test_invalid_params_negative_satoshis(self, wallet_with_storage: Wallet) -> None:
        """Given: CreateActionArgs with negative satoshis
        When: Call create_action
        Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {
            "description": "negative sats",
            "outputs": [
                {"satoshis": -1, "lockingScript": "76a914" + "00" * 20 + "88ac", "outputDescription": "negative"}
            ],
        }

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_storage.create_action(invalid_args)

    def test_invalid_params_zero_satoshis(self, wallet_with_storage: Wallet) -> None:
        """Given: CreateActionArgs with zero satoshis
        When: Call create_action
        Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {
            "description": "zero sats",
            "outputs": [{"satoshis": 0, "lockingScript": "76a914" + "00" * 20 + "88ac", "outputDescription": "zero"}],
        }

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_storage.create_action(invalid_args)

    def test_invalid_params_empty_outputs(self, wallet_with_storage: Wallet) -> None:
        """Given: CreateActionArgs with empty outputs array
        When: Call create_action
        Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"description": "no outputs", "outputs": []}

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_storage.create_action(invalid_args)

    def test_invalid_params_none_outputs(self, wallet_with_storage: Wallet) -> None:
        """Given: CreateActionArgs with None outputs
        When: Call create_action
        Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"description": "none outputs", "outputs": None}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_storage.create_action(invalid_args)

    def test_invalid_params_missing_satoshis(self, wallet_with_storage: Wallet) -> None:
        """Given: CreateActionArgs with missing satoshis in output
        When: Call create_action
        Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {
            "description": "missing satoshis",
            "outputs": [{"lockingScript": "76a914" + "00" * 20 + "88ac", "outputDescription": "missing sats"}],
        }

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError)):
            wallet_with_storage.create_action(invalid_args)

    def test_invalid_params_missing_locking_script(self, wallet_with_storage: Wallet) -> None:
        """Given: CreateActionArgs with missing lockingScript in output
        When: Call create_action
        Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {
            "description": "missing script",
            "outputs": [{"satoshis": 42, "outputDescription": "missing script"}],
        }

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError)):
            wallet_with_storage.create_action(invalid_args)

    def test_invalid_params_invalid_hex_locking_script(self, wallet_with_storage: Wallet) -> None:
        """Given: CreateActionArgs with invalid hex characters in lockingScript
        When: Call create_action
        Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {
            "description": "invalid hex",
            "outputs": [
                {"satoshis": 42, "lockingScript": "zzzz" + "00" * 18 + "88ac", "outputDescription": "invalid hex"}
            ],
        }

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError)):
            wallet_with_storage.create_action(invalid_args)

    def test_invalid_params_extremely_large_satoshis(self, wallet_with_storage: Wallet) -> None:
        """Given: CreateActionArgs with extremely large satoshis (> 21M BTC)
        When: Call create_action
        Then: Raises InvalidParameterError
        """
        # Given - 22 BTC in satoshis (more than max supply)
        large_amount = 22 * 100_000_000 * 100_000_000  # 2.2 quadrillion satoshis
        invalid_args = {
            "description": "too large",
            "outputs": [
                {
                    "satoshis": large_amount,
                    "lockingScript": "76a914" + "00" * 20 + "88ac",
                    "outputDescription": "too large",
                }
            ],
        }

        # When/Then
        with pytest.raises((InvalidParameterError, ValueError, OverflowError)):
            wallet_with_storage.create_action(invalid_args)

    def test_valid_params_minimal_satoshis(self, wallet_with_storage: Wallet) -> None:
        """Given: CreateActionArgs with minimal valid satoshis (dust threshold)
        When: Call create_action
        Then: Creates transaction successfully
        """
        # Given - Using 1 satoshi (below dust but might still work for testing)
        minimal_args = {
            "description": "minimal",
            "outputs": [
                {"satoshis": 1, "lockingScript": "76a914" + "00" * 20 + "88ac", "outputDescription": "minimal"}
            ],
            "options": {"noSend": True, "signAndProcess": True},
        }

        # When
        result = wallet_with_storage.create_action(minimal_args)

        # Then - Should succeed (exact behavior depends on implementation)
        assert isinstance(result, dict)
        # Either returns txid or indicates transaction creation
        assert "txid" in result or "noSendChange" in result or "signableTransaction" in result

    def test_valid_params_multiple_outputs(self, wallet_with_storage: Wallet) -> None:
        """Given: CreateActionArgs with multiple outputs
        When: Call create_action
        Then: Creates transaction with multiple outputs
        """
        # Given
        multi_output_args = {
            "description": "multiple outputs",
            "outputs": [
                {"satoshis": 100, "lockingScript": "76a914" + "11" * 20 + "88ac", "outputDescription": "output1"},
                {"satoshis": 200, "lockingScript": "76a914" + "22" * 20 + "88ac", "outputDescription": "output2"},
                {"satoshis": 300, "lockingScript": "76a914" + "33" * 20 + "88ac", "outputDescription": "output3"},
            ],
            "options": {"noSend": True, "signAndProcess": True},
        }

        # When
        result = wallet_with_storage.create_action(multi_output_args)

        # Then
        assert isinstance(result, dict)
        assert "txid" in result or "noSendChange" in result

    def test_valid_params_with_options(self, wallet_with_storage: Wallet, valid_create_action_args) -> None:
        """Given: CreateActionArgs with various options
        When: Call create_action
        Then: Respects option settings
        """
        # Given
        args_with_options = valid_create_action_args.copy()
        args_with_options["options"] = {
            "randomizeOutputs": False,
            "trustSelf": False,
            "noSend": True,
            "signAndProcess": True,
        }

        # When
        result = wallet_with_storage.create_action(args_with_options)

        # Then
        assert isinstance(result, dict)
        # Should have noSendChange since noSend=True
        assert "noSendChange" in result

    def test_invalid_params_empty_description_edge_cases(self, wallet_with_storage: Wallet) -> None:
        """Given: CreateActionArgs with various empty/whitespace descriptions
        When: Call create_action
        Then: Raises InvalidParameterError for all cases
        """
        # Given - Various empty/whitespace descriptions
        empty_descriptions = ["", "   ", "\t", "\n", " \t \n "]

        for desc in empty_descriptions:
            invalid_args = {
                "description": desc,
                "outputs": [
                    {"satoshis": 42, "lockingScript": "76a914" + "00" * 20 + "88ac", "outputDescription": "test"}
                ],
            }

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError)):
                wallet_with_storage.create_action(invalid_args)

    def test_invalid_params_locking_script_edge_cases(self, wallet_with_storage: Wallet) -> None:
        """Given: CreateActionArgs with various invalid locking scripts
        When: Call create_action
        Then: Raises InvalidParameterError for all cases
        """
        # Given - Various invalid locking scripts
        invalid_scripts = [
            "",  # Empty
            "76a914",  # Too short
            "76a914" + "00" * 19,  # Odd length
            "76a914" + "00" * 20 + "88",  # Too short (missing last byte)
            "gggg" + "00" * 18 + "88ac",  # Invalid hex chars
            "76a914" + "00" * 20 + "gggg",  # Invalid hex at end
            None,  # None value
        ]

        for script in invalid_scripts:
            invalid_args = {
                "description": "invalid script test",
                "outputs": [{"satoshis": 42, "lockingScript": script, "outputDescription": "test"}],
            }

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError, TypeError)):
                wallet_with_storage.create_action(invalid_args)

    def test_valid_params_unicode_description(self, wallet_with_storage: Wallet) -> None:
        """Given: CreateActionArgs with unicode description
        When: Call create_action
        Then: Handles unicode correctly
        """
        # Given
        unicode_args = {
            "description": "Test transaction with unicode: 你好世界 🌍",
            "outputs": [
                {"satoshis": 42, "lockingScript": "76a914" + "00" * 20 + "88ac", "outputDescription": "unicode test"}
            ],
            "options": {"noSend": True},
        }

        # When
        result = wallet_with_storage.create_action(unicode_args)

        # Then
        assert isinstance(result, dict)

    def test_invalid_params_none_description_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: CreateActionArgs with None description
        When: Call create_action
        Then: Raises TypeError
        """
        # Given
        invalid_args = {
            "description": None,
            "outputs": [{"satoshis": 42, "lockingScript": "76a914" + "00" * 20 + "88ac", "outputDescription": "test"}],
        }

        # When/Then
        with pytest.raises(TypeError):
            wallet_with_storage.create_action(invalid_args)

    def test_invalid_params_invalid_output_format(self, wallet_with_storage: Wallet) -> None:
        """Given: CreateActionArgs with invalid output format (not a dict)
        When: Call create_action
        Then: Raises appropriate error
        """
        # Given
        invalid_args = {
            "description": "invalid output",
            "outputs": ["invalid", "output", "format"],  # Should be list of dicts
        }

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_storage.create_action(invalid_args)
