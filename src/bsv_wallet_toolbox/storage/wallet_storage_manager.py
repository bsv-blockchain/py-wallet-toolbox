"""Wallet Storage Manager for multi-storage synchronization.

Manages multiple storage providers (active + backups) and handles
synchronization between them.

Reference:
    wallet-toolbox/src/storage/WalletStorageManager.ts
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from ..errors import InvalidParameterError, WalletError

logger = logging.getLogger(__name__)


# Type definitions
class WalletStorageProvider(Protocol):
    """Protocol for wallet storage providers."""

    def is_storage_provider(self) -> bool: ...
    def make_available(self) -> dict[str, Any]: ...
    def get_settings(self) -> dict[str, Any]: ...
    def find_or_insert_user(self, identity_key: str) -> dict[str, Any]: ...
    def get_sync_chunk(self, args: dict[str, Any]) -> dict[str, Any]: ...
    def process_sync_chunk(self, args: dict[str, Any], chunk: dict[str, Any]) -> dict[str, Any]: ...
    def set_services(self, services: Any) -> None: ...
    def find_or_insert_sync_state_auth(
        self, auth: dict[str, Any], storage_identity_key: str, storage_name: str
    ) -> dict[str, Any]: ...


@dataclass
class AuthId:
    """Authentication ID container."""

    identity_key: str
    user_id: int | None = None
    is_active: bool = False


@dataclass
class TableSettings:
    """Storage settings table data."""

    storage_identity_key: str
    storage_name: str


@dataclass
class TableUser:
    """User table data."""

    user_id: int
    identity_key: str
    active_storage: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class ManagedStorage:
    """Wrapper for managed storage providers."""

    storage: Any  # WalletStorageProvider
    is_storage_provider: bool = False
    is_available: bool = False
    settings: TableSettings | None = None
    user: TableUser | None = None

    def __post_init__(self):
        if hasattr(self.storage, "is_storage_provider"):
            self.is_storage_provider = self.storage.is_storage_provider()


@dataclass
class SyncResult:
    """Result of a sync operation."""

    inserts: int = 0
    updates: int = 0
    log: str = ""


@dataclass
class EntitySyncMap:
    """Sync state for a single entity type."""

    entity_name: str
    count: int = 0
    max_updated_at: datetime | None = None
    id_map: dict[int, int] = field(default_factory=dict)


def create_sync_map() -> dict[str, EntitySyncMap]:
    """Create initial sync map with all entity types."""
    entity_names = [
        "provenTx",
        "outputBasket",
        "outputTag",
        "txLabel",
        "transaction",
        "output",
        "txLabelMap",
        "outputTagMap",
        "certificate",
        "certificateField",
        "commission",
        "provenTxReq",
    ]
    return {name: EntitySyncMap(entity_name=name) for name in entity_names}


class EntitySyncState:
    """Manages sync state between two storage providers.

    Reference:
        wallet-toolbox/src/storage/schema/entities/EntitySyncState.ts
    """

    def __init__(
        self,
        sync_state_id: int = 0,
        user_id: int = 0,
        storage_identity_key: str = "",
        storage_name: str = "",
        init: bool = False,
        ref_num: str = "",
        status: str = "unknown",
        when: datetime | None = None,
        sync_map: dict[str, EntitySyncMap] | None = None,
    ):
        self.sync_state_id = sync_state_id
        self.user_id = user_id
        self.storage_identity_key = storage_identity_key
        self.storage_name = storage_name
        self.init = init
        self.ref_num = ref_num
        self.status = status
        self.when = when
        self.sync_map = sync_map or create_sync_map()
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    @classmethod
    def from_storage(
        cls, storage: WalletStorageProvider, user_identity_key: str, remote_settings: dict[str, Any]
    ) -> "EntitySyncState":
        """Load or create sync state from storage.

        Args:
            storage: Storage provider to query
            user_identity_key: User's identity key
            remote_settings: Settings from remote storage

        Returns:
            EntitySyncState instance
        """
        # Get or create user
        user_result = storage.find_or_insert_user(user_identity_key)
        user = user_result.get("user", {})
        user_id = user.get("userId") or user.get("userId", 0)

        # Get or create sync state
        storage_identity_key = remote_settings.get("storageIdentityKey", "")
        storage_name = remote_settings.get("storageName", "")

        try:
            sync_result = storage.find_or_insert_sync_state_auth(
                {"userId": user_id, "identityKey": user_identity_key}, storage_identity_key, storage_name
            )
            sync_state = sync_result.get("syncState", {})
        except Exception:
            # If sync state doesn't exist, create a new one
            sync_state = {}

        return cls(
            sync_state_id=sync_state.get("syncStateId", 0),
            user_id=user_id,
            storage_identity_key=storage_identity_key,
            storage_name=storage_name,
            init=sync_state.get("init", False),
            ref_num=sync_state.get("refNum", ""),
            status=sync_state.get("status", "unknown"),
            when=sync_state.get("when"),
        )

    def make_request_sync_chunk_args(
        self,
        for_identity_key: str,
        for_storage_identity_key: str,
        max_rough_size: int = 10_000_000,
        max_items: int = 1000,
    ) -> dict[str, Any]:
        """Create arguments for getSyncChunk request.

        Args:
            for_identity_key: Target user identity key
            for_storage_identity_key: Target storage identity key
            max_rough_size: Max rough byte size
            max_items: Max items per chunk

        Returns:
            Dict with sync chunk request arguments
        """
        offsets = []
        for name in [
            "provenTx",
            "outputBasket",
            "outputTag",
            "txLabel",
            "transaction",
            "output",
            "txLabelMap",
            "outputTagMap",
            "certificate",
            "certificateField",
            "commission",
            "provenTxReq",
        ]:
            esm = self.sync_map.get(name, EntitySyncMap(entity_name=name))
            offsets.append({"name": esm.entity_name, "offset": esm.count})

        return {
            "identityKey": for_identity_key,
            "maxRoughSize": max_rough_size,
            "maxItems": max_items,
            "offsets": offsets,
            "since": self.when.isoformat() if self.when else None,
            "fromStorageIdentityKey": self.storage_identity_key,
            "toStorageIdentityKey": for_storage_identity_key,
        }

    @staticmethod
    def sync_chunk_summary(chunk: dict[str, Any]) -> str:
        """Generate a summary of sync chunk contents.

        Args:
            chunk: Sync chunk data

        Returns:
            Summary string
        """
        log = "SYNC CHUNK SUMMARY\n"
        log += f"  from storage: {chunk.get('fromStorageIdentityKey', '')}\n"
        log += f"  to storage: {chunk.get('toStorageIdentityKey', '')}\n"
        log += f"  for user: {chunk.get('userIdentityKey', '')}\n"

        if chunk.get("user"):
            log += f"  USER activeStorage {chunk['user'].get('activeStorage', '')}\n"

        for key, label in [
            ("provenTxs", "PROVEN_TXS"),
            ("provenTxReqs", "PROVEN_TX_REQS"),
            ("transactions", "TRANSACTIONS"),
            ("outputs", "OUTPUTS"),
        ]:
            items = chunk.get(key, [])
            if items:
                log += f"  {label}\n"
                for item in items[:5]:  # Show first 5
                    if key == "provenTxs":
                        log += f"    {item.get('provenTxId')} {item.get('txid')}\n"
                    elif key == "provenTxReqs":
                        log += f"    {item.get('provenTxReqId')} {item.get('txid')} {item.get('status')}\n"
                    elif key == "transactions":
                        log += f"    {item.get('transactionId')} {item.get('txid')} {item.get('status')}\n"
                    elif key == "outputs":
                        log += f"    {item.get('outputId')} {item.get('txid')}.{item.get('vout')}\n"
                if len(items) > 5:
                    log += f"    ... and {len(items) - 5} more\n"

        return log


class WalletStorageManager:
    """Manages multiple storage providers with synchronization support.

    Handles active storage and backup storage providers, with support for
    synchronizing data between them.

    Reference:
        wallet-toolbox/src/storage/WalletStorageManager.ts
    """

    def __init__(
        self,
        identity_key: str,
        active: WalletStorageProvider | None = None,
        backups: list[WalletStorageProvider] | None = None,
    ):
        """Initialize WalletStorageManager.

        Args:
            identity_key: User's identity key
            active: Optional active storage provider
            backups: Optional list of backup storage providers
        """
        self._stores: list[ManagedStorage] = []
        self._is_available = False
        self._active: ManagedStorage | None = None
        self._backups: list[ManagedStorage] = []
        self._conflicting_actives: list[ManagedStorage] = []
        self._auth_id = AuthId(identity_key=identity_key)
        self._services: Any | None = None

        # Add stores
        stores = list(backups or [])
        if active:
            stores.insert(0, active)
        self._stores = [ManagedStorage(storage=s) for s in stores]

    def is_storage_provider(self) -> bool:
        """Check if this manager is a storage provider."""
        return False

    def is_available(self) -> bool:
        """Check if storage is available."""
        return self._is_available

    @property
    def is_active_enabled(self) -> bool:
        """Check if active storage is enabled."""
        if not self._active or not self._active.settings or not self._active.user:
            return False
        return (
            self._active.settings.storage_identity_key == self._active.user.active_storage
            and len(self._conflicting_actives) == 0
        )

    def can_make_available(self) -> bool:
        """Check if storage can be made available."""
        return len(self._stores) > 0

    def make_available(self) -> dict[str, Any]:
        """Make storage available and return settings.

        Returns:
            Settings from the active storage
        """
        if self._is_available and self._active:
            return {
                "storageIdentityKey": self._active.settings.storage_identity_key if self._active.settings else "",
                "storageName": self._active.settings.storage_name if self._active.settings else "",
            }

        self._active = None
        self._backups = []
        self._conflicting_actives = []

        if len(self._stores) < 1:
            raise InvalidParameterError("active", "valid. Must add active storage provider to wallet.")

        backups: list[ManagedStorage] = []

        for _i, store in enumerate(self._stores):
            if not store.is_available or not store.settings or not store.user:
                # Make store available
                store.settings_dict = store.storage.make_available()
                store.settings = TableSettings(
                    storage_identity_key=store.settings_dict.get("storageIdentityKey", ""),
                    storage_name=store.settings_dict.get("storageName", ""),
                )

                user_result = store.storage.find_or_insert_user(self._auth_id.identity_key)
                user_data = user_result.get("user", {})
                store.user = TableUser(
                    user_id=user_data.get("userId") or user_data.get("userId", 0),
                    identity_key=user_data.get("identityKey") or user_data.get("identityKey", ""),
                    active_storage=user_data.get("activeStorage") or user_data.get("activeStorage"),
                )
                store.is_available = True

            if not self._active:
                self._active = store
            else:
                ua = store.user.active_storage if store.user else None
                si = store.settings.storage_identity_key if store.settings else ""
                if ua == si and not self.is_active_enabled:
                    backups.append(self._active)
                    self._active = store
                else:
                    backups.append(store)

        # Review backups, partition out conflicting actives
        if self._active and self._active.settings:
            si = self._active.settings.storage_identity_key
            for store in backups:
                if store.user and store.user.active_storage != si:
                    self._conflicting_actives.append(store)
                else:
                    self._backups.append(store)

        self._is_available = True
        if self._active and self._active.user:
            self._auth_id.user_id = self._active.user.user_id
            self._auth_id.is_active = self.is_active_enabled

        return {
            "storageIdentityKey": (
                self._active.settings.storage_identity_key if self._active and self._active.settings else ""
            ),
            "storageName": self._active.settings.storage_name if self._active and self._active.settings else "",
        }

    def get_auth(self, must_be_active: bool = False) -> AuthId:
        """Get authentication ID.

        Args:
            must_be_active: If True, raise error if not active

        Returns:
            AuthId instance
        """
        if not self.is_available():
            self.make_available()
        if must_be_active and not self._auth_id.is_active:
            raise WalletError("Storage is not active")
        return self._auth_id

    def get_active(self) -> WalletStorageProvider:
        """Get the active storage provider."""
        if not self._active or not self._is_available:
            raise WalletError("An active WalletStorageProvider must be added and makeAvailable must be called.")
        return self._active.storage

    def get_settings(self) -> dict[str, Any]:
        """Get settings from active storage."""
        return self.get_active().get_settings()

    def set_services(self, services: Any) -> None:
        """Set services for all stores."""
        self._services = services
        for store in self._stores:
            if hasattr(store.storage, "set_services"):
                store.storage.set_services(services)

    # =========================================================================
    # SYNC METHODS
    # =========================================================================

    def sync_from_reader(
        self,
        identity_key: str,
        reader: WalletStorageProvider,
        log: str = "",
        prog_log: Callable[[str], str] | None = None,
    ) -> SyncResult:
        """Sync data from a reader storage to local (active) storage.

        Remote → Local synchronization.

        Args:
            identity_key: User's identity key
            reader: Storage provider to read from
            log: Initial log string
            prog_log: Optional progress logging function

        Returns:
            SyncResult with inserts, updates, and log

        Reference:
            wallet-toolbox/src/storage/WalletStorageManager.ts (syncFromReader)
        """
        prog_log = prog_log or (lambda s: s)

        auth = self.get_auth()
        if identity_key != auth.identity_key:
            raise WalletError("Unauthorized: identity key mismatch")

        reader_settings = reader.make_available()
        writer = self.get_active()
        writer_settings = self.get_settings()

        inserts = 0
        updates = 0

        log += prog_log(
            f"syncFromReader from {reader_settings.get('storageName', '')} "
            f"to {writer_settings.get('storageName', '')}\n"
        )

        # Track offsets locally
        local_sync_map = create_sync_map()

        chunk_num = 0
        max_chunks = 100  # Safety limit

        while chunk_num < max_chunks:
            chunk_num += 1

            # Build args with current offsets
            offsets = []
            for name in [
                "provenTx",
                "outputBasket",
                "outputTag",
                "txLabel",
                "transaction",
                "output",
                "txLabelMap",
                "outputTagMap",
                "certificate",
                "certificateField",
                "commission",
                "provenTxReq",
            ]:
                esm = local_sync_map.get(name, EntitySyncMap(entity_name=name))
                offsets.append({"name": esm.entity_name, "offset": esm.count})

            args = {
                "identityKey": identity_key,
                "maxRoughSize": 10_000_000,
                "maxItems": 1000,
                "offsets": offsets,
                "since": None,
                "fromStorageIdentityKey": reader_settings.get("storageIdentityKey", ""),
                "toStorageIdentityKey": writer_settings.get("storageIdentityKey", ""),
            }

            # Get chunk from reader
            chunk = reader.get_sync_chunk(args)

            # Don't let reader update activeStorage
            if chunk.get("user"):
                if self._active and self._active.user:
                    chunk["user"]["activeStorage"] = self._active.user.active_storage

            # Check if sync is complete
            entity_keys = [
                "provenTxs",
                "outputBaskets",
                "outputTags",
                "txLabels",
                "transactions",
                "outputs",
                "txLabelMaps",
                "outputTagMaps",
                "certificates",
                "certificateFields",
                "commissions",
                "provenTxReqs",
            ]
            has_data = any(chunk.get(key) for key in entity_keys)

            if not has_data:
                log += prog_log("Sync complete: no more data to transfer\n")
                break

            # Process chunk on writer (local)
            result = writer.process_sync_chunk(args, chunk)

            inserts += result.get("inserts", 0)
            updates += result.get("updates", 0)
            max_updated = result.get("maxUpdatedAt", "")

            log += prog_log(
                f"chunk {chunk_num} inserted {result.get('inserts', 0)} "
                f"updated {result.get('updates', 0)} {max_updated}\n"
            )

            # Update local offsets
            entity_name_map = {
                "provenTxs": "provenTx",
                "outputBaskets": "outputBasket",
                "outputTags": "outputTag",
                "txLabels": "txLabel",
                "transactions": "transaction",
                "outputs": "output",
                "txLabelMaps": "txLabelMap",
                "outputTagMaps": "outputTagMap",
                "certificates": "certificate",
                "certificateFields": "certificateField",
                "commissions": "commission",
                "provenTxReqs": "provenTxReq",
            }

            for chunk_key, entity_name in entity_name_map.items():
                if chunk.get(chunk_key):
                    local_sync_map[entity_name].count += len(chunk[chunk_key])

            if result.get("done", False):
                break

        log += prog_log(f"syncFromReader complete: {inserts} inserts, {updates} updates\n")

        return SyncResult(inserts=inserts, updates=updates, log=log)

    def sync_to_writer(
        self,
        auth: AuthId,
        writer: WalletStorageProvider,
        log: str = "",
        prog_log: Callable[[str], str] | None = None,
    ) -> SyncResult:
        """Sync data from local (active) storage to a writer storage.

        Local → Remote synchronization.

        Args:
            auth: Authentication ID
            writer: Storage provider to write to
            log: Initial log string
            prog_log: Optional progress logging function

        Returns:
            SyncResult with inserts, updates, and log

        Reference:
            wallet-toolbox/src/storage/WalletStorageManager.ts (syncToWriter)
        """
        prog_log = prog_log or (lambda s: s)
        identity_key = auth.identity_key

        writer_settings = writer.make_available()
        reader = self.get_active()
        reader_settings = self.get_settings()

        inserts = 0
        updates = 0

        log += prog_log(
            f"syncToWriter from {reader_settings.get('storageName', '')} "
            f"to {writer_settings.get('storageName', '')}\n"
        )

        # Track offsets locally for simple implementations that don't persist sync state
        # This allows sync to work even without full sync state management on the writer
        local_sync_map = create_sync_map()

        chunk_num = 0
        max_chunks = 100  # Safety limit

        while chunk_num < max_chunks:
            chunk_num += 1

            # Build args with current offsets
            offsets = []
            for name in [
                "provenTx",
                "outputBasket",
                "outputTag",
                "txLabel",
                "transaction",
                "output",
                "txLabelMap",
                "outputTagMap",
                "certificate",
                "certificateField",
                "commission",
                "provenTxReq",
            ]:
                esm = local_sync_map.get(name, EntitySyncMap(entity_name=name))
                offsets.append({"name": esm.entity_name, "offset": esm.count})

            args = {
                "identityKey": identity_key,
                "maxRoughSize": 10_000_000,
                "maxItems": 1000,
                "offsets": offsets,
                "since": None,  # Full sync for now
                "fromStorageIdentityKey": reader_settings.get("storageIdentityKey", ""),
                "toStorageIdentityKey": writer_settings.get("storageIdentityKey", ""),
            }

            # Get chunk from reader (local)
            chunk = reader.get_sync_chunk(args)

            # Log chunk summary
            log += EntitySyncState.sync_chunk_summary(chunk)

            # Check if sync is complete (only user data, no other entities)
            entity_keys = [
                "provenTxs",
                "outputBaskets",
                "outputTags",
                "txLabels",
                "transactions",
                "outputs",
                "txLabelMaps",
                "outputTagMaps",
                "certificates",
                "certificateFields",
                "commissions",
                "provenTxReqs",
            ]
            has_data = any(chunk.get(key) for key in entity_keys)

            if not has_data:
                log += prog_log("Sync complete: no more data to transfer\n")
                break

            # Process chunk on writer (remote)
            result = writer.process_sync_chunk(args, chunk)

            inserts += result.get("inserts", 0)
            updates += result.get("updates", 0)
            max_updated = result.get("maxUpdatedAt", "")

            log += prog_log(
                f"chunk {chunk_num} inserted {result.get('inserts', 0)} "
                f"updated {result.get('updates', 0)} {max_updated}\n"
            )

            # Update local offsets based on what was in the chunk
            entity_name_map = {
                "provenTxs": "provenTx",
                "outputBaskets": "outputBasket",
                "outputTags": "outputTag",
                "txLabels": "txLabel",
                "transactions": "transaction",
                "outputs": "output",
                "txLabelMaps": "txLabelMap",
                "outputTagMaps": "outputTagMap",
                "certificates": "certificate",
                "certificateFields": "certificateField",
                "commissions": "commission",
                "provenTxReqs": "provenTxReq",
            }

            for chunk_key, entity_name in entity_name_map.items():
                if chunk.get(chunk_key):
                    local_sync_map[entity_name].count += len(chunk[chunk_key])

            if result.get("done", False):
                break

        log += prog_log(f"syncToWriter complete: {inserts} inserts, {updates} updates\n")

        return SyncResult(inserts=inserts, updates=updates, log=log)

    def update_backups(self, prog_log: Callable[[str], str] | None = None) -> str:
        """Sync current active storage to all backup storage providers.

        Args:
            prog_log: Optional progress logging function

        Returns:
            Log string with sync results

        Reference:
            wallet-toolbox/src/storage/WalletStorageManager.ts (updateBackups)
        """
        prog_log = prog_log or (lambda s: s)
        auth = self.get_auth(must_be_active=True)

        log = prog_log(f"BACKUP CURRENT ACTIVE TO {len(self._backups)} STORES\n")

        for backup in self._backups:
            result = self.sync_to_writer(auth, backup.storage, "", prog_log)
            log += result.log

        return log

    def get_stores(self) -> list[dict[str, Any]]:
        """Get information about all managed stores.

        Returns:
            List of store information dicts
        """
        stores = []

        if self._active:
            stores.append(
                {
                    "isActive": True,
                    "isEnabled": self.is_active_enabled,
                    "isBackup": False,
                    "isConflicting": False,
                    "userId": self._active.user.user_id if self._active.user else None,
                    "storageIdentityKey": self._active.settings.storage_identity_key if self._active.settings else "",
                    "storageName": self._active.settings.storage_name if self._active.settings else "",
                    "storageClass": type(self._active.storage).__name__,
                }
            )

        for store in self._conflicting_actives:
            stores.append(
                {
                    "isActive": True,
                    "isEnabled": False,
                    "isBackup": False,
                    "isConflicting": True,
                    "userId": store.user.user_id if store.user else None,
                    "storageIdentityKey": store.settings.storage_identity_key if store.settings else "",
                    "storageName": store.settings.storage_name if store.settings else "",
                    "storageClass": type(store.storage).__name__,
                }
            )

        for store in self._backups:
            stores.append(
                {
                    "isActive": False,
                    "isEnabled": False,
                    "isBackup": True,
                    "isConflicting": False,
                    "userId": store.user.user_id if store.user else None,
                    "storageIdentityKey": store.settings.storage_identity_key if store.settings else "",
                    "storageName": store.settings.storage_name if store.settings else "",
                    "storageClass": type(store.storage).__name__,
                }
            )

        return stores

    def set_active(self, storage_identity_key: str, backup_first: bool = False) -> None:
        """Set the active storage provider.

        Switches the active storage to the provider with the given identity key.
        Optionally backs up data from current active to new active first.

        Args:
            storage_identity_key: Identity key of storage to make active
            backup_first: Whether to backup current active data first

        Raises:
            InvalidParameterError: If storage not found or invalid
            WalletError: If backup/sync operations fail

        Reference:
            wallet-toolbox/src/storage/WalletStorageManager.ts (setActive)
        """
        if not storage_identity_key:
            raise InvalidParameterError("storage_identity_key", "cannot be empty")

        # Find the target storage
        target_store = None
        for store in self._stores:
            if store.settings and store.settings.storage_identity_key == storage_identity_key:
                target_store = store
                break

        if not target_store:
            raise InvalidParameterError("storage_identity_key", f"storage '{storage_identity_key}' not found")

        # If backup_first is True, sync current active to target first
        if backup_first and self._active and self._active != target_store:
            try:
                result = self.sync_to_writer(
                    auth=self.get_auth(),
                    writer=target_store.storage,
                    log=f"Backup before switching to {storage_identity_key}",
                )
                logger.info(f"Backup sync completed: {result.inserts} inserts, {result.updates} updates")
            except Exception as e:
                raise WalletError(f"Backup failed before switching storage: {e}")

        # Update user record to point to new active storage
        if target_store.user:
            target_store.user.active_storage = storage_identity_key

        # Set new active
        self._active = target_store

        # Move any conflicting actives to backups
        self._backups = []
        for store in self._stores:
            if store != target_store:
                self._backups.append(store)

        # Clear conflicting actives (they're now backups)
        self._conflicting_actives = []

        logger.info(f"Switched active storage to {storage_identity_key}")

    def add_wallet_storage_provider(self, provider: WalletStorageProvider) -> None:
        """Add a new storage provider to the manager.

        Args:
            provider: Storage provider to add
        """
        provider.make_available()
        if self._services:
            provider.set_services(self._services)
        self._stores.append(ManagedStorage(storage=provider))
        self._is_available = False
        self.make_available()
