"""Unit tests for ArcadeSSEClient and TaskArcadeSSE.

Reference: ts-wallet-toolbox/src/services/providers/ArcSSEClient.ts
Reference: ts-wallet-toolbox/src/monitor/tasks/TaskArcSSE.ts
"""

import time
from unittest.mock import MagicMock, patch

from bsv_wallet_toolbox.monitor.tasks.task_arcade_sse import TaskArcadeSSE
from bsv_wallet_toolbox.services.providers.arcade_sse import ArcadeSSEClient

TXID = "8e60c4143879918ed03b8fc67b5ac33b8187daa3b46022ee2a9e1eb67e2e46ec"
ARCADE_URL = "https://arcade-v2-us-1.bsvblockchain.tech"


def _stream_response(lines: list[str], status_code: int = 200) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.iter_lines.return_value = iter(lines)
    return response


def _run_client(lines: list[str], **kwargs) -> tuple[list[dict], ArcadeSSEClient, MagicMock]:
    """Run the client over a canned SSE stream until the reader thread ends."""
    events: list[dict] = []
    client = ArcadeSSEClient(
        base_url=ARCADE_URL,
        callback_token="tok",
        on_event=events.append,
        **kwargs,
    )
    mock = _stream_response(lines)
    with patch("bsv_wallet_toolbox.services.providers.arcade_sse.requests.get", return_value=mock) as get:
        client.connect()
        deadline = time.time() + 5
        while client.connected and time.time() < deadline:
            time.sleep(0.01)
    return events, client, get


class TestArcadeSSEClient:
    def test_dispatches_status_events(self) -> None:
        lines = [
            "id: 1700000000000000001",
            "event: status",
            f'data: {{"txid": "{TXID}", "txStatus": "MINED", "timestamp": "2026-07-21T00:00:00Z"}}',
            "",
        ]
        events, client, get = _run_client(lines)

        assert len(events) == 1
        assert events[0]["txid"] == TXID
        assert events[0]["txStatus"] == "MINED"
        assert client.last_event_id == "1700000000000000001"
        # URL; a first connect sends no Last-Event-ID (Arcade then replays only non-terminal statuses)
        assert get.call_args[0][0] == f"{ARCADE_URL}/events?callbackToken=tok"
        assert "Last-Event-ID" not in get.call_args[1]["headers"]

    def test_ignores_keepalives_and_non_status_events(self) -> None:
        lines = [
            ": keepalive",
            "id: 1",
            "event: other",
            'data: {"txid": "x"}',
            "",
            "event: status",
            "data: not-json",
            "",
        ]
        events, _client, _get = _run_client(lines)
        assert events == []

    def test_last_event_id_persistence_callback(self) -> None:
        saved: list[str] = []
        lines = [
            "id: 42",
            "event: status",
            f'data: {{"txid": "{TXID}", "txStatus": "RECEIVED", "timestamp": "t"}}',
            "",
        ]
        _events, _client, _get = _run_client(lines, on_last_event_id_changed=saved.append)
        assert saved == ["42"]

    def test_initial_last_event_id_sent_for_catchup(self) -> None:
        """Resume 1ns before the last id: events sharing that timestamp are replayed too."""
        _events, _client, get = _run_client([], last_event_id="99")
        assert get.call_args[1]["headers"]["Last-Event-ID"] == "98"

    def test_non_numeric_last_event_id_sent_as_is(self) -> None:
        _events, _client, get = _run_client([], last_event_id="abc")
        assert get.call_args[1]["headers"]["Last-Event-ID"] == "abc"

    def test_api_key_header(self) -> None:
        _events, _client, get = _run_client([], api_key="key1")
        assert get.call_args[1]["headers"]["Authorization"] == "Bearer key1"

    def test_stream_end_reports_error(self) -> None:
        errors: list[Exception] = []
        _events, _client, _get = _run_client([], on_error=errors.append)
        assert len(errors) == 1

    def test_connect_failure_reports_error(self) -> None:
        errors: list[Exception] = []
        client = ArcadeSSEClient(
            base_url=ARCADE_URL,
            callback_token="tok",
            on_event=lambda e: None,
            on_error=errors.append,
        )
        with patch(
            "bsv_wallet_toolbox.services.providers.arcade_sse.requests.get",
            return_value=_stream_response([], status_code=503),
        ):
            client.connect()
            deadline = time.time() + 5
            while client.connected and time.time() < deadline:
                time.sleep(0.01)
        assert len(errors) == 1
        assert "503" in str(errors[0])

    def test_connection_error_redacts_callback_token(self) -> None:
        """requests errors quote the URL; the callback token must not reach on_error."""
        errors: list[Exception] = []
        client = ArcadeSSEClient(
            base_url=ARCADE_URL,
            callback_token="SECRET token",
            on_event=lambda e: None,
            on_error=errors.append,
        )
        exc = ConnectionError("Max retries exceeded with url: /events?callbackToken=SECRET%20token (SECRET token)")
        with patch("bsv_wallet_toolbox.services.providers.arcade_sse.requests.get", side_effect=exc):
            client.connect()
            deadline = time.time() + 5
            while client.connected and time.time() < deadline:
                time.sleep(0.01)
        assert len(errors) == 1
        assert "SECRET" not in str(errors[0])
        assert "<redacted>" in str(errors[0])


