"""High-impact coverage tests for storage/crud.py conditions and accessors.

This module targets the most critical uncovered lines in crud.py
to maximize coverage improvement. Focuses on:
- Condition classes (StringCondition, NumericCondition, BoolCondition, TimeCondition)
- Entity accessor methods
- Reader fluent interface methods
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

try:
    from bsv_wallet_toolbox.storage.crud import (
        BoolCondition,
        CertifierAccessor,
        CertifierReader,
        KnownTxAccessor,
        KnownTxReader,
        NumericCondition,
        OutputAccessor,
        OutputReader,
        StringCondition,
        TimeCondition,
        TxNoteAccessor,
        TxNoteReader,
    )
    from bsv_wallet_toolbox.storage.provider import StorageProvider

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    StringCondition = None
    NumericCondition = None
    BoolCondition = None
    TimeCondition = None
    OutputAccessor = None
    OutputReader = None
    TxNoteAccessor = None
    TxNoteReader = None
    KnownTxAccessor = None
    KnownTxReader = None
    CertifierAccessor = None
    CertifierReader = None
    StorageProvider = None


@pytest.fixture
def mock_provider():
    """Create a mock storage provider."""
    provider = Mock(spec=StorageProvider)
    provider.find_outputs.return_value = []
    provider.count_outputs.return_value = 0
    provider.insert_tx_note.return_value = 1
    provider.update_tx_note.return_value = 1
    provider._find_generic.return_value = []
    provider._count_generic.return_value = 0
    provider._insert_generic.return_value = 1
    provider._update_generic.return_value = 1
    provider.find_certificates.return_value = []
    return provider


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="CRUD classes not available")
class TestStringCondition:
    """Test StringCondition class methods."""

    def test_string_condition_equals(self):
        """Test StringCondition.equals method."""
        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = StringCondition(parent, setter)
        result = condition.equals("test_value")

        assert result == parent
        assert len(setter_calls) == 1
        assert setter_calls[0].operator == "equals"
        assert setter_calls[0].value == "test_value"

    def test_string_condition_not_equals(self):
        """Test StringCondition.not_equals method."""
        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = StringCondition(parent, setter)
        result = condition.not_equals("test_value")

        assert result == parent
        assert len(setter_calls) == 1
        assert setter_calls[0].operator == "not_equals"
        assert setter_calls[0].value == "test_value"

    def test_string_condition_in(self):
        """Test StringCondition.in_ method."""
        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = StringCondition(parent, setter)
        result = condition.in_(["value1", "value2"])

        assert result == parent
        assert len(setter_calls) == 1
        assert setter_calls[0].operator == "in"
        assert setter_calls[0].value == ["value1", "value2"]

    def test_string_condition_not_in(self):
        """Test StringCondition.not_in method."""
        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = StringCondition(parent, setter)
        result = condition.not_in(["value1", "value2"])

        assert result == parent
        assert len(setter_calls) == 1
        assert setter_calls[0].operator == "not_in"
        assert setter_calls[0].value == ["value1", "value2"]

    def test_string_condition_like(self):
        """Test StringCondition.like method."""
        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = StringCondition(parent, setter)
        result = condition.like("test%")

        assert result == parent
        assert len(setter_calls) == 1
        assert setter_calls[0].operator == "like"
        assert setter_calls[0].value == "test%"


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="CRUD classes not available")
class TestNumericCondition:
    """Test NumericCondition class methods."""

    def test_numeric_condition_equals(self):
        """Test NumericCondition.equals method."""
        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = NumericCondition(parent, setter)
        result = condition.equals(42)

        assert result == parent
        assert len(setter_calls) == 1
        assert setter_calls[0].operator == "equals"
        assert setter_calls[0].value == 42

    def test_numeric_condition_not_equals(self):
        """Test NumericCondition.not_equals method."""
        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = NumericCondition(parent, setter)
        result = condition.not_equals(42)

        assert result == parent
        assert len(setter_calls) == 1
        assert setter_calls[0].operator == "not_equals"
        assert setter_calls[0].value == 42

    def test_numeric_condition_in(self):
        """Test NumericCondition.in_ method."""
        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = NumericCondition(parent, setter)
        result = condition.in_([1, 2, 3])

        assert result == parent
        assert len(setter_calls) == 1
        assert setter_calls[0].operator == "in"
        assert setter_calls[0].value == [1, 2, 3]

    def test_numeric_condition_not_in(self):
        """Test NumericCondition.not_in method."""
        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = NumericCondition(parent, setter)
        result = condition.not_in([1, 2, 3])

        assert result == parent
        assert len(setter_calls) == 1
        assert setter_calls[0].operator == "not_in"
        assert setter_calls[0].value == [1, 2, 3]

    def test_numeric_condition_like_raises(self):
        """Test NumericCondition.like method raises NotImplementedError."""
        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = NumericCondition(parent, setter)

        with pytest.raises(NotImplementedError, match="Like not supported for numeric fields"):
            condition.like("42%")


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="CRUD classes not available")
class TestBoolCondition:
    """Test BoolCondition class methods."""

    def test_bool_condition_equals(self):
        """Test BoolCondition.equals method."""
        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = BoolCondition(parent, setter)
        result = condition.equals(True)

        assert result == parent
        assert len(setter_calls) == 1
        assert setter_calls[0].operator == "equals"
        assert setter_calls[0].value is True

    def test_bool_condition_not_equals(self):
        """Test BoolCondition.not_equals method."""
        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = BoolCondition(parent, setter)
        result = condition.not_equals(False)

        assert result == parent
        assert len(setter_calls) == 1
        assert setter_calls[0].operator == "not_equals"
        assert setter_calls[0].value is False

    def test_bool_condition_in(self):
        """Test BoolCondition.in_ method."""
        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = BoolCondition(parent, setter)
        result = condition.in_([True, False])

        assert result == parent
        assert len(setter_calls) == 1
        assert setter_calls[0].operator == "in"
        assert setter_calls[0].value == [True, False]

    def test_bool_condition_not_in(self):
        """Test BoolCondition.not_in method."""
        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = BoolCondition(parent, setter)
        result = condition.not_in([True])

        assert result == parent
        assert len(setter_calls) == 1
        assert setter_calls[0].operator == "not_in"
        assert setter_calls[0].value == [True]

    def test_bool_condition_like_raises(self):
        """Test BoolCondition.like method raises NotImplementedError."""
        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = BoolCondition(parent, setter)

        with pytest.raises(NotImplementedError, match="Like not supported for boolean fields"):
            condition.like("pattern")


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="CRUD classes not available")
class TestTimeCondition:
    """Test TimeCondition class methods."""

    def test_time_condition_equals(self):
        """Test TimeCondition.equals method."""
        from datetime import datetime

        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = TimeCondition(parent, setter)
        test_time = datetime(2023, 1, 1, 12, 0, 0)
        result = condition.equals(test_time)

        assert result == parent
        assert len(setter_calls) == 1
        assert setter_calls[0].operator == "equals"
        assert setter_calls[0].value == test_time

    def test_time_condition_not_equals(self):
        """Test TimeCondition.not_equals method."""
        from datetime import datetime

        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = TimeCondition(parent, setter)
        test_time = datetime(2023, 1, 1, 12, 0, 0)
        result = condition.not_equals(test_time)

        assert result == parent
        assert len(setter_calls) == 1
        assert setter_calls[0].operator == "not_equals"
        assert setter_calls[0].value == test_time

    def test_time_condition_in(self):
        """Test TimeCondition.in_ method."""
        from datetime import datetime

        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = TimeCondition(parent, setter)
        test_times = [datetime(2023, 1, 1, 12, 0, 0), datetime(2023, 1, 2, 12, 0, 0)]
        result = condition.in_(test_times)

        assert result == parent
        assert len(setter_calls) == 1
        assert setter_calls[0].operator == "in"
        assert setter_calls[0].value == test_times

    def test_time_condition_not_in(self):
        """Test TimeCondition.not_in method."""
        from datetime import datetime

        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = TimeCondition(parent, setter)
        test_times = [datetime(2023, 1, 1, 12, 0, 0)]
        result = condition.not_in(test_times)

        assert result == parent
        assert len(setter_calls) == 1
        assert setter_calls[0].operator == "not_in"
        assert setter_calls[0].value == test_times

    def test_time_condition_like_raises(self):
        """Test TimeCondition.like method raises NotImplementedError."""

        parent = Mock()
        setter_calls = []

        def setter(spec):
            setter_calls.append(spec)

        condition = TimeCondition(parent, setter)

        with pytest.raises(NotImplementedError, match="Like not supported for time fields"):
            condition.like("2023%")


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="CRUD classes not available")
class TestOutputReader:
    """Test OutputReader fluent interface."""

    def test_output_reader_initialization(self, mock_provider):
        """Test OutputReader initialization."""
        reader = OutputReader(mock_provider)

        assert reader.provider == mock_provider
        assert reader.spec == {}
        assert reader.paging is None

    def test_output_reader_user_id_condition(self, mock_provider):
        """Test OutputReader.user_id condition."""
        reader = OutputReader(mock_provider)
        condition = reader.user_id()

        # Should return a NumericCondition
        assert hasattr(condition, "equals")
        assert hasattr(condition, "not_equals")

    def test_output_reader_transaction_id_condition(self, mock_provider):
        """Test OutputReader.transaction_id condition."""
        reader = OutputReader(mock_provider)
        condition = reader.transaction_id()

        # Should return a NumericCondition
        assert hasattr(condition, "equals")
        assert hasattr(condition, "not_equals")

    def test_output_reader_spendable_condition(self, mock_provider):
        """Test OutputReader.spendable condition."""
        reader = OutputReader(mock_provider)
        condition = reader.spendable()

        # Should return a BoolCondition
        assert hasattr(condition, "equals")
        assert hasattr(condition, "not_equals")

    def test_output_reader_paged(self, mock_provider):
        """Test OutputReader.paged method."""
        reader = OutputReader(mock_provider)
        result = reader.paged(10, 5, True)

        assert result == reader
        assert reader.paging == {"limit": 10, "offset": 5, "desc": True}

    def test_output_reader_find(self, mock_provider):
        """Test OutputReader.find method."""
        reader = OutputReader(mock_provider)
        reader.spec = {"userId": "test_spec"}
        reader.paging = {"limit": 5, "offset": 0}

        result = reader.find()

        assert result == []
        mock_provider.find_outputs.assert_called_once_with(
            {"partial": {"userId": "test_spec"}, "limit": 5, "offset": 0}
        )

    def test_output_reader_count(self, mock_provider):
        """Test OutputReader.count method."""
        reader = OutputReader(mock_provider)
        reader.spec = {"basketId": 123}

        result = reader.count()

        assert result == 0
        mock_provider.count_outputs.assert_called_once_with({"basketId": 123})


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="CRUD classes not available")
class TestTxNoteAccessor:
    """Test TxNoteAccessor methods."""

    def test_tx_note_accessor_read(self, mock_provider):
        """Test TxNoteAccessor.read method."""
        accessor = TxNoteAccessor(mock_provider)
        reader = accessor.read()

        assert isinstance(reader, TxNoteReader)
        assert reader.provider == mock_provider

    def test_tx_note_accessor_create(self, mock_provider):
        """Test TxNoteAccessor.create method."""
        accessor = TxNoteAccessor(mock_provider)

        test_data = {"transactionId": 123, "note": "test note"}
        result = accessor.create(test_data)

        assert result == 1
        mock_provider.insert_tx_note.assert_called_once_with(test_data)

    def test_tx_note_accessor_update(self, mock_provider):
        """Test TxNoteAccessor.update method."""
        accessor = TxNoteAccessor(mock_provider)

        patch = {"note": "updated note"}
        result = accessor.update(123, patch)

        assert result == 1
        mock_provider.update_tx_note.assert_called_once_with(123, patch)


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="CRUD classes not available")
class TestTxNoteReader:
    """Test TxNoteReader fluent interface."""

    def test_tx_note_reader_transaction_id_condition(self, mock_provider):
        """Test TxNoteReader.transaction_id condition."""
        reader = TxNoteReader(mock_provider)
        condition = reader.transaction_id()

        assert hasattr(condition, "equals")
        assert hasattr(condition, "not_equals")

    def test_tx_note_reader_note_condition(self, mock_provider):
        """Test TxNoteReader.note condition."""
        reader = TxNoteReader(mock_provider)
        condition = reader.note()

        assert hasattr(condition, "equals")
        assert hasattr(condition, "like")

    def test_tx_note_reader_find(self, mock_provider):
        """Test TxNoteReader.find method."""
        reader = TxNoteReader(mock_provider)
        reader.spec = {"transactionId": 123}

        result = reader.find()

        assert result == []
        mock_provider._find_generic.assert_called_once_with("tx_note", {"partial": {"transactionId": 123}})

    def test_tx_note_reader_find_with_paging(self, mock_provider):
        """Test TxNoteReader.find method with paging."""
        reader = TxNoteReader(mock_provider)
        reader.spec = {"note": "test"}
        reader.paging = {"limit": 10, "offset": 5, "desc": False}

        reader.find()

        expected_query = {"partial": {"note": "test"}, "limit": 10, "offset": 5, "desc": False}
        mock_provider._find_generic.assert_called_once_with("tx_note", expected_query)


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="CRUD classes not available")
class TestKnownTxAccessor:
    """Test KnownTxAccessor methods."""

    def test_known_tx_accessor_read(self, mock_provider):
        """Test KnownTxAccessor.read method."""
        accessor = KnownTxAccessor(mock_provider)
        reader = accessor.read()

        assert isinstance(reader, KnownTxReader)
        assert reader.provider == mock_provider

    def test_known_tx_accessor_create(self, mock_provider):
        """Test KnownTxAccessor.create method."""
        accessor = KnownTxAccessor(mock_provider)

        test_data = {"txid": "a" * 64}
        result = accessor.create(test_data)

        assert result == 1
        mock_provider._insert_generic.assert_called_once_with("known_tx", test_data)

    def test_known_tx_accessor_update(self, mock_provider):
        """Test KnownTxAccessor.update method."""
        accessor = KnownTxAccessor(mock_provider)

        patch = {"txid": "b" * 64}
        result = accessor.update(456, patch)

        assert result == 1
        mock_provider._update_generic.assert_called_once_with("known_tx", 456, patch)


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="CRUD classes not available")
class TestKnownTxReader:
    """Test KnownTxReader fluent interface."""

    def test_known_tx_reader_txid_condition(self, mock_provider):
        """Test KnownTxReader.txid condition."""
        reader = KnownTxReader(mock_provider)
        condition = reader.txid()

        assert hasattr(condition, "equals")
        assert hasattr(condition, "like")

    def test_known_tx_reader_find(self, mock_provider):
        """Test KnownTxReader.find method."""
        reader = KnownTxReader(mock_provider)
        reader.spec = {"txid": "a" * 64}

        result = reader.find()

        assert result == []
        mock_provider._find_generic.assert_called_once_with("known_tx", {"partial": {"txid": "a" * 64}})


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="CRUD classes not available")
class TestCertifierAccessor:
    """Test CertifierAccessor methods."""

    def test_certifier_accessor_read(self, mock_provider):
        """Test CertifierAccessor.read method."""
        accessor = CertifierAccessor(mock_provider)
        reader = accessor.read()

        assert isinstance(reader, CertifierReader)
        assert reader.provider == mock_provider

    def test_certifier_accessor_create_raises(self, mock_provider):
        """Test CertifierAccessor.create raises NotImplementedError."""
        accessor = CertifierAccessor(mock_provider)

        with pytest.raises(NotImplementedError, match="Certifier entities are derived from certificates"):
            accessor.create({"certifier": "test"})

    def test_certifier_accessor_update_raises(self, mock_provider):
        """Test CertifierAccessor.update raises NotImplementedError."""
        accessor = CertifierAccessor(mock_provider)

        with pytest.raises(NotImplementedError, match="Certifier entities are derived from certificates"):
            accessor.update(123, {"certifier": "updated"})


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="CRUD classes not available")
class TestCertifierReader:
    """Test CertifierReader functionality."""

    def test_certifier_reader_certifier_condition(self, mock_provider):
        """Test CertifierReader.certifier condition."""
        reader = CertifierReader(mock_provider)
        condition = reader.certifier()

        assert hasattr(condition, "equals")
        assert hasattr(condition, "like")

    def test_certifier_reader_find_empty(self, mock_provider):
        """Test CertifierReader.find with empty certificates."""
        reader = CertifierReader(mock_provider)

        result = reader.find()

        assert result == []
        mock_provider.find_certificates.assert_called_once_with({"partial": {}})

    def test_certifier_reader_find_with_certificates(self, mock_provider):
        """Test CertifierReader.find with certificate data."""
        reader = CertifierReader(mock_provider)

        # Mock certificates with different certifiers
        mock_provider.find_certificates.return_value = [
            {"certifier": "certifier_a", "type": "identity"},
            {"certifier": "certifier_b", "type": "employment"},
            {"certifier": "certifier_a", "type": "compliance"},  # Duplicate certifier
        ]

        result = reader.find()

        assert len(result) == 2  # Should deduplicate
        certifiers = {item["certifier"] for item in result}
        assert certifiers == {"certifier_a", "certifier_b"}

    def test_certifier_reader_find_with_filter(self, mock_provider):
        """Test CertifierReader.find with certifier filter."""
        reader = CertifierReader(mock_provider)

        # Mock the Comparable object that gets set
        from bsv_wallet_toolbox.storage.specifications import Comparable

        Comparable(operator="equals", value="certifier_a")
        reader.certifier().equals("certifier_a")

        mock_provider.find_certificates.return_value = [
            {"certifier": "certifier_a", "type": "identity"},
        ]

        result = reader.find()

        assert len(result) == 1
        assert result[0]["certifier"] == "certifier_a"


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="CRUD classes not available")
class TestOutputAccessor:
    """Test OutputAccessor methods."""

    def test_output_accessor_read(self, mock_provider):
        """Test OutputAccessor.read method."""
        accessor = OutputAccessor(mock_provider)
        reader = accessor.read()

        assert isinstance(reader, OutputReader)
        assert reader.provider == mock_provider

    def test_output_accessor_create(self, mock_provider):
        """Test OutputAccessor.create method."""
        accessor = OutputAccessor(mock_provider)

        test_data = {"userId": 1, "basketId": 1, "vout": 0}
        mock_provider.insert_output.return_value = 456
        result = accessor.create(test_data)

        assert result == 456
        mock_provider.insert_output.assert_called_once_with(test_data)

    def test_output_accessor_update(self, mock_provider):
        """Test OutputAccessor.update method."""
        accessor = OutputAccessor(mock_provider)

        patch = {"spendable": False}
        mock_provider.update_output.return_value = 2
        result = accessor.update(123, patch)

        assert result == 2
        mock_provider.update_output.assert_called_once_with(123, patch)
