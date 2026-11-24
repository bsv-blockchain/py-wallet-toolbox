"""Expanded coverage tests for Bitails provider.

This module provides additional test coverage for Bitails provider methods,
focusing on error handling, edge cases, and boundary conditions.
"""

from unittest.mock import Mock, patch

import pytest
import requests

from bsv_wallet_toolbox.services.providers.bitails import (
    Bitails,
    BitailsConfig,
    BitailsPostRawsResult,
    GetMerklePathResult,
    PostBeefResult,
)
from bsv_wallet_toolbox.utils.random_utils import double_sha256_be


class TestBitailsInitialization:
    """Test Bitails initialization and configuration."""

    def test_init_default_config(self) -> None:
        """Test initialization with default configuration."""
        bitails = Bitails()

        assert bitails.chain == "main"
        assert bitails.config.api_key is None
        assert bitails.config.headers is None

    def test_init_custom_config(self) -> None:
        """Test initialization with custom configuration."""
        config = BitailsConfig(api_key="test_key", headers={"X-Custom": "value"})
        bitails = Bitails(chain="test", config=config)

        assert bitails.chain == "test"
        assert bitails.config.api_key == "test_key"
        assert bitails.config.headers == {"X-Custom": "value"}

    def test_init_minimal_config(self) -> None:
        """Test initialization with minimal configuration."""
        bitails = Bitails(chain="main")

        assert bitails.chain == "main"
        assert isinstance(bitails.config, BitailsConfig)

    def test_get_http_headers_no_auth(self) -> None:
        """Test get_http_headers without authentication."""
        bitails = Bitails()

        headers = bitails.get_http_headers()

        expected = {"Content-Type": "application/json", "Accept": "application/json"}
        assert headers == expected

    def test_get_http_headers_with_api_key(self) -> None:
        """Test get_http_headers with API key."""
        config = BitailsConfig(api_key="test_key_123")
        bitails = Bitails(config=config)

        headers = bitails.get_http_headers()

        expected = {"Content-Type": "application/json", "Accept": "application/json", "Authorization": "test_key_123"}
        assert headers == expected

    def test_get_http_headers_with_custom_headers(self) -> None:
        """Test get_http_headers with custom headers."""
        config = BitailsConfig(api_key="key123", headers={"X-Custom": "value", "User-Agent": "test"})
        bitails = Bitails(config=config)

        headers = bitails.get_http_headers()

        expected = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "key123",
            "X-Custom": "value",
            "User-Agent": "test",
        }
        assert headers == expected

    def test_get_http_headers_custom_headers_override_defaults(self) -> None:
        """Test that custom headers can override defaults."""
        config = BitailsConfig(headers={"Content-Type": "text/plain"})
        bitails = Bitails(config=config)

        headers = bitails.get_http_headers()

        assert headers["Content-Type"] == "text/plain"
        assert headers["Accept"] == "application/json"


