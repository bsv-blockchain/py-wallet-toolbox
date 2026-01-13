"""WhatsOnChain API client for blockchain data.

Provides HTTP client for interacting with WhatsOnChain API to fetch
block headers and chain information.

Reference: go-wallet-toolbox/pkg/services/chaintracks/ingest/chaintracks_woc_client.go
"""

import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ...wallet_services import Chain

logger = logging.getLogger(__name__)


class WOCBlockHeaderDTO:
    """DTO for block header from WhatsOnChain API."""

    def __init__(self, data: dict[str, Any]):
        self.hash = data.get("hash", "")
        self.size = data.get("size", 0)
        self.height = data.get("height", 0)
        self.version = data.get("version", 0)
        self.version_hex = data.get("versionHex", "")
        self.merkle_root = data.get("merkleroot", "")
        self.time = data.get("time", 0)
        self.median_time = data.get("mediantime", 0)
        self.nonce = data.get("nonce", 0)
        self.bits = data.get("bits", "")
        self.difficulty = data.get("difficulty", 0.0)
        self.chainwork = data.get("chainwork", "")
        self.prev_block = data.get("previousblockhash", "")
        self.next_block = data.get("nextblockhash", "")
        self.confirmations = data.get("confirmations", 0)

    def to_block_header(self) -> dict[str, Any]:
        """Convert to block header dict."""
        # Handle genesis block (no previous block)
        if not self.prev_block:
            self.prev_block = "0000000000000000000000000000000000000000000000000000000000000000"

        # Convert bits from hex string to int
        bits_int = int(self.bits, 16) if self.bits else 0

        return {
            "version": self.version,
            "previousHash": self.prev_block,
            "merkleRoot": self.merkle_root,
            "time": self.time,
            "bits": bits_int,
            "nonce": self.nonce,
            "height": self.height,
            "hash": self.hash,
        }


class WOCChainInfoDTO:
    """DTO for chain info from WhatsOnChain API."""

    def __init__(self, data: dict[str, Any]):
        self.blocks = data.get("blocks", 0)


class WOCClient:
    """HTTP client for WhatsOnChain API."""

    def __init__(self, chain: Chain, api_key: str | None = None, timeout: int = 30):
        """Initialize WOC client.

        Args:
            chain: Blockchain network ("main" or "test")
            api_key: Optional API key for WhatsOnChain
            timeout: Request timeout in seconds
        """
        self.chain = chain
        self.api_key = api_key
        self.timeout = timeout

        # Base URLs for WhatsOnChain
        self.base_urls = {
            "main": "https://api.whatsonchain.com/v1/bsv/main",
            "test": "https://api.whatsonchain.com/v1/bsv/test",
        }

        # Setup requests session with retry strategy
        self.session = requests.Session()

        retry_strategy = Retry(total=3, status_forcelist=[429, 500, 502, 503, 504], backoff_factor=1)

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set headers
        self.session.headers.update(
            {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "py-wallet-toolbox"}
        )

        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"

    def _get_base_url(self) -> str:
        """Get base URL for current chain."""
        return self.base_urls.get(self.chain, self.base_urls["main"])

    def get_header_by_hash(self, block_hash: str) -> WOCBlockHeaderDTO | None:
        """Fetch block header by hash.

        Args:
            block_hash: Block hash

        Returns:
            Block header DTO or None if not found

        Raises:
            Exception: If request fails
        """
        url = f"{self._get_base_url()}/block/{block_hash}/header"

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            return WOCBlockHeaderDTO(data)

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise Exception(f"Failed to fetch block header: {e}") from e
        except Exception as e:
            raise Exception(f"Failed to fetch block header: {e}") from e

    def get_present_height(self) -> int:
        """Get current blockchain height.

        Returns:
            Current block height

        Raises:
            Exception: If request fails
        """
        url = f"{self._get_base_url()}/chain/info"

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            info = WOCChainInfoDTO(data)
            return info.blocks

        except Exception as e:
            raise Exception(f"Failed to fetch chain info: {e}") from e

    def get_last_headers(self, count: int = 10) -> list[WOCBlockHeaderDTO]:
        """Get last N block headers.

        Args:
            count: Number of headers to fetch (default 10)

        Returns:
            List of block header DTOs

        Raises:
            Exception: If request fails
        """
        url = f"{self._get_base_url()}/block/headers/{count}"

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            return [WOCBlockHeaderDTO(header_data) for header_data in data]

        except Exception as e:
            raise Exception(f"Failed to fetch last headers: {e}") from e

    def get_headers_resource_list(self) -> list[str]:
        """Get list of available bulk header files.

        Returns:
            List of bulk header file names

        Raises:
            Exception: If request fails
        """
        url = f"{self._get_base_url()}/block/headers/files"

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            return data.get("files", [])

        except Exception as e:
            raise Exception(f"Failed to fetch headers resource list: {e}") from e

    def download_header_file(self, url: str) -> bytes:
        """Download a bulk header file from the given URL.

        Args:
            url: URL to download from

        Returns:
            File contents as bytes

        Raises:
            Exception: If download fails
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            return response.content

        except Exception as e:
            raise Exception(f"Failed to download header file from {url}: {e}") from e
