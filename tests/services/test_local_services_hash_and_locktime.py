"""Local WalletServices methods tests: hashOutputScript and nLockTimeIsFinal.

Reference: toolbox/ts-wallet-toolbox/src/services/Services.ts
Reference: go-wallet-toolbox/pkg/internal/txutils/script_hash.go
Reference: go-wallet-toolbox/pkg/wdk/locktime.go
"""

from time import time

import pytest
from bsv.transaction import Transaction
from bsv.transaction_input import TransactionInput

from bsv_wallet_toolbox.services.services import Services


class TestHashOutputScript:
    def test_hash_output_script_matches_expected(self) -> None:
        # Given
        services = Services("main")
        script_hex = "76a91489abcdefabbaabbaabbaabbaabbaabbaabbaabba88ac"
        expected_le = (
            "db46d31e84e16e7fb031b3ab375131a7bb65775c0818dc17fe0d4444efb3d0aa"
        )

        # When
        result = services.hash_output_script(script_hex)

        # Then
        assert result == expected_le


class TestNLockTimeIsFinal:
    def test_final_when_all_sequences_are_maxint(self) -> None:
        # Given: a transaction with all input sequences = 0xFFFFFFFF
        tx = Transaction()
        tx.inputs.append(
            TransactionInput(
                source_txid="00" * 32,
                source_output_index=0,
                sequence=0xFFFFFFFF,
            )
        )
        services = Services("main")

        # When
        result = services.n_lock_time_is_final(tx)

        # Then
        assert result is True

    def test_height_based_locktime_strict_less_than(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Given: height branch (nLockTime < 500_000_000), strict < comparison
        services = Services("main")

        async def fake_get_height() -> int:
            return 800_000

        monkeypatch.setattr(services, "get_height", fake_get_height)

        # When / Then
        assert services.n_lock_time_is_final(799_999) is True
        assert services.n_lock_time_is_final(800_000) is False

    def test_timestamp_based_locktime_strict_less_than(self) -> None:
        # Given: timestamp branch (nLockTime >= 500_000_000), strict < comparison
        services = Services("main")
        now = int(time())

        # When / Then
        assert services.n_lock_time_is_final(now - 10) is True
        assert services.n_lock_time_is_final(now + 3600) is False


