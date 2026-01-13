"""Comprehensive tests for signer/methods.py to achieve 100% coverage.

This module provides exhaustive test coverage for all functions and edge cases
in the signer methods module, targeting the 168 missing lines.
"""

from unittest.mock import Mock, patch

import pytest

from bsv_wallet_toolbox.errors.wallet_errors import WalletError
from bsv_wallet_toolbox.signer.methods import (
    CreateActionResultX,
    _create_new_tx,
    _make_change_lock,
    _make_signable_transaction_beef,
    _make_signable_transaction_result,
    _merge_prior_options,
    _recover_action_from_storage,
    _remove_unlock_scripts,
    _setup_wallet_payment_for_output,
    _verify_unlock_scripts,
    acquire_direct_certificate,
    build_signable_transaction,
    complete_signed_transaction,
    create_action,
    internalize_action,
    process_action,
    prove_certificate,
    sign_action,
)


class TestCreateAction:
    """Comprehensive tests for create_action function."""

    @pytest.fixture
    def mock_wallet(self) -> Mock:
        """Create a mock wallet."""
        wallet = Mock()
        wallet.create_action = Mock()
        wallet.create_action.return_value = {
            "txid": "test_txid",
            "tx": Mock(),
            "amount": 100000,
            "reference": "test_ref",
        }
        return wallet

    def test_create_action_success(self, mock_wallet: Mock) -> None:
        """Test successful create_action execution."""
        auth = {"identityKey": "test_key"}
        vargs = {"description": "test action", "outputs": [], "isNewTx": False}

        with patch("bsv_wallet_toolbox.signer.methods.process_action") as mock_process:
            mock_process.return_value = {"sendWithResults": [], "notDelayedResults": []}

            result = create_action(mock_wallet, auth, vargs)

            assert isinstance(result, CreateActionResultX)
            assert result.txid is None  # No prior tx created

    def test_create_action_wallet_error(self, mock_wallet: Mock) -> None:
        """Test create_action with wallet error."""
        auth = {"identityKey": "test_key"}
        vargs = {"description": "test action", "isNewTx": True}

        with patch("bsv_wallet_toolbox.signer.methods._create_new_tx") as mock_create_tx:
            mock_create_tx.side_effect = Exception("Wallet error")

            with pytest.raises(Exception, match="Wallet error"):
                create_action(mock_wallet, auth, vargs)


