from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def create_engine_from_url(url: str, *, echo: bool = False, **kwargs: Any) -> Any:
    """Create a synchronous SQLAlchemy Engine for supported backends.

    Supports:
      - SQLite: sqlite:///path.db
      - MySQL:  mysql+pymysql://user:pass@host/db
      - Postgres: postgresql+psycopg2://user:pass@host/db
    """
    # Normalize any accidentally async driver URLs back to sync drivers
    url = url.replace("sqlite+aiosqlite://", "sqlite://")
    url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    url = url.replace("mysql+aiomysql://", "mysql+pymysql://")
    return create_engine(url, future=True, echo=echo, **kwargs)


def create_session_factory(engine: Any) -> Any:
    """Create a synchronous SQLAlchemy session factory."""
    return sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


@contextmanager
def session_scope(session_local: Any) -> Iterator[Session]:
    """Provide a transactional scope around a series of operations (sync)."""
    session: Session = session_local()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_sqlite_engine(path: str = "wallet.db", *, echo: bool = False) -> Any:
    """Create a synchronous SQLite Engine."""
    return create_engine_from_url(f"sqlite:///{path}", echo=echo)
