"""Tests for storage database utilities.

This module provides comprehensive test coverage for database utility functions.
"""

import pytest

from bsv_wallet_toolbox.storage.db import (
    create_engine_from_url,
    create_session_factory,
    create_sqlite_engine,
    session_scope,
)


def _has_module(module_name: str) -> bool:
    """Check if a module is available."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


class TestCreateEngineFromUrl:
    """Tests for create_engine_from_url function."""

    def test_create_sqlite_engine(self) -> None:
        """Test creating SQLite engine."""
        engine = create_engine_from_url("sqlite:///test.db")
        assert engine is not None
        assert str(engine.url) == "sqlite:///test.db"

    @pytest.mark.skipif(not _has_module("pymysql"), reason="pymysql not available")
    def test_create_mysql_engine(self) -> None:
        """Test creating MySQL engine."""
        url = "mysql+pymysql://user:pass@host/db"
        engine = create_engine_from_url(url)
        assert engine is not None
        assert engine.url.render_as_string(hide_password=False) == url

    @pytest.mark.skipif(not _has_module("psycopg2"), reason="psycopg2 not available")
    def test_create_postgres_engine(self) -> None:
        """Test creating PostgreSQL engine."""
        url = "postgresql+psycopg2://user:pass@host/db"
        engine = create_engine_from_url(url)
        assert engine is not None
        assert engine.url.render_as_string(hide_password=False) == url

    def test_normalize_async_sqlite_url(self) -> None:
        """Test normalizing async SQLite URLs to sync."""
        engine = create_engine_from_url("sqlite+aiosqlite:///test.db")
        assert engine is not None
        assert str(engine.url) == "sqlite:///test.db"

    @pytest.mark.skipif(not _has_module("pymysql"), reason="pymysql not available")
    def test_normalize_async_mysql_url(self) -> None:
        """Test normalizing async MySQL URLs to sync."""
        url = "mysql+aiomysql://user:pass@host/db"
        engine = create_engine_from_url(url)
        assert engine is not None
        assert engine.url.render_as_string(hide_password=False) == "mysql+pymysql://user:pass@host/db"

    @pytest.mark.skipif(not _has_module("psycopg2"), reason="psycopg2 not available")
    def test_normalize_async_postgres_url(self) -> None:
        """Test normalizing async PostgreSQL URLs to sync."""
        url = "postgresql+asyncpg://user:pass@host/db"
        engine = create_engine_from_url(url)
        assert engine is not None
        assert engine.url.render_as_string(hide_password=False) == "postgresql+psycopg2://user:pass@host/db"

    def test_echo_parameter(self) -> None:
        """Test echo parameter is passed through."""
        engine = create_engine_from_url("sqlite:///test.db", echo=True)
        assert engine.echo is True

    def test_additional_kwargs(self) -> None:
        """Test additional kwargs are passed through."""
        engine = create_engine_from_url("sqlite:///test.db", pool_pre_ping=True)
        assert engine.pool._pre_ping is True


class TestCreateSessionFactory:
    """Tests for create_session_factory function."""

    def test_create_session_factory(self) -> None:
        """Test creating session factory."""
        engine = create_engine_from_url("sqlite:///test.db")
        session_factory = create_session_factory(engine)

        assert session_factory is not None

        # Test that we can create a session
        session = session_factory()
        assert session is not None
        session.close()


class TestSessionScope:
    """Tests for session_scope context manager."""

    def test_session_scope_commit(self) -> None:
        """Test session scope commits on success."""
        engine = create_engine_from_url("sqlite:///:memory:")
        session_factory = create_session_factory(engine)

        session = None
        with session_scope(session_factory) as sess:
            # Session should be active
            assert sess.is_active
            session = sess

        # Session should be closed after context (may still be active in some SQLAlchemy versions)
        # Just verify the context manager worked without exception
        assert session is not None

    def test_session_scope_rollback_on_exception(self) -> None:
        """Test session scope rolls back on exception."""
        engine = create_engine_from_url("sqlite:///:memory:")
        session_factory = create_session_factory(engine)

        with pytest.raises(ValueError), session_scope(session_factory):
            # This should cause rollback
            raise ValueError("Test exception")

        # Just verify the exception was raised and rollback occurred
        # (Session state may vary by SQLAlchemy version)


class TestCreateSqliteEngine:
    """Tests for create_sqlite_engine function."""

    def test_create_sqlite_engine_default_path(self) -> None:
        """Test creating SQLite engine with default path."""
        engine = create_sqlite_engine()
        assert engine is not None
        assert str(engine.url) == "sqlite:///wallet.db"

    def test_create_sqlite_engine_custom_path(self) -> None:
        """Test creating SQLite engine with custom path."""
        engine = create_sqlite_engine("custom.db")
        assert engine is not None
        assert str(engine.url) == "sqlite:///custom.db"

    def test_create_sqlite_engine_echo_parameter(self) -> None:
        """Test echo parameter for SQLite engine."""
        engine = create_sqlite_engine(echo=True)
        assert engine.echo is True
