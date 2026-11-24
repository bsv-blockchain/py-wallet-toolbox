"""The deprecated Arcade names keep working after the rename to BSV Broadcaster."""

import warnings
from unittest.mock import MagicMock, patch

import pytest

from bsv_wallet_toolbox.monitor import tasks
from bsv_wallet_toolbox.monitor.tasks import task_arcade_sse, task_bsv_broadcaster_sse
from bsv_wallet_toolbox.services.providers import arcade, arcade_sse, bsv_broadcaster, bsv_broadcaster_sse
from bsv_wallet_toolbox.services.services import Services

TXID = "8e60c4143879918ed03b8fc67b5ac33b8187daa3b46022ee2a9e1eb67e2e46ec"
BROADCASTER_URL = "https://arcade-v2-us-1.bsvblockchain.tech"


def _sse_client_kwargs() -> dict:
    return {"base_url": BROADCASTER_URL, "callback_token": "tok", "on_event": lambda event: None}


def _monitor() -> MagicMock:
    monitor = MagicMock()
    monitor.services.options = {}
    return monitor


def test_arcade_warns_and_is_a_bsv_broadcaster() -> None:
    with pytest.warns(DeprecationWarning, match="Use BsvBroadcaster"):
        instance = arcade.Arcade(BROADCASTER_URL, "my_api_key")
    assert isinstance(instance, bsv_broadcaster.BsvBroadcaster)
    assert instance.url == BROADCASTER_URL
    assert instance.name == "arcade"
    assert instance.request_headers()["Authorization"] == "Bearer my_api_key"


def test_arcade_behaves_like_bsv_broadcaster() -> None:
    response = MagicMock(status_code=202, text="")
    response.json.return_value = {"txid": TXID, "status": 202, "txStatus": "RECEIVED"}
    with pytest.warns(DeprecationWarning):
        legacy = arcade.Arcade(BROADCASTER_URL)
    with patch("bsv_wallet_toolbox.services.providers.bsv_broadcaster.requests.post", return_value=response) as post:
        result = legacy.post_raw_tx("aabbcc", [TXID])
    assert result.status == "success"
    assert post.call_args[0][0] == f"{BROADCASTER_URL}/tx"


def test_arcade_sse_client_warns_and_is_a_bsv_broadcaster_sse_client() -> None:
    with pytest.warns(DeprecationWarning, match="Use BsvBroadcasterSSEClient"):
        client = arcade_sse.ArcadeSSEClient(**_sse_client_kwargs())
    assert isinstance(client, bsv_broadcaster_sse.BsvBroadcasterSSEClient)
    assert not client.connected


def test_task_arcade_sse_warns_and_is_a_task_bsv_broadcaster_sse() -> None:
    with pytest.warns(DeprecationWarning, match="Use TaskBsvBroadcasterSSE"):
        task = task_arcade_sse.TaskArcadeSSE(_monitor())
    assert isinstance(task, task_bsv_broadcaster_sse.TaskBsvBroadcasterSSE)
    assert task.name == "ArcadeSSE"


@pytest.mark.parametrize(
    "construct",
    [
        lambda: arcade.Arcade(BROADCASTER_URL),
        lambda: arcade_sse.ArcadeSSEClient(**_sse_client_kwargs()),
        lambda: task_arcade_sse.TaskArcadeSSE(_monitor()),
    ],
    ids=["Arcade", "ArcadeSSEClient", "TaskArcadeSSE"],
)
def test_alias_warning_points_at_caller(construct) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        construct()
    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert len(deprecations) == 1
    assert deprecations[0].filename == __file__


def test_new_names_do_not_warn() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        bsv_broadcaster.BsvBroadcaster(BROADCASTER_URL)
        bsv_broadcaster_sse.BsvBroadcasterSSEClient(**_sse_client_kwargs())
        task_bsv_broadcaster_sse.TaskBsvBroadcasterSSE(_monitor())
        services = Services({"chain": "main", "arcadeUrl": BROADCASTER_URL})
        assert services.bsv_broadcaster is not None


def test_services_arcade_attribute_is_a_deprecated_alias() -> None:
    services = Services({"chain": "main", "arcadeUrl": BROADCASTER_URL})
    with pytest.warns(DeprecationWarning, match=r"Use Services\.bsv_broadcaster"):
        assert services.arcade is services.bsv_broadcaster

    replacement = bsv_broadcaster.BsvBroadcaster(BROADCASTER_URL)
    with pytest.warns(DeprecationWarning, match=r"Use Services\.bsv_broadcaster"):
        services.arcade = replacement
    assert services.bsv_broadcaster is replacement


def test_legacy_names_alias_new_ones() -> None:
    assert arcade.ARCADE_TERMINAL_TX_STATUSES is bsv_broadcaster.BSV_BROADCASTER_TERMINAL_TX_STATUSES
    assert arcade.ARCADE_VALIDATION_FAILED_ERROR is bsv_broadcaster.BSV_BROADCASTER_VALIDATION_FAILED_ERROR
    assert arcade.ARCADE_MINED_TX_STATUSES is bsv_broadcaster.BSV_BROADCASTER_MINED_TX_STATUSES
    assert arcade.is_fee_policy_rejection is bsv_broadcaster.is_fee_policy_rejection
    assert task_arcade_sse.MAX_EVENT_ATTEMPTS == task_bsv_broadcaster_sse.MAX_EVENT_ATTEMPTS
    assert task_arcade_sse.PROVEN_TX_REQ_TERMINAL_STATUSES is task_bsv_broadcaster_sse.PROVEN_TX_REQ_TERMINAL_STATUSES


def test_monitor_tasks_package_exports_both_names() -> None:
    assert tasks.TaskBsvBroadcasterSSE is task_bsv_broadcaster_sse.TaskBsvBroadcasterSSE
    assert tasks.TaskArcadeSSE is task_arcade_sse.TaskArcadeSSE
