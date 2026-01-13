"""ChaintracksFetch - HTTP fetch utilities for chaintracks.

Provides HTTP utilities for fetching data from chaintracks services.

Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/ChaintracksFetch.test.ts
"""

from typing import Any

import requests


class ChaintracksFetch:
    """HTTP fetch utilities for chaintracks data.

    Provides methods for fetching JSON and binary data from chaintracks services.
    """

    def __init__(self):
        """Initialize ChaintracksFetch."""
        self.session = requests.Session()

    def fetch_json(self, url: str) -> dict[str, Any]:
        """Fetch JSON data from URL.

        Args:
            url: URL to fetch

        Returns:
            Parsed JSON data

        Raises:
            Exception: If request fails or JSON parsing fails
        """
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def download(self, url: str) -> bytes:
        """Download binary data from URL.

        Args:
            url: URL to download from

        Returns:
            Binary data

        Raises:
            Exception: If request fails
        """
        response = self.session.get(url)
        response.raise_for_status()
        return response.content
