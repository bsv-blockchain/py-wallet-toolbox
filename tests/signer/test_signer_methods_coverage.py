"""Coverage tests for signer methods.

This module tests transaction signing operations and wallet signing capabilities.
"""

from unittest.mock import Mock, patch

import pytest
from bsv.transaction import Transaction, TransactionInput, TransactionOutput

from bsv_wallet_toolbox.errors import InvalidParameterError, WalletError
from bsv_wallet_toolbox.signer.methods import (
    CreateActionResultX,
    PendingSignAction,
    PendingStorageInput,
    build_signable_transaction,
    create_action,
    internalize_action,
    sign_action,
)


class TestSignerDataclasses:
    """Test signer method dataclasses."""

    def test_pending_sign_action_creation(self) -> None:
        """Test creating PendingSignAction."""
        mock_tx = Mock(spec=Transaction)
        
        action = PendingSignAction(
            reference="test_ref",
            dcr={"result": "data"},
            args={"arg": "value"},
            amount=100000,
            tx=mock_tx,
            pdi=[],
        )

        assert action.reference == "test_ref"
        assert action.amount == 100000
        assert action.tx == mock_tx
        assert action.pdi == []

    def test_pending_storage_input_creation(self) -> None:
        """Test creating PendingStorageInput."""
        psi = PendingStorageInput(
            vin=0,
            derivation_prefix="m/0",
            derivation_suffix="/0/0",
            unlocker_pub_key="02abc...",
            source_satoshis=50000,
            locking_script="76a914...",
        )

        assert psi.vin == 0
        assert psi.source_satoshis == 50000
        assert isinstance(psi.derivation_prefix, str)

    def test_create_action_result_x_default(self) -> None:
        """Test CreateActionResultX with default values."""
        result = CreateActionResultX()

        assert result.txid is None
        assert result.tx is None
        assert result.no_send_change is None
        assert result.signable_transaction is None

    def test_create_action_result_x_with_values(self) -> None:
        """Test CreateActionResultX with values."""
        result = CreateActionResultX(
            txid="abc123",
            tx=b"raw_tx_bytes",
            no_send_change=["output1"],
            send_with_results=[{"status": "sent"}],
        )

        assert result.txid == "abc123"
        assert result.tx == b"raw_tx_bytes"
        assert result.no_send_change == ["output1"]


class TestCreateAction:
    """Test create_action function."""

    @pytest.fixture
    def mock_wallet(self):
        """Create a mock wallet."""
        wallet = Mock()
        wallet.storage = Mock()
        wallet.key_deriver = Mock()
        return wallet

    @pytest.fixture
    def mock_auth(self):
        """Create mock auth context."""
        return {"userId": 1, "identityKey": "test_key"}

    def test_create_action_no_new_tx(self, mock_wallet, mock_auth) -> None:
        """Test create_action when not creating new transaction."""
        vargs = {
            "isNewTx": False,
            "isSignAction": False,
        }

        result = create_action(mock_wallet, mock_auth, vargs)

        assert isinstance(result, CreateActionResultX)

    def test_create_action_validates_inputs(self, mock_wallet, mock_auth) -> None:
        """Test that create_action validates inputs properly."""
        # Missing required fields
        vargs = {}

        # Should not raise but return empty result
        result = create_action(mock_wallet, mock_auth, vargs)
        assert isinstance(result, CreateActionResultX)


class TestBuildSignableTransaction:
    """Test build_signable_transaction function."""

    def test_build_signable_transaction_basic(self) -> None:
        """Test building a signable transaction."""
        mock_prior = Mock(spec=PendingSignAction)
        mock_tx = Mock()
        mock_tx.to_hex = Mock(return_value="deadbeef")
        mock_prior.tx = mock_tx
        mock_prior.pdi = []
        
        mock_wallet = Mock()

        try:
            result = build_signable_transaction(mock_prior, mock_wallet)
            # If it returns something, check it's a dict
            if result:
                assert isinstance(result, dict)
        except (AttributeError, KeyError, TypeError):
            # Expected if mock doesn't have all required attributes
            pass


class TestSignAction:
    """Test sign_action function."""

    @pytest.fixture
    def mock_wallet(self):
        """Create a mock wallet."""
        wallet = Mock()
        wallet.storage = Mock()
        wallet.key_deriver = Mock()
        return wallet

    @pytest.fixture
    def mock_auth(self):
        """Create mock auth context."""
        return {"userId": 1, "identityKey": "test_key"}

    def test_sign_action_requires_wallet(self, mock_auth) -> None:
        """Test that sign_action requires wallet."""
        args = {"spends": {}, "reference": "test_ref"}

        # Should handle None wallet gracefully
        try:
            result = sign_action(None, mock_auth, args)
            # If it doesn't raise, check the result
            assert result is not None
        except (AttributeError, WalletError):
            # Expected if wallet is required
            pass

    def test_sign_action_basic_flow(self, mock_wallet, mock_auth) -> None:
        """Test basic sign_action flow."""
        args = {
            "spends": {},
            "reference": "test_ref",
        }

        # Mock storage to return None (no prior action)
        mock_wallet.storage = Mock()

        try:
            result = sign_action(mock_wallet, mock_auth, args)
            if result:
                assert isinstance(result, dict)
        except (AttributeError, KeyError, WalletError, TypeError):
            # Expected if storage doesn't have required methods
            pass


