"""ChaintracksStorage - Pluggable block header storage backend.

⚠️ CRITICAL DESIGN CONSTRAINT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Database column names MUST match TypeScript schema exactly (camelCase)**
- Python variable names: snake_case (internal use only)
- Database column names: camelCase (TS compatibility)

Example:
    class LiveHeadersModel(Base):
        header_id = Column("headerId", ...)  # DB: camelCase, Python: snake_case
        is_active = Column("isActive", ...)  # DB: camelCase, Python: snake_case

WHY: Cross-platform compatibility. Users may:
1. Deploy Python backend with MySQL
2. Later migrate/integrate with TS frontend
3. Need exact schema match for data interchange

All methods return/accept **camelCase keys** in dictionaries to match TS API.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Provides both persistent (SQLite/MySQL) and in-memory storage implementations
for block headers and blockchain synchronization state.

Two implementations:
  - ChaintracksStorage: SQLAlchemy-based persistent storage
  - ChaintracksStorageMemory: SQLite in-memory storage for fast caching

Synchronous, blocking design for consistency with Python implementation.

Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksStorageKnex.ts
"""

from __future__ import annotations

from typing import Any, TypedDict

from sqlalchemy import Column, Integer, String, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from bsv_wallet_toolbox.errors import WalletError

from ..wallet_services import Chain
from .chaintracks.models import StorageQueries

# SQLAlchemy Base for ChaintracksStorage models
Base = declarative_base()


class LiveHeadersModel(Base):  # type: ignore
    """SQLAlchemy model for storing live block headers.

    Maps to TS ChaintracksStorageKnex live_headers table.

    DB column names match TypeScript schema exactly for cross-platform compatibility.
    Python variable names use snake_case for consistency.

    Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksKnexMigrations.ts
    """

    __tablename__ = "live_headers"

    # DB columns named to match TS schema exactly
    header_id = Column("headerId", Integer, primary_key=True)
    previous_header_id = Column("previousHeaderId", Integer, nullable=True)
    previous_hash = Column("previousHash", String(64), nullable=True)
    height = Column(Integer, nullable=False, index=True)
    is_active = Column("isActive", Integer, nullable=False)  # Boolean as int
    is_chain_tip = Column("isChainTip", Integer, nullable=False)  # Boolean as int
    hash = Column(String(64), nullable=False, unique=True, index=True)
    chain_work = Column("chainWork", String(64), nullable=False)
    version = Column(Integer, nullable=False)
    merkle_root = Column("merkleRoot", String(64), nullable=False, index=True)
    time = Column(Integer, nullable=False)
    bits = Column(Integer, nullable=False)
    nonce = Column(Integer, nullable=False)


class BulkFilesModel(Base):  # type: ignore
    """SQLAlchemy model for storing bulk block header files.

    Maps to TS ChaintracksStorageKnex bulk_files table.

    DB column names match TypeScript schema exactly for cross-platform compatibility.

    Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksKnexMigrations.ts

    TODO: Phase 4 - Implement full bulk files schema
    """

    __tablename__ = "bulk_files"

    # Placeholder for bulk files structure
    file_id = Column("fileId", Integer, primary_key=True)
    start_height = Column("startHeight", Integer, nullable=False)
    end_height = Column("endHeight", Integer, nullable=False)


class SyncStateModel(Base):  # type: ignore
    """SQLAlchemy model for tracking block synchronization state.

    Stores the latest synced block height and hash for each chain.
    Used to resume synchronization after service restarts.

    Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksStorageKnex.ts
    """

    __tablename__ = "chaintracks_sync_state"

    # DB columns named to match expected schema
    sync_id = Column("syncId", Integer, primary_key=True)
    chain = Column(String(10), nullable=False, unique=True)
    last_synced_height = Column("lastSyncedHeight", Integer, nullable=False, default=0)
    last_synced_hash = Column("lastSyncedHash", String(64), nullable=True)


class ChaintracksStorageOptions(TypedDict, total=False):
    """Configuration for ChaintracksStorage.

    Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksStorageKnex.ts
    """

    chain: Chain
    database_url: str | None
    readonly: bool


