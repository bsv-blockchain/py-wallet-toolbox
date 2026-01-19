"""CRUD entity accessors for storage provider.

Provides direct CRUD access to storage entities following Go's pattern but adapted for Python.
Each accessor provides a fluent interface for building queries and performing operations.

Reference: go-wallet-toolbox/pkg/storage/crud/
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from typing import Any, Generic, TypeVar

from .provider import StorageProvider

# Generic types for fluent interface
T = TypeVar("T")
ParentT = TypeVar("ParentT")


class Condition(Generic[T, ParentT], ABC):
    """Base condition interface for query building."""

    def __init__(self, parent: ParentT, setter: Callable[[T], None]):
        self.parent = parent
        self.setter = setter

    @abstractmethod
    def equals(self, value: T) -> ParentT:
        """Exact match condition."""
        ...

    @abstractmethod
    def not_equals(self, value: T) -> ParentT:
        """Not equal condition."""
        ...

    @abstractmethod
    def in_(self, values: list[T]) -> ParentT:
        """In list condition."""
        ...

    @abstractmethod
    def not_in(self, values: list[T]) -> ParentT:
        """Not in list condition."""
        ...

    @abstractmethod
    def like(self, pattern: str) -> ParentT:
        """Like pattern condition."""
        ...


class StringCondition(Condition[str, ParentT]):
    """String condition for query building."""

    def equals(self, value: str) -> ParentT:
        """Exact string match."""
        from .specifications import Comparable

        self.setter(Comparable(operator="equals", value=value))
        return self.parent

    def not_equals(self, value: str) -> ParentT:
        """String not equal."""
        from .specifications import Comparable

        self.setter(Comparable(operator="not_equals", value=value))
        return self.parent

    def in_(self, values: list[str]) -> ParentT:
        """String in list."""
        from .specifications import Comparable

        self.setter(Comparable(operator="in", value=values))
        return self.parent

    def not_in(self, values: list[str]) -> ParentT:
        """String not in list."""
        from .specifications import Comparable

        self.setter(Comparable(operator="not_in", value=values))
        return self.parent

    def like(self, pattern: str) -> ParentT:
        """String pattern match."""
        from .specifications import Comparable

        self.setter(Comparable(operator="like", value=pattern))
        return self.parent


class NumericCondition(Condition[int, ParentT]):
    """Numeric condition for query building."""

    def equals(self, value: int) -> ParentT:
        """Exact numeric match."""
        from .specifications import Comparable

        self.setter(Comparable(operator="equals", value=value))
        return self.parent

    def not_equals(self, value: int) -> ParentT:
        """Numeric not equal."""
        from .specifications import Comparable

        self.setter(Comparable(operator="not_equals", value=value))
        return self.parent

    def in_(self, values: list[int]) -> ParentT:
        """Numeric in list."""
        from .specifications import Comparable

        self.setter(Comparable(operator="in", value=values))
        return self.parent

    def not_in(self, values: list[int]) -> ParentT:
        """Numeric not in list."""
        from .specifications import Comparable

        self.setter(Comparable(operator="not_in", value=values))
        return self.parent

    def like(self, pattern: str) -> ParentT:
        """Not applicable for numeric fields."""
        raise NotImplementedError("Like not supported for numeric fields")


class BoolCondition(Condition[bool, ParentT]):
    """Boolean condition for query building."""

    def equals(self, value: bool) -> ParentT:
        """Exact boolean match."""
        from .specifications import Comparable

        self.setter(Comparable(operator="equals", value=value))
        return self.parent

    def not_equals(self, value: bool) -> ParentT:
        """Boolean not equal."""
        from .specifications import Comparable

        self.setter(Comparable(operator="not_equals", value=value))
        return self.parent

    def in_(self, values: list[bool]) -> ParentT:
        """Boolean in list."""
        from .specifications import Comparable

        self.setter(Comparable(operator="in", value=values))
        return self.parent

    def not_in(self, values: list[bool]) -> ParentT:
        """Boolean not in list."""
        from .specifications import Comparable

        self.setter(Comparable(operator="not_in", value=values))
        return self.parent

    def like(self, pattern: str) -> ParentT:
        """Not applicable for boolean fields."""
        raise NotImplementedError("Like not supported for boolean fields")


class TimeCondition(Condition[datetime, ParentT]):
    """Time condition for query building."""

    def equals(self, value: datetime) -> ParentT:
        """Exact time match."""
        from .specifications import Comparable

        self.setter(Comparable(operator="equals", value=value))
        return self.parent

    def not_equals(self, value: datetime) -> ParentT:
        """Time not equal."""
        from .specifications import Comparable

        self.setter(Comparable(operator="not_equals", value=value))
        return self.parent

    def in_(self, values: list[datetime]) -> ParentT:
        """Time in list."""
        from .specifications import Comparable

        self.setter(Comparable(operator="in", value=values))
        return self.parent

    def not_in(self, values: list[datetime]) -> ParentT:
        """Time not in list."""
        from .specifications import Comparable

        self.setter(Comparable(operator="not_in", value=values))
        return self.parent

    def like(self, pattern: str) -> ParentT:
        """Not applicable for time fields."""
        raise NotImplementedError("Like not supported for time fields")


class EntityAccessor(ABC):
    """Base class for entity accessors providing CRUD operations."""

    def __init__(self, provider: StorageProvider):
        self.provider = provider
        self.spec: dict[str, Any] = {}
        self.paging: dict[str, Any] | None = None

    @abstractmethod
    def read(self) -> EntityReader:
        """Return a reader for building queries."""
        ...

    @abstractmethod
    def create(self, data: dict[str, Any]) -> int:
        """Create a new entity."""
        ...

    @abstractmethod
    def update(self, pk_value: int, patch: dict[str, Any]) -> int:
        """Update an existing entity."""
        ...


class EntityReader(ABC):
    """Base reader interface for building entity queries."""

    @abstractmethod
    def find(self) -> list[dict[str, Any]]:
        """Execute query and return results."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Return count of matching records."""
        ...

    @abstractmethod
    def paged(self, limit: int, offset: int, desc: bool = False) -> EntityReader:
        """Apply pagination to query."""
        ...


