"""Expanded tests for CDN reader components.

This module provides comprehensive test coverage for CDN-related classes and methods.
"""

from unittest.mock import Mock, patch

import pytest

from bsv_wallet_toolbox.services.chaintracker.chaintracks.cdn_reader import (
    BulkHeaderFileInfo,
    BulkHeaderFilesInfo,
    CDNReader,
)


class TestBulkHeaderFileInfo:
    """Test BulkHeaderFileInfo class."""

    def test_init(self) -> None:
        """Test BulkHeaderFileInfo initialization."""
        data = {
            "firstHeight": 0,
            "count": 1000,
            "fileName": "headers_0_1000.txt",
            "sourceUrl": "https://cdn.example.com/headers_0_1000.txt",
            "prevChainWork": "0000000000000000000000000000000000000000000000000000000000000000",
            "lastChainWork": "0000000000000000000000000000000000000000000000000000000000000001",
            "prevHash": "0000000000000000000000000000000000000000000000000000000000000000",
            "lastHash": "0000000000000000000000000000000000000000000000000000000000000001",
            "fileHash": b"hash",
            "chain": "main",
        }

        info = BulkHeaderFileInfo(data)

        assert info.first_height == 0
        assert info.count == 1000
        assert info.file_name == "headers_0_1000.txt"
        assert info.source_url == "https://cdn.example.com/headers_0_1000.txt"
        assert info.chain == "main"

    def test_bulk_header_minimum_info(self) -> None:
        """Test bulk_header_minimum_info method."""
        data = {
            "firstHeight": 0,
            "count": 1000,
            "fileName": "headers_0_1000.txt",
            "sourceUrl": "https://cdn.example.com/headers_0_1000.txt",
            "prevChainWork": "0000000000000000000000000000000000000000000000000000000000000000",
            "lastChainWork": "0000000000000000000000000000000000000000000000000000000000000001",
            "prevHash": "0000000000000000000000000000000000000000000000000000000000000000",
            "lastHash": "0000000000000000000000000000000000000000000000000000000000000001",
            "fileHash": b"hash",
            "chain": "main",
        }

        info = BulkHeaderFileInfo(data)
        result = info.bulk_header_minimum_info

        assert result.first_height == 0
        assert result.count == 1000
        assert result.file_name == "headers_0_1000.txt"
        assert result.source_url == "https://cdn.example.com/headers_0_1000.txt"


class TestBulkHeaderFilesInfo:
    """Test BulkHeaderFilesInfo class."""

    def test_init(self) -> None:
        """Test BulkHeaderFilesInfo initialization."""
        data = {
            "rootFolder": "https://cdn.example.com",
            "jsonFilename": "files.json",
            "headersPerFile": 1000,
            "files": [
                {"firstHeight": 0, "count": 1000, "fileName": "file1.txt", "sourceUrl": "url1"},
                {"firstHeight": 1000, "count": 1000, "fileName": "file2.txt", "sourceUrl": "url2"},
            ],
        }

        info = BulkHeaderFilesInfo(data)

        assert info.root_folder == "https://cdn.example.com"
        assert info.json_filename == "files.json"
        assert info.headers_per_file == 1000
        assert len(info.files) == 2
        assert info.files[0].file_name == "file1.txt"
        assert info.files[0].source_url == "url1"

    def test_init_empty_data(self) -> None:
        """Test BulkHeaderFilesInfo with empty data."""
        data = {"files": []}

        info = BulkHeaderFilesInfo(data)

        assert info.files == []

    def test_files_property(self) -> None:
        """Test that files property contains BulkHeaderFileInfo objects."""
        data = {"files": [{"firstHeight": 0, "count": 1000, "fileName": "file1.txt", "sourceUrl": "url1"}]}

        info = BulkHeaderFilesInfo(data)

        assert len(info.files) == 1
        assert isinstance(info.files[0], BulkHeaderFileInfo)
        assert info.files[0].file_name == "file1.txt"
        assert info.files[0].source_url == "url1"


