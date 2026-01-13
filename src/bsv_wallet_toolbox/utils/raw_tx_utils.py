"""Raw transaction helpers.

Utilities around fetching raw transactions from a Services provider, including
small retry loops to tolerate mempool / provider propagation delays.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RawTxRetryConfig:
    """Retry policy for mempool propagation delays."""

    max_wait_seconds: int = 90
    initial_sleep_seconds: int = 2
    later_sleep_seconds: int = 5
    later_threshold_seconds: int = 10


def fetch_raw_tx_with_retry(services: Any, txid: str, retry: RawTxRetryConfig | None = None) -> str:
    """Fetch rawTx (hex) with retries.

    The Services provider might lag on mempool visibility right after broadcast.
    """
    retry = retry or RawTxRetryConfig()
    start = time.time()
    while True:
        raw_hex = services.get_raw_tx(txid)
        if raw_hex:
            return raw_hex
        elapsed = int(time.time() - start)
        if elapsed >= retry.max_wait_seconds:
            break
        wait_s = retry.initial_sleep_seconds if elapsed < retry.later_threshold_seconds else retry.later_sleep_seconds
        time.sleep(wait_s)
    raise RuntimeError(f"Unable to fetch raw transaction for {txid}")
