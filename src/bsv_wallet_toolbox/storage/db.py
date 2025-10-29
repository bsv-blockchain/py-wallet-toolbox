from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


def _enable_sqlite_pragmas(engine: Engine) -> None:
    """Enable SQLite pragmas required for correctness.

    Summary:
        Ensure foreign key constraints are enforced on SQLite.
    TS parity:
        N/A (infra-only helper).
    Args:
        engine: SQLAlchemy Engine.
    Returns:
        None.
    Raises:
        None.
    Reference:
        sdk/py-sdk, toolbox/py-wallet-toolbox/tests
    """
    if engine.dialect.name == "sqlite":
        with engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA foreign_keys=ON;")


def create_engine_from_url(url: str, *, echo: bool = False, **kwargs) -> Engine:
    """Create a SQLAlchemy Engine for any supported backend.

    Summary:
        Create an Engine for SQLite/MySQL/PostgreSQL via a SQLAlchemy URL.
        Automatically enables SQLite pragmas.
    TS parity:
        N/A (infra-only helper).
    Args:
        url: SQLAlchemy URL (e.g., 'sqlite:///wallet.db', 'mysql+pymysql://...', 'postgresql+psycopg://...').
        echo: Enable SQL echo.
        **kwargs: Additional arguments forwarded to create_engine.
    Returns:
        A configured SQLAlchemy Engine.
    Raises:
        sqlalchemy.exc.ArgumentError: If URL is invalid.
    Reference:
        sdk/py-sdk, toolbox/py-wallet-toolbox/tests
    """
    engine = create_engine(url, future=True, echo=echo, **kwargs)
    _enable_sqlite_pragmas(engine)
    return engine


def create_sqlite_engine(path: str = "wallet.db", *, echo: bool = False) -> Engine:
    """Create a SQLite Engine with required pragmas enabled.

    Summary:
        Convenience wrapper for SQLite engines that enforces FK constraints.
    TS parity:
        N/A (infra-only helper).
    Args:
        path: SQLite database file path.
        echo: Enable SQL echo.
    Returns:
        A configured SQLAlchemy Engine.
    Raises:
        None.
    Reference:
        sdk/py-sdk, toolbox/py-wallet-toolbox/tests
    """
    return create_engine_from_url(f"sqlite:///{path}", echo=echo)


def create_session_factory(engine: Engine) -> sessionmaker:
    """Create a SQLAlchemy session factory bound to the given engine.

    Summary:
        Thin wrapper returning a configured sessionmaker.
    TS parity:
        N/A (infra-only helper).
    Args:
        engine: SQLAlchemy Engine.
    Returns:
        A sessionmaker bound to the engine.
    Raises:
        None.
    Reference:
        sdk/py-sdk, toolbox/py-wallet-toolbox/tests
    """
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def session_scope(SessionLocal: sessionmaker) -> Iterator:
    """Provide a transactional scope around a series of operations.

    Summary:
        Context manager that commits on success and rolls back on error.
    TS parity:
        N/A (infra-only helper).
    Args:
        SessionLocal: A sessionmaker instance.
    Returns:
        Iterator over a Session.
    Raises:
        Re-raises any exception after rollback.
    Reference:
        sdk/py-sdk, toolbox/py-wallet-toolbox/tests
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


