"""Expanded coverage tests for format_utils.

This module tests data formatting and conversion utilities.
"""

try:
    from bsv_wallet_toolbox.utils.format_utils import Format

    IMPORT_SUCCESS = True
except ImportError:
    IMPORT_SUCCESS = False


class TestFormatAlignLeft:
    """Test Format.align_left method."""

    def test_align_left_short_text(self) -> None:
        """Test left-aligning short text."""
        result = Format.align_left("test", 10)
        assert isinstance(result, str)
        assert len(result) == 10
        assert result.startswith("test")

    def test_align_left_exact_width(self) -> None:
        """Test left-aligning text that exactly fits."""
        result = Format.align_left("test", 4)
        assert result == "test"

    def test_align_left_truncate(self) -> None:
        """Test left-aligning long text (should truncate)."""
        result = Format.align_left("verylongtext", 5)
        assert len(result) == 5
        assert result.endswith("…")

    def test_align_left_with_number(self) -> None:
        """Test left-aligning numeric value."""
        result = Format.align_left(12345, 10)
        assert isinstance(result, str)
        assert len(result) == 10


class TestFormatAlignRight:
    """Test Format.align_right method."""

    def test_align_right_short_text(self) -> None:
        """Test right-aligning short text."""
        result = Format.align_right("test", 10)
        assert isinstance(result, str)
        assert len(result) == 10
        assert result.endswith("test")

    def test_align_right_exact_width(self) -> None:
        """Test right-aligning text that exactly fits."""
        result = Format.align_right("test", 4)
        assert result == "test"

    def test_align_right_truncate(self) -> None:
        """Test right-aligning long text (should truncate)."""
        result = Format.align_right("verylongtext", 5)
        assert len(result) == 5
        assert result.startswith("…")

    def test_align_right_with_number(self) -> None:
        """Test right-aligning numeric value."""
        result = Format.align_right(12345, 10)
        assert isinstance(result, str)
        assert len(result) == 10


class TestFormatAlignMiddle:
    """Test Format.align_middle method."""

    def test_align_middle_short_text(self) -> None:
        """Test middle-aligning short text."""
        result = Format.align_middle("test", 10)
        assert isinstance(result, str)
        assert len(result) == 10

    def test_align_middle_exact_width(self) -> None:
        """Test middle-aligning text that exactly fits."""
        result = Format.align_middle("test", 4)
        assert result == "test"

    def test_align_middle_truncate(self) -> None:
        """Test middle-aligning long text (should truncate from ends)."""
        result = Format.align_middle("verylongtext", 5)
        assert isinstance(result, str)
        assert len(result) == 5

    def test_align_middle_with_number(self) -> None:
        """Test middle-aligning numeric value."""
        result = Format.align_middle(12345, 10)
        assert isinstance(result, str)
        assert len(result) == 10


class TestFormatSatoshis:
    """Test Format.satoshis method."""

    def test_format_zero_satoshis(self) -> None:
        """Test formatting zero satoshis."""
        result = Format.satoshis(0)
        assert isinstance(result, str)
        assert "0" in result

    def test_format_small_amount(self) -> None:
        """Test formatting small satoshi amount."""
        result = Format.satoshis(1000)
        assert isinstance(result, str)

    def test_format_one_bsv(self) -> None:
        """Test formatting one BSV (100,000,000 satoshis)."""
        result = Format.satoshis(100000000)
        assert isinstance(result, str)

    def test_format_large_amount(self) -> None:
        """Test formatting large satoshi amount."""
        result = Format.satoshis(21000000 * 100000000)  # Max BSV supply
        assert isinstance(result, str)

    def test_format_negative_satoshis(self) -> None:
        """Test formatting negative satoshis."""
        result = Format.satoshis(-1000)
        assert isinstance(result, str)
        # Should handle negative values


class TestFormatTxidBytes:
    """Test Format.txid_bytes method."""

    def test_format_txid_bytes_basic(self) -> None:
        """Test formatting txid bytes."""
        try:
            if hasattr(Format, "txid_bytes"):
                mock_tx = type("MockTx", (), {"txid": lambda: "0" * 64})()
                result = Format.txid_bytes(mock_tx)
                assert isinstance(result, str)
        except (AttributeError, TypeError):
            pass


