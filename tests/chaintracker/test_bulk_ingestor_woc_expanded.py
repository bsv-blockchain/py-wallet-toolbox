"""Expanded tests for BulkIngestorWOC.

This module provides comprehensive test coverage for the BulkIngestorWOC class,
focusing on synchronization logic, error handling, and edge cases.
"""

from unittest.mock import patch

import pytest

from bsv_wallet_toolbox.services.chaintracker.chaintracks.bulk_ingestor_interface import BulkHeaderMinimumInfo
from bsv_wallet_toolbox.services.chaintracker.chaintracks.bulk_ingestor_woc import BulkIngestorWOC
from bsv_wallet_toolbox.services.chaintracker.chaintracks.util.height_range import HeightRange


class TestBulkIngestorWOCInitialization:
    """Test BulkIngestorWOC initialization."""

    def test_init_main_chain(self) -> None:
        """Test initialization for main chain."""
        ingestor = BulkIngestorWOC("main")

        assert ingestor.chain == "main"
        assert ingestor.api_key is None
        assert ingestor.woc_client is not None

    def test_init_test_chain(self) -> None:
        """Test initialization for test chain."""
        ingestor = BulkIngestorWOC("test")

        assert ingestor.chain == "test"
        assert ingestor.api_key is None

    def test_init_with_api_key(self) -> None:
        """Test initialization with API key."""
        api_key = "test_key_123"
        ingestor = BulkIngestorWOC("main", api_key)

        assert ingestor.chain == "main"
        assert ingestor.api_key == api_key


class TestBulkIngestorWOCSynchronize:
    """Test BulkIngestorWOC synchronize method."""

    @pytest.fixture
    def ingestor(self) -> BulkIngestorWOC:
        """Create BulkIngestorWOC instance for testing."""
        return BulkIngestorWOC("main")

    @pytest.mark.asyncio
    async def test_synchronize_success(self, ingestor: BulkIngestorWOC) -> None:
        """Test successful synchronization."""
        present_height = 1000
        range_to_fetch = HeightRange(0, 500)

        # Mock the file info fetching
        mock_file_infos = [
            {
                "filename": "mainNet_0.headers",
                "url": "https://example.com/mainNet_0.headers",
                "heightRange": HeightRange(0, 99999),
                "fileId": 0,
            }
        ]

        with patch.object(ingestor, "_fetch_bulk_header_files_info", return_value=mock_file_infos):
            file_infos, downloader = await ingestor.synchronize(present_height, range_to_fetch)

            assert len(file_infos) == 1
            assert file_infos[0].file_name == "mainNet_0.headers"
            assert file_infos[0].first_height == 0
            assert callable(downloader)

    @pytest.mark.asyncio
    async def test_synchronize_no_files_found(self, ingestor: BulkIngestorWOC) -> None:
        """Test synchronization when no bulk files are found."""
        present_height = 1000
        range_to_fetch = HeightRange(0, 500)

        with patch.object(ingestor, "_fetch_bulk_header_files_info", return_value=[]):
            with pytest.raises(Exception, match="No bulk header files available"):
                await ingestor.synchronize(present_height, range_to_fetch)

    @pytest.mark.asyncio
    async def test_synchronize_fetch_files_error(self, ingestor: BulkIngestorWOC) -> None:
        """Test synchronization when fetching file info fails."""
        present_height = 1000
        range_to_fetch = HeightRange(0, 500)

        with patch.object(ingestor, "_fetch_bulk_header_files_info", side_effect=Exception("API error")):
            with pytest.raises(Exception, match="Failed to synchronize bulk headers: API error"):
                await ingestor.synchronize(present_height, range_to_fetch)


