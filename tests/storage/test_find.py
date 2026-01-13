from datetime import UTC, datetime, timedelta


def test_find_proventx(storage_seeded) -> None:
    storage, seed = storage_seeded
    results = storage.find_proven_txs({"partial": {}})
    assert len(results) == 1
    assert results[0]["provenTxId"] == seed["provenTx"]["provenTxId"]


def test_find_proventxreq(storage_seeded) -> None:
    storage, seed = storage_seeded
    all_results = storage.find_proven_tx_reqs({"partial": {}})
    assert len(all_results) == 2

    completed = storage.find_proven_tx_reqs({"partial": {"status": "completed"}})
    assert len(completed) == 1
    assert completed[0]["provenTxReqId"] == seed["provenTxReqs"]["completed"]["provenTxReqId"]

    batched = storage.find_proven_tx_reqs({"batch": "batch-001"})
    assert len(batched) == 1


def test_find_users(storage_seeded) -> None:
    storage, seed = storage_seeded
    users = storage.find_users({"partial": {}})
    assert {u["userId"] for u in users} == {seed["user1"]["userId"], seed["user2"]["userId"]}


def test_find_certificates(storage_seeded) -> None:
    storage, seed = storage_seeded
    certs = storage.find_certificates({"partial": {}})
    assert len(certs) == 3

    certifier = seed["certificates"]["primary"]["certifier"]
    by_certifier = storage.find_certificates({"certifiers": [certifier]})
    assert len(by_certifier) == 1

    cert_type = seed["certificates"]["secondary"]["type"]
    by_type = storage.find_certificates({"types": [cert_type]})
    assert len(by_type) == 1

    missing = storage.find_certificates({"types": ["non-existent"]})
    assert not missing


def test_find_certificate_fields(storage_seeded) -> None:
    storage, seed = storage_seeded
    fields = storage.find_certificate_fields({"partial": {}})
    assert len(fields) == 3

    for_user1 = storage.find_certificate_fields({"partial": {"userId": seed["user1"]["userId"]}})
    assert len(for_user1) == 3

    for_user2 = storage.find_certificate_fields({"partial": {"userId": seed["user2"]["userId"]}})
    assert not for_user2

    name_fields = storage.find_certificate_fields({"partial": {"fieldName": "name"}})
    assert len(name_fields) == 2


def test_find_output_baskets(storage_seeded) -> None:
    storage, seed = storage_seeded
    baskets = storage.find_output_baskets({"partial": {}})
    assert len(baskets) == 3

    user1_baskets = storage.find_output_baskets({"partial": {"userId": seed["user1"]["userId"]}})
    assert len(user1_baskets) == 3

    inclusive = storage.find_output_baskets({"since": seed["sinceAnchor"]})
    assert len(inclusive) == 3

    future = storage.find_output_baskets({"since": datetime.now(UTC)})
    assert not future

    first_created = min(basket["createdAt"] for basket in baskets)
    exclusive = storage.find_output_baskets(
        {
            "partial": {"userId": seed["user1"]["userId"]},
            "since": first_created + timedelta(minutes=1),
        }
    )
    assert len(exclusive) == 2


def test_find_outputs(storage_seeded) -> None:
    storage, seed = storage_seeded
    outputs = storage.find_outputs({"partial": {}})
    assert len(outputs) == 5  # Updated: 3 original + 2 added for test_create_action tests

    user1_outputs = storage.find_outputs({"partial": {"userId": seed["user1"]["userId"]}})
    assert len(user1_outputs) == 4  # Updated: 2 original + 2 added for test_create_action tests

    user2_outputs = storage.find_outputs({"partial": {"userId": seed["user2"]["userId"]}})
    assert len(user2_outputs) == 1


def test_find_output_tags_and_maps(storage_seeded) -> None:
    storage, seed = storage_seeded
    tags = storage.find_output_tags({"partial": {"userId": seed["user1"]["userId"]}})
    assert len(tags) == 2

    tag_maps = storage.find_output_tag_maps({"partial": {}})
    assert len(tag_maps) == 3


def test_find_transactions_and_commissions(storage_seeded) -> None:
    storage, seed = storage_seeded
    txs = storage.find_transactions({"partial": {}})
    assert len(txs) == 4  # Updated: 3 original + 1 added (tx4) for test_create_action tests

    txs_user1 = storage.find_transactions({"partial": {"userId": seed["user1"]["userId"]}})
    assert len(txs_user1) == 3  # Updated: 2 original + 1 added (tx4) for test_create_action tests

    txs_user2 = storage.find_transactions({"partial": {"userId": seed["user2"]["userId"]}})
    assert len(txs_user2) == 1

    commissions = storage.find_commissions({"partial": {}})
    assert len(commissions) == 3  # Commissions unchanged

    commissions_user1 = storage.find_commissions({"partial": {"userId": seed["user1"]["userId"]}})
    assert len(commissions_user1) == 2  # Commissions unchanged


def test_find_tx_labels_and_maps(storage_seeded) -> None:
    storage, seed = storage_seeded
    labels = storage.find_tx_labels({"partial": {}})
    assert len(labels) == 3

    labels_user1 = storage.find_tx_labels({"partial": {"userId": seed["user1"]["userId"]}})
    assert len(labels_user1) == 2

    tx1_id = seed["transactions"]["tx1"]["transactionId"]
    label_maps = storage.find_tx_label_maps({"partial": {"transactionId": tx1_id}})
    assert len(label_maps) == 2


def test_find_monitor_and_sync_state(storage_seeded) -> None:
    storage, seed = storage_seeded
    monitor_events = storage.find_monitor_events({"partial": {}})
    assert len(monitor_events) == 1
    assert monitor_events[0]["event"] == seed["monitorEvent"]["event"]

    sync_states = storage.find_sync_states({"partial": {}})
    assert len(sync_states) == 1
    assert sync_states[0]["status"] == seed["syncState"]["status"]


def test_find_output_baskets_since_filter_per_user(storage_seeded) -> None:
    storage, seed = storage_seeded
    earliest = min(basket["createdAt"] for basket in seed["outputBaskets"])
    later_threshold = earliest + timedelta(minutes=2)
    filtered = storage.find_output_baskets(
        {
            "partial": {"userId": seed["user1"]["userId"]},
            "since": later_threshold,
        }
    )
    assert len(filtered) == 1
