"""Shared pytest fixtures.

Every test runs against an in-memory SQLite database, so the suite needs no
MySQL server and leaves nothing behind.
"""

from __future__ import annotations

import pytest

from food_processing_system.config import DatabaseConfig
from food_processing_system.database import Database
from food_processing_system.repositories import (
    CustomerRepository,
    OrderRepository,
    RatingRepository,
)
from food_processing_system.services import (
    CustomerService,
    OrderService,
    RatingService,
)


@pytest.fixture()
def db() -> Database:
    """An initialised in-memory SQLite database."""
    database = Database.connect(
        DatabaseConfig(backend="sqlite", sqlite_path=":memory:")
    )
    database.init_schema()
    yield database
    database.close()


@pytest.fixture()
def customer_service(db: Database) -> CustomerService:
    return CustomerService(
        CustomerRepository(db), OrderRepository(db), RatingRepository(db)
    )


@pytest.fixture()
def order_service(db: Database) -> OrderService:
    return OrderService(OrderRepository(db))


@pytest.fixture()
def rating_service(db: Database) -> RatingService:
    return RatingService(RatingRepository(db))
