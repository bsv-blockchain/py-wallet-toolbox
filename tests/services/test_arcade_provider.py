"""Unit tests for the Arcade provider.

Reference: ts-wallet-toolbox/src/services/providers/__tests/Arcade.test.ts
Reference: ts-wallet-toolbox/src/services/__tests/Services.arcade.test.ts
"""

from unittest.mock import MagicMock, patch

from bsv import P2PKH, PrivateKey, Transaction, TransactionInput, TransactionOutput
from bsv.merkle_path import MerklePath
from bsv.transaction.beef import BEEF_V2, Beef

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


def _signed_tx() -> Transaction:
    """A signed tx whose input is linked to its source tx, so EF can be built."""
    key = PrivateKey()
    source = Transaction()
    source.add_output(TransactionOutput(P2PKH().lock(key.address()), 1000))
    tx = Transaction()
    tx.add_input(
        TransactionInput(
            source_transaction=source, source_output_index=0, unlocking_script_template=P2PKH().unlock(key)
        )
    )
    tx.add_output(TransactionOutput(P2PKH().lock(key.address()), 900))
    tx.sign()
    return tx


def _atomic_beef_hex(tx: Transaction) -> str:
    beef = Beef(version=BEEF_V2)
    for tx_input in tx.inputs:
        beef.merge_transaction(tx_input.source_transaction)
    beef.merge_transaction(tx)
    return beef.to_binary_atomic(tx.txid()).hex()


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

    def test_400_request_error_is_service_error(self) -> None:
        """A 400 that is not a tx validation failure (e.g. bad callback URL) must fall through."""
        arcade = Arcade(ARCADE_URL)
        mock = _mock_response(400, {"error": "invalid callback url: private address not allowed"})

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post", return_value=mock):
            result = arcade.post_raw_tx("aabbcc", [TXID])

        assert result.status == "error"
        assert result.service_error is True
        assert result.data.detail == "invalid callback url: private address not allowed"

    def test_400_fee_policy_rejection_is_service_error(self) -> None:
        """Arcade's minimum fee is operator policy: another broadcaster may accept the tx."""
        arcade = Arcade(ARCADE_URL)
        mock = _mock_response(
            400,
            {"error": "transaction failed validation", "reason": "transaction fee is too low: 10 < 50 required"},
        )

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post", return_value=mock):
            result = arcade.post_raw_tx("aabbcc", [TXID])

        assert result.status == "error"
        assert result.service_error is True

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


class TestArcadeBroadcast:
    def test_posts_ef(self) -> None:
        tx = _signed_tx()
        arcade = Arcade(ARCADE_URL)
        mock = _mock_response(202, {"txid": tx.txid(), "status": 202, "txStatus": "RECEIVED"})

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post", return_value=mock) as post:
            result = arcade.broadcast(tx)

        assert result.status == "success"
        assert post.call_args[1]["json"] == {"rawTx": tx.to_ef().hex()}

    def test_no_ef_is_service_error_without_posting(self) -> None:
        """A raw tx (no source data) always fails Arcade validation — don't post it."""
        tx = Transaction.from_hex(_signed_tx().hex())
        arcade = Arcade(ARCADE_URL)

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post") as post:
            result = arcade.broadcast(tx)

        assert result.status == "error"
        assert result.service_error is True
        assert result.notes[0]["what"] == "arcadeEfBuildFailed"
        post.assert_not_called()

    def test_trailing_slash_in_url(self) -> None:
        arcade = Arcade(ARCADE_URL + "/")
        mock = _mock_response(202, {"txid": TXID, "status": 202, "txStatus": "RECEIVED"})

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post", return_value=mock) as post:
            arcade.post_raw_tx("aabbcc", [TXID])

        assert post.call_args[0][0] == f"{ARCADE_URL}/tx"


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

    def test_atomic_and_v1_beef_hex_post_ef(self) -> None:
        tx = _signed_tx()
        arcade = Arcade(ARCADE_URL)
        mock = _mock_response(202, {"txid": tx.txid(), "status": 202, "txStatus": "RECEIVED"})

        for beef_hex in (_atomic_beef_hex(tx), tx.to_beef().hex()):
            with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post", return_value=mock) as post:
                result = arcade.post_beef(beef_hex, [tx.txid()])

            assert result.status == "success"
            assert post.call_args[1]["json"] == {"rawTx": tx.to_ef().hex()}

    def test_non_beef_hex_is_service_error_without_posting(self) -> None:
        tx = _signed_tx()
        arcade = Arcade(ARCADE_URL)

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post") as post:
            result = arcade.post_beef(tx.hex(), [tx.txid()])

        assert result.status == "error"
        assert result.txid_results[0].service_error is True
        post.assert_not_called()


