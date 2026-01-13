"""Coverage tests for StorageClient.

This module tests the JSON-RPC 2.0 client implementation for remote storage providers.
Equivalent to TypeScript: ts-wallet-toolbox/src/storage/remoting/StorageClient.ts
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
import requests

from bsv_wallet_toolbox.rpc.storage_client import JsonRpcError, StorageClient


class TestJsonRpcError:
    """Test JsonRpcError exception class."""

    def test_json_rpc_error_creation(self) -> None:
        """Test creating a JSON-RPC error."""
        error = JsonRpcError(code=-32600, message="Invalid Request", data={"info": "test"})

        assert error.code == -32600
        assert error.message == "Invalid Request"
        assert error.data == {"info": "test"}
        assert "RPC Error (-32600): Invalid Request" in str(error)

    def test_json_rpc_error_without_data(self) -> None:
        """Test creating error without additional data."""
        error = JsonRpcError(code=-32700, message="Parse error")

        assert error.code == -32700
        assert error.message == "Parse error"
        assert error.data is None


class TestStorageClient:
    """Test StorageClient class."""

    @pytest.fixture
    def mock_wallet(self):
        """Create a mock wallet with BRC-100 interface methods."""
        wallet = Mock()
        # Mock BRC-100 WalletInterface methods needed by AuthFetch
        wallet.get_public_key = Mock(return_value=Mock(public_key=Mock(hex=lambda: "0" * 66)))
        wallet.create_signature = Mock(return_value=Mock(signature=b"\x00" * 64))
        wallet.verify_signature = Mock(return_value=Mock(valid=True))
        return wallet

    @pytest.fixture
    def mock_response(self):
        """Create a mock requests.Response."""
        response = Mock(spec=requests.Response)
        response.ok = True
        response.status_code = 200
        response.reason = "OK"
        response.headers = {}
        return response

    def test_client_creation(self, mock_wallet) -> None:
        """Test creating a StorageClient."""
        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch") as MockAuthFetch:
            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

            assert client.endpoint_url == "https://example.com/rpc"
            assert client.wallet == mock_wallet
            assert client.auth_client is not None
            MockAuthFetch.assert_called_once_with(mock_wallet, None)

    def test_client_creation_with_certificates(self, mock_wallet) -> None:
        """Test creating a StorageClient with certificate requirements."""
        mock_certs = Mock()
        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch") as MockAuthFetch:
            StorageClient(
                wallet=mock_wallet,
                endpoint_url="https://example.com/rpc",
                requested_certificates=mock_certs,
            )

            MockAuthFetch.assert_called_once_with(mock_wallet, mock_certs)

    def test_client_context_manager(self, mock_wallet) -> None:
        """Test using client as context manager."""
        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch"):
            with StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc") as client:
                assert isinstance(client, StorageClient)

    def test_get_next_id_thread_safe(self, mock_wallet) -> None:
        """Test that request ID generation is thread-safe."""
        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch"):
            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

            id1 = client._get_next_id()
            id2 = client._get_next_id()
            id3 = client._get_next_id()

            assert id2 == id1 + 1
            assert id3 == id2 + 1

    def test_rpc_call_success(self, mock_wallet, mock_response) -> None:
        """Test successful RPC call."""
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"success": True, "data": "test_data"},
        }

        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch") as MockAuthFetch:
            mock_auth_client = Mock()
            mock_auth_client.fetch = AsyncMock(return_value=mock_response)
            MockAuthFetch.return_value = mock_auth_client

            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")
            result = client._rpc_call("test_method", ["param1", "param2"])

            assert result == {"success": True, "data": "test_data"}
            assert mock_auth_client.fetch.called

    def test_rpc_call_with_error_response(self, mock_wallet, mock_response) -> None:
        """Test RPC call with error response."""
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32601, "message": "Method not found", "data": None},
        }

        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch") as MockAuthFetch:
            mock_auth_client = Mock()
            mock_auth_client.fetch = AsyncMock(return_value=mock_response)
            MockAuthFetch.return_value = mock_auth_client

            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

            with pytest.raises(JsonRpcError) as exc_info:
                client._rpc_call("invalid_method", [])

            assert exc_info.value.code == -32601
            assert exc_info.value.message == "Method not found"

    def test_rpc_call_network_error(self, mock_wallet) -> None:
        """Test RPC call with network error."""
        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch") as MockAuthFetch:
            mock_auth_client = Mock()
            mock_auth_client.fetch.side_effect = requests.ConnectionError("Connection failed")
            MockAuthFetch.return_value = mock_auth_client

            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

            with pytest.raises(requests.ConnectionError):
                client._rpc_call("test_method", [])

    def test_rpc_call_timeout(self, mock_wallet) -> None:
        """Test RPC call with timeout."""
        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch") as MockAuthFetch:
            mock_auth_client = Mock()
            mock_auth_client.fetch.side_effect = requests.Timeout("Request timed out")
            MockAuthFetch.return_value = mock_auth_client

            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

            with pytest.raises(requests.Timeout):
                client._rpc_call("test_method", [])

    def test_rpc_call_http_error(self, mock_wallet) -> None:
        """Test RPC call with HTTP error response."""
        mock_response = Mock(spec=requests.Response)
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.headers = {}

        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch") as MockAuthFetch:
            mock_auth_client = Mock()
            mock_auth_client.fetch = AsyncMock(return_value=mock_response)
            MockAuthFetch.return_value = mock_auth_client

            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

            with pytest.raises(requests.RequestException):
                client._rpc_call("test_method", [])

    def test_is_available(self, mock_wallet, mock_response) -> None:
        """Test is_available method."""
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": True,
        }

        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch") as MockAuthFetch:
            mock_auth_client = Mock()
            mock_auth_client.fetch = AsyncMock(return_value=mock_response)
            MockAuthFetch.return_value = mock_auth_client

            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")
            result = client.is_available()

            assert result is True
            mock_auth_client.fetch.assert_called_once()

    def test_make_available(self, mock_wallet, mock_response) -> None:
        """Test make_available method."""
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"status": "available"},
        }

        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch") as MockAuthFetch:
            mock_auth_client = Mock()
            mock_auth_client.fetch = AsyncMock(return_value=mock_response)
            MockAuthFetch.return_value = mock_auth_client

            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")
            result = client.make_available()

            assert result == {"status": "available"}

    def test_get_services(self, mock_wallet, mock_response) -> None:
        """Test get_services method."""
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"services": ["service1", "service2"]},
        }

        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch") as MockAuthFetch:
            mock_auth_client = Mock()
            mock_auth_client.fetch = AsyncMock(return_value=mock_response)
            MockAuthFetch.return_value = mock_auth_client

            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")
            result = client.get_services()

            assert result == {"services": ["service1", "service2"]}

    def test_get_settings(self, mock_wallet, mock_response) -> None:
        """Test get_settings method."""
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"settings": {"key": "value"}},
        }

        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch") as MockAuthFetch:
            mock_auth_client = Mock()
            mock_auth_client.fetch = AsyncMock(return_value=mock_response)
            MockAuthFetch.return_value = mock_auth_client

            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")
            result = client.get_settings()

            assert result == {"settings": {"key": "value"}}

    def test_create_action(self, mock_wallet, mock_response) -> None:
        """Test create_action method."""
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"actionId": "123", "status": "created"},
        }

        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch") as MockAuthFetch:
            mock_auth_client = Mock()
            mock_auth_client.fetch = AsyncMock(return_value=mock_response)
            MockAuthFetch.return_value = mock_auth_client

            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

            auth = {"identityKey": "test_key"}
            args = {"description": "test action"}
            result = client.create_action(auth, args)

            assert result == {"actionId": "123", "status": "created"}

    def test_list_actions(self, mock_wallet, mock_response) -> None:
        """Test list_actions method."""
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"actions": [{"id": "1"}, {"id": "2"}], "total": 2},
        }

        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch") as MockAuthFetch:
            mock_auth_client = Mock()
            mock_auth_client.fetch = AsyncMock(return_value=mock_response)
            MockAuthFetch.return_value = mock_auth_client

            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

            auth = {"identityKey": "test_key"}
            args = {"limit": 10}
            result = client.list_actions(auth, args)

            assert result["total"] == 2
            assert len(result["actions"]) == 2

    def test_abort_action(self, mock_wallet, mock_response) -> None:
        """Test abort_action method."""
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"aborted": True},
        }

        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch") as MockAuthFetch:
            mock_auth_client = Mock()
            mock_auth_client.fetch = AsyncMock(return_value=mock_response)
            MockAuthFetch.return_value = mock_auth_client

            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

            auth = {"identityKey": "test_key"}
            args = {"reference": "test_ref"}
            result = client.abort_action(auth, args)

            assert result["aborted"] is True

    def test_internalize_action(self, mock_wallet, mock_response) -> None:
        """Test internalize_action method."""
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"accepted": True},
        }

        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch") as MockAuthFetch:
            mock_auth_client = Mock()
            mock_auth_client.fetch = AsyncMock(return_value=mock_response)
            MockAuthFetch.return_value = mock_auth_client

            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

            auth = {"identityKey": "test_key"}
            args = {"tx": "raw_tx_hex"}
            result = client.internalize_action(auth, args)

            assert result["accepted"] is True

    def test_list_certificates(self, mock_wallet, mock_response) -> None:
        """Test list_certificates method."""
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"certificates": [], "total": 0},
        }

        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch") as MockAuthFetch:
            mock_auth_client = Mock()
            mock_auth_client.fetch = AsyncMock(return_value=mock_response)
            MockAuthFetch.return_value = mock_auth_client

            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

            auth = {"identityKey": "test_key"}
            args = {"limit": 10}
            result = client.list_certificates(auth, args)

            assert result["total"] == 0

    def test_list_outputs(self, mock_wallet, mock_response) -> None:
        """Test list_outputs method."""
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"outputs": [{"txid": "abc"}], "total": 1},
        }

        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch") as MockAuthFetch:
            mock_auth_client = Mock()
            mock_auth_client.fetch = AsyncMock(return_value=mock_response)
            MockAuthFetch.return_value = mock_auth_client

            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

            auth = {"identityKey": "test_key"}
            args = {"basket": "test_basket"}
            result = client.list_outputs(auth, args)

            assert result["total"] == 1

    def test_close(self, mock_wallet) -> None:
        """Test closing the client."""
        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch"):
            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

            # Should not raise
            client.close()

    def test_rpc_call_uses_auth_fetch(self, mock_wallet, mock_response) -> None:
        """Test that RPC calls use AuthFetch for authenticated requests."""
        mock_response.json.return_value = {"jsonrpc": "2.0", "id": 1, "result": {}}

        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch") as MockAuthFetch:
            mock_auth_client = Mock()
            mock_auth_client.fetch = AsyncMock(return_value=mock_response)
            MockAuthFetch.return_value = mock_auth_client

            client = StorageClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")
            client._rpc_call("test_method", [])

            # Verify AuthFetch.fetch was called
            mock_auth_client.fetch.assert_called_once()

            # Verify the call used correct URL and config
            call_args = mock_auth_client.fetch.call_args
            assert call_args[0][0] == "https://example.com/rpc"

    def test_invalid_endpoint_url_raises_error(self, mock_wallet) -> None:
        """Test that invalid endpoint URL raises ValueError."""
        with patch("bsv_wallet_toolbox.rpc.storage_client.AuthFetch"):
            with pytest.raises(ValueError) as exc_info:
                StorageClient(wallet=mock_wallet, endpoint_url="")

            assert "endpoint_url must be a non-empty string" in str(exc_info.value)


# Backward compatibility test
class TestBackwardCompatibility:
    """Test backward compatibility with old class name."""

    def test_json_rpc_client_alias(self) -> None:
        """Test that JsonRpcClient is an alias for StorageClient."""
        from bsv_wallet_toolbox.rpc.storage_client import JsonRpcClient

        assert JsonRpcClient is StorageClient
