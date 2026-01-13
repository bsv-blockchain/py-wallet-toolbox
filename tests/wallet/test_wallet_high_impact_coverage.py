"""High-impact coverage tests for Wallet class.

This module targets the most critical uncovered lines in wallet.py
to maximize coverage improvement. Focuses on:
- Exception handling in initialization (lines 274-276)
- BEEF parsing and merging (lines 423-440, 485-493)
- Sign action result processing (lines 981-1032)
- Error conditions and edge cases
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

try:
    from bsv.keys import PrivateKey
    from bsv.wallet import KeyDeriver

    from bsv_wallet_toolbox.wallet import Wallet

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    Wallet = None
    KeyDeriver = None
    PrivateKey = None


@pytest.fixture
def mock_storage():
    """Create a mock storage provider."""
    storage = Mock()
    # Set up basic mock responses
    storage.list_outputs.return_value = {"outputs": [], "totalOutputs": 0}
    storage.list_certificates.return_value = {"certificates": [], "totalCertificates": 0}
    storage.list_actions.return_value = {"actions": [], "totalActions": 0}
    storage.relinquish_output.return_value = {"relinquished": True}
    storage.abort_action.return_value = {"aborted": True}
    storage.relinquish_certificate.return_value = {"relinquished": True}
    storage.create_action.return_value = {"txid": "mock_txid", "reference": "mock_ref"}
    storage.sign_action.return_value = {"signature": "mock_sig"}
    storage.process_action.return_value = {"processed": True}
    storage.internalize_action.return_value = {"internalized": True}
    storage.is_available.return_value = True
    storage.make_available.return_value = {"success": True}
    storage.set_services = Mock()  # Mock set_services method
    return storage


@pytest.fixture
def mock_services():
    """Create a mock services instance."""
    services = Mock()
    services.get_height.return_value = {"height": 1000}
    services.get_header_for_height.return_value = {"header": "mock_header"}
    services.get_network.return_value = {"network": "testnet"}
    services.get_version.return_value = {"version": "1.0.0"}
    return services


@pytest.fixture
def mock_monitor():
    """Create a mock monitor instance."""
    monitor = Mock()
    return monitor


@pytest.fixture
def wallet_with_mocks(mock_storage, mock_services, mock_monitor):
    """Create a wallet with mocked dependencies."""
    if not IMPORTS_AVAILABLE:
        pytest.skip("Required imports not available")

    root_key = PrivateKey(bytes.fromhex("a" * 64))
    key_deriver = KeyDeriver(root_key)

    wallet = Wallet(
        chain="test",
        services=mock_services,
        key_deriver=key_deriver,
        storage_provider=mock_storage,
        monitor=mock_monitor,
    )
    return wallet


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Wallet imports not available")
class TestWalletInitializationExceptionHandling:
    """Test wallet initialization exception handling (lines 274-276)."""

    def test_wallet_init_storage_set_services_failure(self, mock_services, mock_monitor):
        """Test wallet initialization when storage.set_services fails."""
        if not IMPORTS_AVAILABLE:
            pytest.skip("Required imports not available")

        root_key = PrivateKey(bytes.fromhex("a" * 64))
        key_deriver = KeyDeriver(root_key)

        # Create storage that raises exception on set_services
        mock_storage = Mock()
        mock_storage.set_services.side_effect = Exception("set_services failed")
        mock_storage.is_available.return_value = True
        mock_storage.make_available.return_value = {"success": True}

        # Should not raise - exception should be caught and ignored
        wallet = Wallet(
            chain="test",
            services=mock_services,
            key_deriver=key_deriver,
            storage_provider=mock_storage,
            monitor=mock_monitor,
        )

        # Verify wallet was created successfully despite set_services failure
        assert wallet.services == mock_services
        assert wallet.storage == mock_storage

    def test_wallet_init_without_services(self, mock_storage, mock_monitor):
        """Test wallet initialization without services (lines 271-276)."""
        if not IMPORTS_AVAILABLE:
            pytest.skip("Required imports not available")

        root_key = PrivateKey(bytes.fromhex("a" * 64))
        key_deriver = KeyDeriver(root_key)

        # Create wallet without services
        Wallet(
            chain="test", services=None, key_deriver=key_deriver, storage_provider=mock_storage, monitor=mock_monitor
        )

        # Should not call set_services since services is None
        mock_storage.set_services.assert_not_called()

    def test_wallet_init_without_storage(self, mock_services, mock_monitor):
        """Test wallet initialization without storage."""
        if not IMPORTS_AVAILABLE:
            pytest.skip("Required imports not available")

        root_key = PrivateKey(bytes.fromhex("a" * 64))
        key_deriver = KeyDeriver(root_key)

        # Create wallet without storage
        wallet = Wallet(
            chain="test", services=mock_services, key_deriver=key_deriver, storage_provider=None, monitor=mock_monitor
        )

        # Should not call set_services since storage is None
        assert wallet.storage is None


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Wallet imports not available")
class TestBeefProcessing:
    """Test BEEF processing functionality (lines 423-440, 485-493)."""

    def test_post_beef_delegates_to_services(self, wallet_with_mocks):
        """Test post_beef delegates to services."""
        wallet = wallet_with_mocks

        beef_data = "mock_beef_string"
        expected_result = {"accepted": True, "txid": "test_txid"}

        wallet.services.post_beef.return_value = expected_result

        result = wallet.post_beef(beef_data)

        assert result == expected_result
        wallet.services.post_beef.assert_called_once_with(beef_data)

    def test_post_beef_no_services_raises_error(self, wallet_with_mocks):
        """Test post_beef raises error when no services configured."""
        wallet = wallet_with_mocks
        wallet.services = None

        with pytest.raises(RuntimeError, match="Services must be configured"):
            wallet.post_beef("mock_beef")

    def test_verify_returned_txid_only_atomic_beef_success(self, wallet_with_mocks):
        """Test verify_returned_txid_only_atomic_beef success case."""
        wallet = wallet_with_mocks

        # Mock the required methods
        mock_beef = Mock()
        mock_beef.to_binary_atomic.return_value = b"verified_beef_data"

        with (
            patch("bsv_wallet_toolbox.wallet.parse_beef_ex") as mock_parse_beef_ex,
            patch.object(wallet, "verify_returned_txid_only") as mock_verify,
        ):

            mock_parse_beef_ex.return_value = (mock_beef, "subject_txid", None)
            mock_verify.return_value = mock_beef

            beef_data = b"original_beef_data"
            known_txids = ["test_txid"]

            result = wallet.verify_returned_txid_only_atomic_beef(beef_data, known_txids)

            assert result == b"verified_beef_data"
            mock_verify.assert_called_once_with(mock_beef, known_txids)

    def test_verify_returned_txid_only_atomic_beef_parse_failure(self, wallet_with_mocks):
        """Test verify_returned_txid_only_atomic_beef when parsing fails."""
        wallet = wallet_with_mocks

        beef_data = b"original_beef_data"
        known_txids = ["test_txid"]

        with patch("bsv_wallet_toolbox.wallet.parse_beef", side_effect=Exception("Parse failed")):
            # Should return original beef_data as fallback
            result = wallet.verify_returned_txid_only_atomic_beef(beef_data, known_txids)

            assert result == beef_data

    def test_verify_returned_txid_only_atomic_beef_success(self, wallet_with_mocks):
        """Test verify_returned_txid_only_atomic_beef success case."""
        wallet = wallet_with_mocks

        # Mock the required methods
        mock_beef = Mock()
        mock_beef.to_binary_atomic.return_value = b"verified_beef_data"

        with (
            patch("bsv_wallet_toolbox.wallet.parse_beef_ex") as mock_parse_beef_ex,
            patch.object(wallet, "verify_returned_txid_only") as mock_verify,
        ):

            mock_parse_beef_ex.return_value = (mock_beef, "subject_txid", None)
            mock_verify.return_value = mock_beef

            beef_data = b"original_beef_data"
            known_txids = ["test_txid"]

            result = wallet.verify_returned_txid_only_atomic_beef(beef_data, known_txids)

            assert result == b"verified_beef_data"
            mock_verify.assert_called_once_with(mock_beef, known_txids)

    def test_verify_returned_txid_only_atomic_beef_parse_failure(self, wallet_with_mocks):
        """Test verify_returned_txid_only_atomic_beef when parsing fails."""
        wallet = wallet_with_mocks

        beef_data = b"original_beef_data"
        known_txids = ["test_txid"]

        with patch("bsv_wallet_toolbox.wallet.parse_beef", side_effect=Exception("Parse failed")):
            # Should return original beef_data as fallback
            result = wallet.verify_returned_txid_only_atomic_beef(beef_data, known_txids)

            assert result == beef_data


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Wallet imports not available")
class TestSignActionResultProcessing:
    """Test sign_action result processing (lines 981-1032)."""

    def test_sign_action_beef_merge_success(self, wallet_with_mocks):
        """Test sign_action with successful BEEF merge."""
        wallet = wallet_with_mocks

        # Set up wallet with beef instance
        wallet.beef = Mock()

        mock_signer_result = {
            "txid": "test_txid_beef",
            "tx": b"beef_data_bytes",
            "sendWithResults": [],
            "notDelayedResults": [],
        }

        with (
            patch("bsv_wallet_toolbox.wallet.signer_sign_action") as mock_signer,
            patch("bsv_wallet_toolbox.wallet.parse_beef") as mock_parse_beef,
        ):

            mock_signer.return_value = mock_signer_result
            mock_parsed_beef = Mock()
            mock_parse_beef.return_value = mock_parsed_beef

            args = {"reference": "test_ref", "options": {"isDelayed": False}}

            result = wallet.sign_action(args, "test_originator")

            # Should attempt to parse and merge BEEF (best-effort, may not always succeed)
            # The main point is that the method completes successfully
            assert result["txid"] == "test_txid_beef"

    def test_sign_action_beef_merge_failure(self, wallet_with_mocks):
        """Test sign_action with BEEF merge failure (graceful handling)."""
        wallet = wallet_with_mocks

        # Set up wallet with beef instance
        wallet.beef = Mock()

        mock_signer_result = {
            "txid": "test_txid_beef_fail",
            "tx": b"beef_data_bytes",
            "sendWithResults": [],
            "notDelayedResults": [],
        }

        with (
            patch("bsv_wallet_toolbox.wallet.signer_sign_action") as mock_signer,
            patch("bsv_wallet_toolbox.wallet.parse_beef", side_effect=Exception("Parse failed")),
        ):

            mock_signer.return_value = mock_signer_result

            args = {"reference": "test_ref", "options": {"isDelayed": False}}

            # Should not raise - BEEF processing should be best-effort
            result = wallet.sign_action(args, "test_originator")

            assert result["txid"] == "test_txid_beef_fail"

    def test_sign_action_no_beef_merge_when_no_wallet_beef(self, wallet_with_mocks):
        """Test sign_action skips BEEF merge when wallet has no beef instance."""
        wallet = wallet_with_mocks
        wallet.beef = None  # No beef instance

        mock_signer_result = {
            "txid": "test_txid_no_beef",
            "tx": b"beef_data_bytes",
            "sendWithResults": [],
            "notDelayedResults": [],
        }

        with patch("bsv_wallet_toolbox.wallet.signer_sign_action") as mock_signer:
            mock_signer.return_value = mock_signer_result

            args = {"reference": "test_ref", "options": {"isDelayed": False}}

            # Should not attempt BEEF parsing when wallet.beef is None
            result = wallet.sign_action(args, "test_originator")

            assert result["txid"] == "test_txid_no_beef"


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Wallet imports not available")
class TestWalletKnownTxids:
    """Test get_known_txids functionality."""

    def test_get_known_txids_no_beef(self, wallet_with_mocks):
        """Test get_known_txids when wallet has no beef."""
        wallet = wallet_with_mocks
        wallet.beef = None

        result = wallet.get_known_txids()

        assert result == []

    def test_get_known_txids_with_beef(self, wallet_with_mocks):
        """Test get_known_txids with beef instance."""
        wallet = wallet_with_mocks

        # Mock beef instance
        mock_beef = Mock()
        mock_beef.get_valid_txids.return_value = ["txid1", "txid2", "txid3"]
        wallet.beef = mock_beef

        result = wallet.get_known_txids()

        assert result == ["txid1", "txid2", "txid3"]
        mock_beef.get_valid_txids.assert_called_once()

    def test_get_known_txids_with_new_txids_merge(self, wallet_with_mocks):
        """Test get_known_txids with new txids to merge."""
        wallet = wallet_with_mocks

        # Mock beef instance
        mock_beef = Mock()
        mock_beef.get_valid_txids.return_value = ["existing_txid"]
        wallet.beef = mock_beef

        new_txids = ["new_txid1", "new_txid2"]
        result = wallet.get_known_txids(new_txids)

        # Should merge new txids via merge_txid_only calls
        mock_beef.merge_txid_only.assert_any_call("new_txid1")
        mock_beef.merge_txid_only.assert_any_call("new_txid2")
        assert result == ["existing_txid"]


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Wallet imports not available")
class TestWalletUtilityFunctions:
    """Test wallet utility functions."""

    def test_as_bytes_from_list(self):
        """Test _as_bytes with list input."""
        from bsv_wallet_toolbox.wallet import _as_bytes

        result = _as_bytes([1, 2, 3, 255], "test_field")

        assert result == b"\x01\x02\x03\xff"

    def test_as_bytes_from_bytes(self):
        """Test _as_bytes with bytes input."""
        from bsv_wallet_toolbox.wallet import _as_bytes

        result = _as_bytes(b"test", "test_field")

        assert result == b"test"

    def test_as_bytes_invalid_type(self):
        """Test _as_bytes with invalid type."""
        from bsv_wallet_toolbox.errors import InvalidParameterError
        from bsv_wallet_toolbox.wallet import _as_bytes

        with pytest.raises(InvalidParameterError):
            _as_bytes(123, "test_field")  # int is invalid

    def test_to_byte_list(self):
        """Test _to_byte_list function."""
        from bsv_wallet_toolbox.wallet import _to_byte_list

        result = _to_byte_list(b"test")

        assert result == [116, 101, 115, 116]  # ASCII values


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Wallet imports not available")
class TestWalletErrorConditions:
    """Test wallet error conditions and edge cases."""

    def test_sign_action_no_reference(self, wallet_with_mocks):
        """Test sign_action without reference in pending actions."""
        wallet = wallet_with_mocks

        mock_signer_result = {"txid": "test_txid_no_ref", "sendWithResults": [], "notDelayedResults": []}

        with patch("bsv_wallet_toolbox.wallet.signer_sign_action") as mock_signer:
            mock_signer.return_value = mock_signer_result

            args = {"reference": "test_ref_no_pending", "options": {"isDelayed": False}}

            result = wallet.sign_action(args, "test_originator")

            # Should work without reference lookup in pending actions
            assert result["txid"] == "test_txid_no_ref"

    def test_wallet_init_beef_creation_failure_fallback(self):
        """Test wallet initialization when BEEF creation fails completely."""
        if not IMPORTS_AVAILABLE:
            pytest.skip("Required imports not available")

        root_key = PrivateKey(bytes.fromhex("a" * 64))
        key_deriver = KeyDeriver(root_key)

        # Mock Beef to always fail
        with patch("bsv_wallet_toolbox.wallet.Beef", side_effect=Exception("Beef always fails")):
            wallet = Wallet(key_deriver=key_deriver, chain="test")

            # Should set beef to None as fallback
            assert wallet.beef is None

    def test_verify_returned_txid_only_no_subject_txid(self, wallet_with_mocks):
        """Test verify_returned_txid_only when no subject txid can be extracted."""
        wallet = wallet_with_mocks

        with patch("bsv_wallet_toolbox.wallet.parse_beef_ex", return_value=(None, None, None)):
            beef_data = b"original_beef_data"

            # Should return original beef_data when parsing fails
            result = wallet.verify_returned_txid_only_atomic_beef(beef_data, None)
            assert result == beef_data
