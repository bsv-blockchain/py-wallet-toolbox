from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


def create_engine_from_url(url: str, *, echo: bool = False, **kwargs: Any):
    """Create an async SQLAlchemy Engine for any supported backend.

    Summary:
        Create an async Engine for SQLite/MySQL/PostgreSQL via a SQLAlchemy URL.
        Automatically converts URLs to async drivers (aiosqlite, asyncpg, aiomysql).
    TS parity:
        N/A (infra-only helper).
    Args:
        url: SQLAlchemy URL (e.g., 'sqlite:///wallet.db', 'mysql+pymysql://...', 'postgresql://...').
        echo: Enable SQL echo.
        **kwargs: Additional arguments forwarded to create_async_engine.
    Returns:
        A configured async SQLAlchemy Engine.
    Raises:
        sqlalchemy.exc.ArgumentError: If URL is invalid.
    Reference:
        sdk/py-sdk, toolbox/py-wallet-toolbox/tests
    """
    # Convert URLs to async drivers
    if url.startswith("sqlite://"):
        url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    elif url.startswith("mysql+"):
        url = url.replace("mysql+", "mysql+aiomysql+", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return create_async_engine(url, future=True, echo=echo, **kwargs)


def create_session_factory(engine: Any) -> Any:
    """Create an async SQLAlchemy session factory.

    Summary:
        Thin wrapper returning a configured async_sessionmaker.
    TS parity:
        N/A (infra-only helper).
    Args:
        engine: Async SQLAlchemy Engine.
    Returns:
        An async_sessionmaker bound to the engine.
    Raises:
        None.
    Reference:
        sdk/py-sdk, toolbox/py-wallet-toolbox/tests
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False
    )


def session_scope(SessionLocal: Any) -> Any:
    """[DEPRECATED] Placeholder for backward compatibility.
    
    This function exists only to prevent import errors from legacy code.
    For new code, use async_session_scope instead.
    """
    raise NotImplementedError(
        "Synchronous session_scope is no longer supported. "
        "Use async_session_scope with 'async with' instead."
    )


@asynccontextmanager
async def async_session_scope(AsyncSessionLocal: Any) -> AsyncIterator[Any]:
    """Provide a transactional async scope around a series of operations.

    Summary:
        Async context manager that commits on success and rolls back on error.
    TS parity:
        N/A (infra-only helper).
    Args:
        AsyncSessionLocal: An async_sessionmaker instance.
    Yields:
        An async Session.
    Raises:
        Re-raises any exception after rollback.
    Reference:
        sdk/py-sdk, toolbox/py-wallet-toolbox/tests
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def create_sqlite_engine(path: str = "wallet.db", *, echo: bool = False) -> Any:
    """Create an async SQLite Engine.

    Summary:
        Convenience wrapper for async SQLite engines.
    TS parity:
        N/A (infra-only helper).
    Args:
        path: SQLite database file path.
        echo: Enable SQL echo.
    Returns:
        A configured async SQLAlchemy Engine.
    Raises:
        None.
    Reference:
        sdk/py-sdk, toolbox/py-wallet-toolbox/tests
    """
    return create_engine_from_url(f"sqlite:///{path}", echo=echo)


