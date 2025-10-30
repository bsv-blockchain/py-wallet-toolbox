from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import create_session_factory, session_scope
from .models import Base, Output, Settings, User


class StorageProvider:
    """Storage provider backed by SQLAlchemy ORM.

    Summary:
        Minimal provider implementing availability, migration, basic user ops,
        and listOutputs with TS-like JSON shapes. This is a subset oriented to
        unblock Wallet flows until full parity is required.
    TS parity:
        Mirrors toolbox/ts-wallet-toolbox StorageProvider.where applicable, but
        only implements a strict subset: makeAvailable, isAvailable, migrate,
        findOrInsertUser, listOutputs. Shapes align with TS minimal fields.
    Args:
        engine: SQLAlchemy Engine bound to the target database.
        chain: Chain name (e.g., 'main' | 'test').
        storage_identity_key: Unique key identifying this storage instance.
        max_output_script_length: Present for TS parity; not strictly used here.
    Reference:
        toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        toolbox/ts-wallet-toolbox/src/storage/methods/listOutputsKnex.ts
        toolbox/py-wallet-toolbox/tests
        sdk/py-sdk
    """

    def __init__(
        self,
        *,
        engine: Engine,
        chain: str,
        storage_identity_key: str,
        max_output_script_length: int | None = None,
    ) -> None:
        self.engine = engine
        self.SessionLocal = create_session_factory(engine)
        self.chain = chain
        self.storage_identity_key = storage_identity_key
        self.max_output_script_length = max_output_script_length

    # ------------------------------------------------------------------
    # Lifecycle / availability
    # ------------------------------------------------------------------
    def migrate(self) -> None:
        """Create all tables if missing.

        Summary:
            Apply ORM-declared schema to the connected database.
        TS parity:
            Equivalent to initial Knex migration createAll.
        Args:
            None
        Returns:
            None
        Raises:
            sqlalchemy.exc.SQLAlchemyError: On DDL failures.
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/schema/KnexMigrations.ts
        """
        Base.metadata.create_all(self.engine)

    def is_available(self) -> bool:
        """Return True if storage is initialized.

        Summary:
            Checks presence of a `Settings` row for this storage identity.
        TS parity:
            Similar intent as TS `isAvailable` check.
        Args:
            None
        Returns:
            True if available; otherwise False.
        Raises:
            None
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        with session_scope(self.SessionLocal) as s:
            q = select(Settings).where(Settings.storage_identity_key == self.storage_identity_key)
            return s.execute(q).scalar_one_or_none() is not None

    def make_available(self) -> dict[str, Any]:
        """Ensure storage is initialized and return settings info.

        Summary:
            Creates schema (if needed) and inserts a `Settings` row when
            missing. Returns TS-like shape.
        TS parity:
            Mirrors `makeAvailable()` behavior at a high level.
        Args:
            None
        Returns:
            Dict with keys: storageIdentityKey, chain
        Raises:
            sqlalchemy.exc.SQLAlchemyError: On database errors.
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageKnex.ts
        """
        self.migrate()
        with session_scope(self.SessionLocal) as s:
            q = select(Settings).where(Settings.storage_identity_key == self.storage_identity_key)
            row = s.execute(q).scalar_one_or_none()
            if row is None:
                row = Settings(chain=self.chain, storage_identity_key=self.storage_identity_key)
                s.add(row)
                try:
                    s.flush()
                except IntegrityError:
                    s.rollback()
                    # Race insert: re-read
                    row = s.execute(q).scalar_one()
            return {
                "storageIdentityKey": row.storage_identity_key,
                "chain": row.chain,
            }

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    def find_or_insert_user(self, identity_key: str) -> dict[str, int | str]:
        """Find existing user or insert a new one by identity_key.

        Summary:
            Idempotent upsert by public key hex.
        TS parity:
            Same intent as TS storage helpers.
        Args:
            identity_key: Public key hex string.
        Returns:
            Dict with keys: userId, identityKey
        Raises:
            sqlalchemy.exc.SQLAlchemyError: On database errors.
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageReaderWriter.ts
        """
        with session_scope(self.SessionLocal) as s:
            q = select(User).where(User.identity_key == identity_key)
            u = s.execute(q).scalar_one_or_none()
            if u is None:
                u = User(identity_key=identity_key)
                s.add(u)
                try:
                    s.flush()
                except IntegrityError:
                    s.rollback()
                    u = s.execute(q).scalar_one()
            return {"userId": u.user_id, "identityKey": u.identity_key}

    # ------------------------------------------------------------------
    # listOutputs (minimal subset)
    # ------------------------------------------------------------------
    def list_outputs(self, auth: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
        """List wallet outputs for a user with TS-like shape.

        Summary:
            Minimal implementation returning spendable outputs only (spent == False)
            ordered by primary key, supporting limit/offset. Optional inclusion of
            lockingScript when present.
        TS parity:
            Aligns output JSON shape for WalletOutput fields used by tests:
            satoshis, spendable, outpoint, lockingScript (optional). Basket/tags/labels
            and transaction inclusion are omitted.
        Args:
            auth: Dict with 'userId'.
            args: Dict with optional keys 'limit' (int), 'offset' (int),
                  'includeLockingScripts' (bool).
        Returns:
            Dict with keys: totalOutputs, outputs[].
        Raises:
            KeyError: If auth.userId is missing.
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/methods/listOutputsKnex.ts
        """
        user_id = int(auth["userId"])  # KeyError if missing
        limit = int(args.get("limit", 10))
        offset = int(args.get("offset", 0))
        include_scripts = bool(args.get("includeLockingScripts", False))

        if offset < 0:
            offset = -offset - 1

        with session_scope(self.SessionLocal) as s:
            # Query only spendable outputs (spent == False) for minimal parity
            q = select(Output).where((Output.user_id == user_id) & (Output.spent.is_(False)))
            q_count = s.execute(q).scalars().all()
            total = len(q_count)

            # Ordered by primary key for determinism
            q = q.order_by(Output.output_id).limit(limit).offset(offset)
            rows: Iterable[Output] = s.execute(q).scalars().all()

            outputs: list[dict[str, Any]] = []
            for o in rows:
                wo: dict[str, Any] = {
                    "satoshis": int(o.satoshis),
                    "spendable": True,
                    "outpoint": f"{o.txid}.{o.vout}",
                }
                if include_scripts and o.script:
                    wo["lockingScript"] = o.script
                outputs.append(wo)

            return {"totalOutputs": total, "outputs": outputs}


