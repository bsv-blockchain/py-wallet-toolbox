from __future__ import annotations

from typing import Optional
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    DateTime,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import BigInteger
from sqlalchemy.orm import declarative_base, mapped_column, Mapped, relationship
from sqlalchemy import LargeBinary, text
from sqlalchemy.dialects import mysql, postgresql


Base = declarative_base()


class TimestampMixin:
    """Common created_at/updated_at columns (TS addTimeStamps parity).

    - created_at: server default CURRENT_TIMESTAMP
    - updated_at: server default CURRENT_TIMESTAMP, on update set to CURRENT_TIMESTAMP
    """

    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        DateTime(timezone=False)
        .with_variant(mysql.DATETIME(fsp=3), "mysql")
        .with_variant(postgresql.TIMESTAMP(precision=3), "postgresql"),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at",
        DateTime(timezone=False)
        .with_variant(mysql.DATETIME(fsp=3), "mysql")
        .with_variant(postgresql.TIMESTAMP(precision=3), "postgresql"),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )


# 01 Settings
class Settings(TimestampMixin, Base):
    __tablename__ = "settings"

    """Settings table mapping.

    Summary:
        Stores per-storage configuration such as active chain and identity key.
    TS parity:
        Mirrors Knex schema `settings` (subset); field names are snake_case.
    Args:
        N/A (SQLAlchemy declarative model).
    Returns:
        N/A
    Raises:
        N/A
    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/KnexMigrations.ts
    """

    storage_identity_key: Mapped[str] = mapped_column("storageIdentityKey", String(130), primary_key=True)
    storage_name: Mapped[str] = mapped_column("storageName", String(128), nullable=False)
    chain: Mapped[str] = mapped_column(String(10), nullable=False)
    dbtype: Mapped[str] = mapped_column(String(10), nullable=False)
    max_output_script: Mapped[int] = mapped_column("maxOutputScript", Integer, nullable=False)


# 02 User
class User(TimestampMixin, Base):
    __tablename__ = "users"

    """User table mapping.

    Summary:
        Stores user identity key records.
    TS parity:
        Mirrors `users` table in Knex schema (subset).
    Args:
        N/A
    Returns:
        N/A
    Raises:
        N/A
    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/KnexMigrations.ts
    """

    user_id: Mapped[int] = mapped_column("userId", Integer, primary_key=True)
    identity_key: Mapped[str] = mapped_column("identityKey", String(130), nullable=False)
    active_storage: Mapped[str] = mapped_column("activeStorage", String(130), nullable=False, default="")

    __table_args__ = (
        UniqueConstraint("identityKey", name="ux_users_identity"),
    )


