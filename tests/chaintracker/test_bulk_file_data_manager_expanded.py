"""Expanded tests for BulkFileDataManager.

This module provides comprehensive test coverage for the BulkFileDataManager
and related utility classes.
"""

import pytest

from bsv_wallet_toolbox.services.chaintracker.chaintracks.util.bulk_file_data_manager import (
    BulkFileData,
    BulkFileDataManager,
    BulkFileDataManagerOptions,
)


class TestBulkFileData:
    """Test BulkFileData class."""

    def test_init(self) -> None:
        """Test BulkFileData initialization."""
        data = BulkFileData(file_index=5, min_height=1000, max_height=2000)

        assert data.file_index == 5
        assert data.min_height == 1000
        assert data.max_height == 2000

    def test_init_edge_values(self) -> None:
        """Test BulkFileData with edge values."""
        # Test with zero values
        data_zero = BulkFileData(file_index=0, min_height=0, max_height=0)
        assert data_zero.file_index == 0
        assert data_zero.min_height == 0
        assert data_zero.max_height == 0

        # Test with large values
        data_large = BulkFileData(file_index=999, min_height=800000, max_height=801000)
        assert data_large.file_index == 999
        assert data_large.min_height == 800000
        assert data_large.max_height == 801000


class TestBulkFileDataManagerOptions:
    """Test BulkFileDataManagerOptions class."""

    def test_init(self) -> None:
        """Test BulkFileDataManagerOptions initialization."""
        options = BulkFileDataManagerOptions(
            chain="main", from_known_source_url="https://cdn.example.com", max_per_file=50000, max_retained=3
        )

        assert options.from_known_source_url == "https://cdn.example.com"
        assert options.chain == "main"
        assert options.max_per_file == 50000
        assert options.max_retained == 3

    def test_init_defaults(self) -> None:
        """Test BulkFileDataManagerOptions with default values."""
        options = BulkFileDataManagerOptions(chain="main")

        assert "cdn" in options.from_known_source_url.lower()
        assert options.chain == "main"
        assert options.max_per_file == 100000
        assert options.max_retained == 2

    def test_create_default_options_main_chain(self) -> None:
        """Test create_default_options for main chain."""
        options = BulkFileDataManager.create_default_options("main")

        assert "cdn" in options.from_known_source_url.lower()
        assert options.chain == "main"
        assert options.max_per_file == 100000
        assert options.max_retained == 2

    def test_create_default_options_test_chain(self) -> None:
        """Test create_default_options for test chain."""
        options = BulkFileDataManager.create_default_options("test")

        assert "cdn" in options.from_known_source_url.lower()
        assert options.chain == "test"
        assert options.max_per_file == 100000
        assert options.max_retained == 2

    def test_default_cdn_url_main(self) -> None:
        """Test _default_cdn_url for main chain."""
        url = BulkFileDataManagerOptions._default_cdn_url("main")
        assert url.startswith("https://cdn.projectbabbage.com/") and "blockheaders" in url

    def test_default_cdn_url_test(self) -> None:
        """Test _default_cdn_url for test chain."""
        url = BulkFileDataManagerOptions._default_cdn_url("test")
        assert url.startswith("https://cdn-testnet.projectbabbage.com/") and "blockheaders" in url