def _make_monitor(options: dict | None = None) -> MagicMock:
    monitor = MagicMock()
    monitor.services.options = options or {}
    monitor._tasks = []
    return monitor


def _make_task(options: dict | None = None) -> tuple[TaskArcadeSSE, MagicMock]:
    monitor = _make_monitor(options)
    task = TaskArcadeSSE(monitor)
    return task, monitor


class TestTaskArcadeSSESetup:
    def test_disabled_without_arcade_url(self) -> None:
        task, _monitor = _make_task({})
        task.setup()
        assert task.sse_client is None

    def test_disabled_without_callback_token(self) -> None:
        task, _monitor = _make_task({"arcadeUrl": ARCADE_URL})
        task.setup()
        assert task.sse_client is None

    def test_setup_creates_and_connects_client(self) -> None:
        task, _monitor = _make_task({"arcadeUrl": ARCADE_URL, "arcadeCallbackToken": "tok", "arcadeApiKey": "key1"})
        with patch("bsv_wallet_toolbox.monitor.tasks.task_arcade_sse.ArcadeSSEClient") as client_cls:
            task.setup()

        assert task.sse_client is not None
        kwargs = client_cls.call_args[1]
        assert kwargs["base_url"] == ARCADE_URL
        assert kwargs["callback_token"] == "tok"
        assert kwargs["api_key"] == "key1"
        client_cls.return_value.connect.assert_called_once()

    def test_setup_attempted_only_once(self) -> None:
        task, _monitor = _make_task({})
        task.trigger(0)
        task.trigger(0)
        assert task._setup_attempted is True
        assert task.sse_client is None


