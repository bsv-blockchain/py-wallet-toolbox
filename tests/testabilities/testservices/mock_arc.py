"""Mock ARC service with script verification.

This module provides a mock ARC that verifies transaction scripts before
accepting them, catching signing bugs early in tests.

Reference: go-wallet-toolbox/pkg/internal/testabilities/testservices/fixture_arc.go

Key features:
- Script verification using Transaction.verify(scripts_only=True)
- Stores broadcast transactions for later queries
- Simulates SEEN_ON_NETWORK, MINED, DOUBLE_SPEND_ATTEMPTED states
"""

import asyncio
import logging
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MockBroadcastResult:
    """Result of a mock broadcast operation."""

    txid: str | None = None
    status: str = "SEEN_ON_NETWORK"
    http_status: int = 200
    error: str | None = None
    extra_info: str | None = None
    competing_txs: list[str] = field(default_factory=list)


@dataclass
class KnownTransaction:
    """A transaction known to the mock ARC."""

    txid: str
    status: str = "SEEN_ON_NETWORK"
    http_status: int = 200
    block_height: int | None = None
    block_hash: str | None = None
    merkle_path: str | None = None
    no_body: bool = False
    unreachable: bool = False
    competing_txs: list[str] = field(default_factory=list)


class MockARCQueryFixture:
    """Fixture for configuring mock ARC query responses."""

    def __init__(self, arc: "MockARC", txid: str):
        self.arc = arc
        self.txid = txid

    def will_return_http_status(self, http_status: int) -> "MockARCQueryFixture":
        """Configure the query to return a specific HTTP status."""
        tx = self.arc._get_or_create_known_tx(self.txid)
        tx.http_status = http_status
        return self

    def will_be_unreachable(self) -> "MockARCQueryFixture":
        """Configure the query to fail as unreachable."""
        tx = self.arc._get_or_create_known_tx(self.txid)
        tx.unreachable = True
        return self

    def will_return_no_body(self) -> "MockARCQueryFixture":
        """Configure the query to return no response body."""
        tx = self.arc._get_or_create_known_tx(self.txid)
        tx.no_body = True
        return self

    def will_return_different_txid(self) -> "MockARCQueryFixture":
        """Configure the query to return a rotated (different) txid."""
        tx = self.arc._get_or_create_known_tx(self.txid)
        # Rotate the txid by 7 characters
        tx.txid = self.txid[7:] + self.txid[:7]
        return self

    def will_return_double_spending(self, *competing_txs: str) -> "MockARCQueryFixture":
        """Configure the query to indicate double spend."""
        tx = self.arc._get_or_create_known_tx(self.txid)
        tx.status = "DOUBLE_SPEND_ATTEMPTED"
        tx.competing_txs = list(competing_txs)
        return self

    def will_return_transaction_without_merkle_path(self) -> "MockARCQueryFixture":
        """Configure the query to return transaction without merkle path."""
        tx = self.arc._get_or_create_known_tx(self.txid)
        tx.status = "SEEN_ON_NETWORK"
        tx.merkle_path = None
        tx.unreachable = False
        tx.no_body = False
        return self

    def will_return_transaction_with_merkle_path_hex(self, merkle_path: str) -> "MockARCQueryFixture":
        """Configure the query to return transaction with specific merkle path."""
        tx = self.arc._get_or_create_known_tx(self.txid)
        tx.status = "MINED"
        tx.merkle_path = merkle_path
        tx.unreachable = False
        tx.no_body = False
        return self

    def will_return_transaction_with_merkle_path(self, path) -> "MockARCQueryFixture":
        """Configure the query to return transaction with MerklePath object."""
        tx = self.arc._get_or_create_known_tx(self.txid)
        tx.status = "MINED"
        tx.merkle_path = path.to_hex() if hasattr(path, "to_hex") else str(path)
        tx.block_height = path.block_height if hasattr(path, "block_height") else None
        return self

    def will_return_with_mined_tx(self) -> "MockARCQueryFixture":
        """Configure the query to return as mined transaction."""
        tx = self.arc._get_or_create_known_tx(self.txid)
        tx.status = "MINED"
        tx.block_height = 2000  # Mock height
        return self

    def will_return_transaction_on_height(self, height: int) -> "MockARCQueryFixture":
        """Configure the query to return transaction at specific height."""
        tx = self.arc._get_or_create_known_tx(self.txid)
        tx.status = "MINED"
        tx.block_height = height
        return self

    def will_return_transaction_with_block_hash(self, block_hash: str) -> "MockARCQueryFixture":
        """Configure the query to return transaction with specific block hash."""
        tx = self.arc._get_or_create_known_tx(self.txid)
        tx.status = "MINED"
        tx.block_hash = block_hash
        return self

    def will_return_transaction_with_block_height(self, height: int) -> "MockARCQueryFixture":
        """Configure the query to return transaction at specific height."""
        return self.will_return_transaction_on_height(height)