# Commission Entity Accessor
class CommissionAccessor(EntityAccessor):
    """Commission entity accessor."""

    def read(self) -> CommissionReader:
        return CommissionReader(self.provider)

    def create(self, data: dict[str, Any]) -> int:
        return self.provider.insert_commission(data)

    def update(self, pk_value: int, patch: dict[str, Any]) -> int:
        return self.provider.update_commission(pk_value, patch)


class CommissionReader(EntityReader):
    """Commission reader with fluent interface."""

    def __init__(self, provider: StorageProvider):
        self.provider = provider
        self.spec: dict[str, Any] = {}
        self.paging: dict[str, Any] | None = None

    def user_id(self) -> NumericCondition[CommissionReader]:
        def setter(spec) -> None:
            self.spec["userId"] = spec

        return NumericCondition(self, setter)

    def amount(self) -> NumericCondition[CommissionReader]:
        def setter(spec) -> None:
            self.spec["amount"] = spec

        return NumericCondition(self, setter)

    def paged(self, limit: int, offset: int, desc: bool = False) -> CommissionReader:
        self.paging = {"limit": limit, "offset": offset, "desc": desc}
        return self

    def find(self) -> list[dict[str, Any]]:
        query = {"partial": self.spec}
        if self.paging:
            query.update(self.paging)
        return self.provider.find_commissions(query)

    def count(self) -> int:
        return self.provider.count_commissions(self.spec)


# Transaction Entity Accessor
class TransactionAccessor(EntityAccessor):
    """Transaction entity accessor."""

    def read(self) -> TransactionReader:
        return TransactionReader(self.provider)

    def create(self, data: dict[str, Any]) -> int:
        return self.provider.insert_transaction(data)

    def update(self, pk_value: int, patch: dict[str, Any]) -> int:
        return self.provider.update_transaction(pk_value, patch)


class TransactionReader(EntityReader):
    """Transaction reader with fluent interface."""

    def __init__(self, provider: StorageProvider):
        self.provider = provider
        self.spec: dict[str, Any] = {}
        self.paging: dict[str, Any] | None = None

    def user_id(self) -> NumericCondition[TransactionReader]:
        def setter(spec) -> None:
            self.spec["userId"] = spec

        return NumericCondition(self, setter)

    def txid(self) -> StringCondition[TransactionReader]:
        def setter(spec) -> None:
            self.spec["txid"] = spec

        return StringCondition(self, setter)

    def status(self) -> StringCondition[TransactionReader]:
        def setter(spec) -> None:
            self.spec["status"] = spec

        return StringCondition(self, setter)

    def paged(self, limit: int, offset: int, desc: bool = False) -> TransactionReader:
        self.paging = {"limit": limit, "offset": offset, "desc": desc}
        return self

    def find(self) -> list[dict[str, Any]]:
        query = {"partial": self.spec}
        if self.paging:
            query.update(self.paging)
        return self.provider.find_transactions(query)

    def count(self) -> int:
        return self.provider.count_transactions(self.spec)


