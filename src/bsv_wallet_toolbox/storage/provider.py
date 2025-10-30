from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import create_session_factory, session_scope
from .models import Base, Output, OutputBasket, OutputTag, OutputTagMap, Settings, TxLabel, TxLabelMap, User


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
                # Derive dbtype for settings record
                dialect = self.engine.dialect.name
                if dialect == "sqlite":
                    dbtype = "SQLite"
                elif dialect.startswith("mysql"):
                    dbtype = "MySQL"
                elif dialect.startswith("postgres"):
                    dbtype = "PostgreSQL"
                else:
                    dbtype = dialect

                row = Settings(
                    chain=self.chain,
                    storage_identity_key=self.storage_identity_key,
                    storage_name="default",
                    dbtype=dbtype,
                    max_output_script=10_000_000,
                )
                s.add(row)
                try:
                    s.flush()
                except IntegrityError:
                    s.rollback()
                    # Race insert: re-read
                    row = s.execute(q).scalar_one()
            return {
                "storageIdentityKey": row.storage_identity_key,
                "storageName": row.storage_name,
                "chain": row.chain,
                "dbtype": row.dbtype,
                "maxOutputScript": row.max_output_script,
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
            # Base filter: user and spendable
            q = select(Output).where((Output.user_id == user_id) & (Output.spendable.is_(True)))

            # Optional basket name filter
            basket_name = args.get("basket")
            if basket_name:
                bq = select(OutputBasket.basket_id).where(
                    (OutputBasket.user_id == user_id) & (OutputBasket.name == basket_name) & (OutputBasket.is_deleted.is_(False))
                )
                bid = s.execute(bq).scalar_one_or_none()
                if bid is None:
                    return {"totalOutputs": 0, "outputs": []}
                q = q.where(Output.basket_id == bid)

            # Count total first
            total = len(s.execute(q).scalars().all())

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
                if include_scripts and (o.locking_script or o.script):
                    wo["lockingScript"] = (o.locking_script or o.script)
                outputs.append(wo)

            return {"totalOutputs": total, "outputs": outputs}

    # ------------------------------------------------------------------
    # Additional find/list helpers
    # ------------------------------------------------------------------
    def find_output_baskets_auth(self, auth: dict[str, Any], args: dict[str, Any]) -> list[dict[str, Any]]:
        """Find output baskets for a user.

        Summary:
            Minimal filter by user and optional name.
        TS parity:
            Returns subset: basketId, name.
        Args:
            auth: Dict with 'userId'.
            args: Dict with optional 'name'.
        Returns:
            List of baskets.
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        user_id = int(auth["userId"])  # KeyError if missing
        name = args.get("name")
        with session_scope(self.SessionLocal) as s:
            q = select(OutputBasket).where((OutputBasket.user_id == user_id) & (OutputBasket.is_deleted.is_(False)))
            if name:
                q = q.where(OutputBasket.name == name)
            rows = s.execute(q).scalars().all()
            return [{"basketId": r.basket_id, "name": r.name} for r in rows]

    def get_tags_for_output_id(self, output_id: int) -> list[dict[str, Any]]:
        """Return tags associated with an output.

        Summary:
            Joins tag maps and returns tag strings.
        TS parity:
            Returns subset: outputTagId, tag.
        Args:
            output_id: Output primary key.
        Returns:
            List of tag dicts.
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        with session_scope(self.SessionLocal) as s:
            mq = select(OutputTagMap.output_tag_id).where(
                (OutputTagMap.output_id == output_id) & (OutputTagMap.is_deleted.is_(False))
            )
            tag_ids = [i for i in s.execute(mq).scalars().all()]
            if not tag_ids:
                return []
            tq = select(OutputTag).where(OutputTag.output_tag_id.in_(tag_ids), OutputTag.is_deleted.is_(False))
            rows = s.execute(tq).scalars().all()
            return [{"outputTagId": r.output_tag_id, "tag": r.tag} for r in rows]

    def get_labels_for_transaction_id(self, transaction_id: int) -> list[dict[str, Any]]:
        """Return labels associated with a transaction.

        Summary:
            Joins label maps and returns label strings.
        TS parity:
            Returns subset: txLabelId, label.
        Args:
            transaction_id: Transaction primary key.
        Returns:
            List of label dicts.
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        with session_scope(self.SessionLocal) as s:
            mq = select(TxLabelMap.tx_label_id).where(TxLabelMap.transaction_id == transaction_id)
            label_ids = [i for i in s.execute(mq).scalars().all()]
            if not label_ids:
                return []
            tq = select(TxLabel).where(TxLabel.tx_label_id.in_(label_ids), TxLabel.is_deleted.is_(False))
            rows = s.execute(tq).scalars().all()
            return [{"txLabelId": r.tx_label_id, "label": r.label} for r in rows]

    def find_outputs_auth(self, auth: dict[str, Any], args: dict[str, Any]) -> list[dict[str, Any]]:
        """Find outputs by partial filters for a user.

        Summary:
            Minimal filter supporting basket and spendable.
        TS parity:
            Returns TS-like rows subset.
        Args:
            auth: Dict with 'userId'.
            args: Dict with optional 'basket', 'spendable'.
        Returns:
            List of outputs as dicts.
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        user_id = int(auth["userId"])  # KeyError if missing
        basket_name = args.get("basket")
        spendable = args.get("spendable", None)
        with session_scope(self.SessionLocal) as s:
            q = select(Output).where(Output.user_id == user_id)
            if spendable is not None:
                q = q.where(Output.spendable.is_(bool(spendable)))
            if basket_name:
                bq = select(OutputBasket.basket_id).where(
                    (OutputBasket.user_id == user_id) & (OutputBasket.name == basket_name) & (OutputBasket.is_deleted.is_(False))
                )
                bid = s.execute(bq).scalar_one_or_none()
                if bid is None:
                    return []
                q = q.where(Output.basket_id == bid)
            rows: Iterable[Output] = s.execute(q).scalars().all()
            r: list[dict[str, Any]] = []
            for o in rows:
                r.append(
                    {
                        "outputId": o.output_id,
                        "transactionId": None,
                        "basketId": o.basket_id,
                        "spendable": bool(o.spendable),
                        "txid": o.txid,
                        "vout": int(o.vout),
                        "satoshis": int(o.satoshis),
                        "lockingScript": o.locking_script or o.script,
                    }
                )
            return r

    def relinquish_output(self, auth: dict[str, Any], outpoint: str) -> int:
        """Unset basket on an output identified by 'txid.vout'.

        Summary:
            Matches TS relinquishOutput minimal effect.
        TS parity:
            Only clears basket association.
        Args:
            auth: Dict with 'userId'.
            outpoint: String format 'txid.vout'.
        Returns:
            Number of rows affected (0 or 1).
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        user_id = int(auth["userId"])  # KeyError if missing
        try:
            txid, vout_s = outpoint.split(".")
            vout = int(vout_s)
        except Exception:
            return 0
        with session_scope(self.SessionLocal) as s:
            q = select(Output).where((Output.user_id == user_id) & (Output.txid == txid) & (Output.vout == vout))
            o = s.execute(q).scalar_one_or_none()
            if not o:
                return 0
            o.basket_id = None
            s.add(o)
            return 1


