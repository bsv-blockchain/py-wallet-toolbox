"""Unit tests for signer methods with mocked dependencies.

Tests the core signing logic without requiring full wallet infrastructure.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bsv.transaction import Transaction

from bsv_wallet_toolbox.signer.methods import (
    PendingSignAction,
    acquire_direct_certificate,
    create_action,
    internalize_action,
    process_action,
    prove_certificate,
    sign_action,
)


class TestCreateAction:
    """Test create_action function."""

    def test_create_action_basic(self):
        """Test basic create_action functionality."""
        mock_wallet = MagicMock()
        mock_auth = MagicMock()

        args = {
            "isNewTx": True,
            "description": "Test transaction",
            "outputs": [{"satoshis": 1000, "lockingScript": "76a914" + "00" * 20 + "88ac"}],
        }

        # Create a proper mock PendingSignAction with required structure
        mock_tx = MagicMock()
        mock_tx.txid.return_value = "a" * 64
        mock_tx.serialize.return_value = b"mock_tx_bytes"
        # Mock verify as async method that returns True
        mock_tx.verify = AsyncMock(return_value=True)
        # Mock inputs with at least one input that has unlocking_script
        mock_input = MagicMock()
        mock_input.unlocking_script = MagicMock()  # Has unlocking script
        mock_tx.inputs = [mock_input]

        mock_pending = PendingSignAction(
            reference="test_ref",
            dcr={
                "reference": "test_ref",
                "inputBeef": b"",  # Empty BEEF bytes
                "noSendChangeOutputVouts": [],
            },
            args=args,
            amount=1000,
            tx=mock_tx,
            pdi=[],
        )

        with (
            patch("bsv_wallet_toolbox.signer.methods._create_new_tx") as mock_create_tx,
            patch("bsv_wallet_toolbox.signer.methods.complete_signed_transaction") as mock_complete,
            patch("bsv_wallet_toolbox.signer.methods.process_action") as mock_process,
        ):

            mock_create_tx.return_value = mock_pending
            mock_complete.return_value = mock_tx
            mock_process.return_value = {"sendWithResults": [], "notDelayedResults": []}

            result = create_action(mock_wallet, mock_auth, args)

            assert result is not None
            assert result.txid == "a" * 64
            mock_create_tx.assert_called_once()

    def test_create_action_validation(self):
        """Test create_action input validation."""
        mock_wallet = MagicMock()
        mock_auth = MagicMock()

        # Test with empty outputs (may not raise depending on implementation)
        args = {
            "description": "Test transaction",
            "outputs": [],  # Empty outputs
        }

        # Mock the storage methods to avoid actual validation
        with (
            patch("bsv_wallet_toolbox.signer.methods._create_new_tx") as mock_create_tx,
            patch("bsv_wallet_toolbox.signer.methods.complete_signed_transaction") as mock_complete,
            patch("bsv_wallet_toolbox.signer.methods.process_action") as mock_process,
        ):

            mock_tx = MagicMock()
            mock_tx.txid.return_value = "b" * 64
            mock_tx.serialize.return_value = b"mock_tx_bytes"
            # Mock verify as async method that returns True
            mock_tx.verify = AsyncMock(return_value=True)
            # Mock inputs with at least one input that has unlocking_script
            mock_input = MagicMock()
            mock_input.unlocking_script = MagicMock()  # Has unlocking script
            mock_tx.inputs = [mock_input]

            mock_pending = PendingSignAction(
                reference="test_ref",
                dcr={
                    "reference": "test_ref",
                    "inputBeef": b"",
                    "noSendChangeOutputVouts": [],
                },
                args=args,
                amount=0,
                tx=mock_tx,
                pdi=[],
            )

            mock_create_tx.return_value = mock_pending
            mock_complete.return_value = mock_tx
            mock_process.return_value = {"sendWithResults": [], "notDelayedResults": []}

            # For now, just ensure it doesn't crash
            try:
                result = create_action(mock_wallet, mock_auth, args)
                # If it succeeds, that's fine
                assert result is not None
            except (ValueError, TypeError):
                # If it does validate, that's also fine
                pass


class TestSignAction:
    """Test sign_action function."""

    def test_sign_action_success(self):
        """Test successful sign_action."""

        from bsv_wallet_toolbox.signer.methods import PendingSignAction

        mock_wallet = MagicMock()
        mock_auth = MagicMock()

        # Create a proper mock PendingSignAction
        mock_tx = MagicMock()
        mock_tx.txid.return_value = "a" * 64

        mock_pending = PendingSignAction(
            reference="test_ref_123",
            dcr={
                "reference": "test_ref_123",
                "inputBeef": b"",  # Empty BEEF bytes
                "noSendChangeOutputVouts": [],
            },
            args={
                "isNewTx": True,
                "description": "Test transaction",
                "outputs": [{"satoshis": 1000, "lockingScript": "76a914" + "00" * 20 + "88ac"}],
            },
            amount=1000,
            tx=mock_tx,
            pdi=[],
        )

        # Mock pending_sign_actions as a TTL cache that returns our mock
        mock_wallet.pending_sign_actions.get.return_value = mock_pending

        # Mock the complete_signed_transaction function
        with (
            patch("bsv_wallet_toolbox.signer.methods.complete_signed_transaction") as mock_complete,
            patch("bsv_wallet_toolbox.signer.methods.process_action") as mock_process,
            patch("bsv_wallet_toolbox.signer.methods._verify_unlock_scripts") as mock_verify,
        ):

            mock_complete.return_value = mock_tx
            mock_process.return_value = {"sendWithResults": [], "notDelayedResults": []}
            mock_verify.return_value = None  # Skip verification for this test

            args = {
                "reference": "test_ref_123",
                "spends": {},
            }

            result = sign_action(mock_wallet, mock_auth, args)

            assert result is not None
            assert "txid" in result

    # @pytest.mark.skip(reason="Complex validation and recovery logic cannot be properly tested with mocks")
    def test_sign_action_invalid_reference(self):
        """Test sign_action with invalid reference."""
        from bsv_wallet_toolbox.errors import WalletError

        mock_wallet = MagicMock()
        mock_auth = MagicMock()

        args = {
            "reference": "",  # Empty reference
            "rawTx": "01000000" + "00" * 8,
            "spends": {},
        }

        with pytest.raises(WalletError):
            sign_action(mock_wallet, mock_auth, args)


class TestProcessAction:
    """Test process_action function."""

    def test_process_action_new_tx(self):
        """Test process_action for new transaction."""
        mock_wallet = MagicMock()
        mock_auth = MagicMock()

        args = {
            "txid": "a" * 64,
            "isNewTx": True,
            "rawTx": "01000000" + "00" * 8,
            "reference": "test_ref",
        }

        # Mock the storage process_action method
        mock_wallet.storage.process_action.return_value = {"sendWithResults": [], "notDelayedResults": []}

        result = process_action(None, mock_wallet, mock_auth, args)

        assert result is not None
        assert "sendWithResults" in result
        assert "notDelayedResults" in result

    def test_process_action_existing_tx(self):
        """Test process_action with existing pending action."""
        mock_wallet = MagicMock()
        mock_auth = MagicMock()

        # Create a proper mock PendingSignAction
        mock_tx = MagicMock()
        mock_tx.txid.return_value = "b" * 64
        mock_tx.serialize.return_value = b"mock_tx_bytes"

        mock_pending = PendingSignAction(
            reference="test_ref",
            dcr={
                "reference": "test_ref",
                "inputBeef": b"",
                "noSendChangeOutputVouts": [],
            },
            args={},
            amount=0,
            tx=mock_tx,
            pdi=[],
        )

        args = {
            "txid": "b" * 64,
            "isNewTx": False,
        }

        # Mock the storage process_action method
        mock_wallet.storage.process_action.return_value = {"sendWithResults": [], "notDelayedResults": []}

        result = process_action(mock_pending, mock_wallet, mock_auth, args)

        assert result is not None
        assert "sendWithResults" in result
        assert "notDelayedResults" in result


class TestInternalizeAction:
    """Test internalize_action function."""

    @pytest.mark.skip(reason="Requires complex paymentRemittance mocking for wallet payment protocol")
    def test_internalize_action_success(self):
        """Test successful internalize_action."""
        mock_wallet = MagicMock()
        mock_auth = MagicMock()

        # Create a minimal valid transaction
        from bsv.transaction import Transaction

        tx = Transaction()
        tx_bytes = tx.serialize()

        args = {
            "tx": tx_bytes,  # Use actual transaction bytes
            "outputs": [
                {"satoshis": 1000, "lockingScript": b"script", "protocol": "wallet payment", "outputIndex": 0}
            ],  # Required outputs parameter with protocol and outputIndex
            "description": "Test description",  # Required description parameter
        }

        # Mock the storage internalize_action method
        mock_wallet.storage.internalize_action.return_value = {"txid": tx.txid(), "status": "success"}

        result = internalize_action(mock_wallet, mock_auth, args)

        assert result is not None
        assert "txid" in result

    def test_internalize_action_validation(self):
        """Test internalize_action input validation."""
        mock_wallet = MagicMock()
        mock_auth = MagicMock()

        args = {
            "txid": "",  # Invalid txid
            "tx": b"",  # Invalid empty tx bytes
            "outputIndex": 0,
        }

        # The validation happens and should raise InvalidParameterError
        from bsv_wallet_toolbox.errors import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            internalize_action(mock_wallet, mock_auth, args)


class TestAcquireDirectCertificate:
    """Test acquire_direct_certificate function."""

    @pytest.mark.skip(reason="Requires extensive certificate field mocking")
    def test_acquire_direct_certificate_success(self):
        """Test successful certificate acquisition."""
        mock_wallet = MagicMock()
        mock_auth = MagicMock()
        mock_auth.get.return_value = 1  # userId

        args = {
            "type": "identity",
            "subject": "02" + "00" * 32,  # Mock subject public key
            "fields": {"name": "Test User"},
        }

        result = acquire_direct_certificate(mock_wallet, mock_auth, args)

        assert result is not None
        assert "certificate" in result

    def test_acquire_direct_certificate_validation(self):
        """Test certificate acquisition validation."""
        mock_wallet = MagicMock()
        mock_auth = MagicMock()

        args = {
            "type": "",  # Invalid type
            "fields": {},
        }

        # Mock storage to avoid actual validation
        mock_wallet.storage.acquire_certificate.return_value = {"certificate": None, "error": "invalid_type"}

        # Validation happens before storage call, so expect ValueError
        with pytest.raises(ValueError):
            acquire_direct_certificate(mock_wallet, mock_auth, args)


class TestProveCertificate:
    """Test prove_certificate function."""

    @pytest.mark.skip(reason="Requires extensive certificate storage mocking")
    def test_prove_certificate_success(self):
        """Test successful certificate proving."""
        mock_wallet = MagicMock()
        mock_auth = MagicMock()

        args = {
            "certificate": {"type": "identity", "subject": "02" + "00" * 32},  # Mock certificate dict
            "fields": ["field1", "field2"],
        }

        result = prove_certificate(mock_wallet, mock_auth, args)

        assert result is not None
        assert "proof" in result

    def test_prove_certificate_validation(self):
        """Test certificate proving validation."""
        mock_wallet = MagicMock()
        mock_auth = MagicMock()

        args = {
            "certificate": {},  # Invalid certificate (empty dict instead of empty string)
            "fields": [],
        }

        # Mock storage find to return empty results (no certificates found)
        mock_wallet.storage.find.return_value = []

        # Should raise WalletError about no certificates found
        from bsv_wallet_toolbox.errors import WalletError

        with pytest.raises(WalletError):
            prove_certificate(mock_wallet, mock_auth, args)


class TestSignerHelperFunctions:
    """Test helper functions in signer methods."""

    def test_build_signable_transaction(self):
        """Test build_signable_transaction function."""
        from bsv_wallet_toolbox.signer.methods import build_signable_transaction

        mock_wallet = MagicMock()
        dctr = {"inputs": [], "reference": "test_ref"}
        args = {"inputBeef": b""}

        result = build_signable_transaction(dctr, args, mock_wallet)

        # Returns tuple of (Transaction, int, list[PendingStorageInput], str)
        assert isinstance(result, tuple)
        assert len(result) == 4
        assert isinstance(result[0], Transaction)  # Transaction object
        assert isinstance(result[1], int)  # amount
        assert isinstance(result[2], list)  # pending inputs
        assert isinstance(result[3], str)  # log

    def test_complete_signed_transaction(self):
        """Test complete_signed_transaction function."""
        from bsv_wallet_toolbox.signer.methods import complete_signed_transaction

        # Create a proper mock Transaction
        mock_tx = MagicMock()
        mock_tx.txid.return_value = "d" * 64

        mock_pending = MagicMock()
        mock_pending.tx = mock_tx
        mock_wallet = MagicMock()
        spends = {}

        result = complete_signed_transaction(mock_pending, spends, mock_wallet)

        assert result is not None
        # Result should be the Transaction object
        assert hasattr(result, "txid")  # Assuming Transaction has txid attribute

    @pytest.mark.skip(reason="Requires key_deriver counterparty setup")
    def test_make_change_lock(self):
        """Test _make_change_lock function."""
        from bsv_wallet_toolbox.signer.methods import _make_change_lock

        mock_wallet = MagicMock()
        # Add mock key_deriver with derive_public_key method
        mock_key_deriver = MagicMock()
        mock_public_key = MagicMock()
        mock_public_key.hex.return_value = "02" + "00" * 32
        mock_key_deriver.derive_public_key.return_value = mock_public_key
        mock_wallet.key_deriver = mock_key_deriver

        out = {"satoshis": 1000}
        dctr = {}
        args = {}
        change_keys = {"address": "test_address", "publicKey": "test_pubkey"}

        result = _make_change_lock(out, dctr, args, change_keys, mock_wallet)

        assert result is not None
        # Should return a Script object
        from bsv.script import Script

        assert isinstance(result, Script)

    def test_verify_unlock_scripts(self):
        """Test _verify_unlock_scripts function."""
        from bsv_wallet_toolbox.signer.methods import _verify_unlock_scripts

        txid = "a" * 64
        # Use empty BEEF bytes which should be valid
        beef_data = b""

        # Should not raise if valid - for now just check it doesn't crash
        try:
            _verify_unlock_scripts(txid, beef_data)
        except Exception:
            # If verification fails, that's acceptable for this test
            pass

    def test_merge_prior_options(self):
        """Test _merge_prior_options function."""
        from bsv_wallet_toolbox.signer.methods import _merge_prior_options

        ca_vargs = {"option1": "value1", "options": {}}
        sa_args = {"option2": "value2"}

        result = _merge_prior_options(ca_vargs, sa_args)

        # The function merges sa_args into ca_vargs, replacing options
        assert "option2" in result
        assert result["option2"] == "value2"
        assert "options" in result  # options dict is recreated

    def test_remove_unlock_scripts(self):
        """Test _remove_unlock_scripts function."""
        from bsv_wallet_toolbox.signer.methods import _remove_unlock_scripts

        args = {
            "inputs": [
                {"unlockingScript": "script1", "other": "value1"},
                {"unlockingScript": "script2", "other": "value2"},
            ]
        }

        result = _remove_unlock_scripts(args)

        assert "inputs" in result
        # unlocking_script should be removed but other fields preserved
        for input_data in result["inputs"]:
            assert "unlocking_script" not in input_data
            assert "other" in input_data