class TestBuildSignableTransaction:
    """Comprehensive tests for build_signable_transaction function."""

    @pytest.fixture
    def mock_wallet(self) -> Mock:
        """Create a mock wallet for build_signable_transaction tests."""
        wallet = Mock()
        wallet.get_client_change_key_pair.return_value = ["key1", "key2"]
        return wallet

    def test_build_signable_transaction_empty_inputs_outputs(self, mock_wallet: Mock) -> None:
        """Test build_signable_transaction with empty inputs and outputs."""
        dctr = {"inputs": [], "outputs": []}
        args = {"description": "test"}

        with patch("bsv_wallet_toolbox.signer.methods.Transaction") as mock_tx_class:
            mock_tx = Mock()
            mock_tx_class.return_value = mock_tx

            result = build_signable_transaction(dctr, args, mock_wallet)

            assert result is not None
            mock_tx_class.assert_called_once()

    def test_build_signable_transaction_with_storage_inputs_p2pkh(self, mock_wallet: Mock) -> None:
        """Test build_signable_transaction with P2PKH storage inputs."""
        dctr = {
            "inputs": [],
            "outputs": [{"satoshis": 1000, "lockingScript": "deadbeef", "vout": 0}],
            "storageInputs": [
                {
                    "vin": 0,
                    "type": "P2PKH",
                    "derivationPrefix": "m/44'/0'/0'/0",
                    "derivationSuffix": "0",
                    "senderIdentityKey": "key",
                    "sourceSatoshis": 2000,
                    "sourceLockingScript": "script",
                    "sourceTxid": "txid",
                    "sourceVout": 0,
                    "sourceTransaction": "deadbeef",
                }
            ],
        }
        args = {"description": "test"}

        with patch("bsv_wallet_toolbox.signer.methods.Transaction") as mock_tx_class:
            with patch("bsv_wallet_toolbox.signer.methods.Script") as mock_script_class:
                mock_tx = Mock()
                mock_script_class.return_value = Mock()
                mock_tx_class.return_value = mock_tx
                mock_tx.add_input = Mock()
                mock_tx.add_output = Mock()

                result = build_signable_transaction(dctr, args, mock_wallet)

                assert result is not None
                mock_wallet.get_client_change_key_pair.assert_called_once()

    def test_build_signable_transaction_with_storage_inputs_p2pkh_derivation_error(self, mock_wallet: Mock) -> None:
        """Test build_signable_transaction with derivation error in P2PKH."""
        dctr = {
            "inputs": [],
            "outputs": [{"satoshis": 1000, "lockingScript": "deadbeef"}],
            "storageInputs": [
                {
                    "vin": 0,
                    "type": "P2PKH",
                    "derivationPrefix": "invalid",
                    "derivationSuffix": "0",
                    "senderIdentityKey": "key",
                    "sourceSatoshis": 2000,
                    "sourceLockingScript": "script",
                    "sourceTxid": "txid",
                    "sourceVout": 0,
                    "sourceTransaction": "deadbeef",
                }
            ],
        }
        args = {"description": "test"}

        mock_wallet.derive_public_key.side_effect = Exception("Derivation error")

        with pytest.raises(Exception):
            build_signable_transaction(dctr, args, mock_wallet)

    def test_build_signable_transaction_unsupported_input_type(self, mock_wallet: Mock) -> None:
        """Test build_signable_transaction with unsupported input type."""
        dctr = {
            "inputs": [],
            "outputs": [{"satoshis": 1000, "lockingScript": "deadbeef"}],
            "storageInputs": [
                {
                    "vin": 0,
                    "type": "UNSUPPORTED_TYPE",
                    "derivationPrefix": "prefix",
                    "derivationSuffix": "suffix",
                    "senderIdentityKey": "key",
                    "sourceSatoshis": 1000,
                    "sourceLockingScript": "script",
                    "sourceTxid": "txid",
                    "sourceVout": 0,
                    "sourceTransaction": "deadbeef",
                }
            ],
        }
        args = {"description": "test"}

        with pytest.raises(Exception):  # Should raise WalletError for unsupported type
            build_signable_transaction(dctr, args, mock_wallet)

    def test_build_signable_transaction_with_change_outputs(self, mock_wallet: Mock) -> None:
        """Test build_signable_transaction with change outputs."""
        dctr = {
            "inputs": [],
            "outputs": [{"satoshis": 1000, "lockingScript": "deadbeef", "vout": 0}],
            "storageOutputs": [{"purpose": "change", "satoshis": 500, "vout": 1}],
        }
        args = {"description": "test"}

        with patch("bsv_wallet_toolbox.signer.methods.Transaction") as mock_tx_class:
            with patch("bsv_wallet_toolbox.signer.methods.validate_satoshis") as mock_validate:
                mock_validate.return_value = 2000
                mock_tx = Mock()
                mock_tx_class.return_value = mock_tx
                mock_tx.add_input = Mock()
                mock_tx.add_output = Mock()

                result = build_signable_transaction(dctr, args, mock_wallet)

                assert result is not None

    def test_build_signable_transaction_with_input_beef(self, mock_wallet: Mock) -> None:
        """Test build_signable_transaction with input BEEF."""
        dctr = {
            "inputs": [{"beef": "input_beef_data"}],
            "outputs": [{"satoshis": 1000, "lockingScript": "deadbeef", "vout": 0}],
        }
        args = {"inputBeef": "hex_beef_data", "isSignAction": True}

        with patch("bsv_wallet_toolbox.signer.methods.parse_beef") as mock_parse_beef:
            with patch("bsv_wallet_toolbox.signer.methods.Transaction") as mock_tx_class:
                mock_beef = Mock()
                mock_beef.find_txid.return_value = {"tx": "found_tx"}
                mock_parse_beef.return_value = mock_beef

                mock_tx = Mock()
                mock_tx_class.return_value = mock_tx

                result = build_signable_transaction(dctr, args, mock_wallet)

                assert result is not None
                mock_parse_beef.assert_called_once()

    def test_build_signable_transaction_input_beef_txid_not_found(self, mock_wallet: Mock) -> None:
        """Test build_signable_transaction with input BEEF but txid not found."""
        dctr = {"inputs": [{"beef": "input_beef_data"}], "outputs": [{"satoshis": 1000, "lockingScript": "deadbeef"}]}
        args = {"inputBeef": "hex_beef_data", "isSignAction": True}

        with patch("bsv_wallet_toolbox.signer.methods.parse_beef") as mock_parse_beef:
            with patch("bsv_wallet_toolbox.signer.methods.Transaction") as mock_tx_class:
                mock_beef = Mock()
                mock_beef.find_txid.return_value = None
                mock_parse_beef.return_value = mock_beef

                mock_tx = Mock()
                mock_tx_class.return_value = mock_tx

                with pytest.raises(Exception):  # Should raise error when txid not found in BEEF
                    build_signable_transaction(dctr, args, mock_wallet)


