"""Tests for the database abstraction and SQL-injection safety."""

from __future__ import annotations

import pytest

from food_processing_system.config import DatabaseConfig
from food_processing_system.database import Database, DatabaseError
from food_processing_system.repositories import CustomerRepository
from food_processing_system.services import CustomerService


def test_init_schema_creates_tables(db: Database) -> None:
    # Querying the tables should not raise once the schema is initialised.
    assert db.query("SELECT COUNT(*) AS n FROM customers")[0]["n"] == 0
    assert db.query("SELECT COUNT(*) AS n FROM orders")[0]["n"] == 0
    assert db.query("SELECT COUNT(*) AS n FROM ratings")[0]["n"] == 0


def test_unknown_backend_raises() -> None:
    with pytest.raises(DatabaseError):
        Database.connect(DatabaseConfig(backend="oracle"))


def test_parameterised_queries_prevent_injection(
    customer_service: CustomerService, db: Database
) -> None:
    # A classic injection payload as the "name" must be stored literally and
    # must NOT drop the table.
    payload = "Robert'); DROP TABLE customers;--"
    customer_service.register(payload, 1, "Mumbai", "pw")
    repo = CustomerRepository(db)
    stored = repo.get(1)
    assert stored is not None
    assert stored.name == payload  # stored verbatim, table intact
    assert repo.count() == 1