class TestCDNReader:
    """Test CDNReader class."""

    @pytest.fixture
    def reader(self) -> CDNReader:
        """Create CDNReader instance for testing."""
        return CDNReader()

    def test_init_default_params(self, reader: CDNReader) -> None:
        """Test initialization with default parameters."""
        assert reader.base_url == "https://cdn.projectbabbage.com/blockheaders"
        assert reader.timeout == 30

    def test_init_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        reader = CDNReader(base_url="https://custom.cdn.com", timeout=60)

        assert reader.base_url == "https://custom.cdn.com"
        assert reader.timeout == 60

    def test_fetch_bulk_header_files_info_main_chain(self, reader: CDNReader) -> None:
        """Test fetching bulk header files info for main chain."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "files": [
                {
                    "firstHeight": 0,
                    "count": 1000,
                    "fileName": "bitcoin-headers-0-1000.txt",
                    "sourceUrl": "https://cdn.com/file1.txt",
                }
            ]
        }

        with patch.object(reader.session, "get", return_value=mock_response) as mock_get:
            result = reader.fetch_bulk_header_files_info("main")

            assert isinstance(result, BulkHeaderFilesInfo)
            assert len(result.files) == 1
            assert result.files[0].file_name == "bitcoin-headers-0-1000.txt"

            # Verify correct URL was called
            expected_url = "https://cdn.projectbabbage.com/blockheaders/mainNetBlockHeaders.json"
            mock_get.assert_called_once_with(expected_url, timeout=30)

    def test_fetch_bulk_header_files_info_test_chain(self, reader: CDNReader) -> None:
        """Test fetching bulk header files info for test chain."""
        mock_response = Mock()
        mock_response.json.return_value = {"files": []}

        with patch.object(reader.session, "get", return_value=mock_response) as mock_get:
            result = reader.fetch_bulk_header_files_info("test")

            assert isinstance(result, BulkHeaderFilesInfo)
            assert result.files == []

            # Verify correct URL was called
            expected_url = "https://cdn.projectbabbage.com/blockheaders/testNetBlockHeaders.json"
            mock_get.assert_called_once_with(expected_url, timeout=30)

    def test_fetch_bulk_header_files_info_http_error(self, reader: CDNReader) -> None:
        """Test fetching files info with HTTP error."""
        with patch.object(reader.session, "get", side_effect=Exception("404 Not Found")):
            with pytest.raises(Exception, match="Failed to fetch bulk header files info: 404 Not Found"):
                reader.fetch_bulk_header_files_info("main")

    def test_fetch_bulk_header_files_info_invalid_json(self, reader: CDNReader) -> None:
        """Test fetching files info with invalid JSON response."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch.object(reader.session, "get", return_value=mock_response):
            with pytest.raises(Exception, match="Failed to fetch bulk header files info"):
                reader.fetch_bulk_header_files_info("main")

    def test_download_bulk_header_file_success(self, reader: CDNReader) -> None:
        """Test successful bulk header file download."""
        filename = "test-headers.txt"
        expected_content = b"header_data_1\nheader_data_2"

        mock_response = Mock()
        mock_response.content = expected_content

        with patch.object(reader.session, "get", return_value=mock_response) as mock_get:
            result = reader.download_bulk_header_file(filename)

            assert result == expected_content

            # Verify correct URL was called
            expected_url = f"https://cdn.projectbabbage.com/blockheaders/{filename}"
            mock_get.assert_called_once_with(expected_url, timeout=30)

    def test_download_bulk_header_file_empty_content(self, reader: CDNReader) -> None:
        """Test downloading bulk header file with empty content."""
        filename = "empty-headers.txt"

        mock_response = Mock()
        mock_response.content = b""

        with patch.object(reader.session, "get", return_value=mock_response):
            result = reader.download_bulk_header_file(filename)

            assert result == b""

    def test_download_bulk_header_file_http_error(self, reader: CDNReader) -> None:
        """Test downloading bulk header file with HTTP error."""
        filename = "missing-file.txt"

        with patch.object(reader.session, "get", side_effect=Exception("403 Forbidden")):
            with pytest.raises(Exception, match="Failed to download bulk header file"):
                reader.download_bulk_header_file(filename)

    def test_download_bulk_header_file_timeout(self, reader: CDNReader) -> None:
        """Test downloading bulk header file with timeout."""
        filename = "large-file.txt"

        import requests

        with patch.object(reader.session, "get", side_effect=requests.Timeout("Request timeout")):
            with pytest.raises(Exception, match="Failed to download bulk header file"):
                reader.download_bulk_header_file(filename)


class TestCDNReaderEdgeCases:
    """Test CDNReader edge cases and error conditions."""

    @pytest.fixture
    def reader(self) -> CDNReader:
        """Create CDNReader instance for testing."""
        return CDNReader()

    def test_fetch_bulk_header_files_info_malformed_response(self, reader: CDNReader) -> None:
        """Test fetching files info with malformed response."""
        # Test with missing 'files' key
        mock_response = Mock()
        mock_response.json.return_value = {"error": "No files available"}

        with patch.object(reader.session, "get", return_value=mock_response):
            result = reader.fetch_bulk_header_files_info("main")

            # Should create BulkHeaderFilesInfo with whatever data we got
            assert isinstance(result, BulkHeaderFilesInfo)
            # The result won't have the original data stored, just parsed fields
            assert result.files == []  # No valid files in the malformed response

    def test_download_bulk_header_file_special_characters_filename(self, reader: CDNReader) -> None:
        """Test downloading file with special characters in filename."""
        filename = "headers_0-1000_v2.1.txt"
        content = b"special_content"

        mock_response = Mock()
        mock_response.content = content

        with patch.object(reader.session, "get", return_value=mock_response) as mock_get:
            result = reader.download_bulk_header_file(filename)

            assert result == content

            # Verify URL encoding if needed
            expected_url = f"https://cdn.projectbabbage.com/blockheaders/{filename}"
            mock_get.assert_called_once_with(expected_url, timeout=30)

    def test_init_zero_timeout(self) -> None:
        """Test initialization with zero timeout."""
        reader = CDNReader(timeout=0)

        assert reader.timeout == 0

        # Test that zero timeout is passed to requests
        mock_response = Mock()
        mock_response.json.return_value = {"files": []}

        with patch.object(reader.session, "get", return_value=mock_response) as mock_get:
            reader.fetch_bulk_header_files_info("main")

            call_kwargs = mock_get.call_args[1]
            assert call_kwargs["timeout"] == 0

    def test_custom_base_url_formatting(self) -> None:
        """Test custom base URL formatting."""
        custom_base = "https://my-custom-cdn.com/api/v1"
        reader = CDNReader(base_url=custom_base)

        mock_response = Mock()
        mock_response.json.return_value = {"files": []}

        with patch.object(reader.session, "get", return_value=mock_response) as mock_get:
            reader.fetch_bulk_header_files_info("main")

            expected_url = f"{custom_base}/mainNetBlockHeaders.json"
            mock_get.assert_called_once_with(expected_url, timeout=30)