class TestBulkIngestorWOCFetchBulkHeaderFilesInfo:
    """Test _fetch_bulk_header_files_info method."""

    @pytest.fixture
    def ingestor(self) -> BulkIngestorWOC:
        """Create BulkIngestorWOC instance for testing."""
        return BulkIngestorWOC("main")

    def test_fetch_bulk_header_files_info_success(self, ingestor: BulkIngestorWOC) -> None:
        """Test successful fetching of bulk header files info."""
        # Mock the WOC client to return filenames
        mock_filenames = ["mainNet_0.headers", "mainNet_1.headers"]

        with patch.object(ingestor.woc_client, "get_headers_resource_list", return_value=mock_filenames):
            result = ingestor._fetch_bulk_header_files_info()

            assert len(result) == 2
            assert result[0]["filename"] == "mainNet_0.headers"
            assert "heightRange" in result[0]
            assert result[0]["fileId"] == 0
            assert result[1]["filename"] == "mainNet_1.headers"
            assert result[1]["fileId"] == 1

    def test_fetch_bulk_header_files_info_empty_response(self, ingestor: BulkIngestorWOC) -> None:
        """Test fetching files info when API returns empty list."""
        with patch.object(ingestor.woc_client, "get_headers_resource_list", return_value=[]):
            result = ingestor._fetch_bulk_header_files_info()

            assert result == []

    def test_fetch_bulk_header_files_info_api_error(self, ingestor: BulkIngestorWOC) -> None:
        """Test fetching files info when API call fails."""
        with patch.object(ingestor.woc_client, "get_headers_resource_list", side_effect=Exception("Network error")):
            result = ingestor._fetch_bulk_header_files_info()

            assert result == []

    def test_fetch_bulk_header_files_info_invalid_response(self, ingestor: BulkIngestorWOC) -> None:
        """Test fetching files info with invalid response format."""
        # Test with None response
        with patch.object(ingestor.woc_client, "get_headers_resource_list", return_value=None):
            result = ingestor._fetch_bulk_header_files_info()

            assert result == []

        # Test with non-list response
        with patch.object(ingestor.woc_client, "get_headers_resource_list", return_value="invalid"):
            result = ingestor._fetch_bulk_header_files_info()

            assert result == []


class TestBulkIngestorWOCBulkFileDownloader:
    """Test _bulk_file_downloader method."""

    @pytest.fixture
    def ingestor(self) -> BulkIngestorWOC:
        """Create BulkIngestorWOC instance for testing."""
        return BulkIngestorWOC("main")

    def test_bulk_file_downloader_creation(self, ingestor: BulkIngestorWOC) -> None:
        """Test that _bulk_file_downloader returns a callable."""
        downloader = ingestor._bulk_file_downloader()

        assert callable(downloader)

    def test_bulk_file_downloader_execution(self, ingestor: BulkIngestorWOC) -> None:
        """Test execution of the bulk file downloader."""
        downloader = ingestor._bulk_file_downloader()

        # Mock file info
        file_info = BulkHeaderMinimumInfo(
            first_height=0, count=1000, file_name="test_headers.txt", source_url="https://example.com/test_headers.txt"
        )

        # Mock the download process
        mock_data = b"header_data_line_1\nheader_data_line_2"

        with patch.object(ingestor.woc_client, "download_header_file", return_value=mock_data) as mock_download:
            result = downloader(file_info)

            # Should return the downloaded data
            assert result == mock_data

            # Verify the download was called with the correct URL
            mock_download.assert_called_once_with("https://example.com/test_headers.txt")

    def test_bulk_file_downloader_http_error(self, ingestor: BulkIngestorWOC) -> None:
        """Test bulk file downloader with HTTP error."""
        downloader = ingestor._bulk_file_downloader()

        file_info = BulkHeaderMinimumInfo(
            first_height=0, count=1000, file_name="test_headers.txt", source_url="https://example.com/test_headers.txt"
        )

        with patch.object(ingestor.woc_client, "download_header_file", side_effect=Exception("404 Not Found")):
            with pytest.raises(Exception, match="404 Not Found"):
                downloader(file_info)

    def test_bulk_file_downloader_timeout(self, ingestor: BulkIngestorWOC) -> None:
        """Test bulk file downloader with timeout."""
        downloader = ingestor._bulk_file_downloader()

        file_info = BulkHeaderMinimumInfo(
            first_height=0, count=1000, file_name="test_headers.txt", source_url="https://example.com/test_headers.txt"
        )

        with patch.object(ingestor.woc_client, "download_header_file", side_effect=Exception("Request timeout")):
            with pytest.raises(Exception, match="Request timeout"):
                downloader(file_info)

    def test_bulk_file_downloader_missing_url(self, ingestor: BulkIngestorWOC) -> None:
        """Test bulk file downloader with missing URL in file info."""
        downloader = ingestor._bulk_file_downloader()

        file_info = BulkHeaderMinimumInfo(
            first_height=0, count=1000, file_name="test_headers.txt", source_url=""  # Empty URL
        )

        with pytest.raises(Exception, match="SourceURL is required"):
            downloader(file_info)

    def test_bulk_file_downloader_custom_timeout(self, ingestor: BulkIngestorWOC) -> None:
        """Test bulk file downloader uses WOC client for downloading."""
        downloader = ingestor._bulk_file_downloader()

        file_info = BulkHeaderMinimumInfo(
            first_height=0, count=1000, file_name="test_headers.txt", source_url="https://example.com/test_headers.txt"
        )

        mock_data = b"header data"

        with patch.object(ingestor.woc_client, "download_header_file", return_value=mock_data) as mock_download:
            result = downloader(file_info)

            assert result == mock_data
            mock_download.assert_called_once_with("https://example.com/test_headers.txt")