# 03 SyncState
class SyncState(TimestampMixin, Base):
    __tablename__ = "sync_states"

    """Sync state table mapping.

    Summary:
        Tracks per-user synchronization and last synced height for a storage identity.
    TS parity:
        Mirrors `sync_states` (subset) with consolidated fields.
    Args:
        N/A
    Returns:
        N/A
    Raises:
        N/A
    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/KnexMigrations.ts
    """

    sync_state_id: Mapped[int] = mapped_column("syncStateId", Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column("userId", ForeignKey("users.userId", ondelete="CASCADE"), nullable=False)
    storage_identity_key: Mapped[str] = mapped_column("storageIdentityKey", String(130), nullable=False, default="")
    storage_name: Mapped[str] = mapped_column("storageName", String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="unknown")
    init: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ref_num: Mapped[str] = mapped_column("refNum", String(100), nullable=False)
    sync_map: Mapped[str] = mapped_column("syncMap", Text, nullable=False)
    when: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    satoshis: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    error_local: Mapped[Optional[str]] = mapped_column("errorLocal", Text, nullable=True)
    error_other: Mapped[Optional[str]] = mapped_column("errorOther", Text, nullable=True)

    user: Mapped[User] = relationship("User")

    __table_args__ = (
        UniqueConstraint("refNum", name="ux_sync_states_refnum"),
        Index("ix_sync_states_status", "status"),
    )


# 04 Transaction
class Transaction(TimestampMixin, Base):
    __tablename__ = "transactions"

    """Transaction table mapping.

    Summary:
        Stores wallet transactions, raw payloads and minimal metadata.
    TS parity:
        Mirrors `transactions` with Pythonic snake_case fields.
    Args:
        N/A
    Returns:
        N/A
    Raises:
        N/A
    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/KnexMigrations.ts
    """

    transaction_id: Mapped[int] = mapped_column("transactionId", Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column("userId", ForeignKey("users.userId", ondelete="CASCADE"), nullable=False)
    proven_tx_id: Mapped[Optional[int]] = mapped_column("provenTxId", ForeignKey("proven_txs.provenTxId"), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    reference: Mapped[str] = mapped_column(String(64), nullable=False)
    is_outgoing: Mapped[bool] = mapped_column("isOutgoing", Boolean, nullable=False, default=False)
    satoshis: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    version: Mapped[Optional[int]] = mapped_column(
        Integer().with_variant(mysql.INTEGER(unsigned=True), "mysql"), nullable=True
    )
    lock_time: Mapped[Optional[int]] = mapped_column(
        "lockTime", Integer().with_variant(mysql.INTEGER(unsigned=True), "mysql"), nullable=True
    )
    description: Mapped[str] = mapped_column(String(2048), nullable=False, default="")
    txid: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    input_beef: Mapped[Optional[bytes]] = mapped_column(
        "inputBEEF", LargeBinary().with_variant(mysql.LONGBLOB, "mysql"), nullable=True
    )
    raw_tx: Mapped[Optional[bytes]] = mapped_column(
        "rawTx", LargeBinary().with_variant(mysql.LONGBLOB, "mysql"), nullable=True
    )

    user: Mapped[User] = relationship("User")

    __table_args__ = (
        UniqueConstraint("reference", name="ux_transactions_reference"),
        Index("ix_transactions_status", "status"),
        CheckConstraint("version >= 0", name="ck_transactions_version_unsigned"),
        CheckConstraint("lockTime >= 0", name="ck_transactions_locktime_unsigned"),
    )


# 05 Output
class Output(TimestampMixin, Base):
    __tablename__ = "outputs"

    """Output table mapping.

    Summary:
        Stores outputs (UTXOs and change), spendability and script metadata.
    TS parity:
        Mirrors `outputs` with minor naming differences (snake_case).
    Args:
        N/A
    Returns:
        N/A
    Raises:
        N/A
    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/KnexMigrations.ts
    """

    output_id: Mapped[int] = mapped_column("outputId", Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column("userId", ForeignKey("users.userId", ondelete="CASCADE"), nullable=False)
    transaction_id: Mapped[int] = mapped_column("transactionId", ForeignKey("transactions.transactionId"), nullable=False)
    basket_id: Mapped[Optional[int]] = mapped_column("basketId", ForeignKey("output_baskets.basketId", ondelete="SET NULL"))
    spendable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    change: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    vout: Mapped[int] = mapped_column(Integer, nullable=False)
    satoshis: Mapped[int] = mapped_column(BigInteger, nullable=False)
    provided_by: Mapped[str] = mapped_column("providedBy", String(130), nullable=False, default="")
    purpose: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    output_description: Mapped[Optional[str]] = mapped_column("outputDescription", String(2048), nullable=True)
    txid: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    sender_identity_key: Mapped[Optional[str]] = mapped_column("senderIdentityKey", String(130), nullable=True)
    derivation_prefix: Mapped[Optional[str]] = mapped_column("derivationPrefix", String(200), nullable=True)
    derivation_suffix: Mapped[Optional[str]] = mapped_column("derivationSuffix", String(200), nullable=True)
    custom_instructions: Mapped[Optional[str]] = mapped_column("customInstructions", String(2500), nullable=True)
    spent_by: Mapped[Optional[int]] = mapped_column("spentBy", ForeignKey("transactions.transactionId", ondelete="SET NULL"))
    sequence_number: Mapped[Optional[int]] = mapped_column("sequenceNumber", Integer, nullable=True)
    spending_description: Mapped[Optional[str]] = mapped_column("spendingDescription", String(2048), nullable=True)
    script_length: Mapped[Optional[int]] = mapped_column(
        "scriptLength", BigInteger().with_variant(mysql.BIGINT(unsigned=True), "mysql"), nullable=True
    )
    script_offset: Mapped[Optional[int]] = mapped_column(
        "scriptOffset", BigInteger().with_variant(mysql.BIGINT(unsigned=True), "mysql"), nullable=True
    )
    locking_script: Mapped[Optional[bytes]] = mapped_column(
        "lockingScript", LargeBinary().with_variant(mysql.LONGBLOB, "mysql"), nullable=True
    )
    spent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    

    user: Mapped[User] = relationship("User")

    __table_args__ = (
        UniqueConstraint("transactionId", "vout", "userId", name="ux_outputs_txid_vout_user"),
        CheckConstraint("scriptLength >= 0", name="ck_outputs_scriptlength_unsigned"),
        CheckConstraint("scriptOffset >= 0", name="ck_outputs_scriptoffset_unsigned"),
    )


# 06 ProvenTx
class ProvenTx(TimestampMixin, Base):
    __tablename__ = "proven_txs"

    """Proven transaction table mapping.

    Summary:
        Stores transactions proven by a Merkle path and block header linkage.
    TS parity:
        Mirrors `proven_txs` core fields.
    Args:
        N/A
    Returns:
        N/A
    Raises:
        N/A
    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/KnexMigrations.ts
    """

    proven_tx_id: Mapped[int] = mapped_column("provenTxId", Integer, primary_key=True)
    txid: Mapped[str] = mapped_column(String(64), nullable=False)
    height: Mapped[int] = mapped_column(
        Integer().with_variant(mysql.INTEGER(unsigned=True), "mysql"), nullable=False
    )

    index: Mapped[int] = mapped_column(Integer, nullable=False)
    merkle_path: Mapped[bytes] = mapped_column(
        "merklePath", LargeBinary().with_variant(mysql.LONGBLOB, "mysql"), nullable=False
    )
    raw_tx: Mapped[bytes] = mapped_column(
        "rawTx", LargeBinary().with_variant(mysql.LONGBLOB, "mysql"), nullable=False
    )
    block_hash: Mapped[str] = mapped_column("blockHash", String(64), nullable=False)
    merkle_root: Mapped[str] = mapped_column("merkleRoot", String(64), nullable=False)

    __table_args__ = (
        UniqueConstraint("txid", name="ux_proven_txs_txid"),
        Index("ix_proven_txs_blockhash", "blockHash"),
        CheckConstraint("height >= 0", name="ck_proven_txs_height_unsigned"),
    )


# 07 ProvenTxReq
class ProvenTxReq(TimestampMixin, Base):
    __tablename__ = "proven_tx_reqs"

    """Proven transaction request table mapping.

    Summary:
        Tracks proof requests and their lifecycle status.
    TS parity:
        Mirrors `proven_tx_reqs` core fields.
    Args:
        N/A
    Returns:
        N/A
    Raises:
        N/A
    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/KnexMigrations.ts
    """

    proven_tx_req_id: Mapped[int] = mapped_column("provenTxReqId", Integer, primary_key=True)
    proven_tx_id: Mapped[Optional[int]] = mapped_column("provenTxId", ForeignKey("proven_txs.provenTxId"))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="unknown")
    attempts: Mapped[int] = mapped_column(
        Integer().with_variant(mysql.INTEGER(unsigned=True), "mysql"), nullable=False, default=0
    )
    notified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    txid: Mapped[str] = mapped_column(String(64), nullable=False)
    batch: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    history: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    notify: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    raw_tx: Mapped[bytes] = mapped_column(
        "rawTx", LargeBinary().with_variant(mysql.LONGBLOB, "mysql"), nullable=False
    )
    input_beef: Mapped[Optional[bytes]] = mapped_column(
        "inputBEEF", LargeBinary().with_variant(mysql.LONGBLOB, "mysql"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("txid", name="ux_proven_tx_reqs_txid"),
        Index("ix_proven_tx_reqs_status", "status"),
        Index("ix_proven_tx_reqs_batch", "batch"),
        CheckConstraint("attempts >= 0", name="ck_proven_tx_reqs_attempts_unsigned"),
    )


# 08 Certificate
class Certificate(TimestampMixin, Base):
    __tablename__ = "certificates"

    """Certificate table mapping.

    Summary:
        Stores user-bound certificates and their issuance metadata.
    TS parity:
        Mirrors `certificates` fields including composite uniqueness.
    Args:
        N/A
    Returns:
        N/A
    Raises:
        N/A
    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/KnexMigrations.ts
    """

    certificate_id: Mapped[int] = mapped_column("certificateId", Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column("userId", ForeignKey("users.userId", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    serial_number: Mapped[str] = mapped_column("serialNumber", String(100), nullable=False)
    certifier: Mapped[str] = mapped_column(String(100), nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    verifier: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    revocation_outpoint: Mapped[str] = mapped_column("revocationOutpoint", String(100), nullable=False)
    signature: Mapped[str] = mapped_column(String(255), nullable=False)
    is_deleted: Mapped[bool] = mapped_column("isDeleted", Boolean, nullable=False, default=False)

    user: Mapped[User] = relationship("User")

    __table_args__ = (
        UniqueConstraint("userId", "type", "certifier", "serialNumber", name="ux_certificates_unique"),
    )


# 09 CertificateField
class CertificateField(TimestampMixin, Base):
    __tablename__ = "certificate_fields"

    """Certificate field table mapping.

    Summary:
        Stores extended certificate fields per certificate.
    TS parity:
        Mirrors `certificate_fields` with name+certificate uniqueness.
    Args:
        N/A
    Returns:
        N/A
    Raises:
        N/A
    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/KnexMigrations.ts
    """

    certificate_field_id: Mapped[int] = mapped_column("certificateFieldId", Integer, primary_key=True)
    certificate_id: Mapped[int] = mapped_column("certificateId", ForeignKey("certificates.certificateId", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column("userId", ForeignKey("users.userId", ondelete="CASCADE"), nullable=False)
    field_name: Mapped[str] = mapped_column("fieldName", String(100), nullable=False)
    field_value: Mapped[str] = mapped_column("fieldValue", String, nullable=False)
    master_key: Mapped[str] = mapped_column("masterKey", String(255), nullable=False, default="")

    certificate: Mapped[Certificate] = relationship("Certificate")

    __table_args__ = (
        Index("ix_certificate_fields_cert", "certificateId"),
        UniqueConstraint("fieldName", "certificateId", name="ux_certificate_fields_name_cert"),
    )


# 10 OutputBasket
class OutputBasket(TimestampMixin, Base):
    __tablename__ = "output_baskets"

    """Output basket table mapping.

    Summary:
        Groups outputs into named baskets per user.
    TS parity:
        Mirrors `output_baskets` and default flags.
    Args:
        N/A
    Returns:
        N/A
    Raises:
        N/A
    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/KnexMigrations.ts
    """

    basket_id: Mapped[int] = mapped_column("basketId", Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    user_id: Mapped[int] = mapped_column("userId", ForeignKey("users.userId", ondelete="CASCADE"), nullable=False)
    number_of_desired_utxos: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    minimum_desired_utxo_value: Mapped[int] = mapped_column(Integer, nullable=False, default=10000)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped[User] = relationship("User")

    __table_args__ = (
        UniqueConstraint("userId", "name", name="ux_output_baskets_user_name"),
    )


# 11 OutputTag
class OutputTag(TimestampMixin, Base):
    __tablename__ = "output_tags"

    """Output tag table mapping.

    Summary:
        Tag strings that can be attached to outputs.
    TS parity:
        Mirrors `output_tags` including soft-delete flag.
    Args:
        N/A
    Returns:
        N/A
    Raises:
        N/A
    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/KnexMigrations.ts
    """

    output_tag_id: Mapped[int] = mapped_column("outputTagId", Integer, primary_key=True)
    tag: Mapped[str] = mapped_column(String(150), nullable=False)
    user_id: Mapped[int] = mapped_column("userId", ForeignKey("users.userId", ondelete="CASCADE"), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped[User] = relationship("User")

    __table_args__ = (
        UniqueConstraint("userId", "tag", name="ux_output_tags_user_tag"),
    )


# 12 OutputTagMap
class OutputTagMap(TimestampMixin, Base):
    __tablename__ = "output_tags_map"

    """Output tag mapping table.

    Summary:
        Associates outputs with tags.
    TS parity:
        Mirrors `output_tags_map` including composite uniqueness.
    Args:
        N/A
    Returns:
        N/A
    Raises:
        N/A
    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/KnexMigrations.ts
    """

    output_id: Mapped[int] = mapped_column("outputId", ForeignKey("outputs.outputId", ondelete="CASCADE"), primary_key=True)
    output_tag_id: Mapped[int] = mapped_column("outputTagId", ForeignKey("output_tags.outputTagId", ondelete="CASCADE"), primary_key=True)
    is_deleted: Mapped[bool] = mapped_column("isDeleted", Boolean, nullable=False, default=False)

    output: Mapped[Output] = relationship("Output")
    output_tag: Mapped[OutputTag] = relationship("OutputTag")

    __table_args__ = (
        UniqueConstraint("outputTagId", "outputId", name="ux_output_tags_map_pair"),
        Index("ix_output_tags_map_output", "outputId"),
    )


# 13 TxLabel
class TxLabel(TimestampMixin, Base):
    __tablename__ = "tx_labels"

    """Transaction label table mapping.

    Summary:
        Label strings that can be attached per user and transaction.
    TS parity:
        Mirrors `tx_labels` including soft-delete flag.
    Args:
        N/A
    Returns:
        N/A
    Raises:
        N/A
    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/KnexMigrations.ts
    """

    tx_label_id: Mapped[int] = mapped_column("txLabelId", Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    user_id: Mapped[int] = mapped_column("userId", ForeignKey("users.userId", ondelete="CASCADE"), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped[User] = relationship("User")

    __table_args__ = (
        UniqueConstraint("userId", "label", name="ux_tx_labels_user_label"),
    )


# 14 TxLabelMap
class TxLabelMap(TimestampMixin, Base):
    __tablename__ = "tx_labels_map"

    """Transaction label mapping table.

    Summary:
        Associates transactions with labels.
    TS parity:
        Mirrors `tx_labels_map` including composite uniqueness.
    Args:
        N/A
    Returns:
        N/A
    Raises:
        N/A
    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/KnexMigrations.ts
    """

    transaction_id: Mapped[int] = mapped_column("transactionId", ForeignKey("transactions.transactionId", ondelete="CASCADE"), primary_key=True)
    tx_label_id: Mapped[int] = mapped_column("txLabelId", ForeignKey("tx_labels.txLabelId", ondelete="CASCADE"), primary_key=True)
    is_deleted: Mapped[bool] = mapped_column("isDeleted", Boolean, nullable=False, default=False)

    transaction: Mapped[Transaction] = relationship("Transaction")
    tx_label: Mapped[TxLabel] = relationship("TxLabel")

    __table_args__ = (
        UniqueConstraint("txLabelId", "transactionId", name="ux_tx_labels_map_pair"),
        Index("ix_tx_labels_map_tx", "transactionId"),
    )


# 15 Commission
class Commission(TimestampMixin, Base):
    __tablename__ = "commissions"

    """Commission table mapping.

    Summary:
        Stores commission outputs and redemption status.
    TS parity:
        Mirrors `commissions` core fields.
    Args:
        N/A
    Returns:
        N/A
    Raises:
        N/A
    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/KnexMigrations.ts
    """

    commission_id: Mapped[int] = mapped_column("commissionId", Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column("userId", ForeignKey("users.userId", ondelete="CASCADE"), nullable=False)
    transaction_id: Mapped[int] = mapped_column("transactionId", ForeignKey("transactions.transactionId", ondelete="CASCADE"), nullable=False, unique=True)
    satoshis: Mapped[int] = mapped_column(Integer, nullable=False)
    key_offset: Mapped[str] = mapped_column("keyOffset", String(130), nullable=False)
    is_redeemed: Mapped[bool] = mapped_column("isRedeemed", Boolean, nullable=False, default=False)
    locking_script: Mapped[bytes] = mapped_column(
        "lockingScript", LargeBinary().with_variant(mysql.LONGBLOB, "mysql"), nullable=False
    )

    user: Mapped[User] = relationship("User")

    __table_args__ = (
        Index("ix_commissions_tx", "transactionId"),
    )


# 16 MonitorEvent
class MonitorEvent(TimestampMixin, Base):
    __tablename__ = "monitor_events"

    """Monitor event table mapping.

    Summary:
        Stores operational monitor events and statuses.
    TS parity:
        Mirrors `monitor_events` with simplified fields.
    Args:
        N/A
    Returns:
        N/A
    Raises:
        N/A
    Reference:
        toolbox/ts-wallet-toolbox/src/storage/schema/KnexMigrations.ts
    """

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_monitor_events_event", "event"),
    )