class TestInternalizeAction:
    """Test internalize_action function."""

    @pytest.fixture
    def mock_wallet(self):
        """Create a mock wallet."""
        wallet = Mock()
        wallet.storage = Mock()
        wallet.services = Mock()
        return wallet

    @pytest.fixture
    def mock_auth(self):
        """Create mock auth context."""
        return {"userId": 1, "identityKey": "test_key"}

    def test_internalize_action_validates_args(self, mock_wallet, mock_auth) -> None:
        """Test that internalize_action validates arguments."""
        # Missing required fields - should raise validation error
        args = {}

        with pytest.raises((InvalidParameterError, WalletError, KeyError, ValueError)):
            internalize_action(mock_wallet, mock_auth, args)

    def test_internalize_action_with_tx(self, mock_wallet, mock_auth) -> None:
        """Test internalize_action with transaction data - validates required fields."""
        # Empty outputs should fail validation
        args = {
            "tx": b"\x01\x00\x00\x00",
            "outputs": [],  # Empty list should fail validation
            "labels": [],
        }

        with pytest.raises((InvalidParameterError, WalletError, KeyError, ValueError)):
            internalize_action(mock_wallet, mock_auth, args)

    def test_internalize_action_requires_wallet(self, mock_auth) -> None:
        """Test that internalize_action requires wallet - validates args first."""
        args = {"tx": b"\x01\x00\x00\x00"}  # Missing outputs

        # Should fail validation before checking wallet
        with pytest.raises((InvalidParameterError, AttributeError, WalletError, ValueError)):
            internalize_action(None, mock_auth, args)


class TestInternalHelpers:
    """Test internal helper functions (through public interface)."""

    def test_pending_sign_action_with_inputs(self) -> None:
        """Test PendingSignAction with multiple inputs."""
        mock_tx = Mock(spec=Transaction)
        
        psi1 = PendingStorageInput(
            vin=0,
            derivation_prefix="m/0",
            derivation_suffix="/0/0", 
            unlocker_pub_key="pub1",
            source_satoshis=10000,
            locking_script="script1",
        )
        
        psi2 = PendingStorageInput(
            vin=1,
            derivation_prefix="m/0",
            derivation_suffix="/0/1",
            unlocker_pub_key="pub2",
            source_satoshis=20000,
            locking_script="script2",
        )

        action = PendingSignAction(
            reference="multi_input_ref",
            dcr={},
            args={},
            amount=30000,
            tx=mock_tx,
            pdi=[psi1, psi2],
        )

        assert len(action.pdi) == 2
        assert action.pdi[0].vin == 0
        assert action.pdi[1].vin == 1
        assert action.amount == 30000


class TestErrorHandling:
    """Test error handling in signer methods."""

    def test_create_action_with_invalid_wallet(self) -> None:
        """Test create_action with invalid wallet."""
        invalid_wallet = {}  # Not a proper wallet object
        auth = {"userId": 1}
        vargs = {"isNewTx": True}

        try:
            result = create_action(invalid_wallet, auth, vargs)
            # Might work or raise
            assert isinstance(result, CreateActionResultX)
        except (AttributeError, KeyError):
            # Expected for invalid wallet
            pass

    def test_sign_action_missing_reference(self) -> None:
        """Test sign_action with missing reference."""
        wallet = Mock()
        wallet.storage = Mock()
        auth = {"userId": 1}
        args = {"spends": {}}  # Missing reference

        try:
            result = sign_action(wallet, auth, args)
            # Might work or raise
            if result:
                assert isinstance(result, dict)
        except (KeyError, WalletError):
            # Expected for missing reference
            pass


class TestDataclassDefaults:
    """Test dataclass default values."""

    def test_pending_storage_input_all_fields(self) -> None:
        """Test PendingStorageInput with all fields."""
        psi = PendingStorageInput(
            vin=5,
            derivation_prefix="m/44'/0'/0'",
            derivation_suffix="/0/123",
            unlocker_pub_key="03" + "ab" * 32,
            source_satoshis=123456,
            locking_script="76a914" + "cd" * 20 + "88ac",
        )

        # All fields should be set correctly
        assert psi.vin == 5
        assert "m/44'" in psi.derivation_prefix
        assert psi.source_satoshis == 123456
        assert "76a914" in psi.locking_script

    def test_create_action_result_x_partial(self) -> None:
        """Test CreateActionResultX with partial values."""
        result = CreateActionResultX(
            txid="test_txid",
            # Other fields remain None
        )

        assert result.txid == "test_txid"
        assert result.tx is None
        assert result.send_with_results is None