class TestBitailsPostBeef:
    """Test Bitails post_beef method."""

    @pytest.fixture
    def bitails(self) -> Bitails:
        """Create Bitails instance for testing."""
        return Bitails()

    def test_post_beef_success(self, bitails: Bitails) -> None:
        """Test successful post_beef operation."""
        mock_beef = {"format": "BEEF", "version": 1}
        txids = ["txid1", "txid2"]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "txids": ["txid1", "txid2"]}

        with patch("requests.post", return_value=mock_response) as mock_post:
            result = bitails.post_beef(mock_beef, txids)

            assert isinstance(result, PostBeefResult)
            assert result.success is True
            assert result.txids == ["txid1", "txid2"]

            # Only the raws go in the body (TS); a Beef object there was a TypeError.
            mock_post.assert_called_once()
            assert set(mock_post.call_args[1]["json"]) == {"raws"}

    def test_post_beef_http_error(self, bitails: Bitails) -> None:
        """Test post_beef with HTTP error."""
        mock_beef = {"format": "BEEF"}
        txids = ["txid1"]

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.raise_for_status.side_effect = requests.HTTPError("400 Bad Request")

        with patch("requests.post", return_value=mock_response):
            result = bitails.post_beef(mock_beef, txids)

            assert isinstance(result, PostBeefResult)
            assert result.success is False
            assert "400 Bad Request" in result.error_message

    def test_post_beef_connection_error(self, bitails: Bitails) -> None:
        """Test post_beef with connection error."""
        mock_beef = {"format": "BEEF"}
        txids = ["txid1"]

        with patch("requests.post", side_effect=requests.ConnectionError("Network error")):
            result = bitails.post_beef(mock_beef, txids)

            assert isinstance(result, PostBeefResult)
            assert result.success is False
            assert "Network error" in result.error_message

    def test_post_beef_timeout_error(self, bitails: Bitails) -> None:
        """Test post_beef with timeout error."""
        mock_beef = {"format": "BEEF"}
        txids = ["txid1"]

        with patch("requests.post", side_effect=requests.Timeout("Request timeout")):
            result = bitails.post_beef(mock_beef, txids)

            assert isinstance(result, PostBeefResult)
            assert result.success is False
            assert "Request timeout" in result.error_message

    def test_post_beef_invalid_json_response(self, bitails: Bitails) -> None:
        """Test post_beef with invalid JSON response."""
        mock_beef = {"format": "BEEF"}
        txids = ["txid1"]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch("requests.post", return_value=mock_response):
            result = bitails.post_beef(mock_beef, txids)

            assert isinstance(result, PostBeefResult)
            assert result.success is False
            assert "Invalid JSON" in result.error_message

    def test_post_beef_empty_txids(self, bitails: Bitails) -> None:
        """Test post_beef with empty txids list."""
        mock_beef = {"format": "BEEF"}
        txids = []

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "txids": []}

        with patch("requests.post", return_value=mock_response):
            result = bitails.post_beef(mock_beef, txids)

            assert isinstance(result, PostBeefResult)
            assert result.success is True
            assert result.txids == []


class TestBitailsPostRaws:
    """Test Bitails post_raws method."""

    @pytest.fixture
    def bitails(self) -> Bitails:
        """Create Bitails instance for testing."""
        return Bitails()

    @staticmethod
    def _txid(raw: str) -> str:
        return bytes(double_sha256_be(bytes.fromhex(raw))).hex()

    def test_post_raws_success(self, bitails: Bitails) -> None:
        """Rows come back in raws order, each with its raw's txid."""
        raws = ["deadbeef", "beefdead"]
        txids = [self._txid(r) for r in raws]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"txid": t} for t in txids]

        with patch("requests.post", return_value=mock_response):
            results = bitails.post_raws(raws, txids)

            assert [r.txid for r in results] == txids
            assert all(isinstance(r, BitailsPostRawsResult) and r.success for r in results)

    def test_post_raws_partial_success(self, bitails: Bitails) -> None:
        """A row without a txid belongs to the raw in its position."""
        raws = ["deadbeef", "beefdead"]
        txids = [self._txid(r) for r in raws]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"txid": txids[0]}, {"error": "Invalid transaction"}]

        with patch("requests.post", return_value=mock_response):
            results = bitails.post_raws(raws, txids)

            assert [r.txid for r in results] == txids
            assert results[0].success is True
            assert results[1].success is False
            assert "Invalid transaction" in results[1].error_message

    @pytest.mark.parametrize(
        "rows",
        [
            [{"txid": "other"}],  # a txid that is not the raw's
            [{}, {}],  # more rows than raws
        ],
    )
    def test_post_raws_rows_not_matching_the_raws_fail_all(self, bitails: Bitails, rows: list) -> None:
        """TS postRaws: a wrong count or txid means no row can be trusted."""
        raws = ["deadbeef"]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = rows

        with patch("requests.post", return_value=mock_response):
            results = bitails.post_raws(raws)

            assert [r.txid for r in results] == [self._txid("deadbeef")]
            assert results[0].success is False
            assert results[0].error is None  # a service error, not a refusal of the tx

    def test_post_raws_empty_lists(self, bitails: Bitails) -> None:
        """Test post_raws with empty lists."""
        raws = []
        txids = []

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        with patch("requests.post", return_value=mock_response):
            results = bitails.post_raws(raws, txids)

            assert len(results) == 0

    def test_post_raws_http_error(self, bitails: Bitails) -> None:
        """Test post_raws with HTTP error."""
        raws = ["deadbeef"]
        txids = ["txid1"]

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Internal Server Error")

        with patch("requests.post", return_value=mock_response):
            results = bitails.post_raws(raws, txids)

            assert len(results) == 1
            assert results[0].success is False
            assert "500 Internal Server Error" in results[0].error_message

    def test_post_raws_connection_error(self, bitails: Bitails) -> None:
        """Test post_raws with connection error."""
        raws = ["deadbeef"]
        txids = ["txid1"]

        with patch("requests.post", side_effect=requests.ConnectionError("Network down")):
            results = bitails.post_raws(raws, txids)

            assert len(results) == 1
            assert results[0].success is False
            assert "Network down" in results[0].error_message


