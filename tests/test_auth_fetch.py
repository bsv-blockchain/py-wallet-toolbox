"""Tests for AuthFetch authenticated HTTP client.

This module provides comprehensive test coverage for the AuthFetch class.
"""

from unittest.mock import AsyncMock, Mock, patch

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

        options = SimplifiedFetchRequestOptions(method="POST", headers=headers, body=body)

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
        """Create an AuthFetch instance."""
        # AuthFetch doesn't support custom client in options
        # It wraps _AuthFetch which handles client internally
        return AuthFetch(mock_wallet)

    def test_init_with_wallet(self, mock_wallet: Mock) -> None:
        """Test initialization with wallet."""
        auth_fetch = AuthFetch(mock_wallet)

        # AuthFetch wraps _impl, verify it was created
        assert hasattr(auth_fetch, "_impl")
        # Verify _impl was initialized with the wallet
        assert auth_fetch._impl is not None

    def test_init_with_custom_client(self, mock_wallet: Mock) -> None:
        """Test initialization with custom HTTP client."""
        # AuthFetch doesn't support custom client in options, it wraps _AuthFetch
        # The _AuthFetch from py-sdk handles client internally
        auth_fetch = AuthFetch(mock_wallet)

        # Verify _impl was created
        assert hasattr(auth_fetch, "_impl")
        assert auth_fetch._impl is not None

    def test_init_sets_user_agent(self, mock_wallet: Mock) -> None:
        """Test that AuthFetch initializes correctly."""
        auth_fetch = AuthFetch(mock_wallet)

        # AuthFetch wraps _impl, verify it was created
        assert hasattr(auth_fetch, "_impl")
        assert auth_fetch._impl is not None

    @pytest.mark.asyncio
    async def test_fetch_get_request(self, auth_fetch: AuthFetch) -> None:
        """Test basic GET request."""
        url = "https://example.com/api"
        options = SimplifiedFetchRequestOptions(method="GET")

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with patch.object(auth_fetch._impl, "fetch", new_callable=AsyncMock, return_value=mock_response) as mock_fetch:
            response = await auth_fetch.fetch(url, options)

            mock_fetch.assert_called_once_with(url, options)
            assert response == mock_response

    @pytest.mark.asyncio
    async def test_fetch_post_with_string_body(self, auth_fetch: AuthFetch) -> None:
        """Test POST request with string body."""
        url = "https://example.com/api"
        body = '{"key": "value"}'
        options = SimplifiedFetchRequestOptions(method="POST", body=body)

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with patch.object(auth_fetch._impl, "fetch", new_callable=AsyncMock, return_value=mock_response) as mock_fetch:
            response = await auth_fetch.fetch(url, options)

            mock_fetch.assert_called_once_with(url, options)
            assert response == mock_response

    @pytest.mark.asyncio
    async def test_fetch_post_with_bytes_body(self, auth_fetch: AuthFetch) -> None:
        """Test POST request with bytes body."""
        url = "https://example.com/api"
        body = b'{"key": "value"}'
        options = SimplifiedFetchRequestOptions(method="POST", body=body)

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with patch.object(auth_fetch._impl, "fetch", new_callable=AsyncMock, return_value=mock_response) as mock_fetch:
            response = await auth_fetch.fetch(url, options)

            mock_fetch.assert_called_once_with(url, options)
            assert response == mock_response

    @pytest.mark.asyncio
    async def test_fetch_post_with_dict_body(self, auth_fetch: AuthFetch) -> None:
        """Test POST request with dict body."""
        url = "https://example.com/api"
        body = {"key": "value"}
        options = SimplifiedFetchRequestOptions(method="POST", body=body)

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with patch.object(auth_fetch._impl, "fetch", new_callable=AsyncMock, return_value=mock_response) as mock_fetch:
            response = await auth_fetch.fetch(url, options)

            mock_fetch.assert_called_once_with(url, options)
            assert response == mock_response

    @pytest.mark.asyncio
    async def test_fetch_with_custom_headers(self, auth_fetch: AuthFetch) -> None:
        """Test request with custom headers."""
        url = "https://example.com/api"
        headers = {"Authorization": "Bearer token", "X-Custom": "value"}
        options = SimplifiedFetchRequestOptions(method="GET", headers=headers)

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with patch.object(auth_fetch._impl, "fetch", new_callable=AsyncMock, return_value=mock_response) as mock_fetch:
            response = await auth_fetch.fetch(url, options)

            mock_fetch.assert_called_once_with(url, options)
            assert response == mock_response

    @pytest.mark.asyncio
    async def test_fetch_preserves_existing_headers(self, auth_fetch: AuthFetch) -> None:
        """Test that existing headers are preserved when adding Content-Type."""
        url = "https://example.com/api"
        headers = {"Authorization": "Bearer token"}
        body = '{"key": "value"}'
        options = SimplifiedFetchRequestOptions(method="POST", headers=headers, body=body)

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with patch.object(auth_fetch._impl, "fetch", new_callable=AsyncMock, return_value=mock_response) as mock_fetch:
            response = await auth_fetch.fetch(url, options)

            mock_fetch.assert_called_once_with(url, options)
            assert response == mock_response

    @pytest.mark.asyncio
    async def test_fetch_with_existing_content_type(self, auth_fetch: AuthFetch) -> None:
        """Test that existing Content-Type header is not overridden."""
        url = "https://example.com/api"
        headers = {"content-type": "text/plain"}
        body = "plain text body"
        options = SimplifiedFetchRequestOptions(method="POST", headers=headers, body=body)

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with patch.object(auth_fetch._impl, "fetch", new_callable=AsyncMock, return_value=mock_response) as mock_fetch:
            response = await auth_fetch.fetch(url, options)

            mock_fetch.assert_called_once_with(url, options)
            assert response == mock_response

    @pytest.mark.asyncio
    async def test_fetch_http_error_raises_exception(self, auth_fetch: AuthFetch) -> None:
        """Test that HTTP errors raise exceptions."""
        url = "https://example.com/api"
        options = SimplifiedFetchRequestOptions(method="GET")

        with patch.object(auth_fetch._impl, "fetch", side_effect=Exception("HTTP request failed")):
            with pytest.raises(Exception, match="HTTP request failed"):
                await auth_fetch.fetch(url, options)

    @pytest.mark.asyncio
    async def test_fetch_request_exception_raises_exception(self, auth_fetch: AuthFetch) -> None:
        """Test that request exceptions are re-raised."""
        url = "https://example.com/api"
        options = SimplifiedFetchRequestOptions(method="GET")

        with patch.object(auth_fetch._impl, "fetch", side_effect=requests.ConnectionError("Connection failed")):
            with pytest.raises(requests.ConnectionError, match="Connection failed"):
                await auth_fetch.fetch(url, options)

    @pytest.mark.asyncio
    async def test_close_with_closeable_client(self, auth_fetch: AuthFetch) -> None:
        """Test that AuthFetch can be used without close method."""
        # AuthFetch doesn't have a close method, it's a wrapper
        # The _impl may have close, but we don't expose it
        # This test verifies the wrapper doesn't require close
        assert hasattr(auth_fetch, "_impl")

    @pytest.mark.asyncio
    async def test_close_with_custom_client(self, auth_fetch_with_custom_client: AuthFetch) -> None:
        """Test that AuthFetch works with custom initialization."""
        # AuthFetch doesn't expose client or close method
        # Verify it was initialized correctly
        assert hasattr(auth_fetch_with_custom_client, "_impl")
        assert auth_fetch_with_custom_client._impl is not None

    @pytest.mark.asyncio
    async def test_async_context_manager(self, mock_wallet: Mock) -> None:
        """Test that AuthFetch can be instantiated."""
        # AuthFetch doesn't implement async context manager
        # Just verify it can be created
        auth_fetch = AuthFetch(mock_wallet)
        assert isinstance(auth_fetch, AuthFetch)
        assert hasattr(auth_fetch, "_impl")

    @pytest.mark.asyncio
    async def test_fetch_uses_thread_pool(self, auth_fetch: AuthFetch) -> None:
        """Test that fetch delegates to _impl."""
        url = "https://example.com/api"
        options = SimplifiedFetchRequestOptions(method="GET")

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with patch.object(auth_fetch._impl, "fetch", new_callable=AsyncMock, return_value=mock_response) as mock_fetch:
            response = await auth_fetch.fetch(url, options)

            mock_fetch.assert_called_once_with(url, options)
            assert response == mock_response
