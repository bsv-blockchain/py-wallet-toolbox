from bsv_wallet_toolbox.manager.wallet_permissions_manager import WalletPermissionsManager


def _make_manager(config: dict[str, bool]) -> WalletPermissionsManager:
    manager: WalletPermissionsManager = object.__new__(WalletPermissionsManager)  # type: ignore[assignment]
    manager._admin_originator = "admin"  # type: ignore[attr-defined]
    manager._config = config  # type: ignore[attr-defined]
    return manager


def test_identity_permissions_counterparty_linkage_calls_protocol_check() -> None:
    calls: list[tuple[str, list, str]] = []

    manager = _make_manager({"seekPermissionsForKeyLinkageRevelation": True})

    def fake_check(originator: str, protocol_id: list, operation: str) -> None:
        calls.append((originator, protocol_id, operation))

    manager._check_protocol_permissions = fake_check  # type: ignore[attr-defined]

    manager._check_identity_permissions(  # type: ignore[attr-defined]
        "example.com",
        "linkage_reveal",
        {"linkage_type": "counterparty", "counterparty": "peer.example"},
    )

    assert calls == [("example.com", [2, "counterparty key linkage revelation peer.example"], "linkageRevelation")]


def test_identity_permissions_specific_linkage_uses_protocol_metadata() -> None:
    calls: list[tuple[str, list, str]] = []
    manager = _make_manager({"seekPermissionsForKeyLinkageRevelation": True})

    def fake_check(originator: str, protocol_id: list, operation: str) -> None:
        calls.append((originator, protocol_id, operation))

    manager._check_protocol_permissions = fake_check  # type: ignore[attr-defined]

    manager._check_identity_permissions(  # type: ignore[attr-defined]
        "origin.example",
        "linkage_reveal",
        {
            "linkage_type": "specific",
            "protocol_id": [2, "protocol name"],
            "key_id": "key-42",
        },
    )

    assert calls == [
        ("origin.example", [2, "specific key linkage revelation protocol name key-42"], "linkageRevelation")
    ]


def test_identity_permissions_resolution_skips_when_disabled() -> None:
    calls: list[tuple[str, list, str]] = []
    manager = _make_manager({"seekPermissionsForIdentityResolution": False})

    def fake_check(originator: str, protocol_id: list, operation: str) -> None:
        calls.append((originator, protocol_id, operation))

    manager._check_protocol_permissions = fake_check  # type: ignore[attr-defined]

    manager._check_identity_permissions("client.example", "resolve")  # type: ignore[attr-defined]

    assert calls == []