class TestBitailsGetMerklePath:
    """Test Bitails get_merkle_path method."""

    @pytest.fixture
    def bitails(self) -> Bitails:
        """Create Bitails instance for testing."""
        return Bitails()

    def test_get_merkle_path_not_found(self, bitails: Bitails) -> None:
        """A 404 returns notes and no merklePath (the TS / WhatsOnChain result shape)."""
        mock_response = Mock(status_code=404, reason="Not Found")

        with patch("requests.get", return_value=mock_response):
            result = bitails.get_merkle_path("unknown_txid", Mock())

        assert result["name"] == "BitailsTsc"
        assert "merklePath" not in result
        assert result["notes"][-1]["what"] == "getMerklePathNotFound"

    @pytest.mark.parametrize(
        "error", [requests.HTTPError("403 Forbidden"), requests.ConnectionError("Network timeout")]
    )
    def test_get_merkle_path_request_error(self, bitails: Bitails, error: Exception) -> None:
        with patch("requests.get", side_effect=error):
            result = bitails.get_merkle_path("test_txid", Mock())

        assert "merklePath" not in result
        assert str(error) in result["error"]["message"]

    def test_get_merkle_path_invalid_json(self, bitails: Bitails) -> None:
        mock_response = Mock(status_code=200, reason="OK", content=b"x")
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch("requests.get", return_value=mock_response):
            result = bitails.get_merkle_path("test_txid", Mock())

        assert "merklePath" not in result
        assert "Invalid JSON" in result["error"]["message"]