def _mined_response(txid: str, merkle_path: MerklePath, block_hash: str = "b" * 64) -> MagicMock:
    return _mock_response(
        200,
        {
            "txid": txid,
            "txStatus": "MINED",
            "blockHash": block_hash,
            "blockHeight": merkle_path.block_height,
            "merklePath": merkle_path.to_hex(),
        },
    )


def _two_leaf_path(txid: str) -> MerklePath:
    return MerklePath(
        870123,
        [[{"offset": 0, "hash_str": txid, "txid": True}, {"offset": 1, "hash_str": "c" * 64}]],
    )


class TestArcadeGetMerklePath:
    def test_mined_returns_verified_proof(self) -> None:
        """Arcade returns merklePath as BUMP hex; it is verified against the header root."""
        mp = _two_leaf_path(TXID)
        header = {"height": 870123, "hash": "b" * 64, "merkleRoot": mp.compute_root(TXID)}
        services = MagicMock()
        services.hash_to_header.return_value = header
        arcade = Arcade(ARCADE_URL)

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.get", return_value=_mined_response(TXID, mp)):
            result = arcade.get_merkle_path(TXID, services=services)

        services.hash_to_header.assert_called_once_with("b" * 64)
        assert result["header"] == header
        assert result["merklePath"]["blockHeight"] == 870123
        # Same dict shape the other providers return: usable by MerklePath(blockHeight, path)
        rebuilt = MerklePath(result["merklePath"]["blockHeight"], result["merklePath"]["path"])
        assert rebuilt.compute_root(TXID) == header["merkleRoot"]

    def test_root_mismatch_returns_no_proof(self) -> None:
        mp = _two_leaf_path(TXID)
        services = MagicMock()
        services.hash_to_header.return_value = {"height": 870123, "hash": "b" * 64, "merkleRoot": "0" * 64}
        arcade = Arcade(ARCADE_URL)

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.get", return_value=_mined_response(TXID, mp)):
            result = arcade.get_merkle_path(TXID, services=services)

        assert "merklePath" not in result
        assert result["notes"][-1]["what"] == "getMerklePathRootMismatch"

    def test_unknown_header_returns_no_proof(self) -> None:
        """Without a header the proof can't be verified — let the next provider try."""
        services = MagicMock()
        services.hash_to_header.side_effect = RuntimeError("header not found")
        arcade = Arcade(ARCADE_URL)

        with patch(
            "bsv_wallet_toolbox.services.providers.arcade.requests.get",
            return_value=_mined_response(TXID, _two_leaf_path(TXID)),
        ):
            result = arcade.get_merkle_path(TXID, services=services)

        assert "merklePath" not in result
        assert result["notes"][-1]["what"] == "getMerklePathNoData"

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

    def test_post_beef_array_broadcasts_with_arcade_only(self) -> None:
        """An Arcade-only configuration must broadcast, not return mocked results."""
        services = _arcade_only_services()
        tx = _signed_tx()
        mock = _mock_response(202, {"txid": tx.txid(), "status": 202, "txStatus": "RECEIVED"})

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post", return_value=mock) as post:
            results = services.post_beef_array([_atomic_beef_hex(tx)])

        assert results[0]["accepted"] is True
        assert post.call_count == 1

    def test_default_options_have_no_arcade_url(self) -> None:
        """Arcade is opt-in: default options never set arcadeUrl."""
        assert create_default_options("main").get("arcadeUrl") is None
        assert create_default_options("test").get("arcadeUrl") is None