class ChaintracksStorage:
    """Persistent block header storage using SQLAlchemy ORM.

    Stores block headers and manages blockchain state for Chaintracks.
    Supports SQLite and MySQL via SQLAlchemy.

    IMPORTANT FOR USERS:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. **Connection Pooling**: Manages session pooling automatically
    2. **Database Selection**:
       - Development: SQLite (file-based)
       - Production: MySQL 8.0+ recommended
    3. **Schema Migration**: Call make_available() before use
    4. **Resource Cleanup**: Always call destroy() on shutdown

    USAGE EXAMPLES:

    # SQLite (Development)
    storage = ChaintracksStorage(
        database_url="sqlite:///chaintracks.db",
        chain="main"
    )

    # MySQL (Production)
    storage = ChaintracksStorage(
        database_url="mysql+pymysql://user:pass@localhost/chaintracks",
        chain="main"
    )

    Synchronous, blocking design for consistency with Python implementation.

    Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksStorageKnex.ts
    """

    @staticmethod
    def create_storage_options(
        chain: Chain,
        database_url: str | None = None,
    ) -> ChaintracksStorageOptions:
        """Create default options for ChaintracksStorage.

        Args:
            chain: Blockchain network ('main' or 'test')
            database_url: Database connection URL (defaults to SQLite)

        Returns:
            Storage options

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksStorageKnex.ts
        """
        options: ChaintracksStorageOptions = {
            "chain": chain,
            "databaseUrl": database_url,
            "readonly": False,
        }
        return options

    def __init__(
        self,
        options: ChaintracksStorageOptions,
        engine: Engine | None = None,
    ) -> None:
        """Initialize ChaintracksStorage.

        Args:
            options: Storage configuration
            engine: SQLAlchemy Engine (creates default SQLite if None)

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksStorageKnex.ts
        """
        self.options: ChaintracksStorageOptions = {**options}
        self.chain: Chain = options.get("chain", "main")
        self.readonly: bool = options.get("readonly", False)

        # Initialize SQLAlchemy engine
        if engine:
            self.engine = engine
        else:
            # Create default SQLite database
            database_url = options.get("databaseUrl")
            if not database_url:
                db_file = f"chaintracks_{self.chain}.db"
                database_url = f"sqlite:///{db_file}"

            self.engine = create_engine(database_url, echo=False)

        # Create session factory
        session_local = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.session_factory: sessionmaker[Any] = session_local
        self.is_available = False

    def make_available(self) -> None:
        """Initialize database tables and prepare for use.

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksStorageKnex.ts

        TODO: Phase 4 - Implement database migrations
        TODO: Phase 4 - Handle existing schema upgrades
        """
        try:
            # Run database migrations
            self._run_migrations()

            # Create all tables
            Base.metadata.create_all(self.engine)
            self.is_available = True
        except Exception as e:
            raise WalletError(f"Failed to initialize ChaintracksStorage: {e!s}")

    def get_height(self) -> int:
        """Get the latest synced block height.

        Returns:
            Latest block height

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksStorageKnex.ts

        TODO: Phase 4 - Optimize with indexed queries
        """
        try:
            session = self.session_factory()
            try:
                # Get highest height from live_headers table
                result = session.query(LiveHeadersModel.height).order_by(LiveHeadersModel.height.desc()).first()
                return result[0] if result else 0
            finally:
                session.close()
        except Exception as e:
            raise WalletError(f"Failed to get height: {e!s}")

    def insert_header(
        self,
        height: int,
        header_hash: str,
        chain_work: str,
        is_active: bool = True,
        is_chain_tip: bool = False,
        version: int = 1,
        merkle_root: str = "",
        time: int = 0,
        bits: int = 0,
        nonce: int = 0,
    ) -> None:
        """Insert a block header into storage.

        Args:
            height: Block height
            header_hash: Block header hash (hex)
            chain_work: Cumulative work (hex)
            is_active: Whether header is active in chain
            is_chain_tip: Whether header is current chain tip
            version: Block version
            merkle_root: Merkle root of transactions
            time: Block timestamp
            bits: Difficulty target (bits)
            nonce: Block nonce

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksStorageKnex.ts

        TODO: Phase 4 - Implement conflict handling (replace on duplicate height)
        """
        try:
            session = self.session_factory()
            try:
                # Check if header already exists
                existing = session.query(LiveHeadersModel).filter_by(height=height).first()
                if existing:
                    # Update existing header
                    existing.hash = header_hash
                    existing.chain_work = chain_work
                    existing.is_active = int(is_active)
                    existing.is_chain_tip = int(is_chain_tip)
                    existing.version = version
                    existing.merkle_root = merkle_root
                    existing.time = time
                    existing.bits = bits
                    existing.nonce = nonce
                else:
                    # Insert new header
                    new_header = LiveHeadersModel(
                        height=height,
                        hash=header_hash,
                        chain_work=chain_work,
                        is_active=int(is_active),
                        is_chain_tip=int(is_chain_tip),
                        version=version,
                        merkle_root=merkle_root,
                        time=time,
                        bits=bits,
                        nonce=nonce,
                    )
                    session.add(new_header)

                session.commit()
            finally:
                session.close()
        except Exception as e:
            raise WalletError(f"Failed to insert header at height {height}: {e!s}")

    def get_header_for_height(self, height: int) -> dict[str, Any] | None:
        """Retrieve block header for specified height.

        Args:
            height: Block height

        Returns:
            Header data or None if not found

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksStorageKnex.ts
        """
        try:
            session = self.session_factory()
            try:
                header = session.query(LiveHeadersModel).filter_by(height=height).first()
                if header:
                    return {
                        "headerId": header.header_id,
                        "height": header.height,
                        "hash": header.hash,
                        "chainWork": header.chain_work,
                        "isActive": bool(header.is_active),
                        "isChainTip": bool(header.is_chain_tip),
                        "version": header.version,
                        "merkleRoot": header.merkle_root,
                        "time": header.time,
                        "bits": header.bits,
                        "nonce": header.nonce,
                    }
                return None
            finally:
                session.close()
        except Exception as e:
            raise WalletError(f"Failed to get header for height {height}: {e!s}")

    def find_headers_for_heights(
        self,
        heights: list[int],
    ) -> dict[int, dict[str, Any]]:
        """Retrieve multiple block headers by height.

        Args:
            heights: List of block heights

        Returns:
            Mapping of heights to header data

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksStorageKnex.ts

        TODO: Phase 4 - Implement batch query optimization
        """
        results: dict[int, dict[str, Any]] = {}
        try:
            session = self.session_factory()
            try:
                # Batch query optimization: use single query with IN clause
                # This is already optimized, but we could add more optimizations like:
                # - Connection pooling
                # - Query result caching
                # - Prepared statements
                headers = session.query(LiveHeadersModel).filter(LiveHeadersModel.height.in_(heights)).all()

                for header in headers:
                    results[header.height] = {
                        "headerId": header.header_id,
                        "height": header.height,
                        "hash": header.hash,
                        "chainWork": header.chain_work,
                        "isActive": bool(header.is_active),
                        "isChainTip": bool(header.is_chain_tip),
                        "version": header.version,
                        "merkleRoot": header.merkle_root,
                        "time": header.time,
                        "bits": header.bits,
                        "nonce": header.nonce,
                    }
            finally:
                session.close()
        except Exception as e:
            raise WalletError(f"Failed to find headers for heights: {e!s}")

        return results

    def get_sync_state(self) -> dict[str, Any]:
        """Get current synchronization state.

        Returns:
            Sync state data (height, hash)

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksStorageKnex.ts

        TODO: Phase 4 - Add reorg detection logic
        """
        try:
            session = self.session_factory()
            try:
                sync_state = session.query(SyncStateModel).filter_by(chain=self.chain).first()
                if sync_state:
                    # Basic reorg detection: check if stored hash matches current chain
                    # In a full implementation, this would:
                    # 1. Compare stored block hash with current chain hash at same height
                    # 2. Detect if reorg occurred
                    # 3. Trigger reorg recovery if needed

                    # TODO: Implement full reorg detection comparing hashes
                    return {
                        "lastSyncedHeight": sync_state.last_synced_height,
                        "lastSyncedHash": sync_state.last_synced_hash,
                    }

                # Create default if not exists
                default_state = SyncStateModel(chain=self.chain, last_synced_height=0)
                session.add(default_state)
                session.commit()
                return {
                    "lastSyncedHeight": 0,
                    "lastSyncedHash": None,
                }
            finally:
                session.close()
        except Exception as e:
            raise WalletError(f"Failed to get sync state: {e!s}")

    def update_sync_state(self, height: int, block_hash: str) -> None:
        """Update synchronization state.

        Args:
            height: Latest synced height
            block_hash: Latest synced block hash

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksStorageKnex.ts

        TODO: Phase 4 - Add transaction safety
        """
        try:
            session = self.session_factory()
            try:
                # Transaction safety: ensure atomic updates
                with session.begin():
                    sync_state = session.query(SyncStateModel).filter_by(chain=self.chain).first()
                    if sync_state:
                        sync_state.last_synced_height = height
                        sync_state.last_synced_hash = block_hash
                    else:
                        sync_state = SyncStateModel(
                            chain=self.chain,
                            last_synced_height=height,
                            last_synced_hash=block_hash,
                        )
                    session.add(sync_state)

                session.commit()
            finally:
                session.close()
        except Exception as e:
            raise WalletError(f"Failed to update sync state: {e!s}")

    def destroy(self) -> None:
        """Clean up and close database resources.

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksStorageKnex.ts

        TODO: Phase 4 - Implement connection pool cleanup
        """
        try:
            if hasattr(self, "engine") and self.engine:
                self.engine.dispose()
            self.is_available = False
        except Exception:
            pass  # Best-effort cleanup

    def query(self, context=None) -> StorageQueries:
        """Get StorageQueries interface for database operations.

        Args:
            context: Optional context (for future use)

        Returns:
            StorageQueries implementation

        Reference: go-wallet-toolbox/pkg/services/chaintracks/gormstorage/provider.go
        """
        from .chaintracks.storage.sqlalchemy_storage import SQLAlchemyStorageQueries

        session = self.session_factory()
        return SQLAlchemyStorageQueries(session)


