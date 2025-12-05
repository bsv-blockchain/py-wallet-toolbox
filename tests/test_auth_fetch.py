"""Tests for AuthFetch authenticated HTTP client.

This module provides comprehensive test coverage for the AuthFetch class.
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch
from typing import Any

import pytest
import requests

from bsv_wallet_toolbox.auth_fetch import AuthFetch, SimplifiedFetchRequestOptions


class TestSimplifiedFetchRequestOptions:
    """Tests for SimplifiedFetchRequestOptions."""

    def test_init_default_values(self) -> None:
        """Test initialization with default values."""
        options = SimplifiedFetchRequestOptions()

        assert options.method == "GET"
        assert options.headers == {}
        assert options.body is None

    def test_init_with_values(self) -> None:
        """Test initialization with provided values."""
        headers = {"Authorization": "Bearer token"}
        body = b"test data"

        options = SimplifiedFetchRequestOptions(
            method="POST",
            headers=headers,
            body=body
        )

        assert options.method == "POST"
        assert options.headers == headers
        assert options.body == body


class TestAuthFetch:
    """Tests for AuthFetch."""

    @pytest.fixture
    def mock_wallet(self) -> Mock:
        """Create a mock wallet."""
        return Mock()

    @pytest.fixture
    def auth_fetch(self, mock_wallet: Mock) -> AuthFetch:
        """Create an AuthFetch instance."""
        return AuthFetch(mock_wallet)

    @pytest.fixture
    def auth_fetch_with_custom_client(self, mock_wallet: Mock) -> AuthFetch:
        """Create an AuthFetch instance with custom HTTP client."""
        custom_client = Mock()
        return AuthFetch(mock_wallet, {"http_client": custom_client})

    def test_init_with_wallet(self, mock_wallet: Mock) -> None:
        """Test initialization with wallet."""
        auth_fetch = AuthFetch(mock_wallet)

        assert auth_fetch.wallet == mock_wallet
        assert auth_fetch.options == {}
        assert hasattr(auth_fetch, 'client')
        assert isinstance(auth_fetch.client, requests.Session)

    def test_init_with_custom_client(self, mock_wallet: Mock) -> None:
        """Test initialization with custom HTTP client."""
        custom_client = Mock()
        auth_fetch = AuthFetch(mock_wallet, {"http_client": custom_client})

        assert auth_fetch.client == custom_client

    def test_init_sets_user_agent(self, mock_wallet: Mock) -> None:
        """Test that default client sets User-Agent header."""
        auth_fetch = AuthFetch(mock_wallet)

        assert "User-Agent" in auth_fetch.client.headers
        assert auth_fetch.client.headers["User-Agent"] == "bsv-wallet-toolbox"

    @pytest.mark.asyncio
    async def test_fetch_get_request(self, auth_fetch: AuthFetch) -> None:
        """Test basic GET request."""
        url = "https://example.com/api"
        options = SimplifiedFetchRequestOptions(method="GET")

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with patch.object(auth_fetch.client, 'request', return_value=mock_response) as mock_request:
            response = await auth_fetch.fetch(url, options)

            mock_request.assert_called_once_with(
                method="GET",
                url=url,
                headers={},
                data=None
            )
            assert response == mock_response

    @pytest.mark.asyncio
    async def test_fetch_post_with_string_body(self, auth_fetch: AuthFetch) -> None:
        """Test POST request with string body."""
        url = "https://example.com/api"
        body = '{"key": "value"}'
        options = SimplifiedFetchRequestOptions(method="POST", body=body)

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with patch.object(auth_fetch.client, 'request', return_value=mock_response) as mock_request:
            response = await auth_fetch.fetch(url, options)

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[1]["method"] == "POST"
            assert call_args[1]["url"] == url
            assert "Content-Type" in call_args[1]["headers"]
            assert call_args[1]["headers"]["Content-Type"] == "application/json"
            assert call_args[1]["data"] == body

    @pytest.mark.asyncio
    async def test_fetch_post_with_bytes_body(self, auth_fetch: AuthFetch) -> None:
        """Test POST request with bytes body."""
        url = "https://example.com/api"
        body = b'{"key": "value"}'
        options = SimplifiedFetchRequestOptions(method="POST", body=body)

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with patch.object(auth_fetch.client, 'request', return_value=mock_response) as mock_request:
            response = await auth_fetch.fetch(url, options)

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[1]["data"] == body.decode('utf-8')

    @pytest.mark.asyncio
    async def test_fetch_post_with_dict_body(self, auth_fetch: AuthFetch) -> None:
        """Test POST request with dict body."""
        url = "https://example.com/api"
        body = {"key": "value"}
        options = SimplifiedFetchRequestOptions(method="POST", body=body)

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with patch.object(auth_fetch.client, 'request', return_value=mock_response) as mock_request:
            response = await auth_fetch.fetch(url, options)

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[1]["json"] == body

    @pytest.mark.asyncio
    async def test_fetch_with_custom_headers(self, auth_fetch: AuthFetch) -> None:
        """Test request with custom headers."""
        url = "https://example.com/api"
        headers = {"Authorization": "Bearer token", "X-Custom": "value"}
        options = SimplifiedFetchRequestOptions(method="GET", headers=headers)

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with patch.object(auth_fetch.client, 'request', return_value=mock_response) as mock_request:
            response = await auth_fetch.fetch(url, options)

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[1]["headers"] == headers

    @pytest.mark.asyncio
    async def test_fetch_preserves_existing_headers(self, auth_fetch: AuthFetch) -> None:
        """Test that existing headers are preserved when adding Content-Type."""
        url = "https://example.com/api"
        headers = {"Authorization": "Bearer token"}
        body = '{"key": "value"}'
        options = SimplifiedFetchRequestOptions(method="POST", headers=headers, body=body)

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with patch.object(auth_fetch.client, 'request', return_value=mock_response) as mock_request:
            response = await auth_fetch.fetch(url, options)

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            expected_headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}
            assert call_args[1]["headers"] == expected_headers

    @pytest.mark.asyncio
    async def test_fetch_with_existing_content_type(self, auth_fetch: AuthFetch) -> None:
        """Test that existing Content-Type header is not overridden."""
        url = "https://example.com/api"
        headers = {"content-type": "text/plain"}
        body = "plain text body"
        options = SimplifiedFetchRequestOptions(method="POST", headers=headers, body=body)

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with patch.object(auth_fetch.client, 'request', return_value=mock_response) as mock_request:
            response = await auth_fetch.fetch(url, options)

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[1]["headers"]["content-type"] == "text/plain"

    @pytest.mark.asyncio
    async def test_fetch_http_error_raises_exception(self, auth_fetch: AuthFetch) -> None:
        """Test that HTTP errors raise exceptions."""
        url = "https://example.com/api"
        options = SimplifiedFetchRequestOptions(method="GET")

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        with patch.object(auth_fetch.client, 'request', return_value=mock_response):
            with pytest.raises(Exception, match="HTTP request failed"):
                await auth_fetch.fetch(url, options)

    @pytest.mark.asyncio
    async def test_fetch_request_exception_raises_exception(self, auth_fetch: AuthFetch) -> None:
        """Test that request exceptions are re-raised."""
        url = "https://example.com/api"
        options = SimplifiedFetchRequestOptions(method="GET")

        with patch.object(auth_fetch.client, 'request', side_effect=requests.ConnectionError("Connection failed")):
            with pytest.raises(Exception, match="HTTP request failed"):
                await auth_fetch.fetch(url, options)

    @pytest.mark.asyncio
    async def test_close_with_closeable_client(self, auth_fetch: AuthFetch) -> None:
        """Test close method with client that has close method."""
        await auth_fetch.close()
        # Should not raise

    @pytest.mark.asyncio
    async def test_close_with_custom_client(self, auth_fetch_with_custom_client: AuthFetch) -> None:
        """Test close method with custom client."""
        custom_client = auth_fetch_with_custom_client.client
        await auth_fetch_with_custom_client.close()

        custom_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_context_manager(self, mock_wallet: Mock) -> None:
        """Test async context manager."""
        with patch('bsv_wallet_toolbox.auth_fetch.AuthFetch.close') as mock_close:
            async with AuthFetch(mock_wallet) as auth_fetch:
                assert isinstance(auth_fetch, AuthFetch)

            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_uses_thread_pool(self, auth_fetch: AuthFetch) -> None:
        """Test that fetch uses thread pool executor."""
        url = "https://example.com/api"
        options = SimplifiedFetchRequestOptions(method="GET")

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with patch.object(auth_fetch.client, 'request', return_value=mock_response) as mock_request:
            with patch('asyncio.get_event_loop') as mock_get_loop:
                mock_loop = Mock()
                mock_get_loop.return_value = mock_loop

                # Mock run_in_executor to return the response directly
                mock_loop.run_in_executor = AsyncMock(return_value=mock_response)

                response = await auth_fetch.fetch(url, options)

                mock_loop.run_in_executor.assert_called_once()
                assert response == mock_response
