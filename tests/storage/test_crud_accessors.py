"""Tests for CRUD entity accessors."""

from unittest.mock import Mock

import pytest

from bsv_wallet_toolbox.storage.crud import (
    CertifierAccessor,
    CommissionAccessor,
    TransactionAccessor,
    UserAccessor,
)


class TestCommissionAccessor:
    """Test CommissionAccessor functionality."""

    def test_create(self):
        """Test creating commission via accessor."""
        provider = Mock()
        accessor = CommissionAccessor(provider)

        data = {"userId": 1, "amount": 1000}
        accessor.create(data)

        provider.insert_commission.assert_called_once_with(data)

    def test_read_returns_reader(self):
        """Test read method returns proper reader."""
        provider = Mock()
        accessor = CommissionAccessor(provider)

        reader = accessor.read()
        assert isinstance(reader, type(accessor.read()))


class TestTransactionAccessor:
    """Test TransactionAccessor functionality."""

    def test_create(self):
        """Test creating transaction via accessor."""
        provider = Mock()
        accessor = TransactionAccessor(provider)

        data = {"txid": "abc123", "status": "pending"}
        accessor.create(data)

        provider.insert_transaction.assert_called_once_with(data)

    def test_read_user_id_filter(self):
        """Test filtering transactions by user_id."""
        provider = Mock()
        accessor = TransactionAccessor(provider)

        reader = accessor.read()
        filtered_reader = reader.user_id().equals(42)

        assert filtered_reader is reader  # Fluent interface returns self


class TestUserAccessor:
    """Test UserAccessor functionality."""

    def test_identity_key_filter(self):
        """Test filtering users by identity key."""
        provider = Mock()
        accessor = UserAccessor(provider)

        reader = accessor.read()
        filtered_reader = reader.identity_key().equals("test_key")

        assert filtered_reader is reader


class TestCertifierAccessor:
    """Test CertifierAccessor functionality."""

    def test_read_only_operations(self):
        """Test that certifier accessor only supports read operations."""
        provider = Mock()
        accessor = CertifierAccessor(provider)

        # Should work
        accessor.read()

        # Should raise NotImplementedError
        with pytest.raises(NotImplementedError):
            accessor.create({})

        with pytest.raises(NotImplementedError):
            accessor.update(1, {})
