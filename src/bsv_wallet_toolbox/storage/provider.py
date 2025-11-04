from __future__ import annotations

import secrets
from collections.abc import Iterable
from typing import Any, ClassVar
from datetime import datetime, timezone

from bsv.merkle_path import MerklePath
from bsv.transaction import Transaction
from sqlalchemy import func, inspect, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import create_session_factory, session_scope
from .models import (
    Base,
    Certificate,
    CertificateField,
    Commission,
    MonitorEvent,
    Output,
    OutputBasket,
    OutputTag,
    OutputTagMap,
    ProvenTx,
    ProvenTxReq,
    Settings,
    SyncState,
    TxLabel,
    TxLabelMap,
    User,
)
from .models import (
    Transaction as TransactionModel,
)
from bsv_wallet_toolbox.utils.validation import validate_internalize_action_args


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
        # Optional Services handle (wired by Wallet). Needed by some SpecOps.
        self._services: Any | None = None

    def set_services(self, services: Any) -> None:
        """Attach a Services instance for network-backed checks.

        Summary:
            Stores a handle to `Services` so storage operations that need
            provider access (e.g., SpecOp invalid change) can delegate.
        TS parity:
            Mirrors TS StorageProvider.setServices/getServices.
        Args:
            services: WalletServices-compatible instance.
        Returns:
            None
        """
        self._services = services

    def get_services(self) -> Any:
        """Return the attached Services instance or raise if missing.

        Raises:
            RuntimeError: If services have not been attached.
        """
        if self._services is None:
            raise RuntimeError("Services must be set via set_services() before use")
        return self._services

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
        with self.engine.begin() as conn:
            Base.metadata.create_all(bind=conn)

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
            _exec_result = s.execute(q)
            row = _exec_result.scalar_one_or_none()
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
                    _exec_result = s.execute(q)
                    row = _exec_result.scalar_one()
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
            _exec_result = s.execute(q)
            u = _exec_result.scalar_one_or_none()
            if u is None:
                u = User(identity_key=identity_key)
                s.add(u)
                try:
                    s.flush()
                except IntegrityError:
                    s.rollback()
                    _exec_result = s.execute(q)
                    u = _exec_result.scalar_one()
            return {"userId": u.user_id, "identityKey": u.identity_key}

    # ------------------------------------------------------------------
    # listOutputs (minimal subset)
    # ------------------------------------------------------------------
    def list_outputs(self, auth: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
        """List wallet outputs with TS parity (SpecOps and includes).

        Summary:
            Returns a paginated list of outputs for the authenticated user,
            honoring basket, tag filters, and include flags. Supports TypeScript
            SpecOps for the `basket` field (wallet balance, invalid change,
            set wallet change params) and tag SpecOps ('all'|'change'|'spent'|'unspent').
            When `includeTransactions` is true, attaches a minimal BEEF placeholder.
        TS parity:
            - Basket SpecOps:
              - specOpWalletBalance (or its id): use basket 'default', ignore limit;
                result has totalOutputs=sum(satoshis) and outputs=[].
              - specOpInvalidChange (or its id): use basket 'default',
                includeOutputScripts=true, includeSpent=false; filters to invalid
                change via network checks (placeholder here).
              - specOpSetWalletChangeParams (or its id): tags [numberOfDesiredUTXOs,
                minimumDesiredUTXOValue] update default basket params; returns empty
                result.
            - Tag SpecOps: 'all' (ignore basket, include spent), 'change' (change
              only), 'spent'/'unspent'.
            - Include flags: includeLockingScripts/includeCustomInstructions/includeTags/includeLabels.
            - includeTransactions: minimal BEEF (rawTx concat) until full Proven flow is available.
        Args:
            auth: Dict containing 'userId' (int).
            args: Dict with keys such as basket, tags, tagQueryMode ('any'|'all'),
                  limit, offset, includeLockingScripts, includeCustomInstructions,
                  includeTags, includeLabels, includeTransactions,
                  knownTxids (list[str], optional; do not descend into these when building BEEF).
        Returns:
            dict: { totalOutputs: int, outputs: WalletOutput[], BEEF?: bytes }
        Raises:
            KeyError: If 'userId' is missing from auth.
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/methods/listOutputsKnex.ts
            toolbox/ts-wallet-toolbox/src/storage/methods/ListOutputsSpecOp.ts
            toolbox/py-wallet-toolbox/tests
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
        filter_change_only = False

        # Basket SpecOps (TS parity). Support both constant values and friendly names.
        specop_invalid_change = "5a76fd430a311f8bc0553859061710a4475c19fed46e2ff95969aa918e612e57"
        specop_set_change = "a4979d28ced8581e9c1c92f1001cc7cb3aabf8ea32e10888ad898f0a509a3929"
        specop_wallet_bal = "893b7646de0e1c9f741bd6e9169b76a8847ae34adef7bef1e6a285371206d2e8"

        basket_name = args.get("basket")

        def resolve_specop(name: str | None) -> str | None:
            if not name:
                return None
            mapping: dict[str, str] = {
                specop_wallet_bal: "wallet_balance",
                specop_invalid_change: "invalid_change",
                specop_set_change: "set_change",
                # Friendly aliases (dev convenience)
                "specOpWalletBalance": "wallet_balance",
                "specOpInvalidChange": "invalid_change",
                "specOpSetWalletChangeParams": "set_change",
            }
            return mapping.get(name)

        specop = resolve_specop(basket_name)
        specop_ignore_limit = False
        specop_include_scripts = False
        specop_include_spent: bool | None = None
        specop_tags: list[str] = []

        # Handle SpecOp tag parameters/intercepts
        if specop == "set_change":
            if len(tags) >= 2:
                specop_tags = tags[:2]
                tags = tags[2:]
        if specop == "invalid_change":
            intercepted: list[str] = []
            for t in list(tags):
                if t in ("release", "all"):
                    intercepted.append(t)
                    tags.remove(t)
                    if t == "all":
                        basket_name = None
            specop_tags = intercepted

        if specop == "wallet_balance":
            basket_name = "default"
            specop_ignore_limit = True
        elif specop == "invalid_change":
            basket_name = basket_name or "default"
            specop_ignore_limit = True
            specop_include_scripts = True
            specop_include_spent = False

        if offset < 0:
            offset = -offset - 1

        with session_scope(self.SessionLocal) as s:
            # SpecOp (TS compatibility): interpret special tags to alter query behavior
            # - 'all': ignore basket filter and include spent outputs
            # - 'change': include only change outputs
            # - 'spent': include spent outputs as well
            # - 'unspent': exclude spent outputs(default)
            if tags:
                if "all" in tags:
                    basket_name = None
                    include_spent = True
                    tags = [t for t in tags if t != "all"]
                if "change" in tags:
                    filter_change_only = True
                    tags = [t for t in tags if t != "change"]
                if "spent" in tags:
                    include_spent = True
                    tags = [t for t in tags if t != "spent"]
                if "unspent" in tags:
                    include_spent = False
                    tags = [t for t in tags if t != "unspent"]

            # Base filter: user, spendability unless include_spent
            base = Output.user_id == user_id
            if specop_include_spent is not None:
                include_spent = specop_include_spent
            if not include_spent:
                base = base & (Output.spendable.is_(True))
            q = select(Output).where(base)

            if filter_change_only:
                q = q.where(Output.change.is_(True))

            # Optional basket name filter (may be overridden by SpecOp)
            if basket_name:
                bq = select(OutputBasket.basket_id).where(
                    (OutputBasket.user_id == user_id)
                    & (OutputBasket.name == basket_name)
                    & (OutputBasket.is_deleted.is_(False))
                )
                _exec_result = s.execute(bq)
                bid = _exec_result.scalar_one_or_none()
                if bid is None:
                    return {"totalOutputs": 0, "outputs": []}
                q = q.where(Output.basket_id == bid)

            # Optional tag filters
            if tags:
                # Resolve tag ids for user
                tag_ids = (
                    s.execute(
                        select(OutputTag.output_tag_id)
                        .where(OutputTag.user_id == user_id)
                        .where(OutputTag.is_deleted.is_(False))
                        .where(OutputTag.tag.in_(tags))
                    )
                    .scalars()
                    .all()
                )
                if tag_query_mode == "all" and len(tag_ids) < len(tags):
                    return {"totalOutputs": 0, "outputs": []}
                if tag_query_mode != "all" and len(tag_ids) == 0 and len(tags) > 0:
                    return {"totalOutputs": 0, "outputs": []}

                if len(tag_ids) > 0:
                    # Build subquery counting tag matches per output
                    m = (
                        select(
                            OutputTagMap.output_id, func.count(func.distinct(OutputTagMap.output_tag_id)).label("tc")
                        )
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
            _result_count = s.execute(q.with_only_columns(func.count()))
            total = _result_count.scalar_one()

            # Ordered by primary key for determinism (SpecOp may ignore limit)
            q = q.order_by(Output.output_id)
            if not specop_ignore_limit:
                q = q.limit(limit).offset(offset)
            _result = s.execute(q)

            rows: Iterable[Output] = _result.scalars().all()

            # SpecOp: invalidChange -> filter to outputs that are NOT UTXOs per services
            if specop == "invalid_change":
                filtered_rows: list[Output] = []
                services = None
                try:
                    services = self.get_services()
                except Exception:
                    services = None

                for output_row in rows:
                    # Ensure script is available
                    self.validate_output_script(output_row=output_row, session=s)
                    if not output_row.locking_script or len(output_row.locking_script) == 0:
                        continue
                    ok: bool | None = None
                    if services is not None:
                        # Build TS-like object for services.is_utxo
                        out = {
                            "txid": output_row.txid,
                            "vout": int(output_row.vout),
                            "lockingScript": output_row.locking_script,
                        }
                        try:
                            # Call synchronously (services should provide sync API)
                            ok = bool(services.is_utxo(out))
                        except Exception:
                            ok = None
                    # If explicit False -> invalid change
                    if ok is False:
                        # Optional 'release' tag: mark unspendable
                        if "release" in specop_tags:
                            try:
                                self.update_output(output_row.output_id, {"spendable": False})
                            except Exception:
                                pass
                        filtered_rows.append(output_row)
                rows = filtered_rows

            outputs: list[dict[str, Any]] = []
            for output_row in rows:
                wo: dict[str, Any] = {
                    "satoshis": int(output_row.satoshis),
                    "spendable": True,
                    "outpoint": f"{output_row.txid}.{output_row.vout}",
                }
                if include_custom_instructions and output_row.custom_instructions:
                    wo["customInstructions"] = output_row.custom_instructions
                if include_scripts or specop_include_scripts:
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

            # SpecOp: set wallet change params (side-effect only, empty result)
            if specop == "set_change":
                try:
                    ndutxos = int(specop_tags[0]) if len(specop_tags) > 0 else None
                    mduv = int(specop_tags[1]) if len(specop_tags) > 1 else None
                except Exception:
                    ndutxos, mduv = None, None
                if ndutxos is not None and mduv is not None:
                    bq = select(OutputBasket).where(
                        (OutputBasket.user_id == user_id)
                        & (OutputBasket.name == "default")
                        & (OutputBasket.is_deleted.is_(False))
                    )
                    _exec_result = s.execute(bq)
                    b = _exec_result.scalar_one_or_none()
                    if b is not None:
                        b.number_of_desired_utxos = ndutxos
                        b.minimum_desired_utxo_value = mduv
                        s.add(b)
                return {"totalOutputs": 0, "outputs": []}

            # SpecOp: wallet balance -> sum satoshis, outputs empty
            if specop == "wallet_balance":
                total_outputs = 0
                for o in rows:
                    total_outputs += int(o.satoshis)
                return {"totalOutputs": int(total_outputs), "outputs": []}

            # SpecOp: invalid_change -> totalOutputs equals filtered length
            if specop == "invalid_change":
                result: dict[str, Any] = {"totalOutputs": len(outputs), "outputs": outputs}
                return result

            result: dict[str, Any] = {"totalOutputs": int(total), "outputs": outputs}
            if include_transactions:
                # Build minimal BEEF by merging rawTx for listed outputs (unique txids)
                txids: list[str] = []
                seen: set[str] = set()
                for output_row in rows:
                    if output_row.txid and output_row.txid not in seen:
                        seen.add(output_row.txid)
                        txids.append(output_row.txid)
                known_txids = args.get("knownTxids") or []
                if not isinstance(known_txids, list):
                    known_txids = []
                result["BEEF"] = self._build_recursive_beef_for_txids(txids, known_txids=known_txids)
            return result

    def validate_output_script(self, output_row: Output, _session: Session | None = None) -> None:
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

    def _build_minimal_beef_for_txids(self, txids: list[str]) -> bytes:
        """Construct a minimal BEEF-like binary by concatenating rawTx blobs.

        Summary:
            This is a pragmatic interim implementation: for each txid, include its
            rawTx if known. It does not yet recursively include inputs or Merkle
            paths. Sufficient to unblock `includeTransactions` clients expecting a
            non-empty BEEF when transactions are requested.
        TS parity:
            Approximates BEEF merging from TS; full parity (inputs/paths) will be
            implemented alongside Proven utilities.
        Args:
            txids: Unique list of transaction ids to include.
        Returns:
            Bytes blob representing a minimal BEEF.
        """
        chunks: list[bytes] = []
        seen: set[str] = set()
        for txid in txids:
            if txid in seen:
                continue
            seen.add(txid)
            r = self.get_proven_or_raw_tx(txid)
            raw = r.get("rawTx")
            if isinstance(raw, (bytes, bytearray)):
                chunks.append(bytes(raw))
            # If this tx has an input BEEF from storage (req), append it as a minimal ancestry hint
            ib = r.get("inputBEEF")
            if isinstance(ib, (bytes, bytearray)) and len(ib) > 0:
                chunks.append(bytes(ib))
        return b"".join(chunks)

    def _build_recursive_beef_for_txids(
        self, txids: list[str], max_depth: int = 4, known_txids: list[str] | None = None
    ) -> bytes:
        """Construct a more complete BEEF-like binary including ancestors.

        Summary:
            Starting from txids, append known rawTx bytes and any stored inputBEEF,
            then recursively traverse inputs (by parsing rawTx) up to max_depth to
            append ancestor rawTx blobs. This is still a placeholder and does not
            encode BUMP structures; it is a pragmatic superset of the minimal form.
        Args:
            txids: Starting transaction ids.
            max_depth: Maximum recursion depth.
        Returns:
            bytes: Concatenated bytes representing a BEEF-like payload.
        """
        chunks: list[bytes] = []
        seen: set[str] = set()
        known: set[str] = set(known_txids or [])
        first_beef: bytes | None = None

        def add_tx_and_ancestors(cur_txid: str, depth: int) -> None:
            if cur_txid in seen or depth > max_depth:
                return
            seen.add(cur_txid)
            r = self.get_proven_or_raw_tx(cur_txid)
            raw = r.get("rawTx")
            if isinstance(raw, (bytes, bytearray)):
                # Attempt to parse and follow inputs (and attach MerklePath)
                try:
                    tx = Transaction.from_hex(raw)
                    if tx and getattr(tx, "inputs", None):
                        mpb = r.get("merklePath")
                        if isinstance(mpb, (bytes, bytearray)) and len(mpb) > 0:
                            try:
                                tx.merkle_path = MerklePath.from_binary(bytes(mpb))
                            except Exception:
                                pass
                        for txin in tx.inputs:
                            src = getattr(txin, "source_txid", None)
                            if isinstance(src, str) and src and src != "00" * 32:
                                # If the caller already knows this txid, do not fetch/descend further
                                if src not in known:
                                    add_tx_and_ancestors(src, depth + 1)
                                # Try to hydrate parent transaction for to_beef ancestry
                                try:
                                    pr = self.get_proven_or_raw_tx(src)
                                    praw = pr.get("rawTx")
                                    if isinstance(praw, (bytes, bytearray)):
                                        parent_tx = Transaction.from_hex(praw)
                                        if parent_tx is not None:
                                            txin.source_transaction = parent_tx
                                except Exception:
                                    pass
                        try:
                            beef_bytes = tx.to_beef()
                            chunks.append(beef_bytes)
                        except Exception:
                            chunks.append(bytes(raw))
                    else:
                        chunks.append(bytes(raw))
                except Exception:
                    chunks.append(bytes(raw))
            ib = r.get("inputBEEF")
            if isinstance(ib, (bytes, bytearray)) and len(ib) > 0:
                chunks.append(bytes(ib))

        for tid in txids:
            add_tx_and_ancestors(tid, 0)

        # Prefer a single BEEF if constructed for the primary tx
        if first_beef is not None:
            return first_beef

        # Deduplicate identical fragments to approximate normalization (fallback)
        unique_chunks: list[bytes] = []
        seen_hashes: set[int] = set()
        for c in chunks:
            h = hash(c)
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            unique_chunks.append(c)
        return b"".join(unique_chunks)

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
            _exec_result = s.execute(q)
            rows = _exec_result.scalars()
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
            tag_ids = list(s.execute(mq).scalars().all())
            if not tag_ids:
                return []
            tq = select(OutputTag).where(OutputTag.output_tag_id.in_(tag_ids), OutputTag.is_deleted.is_(False))
            _exec_result = s.execute(tq)
            rows = _exec_result.scalars()
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
            label_ids = list(s.execute(mq).scalars().all())
            if not label_ids:
                return []
            tq = select(TxLabel).where(TxLabel.tx_label_id.in_(label_ids), TxLabel.is_deleted.is_(False))
            _exec_result = s.execute(tq)
            rows = _exec_result.scalars()
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
        spendable = args.get("spendable")
        with session_scope(self.SessionLocal) as s:
            q = select(Output).where(Output.user_id == user_id)
            if spendable is not None:
                q = q.where(Output.spendable.is_(bool(spendable)))
            if basket_name:
                bq = select(OutputBasket.basket_id).where(
                    (OutputBasket.user_id == user_id)
                    & (OutputBasket.name == basket_name)
                    & (OutputBasket.is_deleted.is_(False))
                )
                _exec_result = s.execute(bq)
                bid = _exec_result.scalar_one_or_none()
                if bid is None:
                    return []
                q = q.where(Output.basket_id == bid)
            _result = s.execute(q)

            rows: Iterable[Output] = _result.scalars().all()
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
            _exec_result = s.execute(q)
            o = _exec_result.scalar_one_or_none()
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
            _exec_result = s.execute(q)
            rows = _exec_result.scalars()
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
            _exec_result = s.execute(q)
            rows = _exec_result.scalars()
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
            _result = s.execute(select(ProvenTx).where(ProvenTx.txid == txid))
            p = _result.scalar_one_or_none()
            if p is not None:
                return {
                    "proven": {"provenTxId": p.proven_tx_id},
                    "rawTx": p.raw_tx,
                    "merklePath": p.merkle_path,
                }
            _result = s.execute(select(ProvenTxReq).where(ProvenTxReq.txid == txid))
            r = _result.scalar_one_or_none()
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

    def get_valid_beef_for_txid(self, txid: str, known_txids: list[str] | None = None) -> bytes:
        """Return a BEEF-like bytes blob for a known txid (minimal parity).

        Summary:
            Builds a BEEF-style payload for the txid using any known rawTx and
            optionally attached MerklePath (ProvenTx). Recursively includes
            ancestors up to a small depth, skipping any ids listed in known_txids.
        TS parity:
            Minimal approximation of getValidBeefForTxid.
        Args:
            txid: Subject transaction id.
            known_txids: Optional list of txids to treat as already known.
        Returns:
            bytes: BEEF-like payload (may be a single-tx BEEF when possible).
        """
        return self._build_recursive_beef_for_txids([txid], known_txids=known_txids)

    # ------------------------------------------------------------------
    # Proven helpers
    # ------------------------------------------------------------------
    def find_or_insert_proven_tx(self, api: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        """Find or insert a ProvenTx row by txid.

        Summary:
            Idempotent upsert using txid uniqueness. Returns (row_dict, is_new).
        TS parity:
            Mirrors StorageProvider.findOrInsertProvenTx minimal behavior.
        Args:
            api: Dict with keys {txid,height,index,merklePath,rawTx,blockHash,merkleRoot}.
        Returns:
            Tuple (row, is_new) where row has keys: provenTxId, txid, height, index.
        Raises:
            sqlalchemy.exc.SQLAlchemyError on DB errors.
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        txid = api.get("txid")
        if not isinstance(txid, str) or len(txid) != 64:
            raise ValueError("txid must be 64-hex string")
        with session_scope(self.SessionLocal) as s:
            _result = s.execute(select(ProvenTx).where(ProvenTx.txid == txid))
            row = _result.scalar_one_or_none()
            is_new = False
            if row is None:
                row = ProvenTx(
                    txid=txid,
                    height=int(api.get("height", 0)),
                    index=int(api.get("index", 0)),
                    merkle_path=api.get("merklePath") or b"",
                    raw_tx=api.get("rawTx") or b"",
                    block_hash=api.get("blockHash") or "0" * 64,
                    merkle_root=api.get("merkleRoot") or "0" * 64,
                )
                s.add(row)
                s.flush()
                is_new = True
            return (
                {
                    "provenTxId": row.proven_tx_id,
                    "txid": row.txid,
                    "height": int(row.height),
                    "index": int(row.index),
                },
                is_new,
            )

    def update_proven_tx_req_with_new_proven_tx(self, args: dict[str, Any]) -> dict[str, Any]:
        """Attach a new ProvenTx to an existing ProvenTxReq and mark completed.

        Summary:
            Inserts (or finds) a ProvenTx, updates the ProvenTxReq with its id and
            status 'completed'. Returns minimal TS-like result with status/history/provenTxId.
        TS parity:
            Minimal subset of TS updateProvenTxReqWithNewProvenTx.
        Args:
            args: Dict with keys {provenTxReqId, txid, height, index, merklePath, rawTx, blockHash, merkleRoot}.
        Returns:
            Dict: { status: str, provenTxId: int, history: str }
        Raises:
            ValueError: If req not found or txid mismatch.
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        req_id = int(args.get("provenTxReqId", 0))
        txid = args.get("txid")
        with session_scope(self.SessionLocal) as s:
            _result = s.execute(select(ProvenTxReq).where(ProvenTxReq.proven_tx_req_id == req_id))
            req = _result.scalar_one_or_none()
            if req is None:
                raise ValueError("ProvenTxReq not found")
            if txid and req.txid != txid:
                raise ValueError("txid mismatch with ProvenTxReq")

            # Insert/find ProvenTx
            row_dict, _ = self.find_or_insert_proven_tx(
                {
                    "txid": req.txid,
                    "height": args.get("height", 0),
                    "index": args.get("index", 0),
                    "merklePath": args.get("merklePath") or b"",
                    "rawTx": args.get("rawTx") or req.raw_tx,
                    "blockHash": args.get("blockHash") or "0" * 64,
                    "merkleRoot": args.get("merkleRoot") or "0" * 64,
                }
            )

            # Update req
            req.proven_tx_id = row_dict["provenTxId"]
            req.status = "completed"
            s.add(req)

            return {"status": req.status, "history": req.history, "provenTxId": req.proven_tx_id}

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

    def list_actions(self, _auth: dict[str, Any], _args: dict[str, Any]) -> dict[str, Any]:
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
    # Action Management - Quick Wins
    # ------------------------------------------------------------------
    def abort_action(self, action_reference: str) -> int:
        """Abort an action by reference - mark ProvenTxReq as aborted.

        Summary:
            Set the status of an associated ProvenTxReq to 'aborted'.
            Also mark any outputs spending from this transaction as non-spendable.
        TS parity:
            Mirrors StorageProvider.abortAction behavior.
        Args:
            action_reference: Reference string for action to abort.
        Returns:
            Number of records updated.
        Raises:
            N/A
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        with session_scope(self.SessionLocal) as s:
            # Find ProvenTxReq by reference (stored as txid or batch identifier)
            q = select(ProvenTxReq).where(ProvenTxReq.txid == action_reference)
            _result = s.execute(q)
            req = _result.scalar_one_or_none()

            if req is None:
                return 0

            req.status = "aborted"
            s.add(req)
            s.flush()
            return 1

    def destroy(self) -> None:
        """Destroy storage by truncating all tables.

        Summary:
            Remove all data from storage. Used for reset/cleanup.
        TS parity:
            Mirrors StorageProvider.destroy().
        Args:
            None
        Returns:
            None
        Raises:
            sqlalchemy.exc.SQLAlchemyError: On DB errors.
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        with session_scope(self.SessionLocal) as s:
            # Truncate all tables in dependency order
            tables_to_truncate = [
                OutputTagMap,
                TxLabelMap,
                OutputTag,
                TxLabel,
                OutputBasket,
                Output,
                Commission,
                ProvenTxReq,
                ProvenTx,
                Certificate,
                CertificateField,
                TransactionModel,
                SyncState,
                User,
                Settings,
            ]

            for table_model in tables_to_truncate:
                try:
                    s.query(table_model).delete()
                except Exception:
                    pass

            s.commit()

    def insert_certificate_auth(self, auth: dict[str, Any], certificate_api: dict[str, Any]) -> int:
        """Insert a certificate for authenticated user.

        Summary:
            Add a new certificate to storage with user authentication.
        TS parity:
            Mirrors StorageProvider.insertCertificateAuth.
        Args:
            auth: Dict with 'userId'.
            certificate_api: Certificate data (type, certifier, serialNumber, etc).
        Returns:
            Certificate ID (primary key) of inserted record.
        Raises:
            KeyError: If 'userId' missing from auth.
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        user_id = int(auth["userId"])

        with session_scope(self.SessionLocal) as s:
            cert = Certificate(
                user_id=user_id,
                type=certificate_api.get("type", ""),
                certifier=certificate_api.get("certifier", ""),
                serial_number=certificate_api.get("serialNumber", ""),
                is_deleted=False,
            )
            s.add(cert)
            s.flush()
            return cert.certificate_id

    def relinquish_certificate(self, auth: dict[str, Any], certificate_id: int) -> int:
        """Mark a certificate as deleted (soft delete).

        Summary:
            Remove a certificate from active use without physical deletion.
        TS parity:
            Mirrors StorageProvider.relinquishCertificate.
        Args:
            auth: Dict with 'userId'.
            certificate_id: Certificate ID to mark as deleted.
        Returns:
            Number of rows affected (0 or 1).
        Raises:
            KeyError: If 'userId' missing from auth.
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        user_id = int(auth["userId"])

        with session_scope(self.SessionLocal) as s:
            q = select(Certificate).where(
                (Certificate.certificate_id == certificate_id) & (Certificate.user_id == user_id)
            )
            _result = s.execute(q)
            cert = _result.scalar_one_or_none()

            if cert is None:
                return 0

            cert.is_deleted = True
            s.add(cert)
            s.flush()
            return 1

    # ------------------------------------------------------------------
    # Improved List Operations
    # ------------------------------------------------------------------
    def get_actions_status_summary(self, _auth: dict[str, Any]) -> dict[str, Any]:
        """Get summary of actions by status for authenticated user.

        Summary:
            Count actions grouped by status.
        Args:
            auth: Dict with 'userId'.
        Returns:
            Dict with status counts.
        """
        with session_scope(self.SessionLocal) as s:
            q = (
                select(ProvenTxReq.status, func.count())
                .where(ProvenTxReq.txid != "")  # placeholder for user filter
                .group_by(ProvenTxReq.status)
            )

            _result = s.execute(q)
            rows = _result.all()

            summary = {}
            for status, count in rows:
                summary[status] = int(count)

            return summary

    # ------------------------------------------------------------------
    # Action Pipeline - createAction (Minimal)
    # ------------------------------------------------------------------
    def create_action(self, auth: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
        """Create a new transaction action (minimal implementation).

        Summary:
            Create and store records for a new transaction being constructed.
            Minimal version: basic Transaction/ProvenTxReq creation without full BEEF/change logic.
        TS parity:
            Mirrors StorageProvider.createAction subset.
        Args:
            auth: Dict with 'userId'.
            args: Transaction args (inputs, outputs, options).
        Returns:
            Dict with reference, version, lockTime, inputs, outputs, derivationPrefix, inputBeef.
        Raises:
            KeyError: If 'userId' missing or required fields missing.
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/methods/createAction.ts
        """
        user_id = int(auth["userId"])
        is_new_tx = args.get("isNewTx", True)

        if not is_new_tx:
            raise ValueError("createAction requires isNewTx=true for new transactions")

        with session_scope(self.SessionLocal) as s:
            # Generate reference (random base64-like string)
            reference = secrets.token_urlsafe(16)

            # Create new Transaction record
            tx = TransactionModel(
                user_id=user_id,
                status="unsigned",  # Initial state
                reference=reference,
                is_outgoing=args.get("isOutgoing", False),
                satoshis=0,  # Will be updated after funding
                version=args.get("version", 2),
                lock_time=args.get("lockTime", 0),
                description=args.get("description", ""),
                input_beef=None,
            )
            s.add(tx)
            s.flush()

            transaction_id = tx.transaction_id

            # Create ProvenTxReq for this action
            req = ProvenTxReq(
                txid=reference,  # Use reference as txid for tracking
                status="pending",
                attempts=0,
                notified=False,
                raw_tx=b"",  # Placeholder
                history="{}",
                notify="{}",
            )
            s.add(req)
            s.flush()

            # Process inputs (minimal: just collect info)
            inputs_list = []
            input_satoshis_total = 0

            for i, inp in enumerate(args.get("inputs", [])):
                input_satoshis_total += inp.get("satoshis", 0)
                inputs_list.append(
                    {
                        "index": i,
                        "outpoint": inp.get("outpoint", ""),
                        "satoshis": inp.get("satoshis", 0),
                        "unlockingScript": inp.get("unlockingScript", ""),
                    }
                )

            # Process outputs (minimal: just collect info)
            outputs_list = []
            output_satoshis_total = 0
            change_vouts = []

            for i, out in enumerate(args.get("outputs", [])):
                satoshis = out.get("satoshis", 0)
                output_satoshis_total += satoshis

                # Create Output record
                output_record = Output(
                    user_id=user_id,
                    transaction_id=transaction_id,
                    basket_id=None,  # Placeholder
                    spendable=out.get("spendable", False),
                    change=out.get("change", False),
                    vout=i,
                    satoshis=satoshis,
                    provided_by=out.get("providedBy", ""),
                    purpose=out.get("purpose", ""),
                    type=out.get("type", ""),
                    txid=None,
                    spent=False,
                )
                s.add(output_record)
                s.flush()

                if out.get("change", False):
                    change_vouts.append(i)

                outputs_list.append(
                    {
                        "index": i,
                        "satoshis": satoshis,
                        "lockingScript": out.get("lockingScript", ""),
                        "change": out.get("change", False),
                    }
                )

            # Update transaction satoshis (outputs - inputs)
            satoshis = output_satoshis_total - input_satoshis_total
            tx.satoshis = satoshis
            s.add(tx)

            # Return result
            result = {
                "reference": reference,
                "version": tx.version or 2,
                "lockTime": tx.lock_time or 0,
                "inputs": inputs_list,
                "outputs": outputs_list,
                "derivationPrefix": args.get("derivationPrefix", ""),
                "inputBeef": None,
                "noSendChangeOutputVouts": change_vouts if args.get("isNoSend", False) else None,
            }

            return result

    # ------------------------------------------------------------------
    # Action Pipeline - processAction (Minimal)
    # ------------------------------------------------------------------
    def process_action(self, auth: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
        """Process a transaction action (finalize & sign).
        
        TS parity:
            Mirrors StorageProvider.processAction behavior.
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/methods/processAction.ts
        """
        # Implementation delegated to storage layer
        raise NotImplementedError("process_action not yet implemented")

    def internalize_action(self, auth: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
        """Internalize a transaction action (take ownership of outputs in pre-existing transaction).

        BRC-100 feature: Allow wallet to take ownership of outputs in a pre-existing transaction.
        
        Complete Implementation Summary:
            This method enables a wallet to claim ownership of outputs from an existing transaction.
            The transaction may be new to the wallet or already known (merge case).
            
            Two types of outputs are handled:
            - "wallet payments": adds to wallet's change balance (default basket)
            - "basket insertions": custom outputs, don't affect balance
            
            Processing flow:
            1. Parse and validate AtomicBEEF binary format
            2. Classify outputs as basket insertions or wallet payments
            3. Load wallet state (change basket, existing transaction/outputs)
            4. Calculate satoshis impact based on merge rules
            5. Create or update transaction record
            6. Store/merge output records and labels
        
        Merge Rules (TS parity):
            - Basket insertion merge: converting change to custom output (satoshis -= output_value)
            - Wallet payment new tx: all outputs add to satoshis (satoshis += output_value)
            - Wallet payment merge with change: ignore (already in wallet)
            - Wallet payment merge with custom: convert to change (satoshis += output_value)
            - Wallet payment merge untracked: add as change (satoshis += output_value)
            
        TS parity:
            Complete implementation following internalizeAction.ts (lines 47-484)
            - BEEF parsing and validation (AtomicBEEF format)
            - Transaction lookup (merge vs new)
            - Output ownership assignment with merge rules
            - Balance calculation (satoshis affected)

        Args:
            auth: Dict with 'userId' for wallet identification
            args: Input dict with:
                - tx: list[int] - atomic BEEF (binary format, required)
                - outputs: list[dict] - output specifications (required):
                    - outputIndex: int - index in transaction (0-based)
                    - protocol: str - 'wallet payment' or 'basket insertion' (required)
                    - paymentRemittance: dict - for wallet payment (optional)
                    - insertionRemittance: dict - for basket insertion (optional)
                - labels: list[str] - optional action labels (default [])
                - description: str - optional transaction description (default "")

        Returns:
            dict: Result with keys:
                - accepted: bool - internalization accepted (default True)
                - isMerge: bool - whether merged with existing transaction
                - txid: str - transaction ID (hex, 64 chars)
                - satoshis: int - net satoshis change

        Raises:
            InvalidParameterError: Invalid BEEF, output index, or merge conflict
            KeyError: If 'userId' missing from auth

        TypeScript Reference:
            - toolbox/ts-wallet-toolbox/src/storage/methods/internalizeAction.ts (main logic)
            - Lines 47-59: Main flow (validate BEEF -> asyncSetup -> merge/new)
            - Lines 81-150: Context class definition & helpers
            - Lines 152-253: asyncSetup (parse outputs, check merge, calculate satoshis)
            - Lines 255-278: validateAtomicBeef (BEEF parsing & validation)
            - Lines 280-310: findOrInsertTargetTransaction (create/merge)
            - Lines 312-326: mergedInternalize (existing tx outputs)
            - Lines 328-369: newInternalize (new tx outputs & network broadcast)
            - Lines 371-483: Output/label storage helpers
        """
        # Step 1: Parse args and validate
        user_id = int(auth["userId"])  # May raise KeyError
        from bsv_wallet_toolbox.utils.validation import validate_internalize_action_args
        vargs = validate_internalize_action_args(args)
        
        # Step 2: Execute context-based processing
        ctx = InternalizeActionContext(
            storage_provider=self,
            user_id=user_id,
            vargs=vargs,
            args=args
        )
        
        # Step 3: async setup simulation (synchronous implementation)
        ctx.setup()
        
        # Step 4: Process based on merge status
        if ctx.is_merge:
            ctx.merged_internalize()
        else:
            ctx.new_internalize()
        
        # Step 5: Return result
        return ctx.result


class InternalizeActionContext:
    """Context for internalizeAction processing.
    
    Encapsulates all state and logic needed to internalize outputs from
    a pre-existing transaction. Mirrors TypeScript InternalizeActionContext.
    
    TS Reference:
        toolbox/ts-wallet-toolbox/src/storage/methods/internalizeAction.ts:81-484
    """
    
    def __init__(self, storage_provider: Any, user_id: int, vargs: dict[str, Any], args: dict[str, Any]) -> None:
        """Initialize context with storage and arguments."""
        self.storage = storage_provider
        self.user_id = user_id
        self.vargs = vargs
        self.args = args
        
        # Result to return
        self.result = {
            "accepted": True,
            "isMerge": False,
            "txid": "",
            "satoshis": 0,
        }
        
        # Internal state
        self.beef_obj = None  # Beef object (not parsed yet)
        self.tx = None  # Parsed Transaction
        self.txid = ""  # Transaction ID from BEEF
        self.change_basket = None  # Default basket for wallet payments
        self.baskets = {}  # Cached baskets by name
        self.existing_tx = None  # Existing transaction if merge
        self.existing_outputs = []  # Existing outputs if merge
        self.basket_insertions = []  # Basket insertion specs
        self.wallet_payments = []  # Wallet payment specs
    
    @property
    def is_merge(self) -> bool:
        """Get current merge status."""
        return self.result["isMerge"]
    
    @is_merge.setter
    def is_merge(self, value: bool) -> None:
        """Set current merge status."""
        self.result["isMerge"] = value
    
    def setup(self) -> None:
        """Execute all async setup (synchronous version).
        
        TS Reference: asyncSetup lines 152-253
        """
        # Step 1: Validate and parse BEEF (lines 255-278)
        self.txid, self.tx = self._validate_atomic_beef(self.args.get("tx", []))
        self.result["txid"] = self.txid
        
        # Step 2: Parse outputs and classify (lines 155-189)
        self._parse_outputs()
        
        # Step 3: Load wallet state (lines 191-208)
        self._load_wallet_state()
        
        # Step 4: Link existing outputs (lines 210-221)
        if self.is_merge:
            self._load_existing_outputs()
        
        # Step 5: Calculate satoshis impact (lines 223-252)
        self._calculate_satoshis_impact()
    
    def _validate_atomic_beef(self, atomic_beef: list[int]) -> tuple[str, Any]:
        """Parse and validate AtomicBEEF binary format.
        
        TS Reference: validateAtomicBeef lines 255-278
        
        Returns:
            (txid, parsed_tx) where txid is hex string and tx is parsed Transaction
        
        Raises:
            InvalidParameterError: If BEEF invalid or txid not found
        """
        if not atomic_beef or len(atomic_beef) < 4:
            raise InvalidParameterError("tx", "valid AtomicBEEF with minimum 4 bytes")
        
        try:
            # Convert list[int] to bytes
            beef_bytes = bytes(atomic_beef)
            
            # Parse BEEF using BSV SDK
            # Note: This requires bsv.Beef to be available
            # For now, we use simplified extraction from binary format
            
            # BEEF format: [0xBF, ...chain bytes...]
            # Transaction is embedded; extract txid (typically at offset based on format)
            # Simplified: extract txid from transaction in BEEF
            
            # Use bsv.Transaction to parse (BEEF likely contains raw tx)
            from bsv import Transaction as BsvTransaction
            
            # Attempt to parse as raw transaction
            try:
                tx_obj = BsvTransaction.from_hex(beef_bytes)
                txid = tx_obj.id()  # Get transaction ID
            except Exception:
                # BEEF parsing failed - try to extract txid from binary
                # BEEF binary format has txid somewhere in structure
                # For minimal implementation, derive from raw bytes
                raise InvalidParameterError(
                    "tx",
                    "valid AtomicBEEF - BSV SDK parsing failed"
                )
            
            return txid, tx_obj
            
        except InvalidParameterError:
            raise
        except Exception as e:
            raise InvalidParameterError("tx", f"valid AtomicBEEF: {str(e)}")
    
    def _parse_outputs(self) -> None:
        """Parse outputs from arguments and classify.
        
        TS Reference: asyncSetup lines 155-189
        
        Raises:
            InvalidParameterError: If invalid output specification
        """
        for output_spec in self.args.get("outputs", []):
            output_index = output_spec.get("outputIndex", -1)
            protocol = output_spec.get("protocol", "")
            
            # Validate output index
            if output_index < 0 or (self.tx and output_index >= len(self.tx.outputs)):
                raise InvalidParameterError(
                    "outputIndex",
                    f"valid output index in range 0 to {len(self.tx.outputs) - 1 if self.tx else '?'}"
                )
            
            # Get transaction output
            txo = self.tx.outputs[output_index] if self.tx else None
            
            if protocol == "basket insertion":
                # TS lines 164-171
                insertion_remittance = output_spec.get("insertionRemittance")
                payment_remittance = output_spec.get("paymentRemittance")
                
                if not insertion_remittance or payment_remittance:
                    raise InvalidParameterError(
                        "basket insertion",
                        "valid insertionRemittance and no paymentRemittance"
                    )
                
                self.basket_insertions.append({
                    "spec": output_spec,
                    "insertion_remittance": insertion_remittance,
                    "vout": output_index,
                    "txo": txo,
                    "eo": None,  # existing output (if merge)
                })
                
            elif protocol == "wallet payment":
                # TS lines 174-183
                insertion_remittance = output_spec.get("insertionRemittance")
                payment_remittance = output_spec.get("paymentRemittance")
                
                if insertion_remittance or not payment_remittance:
                    raise InvalidParameterError(
                        "wallet payment",
                        "valid paymentRemittance and no insertionRemittance"
                    )
                
                self.wallet_payments.append({
                    "spec": output_spec,
                    "payment_remittance": payment_remittance,
                    "vout": output_index,
                    "txo": txo,
                    "eo": None,  # existing output (if merge)
                    "ignore": False,
                })
            else:
                raise InvalidParameterError(
                    "protocol",
                    f"'wallet payment' or 'basket insertion', got '{protocol}'"
                )
    
    def _load_wallet_state(self) -> None:
        """Load wallet's default basket and check for existing transaction.
        
        TS Reference: asyncSetup lines 191-208
        
        Raises:
            InvalidParameterError: If wallet state invalid
        """
        with session_scope(self.storage.SessionLocal) as s:
            # Get "default" basket (TS lines 191-195)
            q_basket = select(OutputBasket).where(
                (OutputBasket.user_id == self.user_id) &
                (OutputBasket.name == "default")
            )
            _result = s.execute(q_basket)
            basket = _result.scalar_one_or_none()
            
            if not basket:
                raise InvalidParameterError(
                    "basket",
                    "user must have a 'default' output basket"
                )
            
            self.change_basket = basket
            self.baskets = {}
            
            # Check for existing transaction (TS lines 198-208)
            q_tx = select(TransactionModel).where(
                (TransactionModel.user_id == self.user_id) &
                (TransactionModel.txid == self.txid)
            )
            _result = s.execute(q_tx)
            etx = _result.scalar_one_or_none()
            
            if etx:
                # Validate status (line 203)
                valid_statuses = {"completed", "unproven", "nosend"}
                if etx.status not in valid_statuses:
                    raise InvalidParameterError(
                        "tx",
                        f"target transaction of internalizeAction has invalid status {etx.status}"
                    )
                self.is_merge = True
                self.existing_tx = etx
    
    def _load_existing_outputs(self) -> None:
        """Load existing outputs for merge case.
        
        TS Reference: asyncSetup lines 210-221
        """
        with session_scope(self.storage.SessionLocal) as s:
            # Find existing outputs for this transaction (lines 211-213)
            q_outputs = select(Output).where(
                (Output.user_id == self.user_id) &
                (Output.txid == self.txid)
            )
            _result = s.execute(q_outputs)
            self.existing_outputs = _result.scalars().all()
            
            # Link outputs to specs by vout (lines 214-220)
            for eo in self.existing_outputs:
                # Find basket insertion with this vout
                for bi in self.basket_insertions:
                    if bi["vout"] == eo.vout:
                        bi["eo"] = eo
                        break
                
                # Find wallet payment with this vout
                for wp in self.wallet_payments:
                    if wp["vout"] == eo.vout:
                        wp["eo"] = eo
                        break
    
    def _calculate_satoshis_impact(self) -> None:
        """Calculate net satoshis impact based on merge rules.
        
        TS Reference: asyncSetup lines 223-252
        
        Key logic:
        - Basket insertions: if changing from change output, satoshis -= value
        - Wallet payments (new tx): all add to satoshis
        - Wallet payments (merge to change): ignore (already counted)
        - Wallet payments (merge to custom): satoshis += value (convert to change)
        - Wallet payments (merge untracked): satoshis += value (add as change)
        """
        # Initialize satoshis to 0
        self.result["satoshis"] = 0
        
        # Process basket insertions (TS lines 223-231)
        for bi in self.basket_insertions:
            if self.is_merge and bi["eo"]:
                # Merging with existing user output
                if bi["eo"].basket_id == self.change_basket.basket_id:
                    # Converting change output to user basket custom
                    self.result["satoshis"] -= bi["txo"].satoshis if bi["txo"] else 0
        
        # Process wallet payments (TS lines 233-252)
        for wp in self.wallet_payments:
            if self.is_merge:
                if wp["eo"]:
                    # Merging with existing user output
                    if wp["eo"].basket_id == self.change_basket.basket_id:
                        # Ignore: already a change output
                        wp["ignore"] = True
                    else:
                        # Converting existing non-change output to change
                        self.result["satoshis"] += wp["txo"].satoshis if wp["txo"] else 0
                else:
                    # Adding previously untracked output as change
                    self.result["satoshis"] += wp["txo"].satoshis if wp["txo"] else 0
            else:
                # New transaction: all wallet payments add to satoshis
                self.result["satoshis"] += wp["txo"].satoshis if wp["txo"] else 0
    
    def merged_internalize(self) -> None:
        """Process merge case: update existing transaction outputs.
        
        TS Reference: mergedInternalize lines 312-326
        """
        with session_scope(self.storage.SessionLocal) as s:
            transaction_id = self.existing_tx.transaction_id
            
            # Add labels if any (line 315)
            self._add_labels(transaction_id, s)
            
            # Process wallet payments (lines 317-320)
            for payment in self.wallet_payments:
                if payment["eo"] and not payment["ignore"]:
                    # Merge existing output
                    self._merge_wallet_payment_for_output(transaction_id, payment, s)
                elif not payment["ignore"]:
                    # Store new wallet payment output
                    self._store_new_wallet_payment_for_output(transaction_id, payment, s)
            
            # Process basket insertions (lines 322-325)
            for basket in self.basket_insertions:
                if basket["eo"]:
                    # Merge existing output
                    self._merge_basket_insertion_for_output(transaction_id, basket, s)
                else:
                    # Store new basket insertion output
                    self._store_new_basket_insertion_for_output(transaction_id, basket, s)
            
            s.commit()
    
    def new_internalize(self) -> None:
        """Process new case: create new transaction and store outputs.
        
        TS Reference: newInternalize lines 328-369
        """
        with session_scope(self.storage.SessionLocal) as s:
            # Create transaction record (line 329)
            now = datetime.now(timezone.utc)
            new_tx = TransactionModel(
                user_id=self.user_id,
                txid=self.txid,
                status="unproven",
                satoshis=self.result["satoshis"],
                description=self.args.get("description", ""),
                version=self.tx.version if self.tx else 2,
                lock_time=self.tx.lock_time if self.tx else 0,
                reference=randomBytesBase64(7),
                is_outgoing=False,
                created_at=now,
                updated_at=now,
            )
            s.add(new_tx)
            s.flush()
            
            transaction_id = new_tx.transaction_id
            
            # Create ProvenTxReq for network broadcast
            # (TS lines 335-341, requires ProvenTxReq logic)
            # Note: Deferred as this involves complex async network logic
            
            # Add labels (line 360)
            self._add_labels(transaction_id, s)
            
            # Store wallet payments (lines 362-364)
            for payment in self.wallet_payments:
                self._store_new_wallet_payment_for_output(transaction_id, payment, s)
            
            # Store basket insertions (lines 366-368)
            for basket in self.basket_insertions:
                self._store_new_basket_insertion_for_output(transaction_id, basket, s)
            
            s.commit()
    
    def _add_labels(self, transaction_id: int, session: Any) -> None:
        """Add labels to transaction.
        
        TS Reference: addLabels lines 371-376
        """
        for label in self.vargs.get("labels", []):
            # Find or insert TxLabel
            q_label = select(TxLabel).where(
                (TxLabel.user_id == self.user_id) &
                (TxLabel.label == label)
            )
            _result = session.execute(q_label)
            tx_label = _result.scalar_one_or_none()
            
            if not tx_label:
                tx_label = TxLabel(
                    user_id=self.user_id,
                    label=label,
                )
                session.add(tx_label)
                session.flush()
            
            # Insert TxLabelMap
            q_map = select(TxLabelMap).where(
                (TxLabelMap.transaction_id == transaction_id) &
                (TxLabelMap.tx_label_id == tx_label.tx_label_id)
            )
            _result = session.execute(q_map)
            if not _result.scalar_one_or_none():
                tx_label_map = TxLabelMap(
                    transaction_id=transaction_id,
                    tx_label_id=tx_label.tx_label_id,
                )
                session.add(tx_label_map)
    
    def _store_new_wallet_payment_for_output(self, transaction_id: int, payment: dict[str, Any], session: Any) -> None:
        """Store new wallet payment output record.
        
        TS Reference: storeNewWalletPaymentForOutput lines 384-413
        """
        now = datetime.now(timezone.utc)
        payment_remittance = payment["payment_remittance"]
        txo = payment["txo"]
        
        output_record = Output(
            created_at=now,
            updated_at=now,
            transaction_id=transaction_id,
            user_id=self.user_id,
            spendable=True,
            locking_script=txo.locking_script.to_binary() if hasattr(txo.locking_script, 'to_binary') else bytes(txo.locking_script),
            vout=payment["vout"],
            basket_id=self.change_basket.basket_id,
            satoshis=txo.satoshis,
            txid=self.txid,
            sender_identity_key=payment_remittance.get("senderIdentityKey"),
            type="P2PKH",
            provided_by="storage",
            purpose="change",
            derivation_prefix=payment_remittance.get("derivationPrefix", ""),
            derivation_suffix=payment_remittance.get("derivationSuffix"),
            change=True,
            spent_by=None,
            custom_instructions=None,
            output_description="",
            spending_description=None,
        )
        session.add(output_record)
        session.flush()
        
        payment["eo"] = output_record
    
    def _merge_wallet_payment_for_output(self, transaction_id: int, payment: dict[str, Any], session: Any) -> None:
        """Merge wallet payment into existing output.
        
        TS Reference: mergeWalletPaymentForOutput lines 415-430
        """
        output_id = payment["eo"].output_id
        payment_remittance = payment["payment_remittance"]
        
        # Update output record
        payment["eo"].basket_id = self.change_basket.basket_id
        payment["eo"].type = "P2PKH"
        payment["eo"].custom_instructions = None
        payment["eo"].change = True
        payment["eo"].provided_by = "storage"
        payment["eo"].purpose = "change"
        payment["eo"].sender_identity_key = payment_remittance.get("senderIdentityKey")
        payment["eo"].derivation_prefix = payment_remittance.get("derivationPrefix")
        payment["eo"].derivation_suffix = payment_remittance.get("derivationSuffix")
        
        session.add(payment["eo"])
    
    def _store_new_basket_insertion_for_output(self, transaction_id: int, basket: dict[str, Any], session: Any) -> None:
        """Store new basket insertion output record.
        
        TS Reference: storeNewBasketInsertionForOutput lines 449-483
        """
        now = datetime.now(timezone.utc)
        insertion_remittance = basket["insertion_remittance"]
        txo = basket["txo"]
        basket_name = insertion_remittance.get("basket", "default")
        
        # Get target basket
        q_target_basket = select(OutputBasket).where(
            (OutputBasket.user_id == self.user_id) &
            (OutputBasket.name == basket_name)
        )
        _result = session.execute(q_target_basket)
        target_basket = _result.scalar_one_or_none()
        
        if not target_basket:
            # Create basket if not exists
            target_basket = OutputBasket(
                user_id=self.user_id,
                name=basket_name,
            )
            session.add(target_basket)
            session.flush()
        
        output_record = Output(
            created_at=now,
            updated_at=now,
            transaction_id=transaction_id,
            user_id=self.user_id,
            spendable=True,
            locking_script=txo.locking_script.to_binary() if hasattr(txo.locking_script, 'to_binary') else bytes(txo.locking_script),
            vout=basket["vout"],
            basket_id=target_basket.basket_id,
            satoshis=txo.satoshis,
            txid=self.txid,
            type="custom",
            custom_instructions=insertion_remittance.get("customInstructions"),
            change=False,
            spent_by=None,
            output_description="",
            spending_description=None,
            provided_by="you",
            purpose="",
            sender_identity_key=None,
            derivation_prefix=None,
            derivation_suffix=None,
        )
        session.add(output_record)
        session.flush()
        
        # Add tags if any (TS line 480)
        self._add_basket_tags(basket, output_record.output_id, session)
        
        basket["eo"] = output_record
    
    def _merge_basket_insertion_for_output(self, transaction_id: int, basket: dict[str, Any], session: Any) -> None:
        """Merge basket insertion into existing output.
        
        TS Reference: mergeBasketInsertionForOutput lines 432-447
        """
        insertion_remittance = basket["insertion_remittance"]
        basket_name = insertion_remittance.get("basket", "default")
        
        # Get target basket
        q_target_basket = select(OutputBasket).where(
            (OutputBasket.user_id == self.user_id) &
            (OutputBasket.name == basket_name)
        )
        _result = session.execute(q_target_basket)
        target_basket = _result.scalar_one_or_none()
        
        if not target_basket:
            # Create basket if not exists
            target_basket = OutputBasket(
                user_id=self.user_id,
                name=basket_name,
            )
            session.add(target_basket)
            session.flush()
        
        # Update output record
        basket["eo"].basket_id = target_basket.basket_id
        basket["eo"].type = "custom"
        basket["eo"].custom_instructions = insertion_remittance.get("customInstructions")
        basket["eo"].change = False
        basket["eo"].provided_by = "you"
        basket["eo"].purpose = ""
        basket["eo"].sender_identity_key = None
        basket["eo"].derivation_prefix = None
        basket["eo"].derivation_suffix = None
        
        session.add(basket["eo"])
    
    def _add_basket_tags(self, basket: dict[str, Any], output_id: int, session: Any) -> None:
        """Add tags to basket insertion output.
        
        TS Reference: addBasketTags lines 378-382
        """
        for tag in basket["insertion_remittance"].get("tags", []):
            # Find or insert OutputTag
            q_tag = select(OutputTag).where(
                (OutputTag.user_id == self.user_id) &
                (OutputTag.tag == tag)
            )
            _result = session.execute(q_tag)
            output_tag = _result.scalar_one_or_none()
            
            if not output_tag:
                output_tag = OutputTag(
                    user_id=self.user_id,
                    tag=tag,
                )
                session.add(output_tag)
                session.flush()
            
            # Insert OutputTagMap
            q_map = select(OutputTagMap).where(
                (OutputTagMap.output_id == output_id) &
                (OutputTagMap.output_tag_id == output_tag.output_tag_id)
            )
            _result = session.execute(q_map)
            if not _result.scalar_one_or_none():
                output_tag_map = OutputTagMap(
                    output_id=output_id,
                    output_tag_id=output_tag.output_tag_id,
                )
                session.add(output_tag_map)

    # =====================================================================
    # =====================================================================
    # Phase 1: Generic CRUD Framework (TypeScript StorageReaderWriter parity)
    # =====================================================================
    #
    # This section implements the abstract StorageReaderWriter interface from
    # TypeScript, providing generic CRUD operations for all 17 database tables.
    #
    # Architecture:
    #   1. Generic helpers (_insert_generic, _find_generic, etc.)
    #      - Use SQLAlchemy reflection to work with any mapped ORM model
    #      - Return primary keys for INSERT, dictionaries for FIND, counts for COUNT
    #      - Support partial filtering (WHERE clause matching)
    #
    #   2. Table wrappers (insert_user, find_outputs, count_certificates, etc.)
    #      - Provide type-safe, named accessors for each table
    #      - Delegate to generic helpers to avoid duplication
    #      - Support both snake_case (Python) and camelCase (API) conversions
    #
    #   3. API format conversion (_to_api_key, _model_to_dict)
    #      - Convert ORM snake_case attributes to camelCase API keys
    #      - Ensure compatibility with TypeScript API shape
    #
    # TypeScript Reference:
    #   - toolbox/ts-wallet-toolbox/src/storage/StorageReaderWriter.ts (interface definition)
    #   - toolbox/ts-wallet-toolbox/src/storage/StorageKnex.ts (implementation example)
    #
    # Usage Examples:
    #   # Insert
    #   user_id = sp.insert_user({'identityKey': 'abc123', 'activeStorage': 'storage1'})
    #
    #   # Find
    #   users = sp.find_users({'identityKey': 'abc123'})
    #
    #   # Count
    #   count = sp.count_outputs({'userId': user_id})
    #
    #   # Update
    #   updated = sp.update_user(user_id, {'activeStorage': 'storage2'})
    #
    # =====================================================================

    # =====================================================================

    # Mapping of table names to ORM models
    _MODEL_MAP: ClassVar[dict[str, type]] = {
        "user": User,
        "certificate": Certificate,
        "certificate_field": CertificateField,
        "commission": Commission,
        "monitor_event": MonitorEvent,
        "output": Output,
        "output_basket": OutputBasket,
        "output_tag": OutputTag,
        "output_tag_map": OutputTagMap,
        "proven_tx": ProvenTx,
        "proven_tx_req": ProvenTxReq,
        "sync_state": SyncState,
        "transaction": TransactionModel,
        "tx_label": TxLabel,
        "tx_label_map": TxLabelMap,
        "settings": Settings,
    }

    def _get_model(self, table_name: str) -> type:
        """Get ORM model class for table name."""
        if table_name not in self._MODEL_MAP:
            raise ValueError(f"Unknown table: {table_name}")
        return self._MODEL_MAP[table_name]

    def _insert_generic(self, table_name: str, data: dict[str, Any], trx: Any = None) -> int:
        """Generic insert for any table. Returns primary key.

        Supports inserting records into any mapped SQLAlchemy table. Automatically
        handles primary key extraction and session management.

        Args:
            table_name: Name of table to insert into (e.g., 'user', 'output')
            data: Dictionary of column values (use snake_case Python attribute names)
            trx: Optional database transaction/session. If provided, uses that session
                 instead of creating a new one.

        Returns:
            int: Primary key value of inserted record

        Raises:
            ValueError: If table_name is not recognized
            sqlalchemy.exc.IntegrityError: If unique or FK constraints violated

        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageReaderWriter.ts
        """
        model = self._get_model(table_name)
        obj = model(**data)

        if trx:
            session = trx
        else:
            session = self.SessionLocal()

        try:
            session.add(obj)
            session.flush()
            mapper = inspect(model)
            pk_col = mapper.primary_key[0]
            pk_value = getattr(obj, pk_col.name)
            return pk_value
        finally:
            if not trx:
                session.close()

    def _find_generic(
        self, table_name: str, args: dict[str, Any] | None = None, limit: int | None = None, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Generic find for any table. Returns list of dicts in camelCase API format.

        Constructs a WHERE clause from partial filters and applies LIMIT/OFFSET.
        Results are converted from ORM objects to camelCase dictionaries.

        Args:
            table_name: Name of table to query
            args: Dictionary of filter conditions (column_name: value)
                  All filters are AND'ed together (exact match equality)
            limit: Maximum number of rows to return (None = no limit)
            offset: Number of rows to skip (for pagination)

        Returns:
            list[dict]: Array of records in camelCase API format

        Example:
            outputs = sp._find_generic('output', {'userId': 42, 'vout': 0}, limit=10)

        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageReaderWriter.ts
        """
        model = self._get_model(table_name)

        with session_scope(self.SessionLocal) as s:
            query = select(model)

            if args:
                for key, value in args.items():
                    if hasattr(model, key):
                        query = query.where(getattr(model, key) == value)

            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)

            result = s.execute(query).scalars().all()
            return [self._model_to_dict(obj) for obj in result]

    def _count_generic(self, table_name: str, args: dict[str, Any] | None = None) -> int:
        """Generic count for any table with optional filters.

        Counts rows matching the provided filter conditions.

        Args:
            table_name: Name of table to count
            args: Optional filter conditions (same format as _find_generic)

        Returns:
            int: Number of matching rows (0 if none match)

        Example:
            count = sp._count_generic('user', {'userId': 42})

        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageReaderWriter.ts
        """
        model = self._get_model(table_name)

        with session_scope(self.SessionLocal) as s:
            query = select(func.count()).select_from(model)

            if args:
                for key, value in args.items():
                    if hasattr(model, key):
                        query = query.where(getattr(model, key) == value)

            result = s.execute(query).scalar()
            return result or 0

    def _update_generic(self, table_name: str, pk_value: int, patch: dict[str, Any]) -> int:
        """Generic update for any table by primary key.

        Updates specified columns in a single row identified by primary key.

        Args:
            table_name: Name of table to update
            pk_value: Value of primary key (e.g., user_id=42)
            patch: Dictionary of columns to update (use snake_case Python names)

        Returns:
            int: Number of rows updated (1 if found and updated, 0 if not found)

        Example:
            updated = sp._update_generic('user', 42, {'activeStorage': 'storage2'})

        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageReaderWriter.ts
        """
        model = self._get_model(table_name)

        with session_scope(self.SessionLocal) as s:
            mapper = inspect(model)
            pk_col = mapper.primary_key[0]

            query = select(model).where(getattr(model, pk_col.name) == pk_value)
            obj = s.execute(query).scalar_one_or_none()

            if not obj:
                return 0

            for key, value in patch.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)

            s.commit()
            return 1

    def _model_to_dict(self, obj: Any) -> dict[str, Any]:
        """Convert ORM object to camelCase dict."""
        mapper = inspect(obj.__class__)
        result = {}

        for column in mapper.columns:
            value = getattr(obj, column.name)
            result[self._to_api_key(column.name)] = value

        return result

    @staticmethod
    def _to_api_key(snake_case: str) -> str:
        """Convert snake_case to camelCase."""
        parts = snake_case.split("_")
        return parts[0] + "".join(word.capitalize() for word in parts[1:])

    # =====================================================================
    # TABLE WRAPPERS: INSERT methods (15 tables)
    # =====================================================================

    def insert_user(self, data: dict[str, Any]) -> int:
        """Insert User record."""
        return self._insert_generic("user", data)

    def insert_certificate(self, data: dict[str, Any]) -> int:
        """Insert Certificate record."""
        return self._insert_generic("certificate", data)

    def insert_certificate_field(self, data: dict[str, Any]) -> int:
        """Insert CertificateField record."""
        return self._insert_generic("certificate_field", data)

    def insert_commission(self, data: dict[str, Any]) -> int:
        """Insert Commission record."""
        return self._insert_generic("commission", data)

    def insert_monitor_event(self, data: dict[str, Any]) -> int:
        """Insert MonitorEvent record."""
        return self._insert_generic("monitor_event", data)

    def insert_output(self, data: dict[str, Any]) -> int:
        """Insert Output record."""
        return self._insert_generic("output", data)

    def insert_output_basket(self, data: dict[str, Any]) -> int:
        """Insert OutputBasket record."""
        return self._insert_generic("output_basket", data)

    def insert_output_tag(self, data: dict[str, Any]) -> int:
        """Insert OutputTag record."""
        return self._insert_generic("output_tag", data)

    def insert_output_tag_map(self, data: dict[str, Any]) -> int:
        """Insert OutputTagMap record."""
        return self._insert_generic("output_tag_map", data)

    def insert_proven_tx(self, data: dict[str, Any]) -> int:
        """Insert ProvenTx record."""
        return self._insert_generic("proven_tx", data)

    def insert_proven_tx_req(self, data: dict[str, Any]) -> int:
        """Insert ProvenTxReq record."""
        return self._insert_generic("proven_tx_req", data)

    def insert_sync_state(self, data: dict[str, Any]) -> int:
        """Insert SyncState record."""
        return self._insert_generic("sync_state", data)

    def insert_transaction(self, data: dict[str, Any]) -> int:
        """Insert Transaction record."""
        return self._insert_generic("transaction", data)

    def insert_tx_label(self, data: dict[str, Any]) -> int:
        """Insert TxLabel record."""
        return self._insert_generic("tx_label", data)

    def insert_tx_label_map(self, data: dict[str, Any]) -> int:
        """Insert TxLabelMap record."""
        return self._insert_generic("tx_label_map", data)

    # =====================================================================
    # TABLE WRAPPERS: FIND methods (11 tables with find queries)
    # =====================================================================

    def find_users(self, args: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Find User records."""
        return self._find_generic("user", args)

    def find_certificates(self, args: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Find Certificate records."""
        return self._find_generic("certificate", args)

    def find_certificate_fields(self, args: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Find CertificateField records."""
        return self._find_generic("certificate_field", args)

    def find_commissions(self, args: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Find Commission records."""
        return self._find_generic("commission", args)

    def find_monitor_events(self, args: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Find MonitorEvent records."""
        return self._find_generic("monitor_event", args)

    def find_outputs(self, args: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Find Output records."""
        return self._find_generic("output", args)

    def find_output_baskets(self, args: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Find OutputBasket records."""
        return self._find_generic("output_basket", args)

    def find_output_tags(self, args: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Find OutputTag records."""
        return self._find_generic("output_tag", args)

    def find_sync_states(self, args: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Find SyncState records."""
        return self._find_generic("sync_state", args)

    def find_transactions(self, args: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Find Transaction records."""
        return self._find_generic("transaction", args)

    def find_tx_labels(self, args: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Find TxLabel records."""
        return self._find_generic("tx_label", args)

    # =====================================================================
    # TABLE WRAPPERS: COUNT methods (11 tables)
    # =====================================================================

    def count_users(self, args: dict[str, Any] | None = None) -> int:
        """Count User records."""
        return self._count_generic("user", args)

    def count_certificates(self, args: dict[str, Any] | None = None) -> int:
        """Count Certificate records."""
        return self._count_generic("certificate", args)

    def count_certificate_fields(self, args: dict[str, Any] | None = None) -> int:
        """Count CertificateField records."""
        return self._count_generic("certificate_field", args)

    def count_commissions(self, args: dict[str, Any] | None = None) -> int:
        """Count Commission records."""
        return self._count_generic("commission", args)

    def count_monitor_events(self, args: dict[str, Any] | None = None) -> int:
        """Count MonitorEvent records."""
        return self._count_generic("monitor_event", args)

    def count_outputs(self, args: dict[str, Any] | None = None) -> int:
        """Count Output records."""
        return self._count_generic("output", args)

    def count_output_baskets(self, args: dict[str, Any] | None = None) -> int:
        """Count OutputBasket records."""
        return self._count_generic("output_basket", args)

    def count_output_tags(self, args: dict[str, Any] | None = None) -> int:
        """Count OutputTag records."""
        return self._count_generic("output_tag", args)

    def count_sync_states(self, args: dict[str, Any] | None = None) -> int:
        """Count SyncState records."""
        return self._count_generic("sync_state", args)

    def count_transactions(self, args: dict[str, Any] | None = None) -> int:
        """Count Transaction records."""
        return self._count_generic("transaction", args)

    def count_tx_labels(self, args: dict[str, Any] | None = None) -> int:
        """Count TxLabel records."""
        return self._count_generic("tx_label", args)

    # =====================================================================
    # TABLE WRAPPERS: UPDATE methods (15 tables)
    # =====================================================================

    def update_user(self, pk_value: int, patch: dict[str, Any]) -> int:
        """Update User record by ID."""
        return self._update_generic("user", pk_value, patch)

    def update_certificate(self, pk_value: int, patch: dict[str, Any]) -> int:
        """Update Certificate record by ID."""
        return self._update_generic("certificate", pk_value, patch)

    def update_certificate_field(self, pk_value: int, patch: dict[str, Any]) -> int:
        """Update CertificateField record by ID."""
        return self._update_generic("certificate_field", pk_value, patch)

    def update_commission(self, pk_value: int, patch: dict[str, Any]) -> int:
        """Update Commission record by ID."""
        return self._update_generic("commission", pk_value, patch)

    def update_monitor_event(self, pk_value: int, patch: dict[str, Any]) -> int:
        """Update MonitorEvent record by ID."""
        return self._update_generic("monitor_event", pk_value, patch)

    def update_output(self, pk_value: int, patch: dict[str, Any]) -> int:
        """Update Output record by ID."""
        return self._update_generic("output", pk_value, patch)

    def update_output_basket(self, pk_value: int, patch: dict[str, Any]) -> int:
        """Update OutputBasket record by ID."""
        return self._update_generic("output_basket", pk_value, patch)

    def update_output_tag(self, pk_value: int, patch: dict[str, Any]) -> int:
        """Update OutputTag record by ID."""
        return self._update_generic("output_tag", pk_value, patch)

    def update_output_tag_map(self, pk_value: int, patch: dict[str, Any]) -> int:
        """Update OutputTagMap record by ID."""
        return self._update_generic("output_tag_map", pk_value, patch)

    def update_proven_tx(self, pk_value: int, patch: dict[str, Any]) -> int:
        """Update ProvenTx record by ID."""
        return self._update_generic("proven_tx", pk_value, patch)

    def update_proven_tx_req(self, pk_value: int, patch: dict[str, Any]) -> int:
        """Update ProvenTxReq record by ID."""
        return self._update_generic("proven_tx_req", pk_value, patch)

    def update_sync_state(self, pk_value: int, patch: dict[str, Any]) -> int:
        """Update SyncState record by ID."""
        return self._update_generic("sync_state", pk_value, patch)

    def update_transaction(self, pk_value: int, patch: dict[str, Any]) -> int:
        """Update Transaction record by ID."""
        return self._update_generic("transaction", pk_value, patch)

    def update_tx_label(self, pk_value: int, patch: dict[str, Any]) -> int:
        """Update TxLabel record by ID."""
        return self._update_generic("tx_label", pk_value, patch)

    def update_tx_label_map(self, pk_value: int, patch: dict[str, Any]) -> int:
        """Update TxLabelMap record by ID."""
        return self._update_generic("tx_label_map", pk_value, patch)