# User Entity Accessor
class UserAccessor(EntityAccessor):
    """User entity accessor."""

    def read(self) -> UserReader:
        return UserReader(self.provider)

    def create(self, data: dict[str, Any]) -> int:
        return self.provider.insert_user(data)

    def update(self, pk_value: int, patch: dict[str, Any]) -> int:
        return self.provider.update_user(pk_value, patch)


class UserReader(EntityReader):
    """User reader with fluent interface."""

    def __init__(self, provider: StorageProvider):
        self.provider = provider
        self.spec: dict[str, Any] = {}
        self.paging: dict[str, Any] | None = None

    def identity_key(self) -> StringCondition[UserReader]:
        def setter(spec) -> None:
            self.spec["identityKey"] = spec

        return StringCondition(self, setter)

    def active_storage(self) -> StringCondition[UserReader]:
        def setter(spec) -> None:
            self.spec["activeStorage"] = spec

        return StringCondition(self, setter)

    def paged(self, limit: int, offset: int, desc: bool = False) -> UserReader:
        self.paging = {"limit": limit, "offset": offset, "desc": desc}
        return self

    def find(self) -> list[dict[str, Any]]:
        query = {"partial": self.spec}
        if self.paging:
            query.update(self.paging)
        return self.provider.find_users(query)

    def count(self) -> int:
        return self.provider.count_users(self.spec)


# Output Basket Entity Accessor
class OutputBasketAccessor(EntityAccessor):
    """Output basket entity accessor."""

    def read(self) -> OutputBasketReader:
        return OutputBasketReader(self.provider)

    def create(self, data: dict[str, Any]) -> int:
        return self.provider.insert_output_basket(data)

    def update(self, pk_value: int, patch: dict[str, Any]) -> int:
        return self.provider.update_output_basket(pk_value, patch)


class OutputBasketReader(EntityReader):
    """Output basket reader with fluent interface."""

    def __init__(self, provider: StorageProvider):
        self.provider = provider
        self.spec: dict[str, Any] = {}
        self.paging: dict[str, Any] | None = None

    def user_id(self) -> NumericCondition[OutputBasketReader]:
        def setter(spec) -> None:
            self.spec["userId"] = spec

        return NumericCondition(self, setter)

    def name(self) -> StringCondition[OutputBasketReader]:
        def setter(spec) -> None:
            self.spec["name"] = spec

        return StringCondition(self, setter)

    def paged(self, limit: int, offset: int, desc: bool = False) -> OutputBasketReader:
        self.paging = {"limit": limit, "offset": offset, "desc": desc}
        return self

    def find(self) -> list[dict[str, Any]]:
        query = {"partial": self.spec}
        if self.paging:
            query.update(self.paging)
        return self.provider.find_output_baskets(query)

    def count(self) -> int:
        return self.provider.count_output_baskets(self.spec)


# Output Entity Accessor
class OutputAccessor(EntityAccessor):
    """Output entity accessor."""

    def read(self) -> OutputReader:
        return OutputReader(self.provider)

    def create(self, data: dict[str, Any]) -> int:
        return self.provider.insert_output(data)

    def update(self, pk_value: int, patch: dict[str, Any]) -> int:
        return self.provider.update_output(pk_value, patch)


class OutputReader(EntityReader):
    """Output reader with fluent interface."""

    def __init__(self, provider: StorageProvider):
        self.provider = provider
        self.spec: dict[str, Any] = {}
        self.paging: dict[str, Any] | None = None

    def user_id(self) -> NumericCondition[OutputReader]:
        def setter(spec) -> None:
            self.spec["userId"] = spec

        return NumericCondition(self, setter)

    def transaction_id(self) -> NumericCondition[OutputReader]:
        def setter(spec) -> None:
            self.spec["transactionId"] = spec

        return NumericCondition(self, setter)

    def spendable(self) -> BoolCondition[OutputReader]:
        def setter(spec) -> None:
            self.spec["spendable"] = spec

        return BoolCondition(self, setter)

    def paged(self, limit: int, offset: int, desc: bool = False) -> OutputReader:
        self.paging = {"limit": limit, "offset": offset, "desc": desc}
        return self

    def find(self) -> list[dict[str, Any]]:
        query = {"partial": self.spec}
        if self.paging:
            query.update(self.paging)
        return self.provider.find_outputs(query)

    def count(self) -> int:
        return self.provider.count_outputs(self.spec)