class TestCompleteSignedTransaction:
    """Comprehensive tests for complete_signed_transaction function."""

    @pytest.fixture
    def mock_wallet(self) -> Mock:
        """Create a mock wallet for complete_signed_transaction tests."""
        wallet = Mock()
        return wallet

    def test_complete_signed_transaction_success(self, mock_wallet: Mock) -> None:
        """Test successful complete_signed_transaction execution."""
        prior = Mock()
        prior.tx = Mock()
        input_mock = Mock()
        prior.tx.inputs = [input_mock]
        prior.inputs = [Mock(unlocking_script_length=10)]
        prior.args = {"inputs": [{"unlockingScriptLength": 10}]}
        prior.pdi = []

        spends = {
            0: {"unlockingScript": "deadbeef", "sequenceNumber": 0xFFFFFFFF}  # 8 hex chars = 4 bytes, within limit
        }

        with patch("bsv_wallet_toolbox.signer.methods.Transaction") as mock_tx_class:
            mock_tx = Mock()
            mock_tx_class.return_value = mock_tx

            result = complete_signed_transaction(prior, spends, mock_wallet)

            assert result is not None

    def test_complete_signed_transaction_unlock_script_too_long(self, mock_wallet: Mock) -> None:
        """Test complete_signed_transaction with unlock script exceeding length."""
        prior = Mock()
        prior.tx = Mock()
        input_mock = Mock()
        prior.tx.inputs = [input_mock]
        prior.inputs = [Mock(unlocking_script_length=5)]  # Max 5 bytes
        prior.args = {"inputs": [{"unlockingScriptLength": 5}]}
        prior.pdi = []

        spends = {
            0: {
                "unlockingScript": "deadbeef12345678",  # 16 hex chars = 8 bytes, exceeds limit
            }
        }

        with pytest.raises(Exception):  # Should raise WalletError
            complete_signed_transaction(prior, spends, mock_wallet)

    def test_complete_signed_transaction_missing_unlocking_script_length(self, mock_wallet: Mock) -> None:
        """Test complete_signed_transaction with missing unlocking_script_length."""
        prior = Mock()
        prior.tx = Mock()
        input_mock = Mock()
        prior.tx.inputs = [input_mock]
        prior.inputs = [Mock(unlocking_script_length=None)]
        prior.args = {"inputs": [{}]}  # Missing unlocking_script_length
        prior.pdi = []

        spends = {
            0: {
                "unlockingScript": "deadbeef",
            }
        }

        with pytest.raises(Exception):  # Should raise WalletError
            complete_signed_transaction(prior, spends, mock_wallet)

    def test_complete_signed_transaction_with_sequence_number(self, mock_wallet: Mock) -> None:
        """Test complete_signed_transaction with sequence number."""
        prior = Mock()
        prior.tx = Mock()
        input_mock = Mock()
        prior.tx.inputs = [input_mock]
        prior.inputs = [Mock(unlocking_script_length=10)]
        prior.args = {"inputs": [{"unlockingScriptLength": 10}]}
        prior.pdi = []

        spends = {0: {"unlockingScript": "deadbeef", "sequenceNumber": 12345}}

        result = complete_signed_transaction(prior, spends, mock_wallet)

        assert result is not None

    def test_complete_signed_transaction_multiple_inputs(self, mock_wallet: Mock) -> None:
        """Test complete_signed_transaction with multiple inputs."""
        prior = Mock()
        prior.tx = Mock()
        input_mock1 = Mock()
        input_mock2 = Mock()
        prior.tx.inputs = [input_mock1, input_mock2]
        prior.inputs = [Mock(unlocking_script_length=10), Mock(unlocking_script_length=15)]
        prior.args = {"inputs": [{"unlockingScriptLength": 10}, {"unlockingScriptLength": 15}]}
        prior.pdi = []

        spends = {0: {"unlockingScript": "deadbeef"}, 1: {"unlockingScript": "beefdead"}}

        result = complete_signed_transaction(prior, spends, mock_wallet)

        assert result is not None

    def test_complete_signed_transaction_empty_spends(self, mock_wallet: Mock) -> None:
        """Test complete_signed_transaction with empty spends dict."""
        prior = Mock()
        prior.tx = Mock()
        prior.tx.inputs = []
        prior.inputs = []
        prior.args = {"inputs": []}
        prior.pdi = []

        spends = {}

        result = complete_signed_transaction(prior, spends, mock_wallet)

        assert result is not None


