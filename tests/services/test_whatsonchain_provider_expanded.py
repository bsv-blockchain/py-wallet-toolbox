"""Expanded coverage tests for WhatsOnChain provider.

This module provides comprehensive test coverage for all methods in the
WhatsOnChain provider implementation, focusing on error paths and edge cases.
"""

from unittest.mock import Mock, patch

import pytest

from bsv_wallet_toolbox.services.providers.whatsonchain import WhatsOnChain
from bsv_wallet_toolbox.services.wallet_services import Chain


class TestWhatsOnChainInitialization:
    """Test WhatsOnChain initialization."""

    def test_init_default_params(self) -> None:
        """Test initialization with default parameters."""
        provider = WhatsOnChain()

        # Check that it has the expected attributes from the base class
        assert hasattr(provider, "chain")
        assert hasattr(provider, "api_key")

    def test_init_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        http_client = Mock()
        provider = WhatsOnChain(network="test", api_key="test_key", http_client=http_client)

        assert provider.chain == "test"
        assert provider.api_key == "test_key"


class TestWhatsOnChainAsyncMethods:
    """Test WhatsOnChain async methods."""

    @pytest.fixture
    def provider(self) -> WhatsOnChain:
        """Create WhatsOnChain provider instance."""
        return WhatsOnChain()

    @pytest.mark.asyncio
    async def test_get_chain(self, provider: WhatsOnChain) -> None:
        """Test get_chain method."""
        with patch.object(provider, "_get_chain", return_value=Chain.MAIN) as mock_get_chain:
            result = await provider.get_chain()

            assert result == Chain.MAIN
            mock_get_chain.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_info(self, provider: WhatsOnChain) -> None:
        """Test get_info method."""
        mock_info = {"name": "WhatsOnChain", "version": "1.0"}
        with patch.object(provider, "_get_info", return_value=mock_info) as mock_get_info:
            result = await provider.get_info()

            assert result == mock_info
            mock_get_info.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_present_height(self, provider: WhatsOnChain) -> None:
        """Test get_present_height method."""
        with patch.object(provider, "_get_present_height", return_value=800000) as mock_get_height:
            result = await provider.get_present_height()

            assert result == 800000
            mock_get_height.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_headers(self, provider: WhatsOnChain) -> None:
        """Test get_headers method."""
        mock_headers = "header_hex_data"
        with patch.object(provider, "_get_headers", return_value=mock_headers) as mock_get_headers:
            result = await provider.get_headers(100, 10)

            assert result == mock_headers
            mock_get_headers.assert_called_with(100, 10)

    @pytest.mark.asyncio
    async def test_find_chain_tip_header(self, provider: WhatsOnChain) -> None:
        """Test find_chain_tip_header method."""
        mock_header = {"height": 800000, "hash": "tip_hash"}
        with patch.object(provider, "_find_chain_tip_header", return_value=mock_header) as mock_find_header:
            result = await provider.find_chain_tip_header()

            assert result == mock_header
            mock_find_header.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_chain_tip_hash(self, provider: WhatsOnChain) -> None:
        """Test find_chain_tip_hash method."""
        with patch.object(provider, "_find_chain_tip_hash", return_value="tip_hash") as mock_find_hash:
            result = await provider.find_chain_tip_hash()

            assert result == "tip_hash"
            mock_find_hash.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_header_for_height_found(self, provider: WhatsOnChain) -> None:
        """Test find_header_for_height when header is found."""
        mock_header = {"height": 100, "hash": "hash100"}
        with patch.object(provider, "_find_header_for_height", return_value=mock_header) as mock_find:
            result = await provider.find_header_for_height(100)

            assert result == mock_header
            mock_find.assert_called_with(100)

    @pytest.mark.asyncio
    async def test_find_header_for_height_not_found(self, provider: WhatsOnChain) -> None:
        """Test find_header_for_height when header is not found."""
        with patch.object(provider, "_find_header_for_height", return_value=None) as mock_find:
            result = await provider.find_header_for_height(999999)

            assert result is None
            mock_find.assert_called_with(999999)

    @pytest.mark.asyncio
    async def test_find_header_for_block_hash_found(self, provider: WhatsOnChain) -> None:
        """Test find_header_for_block_hash when found."""
        mock_header = {"height": 100, "hash": "target_hash"}
        with patch.object(provider, "_find_header_for_block_hash", return_value=mock_header) as mock_find:
            result = await provider.find_header_for_block_hash("target_hash")

            assert result == mock_header
            mock_find.assert_called_with("target_hash")

    @pytest.mark.asyncio
    async def test_find_header_for_block_hash_not_found(self, provider: WhatsOnChain) -> None:
        """Test find_header_for_block_hash when not found."""
        with patch.object(provider, "_find_header_for_block_hash", return_value=None) as mock_find:
            result = await provider.find_header_for_block_hash("unknown_hash")

            assert result is None
            mock_find.assert_called_with("unknown_hash")

    @pytest.mark.asyncio
    async def test_add_header(self, provider: WhatsOnChain) -> None:
        """Test add_header method."""
        mock_header = {"height": 100, "hash": "hash100"}
        with patch.object(provider, "_add_header", return_value=None) as mock_add:
            await provider.add_header(mock_header)

            mock_add.assert_called_with(mock_header)

    @pytest.mark.asyncio
    async def test_start_listening(self, provider: WhatsOnChain) -> None:
        """Test start_listening method."""
        with patch.object(provider, "_start_listening", return_value=None) as mock_start:
            await provider.start_listening()

            mock_start.assert_called_once()

    @pytest.mark.asyncio
    async def test_listening(self, provider: WhatsOnChain) -> None:
        """Test listening method."""
        with patch.object(provider, "_listening", return_value=None) as mock_listening:
            await provider.listening()

            mock_listening.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_listening(self, provider: WhatsOnChain) -> None:
        """Test is_listening method."""
        with patch.object(provider, "_is_listening", return_value=True) as mock_is_listening:
            result = await provider.is_listening()

            assert result is True
            mock_is_listening.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_synchronized(self, provider: WhatsOnChain) -> None:
        """Test is_synchronized method."""
        with patch.object(provider, "_is_synchronized", return_value=False) as mock_is_sync:
            result = await provider.is_synchronized()

            assert result is False
            mock_is_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_headers(self, provider: WhatsOnChain) -> None:
        """Test subscribe_headers method."""
        mock_listener = Mock()
        with patch.object(provider, "_subscribe_headers", return_value="sub_id_123") as mock_subscribe:
            result = await provider.subscribe_headers(mock_listener)

            assert result == "sub_id_123"
            mock_subscribe.assert_called_with(mock_listener)

    @pytest.mark.asyncio
    async def test_subscribe_reorgs(self, provider: WhatsOnChain) -> None:
        """Test subscribe_reorgs method."""
        mock_listener = Mock()
        with patch.object(provider, "_subscribe_reorgs", return_value="reorg_sub_id") as mock_subscribe:
            result = await provider.subscribe_reorgs(mock_listener)

            assert result == "reorg_sub_id"
            mock_subscribe.assert_called_with(mock_listener)

    @pytest.mark.asyncio
    async def test_unsubscribe(self, provider: WhatsOnChain) -> None:
        """Test unsubscribe method."""
        with patch.object(provider, "_unsubscribe", return_value=True) as mock_unsubscribe:
            result = await provider.unsubscribe("sub_id")

            assert result is True
            mock_unsubscribe.assert_called_with("sub_id")

    @pytest.mark.asyncio
    async def test_get_header_bytes_for_height(self, provider: WhatsOnChain) -> None:
        """Test get_header_bytes_for_height method."""
        mock_bytes = b"header_bytes"
        with patch.object(provider, "_get_header_bytes_for_height", return_value=mock_bytes) as mock_get_bytes:
            result = await provider.get_header_bytes_for_height(100)

            assert result == mock_bytes
            mock_get_bytes.assert_called_with(100)

    @pytest.mark.asyncio
    async def test_get_merkle_path(self, provider: WhatsOnChain) -> None:
        """Test get_merkle_path method."""
        mock_services = Mock()
        mock_path = {"merklePath": {"some": "data"}}
        with patch.object(provider, "_get_merkle_path", return_value=mock_path) as mock_get_path:
            result = await provider.get_merkle_path("txid123", mock_services)

            assert result == mock_path
            mock_get_path.assert_called_with("txid123", mock_services)

    @pytest.mark.asyncio
    async def test_update_bsv_exchange_rate(self, provider: WhatsOnChain) -> None:
        """Test update_bsv_exchange_rate method."""
        mock_rate = {"BSV": 50000.0, "timestamp": "2024-01-01"}
        with patch.object(provider, "_update_bsv_exchange_rate", return_value=mock_rate) as mock_update:
            result = await provider.update_bsv_exchange_rate()

            assert result == mock_rate
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_fiat_exchange_rate(self, provider: WhatsOnChain) -> None:
        """Test get_fiat_exchange_rate method."""
        with patch.object(provider, "_get_fiat_exchange_rate", return_value=45000.0) as mock_get_rate:
            result = await provider.get_fiat_exchange_rate("EUR", "USD")

            assert result == 45000.0
            mock_get_rate.assert_called_with("EUR", "USD")

    @pytest.mark.asyncio
    async def test_get_fiat_exchange_rate_default_base(self, provider: WhatsOnChain) -> None:
        """Test get_fiat_exchange_rate with default base currency."""
        with patch.object(provider, "_get_fiat_exchange_rate", return_value=50000.0) as mock_get_rate:
            result = await provider.get_fiat_exchange_rate("USD")

            assert result == 50000.0
            mock_get_rate.assert_called_with("USD", "USD")

    @pytest.mark.asyncio
    async def test_get_utxo_status(self, provider: WhatsOnChain) -> None:
        """Test get_utxo_status method."""
        mock_status = {"utxo": "status_data"}
        with patch.object(provider, "_get_utxo_status", return_value=mock_status) as mock_get_status:
            result = await provider.get_utxo_status("txid", 0)

            assert result == mock_status
            mock_get_status.assert_called_with("txid", 0)

    @pytest.mark.asyncio
    async def test_get_script_history(self, provider: WhatsOnChain) -> None:
        """Test get_script_history method."""
        mock_history = {"history": ["tx1", "tx2"]}
        with patch.object(provider, "_get_script_history", return_value=mock_history) as mock_get_history:
            result = await provider.get_script_history("scripthash")

            assert result == mock_history
            mock_get_history.assert_called_with("scripthash", None)

    @pytest.mark.asyncio
    async def test_get_script_history_with_next(self, provider: WhatsOnChain) -> None:
        """Test get_script_history with use_next parameter."""
        mock_history = {"history": ["tx3", "tx4"]}
        with patch.object(provider, "_get_script_history", return_value=mock_history) as mock_get_history:
            result = await provider.get_script_history("scripthash", True)

            assert result == mock_history
            mock_get_history.assert_called_with("scripthash", True)

    @pytest.mark.asyncio
    async def test_get_transaction_status(self, provider: WhatsOnChain) -> None:
        """Test get_transaction_status method."""
        mock_status = {"confirmations": 6, "blockHeight": 800000}
        with patch.object(provider, "_get_transaction_status", return_value=mock_status) as mock_get_status:
            result = await provider.get_transaction_status("txid123")

            assert result == mock_status
            mock_get_status.assert_called_with("txid123", None)

    @pytest.mark.asyncio
    async def test_get_transaction_status_with_next(self, provider: WhatsOnChain) -> None:
        """Test get_transaction_status with use_next parameter."""
        mock_status = {"confirmations": 0}
        with patch.object(provider, "_get_transaction_status", return_value=mock_status) as mock_get_status:
            result = await provider.get_transaction_status("txid456", True)

            assert result == mock_status
            mock_get_status.assert_called_with("txid456", True)

    @pytest.mark.asyncio
    async def test_get_raw_tx_found(self, provider: WhatsOnChain) -> None:
        """Test get_raw_tx when transaction is found."""
        with patch.object(provider, "_get_raw_tx", return_value="deadbeef") as mock_get_raw:
            result = await provider.get_raw_tx("txid789")

            assert result == "deadbeef"
            mock_get_raw.assert_called_with("txid789")

    @pytest.mark.asyncio
    async def test_get_raw_tx_not_found(self, provider: WhatsOnChain) -> None:
        """Test get_raw_tx when transaction is not found."""
        with patch.object(provider, "_get_raw_tx", return_value=None) as mock_get_raw:
            result = await provider.get_raw_tx("unknown_txid")

            assert result is None
            mock_get_raw.assert_called_with("unknown_txid")

    @pytest.mark.asyncio
    async def test_get_tx_propagation(self, provider: WhatsOnChain) -> None:
        """Test get_tx_propagation method."""
        mock_propagation = {"nodes": 5, "propagated": True}
        with patch.object(provider, "_get_tx_propagation", return_value=mock_propagation) as mock_get_prop:
            result = await provider.get_tx_propagation("txid999")

            assert result == mock_propagation
            mock_get_prop.assert_called_with("txid999")