class ChaintracksStorageMemory(ChaintracksStorage):
    """In-memory block header storage using SQLite in-memory database.

    Fast, ephemeral storage suitable for caching and high-throughput scenarios.
    Inherits all methods from ChaintracksStorage but uses `:memory:` SQLite.

    Synchronous, blocking design for consistency with Python implementation.

    Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksStorageMemory.ts
    """

    def __init__(
        self,
        options: ChaintracksStorageOptions,
    ) -> None:
        """Initialize ChaintracksStorageMemory with in-memory SQLite.

        Args:
            options: Storage configuration (database_url ignored)

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksStorageMemory.ts
        """
        # Force in-memory SQLite URL
        memory_options = {**options}
        memory_options["databaseUrl"] = "sqlite:///:memory:"

        # Create in-memory engine
        memory_engine = create_engine("sqlite:///:memory:", echo=False)

        # Call parent with memory engine
        super().__init__(memory_options, memory_engine)

    @staticmethod
    def create_memory_storage_options(
        chain: Chain,
    ) -> ChaintracksStorageOptions:
        """Create options for in-memory storage.

        Args:
            chain: Blockchain network ('main' or 'test')

        Returns:
            Storage options configured for in-memory use

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Storage/ChaintracksStorageMemory.ts
        """
        return ChaintracksStorage.create_storage_options(chain, "sqlite:///:memory:")

    def _run_migrations(self) -> None:
        """Run database migrations to update schema.

        Handles schema upgrades and data migrations.
        """
        # Check current schema version and migrate as needed
        # For now, this is a basic implementation

        session = self.session_factory()
        try:
            # Check if we have a migrations table
            # Using text() to execute a hardcoded raw SQL query via SQLAlchemy (no user input involved)
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='migrations'"))
            if not result.fetchone():
                # Create migrations table
                session.execute(text("""
                    CREATE TABLE migrations (
                        id INTEGER PRIMARY KEY,
                        version TEXT NOT NULL,
                        applied_at INTEGER NOT NULL
                    )
                """))
                session.commit()

            # TODO: Implement specific migration logic
            # For example:
            # - Add new columns
            # - Transform data
            # - Update indexes

        finally:
            session.close()