class TestProcessAction:
    """Comprehensive tests for process_action function."""

    @pytest.fixture
    def mock_wallet(self) -> Mock:
        """Create a mock wallet for process_action tests."""
        wallet = Mock()
        return wallet

    def test_process_action_without_prior(self, mock_wallet: Mock) -> None:
        """Test process_action without prior action."""
        auth = {"identityKey": "test_key"}
        vargs = {"description": "test", "outputs": []}

        # Mock the storage process_action call to return a dict
        mock_wallet.storage.process_action.return_value = {"status": "success", "txid": "tx123"}

        with patch("bsv_wallet_toolbox.signer.methods._create_new_tx") as mock_create_tx:
            mock_prior = Mock()
            mock_prior.txid = "tx123"
            mock_prior.reference = "ref456"
            mock_create_tx.return_value = mock_prior

            with patch("bsv_wallet_toolbox.signer.methods.build_signable_transaction") as mock_build:
                with patch("bsv_wallet_toolbox.signer.methods.complete_signed_transaction") as mock_complete:
                    mock_build.return_value = (Mock(), 1000, [], "log")
                    mock_complete.return_value = Mock()

                    result = process_action(None, mock_wallet, auth, vargs)

                    assert isinstance(result, dict)
                    assert result["status"] == "success"
                    assert result["txid"] == "tx123"

    def test_process_action_with_prior_sign_action(self, mock_wallet: Mock) -> None:
        """Test process_action with prior action for signing."""
        prior = Mock()
        prior.txid = "prior_txid"
        prior.reference = "prior_ref"
        prior.tx = Mock()
        prior.tx.txid.return_value = "signed_txid"
        prior.tx.serialize.return_value = "raw_tx_data"
        prior.amount = 1000

        auth = {"identityKey": "test_key"}
        vargs = {"isSignAction": True, "spends": {}}

        # Mock the storage process_action call to return a dict
        mock_wallet.storage.process_action.return_value = {"status": "signed", "txid": "signed_txid"}

        result = process_action(prior, mock_wallet, auth, vargs)

        assert isinstance(result, dict)
        assert result["status"] == "signed"
        assert result["txid"] == "signed_txid"

    def test_process_action_with_prior_internalize_action(self, mock_wallet: Mock) -> None:
        """Test process_action with prior action for internalization."""
        prior = Mock()
        prior.txid = "prior_txid"
        prior.reference = "prior_ref"
        prior.tx = Mock()
        prior.tx.txid.return_value = "prior_txid"
        prior.tx.serialize.return_value = "raw_tx_data"

        auth = {"identityKey": "test_key"}
        vargs = {"isInternalizeAction": True}

        # Mock the storage process_action call to return a dict
        mock_wallet.storage.process_action.return_value = {"status": "internalized", "txid": "prior_txid"}

        result = process_action(prior, mock_wallet, auth, vargs)

        assert isinstance(result, dict)
        assert result["status"] == "internalized"
        assert result["txid"] == "prior_txid"

    def test_process_action_error_handling(self, mock_wallet: Mock) -> None:
        """Test process_action error handling."""
        auth = {"identityKey": "test_key"}
        vargs = {"description": "test"}

        with patch("bsv_wallet_toolbox.signer.methods._create_new_tx") as mock_create_tx:
            mock_create_tx.side_effect = Exception("Creation error")

            with pytest.raises(Exception, match="Creation error"):
                process_action(None, mock_wallet, auth, vargs)


class TestSignAction:
    """Comprehensive tests for sign_action function."""

    @pytest.fixture
    def mock_wallet(self) -> Mock:
        """Create a mock wallet for sign_action tests."""
        wallet = Mock()
        return wallet

    def test_sign_action_success(self, mock_wallet: Mock) -> None:
        """Test successful sign_action execution."""
        auth = {"identityKey": "test_key"}
        args = {"reference": "test_ref"}

        with patch("bsv_wallet_toolbox.signer.methods._recover_action_from_storage"):
            with patch("bsv_wallet_toolbox.signer.methods.process_action") as mock_process:
                with patch("bsv_wallet_toolbox.signer.methods.parse_beef") as mock_parse_beef:
                    with patch("bsv_wallet_toolbox.signer.methods._verify_unlock_scripts"):
                        prior = Mock()
                        prior.args = {"inputs": []}
                        prior.tx = Mock()
                        prior.tx.inputs = []
                        prior.tx.txid.return_value = "signed_txid"
                        prior.tx.serialize.return_value = "raw_tx_data"
                        prior.pdi = []
                        prior.dcr = {"inputBeef": b"test_beef_bytes"}
                        mock_wallet.pending_sign_actions.get.return_value = prior
                        mock_process.return_value = {"txid": "signed_txid"}
                        mock_parse_beef.return_value = Mock()

                        result = sign_action(mock_wallet, auth, args)

                        assert isinstance(result, dict)
                        assert result["txid"] == "signed_txid"

    def test_sign_action_no_prior_found(self, mock_wallet: Mock) -> None:
        """Test sign_action when no prior action is found."""
        auth = {"identityKey": "test_key"}
        args = {"reference": "test_ref"}

        with patch("bsv_wallet_toolbox.signer.methods._recover_action_from_storage") as mock_recover:
            mock_recover.return_value = None

            with pytest.raises(Exception):  # Should raise error for missing prior
                sign_action(mock_wallet, auth, args)


