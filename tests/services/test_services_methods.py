"""Unit tests for services/services.py orchestration methods.

Tests service orchestration with mocked providers.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from bsv_wallet_toolbox.services.services import Services, create_default_options


@pytest.fixture
def mock_services():
    """Create mock services for testing."""
    with patch("bsv_wallet_toolbox.services.services.ServiceCollection"):
        services = Services("main")
        return services


class TestServicesInitialization:
    """Test Services initialization."""

    def test_create_default_options_main(self):
        """Test creating default options for mainnet."""
        options = create_default_options("main")
        assert options["chain"] == "main"
        assert "arcUrl" in options  # Check that options dict is properly populated

    def test_create_default_options_test(self):
        """Test creating default options for testnet."""
        options = create_default_options("test")
        assert options["chain"] == "test"
        assert "arcUrl" in options  # Check that options dict is properly populated

    def test_services_init_with_options(self):
        """Test Services initialization with options."""
        options = create_default_options("main")
        with patch("bsv_wallet_toolbox.services.services.ServiceCollection"):
            services = Services(options)
            assert services is not None

    def test_services_init_with_chain(self):
        """Test Services initialization with chain string."""
        with patch("bsv_wallet_toolbox.services.services.ServiceCollection"):
            services = Services("main")
            assert services is not None


class TestServicesBlockchainMethods:
    """Test blockchain-related service methods."""

    async def test_get_height(self, mock_services):
        """Test get_height method."""
        mock_services.whatsonchain.current_height = AsyncMock(return_value=850000)

        height = await mock_services.get_height()
        assert height == 850000

    async def test_get_present_height(self, mock_services):
        """Test get_present_height method."""
        mock_services.whatsonchain.get_present_height = AsyncMock(return_value=850001)

        height = await mock_services.get_present_height()
        assert height == 850001

    async def test_get_chain(self, mock_services):
        """Test get_chain method."""
        mock_services.whatsonchain.get_chain = AsyncMock(return_value="main")
        chain = await mock_services.get_chain()
        assert chain == "main"

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_get_header_for_height(self, mock_services):
        """Test get_header_for_height method."""
        mock_services._service_collections = MagicMock()
        mock_header = b"header_bytes"
        mock_services._service_collections.get_header_for_height.return_value = mock_header

        header = mock_services.get_header_for_height(850000)
        assert header == mock_header

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_find_header_for_height(self, mock_services):
        """Test find_header_for_height method."""
        mock_services._service_collections = MagicMock()
        mock_header = {"hash": "abc123", "height": 850000}
        mock_services._service_collections.find_header_for_height.return_value = mock_header

        header = mock_services.find_header_for_height(850000)
        assert header == mock_header

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_find_chain_tip_header(self, mock_services):
        """Test find_chain_tip_header method."""
        mock_services._service_collections = MagicMock()
        mock_header = {"hash": "tip_hash", "height": 851000}
        mock_services._service_collections.find_chain_tip_header.return_value = mock_header

        header = mock_services.find_chain_tip_header()
        assert header == mock_header

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_find_chain_tip_hash(self, mock_services):
        """Test find_chain_tip_hash method."""
        mock_services._service_collections = MagicMock()
        mock_services._service_collections.find_chain_tip_hash.return_value = "tip_hash_123"

        tip_hash = mock_services.find_chain_tip_hash()
        assert tip_hash == "tip_hash_123"

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_find_header_for_block_hash(self, mock_services):
        """Test find_header_for_block_hash method."""
        mock_services._service_collections = MagicMock()
        mock_header = {"hash": "block_hash", "height": 850000}
        mock_services._service_collections.find_header_for_block_hash.return_value = mock_header

        header = mock_services.find_header_for_block_hash("block_hash")
        assert header == mock_header

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_is_valid_root_for_height(self, mock_services):
        """Test is_valid_root_for_height method."""
        mock_services._service_collections = MagicMock()
        mock_services._service_collections.is_valid_root_for_height.return_value = True

        is_valid = mock_services.is_valid_root_for_height("root_hash", 850000)
        assert is_valid is True


class TestServicesTransactionMethods:
    """Test transaction-related service methods."""

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_get_raw_tx(self, mock_services):
        """Test get_raw_tx method."""
        mock_services._service_collections = MagicMock()
        mock_services._service_collections.get_raw_tx.return_value = "01000000..."

        raw_tx = mock_services.get_raw_tx("a" * 64)
        assert raw_tx == "01000000..."

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_get_merkle_path_for_transaction(self, mock_services):
        """Test get_merkle_path_for_transaction method."""
        mock_services._service_collections = MagicMock()
        mock_path = {"path": [], "blockHeight": 850000}
        mock_services._service_collections.get_merkle_path_for_transaction.return_value = mock_path

        path = mock_services.get_merkle_path_for_transaction("a" * 64)
        assert path == mock_path

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_get_transaction_status(self, mock_services):
        """Test get_transaction_status method."""
        mock_services._service_collections = MagicMock()
        mock_status = {"status": "confirmed", "blockHeight": 850000}
        mock_services._service_collections.get_transaction_status.return_value = mock_status

        status = mock_services.get_transaction_status("a" * 64)
        assert status == mock_status

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_get_tx_propagation(self, mock_services):
        """Test get_tx_propagation method."""
        mock_services._service_collections = MagicMock()
        mock_propagation = {"propagated": True, "peers": 5}
        mock_services._service_collections.get_tx_propagation.return_value = mock_propagation

        propagation = mock_services.get_tx_propagation("a" * 64)
        assert propagation == mock_propagation

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_post_beef(self, mock_services):
        """Test post_beef method."""
        mock_services._service_collections = MagicMock()
        mock_result = {"accepted": True, "txid": "b" * 64}
        mock_services._service_collections.post_beef.return_value = mock_result

        result = mock_services.post_beef("beef_data")
        assert result == mock_result

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_post_beef_array(self, mock_services):
        """Test post_beef_array method."""
        mock_services._service_collections = MagicMock()
        mock_results = [{"accepted": True}, {"accepted": True}]
        mock_services._service_collections.post_beef_array.return_value = mock_results

        results = mock_services.post_beef_array(["beef1", "beef2"])
        assert results == mock_results


class TestServicesExchangeRateMethods:
    """Test exchange rate methods."""

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_update_bsv_exchange_rate(self, mock_services):
        """Test update_bsv_exchange_rate method."""
        mock_services._service_collections = MagicMock()
        mock_rate = {"base": "USD", "rate": 50.0, "timestamp": 1234567890}
        mock_services._service_collections.update_bsv_exchange_rate.return_value = mock_rate

        rate = mock_services.update_bsv_exchange_rate()
        assert rate == mock_rate

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_get_fiat_exchange_rate(self, mock_services):
        """Test get_fiat_exchange_rate method."""
        mock_services._service_collections = MagicMock()
        mock_services._service_collections.get_fiat_exchange_rate.return_value = 1.2

        rate = mock_services.get_fiat_exchange_rate("EUR")
        assert rate == 1.2

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_get_fiat_exchange_rate_with_base(self, mock_services):
        """Test get_fiat_exchange_rate with custom base."""
        mock_services._service_collections = MagicMock()
        mock_services._service_collections.get_fiat_exchange_rate.return_value = 0.85

        rate = mock_services.get_fiat_exchange_rate("GBP", "EUR")
        assert rate == 0.85


class TestServicesUTXOMethods:
    """Test UTXO-related methods."""

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_get_utxo_status(self, mock_services):
        """Test get_utxo_status method."""
        mock_services._service_collections = MagicMock()
        mock_status = {"spent": False, "txid": "a" * 64, "vout": 0}
        mock_services._service_collections.get_utxo_status.return_value = mock_status

        status = mock_services.get_utxo_status("a" * 64, 0)
        assert status == mock_status

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_get_script_history(self, mock_services):
        """Test get_script_history method."""
        mock_services._service_collections = MagicMock()
        mock_history = {"confirmed": [], "unconfirmed": []}
        mock_services._service_collections.get_script_history.return_value = mock_history

        history = mock_services.get_script_history("script_hash_123")
        assert history == mock_history

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_is_utxo(self, mock_services):
        """Test is_utxo method."""
        mock_services._service_collections = MagicMock()
        mock_services._service_collections.is_utxo.return_value = True

        result = mock_services.is_utxo("txid.vout")
        assert result is True


class TestServicesUtilityMethods:
    """Test utility methods."""

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_hash_output_script(self, mock_services):
        """Test hash_output_script method."""
        mock_services._service_collections = MagicMock()
        mock_services._service_collections.hash_output_script.return_value = "script_hash"

        hash_result = mock_services.hash_output_script("script_hex")
        assert hash_result == "script_hash"

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_n_lock_time_is_final(self, mock_services):
        """Test n_lock_time_is_final method."""
        mock_services._service_collections = MagicMock()
        mock_services._service_collections.n_lock_time_is_final.return_value = True

        result = mock_services.n_lock_time_is_final(0)
        assert result is True

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_get_info(self, mock_services):
        """Test get_info method."""
        mock_services._service_collections = MagicMock()
        mock_info = {"version": "1.0", "network": "main"}
        mock_services._service_collections.get_info.return_value = mock_info

        info = mock_services.get_info()
        assert info == mock_info

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_get_headers(self, mock_services):
        """Test get_headers method."""
        mock_services._service_collections = MagicMock()
        mock_services._service_collections.get_headers.return_value = "headers_hex"

        headers = mock_services.get_headers(850000, 10)
        assert headers == "headers_hex"

    def test_get_services_call_history(self, mock_services):
        """Test get_services_call_history method."""
        history = mock_services.get_services_call_history()
        assert isinstance(history, dict)

    def test_get_services_call_history_reset(self, mock_services):
        """Test get_services_call_history with reset."""
        history = mock_services.get_services_call_history(reset=True)
        assert isinstance(history, dict)


class TestServicesChainTrackerMethods:
    """Test chain tracker methods."""

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_get_chain_tracker(self, mock_services):
        """Test get_chain_tracker method."""
        mock_tracker = MagicMock()
        mock_services._chain_tracker = mock_tracker

        tracker = mock_services.get_chain_tracker()
        assert tracker == mock_tracker

    async def test_start_listening(self, mock_services):
        """Test start_listening method."""
        mock_services.whatsonchain = AsyncMock()
        await mock_services.start_listening()
        # Should not raise

    async def test_listening(self, mock_services):
        """Test listening method."""
        mock_services.whatsonchain = AsyncMock()
        await mock_services.listening()
        # Should not raise

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_is_listening(self, mock_services):
        """Test is_listening method."""
        mock_services._chain_tracker = MagicMock()
        mock_services._chain_tracker.is_listening.return_value = True

        result = mock_services.is_listening()
        assert result is True

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_is_synchronized(self, mock_services):
        """Test is_synchronized method."""
        mock_services._chain_tracker = MagicMock()
        mock_services._chain_tracker.is_synchronized.return_value = False

        result = mock_services.is_synchronized()
        assert result is False

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_subscribe_headers(self, mock_services):
        """Test subscribe_headers method."""
        mock_services._chain_tracker = MagicMock()
        mock_services._chain_tracker.subscribe_headers.return_value = "sub_id_123"

        sub_id = mock_services.subscribe_headers(MagicMock())
        assert sub_id == "sub_id_123"

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_subscribe_reorgs(self, mock_services):
        """Test subscribe_reorgs method."""
        mock_services._chain_tracker = MagicMock()
        mock_services._chain_tracker.subscribe_reorgs.return_value = "sub_id_456"

        sub_id = mock_services.subscribe_reorgs(MagicMock())
        assert sub_id == "sub_id_456"

    @pytest.mark.skip(reason="Requires full provider infrastructure")
    def test_unsubscribe(self, mock_services):
        """Test unsubscribe method."""
        mock_services._chain_tracker = MagicMock()
        mock_services._chain_tracker.unsubscribe.return_value = True

        result = mock_services.unsubscribe("sub_id_123")
        assert result is True

    async def test_add_header(self, mock_services):
        """Test add_header method."""
        mock_services.whatsonchain = AsyncMock()
        await mock_services.add_header("header_data")
        # Should not raise