class TestBitailsGetTransactionStatus:
    """Test Bitails get_transaction_status method."""

    @pytest.fixture
    def bitails(self) -> Bitails:
        """Create Bitails instance for testing."""
        return Bitails()

    def test_get_transaction_status_success(self, bitails: Bitails) -> None:
        """Test successful get_transaction_status operation."""
        txid = "test_txid"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"txid": "test_txid", "confirmations": 6, "blockHeight": 800000}

        with patch("requests.get", return_value=mock_response):
            result = bitails.get_transaction_status(txid)

            assert isinstance(result, dict)
            assert result["txid"] == "test_txid"
            assert result["confirmations"] == 6
            assert result["blockHeight"] == 800000

    def test_get_transaction_status_not_found(self, bitails: Bitails) -> None:
        """Test get_transaction_status for non-existent transaction."""
        txid = "unknown_txid"

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Transaction not found"}

        with patch("requests.get", return_value=mock_response):
            result = bitails.get_transaction_status(txid)

            assert isinstance(result, dict)
            assert "error" in result
            assert result["error"] == "Transaction not found"

    def test_get_transaction_status_http_error(self, bitails: Bitails) -> None:
        """Test get_transaction_status with HTTP error."""
        txid = "test_txid"

        with patch("requests.get", side_effect=requests.HTTPError("500 Internal Server Error")):
            result = bitails.get_transaction_status(txid)

            assert isinstance(result, dict)
            assert "error" in result
            assert "500 Internal Server Error" in result["error"]

    def test_get_transaction_status_connection_error(self, bitails: Bitails) -> None:
        """Test get_transaction_status with connection error."""
        txid = "test_txid"

        with patch("requests.get", side_effect=requests.ConnectionError("Network error")):
            result = bitails.get_transaction_status(txid)

            assert isinstance(result, dict)
            assert "error" in result
            assert "Network error" in result["error"]

    def test_get_transaction_status_invalid_json(self, bitails: Bitails) -> None:
        """Test get_transaction_status with invalid JSON response."""
        txid = "test_txid"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch("requests.get", return_value=mock_response):
            result = bitails.get_transaction_status(txid)

            assert isinstance(result, dict)
            assert "error" in result
            assert "Invalid JSON" in result["error"]

    def test_get_transaction_status_with_use_next(self, bitails: Bitails) -> None:
        """Test get_transaction_status with use_next parameter."""
        txid = "test_txid"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"confirmations": 0}

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = bitails.get_transaction_status(txid, use_next=True)

            assert isinstance(result, dict)
            assert result["confirmations"] == 0

            # Verify use_next parameter is passed in URL
            call_args = mock_get.call_args
            assert "useNext=true" in call_args[0][0]


class TestBitailsDataClasses:
    """Test Bitails data classes."""

    def test_bitails_config_defaults(self) -> None:
        """Test BitailsConfig default values."""
        config = BitailsConfig()

        assert config.api_key is None
        assert config.headers is None

    def test_bitails_config_custom_values(self) -> None:
        """Test BitailsConfig with custom values."""
        headers = {"X-Test": "value"}
        config = BitailsConfig(api_key="key123", headers=headers)

        assert config.api_key == "key123"
        assert config.headers == headers

    def test_bitails_post_raws_result_defaults(self) -> None:
        """Test BitailsPostRawsResult default values."""
        result = BitailsPostRawsResult()

        assert result.txid is None
        assert result.success is False
        assert result.error_message == ""

    def test_bitails_post_raws_result_custom_values(self) -> None:
        """Test BitailsPostRawsResult with custom values."""
        result = BitailsPostRawsResult(txid="test_txid", success=True, error_message="some error")

        assert result.txid == "test_txid"
        assert result.success is True
        assert result.error_message == "some error"

    def test_post_beef_result_defaults(self) -> None:
        """Test PostBeefResult default values."""
        result = PostBeefResult()

        assert result.success is False
        assert result.txids == []
        assert result.error_message == ""

    def test_post_beef_result_custom_values(self) -> None:
        """Test PostBeefResult with custom values."""
        result = PostBeefResult(success=True, txids=["tx1", "tx2"], error_message="partial success")

        assert result.success is True
        assert result.txids == ["tx1", "tx2"]
        assert result.error_message == "partial success"

    def test_get_merkle_path_result_defaults(self) -> None:
        """Test GetMerklePathResult default values."""
        result = GetMerklePathResult()

        assert result.success is False
        assert result.merkle_path is None
        assert result.header is None
        assert result.error_message == ""

    def test_get_merkle_path_result_custom_values(self) -> None:
        """Test GetMerklePathResult with custom values."""
        result = GetMerklePathResult(
            success=True, merkle_path={"path": "data"}, header={"hash": "block_hash"}, error_message="some error"
        )

        assert result.success is True
        assert result.merkle_path == {"path": "data"}
        assert result.header == {"hash": "block_hash"}
        assert result.error_message == "some error"
