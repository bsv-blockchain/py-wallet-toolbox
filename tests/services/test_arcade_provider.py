"""Unit tests for the Arcade provider.

Reference: ts-wallet-toolbox/src/services/providers/__tests/Arcade.test.ts
Reference: ts-wallet-toolbox/src/services/__tests/Services.arcade.test.ts
"""

from unittest.mock import MagicMock, patch

from bsv_wallet_toolbox.services.providers.arc import ArcConfig
from bsv_wallet_toolbox.services.providers.arcade import Arcade
from bsv_wallet_toolbox.services.services import Services, create_default_options

TXID = "8e60c4143879918ed03b8fc67b5ac33b8187daa3b46022ee2a9e1eb67e2e46ec"
ARCADE_URL = "https://arcade-v2-us-1.bsvblockchain.tech"


def _mock_response(status_code: int, json_data: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data
    response.text = ""
    return response


class TestArcadePostRawTx:
    def test_success_202_received(self) -> None:
        """Arcade's 202 submit response: {"txid", "status": 202, "txStatus": "RECEIVED"}."""
        arcade = Arcade(ARCADE_URL)
        mock = _mock_response(202, {"txid": TXID, "status": 202, "txStatus": "RECEIVED"})

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post", return_value=mock) as post:
            result = arcade.post_raw_tx("aabbcc", [TXID])

        assert result.status == "success"
        assert result.txid == TXID
        assert result.data == "RECEIVED"
        # Endpoint must be root-level /tx (no /v1 prefix)
        assert post.call_args[0][0] == f"{ARCADE_URL}/tx"
        assert post.call_args[1]["json"] == {"rawTx": "aabbcc"}

    def test_duplicate_submit_rejected_is_error(self) -> None:
        """202 with terminal txStatus (re-submit of a rejected tx) must be an error."""
        arcade = Arcade(ARCADE_URL)
        mock = _mock_response(202, {"txid": TXID, "status": 202, "txStatus": "REJECTED"})

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post", return_value=mock):
            result = arcade.post_raw_tx("aabbcc", [TXID])

        assert result.status == "error"
        assert result.double_spend is False

    def test_double_spend_attempted_is_terminal(self) -> None:
        """DOUBLE_SPEND_ATTEMPTED is terminal in Arcade (unlike ARC)."""
        arcade = Arcade(ARCADE_URL)
        mock = _mock_response(
            202,
            {"txid": TXID, "status": 202, "txStatus": "DOUBLE_SPEND_ATTEMPTED", "competingTxs": ["dead"]},
        )

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post", return_value=mock):
            result = arcade.post_raw_tx("aabbcc", [TXID])

        assert result.status == "error"
        assert result.double_spend is True
        assert result.competing_txs == ["dead"]

    def test_400_is_terminal_not_service_error(self) -> None:
        """400 means the tx itself is invalid — retrying elsewhere won't help."""
        arcade = Arcade(ARCADE_URL)
        mock = _mock_response(400, {"error": "transaction failed validation", "reason": "missing inputs"})

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post", return_value=mock):
            result = arcade.post_raw_tx("aabbcc", [TXID])

        assert result.status == "error"
        assert result.service_error is False
        assert result.data.detail == "transaction failed validation: missing inputs"

    def test_503_is_service_error(self) -> None:
        arcade = Arcade(ARCADE_URL)
        mock = _mock_response(503, {"error": "service overloaded, retry shortly"})

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post", return_value=mock):
            result = arcade.post_raw_tx("aabbcc", [TXID])

        assert result.status == "error"
        assert result.service_error is True

    def test_429_is_rate_limited(self) -> None:
        arcade = Arcade(ARCADE_URL)
        mock = _mock_response(429, {"error": "too many requests"})

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post", return_value=mock):
            result = arcade.post_raw_tx("aabbcc", [TXID])

        assert result.status == "rate_limited"
        assert result.service_error is True

    def test_network_exception_is_service_error(self) -> None:
        arcade = Arcade(ARCADE_URL)

        with patch(
            "bsv_wallet_toolbox.services.providers.arcade.requests.post",
            side_effect=ConnectionError("refused"),
        ):
            result = arcade.post_raw_tx("aabbcc", [TXID])

        assert result.status == "error"
        assert result.service_error is True


class TestArcadePostBeef:
    def test_posts_ef_for_each_txid(self) -> None:
        tx_obj = MagicMock()
        tx_obj.to_ef.return_value = bytes.fromhex("00ef")
        btx = MagicMock(tx_obj=tx_obj)
        beef = MagicMock()
        beef.find_transaction_for_signing.return_value = btx

        arcade = Arcade(ARCADE_URL)
        mock = _mock_response(202, {"txid": TXID, "status": 202, "txStatus": "RECEIVED"})

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post", return_value=mock) as post:
            result = arcade.post_beef(beef, [TXID])

        assert result.status == "success"
        assert len(result.txid_results) == 1
        assert post.call_args[1]["json"] == {"rawTx": "00ef"}

    def test_ef_build_failure_is_service_error(self) -> None:
        """BEEF without source data (txidOnly parents) can't build EF — fall through."""
        beef = MagicMock()
        beef.find_transaction_for_signing.return_value = None

        arcade = Arcade(ARCADE_URL)

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post") as post:
            result = arcade.post_beef(beef, [TXID])

        assert result.status == "error"
        assert result.txid_results[0].service_error is True
        post.assert_not_called()


class TestArcadeGetMerklePath:
    def test_not_mined_returns_no_proof(self) -> None:
        arcade = Arcade(ARCADE_URL)
        mock = _mock_response(200, {"txid": TXID, "txStatus": "SEEN_ON_NETWORK"})

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.get", return_value=mock) as get:
            result = arcade.get_merkle_path(TXID, services=MagicMock())

        assert "merklePath" not in result
        # Endpoint must be root-level /tx/{txid} (no /v1 prefix)
        assert get.call_args[0][0] == f"{ARCADE_URL}/tx/{TXID}"


class TestArcadeConfigHandling:
    def test_api_key_string_config(self) -> None:
        arcade = Arcade(ARCADE_URL, "my_api_key")
        assert arcade.request_headers()["Authorization"] == "Bearer my_api_key"

    def test_callback_headers(self) -> None:
        config = ArcConfig(callback_url="https://example.com/cb", callback_token="tok123")
        arcade = Arcade(ARCADE_URL, config)
        headers = arcade.request_headers()
        assert headers["X-CallbackUrl"] == "https://example.com/cb"
        assert headers["X-CallbackToken"] == "tok123"

    def test_default_name(self) -> None:
        assert Arcade(ARCADE_URL).name == "arcade"


class TestServicesArcadeRegistration:
    def test_no_arcade_url_no_arcade_provider(self) -> None:
        """Back-compat: no arcadeUrl -> no Arcade provider, collections unchanged."""
        services = Services({"chain": "test"})

        assert services.arcade is None
        names = [entry["name"] for entry in services.post_beef_services.services]
        assert "arcade" not in names

    def test_arcade_url_registers_arcade_first(self) -> None:
        """arcadeUrl provided -> Arcade registered FIRST in post_beef_services."""
        services = Services(
            {
                "chain": "test",
                "arcadeUrl": ARCADE_URL,
                "arcUrl": "https://arc-test.taal.com",
            }
        )

        assert services.arcade is not None
        post_beef_names = [entry["name"] for entry in services.post_beef_services.services]
        assert post_beef_names[0] == "arcade"
        merkle_path_names = [entry["name"] for entry in services.get_merkle_path_services.services]
        assert merkle_path_names[0] == "arcade"

    def test_arcade_callback_options_wired(self) -> None:
        services = Services(
            {
                "chain": "test",
                "arcadeUrl": ARCADE_URL,
                "arcadeApiKey": "key1",
                "arcadeCallbackUrl": "https://example.com/cb",
                "arcadeCallbackToken": "tok",
            }
        )

        assert services.arcade.api_key == "key1"
        assert services.arcade.callback_url == "https://example.com/cb"
        assert services.arcade.callback_token == "tok"

    def test_default_options_have_no_arcade_url(self) -> None:
        """Arcade is opt-in: default options never set arcadeUrl."""
        assert create_default_options("main").get("arcadeUrl") is None
        assert create_default_options("test").get("arcadeUrl") is None