class TestInternalizeAction:
    """Comprehensive tests for internalize_action function."""

    @pytest.fixture
    def mock_wallet(self) -> Mock:
        """Create a mock wallet for internalize_action tests."""
        wallet = Mock()
        return wallet

    def test_internalize_action_success(self, mock_wallet: Mock) -> None:
        """Test successful internalize_action execution."""
        auth = {"identityKey": "test_key"}
        args = {
            "reference": "test_ref",
            "tx": b"test_beef_data",
            "outputs": [
                {
                    "amount": 1000,
                    "script": "test_script",
                    "protocol": "wallet payment",
                    "outputIndex": 0,
                    "paymentRemittance": {"derivationPrefix": "dGVzdA==", "derivationSuffix": "c3VmZml4"},
                }
            ],
            "description": "Test transaction description",
        }

        with patch("bsv_wallet_toolbox.signer.methods._recover_action_from_storage") as mock_recover:
            with patch("bsv_wallet_toolbox.signer.methods.process_action") as mock_process:
                with patch("bsv_wallet_toolbox.signer.methods.parse_beef_ex") as mock_parse_beef_ex:
                    with patch("bsv_wallet_toolbox.signer.methods._setup_wallet_payment_for_output"):
                        mock_recover.return_value = Mock()
                        mock_process.return_value = {"txid": "internalized_txid"}
                        beef_mock = Mock()
                        beef_mock.atomic_txid = "test_txid"
                        btx_mock = {"tx": Mock()}
                        btx_mock["tx"].outputs = [Mock()]
                        beef_mock.find_txid.return_value = btx_mock
                        # parse_beef_ex returns tuple (beef, subject_txid, subject_tx)
                        mock_parse_beef_ex.return_value = (beef_mock, "test_txid", btx_mock["tx"])
                        mock_wallet.storage.internalize_action.return_value = {"txid": "internalized_txid"}

                        result = internalize_action(mock_wallet, auth, args)

                    assert isinstance(result, dict)
                    assert result["txid"] == "internalized_txid"

    def test_internalize_action_no_prior_found(self, mock_wallet: Mock) -> None:
        """Test internalize_action when no prior action is found."""
        auth = {"identityKey": "test_key"}
        args = {"reference": "test_ref"}

        with patch("bsv_wallet_toolbox.signer.methods._recover_action_from_storage") as mock_recover:
            mock_recover.return_value = None

            with pytest.raises(Exception):  # Should raise error for missing prior
                internalize_action(mock_wallet, auth, args)


class TestAcquireDirectCertificate:
    """Comprehensive tests for acquire_direct_certificate function."""

    @pytest.fixture
    def mock_wallet(self) -> Mock:
        """Create a mock wallet for acquire_direct_certificate tests."""
        wallet = Mock()
        return wallet

    def test_acquire_direct_certificate_success(self, mock_wallet: Mock) -> None:
        """Test successful acquire_direct_certificate execution."""
        auth = {"identityKey": "test_key", "userId": "test_user"}
        vargs = {"type": "identity", "fields": {}, "subject": "test_subject", "certifier": "test_certifier"}

        with patch("bsv_wallet_toolbox.signer.methods.create_action") as mock_create:
            mock_create.return_value = {"txid": "cert_txid"}

            result = acquire_direct_certificate(mock_wallet, auth, vargs)

            assert isinstance(result, dict)
            assert result["type"] == "identity"
            assert result["subject"] == "test_subject"

    def test_acquire_direct_certificate_error(self, mock_wallet: Mock) -> None:
        """Test acquire_direct_certificate with validation error."""
        auth = {"identityKey": "test_key"}
        vargs = {"type": "identity"}

        with pytest.raises(ValueError, match="Certificate acquisition failed"):
            acquire_direct_certificate(mock_wallet, auth, vargs)


class TestProveCertificate:
    """Comprehensive tests for prove_certificate function."""

    @pytest.fixture
    def mock_wallet(self) -> Mock:
        """Create a mock wallet for prove_certificate tests."""
        wallet = Mock()
        return wallet

    def test_prove_certificate_success(self, mock_wallet: Mock) -> None:
        """Test successful prove_certificate execution."""
        auth = {"identityKey": "test_key"}
        vargs = {"certificateTxid": "cert_txid"}

        with patch("bsv_wallet_toolbox.signer.methods.create_action") as mock_create:
            mock_create.return_value = {"txid": "proof_txid"}
            mock_wallet.storage.list_certificates.return_value = {"certificates": [{"id": 1, "type": "test"}]}

            result = prove_certificate(mock_wallet, auth, vargs)

            assert isinstance(result, dict)
            assert "keyringForVerifier" in result

    def test_prove_certificate_error(self, mock_wallet: Mock) -> None:
        """Test prove_certificate with error."""
        auth = {"identityKey": "test_key"}
        vargs = {"certificateTxid": "cert_txid"}

        mock_wallet.storage.list_certificates.return_value = {"certificates": []}

        with pytest.raises(WalletError, match="Expected exactly one certificate match"):
            prove_certificate(mock_wallet, auth, vargs)


