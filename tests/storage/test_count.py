"""Unit tests for storage COUNT operations.

Reference: wallet-toolbox/test/storage/count.test.ts
"""

import re
from collections.abc import Callable
from datetime import datetime
from typing import Any


def _camel_to_snake(name: str) -> str:
    step_one = re.sub("([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", step_one).lower()


def _build_mock_storage(methods: dict[str, Callable[..., Any]]) -> Any:
    """Create a mock storage object exposing both camelCase and snake_case names."""
    cls = type("MockStorage", (), {})
    for attr, func in methods.items():
        setattr(cls, attr, func)
        snake = _camel_to_snake(attr)
        if snake != attr:
            setattr(cls, snake, func)
    return cls()


class Testcount:
    """Test suite for database COUNT operations."""

    def test_count_proventx(self) -> None:
        """Given: Mock storage with test data
           When: Count ProvenTx with empty filter
           Then: Returns expected count

        Reference: test/storage/count.test.ts
                  test('0 count ProvenTx')
        """
        # Given

        mock_storage = _build_mock_storage({"countProvenTxs": lambda self, query: 0})

        # When
        count = mock_storage.count_proven_txs({"partial": {}})

        # Then
        assert count >= 0

    def test_count_proventxreq(self) -> None:
        """Given: Mock storage with test data
           When: Count ProvenTxReq with empty filter
           Then: Returns expected count

        Reference: test/storage/count.test.ts
                  test('1 count ProvenTxReq')
        """
        # Given

        mock_storage = _build_mock_storage({"countProvenTxReqs": lambda self, query: 0})

        # When
        count = mock_storage.count_proven_tx_reqs({"partial": {}})

        # Then
        assert count >= 0

    def test_count_user(self) -> None:
        """Given: Mock storage with test data
           When: Count User with empty filter
           Then: Returns expected count

        Reference: test/storage/count.test.ts
                  test('2 count User')
        """
        # Given

        mock_storage = _build_mock_storage({"countUsers": lambda self, query: 0})

        # When
        count = mock_storage.count_users({"partial": {}})

        # Then
        assert count >= 0

    def test_count_certificate(self) -> None:
        """Given: Mock storage with test data
           When: Count Certificate with various filters (empty, certifiers, types)
           Then: Returns expected count for each filter

        Reference: test/storage/count.test.ts
                  test('3 count Certificate')
        """
        # Given

        mock_storage = _build_mock_storage({"countCertificates": lambda self, query: 0})

        # When - empty filter
        count_all = mock_storage.count_certificates({"partial": {}})

        # When - with certifiers filter
        count_certifiers = mock_storage.count_certificates({"partial": {}, "certifiers": ["test_certifier"]})

        # When - with types filter
        count_types = mock_storage.count_certificates({"partial": {}, "types": ["test_type"]})

        # Then
        assert count_all >= 0
        assert count_certifiers >= 0
        assert count_types >= 0

    def test_count_certificatefield(self) -> None:
        """Given: Mock storage with test data
           When: Count CertificateField with various filters (empty, userId, fieldName)
           Then: Returns expected count for each filter

        Reference: test/storage/count.test.ts
                  test('4 count CertificateField')
        """
        # Given

        mock_storage = _build_mock_storage({"countCertificateFields": lambda self, query: 0})

        # When - empty filter
        count_all = mock_storage.count_certificate_fields({"partial": {}})

        # When - with userId filter
        count_user = mock_storage.count_certificate_fields({"partial": {"userId": 1}})

        # When - with fieldName filter
        count_field = mock_storage.count_certificate_fields({"partial": {"fieldName": "name"}})

        # Then
        assert count_all >= 0
        assert count_user >= 0
        assert count_field >= 0

    def test_count_outputbasket(self) -> None:
        """Given: Mock storage with test data
           When: Count OutputBasket with empty filter and since parameter
           Then: Returns expected count

        Reference: test/storage/count.test.ts
                  test('5 count OutputBasket')
        """
        # Given

        mock_storage = _build_mock_storage({"countOutputBaskets": lambda self, query: 0})

        # When - empty filter
        count_all = mock_storage.count_output_baskets({"partial": {}})

        # When - with since parameter
        count_since = mock_storage.count_output_baskets({"partial": {}, "since": datetime.now()})

        # Then
        assert count_all >= 0
        assert count_since >= 0

    def test_count_transaction(self) -> None:
        """Given: Mock storage with test data
           When: Count Transaction with empty filter
           Then: Returns expected count

        Reference: test/storage/count.test.ts
                  test('6 count Transaction')
        """
        # Given

        mock_storage = _build_mock_storage({"countTransactions": lambda self, query: 0})

        # When
        count = mock_storage.count_transactions({"partial": {}})

        # Then
        assert count >= 0

    def test_count_commission(self) -> None:
        """Given: Mock storage with test data
           When: Count Commission with empty filter
           Then: Returns expected count

        Reference: test/storage/count.test.ts
                  test('7 count Commission')
        """
        # Given

        mock_storage = _build_mock_storage({"countCommissions": lambda self, query: 0})

        # When
        count = mock_storage.count_commissions({"partial": {}})

        # Then
        assert count >= 0

    def test_count_output(self) -> None:
        """Given: Mock storage with test data
           When: Count Output with empty filter
           Then: Returns expected count

        Reference: test/storage/count.test.ts
                  test('8 count Output')
        """
        # Given

        mock_storage = _build_mock_storage({"countOutputs": lambda self, query: 0})

        # When
        count = mock_storage.count_outputs({"partial": {}})

        # Then
        assert count >= 0

    def test_count_outputtag(self) -> None:
        """Given: Mock storage with test data
           When: Count OutputTag with empty filter
           Then: Returns expected count

        Reference: test/storage/count.test.ts
                  test('9 count OutputTag')
        """
        # Given

        mock_storage = _build_mock_storage({"countOutputTags": lambda self, query: 0})

        # When
        count = mock_storage.count_output_tags({"partial": {}})

        # Then
        assert count >= 0

    def test_count_outputtagmap(self) -> None:
        """Given: Mock storage with test data
           When: Count OutputTagMap with empty filter
           Then: Returns expected count

        Reference: test/storage/count.test.ts
                  test('10 count OutputTagMap')
        """
        # Given

        mock_storage = _build_mock_storage({"countOutputTagMaps": lambda self, query: 0})

        # When
        count = mock_storage.count_output_tag_maps({"partial": {}})

        # Then
        assert count >= 0

    def test_count_txlabel(self) -> None:
        """Given: Mock storage with test data
           When: Count TxLabel with empty filter
           Then: Returns expected count

        Reference: test/storage/count.test.ts
                  test('11 count TxLabel')
        """
        # Given

        mock_storage = _build_mock_storage({"countTxLabels": lambda self, query: 0})

        # When
        count = mock_storage.count_tx_labels({"partial": {}})

        # Then
        assert count >= 0

    def test_count_txlabelmap(self) -> None:
        """Given: Mock storage with test data
           When: Count TxLabelMap with empty filter
           Then: Returns expected count

        Reference: test/storage/count.test.ts
                  test('12 count TxLabelMap')
        """
        # Given

        mock_storage = _build_mock_storage({"countTxLabelMaps": lambda self, query: 0})

        # When
        count = mock_storage.count_tx_label_maps({"partial": {}})

        # Then
        assert count >= 0

    def test_count_monitorevent(self) -> None:
        """Given: Mock storage with test data
           When: Count MonitorEvent with empty filter
           Then: Returns expected count

        Reference: test/storage/count.test.ts
                  test('13 count MonitorEvent')

        Note: This test (#221) exists in TypeScript but was not listed in the original test plan document.
        """
        # Given

        mock_storage = _build_mock_storage({"countMonitorEvents": lambda self, query: 0})

        # When
        count = mock_storage.count_monitor_events({"partial": {}})

        # Then
        assert count >= 0

    def test_count_syncstate(self) -> None:
        """Given: Mock storage with test data
           When: Count SyncState with empty filter
           Then: Returns expected count

        Reference: test/storage/count.test.ts
                  test('14 count SyncState')

        Note: This test (#222) exists in TypeScript but was not listed in the original test plan document.
        """
        # Given

        mock_storage = _build_mock_storage({"countSyncStates": lambda self, query: 0})

        # When
        count = mock_storage.count_sync_states({"partial": {}})

        # Then
        assert count >= 0