class MockARC:
    """Mock ARC service with script verification.

    This mock ARC:
    - Verifies transaction scripts before accepting (catches signing bugs)
    - Stores broadcast transactions for later queries
    - Supports configurable responses for testing error cases

    Reference: go-wallet-toolbox/pkg/internal/testabilities/testservices/fixture_arc.go
    """

    # HTTP status codes from ARC
    HTTP_STATUS_MALFORMED = 463
    HTTP_STATUS_FEE_VALIDATION_FAILED = 473

    # Test constants
    DEPLOYMENT_ID = "py-wallet-toolbox-test"
    TEST_BLOCK_HASH = "0000000014209ae688e547a58db514ac75e3a10a81ac25b3d357fa92a8ce5128"

    def __init__(self, verify_scripts: bool = True):
        """Initialize MockARC.

        Args:
            verify_scripts: Whether to verify transaction scripts on broadcast
        """
        self.verify_scripts = verify_scripts
        self._known_transactions: dict[str, KnownTransaction] = {}
        self._lock = Lock()
        self._broadcast_without_response_body = False
        self._hold_broadcast = False

    def is_up_and_running(self) -> None:
        """Mark the mock ARC as ready to accept connections."""
        # Already ready by default

    def will_always_return_status(self, http_status: int) -> None:
        """Configure the mock to always return a specific HTTP status."""
        # This would be used for error injection testing

    def when_querying_tx(self, txid: str) -> MockARCQueryFixture:
        """Create a fixture for configuring query responses for a specific txid."""
        return MockARCQueryFixture(self, txid)

    def on_broadcast(self) -> "MockARC":
        """Get self for broadcast configuration."""
        return self

    def will_return_no_body(self) -> "MockARC":
        """Configure broadcast to return no response body."""
        self._broadcast_without_response_body = True
        return self

    def hold_broadcasting(self) -> "MockARC":
        """Hold all broadcasting (for testing timeouts)."""
        self._hold_broadcast = True
        return self

    def release_broadcasting(self) -> "MockARC":
        """Release held broadcasting."""
        self._hold_broadcast = False
        return self

    def _get_or_create_known_tx(self, txid: str) -> KnownTransaction:
        """Get or create a known transaction entry."""
        with self._lock:
            if txid not in self._known_transactions:
                self._known_transactions[txid] = KnownTransaction(txid=txid)
            return self._known_transactions[txid]

    def _get_known_transaction(self, txid: str) -> KnownTransaction | None:
        """Get a known transaction by txid."""
        with self._lock:
            return self._known_transactions.get(txid)

    def _save_known_transaction(self, tx: KnownTransaction) -> None:
        """Save a known transaction."""
        with self._lock:
            self._known_transactions[tx.txid] = tx

    def verify_tx_scripts(self, tx) -> bool:
        """Verify transaction scripts.

        This mirrors Go's verifyTxScripts() in fixture_arc.go.

        Args:
            tx: Transaction to verify

        Returns:
            bool: True if all scripts are valid
        """
        if not self.verify_scripts:
            return True

        try:
            # Check each input has an unlocking script
            for vin, tx_input in enumerate(tx.inputs):
                unlock_script = getattr(tx_input, "unlocking_script", None)
                if not unlock_script or len(unlock_script) == 0:
                    logger.warning(f"Transaction {tx.txid()} has input {vin} without unlocking script")
                    return False

                # Log debug info
                logger.debug(f"Transaction {tx.txid()} input {vin} unlocking script: {unlock_script}")

                # Check source transaction is available
                source_tx = getattr(tx_input, "source_transaction", None)
                if source_tx:
                    source_vout = getattr(tx_input, "source_tx_out_index", 0)
                    if source_vout < len(source_tx.outputs):
                        utxo = source_tx.outputs[source_vout]
                        if hasattr(utxo, "locking_script") and utxo.locking_script:
                            logger.debug(
                                f"Transaction {tx.txid()} input {vin} source locking script: {utxo.locking_script}"
                            )

            # Full script verification using Transaction.verify()
            # This mirrors TS Spend.validate() and Go spv.VerifyScripts()
            async def _async_verify():
                return await tx.verify(chaintracker=None, scripts_only=True)

            try:
                loop = asyncio.get_running_loop()
                # Already in async context
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    is_valid = loop.run_in_executor(pool, lambda: asyncio.run(_async_verify()))
            except RuntimeError:
                # No running loop
                is_valid = asyncio.run(_async_verify())

            if not is_valid:
                logger.warning(f"Transaction {tx.txid()} has invalid scripts")
                return False

            return True

        except Exception as e:
            logger.warning(f"Script verification failed: {e}")
            return False

    async def broadcast(self, beef_hex: str) -> MockBroadcastResult:
        """Broadcast a transaction (mock implementation).

        Args:
            beef_hex: BEEF hex string to broadcast

        Returns:
            MockBroadcastResult: The broadcast result
        """
        if self._hold_broadcast:
            # Wait indefinitely (for timeout testing)
            await asyncio.sleep(float("inf"))

        try:
            from bsv.transaction import Beef

            # Parse BEEF
            beef_bytes = bytes.fromhex(beef_hex)
            beef = Beef.from_bytes(beef_bytes)

            # Get main transaction
            tx = beef.get_main_tx()
            if tx is None:
                return MockBroadcastResult(
                    http_status=self.HTTP_STATUS_MALFORMED,
                    error="no transaction found - empty request body",
                )

            # Verify scripts
            if self.verify_scripts and not self.verify_tx_scripts(tx):
                return MockBroadcastResult(
                    http_status=self.HTTP_STATUS_FEE_VALIDATION_FAILED,
                    error="inputs must have an unlocking script or an unlocker",
                )

            # Store the transaction
            txid = tx.txid()
            known_tx = self._get_or_create_known_tx(txid)
            if known_tx.status != "MINED":
                known_tx.status = "SEEN_ON_NETWORK"
            self._save_known_transaction(known_tx)

            if self._broadcast_without_response_body:
                return MockBroadcastResult(txid=txid, http_status=200)

            return MockBroadcastResult(
                txid=txid,
                status=known_tx.status,
                http_status=200,
            )

        except Exception as e:
            return MockBroadcastResult(
                http_status=self.HTTP_STATUS_MALFORMED,
                error=str(e),
            )

    async def get_tx_status(self, txid: str) -> dict[str, Any]:
        """Get transaction status (mock implementation).

        Args:
            txid: Transaction ID to query

        Returns:
            dict: Transaction status response
        """
        known_tx = self._get_known_transaction(txid)

        if known_tx is None:
            return {
                "txid": txid,
                "status": "NOT_FOUND",
            }

        if known_tx.unreachable:
            raise ConnectionError("ARC unreachable")

        if known_tx.no_body:
            return {}

        result = {
            "txid": known_tx.txid,
            "txStatus": known_tx.status,
        }

        if known_tx.block_height is not None:
            result["blockHeight"] = known_tx.block_height

        if known_tx.block_hash is not None:
            result["blockHash"] = known_tx.block_hash

        if known_tx.merkle_path is not None:
            result["merklePath"] = known_tx.merkle_path

        if known_tx.competing_txs:
            result["competingTxs"] = known_tx.competing_txs

        return result

    def tx_info_json(self, txid: str) -> str:
        """Get transaction info as JSON string.

        Args:
            txid: Transaction ID

        Returns:
            str: JSON string of transaction info
        """
        import json

        known_tx = self._get_known_transaction(txid)
        if known_tx is None:
            raise ValueError(f"Transaction {txid} not found - invalid test setup")

        result = {
            "txid": known_tx.txid,
            "txStatus": known_tx.status,
        }

        if known_tx.block_height is not None:
            result["blockHeight"] = known_tx.block_height

        if known_tx.merkle_path is not None:
            result["merklePath"] = known_tx.merkle_path

        return json.dumps(result)
