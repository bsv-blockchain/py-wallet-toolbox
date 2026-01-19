"""Unit tests for ChaintracksFetch.

This module tests HTTP fetch utilities for chaintracks.

Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/ChaintracksFetch.test.ts
"""

import pytest

try:
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.util import (
        ChaintracksFetch,
        valid_bulk_header_files_by_file_hash,
    )
    from bsv_wallet_toolbox.utils import as_array, as_string, sha256_hash

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class TestChaintracksFetch:
    """Test suite for ChaintracksFetch.

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/ChaintracksFetch.test.ts
               describe('ChaintracksFetch tests')
    """

    @pytest.mark.integration
    def test_fetchjson(self) -> None:
        """Given: ChaintracksFetch instance and CDN URL
           When: Fetch JSON resource
           Then: Returns defined BulkHeaderFilesInfo with > 4 files

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/ChaintracksFetch.test.ts
                   test('0 fetchJson')

        Note: Requires network access to cdn.projectbabbage.com
        """
        # Given
        fetch = ChaintracksFetch()
        cdn_url = "https://cdn.projectbabbage.com/blockheaders/"
        json_resource = f"{cdn_url}/testNetBlockHeaders.json"

        # When
        info = fetch.fetch_json(json_resource)

        # Then
        assert info is not None
        assert len(info["files"]) > 4

    @pytest.mark.integration
    def test_download(self) -> None:
        """Given: ChaintracksFetch instance and CDN URL
           When: Download testNet_0.headers file
           Then: Returns 8000000 bytes with valid hash

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/ChaintracksFetch.test.ts
                   test('1 download')
        """
        # Given
        fetch = ChaintracksFetch()
        cdn_url = "https://cdn.projectbabbage.com/blockheaders/"
        url = f"{cdn_url}/testNet_0.headers"

        # When
        data = fetch.download(url)

        # Then
        assert len(data) == 8000000
        file_hash = as_string(sha256_hash(as_array(data)), "base64")
        assert valid_bulk_header_files_by_file_hash()[file_hash] is not None

    @pytest.mark.integration
    def test_download_716(self) -> None:
        """Given: ChaintracksFetch instance and CDN URL
           When: Download testNet_4.headers file
           Then: Returns 8000000 bytes (80 * 100000) with valid hash

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/ChaintracksFetch.test.ts
                   test('3 download')
        """
        # Given
        fetch = ChaintracksFetch()
        cdn_url = "https://cdn.projectbabbage.com/blockheaders/"
        url = f"{cdn_url}/testNet_4.headers"

        # When
        data = fetch.download(url)

        # Then
        assert len(data) == 80 * 100000
        file_hash = as_string(sha256_hash(as_array(data)), "base64")
        assert valid_bulk_header_files_by_file_hash()[file_hash] is not None

    @pytest.mark.integration
    def test_download_717(self) -> None:
        """Given: ChaintracksFetch instance and CDN URL
           When: Download testNet_15.headers file
           Then: Returns data with valid hash

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/ChaintracksFetch.test.ts
                   test('4 download')
        """
        # Given
        fetch = ChaintracksFetch()
        cdn_url = "https://cdn.projectbabbage.com/blockheaders/"
        url = f"{cdn_url}/testNet_15.headers"

        # When
        data = fetch.download(url)

        # Then
        file_hash = as_string(sha256_hash(as_array(data)), "base64")
        assert valid_bulk_header_files_by_file_hash()[file_hash] is not None