class TestTaskArcadeSSEProcessing:
    def _task_with_req(
        self, req: dict, options: dict | None = None, transaction_ids: list[int] | None = None
    ) -> tuple[TaskArcadeSSE, MagicMock]:
        task, monitor = _make_task(options or {})
        monitor.storage.find_proven_tx_reqs.return_value = [req]
        monitor.storage.find_transactions.return_value = [{"transactionId": i} for i in transaction_ids or []]
        return task, monitor

    def test_trigger_runs_only_with_pending_events(self) -> None:
        task, _monitor = _make_task({})
        assert task.trigger(0)["run"] is False
        task._on_event({"txid": TXID, "txStatus": "MINED"})
        assert task.trigger(0)["run"] is True

    def test_seen_on_network_marks_unmined(self) -> None:
        req = {"provenTxReqId": 7, "txid": TXID, "status": "sending", "notify": {}}
        task, monitor = self._task_with_req(req, transaction_ids=[1, 2])
        task._on_event({"txid": TXID, "txStatus": "SEEN_ON_NETWORK"})

        log = task.run_task()

        monitor.storage.update_proven_tx_req.assert_called_once_with(7, {"status": "unmined"})
        # Transactions are resolved by txid: storage never populates notify.transactionIds
        monitor.storage.find_transactions.assert_called_once_with({"partial": {"txid": TXID}})
        monitor.storage.update_transactions_status.assert_called_once_with([1, 2], "unproven")
        assert "req 7 => unmined" in log

    def test_mined_flags_check_for_proofs(self) -> None:
        req = {"provenTxReqId": 7, "status": "unmined", "notify": {}}
        task, monitor = self._task_with_req(req)
        proofs_task = MagicMock()
        proofs_task.name = "CheckForProofs"
        proofs_task.check_now = False
        monitor._tasks = [proofs_task]
        task._on_event({"txid": TXID, "txStatus": "MINED"})

        log = task.run_task()

        assert proofs_task.check_now is True
        assert "proof check requested" in log

    def test_double_spend_marks_failed(self) -> None:
        req = {"provenTxReqId": 7, "txid": TXID, "status": "unmined", "notify": {}}
        task, monitor = self._task_with_req(req, transaction_ids=[3])
        task._on_event({"txid": TXID, "txStatus": "DOUBLE_SPEND_ATTEMPTED"})

        log = task.run_task()

        monitor.storage.update_proven_tx_req.assert_called_once_with(7, {"status": "doubleSpend"})
        # update_transactions_status releases the inputs of transactions marked failed
        monitor.storage.update_transactions_status.assert_called_once_with([3], "failed")
        assert "req 7 => doubleSpend" in log

    def test_rejected_marks_invalid(self) -> None:
        req = {"provenTxReqId": 7, "txid": TXID, "status": "unsent", "notify": {}}
        task, monitor = self._task_with_req(req, transaction_ids=[4])
        task._on_event({"txid": TXID, "txStatus": "REJECTED"})

        log = task.run_task()

        monitor.storage.update_proven_tx_req.assert_called_once_with(7, {"status": "invalid"})
        monitor.storage.update_transactions_status.assert_called_once_with([4], "failed")
        assert "req 7 => invalid" in log

    def test_terminal_req_is_skipped(self) -> None:
        req = {"provenTxReqId": 7, "status": "completed", "notify": {}}
        task, monitor = self._task_with_req(req)
        task._on_event({"txid": TXID, "txStatus": "SEEN_ON_NETWORK"})

        log = task.run_task()

        monitor.storage.update_proven_tx_req.assert_not_called()
        assert "already terminal" in log

    def test_no_matching_req(self) -> None:
        task, monitor = _make_task({})
        monitor.storage.find_proven_tx_reqs.return_value = []
        task._on_event({"txid": TXID, "txStatus": "MINED"})

        log = task.run_task()

        assert "No matching ProvenTxReq" in log

    def test_event_failure_does_not_drop_remaining_events(self) -> None:
        task, monitor = _make_task({})
        monitor.storage.find_proven_tx_reqs.side_effect = [RuntimeError("database is locked"), []]
        task._on_event({"txid": "a" * 64, "txStatus": "MINED"})
        task._on_event({"txid": TXID, "txStatus": "MINED"})

        log = task.run_task()

        assert "failed to process" in log and "database is locked" in log
        assert f"SSE: txid={TXID} status=MINED" in log
        assert monitor.storage.find_proven_tx_reqs.call_count == 2

    def test_events_drained_after_run(self) -> None:
        task, monitor = _make_task({})
        monitor.storage.find_proven_tx_reqs.return_value = []
        task._on_event({"txid": TXID, "txStatus": "MINED"})
        task.run_task()
        assert task.trigger(0)["run"] is False