class TestHelperFunctions:
    """Comprehensive tests for helper functions."""

    def test_remove_unlock_scripts_basic(self) -> None:
        """Test _remove_unlock_scripts basic functionality."""
        args = {
            "inputs": [
                {"unlockingScript": "script1", "otherField": "value1"},
                {"unlockingScript": "script2", "otherField": "value2"},
                {"otherField": "value3"},  # No unlocking_script
            ]
        }

        result = _remove_unlock_scripts(args)

        assert result is not None
        assert len(result["inputs"]) == 3
        for input_data in result["inputs"]:
            assert "unlockingScript" not in input_data
            assert "otherField" in input_data

    def test_remove_unlock_scripts_none_values(self) -> None:
        """Test _remove_unlock_scripts with None values."""
        args = {"inputs": [{"unlockingScript": None}, {"unlockingScript": "valid_script"}]}

        result = _remove_unlock_scripts(args)

        assert result is not None
        assert len(result["inputs"]) == 2
        for input_data in result["inputs"]:
            assert "unlockingScript" not in input_data

    def test_remove_unlock_scripts_empty_inputs(self) -> None:
        """Test _remove_unlock_scripts with empty inputs."""
        args = {"inputs": []}

        result = _remove_unlock_scripts(args)

        assert result is not None
        assert result["inputs"] == []

    def test_make_change_lock_success(self) -> None:
        """Test _make_change_lock success."""
        out = {"keyID": "test_key"}
        dctr = {"derivationPrefix": "m/44'/0'/0'/1", "derivationSuffix": "0"}
        args = {}
        change_keys = Mock()
        wallet = Mock()

        with (
            patch("bsv_wallet_toolbox.signer.methods.Script") as mock_script_class,
            patch("bsv_wallet_toolbox.signer.methods.Protocol") as mock_protocol_class,
            patch("bsv_wallet_toolbox.signer.methods.Counterparty") as mock_counterparty_class,
            patch("bsv_wallet_toolbox.signer.methods.CounterpartyType") as mock_counterparty_type_class,
            patch("bsv_wallet_toolbox.signer.methods.P2PKH") as mock_p2pkh_class,
        ):
            mock_script = Mock()
            mock_script_class.return_value = mock_script

            # Mock protocol
            mock_protocol = Mock()
            mock_protocol_class.return_value = mock_protocol

            # Mock counterparty type
            mock_counterparty_type = Mock()
            mock_counterparty_type.self_ = "self_type"
            mock_counterparty_type_class.return_value = mock_counterparty_type

            # Mock counterparty
            mock_counterparty = Mock()
            mock_counterparty_class.return_value = mock_counterparty

            # Mock wallet key deriver
            mock_pub_key = Mock()
            mock_pub_key.to_hash160.return_value = b"test_hash"
            wallet.key_deriver.derive_public_key.return_value = mock_pub_key

            # Mock P2PKH
            mock_p2pkh = Mock()
            mock_p2pkh.lock.return_value = mock_script
            mock_p2pkh_class.return_value = mock_p2pkh

            result = _make_change_lock(out, dctr, args, change_keys, wallet)

            assert result is not None

    def test_make_change_lock_derivation_error(self) -> None:
        """Test _make_change_lock with derivation error."""
        out = {"keyID": "test_key"}
        dctr = {"derivationPrefix": "invalid", "derivationSuffix": "0"}
        args = {}
        change_keys = Mock()
        wallet = Mock()

        with (
            patch("bsv_wallet_toolbox.signer.methods.Script") as mock_script_class,
            patch("bsv_wallet_toolbox.signer.methods.Protocol") as mock_protocol_class,
            patch("bsv_wallet_toolbox.signer.methods.Counterparty") as mock_counterparty_class,
            patch("bsv_wallet_toolbox.signer.methods.CounterpartyType") as mock_counterparty_type_class,
            patch("bsv_wallet_toolbox.signer.methods.P2PKH") as mock_p2pkh_class,
        ):
            mock_script = Mock()
            mock_script_class.return_value = mock_script

            # Mock protocol
            mock_protocol = Mock()
            mock_protocol_class.return_value = mock_protocol

            # Mock counterparty type
            mock_counterparty_type = Mock()
            mock_counterparty_type.self_ = "self_type"
            mock_counterparty_type_class.return_value = mock_counterparty_type

            # Mock counterparty
            mock_counterparty = Mock()
            mock_counterparty_class.return_value = mock_counterparty

            # Mock wallet key deriver to raise exception
            wallet.key_deriver.derive_public_key.side_effect = Exception("Derivation failed")

            # Mock P2PKH for fallback
            mock_p2pkh = Mock()
            mock_p2pkh.lock.return_value = mock_script
            mock_p2pkh_class.return_value = mock_p2pkh

            with pytest.raises(WalletError, match="Unable to create change lock script"):
                _make_change_lock(out, dctr, args, change_keys, wallet)

    def test_verify_unlock_scripts_success(self) -> None:
        """Test _verify_unlock_scripts success."""
        from unittest.mock import AsyncMock

        txid = "test_txid"
        beef = Mock()

        # Set up beef mock structure
        beef_tx = Mock()
        mock_tx = Mock()
        # Create mock input with unlocking_script attribute
        mock_input = Mock()
        mock_input.unlocking_script = Mock()  # Has unlocking script
        mock_tx.inputs = [mock_input]
        # Mock verify as async method that returns True
        mock_tx.verify = AsyncMock(return_value=True)
        beef_tx.tx_obj = mock_tx
        beef.txs = {txid: beef_tx}

        with patch("bsv_wallet_toolbox.signer.methods.Beef") as mock_beef_class:
            mock_beef_instance = Mock()
            mock_beef_class.return_value = mock_beef_instance
            mock_beef_instance.verify_txid.return_value = True

            # Should not raise exception
            _verify_unlock_scripts(txid, beef)

    def test_verify_unlock_scripts_failure(self) -> None:
        """Test _verify_unlock_scripts failure."""
        txid = "test_txid"
        beef = Mock()

        with patch("bsv_wallet_toolbox.signer.methods.Beef") as mock_beef_class:
            mock_beef_instance = Mock()
            mock_beef_class.return_value = mock_beef_instance
            mock_beef_instance.verify_txid.return_value = False

            with pytest.raises(Exception):  # Should raise WalletError
                _verify_unlock_scripts(txid, beef)

    def test_merge_prior_options_basic(self) -> None:
        """Test _merge_prior_options basic functionality."""
        ca_vargs = {"options": {"acceptDelayedBroadcast": True}}
        sa_args = {"option2": "value2"}

        result = _merge_prior_options(ca_vargs, sa_args)

        assert isinstance(result, dict)
        assert "option2" in result
        assert "options" in result
        assert result["options"]["acceptDelayedBroadcast"] is True

    def test_merge_prior_options_empty(self) -> None:
        """Test _merge_prior_options with empty args."""
        result = _merge_prior_options({}, {})

        assert isinstance(result, dict)

    def test_merge_prior_options_overrides(self) -> None:
        """Test _merge_prior_options with overlapping keys."""
        ca_vargs = {"option1": "value1", "shared": "ca_value"}
        sa_args = {"option2": "value2", "shared": "sa_value"}

        result = _merge_prior_options(ca_vargs, sa_args)

        assert result["shared"] == "sa_value"  # sa_args should override

    def test_setup_wallet_payment_for_output_success(self) -> None:
        """Test _setup_wallet_payment_for_output success."""
        output_spec = {
            "satoshis": 1000,
            "paymentRemittance": {"derivationPrefix": "m/44'/0'/0'/1", "derivationSuffix": "0"},
        }
        tx = Mock()
        tx.outputs = [Mock()]
        # Set locking_script as a string to avoid isinstance check with mocked Script
        tx.outputs[0].locking_script = "test_script_hex"
        wallet = Mock()
        brc29_protocol_id = ["protocol1"]

        # Don't patch Script - it's used in isinstance() checks and needs to be a real type
        with (
            patch("bsv_wallet_toolbox.signer.methods.Protocol") as mock_protocol_class,
            patch("bsv_wallet_toolbox.signer.methods.Counterparty") as mock_counterparty_class,
            patch("bsv_wallet_toolbox.signer.methods.CounterpartyType") as mock_counterparty_type_class,
            patch("bsv_wallet_toolbox.signer.methods.P2PKH") as mock_p2pkh_class,
        ):
            mock_script = Mock()
            mock_script.hex.return_value = "test_script_hex"

            # Mock protocol
            mock_protocol = Mock()
            mock_protocol_class.return_value = mock_protocol

            # Mock counterparty type
            mock_counterparty_type = Mock()
            mock_counterparty_type.self_ = "self_type"
            mock_counterparty_type_class.return_value = mock_counterparty_type

            # Mock counterparty
            mock_counterparty = Mock()
            mock_counterparty_class.return_value = mock_counterparty

            # Mock wallet key deriver
            mock_priv_key = Mock()
            mock_pub_key = Mock()
            mock_pub_key.to_hash160.return_value = b"test_hash"
            mock_priv_key.public_key.return_value = mock_pub_key
            wallet.key_deriver.derive_private_key.return_value = mock_priv_key

            # Mock P2PKH
            mock_p2pkh = Mock()
            mock_p2pkh.lock.return_value = mock_script
            mock_p2pkh_class.return_value = mock_p2pkh

            # Make sure the expected script hex matches the output script hex
            # The output script is "test_script_hex", so expected should match
            mock_script.hex.return_value = "test_script_hex"

            # Should not raise exception
            _setup_wallet_payment_for_output(output_spec, tx, wallet, brc29_protocol_id)

    def test_setup_wallet_payment_for_output_missing_payment(self) -> None:
        """Test _setup_wallet_payment_for_output with missing payment."""
        output_spec = {"satoshis": 1000}  # No payment_remittance
        tx = Mock()
        wallet = Mock()
        brc29_protocol_id = ["protocol1"]

        with pytest.raises(Exception):  # Should raise error for missing payment
            _setup_wallet_payment_for_output(output_spec, tx, wallet, brc29_protocol_id)

    def test_recover_action_from_storage_found(self) -> None:
        """Test _recover_action_from_storage when action is found."""
        wallet = Mock()
        auth = {"identityKey": "test_key", "userId": "test_user"}
        reference = "test_ref"

        # Mock storage.find to return a transaction record
        tx_record = {"rawTx": b"test_raw_tx", "satoshis": 1000}
        wallet.storage.find.return_value = [tx_record]

        # Mock the Transaction import inside the function
        with patch("bsv.transaction.Transaction") as mock_transaction:
            mock_tx = Mock()
            mock_tx.txid.return_value = "test_txid"
            mock_transaction.from_bytes.return_value = mock_tx

            result = _recover_action_from_storage(wallet, auth, reference)

        assert result is not None
        assert hasattr(result, "tx")
        wallet.storage.find.assert_called_once()

    def test_recover_action_from_storage_not_found(self) -> None:
        """Test _recover_action_from_storage when action is not found."""
        wallet = Mock()
        auth = {"identityKey": "test_key"}
        reference = "test_ref"

        wallet.get_action_by_reference.return_value = None

        result = _recover_action_from_storage(wallet, auth, reference)

        assert result is None

    def test_recover_action_from_storage_error(self) -> None:
        """Test _recover_action_from_storage with error."""
        wallet = Mock()
        auth = {"identityKey": "test_key", "userId": "test_user"}
        reference = "test_ref"

        # Make storage.find raise an exception
        wallet.storage.find.side_effect = Exception("Storage error")

        result = _recover_action_from_storage(wallet, auth, reference)

        assert result is None


