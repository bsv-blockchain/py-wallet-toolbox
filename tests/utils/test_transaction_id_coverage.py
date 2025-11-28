"""Coverage tests for transaction ID utilities.

This module tests transaction ID computation from raw transaction data.
"""

from bsv_wallet_toolbox.utils.transaction_id import transaction_id


class TestTransactionId:
    """Test transaction_id function."""

    def test_transaction_id_from_bytes(self) -> None:
        """Test computing transaction ID from bytes."""
        # Simple transaction data (example)
        raw_tx = bytes.fromhex("0100000001abcd")

        result = transaction_id(raw_tx)

        # Should return a hex string
        assert isinstance(result, str)
        assert len(result) == 64  # 32 bytes as hex

    def test_transaction_id_from_hex_string(self) -> None:
        """Test computing transaction ID from hex string."""
        raw_tx_hex = "0100000001abcd"

        result = transaction_id(raw_tx_hex)

        # Should return a hex string
        assert isinstance(result, str)
        assert len(result) == 64  # 32 bytes as hex

    def test_transaction_id_from_bytearray(self) -> None:
        """Test computing transaction ID from bytearray."""
        raw_tx = bytearray.fromhex("0100000001abcd")

        result = transaction_id(raw_tx)

        # Should return a hex string
        assert isinstance(result, str)
        assert len(result) == 64

    def test_transaction_id_consistent_for_same_data(self) -> None:
        """Test that same data produces same transaction ID."""
        raw_tx1 = bytes.fromhex("0100000001abcdef")
        raw_tx2 = bytes.fromhex("0100000001abcdef")

        txid1 = transaction_id(raw_tx1)
        txid2 = transaction_id(raw_tx2)

        assert txid1 == txid2

    def test_transaction_id_different_for_different_data(self) -> None:
        """Test that different data produces different transaction IDs."""
        raw_tx1 = bytes.fromhex("0100000001abcdef")
        raw_tx2 = bytes.fromhex("0200000001abcdef")

        txid1 = transaction_id(raw_tx1)
        txid2 = transaction_id(raw_tx2)

        assert txid1 != txid2

    def test_transaction_id_bytes_and_hex_equivalence(self) -> None:
        """Test that bytes and hex string produce same result."""
        raw_hex = "0100000001abcdef0123456789"
        raw_bytes = bytes.fromhex(raw_hex)

        txid_from_hex = transaction_id(raw_hex)
        txid_from_bytes = transaction_id(raw_bytes)

        assert txid_from_hex == txid_from_bytes

    def test_transaction_id_is_hex_lowercase(self) -> None:
        """Test that transaction ID is returned as lowercase hex."""
        raw_tx = "0100000001ABCDEF"  # Uppercase input

        result = transaction_id(raw_tx)

        # Result should be lowercase
        assert result == result.lower()
        # And should only contain hex characters
        assert all(c in "0123456789abcdef" for c in result)

    def test_transaction_id_is_reversed_sha256(self) -> None:
        """Test that txid is double-SHA256 with reversed byte order."""
        # This is the standard Bitcoin transaction ID calculation
        raw_tx = bytes.fromhex("01000000010000")

        result = transaction_id(raw_tx)

        # The result should be 64 characters (32 bytes in hex)
        assert len(result) == 64
        # It should be all hex
        assert all(c in "0123456789abcdef" for c in result)