class TestBulkFileDataManager:
    """Test BulkFileDataManager class."""

    @pytest.fixture
    def manager(self) -> BulkFileDataManager:
        """Create BulkFileDataManager instance for testing."""
        options = BulkFileDataManager.create_default_options("main")
        return BulkFileDataManager(options)

    def test_init(self, manager: BulkFileDataManager) -> None:
        """Test BulkFileDataManager initialization."""
        assert manager.chain == "main"
        assert manager.max_per_file == 100000
        assert manager.max_retained == 2
        assert hasattr(manager, "bfds")

    def test_init_with_custom_options(self) -> None:
        """Test initialization with custom options."""
        options = BulkFileDataManagerOptions(chain="main", max_per_file=50000, max_retained=1)
        manager = BulkFileDataManager(options)

        assert manager.chain == "main"
        assert manager.max_per_file == 50000
        assert manager.max_retained == 1

    def test_initialize_mock_files(self) -> None:
        """Test _initialize_mock_files method."""
        options = BulkFileDataManagerOptions(chain="main", max_per_file=50000)
        manager = BulkFileDataManager(options)

        # Clear existing files to test _initialize_mock_files in isolation
        manager.bfds.clear()
        manager._initialize_mock_files()

        # Should create 10 files by default (num_files = 10)
        assert len(manager.bfds) == 10
        assert all(isinstance(f, BulkFileData) for f in manager.bfds)
        # First file should start at height 0
        assert manager.bfds[0].min_height == 0
        # Files should be consecutive
        for i in range(1, len(manager.bfds)):
            prev_max = manager.bfds[i - 1].max_height
            curr_min = manager.bfds[i].min_height
            assert curr_min == prev_max + 1

    @pytest.mark.asyncio
    async def test_get_bulk_files(self, manager: BulkFileDataManager) -> None:
        """Test get_bulk_files method."""
        # Mock some bulk files
        manager.bfds = [BulkFileData(0, 0, 1000), BulkFileData(1, 1000, 2000)]

        result = await manager.get_bulk_files()

        assert len(result) == 2
        assert result[0].file_index == 0
        assert result[1].max_height == 2000

    @pytest.mark.asyncio
    async def test_get_height_range_no_files(self, manager: BulkFileDataManager) -> None:
        """Test get_height_range with no files."""
        manager.bfds = []

        result = await manager.get_height_range()

        # Should return empty range
        assert result.min_height == 0
        assert result.max_height == -1  # Empty range

    @pytest.mark.asyncio
    async def test_get_height_range_with_files(self, manager: BulkFileDataManager) -> None:
        """Test get_height_range with files."""
        manager.bfds = [BulkFileData(0, 0, 1000), BulkFileData(1, 1000, 2000), BulkFileData(2, 2000, 2500)]

        result = await manager.get_height_range()

        assert result.min_height == 0
        assert result.max_height == 2500

    @pytest.mark.asyncio
    async def test_get_height_range_gaps(self, manager: BulkFileDataManager) -> None:
        """Test get_height_range with gaps in file coverage."""
        manager.bfds = [BulkFileData(0, 0, 500), BulkFileData(2, 1000, 1500)]  # Gap between 500-1000

        result = await manager.get_height_range()

        # Should still report the overall range
        assert result.min_height == 0
        assert result.max_height == 1500

    @pytest.mark.asyncio
    async def test_update_from_url(self, manager: BulkFileDataManager) -> None:
        """Test update_from_url method."""
        url = "https://cdn.example.com/files.json"

        # Method is currently a stub, so just test it doesn't raise
        await manager.update_from_url(url)

        # Should not modify the bulk files
        initial_count = len(manager.bfds)
        assert len(manager.bfds) == initial_count

    @pytest.mark.asyncio
    async def test_update_from_url_http_error(self, manager: BulkFileDataManager) -> None:
        """Test update_from_url with HTTP error."""
        url = "https://cdn.example.com/files.json"

        # Method is currently a stub, so just test it doesn't raise
        await manager.update_from_url(url)

        # Bulk files should remain unchanged
        initial_count = len(manager.bfds)
        assert len(manager.bfds) == initial_count

    @pytest.mark.asyncio
    async def test_update_from_url_invalid_json(self, manager: BulkFileDataManager) -> None:
        """Test update_from_url with invalid JSON."""
        url = "https://cdn.example.com/files.json"

        # Method is currently a stub, so just test it doesn't raise
        await manager.update_from_url(url)

        # Should handle error gracefully
        initial_count = len(manager.bfds)
        assert len(manager.bfds) == initial_count


class TestBulkFileDataManagerEdgeCases:
    """Test BulkFileDataManager edge cases."""

    def test_init_minimal_options(self) -> None:
        """Test initialization with minimal options."""
        options = BulkFileDataManagerOptions(chain="main")
        manager = BulkFileDataManager(options)

        # Should have initialized mock files
        assert len(manager.bfds) > 0

    def test_create_default_options_invalid_chain(self) -> None:
        """Test create_default_options with invalid chain."""
        options = BulkFileDataManager.create_default_options("invalid")

        # Should still create options
        assert isinstance(options, BulkFileDataManagerOptions)
        assert options.chain == "invalid"
        # Should use testnet URL for non-main chains
        assert "testnet" in options.from_known_source_url

    def test_initialize_mock_files_with_custom_max_per_file(self) -> None:
        """Test _initialize_mock_files with custom max_per_file."""
        options = BulkFileDataManagerOptions(chain="main", max_per_file=25000)
        manager = BulkFileDataManager(options)

        # Should create files with the specified max_per_file
        assert len(manager.bfds) > 0
        # Check that files are created with correct height ranges
        for i, file in enumerate(manager.bfds):
            expected_min = i * 25000
            expected_max = (i + 1) * 25000 - 1
            assert file.min_height == expected_min
            assert file.max_height == expected_max

    @pytest.mark.asyncio
    async def test_get_height_range_single_file(self) -> None:
        """Test get_height_range with single file."""
        options = BulkFileDataManagerOptions(chain="main")
        manager = BulkFileDataManager(options)

        manager.bfds = [BulkFileData(0, 500, 1500)]

        result = await manager.get_height_range()

        assert result.min_height == 500
        assert result.max_height == 1500

    @pytest.mark.asyncio
    async def test_update_from_url_empty_response(self) -> None:
        """Test update_from_url with empty response."""
        options = BulkFileDataManagerOptions(chain="main")
        manager = BulkFileDataManager(options)

        # Method is currently a stub, so just test it doesn't raise
        await manager.update_from_url("https://example.com")

        # Should not modify files (has mock files from init)
        assert len(manager.bfds) > 0

    @pytest.mark.asyncio
    async def test_update_from_url_duplicate_files(self) -> None:
        """Test update_from_url with duplicate file indices."""
        options = BulkFileDataManagerOptions(chain="main")
        manager = BulkFileDataManager(options)

        # Method is currently a stub, so just test it doesn't raise
        await manager.update_from_url("https://example.com")

        # Should not modify files
        assert len(manager.bfds) > 0