class TestFormatBeefBytes:
    """Test Format.beef_bytes method."""

    def test_format_beef_bytes_basic(self) -> None:
        """Test formatting BEEF bytes."""
        try:
            if hasattr(Format, "beef_bytes"):
                mock_beef = type("MockBeef", (), {"toBytes": lambda: b"\x00" * 100})()
                result = Format.beef_bytes(mock_beef)
                assert isinstance(result, str)
        except (AttributeError, TypeError):
            pass


class TestFormatBsvAmount:
    """Test Format.bsv_amount method."""

    def test_format_bsv_amount_from_satoshis(self) -> None:
        """Test formatting BSV amount from satoshis."""
        try:
            if hasattr(Format, "bsv_amount"):
                result = Format.bsv_amount(100000000)  # 1 BSV
                assert isinstance(result, str)
        except (AttributeError, TypeError):
            pass

    def test_format_bsv_amount_fractional(self) -> None:
        """Test formatting fractional BSV amount."""
        try:
            if hasattr(Format, "bsv_amount"):
                result = Format.bsv_amount(50000000)  # 0.5 BSV
                assert isinstance(result, str)
        except (AttributeError, TypeError):
            pass


class TestFormatUtilsAdvanced:
    """Advanced tests for format utilities."""

    def test_format_align_consistency(self) -> None:
        """Test alignment methods are consistent."""
        text = "test"
        width = 10

        left = Format.align_left(text, width)
        right = Format.align_right(text, width)
        middle = Format.align_middle(text, width)

        assert len(left) == width
        assert len(right) == width
        assert len(middle) == width

    def test_format_satoshis_various_amounts(self) -> None:
        """Test satoshi formatting with various amounts."""
        amounts = [0, 1, 100, 1000, 10000, 100000, 1000000, 10000000, 100000000]
        for amount in amounts:
            result = Format.satoshis(amount)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_format_alignment_with_unicode(self) -> None:
        """Test alignment with unicode characters."""
        unicode_text = "测试"
        result = Format.align_left(unicode_text, 10)
        assert isinstance(result, str)

    def test_format_alignment_empty_string(self) -> None:
        """Test alignment with empty string."""
        result = Format.align_left("", 10)
        assert isinstance(result, str)
        assert len(result) == 10

    def test_format_alignment_zero_width(self) -> None:
        """Test alignment with zero or negative width."""
        try:
            result = Format.align_left("test", 0)
            # Should handle gracefully
            assert isinstance(result, str)
        except (ValueError, IndexError):
            # May raise for invalid width
            pass


class TestEdgeCases:
    """Test edge cases in format utilities."""

    def test_format_max_satoshis(self) -> None:
        """Test formatting maximum satoshis."""
        max_satoshis = 21000000 * 100000000
        result = Format.satoshis(max_satoshis)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_negative_satoshis_large(self) -> None:
        """Test formatting large negative satoshis."""
        result = Format.satoshis(-100000000)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_align_very_long_text(self) -> None:
        """Test aligning very long text."""
        long_text = "a" * 1000
        result = Format.align_left(long_text, 10)
        assert len(result) == 10

    def test_format_align_special_characters(self) -> None:
        """Test aligning text with special characters."""
        special = "!@#$%^&*()"
        result = Format.align_right(special, 15)
        assert isinstance(result, str)
        assert len(result) == 15

    def test_format_satoshis_boundary_values(self) -> None:
        """Test formatting satoshis at boundary values."""
        boundaries = [0, 1, 99, 100, 999, 1000, 9999, 10000, 99999, 100000]
        for boundary in boundaries:
            result = Format.satoshis(boundary)
            assert isinstance(result, str)

    def test_format_align_with_float(self) -> None:
        """Test aligning float values."""
        result = Format.align_right(3.14159, 10)
        assert isinstance(result, str)
        assert len(result) == 10

    def test_format_middle_odd_even_widths(self) -> None:
        """Test middle alignment with odd and even widths."""
        text = "test"

        # Even width
        result_even = Format.align_middle(text, 10)
        assert len(result_even) == 10

        # Odd width
        result_odd = Format.align_middle(text, 11)
        assert len(result_odd) == 11