def _arcade_only_services(**options: str) -> Services:
    services = Services({"chain": "main", "arcadeUrl": ARCADE_URL, "arcadeCallbackToken": "tok", **options})
    services.arc_taal = None
    services.arc_gorillapool = None
    services.bitails = None
    return services


class TestServicesPostBeefArcade:
    def test_arcade_is_tried_first_with_callback_token(self) -> None:
        services = _arcade_only_services()
        services.arc_taal = MagicMock()
        tx = _signed_tx()
        mock = _mock_response(202, {"txid": tx.txid(), "status": 202, "txStatus": "RECEIVED"})

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post", return_value=mock) as post:
            result = services.post_beef(_atomic_beef_hex(tx))

        assert result["accepted"] is True
        assert result["txid"] == tx.txid()
        # Only the subject tx is posted, as EF, under the wallet's callback token
        assert post.call_count == 1
        assert post.call_args[1]["json"] == {"rawTx": tx.to_ef().hex()}
        assert post.call_args[1]["headers"]["X-CallbackToken"] == "tok"
        services.arc_taal.broadcast.assert_not_called()

    def test_service_error_falls_through(self) -> None:
        services = _arcade_only_services()
        services.bitails = MagicMock()
        services.bitails.post_beef.return_value = {"accepted": True, "txid": "x", "message": "ok"}
        tx = _signed_tx()

        with patch(
            "bsv_wallet_toolbox.services.providers.arcade.requests.post",
            return_value=_mock_response(503, {"error": "service overloaded, retry shortly"}),
        ):
            result = services.post_beef(_atomic_beef_hex(tx))

        assert result["accepted"] is True
        services.bitails.post_beef.assert_called_once()

    def test_validation_failure_is_terminal(self) -> None:
        services = _arcade_only_services()
        services.bitails = MagicMock()
        tx = _signed_tx()

        with patch(
            "bsv_wallet_toolbox.services.providers.arcade.requests.post",
            return_value=_mock_response(400, {"error": "transaction failed validation", "reason": "bad script"}),
        ):
            result = services.post_beef(_atomic_beef_hex(tx))

        assert result["accepted"] is False
        assert "bad script" in result["message"]
        services.bitails.post_beef.assert_not_called()

    def test_fee_policy_rejection_falls_through(self) -> None:
        services = _arcade_only_services()
        services.bitails = MagicMock()
        services.bitails.post_beef.return_value = {"accepted": True, "txid": "x", "message": "ok"}
        tx = _signed_tx()

        with patch(
            "bsv_wallet_toolbox.services.providers.arcade.requests.post",
            return_value=_mock_response(
                400,
                {"error": "transaction failed validation", "reason": "transaction fee is too low: 10 < 50 required"},
            ),
        ):
            result = services.post_beef(_atomic_beef_hex(tx))

        assert result["accepted"] is True
        services.bitails.post_beef.assert_called_once()

    def test_double_spend_is_reported(self) -> None:
        services = _arcade_only_services()
        tx = _signed_tx()
        mock = _mock_response(
            202,
            {"txid": tx.txid(), "status": 202, "txStatus": "DOUBLE_SPEND_ATTEMPTED", "competingTxs": ["dead"]},
        )

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post", return_value=mock):
            result = services.post_beef(_atomic_beef_hex(tx))

        assert result["accepted"] is False
        assert result["doubleSpend"] is True

    def test_raw_tx_skips_arcade(self) -> None:
        """A bare raw tx cannot be encoded as EF, so Arcade is skipped without posting."""
        services = _arcade_only_services()
        services.bitails = MagicMock()
        services.bitails.post_beef.return_value = {"accepted": True, "txid": "x", "message": "ok"}

        with patch("bsv_wallet_toolbox.services.providers.arcade.requests.post") as post:
            result = services.post_beef(_signed_tx().hex())

        assert result["accepted"] is True
        post.assert_not_called()