class TestWhatsOnChainErrorHandling:
    """Test WhatsOnChain error handling and edge cases."""

    @pytest.fixture
    def provider(self) -> WhatsOnChain:
        """Create WhatsOnChain provider instance."""
        return WhatsOnChain()

    @pytest.mark.asyncio
    async def test_get_chain_error_propagation(self, provider: WhatsOnChain) -> None:
        """Test that get_chain propagates errors from underlying method."""
        with patch.object(provider, "_get_chain", side_effect=Exception("Network error")):
            with pytest.raises(Exception, match="Network error"):
                await provider.get_chain()

    @pytest.mark.asyncio
    async def test_get_present_height_error_propagation(self, provider: WhatsOnChain) -> None:
        """Test that get_present_height propagates errors."""
        with patch.object(provider, "_get_present_height", side_effect=ConnectionError("API down")):
            with pytest.raises(ConnectionError, match="API down"):
                await provider.get_present_height()

    @pytest.mark.asyncio
    async def test_find_header_for_height_none_result(self, provider: WhatsOnChain) -> None:
        """Test find_header_for_height returns None when not found."""
        with patch.object(provider, "_find_header_for_height", return_value=None):
            result = await provider.find_header_for_height(0)  # Genesis block might not exist

            assert result is None

    @pytest.mark.asyncio
    async def test_subscribe_headers_returns_subscription_id(self, provider: WhatsOnChain) -> None:
        """Test subscribe_headers returns a subscription identifier."""
        mock_listener = Mock()
        with patch.object(provider, "_subscribe_headers", return_value="header_sub_123"):
            result = await provider.subscribe_headers(mock_listener)

            assert isinstance(result, str)
            assert result == "header_sub_123"

    @pytest.mark.asyncio
    async def test_unsubscribe_returns_success_status(self, provider: WhatsOnChain) -> None:
        """Test unsubscribe returns boolean success status."""
        with patch.object(provider, "_unsubscribe", return_value=False):  # Failed to unsubscribe
            result = await provider.unsubscribe("invalid_id")

            assert isinstance(result, bool)
            assert result is False

    @pytest.mark.asyncio
    async def test_get_fiat_exchange_rate_numeric_result(self, provider: WhatsOnChain) -> None:
        """Test get_fiat_exchange_rate returns numeric value."""
        with patch.object(provider, "_get_fiat_exchange_rate", return_value=123.45):
            result = await provider.get_fiat_exchange_rate("JPY")

            assert isinstance(result, (int, float))
            assert result == 123.45

    @pytest.mark.asyncio
    async def test_get_script_history_returns_dict(self, provider: WhatsOnChain) -> None:
        """Test get_script_history returns dictionary structure."""
        mock_history = {"txs": [], "total": 0}
        with patch.object(provider, "_get_script_history", return_value=mock_history):
            result = await provider.get_script_history("scripthash123")

            assert isinstance(result, dict)
            assert "txs" in result

    @pytest.mark.asyncio
    async def test_get_transaction_status_confirmations_field(self, provider: WhatsOnChain) -> None:
        """Test get_transaction_status returns expected status structure."""
        mock_status = {"confirmations": 12, "blockHash": "hash123"}
        with patch.object(provider, "_get_transaction_status", return_value=mock_status):
            result = await provider.get_transaction_status("txid")

            assert isinstance(result, dict)
            assert "confirmations" in result
            assert result["confirmations"] == 12