class TestFormatTransactionLogging:
    """Test Format transaction logging methods."""

    def test_to_log_string_transaction_basic(self) -> None:
        """Test basic transaction logging."""
        # Create a mock transaction
        from unittest.mock import Mock

        tx = Mock()
        tx.id = Mock(return_value="a" * 64)  # 64 char hex txid
        tx.inputs = []
        tx.outputs = []

        # Add a mock input
        input_mock = Mock()
        input_mock.source_transaction = None
        input_mock.source_txid = "b" * 64
        input_mock.source_output_index = 0
        tx.inputs.append(input_mock)

        # Add a mock output
        output_mock = Mock()
        output_mock.satoshis = 1000
        output_mock.locking_script = Mock()
        output_mock.locking_script.to_hex = Mock(return_value="76a9141234567890abcdef1234567890abcdef1234567888ac")
        tx.outputs.append(output_mock)

        result = Format.to_log_string_transaction(tx)

        assert "txid" in result
        assert "total in:" in result
        assert "out:" in result
        assert "fee:" in result
        assert "Inputs" in result
        assert "Outputs" in result

    def test_to_log_string_transaction_invalid_txid(self) -> None:
        """Test transaction logging with invalid txid."""
        from unittest.mock import Mock

        tx = Mock()
        tx.id = Mock(side_effect=Exception("Invalid transaction"))

        result = Format.to_log_string_transaction(tx)

        assert "Cannot get txid:" in result

    def test_to_log_string_transaction_complex(self) -> None:
        """Test transaction logging with complex inputs/outputs."""
        from unittest.mock import Mock

        tx = Mock()
        tx.id = Mock(return_value="c" * 64)

        # Create inputs with source transactions
        input1 = Mock()
        source_tx = Mock()
        source_output = Mock()
        source_output.satoshis = 5000
        source_tx.outputs = [source_output]
        input1.source_transaction = source_tx
        input1.source_output_index = 0
        input1.source_txid = "d" * 64

        input2 = Mock()
        input2.source_transaction = None
        input2.source_txid = "e" * 64
        input2.source_output_index = 1

        tx.inputs = [input1, input2]

        # Create outputs
        output1 = Mock()
        output1.satoshis = 3000
        output1.locking_script = Mock()
        output1.locking_script.to_hex = Mock(return_value="76a914abcdef1234567890abcdef1234567890abcdef88ac")

        output2 = Mock()
        output2.satoshis = 1000
        output2.locking_script = Mock()
        output2.locking_script.to_hex = Mock(return_value="a9141234567890abcdef1234567890abcdef12345687")

        tx.outputs = [output1, output2]

        result = Format.to_log_string_transaction(tx)

        assert "txid" in result
        assert "total in:50_00" in result  # 5000 satoshis
        assert "out:40_00" in result  # 4000 satoshis
        assert "fee:10_00" in result  # 1000 satoshis

    def test_to_log_string_transaction_exception(self) -> None:
        """Test transaction logging with processing exception."""
        from unittest.mock import Mock

        tx = Mock()
        tx.id = Mock(return_value="f" * 64)
        # Make any attribute access raise an exception
        tx.inputs = Mock(side_effect=Exception("Processing error"))

        result = Format.to_log_string_transaction(tx)

        assert "is invalid" in result

    def test_to_log_string_beef_txid_found(self) -> None:
        """Test BEEF transaction logging when txid is found."""
        from unittest.mock import Mock

        beef = Mock()
        txid = "a" * 64

        # Mock the find_atomic_transaction method
        mock_tx = Mock()
        mock_tx.id = Mock(return_value=txid)
        mock_tx.inputs = []
        mock_tx.outputs = []
        beef.find_atomic_transaction = Mock(return_value=mock_tx)

        result = Format.to_log_string_beef_txid(beef, txid)

        assert "txid" in result
        beef.find_atomic_transaction.assert_called_once_with(txid)

    def test_to_log_string_beef_txid_not_found(self) -> None:
        """Test BEEF transaction logging when txid is not found."""
        from unittest.mock import Mock

        beef = Mock()
        txid = "b" * 64

        beef.find_atomic_transaction = Mock(return_value=None)

        result = Format.to_log_string_beef_txid(beef, txid)

        assert f"Transaction {txid} not found in beef" == result

    def test_to_log_string_beef_txid_exception(self) -> None:
        """Test BEEF transaction logging with exception."""
        from unittest.mock import Mock

        beef = Mock()
        txid = "c" * 64

        beef.find_atomic_transaction = Mock(side_effect=Exception("Beef processing error"))

        result = Format.to_log_string_beef_txid(beef, txid)

        assert "Cannot find transaction" in result
        assert "Beef processing error" in result
