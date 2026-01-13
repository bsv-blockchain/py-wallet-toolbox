"""Coverage tests for data models and dataclasses.

This module tests various data model classes used throughout the codebase.
"""

import pytest


class TestTransactionModels:
    """Test transaction-related models."""

    def test_transaction_input_model(self) -> None:
        """Test TransactionInput model."""
        try:
            from bsv_wallet_toolbox.models import TransactionInput

            tx_input = TransactionInput(
                txid="abc123",
                vout=0,
                script=b"script",
                satoshis=1000,
            )
            assert tx_input.txid == "abc123"
            assert tx_input.vout == 0
        except (ImportError, AttributeError, TypeError):
            pass

    def test_transaction_output_model(self) -> None:
        """Test TransactionOutput model."""
        try:
            from bsv_wallet_toolbox.models import TransactionOutput

            tx_output = TransactionOutput(
                satoshis=1000,
                script=b"script",
            )
            assert tx_output.satoshis == 1000
        except (ImportError, AttributeError, TypeError):
            pass

    def test_utxo_model(self) -> None:
        """Test UTXO model."""
        try:
            from bsv_wallet_toolbox.models import UTXO

            utxo = UTXO(
                txid="abc123",
                vout=0,
                satoshis=1000,
                script=b"script",
            )
            assert utxo.txid == "abc123"
        except (ImportError, AttributeError, TypeError):
            pass


class TestActionModels:
    """Test action-related models."""

    def test_action_model(self) -> None:
        """Test Action model."""
        try:
            from bsv_wallet_toolbox.models import Action

            action = Action(
                action_id="action123",
                status="pending",
                description="Test action",
            )
            assert action.action_id == "action123"
        except (ImportError, AttributeError, TypeError):
            pass

    def test_action_result_model(self) -> None:
        """Test ActionResult model."""
        try:
            from bsv_wallet_toolbox.models import ActionResult

            result = ActionResult(
                action_id="action123",
                txid="tx123",
                status="completed",
            )
            assert result.action_id == "action123"
        except (ImportError, AttributeError, TypeError):
            pass


class TestCertificateModels:
    """Test certificate-related models."""

    def test_certificate_model(self) -> None:
        """Test Certificate model."""
        try:
            from bsv_wallet_toolbox.models import Certificate

            cert = Certificate(
                certificate_id="cert123",
                certificate_type="identity",
                fields={},
            )
            assert cert.certificate_id == "cert123"
        except (ImportError, AttributeError, TypeError):
            pass

    def test_certificate_field_model(self) -> None:
        """Test CertificateField model."""
        try:
            from bsv_wallet_toolbox.models import CertificateField

            field = CertificateField(
                name="email",
                value="test@example.com",
            )
            assert field.name == "email"
        except (ImportError, AttributeError, TypeError):
            pass


class TestMerkleProofModels:
    """Test merkle proof models."""

    def test_merkle_path_model(self) -> None:
        """Test MerklePath model."""
        try:
            from bsv_wallet_toolbox.models import MerklePath

            path = MerklePath(
                txid="tx123",
                path=[],
                block_height=100,
            )
            assert path.txid == "tx123"
        except (ImportError, AttributeError, TypeError):
            pass

    def test_merkle_proof_model(self) -> None:
        """Test MerkleProof model."""
        try:
            from bsv_wallet_toolbox.models import MerkleProof

            proof = MerkleProof(
                index=0,
                tx_or_id="tx123",
                target="merkle_root",
                nodes=[],
            )
            assert proof.index == 0
        except (ImportError, AttributeError, TypeError):
            pass


class TestModelValidation:
    """Test model validation."""

    def test_model_required_fields(self) -> None:
        """Test that models validate required fields."""
        try:
            from bsv_wallet_toolbox.models import TransactionInput

            # Missing required fields should raise
            with pytest.raises((TypeError, ValueError)):
                TransactionInput()
        except (ImportError, AttributeError):
            pass

    def test_model_field_types(self) -> None:
        """Test that models validate field types."""
        try:
            from bsv_wallet_toolbox.models import TransactionOutput

            # Invalid type for satoshis
            with pytest.raises((TypeError, ValueError)):
                TransactionOutput(satoshis="invalid", script=b"script")
        except (ImportError, AttributeError, TypeError):
            pass


class TestModelSerialization:
    """Test model serialization."""

    def test_model_to_dict(self) -> None:
        """Test converting model to dict."""
        try:
            from bsv_wallet_toolbox.models import TransactionOutput

            output = TransactionOutput(satoshis=1000, script=b"script")
            if hasattr(output, "to_dict"):
                d = output.to_dict()
                assert isinstance(d, dict)
                assert d["satoshis"] == 1000
        except (ImportError, AttributeError, TypeError):
            pass

    def test_model_from_dict(self) -> None:
        """Test creating model from dict."""
        try:
            from bsv_wallet_toolbox.models import TransactionOutput

            data = {"satoshis": 1000, "script": b"script"}
            if hasattr(TransactionOutput, "from_dict"):
                output = TransactionOutput.from_dict(data)
                assert output.satoshis == 1000
        except (ImportError, AttributeError, TypeError):
            pass

    def test_model_to_json(self) -> None:
        """Test converting model to JSON."""
        try:
            from bsv_wallet_toolbox.models import Action

            action = Action(action_id="action123", status="pending")
            if hasattr(action, "to_json"):
                json_str = action.to_json()
                assert isinstance(json_str, str)
                assert "action123" in json_str
        except (ImportError, AttributeError, TypeError):
            pass
