from __future__ import annotations

from typing import Optional

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, mapped_column, Mapped, relationship


Base = declarative_base()


# 01 Settings
class Settings(Base):
    __tablename__ = "settings"

    settings_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain: Mapped[str] = mapped_column(String(8), nullable=False)  # 'main' | 'test'
    storage_identity_key: Mapped[str] = mapped_column(String(130), nullable=False)

    __table_args__ = (
        UniqueConstraint("storage_identity_key", name="ux_settings_identity"),
    )


# 02 User
class User(Base):
    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identity_key: Mapped[str] = mapped_column(String(130), nullable=False)  # pubkey hex

    __table_args__ = (
        UniqueConstraint("identity_key", name="ux_user_identity"),
    )


# 03 SyncState
class SyncState(Base):
    __tablename__ = "sync_state"

    sync_state_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    storage_identity_key: Mapped[str] = mapped_column(String(130), nullable=False)
    last_synced_height: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped[User] = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "storage_identity_key", name="ux_sync_state_user_store"),
        Index("ix_sync_state_user", "user_id"),
    )


# 04 Transaction
class Transaction(Base):
    __tablename__ = "transaction"

    transaction_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    txid: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_tx: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)

    user: Mapped[User] = relationship("User")

    __table_args__ = (
        UniqueConstraint("txid", "user_id", name="ux_tx_txid_user"),
        Index("ix_tx_user", "user_id"),
    )


# 05 Output
class Output(Base):
    __tablename__ = "output"

    output_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    txid: Mapped[str] = mapped_column(String(64), nullable=False)
    vout: Mapped[int] = mapped_column(Integer, nullable=False)
    satoshis: Mapped[int] = mapped_column(Integer, nullable=False)
    script: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    spent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    spent_txid: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    spent_height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    user: Mapped[User] = relationship("User")

    __table_args__ = (
        UniqueConstraint("txid", "vout", "user_id", name="ux_output_outpoint_user"),
        Index("ix_output_user", "user_id"),
    )


# 06 ProvenTx
class ProvenTx(Base):
    __tablename__ = "proven_tx"

    proven_tx_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    txid: Mapped[str] = mapped_column(String(64), nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("txid", name="ux_proven_tx_txid"),
    )


# 07 ProvenTxReq
class ProvenTxReq(Base):
    __tablename__ = "proven_tx_req"

    proven_tx_req_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    txid: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)

    __table_args__ = (
        Index("ix_proven_tx_req_txid", "txid"),
    )


# 08 Certificate
class Certificate(Base):
    __tablename__ = "certificate"

    certificate_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(128), nullable=False)

    user: Mapped[User] = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "serial_number", name="ux_certificate_serial"),
    )


# 09 CertificateField
class CertificateField(Base):
    __tablename__ = "certificate_field"

    certificate_field_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    certificate_id: Mapped[int] = mapped_column(ForeignKey("certificate.certificate_id", ondelete="CASCADE"), nullable=False)
    field_name: Mapped[str] = mapped_column(String(128), nullable=False)
    field_value: Mapped[str] = mapped_column(Text, nullable=False)

    certificate: Mapped[Certificate] = relationship("Certificate")

    __table_args__ = (
        Index("ix_certificate_field_cert", "certificate_id"),
    )


# 10 OutputBasket
class OutputBasket(Base):
    __tablename__ = "output_basket"

    basket_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)

    user: Mapped[User] = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="ux_output_basket_user_name"),
    )


# 11 OutputTag
class OutputTag(Base):
    __tablename__ = "output_tag"

    output_tag_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tag: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)

    user: Mapped[User] = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "tag", name="ux_output_tag_user_tag"),
    )


# 12 OutputTagMap
class OutputTagMap(Base):
    __tablename__ = "output_tag_map"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    output_id: Mapped[int] = mapped_column(ForeignKey("output.output_id", ondelete="CASCADE"), nullable=False)
    output_tag_id: Mapped[int] = mapped_column(ForeignKey("output_tag.output_tag_id", ondelete="CASCADE"), nullable=False)

    output: Mapped[Output] = relationship("Output")
    output_tag: Mapped[OutputTag] = relationship("OutputTag")

    __table_args__ = (
        UniqueConstraint("output_id", "output_tag_id", name="ux_output_tag_map_pair"),
        Index("ix_output_tag_map_output", "output_id"),
    )


# 13 TxLabel
class TxLabel(Base):
    __tablename__ = "tx_label"

    tx_label_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)

    user: Mapped[User] = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "label", name="ux_tx_label_user_label"),
    )


# 14 TxLabelMap
class TxLabelMap(Base):
    __tablename__ = "tx_label_map"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transaction.transaction_id", ondelete="CASCADE"), nullable=False)
    tx_label_id: Mapped[int] = mapped_column(ForeignKey("tx_label.tx_label_id", ondelete="CASCADE"), nullable=False)

    transaction: Mapped[Transaction] = relationship("Transaction")
    tx_label: Mapped[TxLabel] = relationship("TxLabel")

    __table_args__ = (
        UniqueConstraint("transaction_id", "tx_label_id", name="ux_tx_label_map_pair"),
        Index("ix_tx_label_map_tx", "transaction_id"),
    )


# 15 Commission
class Commission(Base):
    __tablename__ = "commission"

    commission_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    satoshis: Mapped[int] = mapped_column(Integer, nullable=False)

    user: Mapped[User] = relationship("User")

    __table_args__ = (
        Index("ix_commission_user", "user_id"),
    )


# 16 MonitorEvent
class MonitorEvent(Base):
    __tablename__ = "monitor_event"

    monitor_event_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    txid: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    user: Mapped[User] = relationship("User")

    __table_args__ = (
        Index("ix_monitor_event_user", "user_id"),
        Index("ix_monitor_event_txid", "txid"),
    )


