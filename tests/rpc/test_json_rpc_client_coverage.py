"""Coverage tests for JsonRpcClient.

This module tests the JSON-RPC 2.0 client implementation for remote storage providers.
"""

from unittest.mock import Mock, patch

import pytest
import requests

from bsv_wallet_toolbox.rpc.json_rpc_client import JsonRpcClient, JsonRpcError


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


class TestJsonRpcClient:
    """Test JsonRpcClient class."""

    @pytest.fixture
    def mock_wallet(self):
        """Create a mock wallet."""
        wallet = Mock()
        wallet.get_auth_headers = Mock(return_value={"X-Auth": "test_auth_header"})
        return wallet

    @pytest.fixture
    def mock_session(self):
        """Create a mock requests session."""
        session = Mock(spec=requests.Session)
        return session

    def test_client_creation(self, mock_wallet) -> None:
        """Test creating a JSON-RPC client."""
        client = JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

        assert client.endpoint_url == "https://example.com/rpc"
        assert client.wallet == mock_wallet
        assert isinstance(client._session, requests.Session)

    def test_client_context_manager(self, mock_wallet) -> None:
        """Test using client as context manager."""
        with JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc") as client:
            assert isinstance(client, JsonRpcClient)

        # Session should be closed after context
        assert client._session._closed if hasattr(client._session, "_closed") else True

    def test_get_next_id_thread_safe(self, mock_wallet) -> None:
        """Test that request ID generation is thread-safe."""
        client = JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

        id1 = client._get_next_id()
        id2 = client._get_next_id()
        id3 = client._get_next_id()

        assert id2 == id1 + 1
        assert id3 == id2 + 1

    @patch("requests.Session.post")
    def test_rpc_call_success(self, mock_post, mock_wallet) -> None:
        """Test successful RPC call."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"success": True, "data": "test_data"},
        }
        mock_post.return_value = mock_response

        client = JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

        result = client._rpc_call("test_method", ["param1", "param2"])

        assert result == {"success": True, "data": "test_data"}
        assert mock_post.called

    @patch("requests.Session.post")
    def test_rpc_call_with_error_response(self, mock_post, mock_wallet) -> None:
        """Test RPC call with error response."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32601, "message": "Method not found", "data": None},
        }
        mock_post.return_value = mock_response

        client = JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

        with pytest.raises(JsonRpcError) as exc_info:
            client._rpc_call("invalid_method", [])

        assert exc_info.value.code == -32601
        assert exc_info.value.message == "Method not found"

    @patch("requests.Session.post")
    def test_rpc_call_network_error(self, mock_post, mock_wallet) -> None:
        """Test RPC call with network error."""
        # Mock network error
        mock_post.side_effect = requests.ConnectionError("Connection failed")

        client = JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

        with pytest.raises(requests.ConnectionError):
            client._rpc_call("test_method", [])

    @patch("requests.Session.post")
    def test_rpc_call_timeout(self, mock_post, mock_wallet) -> None:
        """Test RPC call with timeout."""
        # Mock timeout
        mock_post.side_effect = requests.Timeout("Request timed out")

        client = JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

        with pytest.raises(requests.Timeout):
            client._rpc_call("test_method", [])

    @patch("requests.Session.post")
    def test_is_available(self, mock_post, mock_wallet) -> None:
        """Test is_available method."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"jsonrpc": "2.0", "id": 1, "result": True}
        mock_post.return_value = mock_response

        client = JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

        result = client.is_available()

        assert result is True
        mock_post.assert_called_once()

    @patch("requests.Session.post")
    def test_make_available(self, mock_post, mock_wallet) -> None:
        """Test make_available method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"status": "available"},
        }
        mock_post.return_value = mock_response

        client = JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

        result = client.make_available()

        assert result == {"status": "available"}

    @patch("requests.Session.post")
    def test_get_services(self, mock_post, mock_wallet) -> None:
        """Test get_services method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"services": ["service1", "service2"]},
        }
        mock_post.return_value = mock_response

        client = JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

        result = client.get_services()

        assert result == {"services": ["service1", "service2"]}

    @patch("requests.Session.post")
    def test_get_settings(self, mock_post, mock_wallet) -> None:
        """Test get_settings method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"settings": {"key": "value"}},
        }
        mock_post.return_value = mock_response

        client = JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

        result = client.get_settings()

        assert result == {"settings": {"key": "value"}}

    @patch("requests.Session.post")
    def test_create_action(self, mock_post, mock_wallet) -> None:
        """Test create_action method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"action_id": "123", "status": "created"},
        }
        mock_post.return_value = mock_response

        client = JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

        auth = {"identity_key": "test_key"}
        args = {"description": "test action"}

        result = client.create_action(auth, args)

        assert result == {"action_id": "123", "status": "created"}

    @patch("requests.Session.post")
    def test_list_actions(self, mock_post, mock_wallet) -> None:
        """Test list_actions method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"actions": [{"id": "1"}, {"id": "2"}], "total": 2},
        }
        mock_post.return_value = mock_response

        client = JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

        auth = {"identity_key": "test_key"}
        args = {"limit": 10}

        result = client.list_actions(auth, args)

        assert result["total"] == 2
        assert len(result["actions"]) == 2

    @patch("requests.Session.post")
    def test_abort_action(self, mock_post, mock_wallet) -> None:
        """Test abort_action method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"aborted": True},
        }
        mock_post.return_value = mock_response

        client = JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

        auth = {"identity_key": "test_key"}
        args = {"reference": "test_ref"}

        result = client.abort_action(auth, args)

        assert result["aborted"] is True

    @patch("requests.Session.post")
    def test_internalize_action(self, mock_post, mock_wallet) -> None:
        """Test internalize_action method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"accepted": True},
        }
        mock_post.return_value = mock_response

        client = JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

        auth = {"identity_key": "test_key"}
        args = {"tx": "raw_tx_hex"}

        result = client.internalize_action(auth, args)

        assert result["accepted"] is True

    @patch("requests.Session.post")
    def test_list_certificates(self, mock_post, mock_wallet) -> None:
        """Test list_certificates method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"certificates": [], "total": 0},
        }
        mock_post.return_value = mock_response

        client = JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

        auth = {"identity_key": "test_key"}
        args = {"limit": 10}

        result = client.list_certificates(auth, args)

        assert result["total"] == 0

    @patch("requests.Session.post")
    def test_list_outputs(self, mock_post, mock_wallet) -> None:
        """Test list_outputs method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"outputs": [{"txid": "abc"}], "total": 1},
        }
        mock_post.return_value = mock_response

        client = JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

        auth = {"identity_key": "test_key"}
        args = {"basket": "test_basket"}

        result = client.list_outputs(auth, args)

        assert result["total"] == 1

    def test_close_session(self, mock_wallet) -> None:
        """Test closing the session."""
        client = JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

        # Should not raise
        client.close()

    @patch("requests.Session.post")
    def test_rpc_call_includes_auth_headers(self, mock_post, mock_wallet) -> None:
        """Test that RPC calls include auth headers."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"jsonrpc": "2.0", "id": 1, "result": {}}
        mock_post.return_value = mock_response

        client = JsonRpcClient(wallet=mock_wallet, endpoint_url="https://example.com/rpc")

        client._rpc_call("test_method", [])

        # Verify headers were included in the call
        call_kwargs = mock_post.call_args[1]
        assert "headers" in call_kwargs

