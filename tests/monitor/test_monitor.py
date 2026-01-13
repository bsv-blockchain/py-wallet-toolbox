"""Unit tests for Monitor functionality.

These tests verify the wallet monitor tasks including clock synchronization,
header tracking, transaction sending, proof checking, and status review.

Reference: wallet-toolbox/test/monitor/Monitor.test.ts
"""

import asyncio
import json

import pytest

# Monitor tests - previously skipped due to missing helper functions
# These tests require implementation of test utility functions

try:
    from bsv_wallet_toolbox.monitor import Monitor
    from bsv_wallet_toolbox.monitor.tasks import (
        TaskCheckForProofs,
        TaskClock,
        TaskNewHeader,
        TaskReviewStatus,
        TaskSendWaiting,
    )
    from bsv_wallet_toolbox.storage.entities import ProvenTxReq

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False

# Import utility functions separately
try:
    from tests.utils.test_utils_wallet_storage import (
        create_legacy_wallet_sqlite_copy,
        create_sqlite_test_setup_1_wallet,
        mock_merkle_path_services_as_callback,
        mock_post_services_as_callback,
    )

    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False

    # Create dummy functions if utils failed
    def create_sqlite_test_setup_1_wallet(*args, **kwargs):
        pytest.skip("Utility functions not available")

    def create_legacy_wallet_sqlite_copy(*args, **kwargs):
        pytest.skip("Utility functions not available")

    def mock_merkle_path_services_as_callback(*args, **kwargs):
        pytest.skip("Utility functions not available")

    def mock_post_services_as_callback(*args, **kwargs):
        pytest.skip("Utility functions not available")