class TestBulkIngestorWOCEdgeCases:
    """Test BulkIngestorWOC edge cases and error conditions."""

    @pytest.fixture
    def ingestor(self) -> BulkIngestorWOC:
        """Create BulkIngestorWOC instance for testing."""
        return BulkIngestorWOC("main")

    def test_init_invalid_chain(self, ingestor: BulkIngestorWOC) -> None:
        """Test initialization with invalid chain (should not raise)."""
        # Chain validation happens in WOCClient, not here
        ingestor_invalid = BulkIngestorWOC("invalid_chain")  # type: ignore

        assert ingestor_invalid.chain == "invalid_chain"

    def test_fetch_bulk_header_files_info_malformed_response(self, ingestor: BulkIngestorWOC) -> None:
        """Test fetching files info with malformed API response."""
        malformed_responses = [
            [{"filename": "test.txt"}],  # Missing url
            [{"url": "https://example.com"}],  # Missing filename
            [{"filename": "", "url": ""}],  # Empty strings
            [{"filename": None, "url": None}],  # None values
        ]

        for malformed_response in malformed_responses:
            with patch.object(ingestor.woc_client, "get_headers_resource_list", return_value=malformed_response):
                result = ingestor._fetch_bulk_header_files_info()

                # Should filter out invalid filenames and return valid ones
                # Since these are invalid filenames, result should be empty
                assert len(result) == 0

    @pytest.mark.asyncio
    async def test_synchronize_range_validation(self, ingestor: BulkIngestorWOC) -> None:
        """Test synchronize with various range configurations."""
        present_height = 1000

        # Test with range that goes beyond present height
        range_to_fetch = HeightRange(500, 1200)  # Beyond present height

        mock_file_infos = [
            {
                "filename": "mainNet_0.headers",
                "url": "https://example.com/mainNet_0.headers",
                "heightRange": HeightRange(0, 99999),
                "fileId": 0,
            }
        ]

        with patch.object(ingestor, "_fetch_bulk_header_files_info", return_value=mock_file_infos):
            file_infos, _downloader = await ingestor.synchronize(present_height, range_to_fetch)

            assert len(file_infos) == 1
            assert file_infos[0].file_name == "mainNet_0.headers"

    def test_bulk_file_downloader_empty_response(self, ingestor: BulkIngestorWOC) -> None:
        """Test bulk file downloader with empty response."""
        downloader = ingestor._bulk_file_downloader()

        file_info = BulkHeaderMinimumInfo(
            first_height=0, count=1000, file_name="empty.txt", source_url="https://example.com/empty.txt"
        )

        mock_data = b""

        with patch.object(ingestor.woc_client, "download_header_file", return_value=mock_data):
            result = downloader(file_info)

            assert result == b""

    def test_bulk_file_downloader_large_file(self, ingestor: BulkIngestorWOC) -> None:
        """Test bulk file downloader with large file content."""
        downloader = ingestor._bulk_file_downloader()

        file_info = BulkHeaderMinimumInfo(
            first_height=0,
            count=1000,
            file_name="large_headers.txt",
            source_url="https://example.com/large_headers.txt",
        )

        # Simulate large content (multiple header lines)
        large_content = "\n".join([f"header_{i}" for i in range(1000)]).encode("utf-8")

        with patch.object(ingestor.woc_client, "download_header_file", return_value=large_content):
            result = downloader(file_info)

            assert result == large_content
            assert len(result.decode("utf-8").split("\n")) == 1000
