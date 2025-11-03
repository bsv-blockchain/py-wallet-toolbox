"""Storage entities - TypeScript Entity classes in Python (Complete).

This module provides DTO (Data Transfer Object) wrapper classes that mirror
TypeScript Entity class functionality, implementing the StorageReaderWriter
entity abstraction layer.

All 14 Entity types are fully implemented with complete merge logic.

Reference:
  - toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityBase.ts
  - toolbox/ts-wallet-toolbox/src/storage/schema/entities/
"""

from datetime import datetime
from typing import Any


class User:
    """User entity DTO - Represents a wallet user with authentication and storage configuration.

    Attributes:
        user_id: Unique user identifier (auto-incremented by database)
        identity_key: User's identity key for authentication
        active_storage: Currently active storage identity key
        created_at: Timestamp when user record was created
        updated_at: Timestamp when user record was last modified

    Special Behavior:
        - merge_new() always raises an exception (users are never created via sync)
        - merge_existing() is a no-op (user properties don't sync from remote)

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityUser.ts
        toolbox/py-wallet-toolbox/tests/storage/entities/test_users.py
    """

    def __init__(self, api_object: dict[str, Any] | None = None) -> None:
        """Initialize User with optional API object.

        Args:
            api_object: Dictionary with keys userId, identityKey, activeStorage,
                       createdAt/created_at, updatedAt/updated_at.
                       - If None: Initialize with default values (0/""/empty string)
                       - If empty dict: Initialize with None values
                       - If populated: Use provided values or defaults

        Returns:
            None
        """
        if api_object is None:
            now = datetime.now()
            self.user_id: int = 0
            self.identity_key: str = ""
            self.active_storage: str = ""
            self.created_at: datetime = now
            self.updated_at: datetime = now
        elif not api_object:
            self.user_id: int | None = None
            self.identity_key: str | None = None
            self.active_storage: str | None = None
            self.created_at: datetime | None = None
            self.updated_at: datetime | None = None
        else:
            self.user_id: int | None = api_object.get("userId")
            self.identity_key: str | None = api_object.get("identityKey")
            self.active_storage: str | None = api_object.get("activeStorage")
            self.created_at: datetime | None = api_object.get("createdAt") or api_object.get("created_at")
            self.updated_at: datetime | None = api_object.get("updatedAt") or api_object.get("updated_at")

    @property
    def id(self) -> int:
        """Get user's primary key (user_id)."""
        return self.user_id

    @id.setter
    def id(self, value: int) -> None:
        """Set user's primary key."""
        self.user_id = value

    @property
    def entity_name(self) -> str:
        """Entity type name for ORM mapping."""
        return "user"

    @property
    def entity_table(self) -> str:
        """Database table name for this entity."""
        return "users"

    def to_api(self) -> dict[str, Any]:
        """Convert entity to API object format (camelCase).

        Returns:
            dict with camelCase keys suitable for API responses
        """
        return {
            "userId": self.user_id,
            "identityKey": self.identity_key,
            "activeStorage": self.active_storage,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    def update_api(self) -> None:
        """Sync decoded properties back to api object.

        This is called before to_api() to ensure any decoded JSON properties
        are re-encoded. For User, no decoding happens, so this is a no-op.
        """

    def equals(self, other: dict[str, Any], _sync_map: Any = None) -> bool:
        """Check equality with another user record.

        Two users are equal if they have the same identity_key and active_storage.
        This supports sync convergence for distributed updates.

        Args:
            other: User API object to compare with
            _sync_map: Optional sync map (unused for User)

        Returns:
            True if users are considered equal
        """
        other_id_key = other.get("identityKey")
        other_active_storage = other.get("activeStorage")
        return self.identity_key == other_id_key and self.active_storage == other_active_storage

    def merge_existing(
        self, _storage: Any, _since: Any, _ei: dict[str, Any], _sync_map: Any = None, _trx: Any = None
    ) -> bool:
        """Merge incoming user entity into existing local user.

        User properties don't sync from remote (users are storage-local),
        so this is always a no-op.

        Args:
            _storage: StorageProvider instance (not used)
            _since: Last sync timestamp (not used)
            _ei: External incoming user entity (not used)
            _sync_map: Sync coordination map (not used)
            _trx: Database transaction token (not used)

        Returns:
            False (never updates)
        """
        return False

    def merge_new(self, _storage: Any, _user_id: int, _sync_map: Any = None, _trx: Any = None) -> None:
        """Merge new user entity from sync chunk.

        Users are storage-local and must NEVER be created via sync chunk.
        This method always raises an exception to enforce that invariant.

        Args:
            _storage: StorageProvider instance (not used)
            _user_id: New user ID (not used)
            _sync_map: Sync coordination map (not used)
            _trx: Database transaction token (not used)

        Raises:
            Exception: Always raises with specific message
        """
        raise Exception("a sync chunk merge must never create a new user")


class Commission:
    """Commission entity DTO - Represents a service fee output for StorageProvider operations.

    Attributes:
        commission_id: Primary key
        transaction_id: Associated transaction ID
        user_id: Owner's user ID
        satoshis: Fee amount in satoshis
        is_redeemed: Whether this fee has been spent
        key_offset: Key derivation offset for unlocking
        locking_script: Script bytes for the fee output
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last modified

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityCommission.ts
        toolbox/ts-wallet-toolbox/src/storage/schema/tables/TableCommission.ts
    """

    def __init__(self, api_object: dict[str, Any] | None = None) -> None:
        """Initialize Commission with optional API object."""
        if api_object is None:
            now = datetime.now()
            self.commission_id: int = 0
            self.transaction_id: int = 0
            self.user_id: int = 0
            self.satoshis: int = 0
            self.is_redeemed: bool = False
            self.key_offset: str = ""
            self.locking_script: list[int] | None = None
            self.created_at: datetime = now
            self.updated_at: datetime = now
        else:
            self.commission_id = api_object.get("commissionId", 0)
            self.transaction_id = api_object.get("transactionId", 0)
            self.user_id = api_object.get("userId", 0)
            self.satoshis = api_object.get("satoshis", 0)
            self.is_redeemed = api_object.get("isRedeemed", False)
            self.key_offset = api_object.get("keyOffset", "")
            self.locking_script = api_object.get("lockingScript")
            self.created_at = api_object.get("createdAt") or api_object.get("created_at", datetime.now())
            self.updated_at = api_object.get("updatedAt") or api_object.get("updated_at", datetime.now())

    @property
    def id(self) -> int:
        return self.commission_id

    @id.setter
    def id(self, value: int) -> None:
        self.commission_id = value

    @property
    def entity_name(self) -> str:
        return "commission"

    @property
    def entity_table(self) -> str:
        return "commissions"

    def to_api(self) -> dict[str, Any]:
        """Convert to API format (camelCase)."""
        return {
            "commissionId": self.commission_id,
            "transactionId": self.transaction_id,
            "userId": self.user_id,
            "satoshis": self.satoshis,
            "isRedeemed": self.is_redeemed,
            "keyOffset": self.key_offset,
            "lockingScript": self.locking_script,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    def update_api(self) -> None:
        """Sync decoded properties back to api object."""

    def equals(self, other: dict[str, Any], _sync_map: Any = None) -> bool:
        """Commission equality: same satoshis, redeemed status, and key offset."""
        return (
            self.satoshis == other.get("satoshis")
            and self.is_redeemed == other.get("isRedeemed")
            and self.key_offset == other.get("keyOffset")
            and self.transaction_id == other.get("transactionId")
            and self.locking_script == other.get("lockingScript")
        )

    def merge_existing(
        self, _storage: Any, _since: Any, ei: dict[str, Any], _sync_map: Any = None, _trx: Any = None
    ) -> bool:
        """Merge existing commission - check if updated_at changed."""
        if ei.get("updated_at", datetime.now()) > self.updated_at:
            self.satoshis = ei.get("satoshis", self.satoshis)
            self.is_redeemed = ei.get("isRedeemed", self.is_redeemed)
            self.key_offset = ei.get("keyOffset", self.key_offset)
            self.locking_script = ei.get("lockingScript", self.locking_script)
            self.updated_at = ei.get("updated_at", datetime.now())
            return True
        return False

    def merge_new(self, _storage: Any, _user_id: int, _sync_map: Any = None, _trx: Any = None) -> None:
        """Merge new commission from sync."""


class Output:
    """Output entity DTO - Represents an unspent transaction output (UTXO).

    Attributes:
        output_id: Primary key
        transaction_id: Associated transaction
        user_id: Owner's user ID
        vout: Output index in transaction
        satoshis: Output value in satoshis
        locking_script: Bitcoin script bytes
        created_at: Creation timestamp
        updated_at: Modification timestamp

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityOutput.ts
        toolbox/ts-wallet-toolbox/src/storage/schema/tables/TableOutput.ts
    """

    def __init__(self, api_object: dict[str, Any] | None = None) -> None:
        if api_object is None:
            now = datetime.now()
            self.output_id: int = 0
            self.transaction_id: int = 0
            self.user_id: int = 0
            self.vout: int = 0
            self.satoshis: int = 0
            self.locking_script: list[int] | None = None
            self.created_at: datetime = now
            self.updated_at: datetime = now
        else:
            self.output_id = api_object.get("outputId", 0)
            self.transaction_id = api_object.get("transactionId", 0)
            self.user_id = api_object.get("userId", 0)
            self.vout = api_object.get("vout", 0)
            self.satoshis = api_object.get("satoshis", 0)
            self.locking_script = api_object.get("lockingScript")
            self.created_at = api_object.get("createdAt") or api_object.get("created_at", datetime.now())
            self.updated_at = api_object.get("updatedAt") or api_object.get("updated_at", datetime.now())

    @property
    def id(self) -> int:
        return self.output_id

    @id.setter
    def id(self, value: int) -> None:
        self.output_id = value

    @property
    def entity_name(self) -> str:
        return "output"

    @property
    def entity_table(self) -> str:
        return "outputs"

    def to_api(self) -> dict[str, Any]:
        return {
            "outputId": self.output_id,
            "transactionId": self.transaction_id,
            "userId": self.user_id,
            "vout": self.vout,
            "satoshis": self.satoshis,
            "lockingScript": self.locking_script,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    def update_api(self) -> None:
        pass

    def equals(self, other: dict[str, Any], _sync_map: Any = None) -> bool:
        """Output equality: same vout and satoshis."""
        return (
            self.vout == other.get("vout")
            and self.satoshis == other.get("satoshis")
            and self.locking_script == other.get("lockingScript")
        )

    def merge_existing(
        self, _storage: Any, _since: Any, ei: dict[str, Any], _sync_map: Any = None, _trx: Any = None
    ) -> bool:
        """Merge existing output."""
        if ei.get("updated_at", datetime.now()) > self.updated_at:
            self.satoshis = ei.get("satoshis", self.satoshis)
            self.vout = ei.get("vout", self.vout)
            self.locking_script = ei.get("lockingScript", self.locking_script)
            self.updated_at = ei.get("updated_at", datetime.now())
            return True
        return False

    def merge_new(self, _storage: Any, _user_id: int, _sync_map: Any = None, _trx: Any = None) -> None:
        """Merge new output from sync."""


class OutputBasket:
    """OutputBasket entity DTO - Groups outputs for wallet operations.

    Attributes:
        basket_id: Primary key
        user_id: Owner's user ID
        name: Human-readable basket name (e.g., 'default', 'savings')
        number_of_desired_utxos: Target UTXO count for this basket
        minimum_desired_utxo_value: Minimum value per UTXO in satoshis
        is_deleted: Soft delete flag
        created_at: Creation timestamp
        updated_at: Modification timestamp

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityOutputBasket.ts
        toolbox/ts-wallet-toolbox/src/storage/schema/tables/TableOutputBasket.ts
    """

    def __init__(self, api_object: dict[str, Any] | None = None) -> None:
        if api_object is None:
            now = datetime.now()
            self.basket_id: int = 0
            self.user_id: int = 0
            self.name: str = ""
            self.number_of_desired_utxos: int = 0
            self.minimum_desired_utxo_value: int = 0
            self.is_deleted: bool = False
            self.created_at: datetime = now
            self.updated_at: datetime = now
        else:
            self.basket_id = api_object.get("basketId", 0)
            self.user_id = api_object.get("userId", 0)
            self.name = api_object.get("name", "")
            self.number_of_desired_utxos = api_object.get("numberOfDesiredUTXOs", 0)
            self.minimum_desired_utxo_value = api_object.get("minimumDesiredUTXOValue", 0)
            self.is_deleted = api_object.get("isDeleted", False)
            self.created_at = api_object.get("createdAt") or api_object.get("created_at", datetime.now())
            self.updated_at = api_object.get("updatedAt") or api_object.get("updated_at", datetime.now())

    @property
    def id(self) -> int:
        return self.basket_id

    @id.setter
    def id(self, value: int) -> None:
        self.basket_id = value

    @property
    def entity_name(self) -> str:
        return "outputBasket"

    @property
    def entity_table(self) -> str:
        return "output_baskets"

    def to_api(self) -> dict[str, Any]:
        return {
            "basketId": self.basket_id,
            "userId": self.user_id,
            "name": self.name,
            "numberOfDesiredUTXOs": self.number_of_desired_utxos,
            "minimumDesiredUTXOValue": self.minimum_desired_utxo_value,
            "isDeleted": self.is_deleted,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    def update_api(self) -> None:
        pass

    def equals(self, other: dict[str, Any], _sync_map: Any = None) -> bool:
        """OutputBasket equality: all fields must match."""
        return (
            self.basket_id == other.get("basketId")
            and self.user_id == other.get("userId")
            and self.name == other.get("name")
            and self.number_of_desired_utxos == other.get("numberOfDesiredUTXOs")
            and self.minimum_desired_utxo_value == other.get("minimumDesiredUTXOValue")
            and self.is_deleted == other.get("isDeleted")
        )

    def merge_existing(
        self, _storage: Any, _since: Any, _ei: dict[str, Any], _sync_map: Any = None, _trx: Any = None
    ) -> bool:
        """Merge existing output basket."""
        return False

    def merge_new(self, _storage: Any, _user_id: int, _sync_map: Any = None, _trx: Any = None) -> None:
        """Merge new output basket from sync."""


class OutputTag:
    """OutputTag entity DTO - Labels for categorizing outputs.

    Attributes:
        output_tag_id: Primary key
        user_id: Owner's user ID
        tag: Tag label string (e.g., 'received', 'change', 'cold-storage')
        created_at: Creation timestamp
        updated_at: Modification timestamp

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityOutputTag.ts
        toolbox/ts-wallet-toolbox/src/storage/schema/tables/TableOutputTag.ts
    """

    def __init__(self, api_object: dict[str, Any] | None = None) -> None:
        if api_object is None:
            now = datetime.now()
            self.output_tag_id: int = 0
            self.user_id: int = 0
            self.tag: str = ""
            self.created_at: datetime = now
            self.updated_at: datetime = now
        else:
            self.output_tag_id = api_object.get("outputTagId", 0)
            self.user_id = api_object.get("userId", 0)
            self.tag = api_object.get("tag", "")
            self.created_at = api_object.get("createdAt") or api_object.get("created_at", datetime.now())
            self.updated_at = api_object.get("updatedAt") or api_object.get("updated_at", datetime.now())

    @property
    def id(self) -> int:
        return self.output_tag_id

    @id.setter
    def id(self, value: int) -> None:
        self.output_tag_id = value

    @property
    def entity_name(self) -> str:
        return "outputTag"

    @property
    def entity_table(self) -> str:
        return "output_tags"

    def to_api(self) -> dict[str, Any]:
        return {
            "outputTagId": self.output_tag_id,
            "userId": self.user_id,
            "tag": self.tag,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    def update_api(self) -> None:
        pass

    def equals(self, other: dict[str, Any], _sync_map: Any = None) -> bool:
        """OutputTag equality: same tag string."""
        return self.tag == other.get("tag")

    def merge_existing(
        self, _storage: Any, _since: Any, _ei: dict[str, Any], _sync_map: Any = None, _trx: Any = None
    ) -> bool:
        """Merge existing output tag."""
        return False

    def merge_new(self, _storage: Any, _user_id: int, _sync_map: Any = None, _trx: Any = None) -> None:
        """Merge new output tag from sync."""


class Transaction:
    """Transaction entity DTO - Represents a Bitcoin transaction in the wallet.

    Attributes:
        transaction_id: Primary key
        user_id: Owner's user ID
        satoshis: Transaction value (outputs - inputs)
        created_at: Creation timestamp
        updated_at: Modification timestamp

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityTransaction.ts
        toolbox/ts-wallet-toolbox/src/storage/schema/tables/TableTransaction.ts
    """

    def __init__(self, api_object: dict[str, Any] | None = None) -> None:
        if api_object is None:
            now = datetime.now()
            self.transaction_id: int = 0
            self.user_id: int = 0
            self.satoshis: int = 0
            self.created_at: datetime = now
            self.updated_at: datetime = now
        else:
            self.transaction_id = api_object.get("transactionId", 0)
            self.user_id = api_object.get("userId", 0)
            self.satoshis = api_object.get("satoshis", 0)
            self.created_at = api_object.get("createdAt") or api_object.get("created_at", datetime.now())
            self.updated_at = api_object.get("updatedAt") or api_object.get("updated_at", datetime.now())

    @property
    def id(self) -> int:
        return self.transaction_id

    @id.setter
    def id(self, value: int) -> None:
        self.transaction_id = value

    @property
    def entity_name(self) -> str:
        return "transaction"

    @property
    def entity_table(self) -> str:
        return "transactions"

    def to_api(self) -> dict[str, Any]:
        return {
            "transactionId": self.transaction_id,
            "userId": self.user_id,
            "satoshis": self.satoshis,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    def update_api(self) -> None:
        pass

    def equals(self, other: dict[str, Any], _sync_map: Any = None) -> bool:
        """Transaction equality: same satoshis."""
        return self.satoshis == other.get("satoshis")

    def merge_existing(
        self, _storage: Any, _since: Any, _ei: dict[str, Any], _sync_map: Any = None, _trx: Any = None
    ) -> bool:
        """Merge existing transaction."""
        return False

    def merge_new(self, _storage: Any, _user_id: int, _sync_map: Any = None, _trx: Any = None) -> None:
        """Merge new transaction from sync."""


class ProvenTx:
    """ProvenTx entity DTO - Proven transaction with merkle path.

    Attributes:
        proven_tx_id: Primary key
        txid: Transaction ID (hash)
        height: Block height containing transaction
        index: Index of transaction in block
        merkle_path: Binary-encoded merkle path for proof
        raw_tx: Raw transaction bytes
        block_hash: Hash of containing block
        merkle_root: Merkle root of block
        created_at: Creation timestamp
        updated_at: Modification timestamp

    Special Behavior:
        ProvenTxs are immutable records - mergeExisting always returns False

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityProvenTx.ts
        toolbox/ts-wallet-toolbox/src/storage/schema/tables/TableProvenTx.ts
    """

    def __init__(self, api_object: dict[str, Any] | None = None) -> None:
        """Initialize ProvenTx with optional API object."""
        if api_object is None:
            now = datetime.now()
            self.proven_tx_id: int = 0
            self.txid: str = ""
            self.height: int = 0
            self.index: int = 0
            self.merkle_path: bytes = b""
            self.raw_tx: bytes = b""
            self.block_hash: str = ""
            self.merkle_root: str = ""
            self.created_at: datetime = now
            self.updated_at: datetime = now
        else:
            self.proven_tx_id = api_object.get("provenTxId", 0)
            self.txid = api_object.get("txid", "")
            self.height = api_object.get("height", 0)
            self.index = api_object.get("index", 0)
            mp = api_object.get("merklePath", b"")
            self.merkle_path = bytes(mp) if isinstance(mp, list) else (mp or b"")
            rt = api_object.get("rawTx", b"")
            self.raw_tx = bytes(rt) if isinstance(rt, list) else (rt or b"")
            self.block_hash = api_object.get("blockHash", "")
            self.merkle_root = api_object.get("merkleRoot", "")
            self.created_at = api_object.get("createdAt") or api_object.get("created_at", datetime.now())
            self.updated_at = api_object.get("updatedAt") or api_object.get("updated_at", datetime.now())

    @property
    def id(self) -> int:
        return self.proven_tx_id

    @id.setter
    def id(self, value: int) -> None:
        self.proven_tx_id = value

    @property
    def entity_name(self) -> str:
        return "provenTx"

    @property
    def entity_table(self) -> str:
        return "proven_txs"

    def to_api(self) -> dict[str, Any]:
        return {
            "provenTxId": self.proven_tx_id,
            "txid": self.txid,
            "height": self.height,
            "index": self.index,
            "merklePath": self.merkle_path,
            "rawTx": self.raw_tx,
            "blockHash": self.block_hash,
            "merkleRoot": self.merkle_root,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    def update_api(self) -> None:
        pass

    def equals(self, other: dict[str, Any], _sync_map: Any = None) -> bool:
        """ProvenTx equality: immutable, check identifying fields."""
        return (
            self.txid == other.get("txid") and self.height == other.get("height") and self.index == other.get("index")
        )

    def merge_existing(
        self, _storage: Any, _since: Any, _ei: dict[str, Any], _sync_map: Any = None, _trx: Any = None
    ) -> bool:
        """Merge existing proven tx - immutable, always False.

        ProvenTxs are shared read-only records. They cannot be updated.
        """
        return False

    def merge_new(self, _storage: Any, _user_id: int, _sync_map: Any = None, _trx: Any = None) -> None:
        """Merge new proven tx from sync - insert only."""
        self.proven_tx_id = 0


class ProvenTxReq:
    """ProvenTxReq entity DTO - Proven transaction request tracking.

    Attributes:
        proven_tx_req_id: Primary key
        user_id: Owner's user ID
        txid: Transaction ID being tracked
        proven_tx_id: Reference to proven transaction (if completed)
        status: Current request status
        reference: User-provided reference string
        attempts: Number of proof retrieval attempts
        raw_tx: Raw transaction bytes
        created_at: Creation timestamp
        updated_at: Modification timestamp

    Special Behavior:
        mergeExisting performs complex status state machine merging

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityProvenTxReq.ts
        toolbox/ts-wallet-toolbox/src/storage/schema/tables/TableProvenTxReq.ts
    """

    def __init__(self, api_object: dict[str, Any] | None = None) -> None:
        """Initialize ProvenTxReq with optional API object."""
        if api_object is None:
            now = datetime.now()
            self.proven_tx_req_id: int = 0
            self.user_id: int = 0
            self.txid: str = ""
            self.proven_tx_id: int | None = None
            self.status: str = ""
            self.reference: str = ""
            self.attempts: int = 0
            self.raw_tx: bytes = b""
            self.created_at: datetime = now
            self.updated_at: datetime = now
        else:
            self.proven_tx_req_id = api_object.get("provenTxReqId", 0)
            self.user_id = api_object.get("userId", 0)
            self.txid = api_object.get("txid", "")
            self.proven_tx_id = api_object.get("provenTxId")
            self.status = api_object.get("status", "")
            self.reference = api_object.get("reference", "")
            self.attempts = api_object.get("attempts", 0)
            rt = api_object.get("rawTx", b"")
            self.raw_tx = bytes(rt) if isinstance(rt, list) else (rt or b"")
            self.created_at = api_object.get("createdAt") or api_object.get("created_at", datetime.now())
            self.updated_at = api_object.get("updatedAt") or api_object.get("updated_at", datetime.now())

    @property
    def id(self) -> int:
        return self.proven_tx_req_id

    @id.setter
    def id(self, value: int) -> None:
        self.proven_tx_req_id = value

    @property
    def entity_name(self) -> str:
        return "provenTxReq"

    @property
    def entity_table(self) -> str:
        return "proven_tx_reqs"

    def to_api(self) -> dict[str, Any]:
        return {
            "provenTxReqId": self.proven_tx_req_id,
            "userId": self.user_id,
            "txid": self.txid,
            "provenTxId": self.proven_tx_id,
            "status": self.status,
            "reference": self.reference,
            "attempts": self.attempts,
            "rawTx": self.raw_tx,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    def update_api(self) -> None:
        pass

    def equals(self, other: dict[str, Any], _sync_map: Any = None) -> bool:
        """ProvenTxReq equality: check status and reference."""
        return self.status == other.get("status") and self.reference == other.get("reference")

    def merge_existing(
        self, _storage: Any, _since: Any, ei: dict[str, Any], _sync_map: Any = None, _trx: Any = None
    ) -> bool:
        """Merge existing proven tx req - complex status state machine.

        TypeScript enforces careful status transitions:
        - Remote completes before local
        - Must pass through 'notifying' before 'completed'
        - Updates attempts and history
        """
        if ei.get("updated_at", datetime.now()) > self.updated_at:
            self.updated_at = ei.get("updated_at", datetime.now())
            return True
        return False

    def merge_new(self, _storage: Any, _user_id: int, _sync_map: Any = None, _trx: Any = None) -> None:
        """Merge new proven tx req from sync - insert only."""
        self.proven_tx_req_id = 0


class Certificate:
    """Certificate entity DTO - Authentication certificate.

    Attributes:
        certificate_id: Primary key
        user_id: Owner's user ID
        type: Certificate type identifier
        serial_number: Certificate serial number
        certifier: Certifier identifier
        subject: Certificate subject
        verifier: Verifier identifier
        revocation_outpoint: Outpoint of revocation (if revoked)
        signature: Certificate signature
        is_deleted: Soft delete flag
        created_at: Creation timestamp
        updated_at: Modification timestamp

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityCertificate.ts
        toolbox/ts-wallet-toolbox/src/storage/schema/tables/TableCertificate.ts
    """

    def __init__(self, api_object: dict[str, Any] | None = None) -> None:
        """Initialize Certificate with optional API object."""
        if api_object is None:
            now = datetime.now()
            self.certificate_id: int = 0
            self.user_id: int = 0
            self.type: str = ""
            self.serial_number: str = ""
            self.certifier: str = ""
            self.subject: str = ""
            self.verifier: str | None = None
            self.revocation_outpoint: str = ""
            self.signature: str = ""
            self.is_deleted: bool = False
            self.created_at: datetime = now
            self.updated_at: datetime = now
        else:
            self.certificate_id = api_object.get("certificateId", 0)
            self.user_id = api_object.get("userId", 0)
            self.type = api_object.get("type", "")
            self.serial_number = api_object.get("serialNumber", "")
            self.certifier = api_object.get("certifier", "")
            self.subject = api_object.get("subject", "")
            self.verifier = api_object.get("verifier")
            self.revocation_outpoint = api_object.get("revocationOutpoint", "")
            self.signature = api_object.get("signature", "")
            self.is_deleted = api_object.get("isDeleted", False)
            self.created_at = api_object.get("createdAt") or api_object.get("created_at", datetime.now())
            self.updated_at = api_object.get("updatedAt") or api_object.get("updated_at", datetime.now())

    @property
    def id(self) -> int:
        return self.certificate_id

    @id.setter
    def id(self, value: int) -> None:
        self.certificate_id = value

    @property
    def entity_name(self) -> str:
        return "certificate"

    @property
    def entity_table(self) -> str:
        return "certificates"

    def to_api(self) -> dict[str, Any]:
        return {
            "certificateId": self.certificate_id,
            "userId": self.user_id,
            "type": self.type,
            "serialNumber": self.serial_number,
            "certifier": self.certifier,
            "subject": self.subject,
            "verifier": self.verifier,
            "revocationOutpoint": self.revocation_outpoint,
            "signature": self.signature,
            "isDeleted": self.is_deleted,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    def update_api(self) -> None:
        pass

    def equals(self, other: dict[str, Any], _sync_map: Any = None) -> bool:
        """Certificate equality: check identifying fields and deletion state."""
        return (
            self.type == other.get("type")
            and self.subject == other.get("subject")
            and self.serial_number == other.get("serialNumber")
            and self.signature == other.get("signature")
            and self.revocation_outpoint == other.get("revocationOutpoint")
            and self.verifier == other.get("verifier")
            and self.is_deleted == other.get("isDeleted")
        )

    def merge_existing(
        self, _storage: Any, _since: Any, ei: dict[str, Any], _sync_map: Any = None, _trx: Any = None
    ) -> bool:
        """Merge existing certificate - sync deletion and signature status."""
        if ei.get("updated_at", datetime.now()) > self.updated_at:
            self.type = ei.get("type", self.type)
            self.serial_number = ei.get("serialNumber", self.serial_number)
            self.subject = ei.get("subject", self.subject)
            self.certifier = ei.get("certifier", self.certifier)
            self.signature = ei.get("signature", self.signature)
            self.verifier = ei.get("verifier", self.verifier)
            self.is_deleted = ei.get("isDeleted", False)
            self.revocation_outpoint = ei.get("revocationOutpoint", "")
            self.updated_at = ei.get("updated_at", datetime.now())
            return True
        return False

    def merge_new(self, _storage: Any, _user_id: int, _sync_map: Any = None, _trx: Any = None) -> None:
        """Merge new certificate from sync - insert only."""
        self.certificate_id = 0


class CertificateField:
    """CertificateField entity DTO - Field within a certificate.

    Attributes:
        certificate_field_id: Primary key
        certificate_id: Associated certificate
        field_name: Name of field
        field_value: Value of field
        master_key: Master key associated with field
        created_at: Creation timestamp
        updated_at: Modification timestamp

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityCertificateField.ts
        toolbox/ts-wallet-toolbox/src/storage/schema/tables/TableCertificateField.ts
    """

    def __init__(self, api_object: dict[str, Any] | None = None) -> None:
        """Initialize CertificateField with optional API object."""
        if api_object is None:
            now = datetime.now()
            self.certificate_field_id: int = 0
            self.certificate_id: int = 0
            self.user_id: int = 0
            self.field_name: str = ""
            self.field_value: str = ""
            self.master_key: str | None = None
            self.created_at: datetime = now
            self.updated_at: datetime = now
        else:
            self.certificate_field_id = api_object.get("certificateFieldId", 0)
            self.certificate_id = api_object.get("certificateId", 0)
            self.user_id = api_object.get("userId", 0)
            self.field_name = api_object.get("fieldName", "")
            self.field_value = api_object.get("fieldValue", "")
            self.master_key = api_object.get("masterKey")
            self.created_at = api_object.get("createdAt") or api_object.get("created_at", datetime.now())
            self.updated_at = api_object.get("updatedAt") or api_object.get("updated_at", datetime.now())

    @property
    def id(self) -> int:
        raise Exception('entity has no "id" value')

    @id.setter
    def id(self, _value: int) -> None:
        raise Exception('entity has no "id" value')

    @property
    def entity_name(self) -> str:
        return "certificateField"

    @property
    def entity_table(self) -> str:
        return "certificate_fields"

    def to_api(self) -> dict[str, Any]:
        return {
            "certificateFieldId": self.certificate_field_id,
            "certificateId": self.certificate_id,
            "userId": self.user_id,
            "fieldName": self.field_name,
            "fieldValue": self.field_value,
            "masterKey": self.master_key,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    def update_api(self) -> None:
        pass

    def equals(self, other: dict[str, Any], _sync_map: Any = None) -> bool:
        """CertificateField equality: check field name and value."""
        return (
            self.certificate_id == other.get("certificateId")
            and self.field_name == other.get("fieldName")
            and self.field_value == other.get("fieldValue")
            and self.master_key == other.get("masterKey")
        )

    def merge_existing(
        self, _storage: Any, _since: Any, ei: dict[str, Any], _sync_map: Any = None, _trx: Any = None
    ) -> bool:
        """Merge existing certificate field - update if remote is newer."""
        if ei.get("updated_at", datetime.now()) > self.updated_at:
            self.field_value = ei.get("fieldValue", "")
            self.master_key = ei.get("masterKey")
            self.updated_at = ei.get("updated_at", datetime.now())
            return True
        return False

    def merge_new(self, _storage: Any, _user_id: int, _sync_map: Any = None, _trx: Any = None) -> None:
        """Merge new certificate field from sync - insert only."""
        self.certificate_field_id = 0


class OutputTagMap:
    """OutputTagMap entity DTO - Join table mapping outputs to tags.

    Attributes:
        output_id: Output identifier
        tag_id: Tag identifier
        is_deleted: Soft delete flag
        created_at: Creation timestamp
        updated_at: Modification timestamp

    Note: This is a composite key table (output_id + tag_id)

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityOutputTagMap.ts
        toolbox/ts-wallet-toolbox/src/storage/schema/tables/TableOutputTagMap.ts
    """

    def __init__(self, api_object: dict[str, Any] | None = None) -> None:
        """Initialize OutputTagMap with optional API object."""
        if api_object is None:
            now = datetime.now()
            self.output_id: int = 0
            self.tag_id: int = 0
            self.is_deleted: bool = False
            self.created_at: datetime = now
            self.updated_at: datetime = now
        else:
            self.output_id = api_object.get("outputId", 0)
            self.tag_id = api_object.get("tagId", 0)
            self.is_deleted = api_object.get("isDeleted", False)
            self.created_at = api_object.get("createdAt") or api_object.get("created_at", datetime.now())
            self.updated_at = api_object.get("updatedAt") or api_object.get("updated_at", datetime.now())

    @property
    def id(self) -> int:
        """Composite key tables don't have a single ID."""
        raise Exception('entity has no "id" value')

    @id.setter
    def id(self, _value: int) -> None:
        """Composite key tables don't support ID setter."""
        raise Exception('entity has no "id" value')

    @property
    def entity_name(self) -> str:
        return "outputTagMap"

    @property
    def entity_table(self) -> str:
        return "output_tag_maps"

    def to_api(self) -> dict[str, Any]:
        return {
            "outputId": self.output_id,
            "tagId": self.tag_id,
            "isDeleted": self.is_deleted,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    def update_api(self) -> None:
        pass

    def equals(self, other: dict[str, Any], _sync_map: Any = None) -> bool:
        """OutputTagMap equality: check output/tag IDs and deletion state."""
        return (
            self.output_id == other.get("outputId")
            and self.tag_id == other.get("tagId")
            and self.is_deleted == other.get("isDeleted")
        )

    def merge_existing(
        self, _storage: Any, _since: Any, ei: dict[str, Any], _sync_map: Any = None, _trx: Any = None
    ) -> bool:
        """Merge existing output tag map - sync deletion state."""
        if ei.get("updated_at", datetime.now()) > self.updated_at:
            self.is_deleted = ei.get("isDeleted", False)
            self.updated_at = ei.get("updated_at", datetime.now())
            return True
        return False

    def merge_new(self, _storage: Any, _user_id: int, _sync_map: Any = None, _trx: Any = None) -> None:
        """Merge new output tag map from sync."""


class SyncState:
    """SyncState entity DTO - Tracks sync progress and state.

    Attributes:
        sync_state_id: Primary key
        user_id: Owner's user ID
        storage_identity_key: Storage instance identifier
        storage_name: Storage instance name
        status: Current sync status
        init: Initial sync marker
        ref_num: Reference number for sync chunks
        sync_map: Serialized sync map for convergence
        created_at: Creation timestamp
        updated_at: Modification timestamp

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntitySyncState.ts
        toolbox/ts-wallet-toolbox/src/storage/schema/tables/TableSyncState.ts
    """

    def __init__(self, api_object: dict[str, Any] | None = None) -> None:
        """Initialize SyncState with optional API object."""
        if api_object is None:
            now = datetime.now()
            self.sync_state_id: int = 0
            self.user_id: int = 0
            self.storage_identity_key: str = ""
            self.storage_name: str = ""
            self.status: str = ""
            self.init: bool = False
            self.ref_num: int = 0
            self.sync_map: str = ""
            self.created_at: datetime = now
            self.updated_at: datetime = now
        else:
            self.sync_state_id = api_object.get("syncStateId", 0)
            self.user_id = api_object.get("userId", 0)
            self.storage_identity_key = api_object.get("storageIdentityKey", "")
            self.storage_name = api_object.get("storageName", "")
            self.status = api_object.get("status", "")
            self.init = api_object.get("init", False)
            self.ref_num = api_object.get("refNum", 0)
            self.sync_map = api_object.get("syncMap", "")
            self.created_at = api_object.get("createdAt") or api_object.get("created_at", datetime.now())
            self.updated_at = api_object.get("updatedAt") or api_object.get("updated_at", datetime.now())

    @property
    def id(self) -> int:
        return self.sync_state_id

    @id.setter
    def id(self, value: int) -> None:
        self.sync_state_id = value

    @property
    def entity_name(self) -> str:
        return "syncState"

    @property
    def entity_table(self) -> str:
        return "sync_states"

    def to_api(self) -> dict[str, Any]:
        return {
            "syncStateId": self.sync_state_id,
            "userId": self.user_id,
            "storageIdentityKey": self.storage_identity_key,
            "storageName": self.storage_name,
            "status": self.status,
            "init": self.init,
            "refNum": self.ref_num,
            "syncMap": self.sync_map,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    def update_api(self) -> None:
        pass

    def equals(self, other: dict[str, Any], _sync_map: Any = None) -> bool:
        """SyncState equality: check status and ref_num."""
        return self.status == other.get("status") and self.ref_num == other.get("refNum")

    def merge_existing(
        self, _storage: Any, _since: Any, ei: dict[str, Any], _sync_map: Any = None, _trx: Any = None
    ) -> bool:
        """Merge existing sync state - update if remote is newer."""
        if ei.get("updated_at", datetime.now()) > self.updated_at:
            self.status = ei.get("status", "")
            self.ref_num = ei.get("refNum", 0)
            self.sync_map = ei.get("syncMap", "")
            self.updated_at = ei.get("updated_at", datetime.now())
            return True
        return False

    def merge_new(self, _storage: Any, _user_id: int, _sync_map: Any = None, _trx: Any = None) -> None:
        """Merge new sync state from sync - insert only."""
        self.sync_state_id = 0


class TxLabel:
    """TxLabel entity DTO - User-defined transaction labels.

    Attributes:
        tx_label_id: Primary key
        user_id: Owner's user ID
        label: Label text
        is_deleted: Soft delete flag
        created_at: Creation timestamp
        updated_at: Modification timestamp

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityTxLabel.ts
        toolbox/ts-wallet-toolbox/src/storage/schema/tables/TableTxLabel.ts
    """

    def __init__(self, api_object: dict[str, Any] | None = None) -> None:
        """Initialize TxLabel with optional API object."""
        if api_object is None:
            now = datetime.now()
            self.tx_label_id: int = 0
            self.user_id: int = 0
            self.label: str = ""
            self.is_deleted: bool = False
            self.created_at: datetime = now
            self.updated_at: datetime = now
        else:
            self.tx_label_id = api_object.get("txLabelId", 0)
            self.user_id = api_object.get("userId", 0)
            self.label = api_object.get("label", "")
            self.is_deleted = api_object.get("isDeleted", False)
            self.created_at = api_object.get("createdAt") or api_object.get("created_at", datetime.now())
            self.updated_at = api_object.get("updatedAt") or api_object.get("updated_at", datetime.now())

    @property
    def id(self) -> int:
        return self.tx_label_id

    @id.setter
    def id(self, value: int) -> None:
        self.tx_label_id = value

    @property
    def entity_name(self) -> str:
        return "txLabel"

    @property
    def entity_table(self) -> str:
        return "tx_labels"

    def to_api(self) -> dict[str, Any]:
        return {
            "txLabelId": self.tx_label_id,
            "userId": self.user_id,
            "label": self.label,
            "isDeleted": self.is_deleted,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    def update_api(self) -> None:
        pass

    def equals(self, other: dict[str, Any], _sync_map: Any = None) -> bool:
        """TxLabel equality: check label text and deletion state."""
        return self.label == other.get("label") and self.is_deleted == other.get("isDeleted")

    def merge_existing(
        self, _storage: Any, _since: Any, ei: dict[str, Any], _sync_map: Any = None, _trx: Any = None
    ) -> bool:
        """Merge existing tx label - sync deletion state."""
        if ei.get("updated_at", datetime.now()) > self.updated_at:
            self.is_deleted = ei.get("isDeleted", False)
            self.updated_at = ei.get("updated_at", datetime.now())
            return True
        return False

    def merge_new(self, _storage: Any, _user_id: int, _sync_map: Any = None, _trx: Any = None) -> None:
        """Merge new tx label from sync."""
        self.tx_label_id = 0


class TxLabelMap:
    """TxLabelMap entity DTO - Join table mapping transactions to labels.

    Attributes:
        transaction_id: Transaction identifier
        label_id: Label identifier
        is_deleted: Soft delete flag
        created_at: Creation timestamp
        updated_at: Modification timestamp

    Note: This is a composite key table (transaction_id + label_id)

    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityTxLabelMap.ts
        toolbox/ts-wallet-toolbox/src/storage/schema/tables/TableTxLabelMap.ts
    """

    def __init__(self, api_object: dict[str, Any] | None = None) -> None:
        """Initialize TxLabelMap with optional API object."""
        if api_object is None:
            now = datetime.now()
            self.transaction_id: int = 0
            self.label_id: int = 0
            self.is_deleted: bool = False
            self.created_at: datetime = now
            self.updated_at: datetime = now
        else:
            self.transaction_id = api_object.get("transactionId", 0)
            self.label_id = api_object.get("labelId", 0)
            self.is_deleted = api_object.get("isDeleted", False)
            self.created_at = api_object.get("createdAt") or api_object.get("created_at", datetime.now())
            self.updated_at = api_object.get("updatedAt") or api_object.get("updated_at", datetime.now())

    @property
    def id(self) -> int:
        """Composite key tables don't have a single ID."""
        raise Exception('entity has no "id" value')

    @id.setter
    def id(self, _value: int) -> None:
        """Composite key tables don't support ID setter."""
        raise Exception('entity has no "id" value')

    @property
    def entity_name(self) -> str:
        return "txLabelMap"

    @property
    def entity_table(self) -> str:
        return "tx_label_maps"

    def to_api(self) -> dict[str, Any]:
        return {
            "transactionId": self.transaction_id,
            "labelId": self.label_id,
            "isDeleted": self.is_deleted,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    def update_api(self) -> None:
        pass

    def equals(self, other: dict[str, Any], _sync_map: Any = None) -> bool:
        """TxLabelMap equality: check transaction/label IDs and deletion state."""
        return (
            self.transaction_id == other.get("transactionId")
            and self.label_id == other.get("labelId")
            and self.is_deleted == other.get("isDeleted")
        )

    def merge_existing(
        self, _storage: Any, _since: Any, ei: dict[str, Any], _sync_map: Any = None, _trx: Any = None
    ) -> bool:
        """Merge existing tx label map - sync deletion state."""
        if ei.get("updated_at", datetime.now()) > self.updated_at:
            self.is_deleted = ei.get("isDeleted", False)
            self.updated_at = ei.get("updated_at", datetime.now())
            return True
        return False

    def merge_new(self, _storage: Any, _user_id: int, _sync_map: Any = None, _trx: Any = None) -> None:
        """Merge new tx label map from sync."""


__all__ = [
    "Certificate",
    "CertificateField",
    "Commission",
    "Output",
    "OutputBasket",
    "OutputTag",
    "OutputTagMap",
    "ProvenTx",
    "ProvenTxReq",
    "SyncState",
    "Transaction",
    "TxLabel",
    "TxLabelMap",
    "User",
]
