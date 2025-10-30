from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy import select, func
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import create_session_factory, session_scope
from .models import (
    Base,
    Output,
    OutputBasket,
    OutputTag,
    OutputTagMap,
    Settings,
    TxLabel,
    TxLabelMap,
    User,
    Certificate,
    ProvenTx,
    ProvenTxReq,
)


class StorageProvider:
    """Storage provider backed by SQLAlchemy ORM.

    Summary:
        Provides database-backed storage operations for the wallet. Implements a
        minimal subset needed to unblock Wallet list flows while keeping TS-like
        shapes for results.
    TS parity:
        Mirrors toolbox/ts-wallet-toolbox `StorageProvider` where applicable.
        Implemented subset: makeAvailable, isAvailable, migrate, findOrInsertUser,
        listOutputs and basic certificate/proven helpers. Result shapes follow the
        TypeScript definitions at a minimal level.
    Args:
        engine: SQLAlchemy Engine bound to the target database.
        chain: Current chain identifier ('main'|'test').
        storage_identity_key: Unique key identifying this storage instance.
        max_output_script_length: Optional limit for script storage; kept for parity.
    Returns:
        N/A
    Raises:
        N/A
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
        include_tags = bool(args.get("includeTags", False))
        include_labels = bool(args.get("includeLabels", False))
        include_custom_instructions = bool(args.get("includeCustomInstructions", False))
        include_transactions = bool(args.get("includeTransactions", False))
        include_spent = bool(args.get("includeSpent", False))
        tag_query_mode = args.get("tagQueryMode", "any")  # 'any' | 'all'
        tags: list[str] = list(args.get("tags", []) or [])

        if offset < 0:
            offset = -offset - 1

        with session_scope(self.SessionLocal) as s:
            # Base filter: user, spendability unless include_spent
            base = (Output.user_id == user_id)
            if not include_spent:
                base = base & (Output.spendable.is_(True))
            q = select(Output).where(base)

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

            # Optional tag filters
            if tags:
                # Resolve tag ids for user
                tag_ids = s.execute(
                    select(OutputTag.output_tag_id)
                    .where(OutputTag.user_id == user_id)
                    .where(OutputTag.is_deleted.is_(False))
                    .where(OutputTag.tag.in_(tags))
                ).scalars().all()
                if tag_query_mode == "all" and len(tag_ids) < len(tags):
                    return {"totalOutputs": 0, "outputs": []}
                if tag_query_mode != "all" and len(tag_ids) == 0 and len(tags) > 0:
                    return {"totalOutputs": 0, "outputs": []}

                if len(tag_ids) > 0:
                    # Build subquery counting tag matches per output
                    m = (
                        select(OutputTagMap.output_id, func.count(func.distinct(OutputTagMap.output_tag_id)).label("tc"))
                        .where(OutputTagMap.output_tag_id.in_(tag_ids))
                        .where(OutputTagMap.is_deleted.is_(False))
                        .group_by(OutputTagMap.output_id)
                        .subquery()
                    )
                    q = q.join(m, m.c.output_id == Output.output_id)
                    if tag_query_mode == "all":
                        q = q.where(m.c.tc == len(tag_ids))
                    else:
                        q = q.where(m.c.tc > 0)

            # Count total first (before limit/offset)
            total = s.execute(q.with_only_columns(func.count())).scalar_one()

            # Ordered by primary key for determinism
            q = q.order_by(Output.output_id).limit(limit).offset(offset)
            rows: Iterable[Output] = s.execute(q).scalars().all()

            outputs: list[dict[str, Any]] = []
            for output_row in rows:
                wo: dict[str, Any] = {
                    "satoshis": int(output_row.satoshis),
                    "spendable": True,
                    "outpoint": f"{output_row.txid}.{output_row.vout}",
                }
                if include_custom_instructions and output_row.custom_instructions:
                    wo["customInstructions"] = output_row.custom_instructions
                if include_scripts:
                    # TS uses short names like 'o'/'s'; Python uses descriptive names for clarity.
                    self.validate_output_script(output_row=output_row, session=s)
                    if output_row.locking_script:
                        wo["lockingScript"] = output_row.locking_script
                if include_labels and output_row.txid:
                    wo["labels"] = [
                        t["label"] for t in self.get_labels_for_transaction_id(output_row.transaction_id or 0)
                    ]
                if include_tags:
                    wo["tags"] = [t["tag"] for t in self.get_tags_for_output_id(output_row.output_id)]
                outputs.append(wo)

            result: dict[str, Any] = {"totalOutputs": int(total), "outputs": outputs}
            if include_transactions:
                # Minimal: do not generate full BEEF yet; maintain key presence for callers
                result["BEEF"] = bytes()
            return result

    def validate_output_script(self, output_row: Output, session: Session | None = None) -> None:
        """Ensure `locking_script` is populated using rawTx slice if needed.

        Summary:
            If `scriptLength` and `scriptOffset` are present and `lockingScript`
            is missing or length mismatch, read script slice from rawTx storage.
        TS parity:
            Mirrors validateOutputScript behavior using getRawTxOfKnownValidTransaction.
        Note:
            TS code often uses short var names like 'o' and 's'. Python implementation
            uses descriptive names 'output_row' and 'session' for readability.
        Args:
            output_row: Output ORM instance.
            session: Optional active session (unused here).
        Returns:
            None (mutates `o.locking_script` in place when available).
        """
        if not output_row.script_length or not output_row.script_offset or not output_row.txid:
            return
        if output_row.locking_script and len(output_row.locking_script) == int(output_row.script_length):
            return
        script = self.get_raw_tx_of_known_valid_transaction(
            output_row.txid, int(output_row.script_offset), int(output_row.script_length)
        )
        if script:
            output_row.locking_script = script

    # ------------------------------------------------------------------
    # Additional find/list helpers
    # ------------------------------------------------------------------
    def find_output_baskets_auth(self, auth: dict[str, Any], args: dict[str, Any]) -> list[dict[str, Any]]:
        """Find output baskets for a user.

        Summary:
            Return baskets filtered by user and optional name. Minimal fields are
            returned to match TS list shapes.
        TS parity:
            Returns subset fields {basketId, name}; no soft-deleted rows are returned.
        Args:
            auth: Authentication dict that must include 'userId'.
            args: Optional filters. Supports 'name'.
        Returns:
            List of dicts with keys: basketId, name.
        Raises:
            KeyError: If 'userId' is missing from auth.
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
            Lookup tags via join on mapping table and return minimal fields.
        TS parity:
            Returns subset fields {outputTagId, tag}; excludes soft-deleted rows.
        Args:
            output_id: Output primary key.
        Returns:
            List of dicts with keys: outputTagId, tag.
        Raises:
            N/A
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
            Lookup labels via join on mapping table and return minimal fields.
        TS parity:
            Returns subset fields {txLabelId, label}; excludes soft-deleted rows.
        Args:
            transaction_id: Transaction primary key.
        Returns:
            List of dicts with keys: txLabelId, label.
        Raises:
            N/A
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
            Query outputs by user, basket (optional) and spendable flag. Return
            minimal subset fields required by Wallet list views.
        TS parity:
            Returns subset fields including {outputId, basketId, spendable, txid, vout,
            satoshis, lockingScript?}.
        Args:
            auth: Authentication dict that must include 'userId'.
            args: Optional filters: 'basket', 'spendable'.
        Returns:
            List of dicts representing outputs with minimal fields.
        Raises:
            KeyError: If 'userId' is missing from auth.
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
            Remove basket association for the specified outpoint owned by the auth user.
        TS parity:
            Same intent and minimal side effect as TS relinquishOutput.
        Args:
            auth: Dict with 'userId'.
            outpoint: Outpoint string 'txid.vout'.
        Returns:
            Number of rows affected (0 or 1).
        Raises:
            KeyError: If 'userId' is missing from auth.
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

    # ------------------------------------------------------------------
    # Certificates / Proven / Utility
    # ------------------------------------------------------------------
    def find_certificates_auth(self, auth: dict[str, Any], args: dict[str, Any]) -> list[dict[str, Any]]:
        """Find certificates for a user (subset fields).

        Summary:
            Query certificates for the authenticated user with optional filters.
        TS parity:
            Returns minimal fields {certificateId, userId, type, certifier, serialNumber, isDeleted}.
        Args:
            auth: Dict with 'userId'.
            args: Optional filters: 'type', 'certifier', 'serialNumber'.
        Returns:
            List of certificate dicts.
        Raises:
            KeyError: If 'userId' is missing from auth.
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        user_id = int(auth["userId"])  # KeyError if missing
        with session_scope(self.SessionLocal) as s:
            q = select(Certificate).where(Certificate.user_id == user_id, Certificate.is_deleted.is_(False))
            if t := args.get("type"):
                q = q.where(Certificate.type == t)
            if c := args.get("certifier"):
                q = q.where(Certificate.certifier == c)
            if sn := args.get("serialNumber"):
                q = q.where(Certificate.serial_number == sn)
            rows = s.execute(q).scalars().all()
            return [
                {
                    "certificateId": r.certificate_id,
                    "userId": r.user_id,
                    "type": r.type,
                    "certifier": r.certifier,
                    "serialNumber": r.serial_number,
                    "isDeleted": bool(r.is_deleted),
                }
                for r in rows
            ]

    def find_proven_tx_reqs(self, args: dict[str, Any]) -> list[dict[str, Any]]:
        """Find ProvenTxReq rows by partial filters (subset fields).

        Summary:
            Query current proven transaction requests using optional filters.
        TS parity:
            Returns minimal fields {provenTxReqId, txid, status, attempts, notified}.
        Args:
            args: Optional filters: 'txid', 'status', 'batch'.
        Returns:
            List of proven tx req dicts.
        Raises:
            N/A
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        with session_scope(self.SessionLocal) as s:
            q = select(ProvenTxReq)
            if txid := args.get("txid"):
                q = q.where(ProvenTxReq.txid == txid)
            if status := args.get("status"):
                q = q.where(ProvenTxReq.status == status)
            if batch := args.get("batch"):
                q = q.where(ProvenTxReq.batch == batch)
            rows = s.execute(q).scalars().all()
            return [
                {
                    "provenTxReqId": r.proven_tx_req_id,
                    "txid": r.txid,
                    "status": r.status,
                    "attempts": int(r.attempts),
                    "notified": bool(r.notified),
                }
                for r in rows
            ]

    def get_proven_or_raw_tx(self, txid: str) -> dict[str, Any]:
        """Return proven or raw tx for a txid if known (subset fields).

        Summary:
            Look up a txid first in proven set, then in reqs for rawTx/inputBEEF.
        TS parity:
            Returns TS-like keys {proven?, rawTx?, inputBEEF?} with minimal content.
        Args:
            txid: Transaction id string.
        Returns:
            Dict containing presence of proven or rawTx (and optional inputBEEF).
        Raises:
            N/A
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        with session_scope(self.SessionLocal) as s:
            p = s.execute(select(ProvenTx).where(ProvenTx.txid == txid)).scalar_one_or_none()
            if p is not None:
                return {"proven": {"provenTxId": p.proven_tx_id}, "rawTx": p.raw_tx}
            r = s.execute(select(ProvenTxReq).where(ProvenTxReq.txid == txid)).scalar_one_or_none()
            if r is None:
                return {"proven": None, "rawTx": None}
            return {"proven": None, "rawTx": r.raw_tx, "inputBEEF": r.input_beef}

    def get_raw_tx_of_known_valid_transaction(
        self, txid: str | None, offset: int | None, length: int | None
    ) -> bytes | None:
        """Return rawTx slice for a known transaction (if available).

        Summary:
            Convenience accessor that returns a segment of a known rawTx when
            offset and length are provided; otherwise returns the entire rawTx.
        TS parity:
            Mirrors helper intent used by TS storage read paths.
        Args:
            txid: Transaction id to look up.
            offset: Optional byte offset.
            length: Optional byte length.
        Returns:
            Raw bytes or None if unknown.
        Raises:
            N/A
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        if not txid:
            return None
        r = self.get_proven_or_raw_tx(txid)
        raw = r.get("rawTx")
        if not raw:
            return None
        if offset is None or length is None:
            return raw
        return bytes(raw[offset : offset + length])

    def verify_known_valid_transaction(self, txid: str) -> bool:
        """Return True if txid is known proven or rawTx is present.

        Summary:
            Mirrors TS `verifyKnownValidTransaction` by checking for a ProvenTx or
            a rawTx stored for the given txid.
        TS parity:
            Returns boolean only, without side effects.
        Args:
            txid: Transaction id string.
        Returns:
            True if proven or rawTx present; otherwise False.
        """
        r = self.get_proven_or_raw_tx(txid)
        return bool(r.get("proven") or r.get("rawTx"))

    # ------------------------------------------------------------------
    # Listing APIs (minimal shapes)
    # ------------------------------------------------------------------
    def list_certificates(self, auth: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
        """List certificates (TS-like minimal shape).

        Summary:
            Return a minimal TS-like list result for certificates.
        TS parity:
            Keys match TS list result: {totalCertificates, certificates[]}.
        Args:
            auth: Dict with 'userId'.
            args: Optional certificate filters.
        Returns:
            Dict with keys totalCertificates and certificates.
        Raises:
            KeyError: If 'userId' is missing from auth.
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        rows = self.find_certificates_auth(auth, args)
        return {"totalCertificates": len(rows), "certificates": rows}

    def list_actions(self, auth: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
        """List actions (minimal placeholder: empty list).

        Summary:
            Placeholder returning a valid TS-like list result until action workflow
            is implemented.
        TS parity:
            Keys match TS list result: {totalActions, actions[]}.
        Args:
            auth: Dict with 'userId'. Present for parity though unused here.
            args: Optional filters. Ignored in minimal implementation.
        Returns:
            Dict with keys totalActions and actions.
        Raises:
            N/A
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        return {"totalActions": 0, "actions": []}

    # ------------------------------------------------------------------
    # Change selection helpers (minimal)
    # ------------------------------------------------------------------
    def count_change_inputs(self, user_id: int, basket_id: int, exclude_sending: bool) -> int:
        """Count spendable outputs in a basket (optionally excluding 'sending').

        Summary:
            Minimal implementation: counts spendable outputs for a user and basket.
            If exclude_sending is True, excludes outputs whose spending transaction
            is currently in status 'sending'.
        TS parity:
            Approximates TS behavior for counting change inputs.
        Args:
            user_id: User identifier.
            basket_id: Basket identifier.
            exclude_sending: Exclude outputs in a 'sending' state.
        Returns:
            Integer count of available change inputs.
        """
        with session_scope(self.SessionLocal) as s:
            q = select(Output).where(
                (Output.user_id == user_id)
                & (Output.basket_id == basket_id)
                & (Output.spendable.is_(True))
            )
            rows: Iterable[Output] = s.execute(q).scalars().all()
            if not exclude_sending:
                return len(rows)

            # Exclude outputs that are tied to a 'sending' transaction via spentBy
            # Note: Minimal approximation; if no spentBy, consider it available.
            count = 0
            for output_row in rows:
                if output_row.spent_by is None:
                    count += 1
                else:
                    tx = s.execute(
                        select(ProvenTxReq).where(ProvenTxReq.proven_tx_id == output_row.spent_by)
                    ).scalar_one_or_none()
                    # If req not found or not 'sending', still count
                    if not tx or tx.status != "sending":
                        count += 1
            return count

    def allocate_change_input(
        self,
        user_id: int,
        basket_id: int,
        target_satoshis: int,
        exact_satoshis: int | None,
        exclude_sending: bool,
        transaction_id: int,
    ) -> dict[str, Any] | None:
        """Pick one spendable output as a change input candidate (minimal).

        Summary:
            Select a single spendable output from a basket that meets the target
            value. If exact_satoshis is provided, require exact match.
        TS parity:
            Minimal approximation to unlock downstream flows; does not update
            spendable flags nor lock rows.
        Args:
            user_id: User identifier.
            basket_id: Basket identifier.
            target_satoshis: Desired value.
            exact_satoshis: If provided, require exact value.
            exclude_sending: Exclude outputs in 'sending'.
            transaction_id: Current transaction id (unused minimal).
        Returns:
            Minimal output dict or None.
        """
        with session_scope(self.SessionLocal) as s:
            q = select(Output).where(
                (Output.user_id == user_id)
                & (Output.basket_id == basket_id)
                & (Output.spendable.is_(True))
            )
            rows: list[Output] = s.execute(q).scalars().all()
            # Apply exclude_sending filter (approximate)
            def ok(output_row: Output) -> bool:
                if exclude_sending and output_row.spent_by is not None:
                    req = s.execute(
                        select(ProvenTxReq).where(ProvenTxReq.proven_tx_id == output_row.spent_by)
                    ).scalar_one_or_none()
                    if req and req.status == "sending":
                        return False
                if exact_satoshis is not None:
                    return int(output_row.satoshis) == int(exact_satoshis)
                return int(output_row.satoshis) >= int(target_satoshis)

            candidates = [output_row for output_row in rows if ok(output_row)]
            if not candidates:
                return None
            # Choose smallest sufficient (greedy)
            candidates.sort(key=lambda output_row: int(output_row.satoshis))
            output_row = candidates[0]
            return {
                "outputId": output_row.output_id,
                "basketId": output_row.basket_id,
                "txid": output_row.txid,
                "vout": int(output_row.vout),
                "satoshis": int(output_row.satoshis),
            }