class TestTransactionHelpers:
    """Comprehensive tests for transaction helper functions."""

    def test_create_new_tx_success(self) -> None:
        """Test _create_new_tx success."""
        wallet = Mock()
        auth = {"identityKey": "test_key"}
        args = {"description": "test"}

        # Mock wallet.storage.create_action
        mock_result = {"txid": "tx123", "reference": "ref456", "inputs": [], "outputs": []}
        wallet.storage.create_action.return_value = mock_result

        # Mock wallet methods
        wallet.get_client_change_key_pair.return_value = Mock()

        result = _create_new_tx(wallet, auth, args)

        assert result.reference == "ref456"
        assert result.dcr["txid"] == "tx123"

    def test_make_signable_transaction_result(self) -> None:
        """Test _make_signable_transaction_result."""
        prior = Mock()
        prior.tx = Mock()
        prior.tx.txid.return_value = "test_txid"
        prior.tx.inputs = []
        prior.tx.serialize.return_value = b"test_tx_bytes"
        prior.dcr = {"noSendChangeOutputVouts": [], "reference": "test_ref"}
        wallet = Mock()
        wallet.pending_sign_actions = {}
        args = {}

        with patch("bsv_wallet_toolbox.signer.methods._make_signable_transaction_beef") as mock_beef:
            mock_beef.return_value = b"test_beef_bytes"

            result = _make_signable_transaction_result(prior, wallet, args)

        assert isinstance(result, CreateActionResultX)

    def test_make_signable_transaction_beef_success(self) -> None:
        """Test _make_signable_transaction_beef success."""
        tx = Mock()
        tx.inputs = []
        input_beef = b"beef_data"

        with patch("bsv_wallet_toolbox.signer.methods.Beef") as mock_beef_class:
            with patch("bsv_wallet_toolbox.signer.methods.Transaction") as mock_tx_class:
                mock_beef = Mock()
                mock_beef.to_binary_atomic.return_value = b"combined_beef"
                mock_beef_class.return_value = mock_beef

                mock_combined_tx = Mock()
                mock_tx_class.return_value = mock_combined_tx

                result = _make_signable_transaction_beef(tx, input_beef)

                assert result == b"combined_beef"
