"""Expanded coverage tests for Wallet class methods.

This module provides comprehensive tests for Wallet methods that have low coverage,
focusing on mocking and edge cases.
"""

from unittest.mock import Mock, patch

from bsv_wallet_toolbox.wallet import Wallet


class TestWalletBlockchainMethods:
    """Test wallet blockchain-related methods."""

    def test_get_present_height(self, wallet_with_storage: Wallet) -> None:
        """Test get_present_height method."""
        # Mock services property
        mock_services = Mock()
        mock_services.get_present_height.return_value = 800000

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.get_present_height()
            assert result == 800000
            mock_services.get_present_height.assert_called_once()

    def test_get_chain(self, wallet_with_storage: Wallet) -> None:
        """Test get_chain method."""
        result = wallet_with_storage.get_chain()
        assert result == "main"

    def test_find_chain_tip_header(self, wallet_with_storage: Wallet) -> None:
        """Test find_chain_tip_header method."""
        mock_header = {"hash": "abcd" * 16, "height": 800000}
        mock_services = Mock()
        mock_services.find_chain_tip_header.return_value = mock_header

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.find_chain_tip_header()
            assert result == mock_header
            mock_services.find_chain_tip_header.assert_called_once()

    def test_find_chain_tip_hash(self, wallet_with_storage: Wallet) -> None:
        """Test find_chain_tip_hash method."""
        mock_hash = "abcd" * 16
        mock_services = Mock()
        mock_services.find_chain_tip_hash.return_value = mock_hash

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.find_chain_tip_hash()
            assert result == mock_hash
            mock_services.find_chain_tip_hash.assert_called_once()

    def test_find_header_for_block_hash(self, wallet_with_storage: Wallet) -> None:
        """Test find_header_for_block_hash method."""
        block_hash = "abcd" * 16
        mock_header = {"hash": block_hash, "height": 800000}
        mock_services = Mock()
        mock_services.find_header_for_block_hash.return_value = mock_header

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.find_header_for_block_hash(block_hash)
            assert result == mock_header
            mock_services.find_header_for_block_hash.assert_called_once_with(block_hash)

    def test_find_header_for_height(self, wallet_with_storage: Wallet) -> None:
        """Test find_header_for_height method."""
        height = 800000
        mock_header = {"hash": "abcd" * 16, "height": height}
        mock_services = Mock()
        mock_services.find_header_for_height.return_value = mock_header

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.find_header_for_height(height)
            assert result == mock_header
            mock_services.find_header_for_height.assert_called_once_with(height)


class TestWalletTransactionStatusMethods:
    """Test wallet transaction status methods."""

    def test_get_tx_propagation(self, wallet_with_storage: Wallet) -> None:
        """Test get_tx_propagation method."""
        txid = "abcd" * 16
        mock_result = {"txid": txid, "propagated": True}
        mock_services = Mock()
        mock_services.get_tx_propagation.return_value = mock_result

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.get_tx_propagation(txid)
            assert result == mock_result
            mock_services.get_tx_propagation.assert_called_once_with(txid)

    def test_get_utxo_status(self, wallet_with_storage: Wallet) -> None:
        """Test get_utxo_status method."""
        outpoint = "abcd1234:0"
        mock_result = {"outpoint": outpoint, "status": "unspent"}
        mock_services = Mock()
        mock_services.get_utxo_status.return_value = mock_result

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.get_utxo_status(outpoint)
            assert result == mock_result
            mock_services.get_utxo_status.assert_called_once_with(outpoint, None, None)

    def test_get_script_history(self, wallet_with_storage: Wallet) -> None:
        """Test get_script_history method."""
        script_hash = "abcd" * 16
        mock_result = {"scriptHash": script_hash, "history": []}
        mock_services = Mock()
        mock_services.get_script_history.return_value = mock_result

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.get_script_history(script_hash)
            assert result == mock_result
            mock_services.get_script_history.assert_called_once_with(script_hash)

    def test_get_transaction_status(self, wallet_with_storage: Wallet) -> None:
        """Test get_transaction_status method."""
        txid = "abcd" * 16
        mock_result = {"txid": txid, "status": "confirmed"}
        mock_services = Mock()
        mock_services.get_transaction_status.return_value = mock_result

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.get_transaction_status(txid)
            assert result == mock_result
            mock_services.get_transaction_status.assert_called_once_with(txid)

    def test_get_raw_tx(self, wallet_with_storage: Wallet) -> None:
        """Test get_raw_tx method."""
        txid = "abcd" * 16
        raw_tx_data = "abcd"
        mock_services = Mock()
        mock_services.get_raw_tx.return_value = raw_tx_data

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.get_raw_tx(txid)
            # Method wraps the result in {"data": ...}
            assert result == {"data": raw_tx_data}
            mock_services.get_raw_tx.assert_called_once_with(txid)