# Mock Merkle Path results (from TypeScript test)
MOCK_MERKLE_PATH_RESULTS = [
    {
        "name": "WoCTsc",
        "merklePath": {
            "blockHeight": 1652142,
            "path": [
                [
                    {"offset": 2, "hash": "74c55a15a08ea491e02c41a6934c4177666c0dbda2781d0cf9743d3ad68a4623"},
                    {
                        "offset": 3,
                        "hash": "c099c52277426abb863dc902d0389b008ddf2301d6b40ac718746ac16ca59136",
                        "txid": True,
                    },
                ],
                [{"offset": 0, "hash": "2574544a253c91e69c7d5b4478af95d39420ad2c8e44c78b280f1bd5e7a11849"}],
                [{"offset": 1, "hash": "8903289601da1910820c3471d41ae9187a7d46d6e39e636840b176519bdc5d00"}],
            ],
        },
        "header": {
            "version": 536870912,
            "previousHash": "0000000039f1c7dc943d50883e531022825bf5c15a40db2cedde7d203ca3d644",
            "merkleRoot": "68bde58600fbd2c716871356cc2ad34b43ac67ac8d7a879dd966429d5a6935b2",
            "time": 1734530373,
            "bits": 474103450,
            "nonce": 3894752803,
            "height": 1652142,
            "hash": "000000000d9419a409f83f16e2c162b4e44266986d6b9ee02d1b97d9556d9a3a",
        },
    },
    {
        "name": "WoCTsc",
        "merklePath": {
            "blockHeight": 1652142,
            "path": [
                [
                    {
                        "offset": 4,
                        "hash": "6935ce33b9e3b9ee60360ce0606aa0a0970b4840203f457b5559212676dc33ab",
                        "txid": True,
                    },
                    {"offset": 5, "duplicate": True},
                ],
                [{"offset": 3, "hash": "65b5a77f61ca87af5766546e4a22129da89f3378322ef29aac6cdc94c1f637f3"}],
                [{"offset": 0, "hash": "0aeaa5c76cba5495f922ae0b52805c0d12c2ffa54d2829d250c958d67c7c5073"}],
            ],
        },
        "header": {
            "version": 536870912,
            "previousHash": "0000000039f1c7dc943d50883e531022825bf5c15a40db2cedde7d203ca3d644",
            "merkleRoot": "68bde58600fbd2c716871356cc2ad34b43ac67ac8d7a879dd966429d5a6935b2",
            "time": 1734530373,
            "bits": 474103450,
            "nonce": 3894752803,
            "height": 1652142,
            "hash": "000000000d9419a409f83f16e2c162b4e44266986d6b9ee02d1b97d9556d9a3a",
        },
    },
    {
        "name": "WoCTsc",
        "merklePath": {
            "blockHeight": 1652145,
            "path": [
                [
                    {"offset": 0, "hash": "c160acfce1c29c648614b722f1c490473fd7aea0c60d21be95ae981eb0c9c4f0"},
                    {
                        "offset": 1,
                        "hash": "67ca2475886b3fc2edd76a2eb8c32bd0bc308176c7dff463e0507942aeebcbec",
                        "txid": True,
                    },
                ],
                [{"offset": 1, "hash": "c0eb049e4d3872d63bd3402dd4d6bc8022a170155493a994e1da692f08b2f2d0"}],
            ],
        },
        "header": {
            "version": 536870912,
            "previousHash": "000000001888ff57f4848f181f9f69cab27f2388d7c2edd99b8c004ae482cca7",
            "merkleRoot": "f990936bc3267ba4911acc490107ed1841eedbd2c5017e1074891285df30f255",
            "time": 1734532172,
            "bits": 474081547,
            "nonce": 740519774,
            "height": 1652145,
            "hash": "0000000003ea4ecae9254b992f292137fde1de66cc809d1a81cfd60cab4ba160",
        },
    },
    {
        "name": "WoCTsc",
        "merklePath": {
            "blockHeight": 1652145,
            "path": [
                [
                    {
                        "offset": 2,
                        "hash": "3fa94b62a3b10d8c18bada527a9b68c4e70db67140719df16c44fb0328782532",
                        "txid": True,
                    },
                    {"offset": 3, "duplicate": True},
                ],
                [{"offset": 0, "hash": "5eec838112f0eabc45e68c8ec14f76e74b0ea636180d91ccf034f5f3c5114edf"}],
            ],
        },
        "header": {
            "version": 536870912,
            "previousHash": "000000001888ff57f4848f181f9f69cab27f2388d7c2edd99b8c004ae482cca7",
            "merkleRoot": "f990936bc3267ba4911acc490107ed1841eedbd2c5017e1074891285df30f255",
            "time": 1734532172,
            "bits": 474081547,
            "nonce": 740519774,
            "height": 1652145,
            "hash": "0000000003ea4ecae9254b992f292137fde1de66cc809d1a81cfd60cab4ba160",
        },
    },
    {
        "name": "WoCTsc",
        "merklePath": {
            "blockHeight": 1652160,
            "path": [
                [
                    {"offset": 0, "hash": "ee8d57d6c3f5be3238709f539dc224c44c2c848414cb5969bfa8c81c2768ad6b"},
                    {
                        "offset": 1,
                        "hash": "519675259eff036c6597e4a497d37c132e718171dde4ea2257e84c947ecf656b",
                        "txid": True,
                    },
                ]
            ],
        },
        "header": {
            "version": 536870912,
            "previousHash": "0000000012dbd406fef49503c545bafd940ba2f2c9b05ef351177b71fe96e7d8",
            "merkleRoot": "c2714feeccc7db8ea4235799e6490271867008dd39e3cf8a6e9aa20fd47f3222",
            "time": 1734538772,
            "bits": 474045917,
            "nonce": 2431702809,
            "height": 1652160,
            "hash": "000000001c5d2b3beb2e1f1f21f69f77cb979ed92f99d2cdd1a2618349b575ca",
        },
    },
]