# TxNote Entity Accessor
class TxNoteAccessor(EntityAccessor):
    """Transaction note entity accessor."""

    def read(self) -> TxNoteReader:
        return TxNoteReader(self.provider)

    def create(self, data: dict[str, Any]) -> int:
        return self.provider.insert_tx_note(data)

    def update(self, pk_value: int, patch: dict[str, Any]) -> int:
        return self.provider.update_tx_note(pk_value, patch)


class TxNoteReader(EntityReader):
    """TxNote reader with fluent interface."""

    def __init__(self, provider: StorageProvider):
        self.provider = provider
        self.spec: dict[str, Any] = {}
        self.paging: dict[str, Any] | None = None

    def transaction_id(self) -> NumericCondition[TxNoteReader]:
        def setter(spec) -> None:
            self.spec["transactionId"] = spec

        return NumericCondition(self, setter)

    def note(self) -> StringCondition[TxNoteReader]:
        def setter(spec) -> None:
            self.spec["note"] = spec

        return StringCondition(self, setter)

    def paged(self, limit: int, offset: int, desc: bool = False) -> TxNoteReader:
        self.paging = {"limit": limit, "offset": offset, "desc": desc}
        return self

    def find(self) -> list[dict[str, Any]]:
        # TxNote doesn't have a specific finder method, use generic
        query = {"partial": self.spec}
        if self.paging:
            query.update(self.paging)
        return self.provider._find_generic("tx_note", query)

    def count(self) -> int:
        return self.provider._count_generic("tx_note", self.spec)


# KnownTx Entity Accessor
class KnownTxAccessor(EntityAccessor):
    """Known transaction entity accessor."""

    def read(self) -> KnownTxReader:
        return KnownTxReader(self.provider)

    def create(self, data: dict[str, Any]) -> int:
        # KnownTx might not have direct insert, use generic
        return self.provider._insert_generic("known_tx", data)

    def update(self, pk_value: int, patch: dict[str, Any]) -> int:
        return self.provider._update_generic("known_tx", pk_value, patch)


class KnownTxReader(EntityReader):
    """KnownTx reader with fluent interface."""

    def __init__(self, provider: StorageProvider):
        self.provider = provider
        self.spec: dict[str, Any] = {}
        self.paging: dict[str, Any] | None = None

    def txid(self) -> StringCondition[KnownTxReader]:
        def setter(spec) -> None:
            self.spec["txid"] = spec

        return StringCondition(self, setter)

    def paged(self, limit: int, offset: int, desc: bool = False) -> KnownTxReader:
        self.paging = {"limit": limit, "offset": offset, "desc": desc}
        return self

    def find(self) -> list[dict[str, Any]]:
        # KnownTx doesn't have a specific finder method, use generic
        query = {"partial": self.spec}
        if self.paging:
            query.update(self.paging)
        return self.provider._find_generic("known_tx", query)

    def count(self) -> int:
        return self.provider._count_generic("known_tx", self.spec)


# Certifier Entity Accessor
class CertifierAccessor(EntityAccessor):
    """Certifier entity accessor (wrapper around certificate queries)."""

    def read(self) -> CertifierReader:
        return CertifierReader(self.provider)

    def create(self, data: dict[str, Any]) -> int:
        # Certifier is derived from certificates, not directly creatable
        raise NotImplementedError("Certifier entities are derived from certificates")

    def update(self, pk_value: int, patch: dict[str, Any]) -> int:
        # Certifier is derived from certificates, not directly updatable
        raise NotImplementedError("Certifier entities are derived from certificates")


class CertifierReader(EntityReader):
    """Certifier reader - provides distinct certifier information from certificates."""

    def __init__(self, provider: StorageProvider):
        self.provider = provider
        self.spec: dict[str, Any] = {}
        self.paging: dict[str, Any] | None = None

    def certifier(self) -> StringCondition[CertifierReader]:
        def setter(spec) -> None:
            self.spec["certifier"] = spec

        return StringCondition(self, setter)

    def paged(self, limit: int, offset: int, desc: bool = False) -> CertifierReader:
        self.paging = {"limit": limit, "offset": offset, "desc": desc}
        return self

    def find(self) -> list[dict[str, Any]]:
        # Get distinct certifiers from certificates
        certificates = self.provider.find_certificates({"partial": self.spec})
        certifiers = {}
        for cert in certificates:
            key = cert.get("certifier")
            if key and key not in certifiers:
                certifiers[key] = {"certifier": key}
        return list(certifiers.values())

    def count(self) -> int:
        # Get count of distinct certifiers
        certifiers = self.find()
        return len(certifiers)