class TestWalletExchangeRateMethods:
    """Test wallet exchange rate methods."""

    def test_update_bsv_exchange_rate(self, wallet_with_storage: Wallet) -> None:
        """Test update_bsv_exchange_rate method."""
        mock_result = {"rate": 100.0, "currency": "USD"}
        mock_services = Mock()
        mock_services.update_bsv_exchange_rate.return_value = mock_result

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.update_bsv_exchange_rate()
            assert result == mock_result
            mock_services.update_bsv_exchange_rate.assert_called_once()

    def test_get_fiat_exchange_rate(self, wallet_with_storage: Wallet) -> None:
        """Test get_fiat_exchange_rate method."""
        currency = "EUR"
        base = "USD"
        expected_rate = 0.85
        mock_services = Mock()
        mock_services.get_fiat_exchange_rate.return_value = expected_rate

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.get_fiat_exchange_rate(currency, base)
            assert result == expected_rate
            mock_services.get_fiat_exchange_rate.assert_called_once_with(currency, base)

    def test_get_fiat_exchange_rate_default_base(self, wallet_with_storage: Wallet) -> None:
        """Test get_fiat_exchange_rate with default base."""
        currency = "EUR"
        expected_rate = 0.85
        mock_services = Mock()
        mock_services.get_fiat_exchange_rate.return_value = expected_rate

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.get_fiat_exchange_rate(currency)
            assert result == expected_rate
            mock_services.get_fiat_exchange_rate.assert_called_once_with(currency, "USD")


class TestWalletMerklePathMethods:
    """Test wallet merkle path methods."""

    def test_get_merkle_path_for_transaction(self, wallet_with_storage: Wallet) -> None:
        """Test get_merkle_path_for_transaction method."""
        txid = "abcd" * 16
        mock_result = {"txid": txid, "merklePath": []}
        mock_services = Mock()
        mock_services.get_merkle_path_for_transaction.return_value = mock_result

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.get_merkle_path_for_transaction(txid)
            assert result == mock_result
            mock_services.get_merkle_path_for_transaction.assert_called_once_with(txid)

    def test_is_valid_root_for_height(self, wallet_with_storage: Wallet) -> None:
        """Test is_valid_root_for_height method."""
        root = "abcd" * 16
        height = 800000
        expected_result = True
        mock_services = Mock()
        mock_services.is_valid_root_for_height.return_value = expected_result

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.is_valid_root_for_height(root, height)
            assert result == expected_result
            mock_services.is_valid_root_for_height.assert_called_once_with(root, height)


class TestWalletBeefMethods:
    """Test wallet BEEF posting methods."""

    def test_post_beef(self, wallet_with_storage: Wallet) -> None:
        """Test post_beef method."""
        beef = "mock_beef_data"
        mock_result = {"status": "success", "txid": "abcd" * 16}
        mock_services = Mock()
        mock_services.post_beef.return_value = mock_result

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.post_beef(beef)
            assert result == mock_result
            mock_services.post_beef.assert_called_once_with(beef)

    def test_post_beef_array(self, wallet_with_storage: Wallet) -> None:
        """Test post_beef_array method."""
        beefs = ["beef1", "beef2", "beef3"]
        mock_results = [
            {"status": "success", "txid": "tx1"},
            {"status": "success", "txid": "tx2"},
            {"status": "success", "txid": "tx3"},
        ]
        mock_services = Mock()
        mock_services.post_beef_array.return_value = mock_results

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.post_beef_array(beefs)
            assert result == mock_results
            mock_services.post_beef_array.assert_called_once_with(beefs)


class TestWalletKeyMethods:
    """Test wallet key-related methods."""

    def test_get_client_change_key_pair(self, wallet_with_storage: Wallet) -> None:
        """Test get_client_change_key_pair method."""
        result = wallet_with_storage.get_client_change_key_pair()
        # Should return dict with camelCase keys
        assert isinstance(result, dict)
        assert "privateKey" in result
        assert "publicKey" in result
        assert isinstance(result["privateKey"], str)
        assert isinstance(result["publicKey"], str)

    def test_get_identity_key(self, wallet_with_storage: Wallet) -> None:
        """Test get_identity_key method."""
        result = wallet_with_storage.get_identity_key()
        # Should return public key as hex string
        assert isinstance(result, str)
        assert len(result) == 66  # 33 bytes * 2 hex chars