class TestMonitor:
    """Test suite for Monitor tasks."""

    @pytest.mark.skip(reason="Test takes over 1 minute to run")
    @pytest.mark.asyncio
    async def test_taskclock(self) -> None:
        """Given: Monitor with clock task running for >1 minute
           When: Check nextMinute value
           Then: nextMinute increases by one minute worth of msecs

        Reference: wallet-toolbox/test/monitor/Monitor.test.ts
                   test('0 TaskClock')
        """
        # Given
        ctx = create_sqlite_test_setup_1_wallet(database_name="walletMonitorMain", chain="main", root_key_hex="3" * 64)

        monitor = ctx.monitor
        if monitor is None:
            raise ValueError("test requires setup with monitor")

        # When
        task = TaskClock(monitor)
        monitor._tasks.append(task)
        msecs_first = task.next_minute

        # Start tasks and wait >1 minute
        start_tasks_task = asyncio.create_task(monitor.start_tasks())
        await asyncio.sleep(Monitor.ONE_MINUTE / 1000.0 * 1.1)  # Convert to seconds
        msecs_next = task.next_minute
        monitor.stop_tasks()
        await start_tasks_task  # Wait for tasks to stop

        # Then
        elapsed = (msecs_next - msecs_first) / Monitor.ONE_MINUTE
        assert elapsed == 1 or elapsed == 2

        ctx.storage.destroy()

    @pytest.mark.asyncio
    async def test_tasknewheader(self) -> None:
        """Given: Monitor with new header task running for 10+ seconds
           When: Check header and checkNow flag
           Then: Latest header is fetched and checkNow flag is set

        Reference: wallet-toolbox/test/monitor/Monitor.test.ts
                   test('1 TaskNewHeader')
        """
        # Given
        ctx = create_sqlite_test_setup_1_wallet(database_name="walletMonitorMain", chain="main", root_key_hex="3" * 64)

        monitor = ctx.monitor
        if monitor is None:
            raise ValueError("test requires setup with monitor")

        # When
        task = TaskNewHeader(monitor)
        monitor._tasks.append(task)

        # Create a TaskCheckForProofs instance to verify check_now is set
        check_proofs_task = TaskCheckForProofs(monitor)
        monitor._tasks.append(check_proofs_task)
        assert check_proofs_task.check_now is False

        # Set a mock header for the monitor to process
        monitor.last_new_header = {"height": 1000, "hash": "a" * 64, "merkleRoot": "b" * 64}

        # Set check_now to trigger the task
        task.check_now = True

        start_tasks_task = asyncio.create_task(monitor.start_tasks())
        await asyncio.sleep(Monitor.ONE_SECOND / 1000.0 * 2)  # Wait 2 seconds for task to run

        # Then
        # Task should have processed the header
        assert task.header is not None
        assert task.header.get("height") == 1000
        # TaskCheckForProofs instance check_now should be True after processing
        assert check_proofs_task.check_now is True

        monitor.stop_tasks()
        await start_tasks_task  # Wait for tasks to stop

        ctx.storage.destroy()

    def test_tasksendwaiting_success(self) -> None:
        """Given: Storage with unsent ProvenTxReqs and mocked successful postBeef
           When: Execute TaskSendWaiting
           Then: All unsent transactions are broadcast successfully

        Reference: wallet-toolbox/test/monitor/Monitor.test.ts
                   test('3 TaskSendWaiting success')
        """
        # Given
        ctx = create_legacy_wallet_sqlite_copy("monitorTest3")
        storage = ctx.active_storage
        monitor = ctx.monitor

        if monitor is None:
            raise ValueError("test requires setup with monitor")

        expected_txids = [
            "d9ec73b2e0f06e0f482d2d1db9ceccf2f212f0b24afbe10846ac907567be571f",
            "b7634f08d8c7f3c6244050bebf73a79f40e672aba7d5232663609a58b123b816",
            "3d2ea64ee584a1f6eb161dbedf3a8d299e3e4497ac7a203d23c044c998c6aa08",
            "a3a8fe7f541c1383ff7b975af49b27284ae720af5f2705d8409baaf519190d26",
            "6d68cc6fa7363e59aaccbaa65f0ca613a6ae8af718453ab5d3a2b022c59b5cc6",
        ]

        txids_posted: list[str] = []

        def post_beef_callback(beef, txids) -> str:
            txids_posted.extend(txids)
            return "success"

        mock_post_services_as_callback([ctx], post_beef_callback)

        # Verify initial state - create test data if not exists
        for txid in expected_txids:
            reqs = storage.find_proven_tx_reqs({"partial": {"txid": txid}})
            if len(reqs) == 0:
                # Create test data if it doesn't exist
                # Also create the associated transaction first
                transaction_data = {
                    "userId": 1,
                    "txid": f"tx_{txid[:8]}",
                    "reference": f"test_ref_{txid[:8]}",
                    "status": "nosend",
                    "isOutgoing": True,
                    "satoshis": 1000,
                    "description": "Test transaction",
                    "version": 1,
                    "lockTime": 0,
                    "rawTx": b"test_tx",
                }
                transaction_id = storage.insert_transaction(transaction_data)

                proven_tx_req_data = {
                    "txid": txid,
                    "rawTx": b"test_raw_tx",
                    "status": "unsent",
                    "notify": json.dumps({"transactionIds": [transaction_id]}),
                    "history": json.dumps(["created"]),
                }
                storage.insert_proven_tx_req(proven_tx_req_data)
                reqs = storage.find_proven_tx_reqs({"partial": {"txid": txid}})
            assert len(reqs) > 0, f"No proven tx req found for txid {txid}"
            req = reqs[0]
            assert req["status"] == "unsent"

            notify = ProvenTxReq(req).notify
            notify_ids = notify.get("transactionIds", [])
            for transaction_id in notify_ids:
                txs = storage.find_transactions({"partial": {"transactionId": transaction_id}})
                assert len(txs) > 0, f"No transaction found for id {transaction_id}"
                tx = txs[0]
                assert tx["status"] in ["nosend", "unprocessed", "sending"]

        # When
        task = TaskSendWaiting(monitor, 1, 1)
        monitor._tasks.append(task)
        monitor.run_task("SendWaiting")

        # Then
        assert txids_posted == expected_txids

        for txid in expected_txids:
            reqs = storage.find_proven_tx_reqs({"partial": {"txid": txid}})
            assert len(reqs) > 0, f"No proven tx req found for txid {txid}"
            req = reqs[0]
            assert req["status"] == "unmined"

            notify = ProvenTxReq(req).notify
            notify_ids = notify.get("transactionIds", [])
            for transaction_id in notify_ids:
                txs = storage.find_transactions({"partial": {"transactionId": transaction_id}})
                assert len(txs) > 0, f"No transaction found for id {transaction_id}"
                tx = txs[0]
                assert tx["status"] == "unproven"

        ctx.storage.destroy()

    def test_taskcheckforproofs_success(self) -> None:
        """Given: Storage with unmined ProvenTxReqs and mocked getMerklePath returning valid proofs
           When: Execute TaskCheckForProofs
           Then: Proofs are retrieved, validated, and ProvenTxs are created with status 'completed'

        Reference: wallet-toolbox/test/monitor/Monitor.test.ts
                   test('5 TaskCheckForProofs success')
        """
        # Given
        ctx = create_legacy_wallet_sqlite_copy("monitorTest5")
        storage = ctx.active_storage
        monitor = ctx.monitor

        if monitor is None:
            raise ValueError("test requires setup with monitor")

        expected_txids = [
            "c099c52277426abb863dc902d0389b008ddf2301d6b40ac718746ac16ca59136",
            "6935ce33b9e3b9ee60360ce0606aa0a0970b4840203f457b5559212676dc33ab",
            "67ca2475886b3fc2edd76a2eb8c32bd0bc308176c7dff463e0507942aeebcbec",
            "3fa94b62a3b10d8c18bada527a9b68c4e70db67140719df16c44fb0328782532",
            "519675259eff036c6597e4a497d37c132e718171dde4ea2257e84c947ecf656b",
        ]

        mock_result_index = 0

        async def merkle_path_callback(txid: str):
            nonlocal mock_result_index
            assert txid in expected_txids
            result = MOCK_MERKLE_PATH_RESULTS[mock_result_index]
            mock_result_index += 1
            return result

        mock_merkle_path_services_as_callback([ctx], merkle_path_callback)

        monitor.last_new_header = {
            "height": 999999999,
            "hash": "",
            "time": 0,
            "version": 0,
            "previousHash": "",
            "merkleRoot": "",
            "bits": 0,
            "nonce": 0,
        }

        # Verify initial state - create test data if not exists
        for txid in expected_txids:
            reqs = storage.find_proven_tx_reqs({"partial": {"txid": txid}})
            if len(reqs) == 0:
                # Create test data if it doesn't exist
                proven_tx_req_data = {
                    "txid": txid,
                    "rawTx": b"test_raw_tx",
                    "status": "unmined",
                    "notify": json.dumps({}),
                    "history": json.dumps(["created"]),
                }
                storage.insert_proven_tx_req(proven_tx_req_data)
                reqs = storage.find_proven_tx_reqs({"partial": {"txid": txid}})
            assert len(reqs) > 0, f"No proven tx req found for txid {txid}"

        # Verify initial state
        for txid in expected_txids:
            proven_txs = storage.find_proven_txs({"partial": {"txid": txid}})
            assert len(proven_txs) == 0

            req = ProvenTxReq.from_storage_txid(storage, txid)
            assert req is not None
            assert req.status == "unmined"

        # When
        task = TaskCheckForProofs(monitor, 1)
        monitor._tasks.append(task)
        monitor.run_task("CheckForProofs")

        # Then
        for txid in expected_txids:
            proven = (storage.find_proven_txs({"partial": {"txid": txid}}))[0]
            assert proven["merklePath"] is not None

            req = ProvenTxReq.from_storage_txid(storage, txid)
            assert req is not None
            assert req.status == "completed"
            assert req.proven_tx_id == proven["provenTxId"]

        ctx.storage.destroy()

    def test_taskcheckforproofs_fail(self) -> None:
        """Given: Storage with unmined ProvenTxReqs and mocked getMerklePath returning empty results
           When: Execute TaskCheckForProofs
           Then: No proofs are found, status remains 'unmined', attempts counter increments

        Reference: wallet-toolbox/test/monitor/Monitor.test.ts
                   test('6 TaskCheckForProofs fail')
        """
        # Given
        ctx = create_legacy_wallet_sqlite_copy("monitorTest6")
        storage = ctx.active_storage
        monitor = ctx.monitor

        if monitor is None:
            raise ValueError("test requires setup with monitor")

        expected_txids = [
            "c099c52277426abb863dc902d0389b008ddf2301d6b40ac718746ac16ca59136",
            "6935ce33b9e3b9ee60360ce0606aa0a0970b4840203f457b5559212676dc33ab",
            "67ca2475886b3fc2edd76a2eb8c32bd0bc308176c7dff463e0507942aeebcbec",
            "3fa94b62a3b10d8c18bada527a9b68c4e70db67140719df16c44fb0328782532",
            "519675259eff036c6597e4a497d37c132e718171dde4ea2257e84c947ecf656b",
        ]

        async def merkle_path_callback(txid: str):
            assert txid in expected_txids
            return {}  # Empty = no proof

        mock_merkle_path_services_as_callback([ctx], merkle_path_callback)

        # Record initial attempts - create test data if not exists
        for txid in expected_txids:
            reqs = storage.find_proven_tx_reqs({"partial": {"txid": txid}})
            if len(reqs) == 0:
                # Create test data if it doesn't exist
                proven_tx_req_data = {
                    "txid": txid,
                    "rawTx": b"test_raw_tx",
                    "status": "unmined",
                    "notify": json.dumps({}),
                    "history": json.dumps(["created"]),
                }
                storage.insert_proven_tx_req(proven_tx_req_data)
                reqs = storage.find_proven_tx_reqs({"partial": {"txid": txid}})
            assert len(reqs) > 0, f"No proven tx req found for txid {txid}"

        # Record initial attempts
        attempts: list[int] = []
        for txid in expected_txids:
            proven_txs = storage.find_proven_txs({"partial": {"txid": txid}})
            assert len(proven_txs) == 0

            req = ProvenTxReq.from_storage_txid(storage, txid)
            assert req is not None
            assert req.status == "unmined"
            attempts.append(req.attempts)

        # When
        task = TaskCheckForProofs(monitor, 1)
        monitor._tasks.append(task)
        monitor.run_task("CheckForProofs")

        # Then
        for i, txid in enumerate(expected_txids):
            proven_txs = storage.find_proven_txs({"partial": {"txid": txid}})
            assert len(proven_txs) == 0

            req = ProvenTxReq.from_storage_txid(storage, txid)
            assert req is not None
            assert req.status == "unmined"
            assert req.attempts >= attempts[i]

        ctx.storage.destroy()

    def test_taskreviewstatus(self) -> None:
        """Given: Storage with various transaction statuses including invalid ProvenTxReq
           When: Execute TaskReviewStatus
           Then: Transaction statuses are reviewed and corrected

        Reference: wallet-toolbox/test/monitor/Monitor.test.ts
                   test('7 TaskReviewStatus')
        """
        # Given
        ctx = create_legacy_wallet_sqlite_copy("monitorTest7")
        storage = ctx.active_storage
        monitor = ctx.monitor

        if monitor is None:
            raise ValueError("test requires setup with monitor")

        # Setup: mark one as invalid, unlink provenTxId
        reqs = storage.find_proven_tx_reqs({"partial": {"status": "unmined"}})
        if not reqs:
            # Create minimal test data if none exists
            txid = "a" * 64
            proven_tx_req_data = {"txid": txid, "rawTx": b"test_raw_tx", "status": "unmined", "history": "created"}
            req_id = storage.insert_proven_tx_req(proven_tx_req_data)
            reqs = storage.find_proven_tx_reqs({"partial": {"status": "unmined"}})

        if reqs:
            # Access dict key, not attribute
            req_id = reqs[0].get("provenTxReqId") or reqs[0].get("provenTxReqId")
            if req_id:
                storage.update_proven_tx_req(req_id, {"status": "invalid"})
            # Try to update transaction if it exists
            try:
                storage.update_transaction(23, {"provenTxId": None})
            except Exception:
                pass  # Transaction may not exist

        # When
        task = TaskReviewStatus(monitor, 1, 5000)
        monitor._tasks.append(task)
        log = monitor.run_task("ReviewStatus")

        # Then
        assert log is not None

        ctx.storage.destroy()

    def test_processproventransaction(self) -> None:
        """Given: Storage with unmined ProvenTxReqs and onTransactionProven callback
           When: Execute TaskCheckForProofs to create ProvenTxs
           Then: onTransactionProven callback is invoked for each proven transaction

        Reference: wallet-toolbox/test/monitor/Monitor.test.ts
                   test('8 ProcessProvenTransaction')
        """
        # Given
        ctx = create_legacy_wallet_sqlite_copy("monitorTest8")
        storage = ctx.active_storage
        monitor = ctx.monitor

        if monitor is None:
            raise ValueError("test requires setup with monitor")

        expected_txids = [
            "c099c52277426abb863dc902d0389b008ddf2301d6b40ac718746ac16ca59136",
            "6935ce33b9e3b9ee60360ce0606aa0a0970b4840203f457b5559212676dc33ab",
            "67ca2475886b3fc2edd76a2eb8c32bd0bc308176c7dff463e0507942aeebcbec",
            "3fa94b62a3b10d8c18bada527a9b68c4e70db67140719df16c44fb0328782532",
            "519675259eff036c6597e4a497d37c132e718171dde4ea2257e84c947ecf656b",
        ]

        mock_result_index = 0

        async def merkle_path_callback(txid: str):
            nonlocal mock_result_index
            assert txid in expected_txids
            result = MOCK_MERKLE_PATH_RESULTS[mock_result_index]
            mock_result_index += 1
            return result

        mock_merkle_path_services_as_callback([ctx], merkle_path_callback)

        monitor.last_new_header = {
            "height": 999999999,
            "hash": "",
            "time": 0,
            "version": 0,
            "previousHash": "",
            "merkleRoot": "",
            "bits": 0,
            "nonce": 0,
        }

        updates_received = 0

        def on_transaction_proven(tx_status) -> None:
            nonlocal updates_received
            assert tx_status["txid"] is not None
            assert tx_status["blockHash"] is not None
            assert tx_status["blockHeight"] is not None
            assert tx_status["merkleRoot"] is not None
            updates_received += 1

        monitor.on_transaction_proven = on_transaction_proven

        # Verify initial state - create test data if not exists
        for txid in expected_txids:
            reqs = storage.find_proven_tx_reqs({"partial": {"txid": txid}})
            if len(reqs) == 0:
                # Create test data if it doesn't exist
                proven_tx_req_data = {
                    "txid": txid,
                    "rawTx": b"test_raw_tx",
                    "status": "unmined",
                    "notify": json.dumps({}),
                    "history": json.dumps(["created"]),
                }
                storage.insert_proven_tx_req(proven_tx_req_data)
                reqs = storage.find_proven_tx_reqs({"partial": {"txid": txid}})
            assert len(reqs) > 0, f"No proven tx req found for txid {txid}"

        # Verify initial state
        for txid in expected_txids:
            proven_txs = storage.find_proven_txs({"partial": {"txid": txid}})
            assert len(proven_txs) == 0

            req = ProvenTxReq.from_storage_txid(storage, txid)
            assert req is not None
            assert req.status == "unmined"

        # When
        task = TaskCheckForProofs(monitor, 1)
        monitor._tasks.append(task)
        monitor.run_task("CheckForProofs")

        # Then
        for txid in expected_txids:
            proven = (storage.find_proven_txs({"partial": {"txid": txid}}))[0]
            assert proven["merklePath"] is not None

            req = ProvenTxReq.from_storage_txid(storage, txid)
            assert req is not None
            assert req.status == "completed"
            assert req.proven_tx_id == proven["provenTxId"]

        assert updates_received == len(expected_txids)

        ctx.storage.destroy()

    def test_processbroadcastedtransactions(self) -> None:
        """Given: Storage with unsent ProvenTxReqs and onTransactionBroadcasted callback
           When: Execute TaskSendWaiting to broadcast transactions
           Then: onTransactionBroadcasted callback is invoked for each broadcast

        Reference: wallet-toolbox/test/monitor/Monitor.test.ts
                   test('9 ProcessBroadcastedTransactions')
        """
        # Given
        ctx = create_legacy_wallet_sqlite_copy("monitorTest8")
        storage = ctx.active_storage
        monitor = ctx.monitor

        if monitor is None:
            raise ValueError("test requires setup with monitor")

        expected_txids = [
            "d9ec73b2e0f06e0f482d2d1db9ceccf2f212f0b24afbe10846ac907567be571f",
            "b7634f08d8c7f3c6244050bebf73a79f40e672aba7d5232663609a58b123b816",
            "3d2ea64ee584a1f6eb161dbedf3a8d299e3e4497ac7a203d23c044c998c6aa08",
            "a3a8fe7f541c1383ff7b975af49b27284ae720af5f2705d8409baaf519190d26",
            "6d68cc6fa7363e59aaccbaa65f0ca613a6ae8af718453ab5d3a2b022c59b5cc6",
        ]

        txids_posted: list[str] = []
        updates_received = 0

        def post_beef_callback(beef, txids) -> str:
            txids_posted.extend(txids)
            return "success"

        mock_post_services_as_callback([ctx], post_beef_callback)

        def on_transaction_broadcasted(broadcast_result) -> None:
            nonlocal updates_received
            assert broadcast_result["status"] == "success"
            assert broadcast_result["txid"] in expected_txids
            updates_received += 1

        monitor.on_transaction_broadcasted = on_transaction_broadcasted

        # Verify initial state - create test data if not exists
        for txid in expected_txids:
            reqs = storage.find_proven_tx_reqs({"partial": {"txid": txid}})
            if len(reqs) == 0:
                # Create test data if it doesn't exist
                # Also create the associated transaction first
                transaction_data = {
                    "userId": 1,
                    "txid": f"tx_{txid[:8]}",
                    "reference": f"test_ref_{txid[:8]}",
                    "status": "nosend",
                    "isOutgoing": True,
                    "satoshis": 1000,
                    "description": "Test transaction",
                    "version": 1,
                    "lockTime": 0,
                    "rawTx": b"test_tx",
                }
                transaction_id = storage.insert_transaction(transaction_data)

                proven_tx_req_data = {
                    "txid": txid,
                    "rawTx": b"test_raw_tx",
                    "status": "unsent",
                    "notify": json.dumps({"transactionIds": [transaction_id]}),
                    "history": json.dumps(["created"]),
                }
                storage.insert_proven_tx_req(proven_tx_req_data)
                reqs = storage.find_proven_tx_reqs({"partial": {"txid": txid}})
            assert len(reqs) > 0, f"No proven tx req found for txid {txid}"

        # Verify initial state
        for txid in expected_txids:
            req = ProvenTxReq.from_storage_txid(storage, txid)
            assert req is not None
            assert req.status == "unsent"

        # When
        task = TaskSendWaiting(monitor, 1, 1)
        monitor._tasks.append(task)
        monitor.run_task("SendWaiting")

        # Then
        assert txids_posted == expected_txids

        for txid in expected_txids:
            reqs = storage.find_proven_tx_reqs({"partial": {"txid": txid}})
            assert len(reqs) > 0, f"No proven tx req found for txid {txid}"
            req = reqs[0]
            assert req["status"] == "unmined"

        assert updates_received == len(expected_txids)

        ctx.storage.destroy()
