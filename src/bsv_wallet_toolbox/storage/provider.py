from __future__ import annotations

from typing import Any, Iterable
from bsv.transaction import Transaction
from bsv.merkle_path import MerklePath

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
              - specOpWalletBalance (or its id): use basket 'default', ignore limit; result has totalOutputs=sum(satoshis) and outputs=[].
              - specOpInvalidChange (or its id): use basket 'default', includeOutputScripts=true, includeSpent=false; filters to invalid change via network checks (placeholder here).
              - specOpSetWalletChangeParams (or its id): tags [numberOfDesiredUTXOs, minimumDesiredUTXOValue] update default basket params; returns empty result.
            - Tag SpecOps: 'all' (ignore basket, include spent), 'change' (change only), 'spent'/'unspent'.
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
        SPECOP_INVALID_CHANGE = "5a76fd430a311f8bc0553859061710a4475c19fed46e2ff95969aa918e612e57"
        SPECOP_SET_CHANGE = "a4979d28ced8581e9c1c92f1001cc7cb3aabf8ea32e10888ad898f0a509a3929"
        SPECOP_WALLET_BAL = "893b7646de0e1c9f741bd6e9169b76a8847ae34adef7bef1e6a285371206d2e8"

        basket_name = args.get("basket")

        def resolve_specop(name: str | None) -> str | None:
            if not name:
                return None
            mapping: dict[str, str] = {
                SPECOP_WALLET_BAL: "wallet_balance",
                SPECOP_INVALID_CHANGE: "invalid_change",
                SPECOP_SET_CHANGE: "set_change",
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
            basket_name = "default" if basket_name else "default"
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
            # - 'unspent': exclude spent outputs（default）
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
            base = (Output.user_id == user_id)
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
                    (OutputBasket.user_id == user_id) & (OutputBasket.name == basket_name) & (OutputBasket.is_deleted.is_(False))
                )
                _exec_result = s.execute(bq)
                bid = _exec_result.scalar_one_or_none()
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
                            # Run only when no running loop is present
                            asyncio.get_running_loop()
                            ok = None  # cannot await here; skip network check
                        except RuntimeError:
                            try:
                                ok = bool(asyncio.run(services.is_utxo(out)))
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

    def _build_recursive_beef_for_txids(self, txids: list[str], max_depth: int = 4, known_txids: list[str] | None = None) -> bytes:
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
                            if first_beef is None:
                                first_beef = beef_bytes
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
            tag_ids = [i for i in s.execute(mq).scalars().all()]
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
            label_ids = [i for i in s.execute(mq).scalars().all()]
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
        spendable = args.get("spendable", None)
        with session_scope(self.SessionLocal) as s:
            q = select(Output).where(Output.user_id == user_id)
            if spendable is not None:
                q = q.where(Output.spendable.is_(bool(spendable)))
            if basket_name:
                bq = select(OutputBasket.basket_id).where(
                    (OutputBasket.user_id == user_id) & (OutputBasket.name == basket_name) & (OutputBasket.is_deleted.is_(False))
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

    def update_output(self, output_id: int, patch: dict[str, Any]) -> int:
        """Update fields on an `Output` row by id (minimal keys).

        Summary:
            Minimal updater to support SpecOps like 'release' (set spendable=false)
            and basket reassignment. Only a safe subset of fields is supported.
        TS parity:
            Mirrors intent of TS `updateOutput` used by SpecOps and workflows.
        Args:
            output_id: Primary key of output to update.
            patch: Dict of fields to update. Supported keys:
                - 'spendable': bool
                - 'basketId': int | None
        Returns:
            int: Number of rows affected (0 or 1).
        Raises:
            N/A
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        allowed = {"spendable", "basketId"}
        to_apply = {k: v for k, v in patch.items() if k in allowed}
        if not to_apply:
            return 0
        with session_scope(self.SessionLocal) as s:
            _result = s.execute(select(Output).where(Output.output_id == output_id))
            o = _result.scalar_one_or_none()
            if not o:
                return 0
            if "spendable" in to_apply:
                o.spendable = bool(to_apply["spendable"])
            if "basketId" in to_apply:
                o.basket_id = to_apply["basketId"]
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
            _result = s.execute(q)

            rows: Iterable[Output] = _result.scalars().all()
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
            _exec_result = s.execute(q)
            rows: list[Output] = _exec_result.scalars().all()
            # Apply exclude_sending filter (approximate)
            def ok(output_row: Output) -> bool:
                if exclude_sending and output_row.spent_by is not None:
                    _exec_result_inner = s.execute(
                        select(ProvenTxReq).where(ProvenTxReq.proven_tx_id == output_row.spent_by)
                    )
                    req = _exec_result_inner.scalar_one_or_none()
                    if req and req.status == "sending":
                        return False
                if exact_satoshis is not None:
                    return int(output_row.satoshis) == int(exact_satoshis)
                return int(output_row.satoshis) >= int(target_satoshis)

            candidates = []
            for output_row in rows:
                if ok(output_row):
                    candidates.append(output_row)
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