class TestWalletBeefVerificationMethods:
    """Test wallet BEEF verification methods."""

    def test_verify_returned_txid_only(self, wallet_with_storage: Wallet) -> None:
        """Test verify_returned_txid_only method."""
        # Create a mock beef object with proper txs structure
        mock_beef = Mock()
        mock_beef.txs = {}  # Empty dict so values() returns empty iterable

        # Set return_txid_only to False so the method processes transactions
        wallet_with_storage.return_txid_only = False

        known_txids = ["tx1", "tx2"]
        result = wallet_with_storage.verify_returned_txid_only(mock_beef, known_txids)

        assert result == mock_beef

    def test_verify_returned_txid_only_atomic_beef(self, wallet_with_storage: Wallet) -> None:
        """Test verify_returned_txid_only_atomic_beef method."""
        # This method takes bytes, not a Beef object, and returns bytes or None
        beef_data = b"mock_beef_bytes"

        # Set return_txid_only to False
        wallet_with_storage.return_txid_only = False

        known_txids = ["tx1", "tx2"]
        result = wallet_with_storage.verify_returned_txid_only_atomic_beef(beef_data, known_txids)

        # Should return the beef data (mocked to return the same)
        assert result == beef_data


class TestWalletKnownTxidsMethods:
    """Test wallet known txids methods."""

    def test_get_known_txids_empty(self, wallet_with_storage: Wallet) -> None:
        """Test get_known_txids with no new txids."""
        result = wallet_with_storage.get_known_txids()
        assert isinstance(result, list)

    def test_get_known_txids_with_new_txids(self, wallet_with_storage: Wallet) -> None:
        """Test get_known_txids with new txids."""
        # Force fallback to _known_txids by disabling beef (matching test_wallet_getknowntxids.py pattern)
        # This ensures the test works regardless of BEEF state
        wallet_with_storage.beef = None

        new_txids = ["tx1", "tx2", "tx3"]
        result = wallet_with_storage.get_known_txids(new_txids)

        assert isinstance(result, list)
        # Should include the new txids
        assert all(txid in result for txid in new_txids)


class TestWalletDestructionMethods:
    """Test wallet destruction methods."""

    def test_destroy_wallet(self, wallet_with_storage: Wallet) -> None:
        """Test destroy method."""
        mock_storage = Mock()

        with patch.object(wallet_with_storage, "storage", mock_storage):
            wallet_with_storage.destroy()

            # Should call destroy on storage
            mock_storage.destroy.assert_called_once()


class TestWalletAuthenticationMethods:
    """Test wallet authentication methods."""

    def test_is_authenticated(self, wallet_with_storage: Wallet) -> None:
        """Test is_authenticated method."""
        # This is a BRC-100 interface method with specific signature
        result = wallet_with_storage.is_authenticated({})
        assert isinstance(result, dict)
        assert "authenticated" in result

    def test_wait_for_authentication(self, wallet_with_storage: Wallet) -> None:
        """Test wait_for_authentication method."""
        # This is a BRC-100 interface method with specific signature
        result = wallet_with_storage.wait_for_authentication({})
        assert isinstance(result, dict)


class TestWalletNetworkMethods:
    """Test wallet network-related methods."""

    def test_get_network(self, wallet_with_storage: Wallet) -> None:
        """Test get_network method."""
        # This is a BRC-100 interface method with specific signature
        result = wallet_with_storage.get_network({})
        assert isinstance(result, dict)
        assert "network" in result

    def test_get_version(self, wallet_with_storage: Wallet) -> None:
        """Test get_version method."""
        # This is a BRC-100 interface method with specific signature
        result = wallet_with_storage.get_version({})
        assert isinstance(result, dict)
        assert "version" in result

    def test_get_height(self, wallet_with_storage: Wallet) -> None:
        """Test get_height method."""
        # This is a BRC-100 interface method with specific signature
        mock_services = Mock()
        mock_services.get_height.return_value = {"height": 800000}

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.get_height({})
            assert isinstance(result, dict)


class TestWalletStoragePartyMethods:
    """Test wallet storage party methods."""

    def test_storage_party(self, wallet_with_storage: Wallet) -> None:
        """Test storage_party property."""
        result = wallet_with_storage.storage_party
        assert isinstance(result, str)
        assert len(result) > 0


class TestWalletHeaderMethods:
    """Test wallet header-related methods."""

    def test_get_header(self, wallet_with_storage: Wallet) -> None:
        """Test get_header method."""
        args = {"height": 800000}

        # Mock services to return bytes (which gets converted to hex)
        # 32 bytes -> 64 hex characters
        header_bytes = bytes.fromhex("abcd" * 16)  # 32 bytes
        mock_services = Mock()
        mock_services.get_header_for_height.return_value = header_bytes

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.get_header(args)
            assert result == {"header": header_bytes.hex()}

    def test_get_header_for_height(self, wallet_with_storage: Wallet) -> None:
        """Test get_header_for_height method."""
        args = {"height": 800000}

        # Mock services to return bytes (which gets converted to hex)
        # 32 bytes -> 64 hex characters
        header_bytes = bytes.fromhex("abcd" * 16)  # 32 bytes
        mock_services = Mock()
        mock_services.get_header_for_height.return_value = header_bytes

        with patch.object(wallet_with_storage, "services", mock_services):
            result = wallet_with_storage.get_header_for_height(args)
            assert result == {"header": header_bytes.hex()}
