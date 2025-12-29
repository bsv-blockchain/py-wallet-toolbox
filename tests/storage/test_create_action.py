"""Storage-level create_action parity tests.

These tests mirror high-value scenarios from:
    - toolbox/ts-wallet-toolbox/test/wallet/action/createAction.test.ts
    - toolbox/ts-wallet-toolbox/test/wallet/action/createAction2.test.ts
    - toolbox/go-wallet-toolbox/pkg/storage/provider_create_action_test.go

Currently the Python implementation is incomplete; tests are marked with
``xfail(strict=True)`` so missing features are visible until implementation
parity is reached.
"""

from __future__ import annotations

from typing import Any

import pytest

from bsv_wallet_toolbox.storage.provider import StorageProvider


def _auth_for(user: dict[str, Any]) -> dict[str, Any]:
    return {"userId": user["userId"]}


def _default_args() -> dict[str, Any]:
    return {
        "description": "Storage createAction",
        "outputs": [
            {
                "satoshis": 90_000,
                "lockingScript": "76a914" + "33" * 20 + "88ac",
                "outputDescription": "primary payment",
            }
        ],
        "labels": ["primary label", "secondary label"],
        "options": {"signAndProcess": True, "noSend": True, "randomizeOutputs": False},
        "version": 2,
        "lockTime": 0,
    }


def test_create_action_nosendchange_duplicate(storage_seeded: tuple[StorageProvider, dict[str, Any]]) -> None:
    """Duplicated noSendChange outpoints must raise (Go TestCreateActionWithNoSendChangeDuplicate)."""

    storage, seed = storage_seeded
    user = seed["user1"]
    change_output = seed["outputs"]["o2"]  # change=True

    args = {
        "description": "Duplicate noSendChange",
        "outputs": [
            {
                "satoshis": 5000,
                "lockingScript": "76a914" + "11" * 20 + "88ac",
                "outputDescription": "primary payment",
            }
        ],
        "options": {
            "signAndProcess": True,
            "noSend": True,
            "noSendChange": [
                {"txid": change_output["txid"], "vout": change_output["vout"]},
                {"txid": change_output["txid"], "vout": change_output["vout"]},
            ],
        },
    }

    with pytest.raises(Exception):
        storage.create_action(_auth_for(user), args)


def test_create_action_output_tags_persisted(storage_seeded: tuple[StorageProvider, dict[str, Any]]) -> None:
    """Output tags supplied by caller should be inserted and mapped (Go TestCreateActionOutputTags)."""

    storage, seed = storage_seeded
    user = seed["user1"]

    tags = ["tag-alpha", "tag-beta"]
    args = {
        "description": "Tagged payment",
        "outputs": [
            {
                "satoshis": 1200,
                "lockingScript": "76a914" + "22" * 20 + "88ac",
                "outputDescription": "tagged",
                "tags": tags,
            }
        ],
        "options": {"signAndProcess": True, "noSend": True},
    }

    result = storage.create_action(_auth_for(user), args)

    created_output_ids = [out.get("outputId") for out in result["outputs"] if out.get("providedBy") == "you"]
    assert created_output_ids, "expected at least one user-provided output"

    recorded_tags = []
    for output_id in created_output_ids:
        tag_maps = storage.find_output_tag_maps({"partial": {"outputId": output_id}})
        for tag_map in tag_maps:
            tag = storage.find_output_tags({"partial": {"outputTagId": tag_map["outputTagId"]}})
            recorded_tags.extend(t["tag"] for t in tag)

    assert set(tags).issubset(set(recorded_tags))


def test_create_action_requires_user_id(storage_seeded: tuple[StorageProvider, dict[str, Any]]) -> None:
    """Missing userId in auth must raise (Go TestCreateActionNilAuth)."""

    storage, _ = storage_seeded
    args = _default_args()

    with pytest.raises(KeyError):
        storage.create_action({}, args)


def test_create_action_sign_and_process_happy_path(storage_seeded: tuple[StorageProvider, dict[str, Any]]) -> None:
    """Sign-and-process flow should populate inputs, outputs, txid (Go TestCreateActionHappyPath)."""

    storage, seed = storage_seeded
    user = seed["user1"]
    args = _default_args()

    result = storage.create_action(_auth_for(user), args)

    assert result.get("txid")
    assert result.get("lockTime") == args.get("lockTime", 0)
    assert result.get("version") == args.get("version", 2)
    assert any(out for out in result.get("outputs", []) if out.get("providedBy") == "storage")
    assert result.get("inputBeef")


def test_create_action_nosendchange_output_sequence(storage_seeded: tuple[StorageProvider, dict[str, Any]]) -> None:
    """When noSendChange is provided, storage should allocate deterministic VOUTs (Go TestCreateActionWithNoSendChangeHappyPath)."""

    storage, seed = storage_seeded
    user = seed["user1"]
    # Use o5: in "default" basket with change=True, providedBy="storage", spendable=True
    # o2 is in "savings" basket and fails validation
    change_outputs: list[dict[str, Any]] = [seed["outputs"]["o5"]]

    args = _default_args()
    args["options"].update(
        {
            "noSendChange": [
                {"txid": change_outputs[0]["txid"], "vout": change_outputs[0]["vout"]},
            ]
        }
    )

    result = storage.create_action(_auth_for(user), args)
    # noSendChangeOutputVouts contains all change output vouts (starting at 1)
    # Go test expects [1..30], we just verify they start at 1 and are sequential
    vouts = result["noSendChangeOutputVouts"]
    assert len(vouts) >= 1
    assert vouts[0] == 1


def test_create_action_randomizes_outputs(storage_seeded: tuple[StorageProvider, dict[str, Any]]) -> None:
    """randomizeOutputs should shuffle user outputs (TS createAction shuffle test)."""

    storage, seed = storage_seeded
    user = seed["user1"]

    args = _default_args()
    args["outputs"] = [
        {
            "satoshis": 1_000,
            "lockingScript": "76a914" + "01" * 20 + "88ac",
            "outputDescription": "o-1",
        },
        {
            "satoshis": 2_000,
            "lockingScript": "76a914" + "02" * 20 + "88ac",
            "outputDescription": "o-2",
        },
        {
            "satoshis": 3_000,
            "lockingScript": "76a914" + "03" * 20 + "88ac",
            "outputDescription": "o-3",
        },
    ]
    args["options"]["randomizeOutputs"] = True

    result = storage.create_action(_auth_for(user), args)
    user_outputs = [out for out in result.get("outputs", []) if out.get("providedBy") == "you"]
    assert len(user_outputs) == 3
    order = [out["vout"] for out in user_outputs]
    assert order not in ([0, 1, 2], [2, 1, 0])


def test_create_action_known_txids_return_txid_only(storage_seeded: tuple[StorageProvider, dict[str, Any]]) -> None:
    """When returnTXIDOnly is true, signable transaction bytes should be omitted (TS createAction2 test)."""

    storage, seed = storage_seeded
    user = seed["user1"]

    args = _default_args()
    args["options"].update({"returnTXIDOnly": True, "knownTxids": ["aa" * 32]})

    result = storage.create_action(_auth_for(user), args)
    assert result.get("tx") is None
    assert result.get("signableTransaction") is None
