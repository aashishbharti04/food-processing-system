"""Database access layer.

Provides a thin abstraction over two backends — MySQL (production) and SQLite
(local/dev/test) — so the rest of the application can stay backend-agnostic.

The two drivers disagree on small details (parameter placeholder, auto-increment
syntax, ``DECIMAL`` vs ``FLOAT`` returns). This module hides those differences
behind a single :class:`Database` object exposing parameterised ``execute`` and
``query`` helpers. All callers MUST pass parameters separately — never format
values into SQL strings — which is what closes the SQL-injection hole present in
the original code.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from .config import SCHEMA_PATH, DatabaseConfig


class DatabaseError(RuntimeError):
    """Raised when the database cannot be reached or a query fails."""


class Database:
    """A backend-agnostic database connection wrapper.

    Use as a context manager to guarantee the connection is closed::

        with Database.connect(config) as db:
            db.execute("INSERT ...", params)
    """

    def __init__(self, connection: Any, *, placeholder: str, backend: str) -> None:
        self._conn = connection
        self._placeholder = placeholder
        self.backend = backend

    # -- Construction ----------------------------------------------------- #

    @classmethod
    def connect(cls, config: DatabaseConfig) -> Database:
        """Open a connection for the configured backend."""
        if config.backend == "sqlite":
            return cls._connect_sqlite(config)
        if config.backend == "mysql":
            return cls._connect_mysql(config)
        raise DatabaseError(
            f"Unknown DB_BACKEND '{config.backend}'. Use 'mysql' or 'sqlite'."
        )

    @classmethod
    def _connect_sqlite(cls, config: DatabaseConfig) -> Database:
        try:
            conn = sqlite3.connect(config.sqlite_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as exc:  # pragma: no cover - environment specific.
            raise DatabaseError(f"Could not open SQLite database: {exc}") from exc
        return cls(conn, placeholder="?", backend="sqlite")

    @classmethod
    def _connect_mysql(cls, config: DatabaseConfig) -> Database:
        try:
            import mysql.connector as mysql  # Imported lazily so SQLite users
        except ImportError as exc:  # need not install the MySQL driver.
            raise DatabaseError(
                "mysql-connector-python is required for the MySQL backend. "
                "Install it with `pip install mysql-connector-python`."
            ) from exc
        try:
            conn = mysql.connect(
                host=config.host,
                port=config.port,
                user=config.user,
                password=config.password,
                database=config.database,
            )
        except mysql.Error as exc:
            raise DatabaseError(f"Could not connect to MySQL: {exc}") from exc
        return cls(conn, placeholder="%s", backend="mysql")

    # -- Query helpers ---------------------------------------------------- #

    def _adapt(self, sql: str) -> str:
        """Translate the canonical ``?`` placeholder to the backend's style."""
        if self._placeholder == "?":
            return sql
        return sql.replace("?", self._placeholder)

    def execute(self, sql: str, params: Sequence[Any] = ()) -> int:
        """Run a write statement and return the new row id (or 0)."""
        cursor = self._conn.cursor()
        try:
            cursor.execute(self._adapt(sql), tuple(params))
            self._conn.commit()
            return int(cursor.lastrowid or 0)
        except Exception as exc:  # noqa: BLE001 - normalise driver errors.
            self._conn.rollback()
            raise DatabaseError(str(exc)) from exc
        finally:
            cursor.close()

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
        """Run a read statement and return a list of dict rows."""
        cursor = self._conn.cursor()
        try:
            cursor.execute(self._adapt(sql), tuple(params))
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, _as_tuple(row), strict=False)) for row in rows]
        except Exception as exc:  # noqa: BLE001 - normalise driver errors.
            raise DatabaseError(str(exc)) from exc
        finally:
            cursor.close()

    def init_schema(self, schema_path: Path = SCHEMA_PATH) -> None:
        """Create the application tables if they do not yet exist."""
        statements = _split_statements(schema_path.read_text(encoding="utf-8"))
        for statement in statements:
            self.execute(statement)

    # -- Lifecycle -------------------------------------------------------- #

    def close(self) -> None:
        """Close the underlying connection."""
        try:
            self._conn.close()
        except Exception:  # noqa: BLE001 - closing should never raise upward.
            pass

    def __enter__(self) -> Database:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


def _as_tuple(row: Any) -> Iterable[Any]:
    """Normalise a driver row (sqlite3.Row or tuple) to an iterable of values."""
    if isinstance(row, sqlite3.Row):
        return tuple(row)
    return row


def _split_statements(script: str) -> list[str]:
    """Split a SQL script into individual statements, ignoring comments."""
    cleaned_lines = [
        line for line in script.splitlines() if not line.strip().startswith("--")
    ]
    cleaned = "\n".join(cleaned_lines)
    return [stmt.strip() for stmt in cleaned.split(";") if stmt.strip()]
