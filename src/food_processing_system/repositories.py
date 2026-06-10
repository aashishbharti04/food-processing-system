"""Data-access repositories.

Each repository owns the SQL for a single table and returns typed domain
models. Every query is parameterised, which removes the SQL-injection risk that
was present throughout the original implementation.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .database import Database
from .models import Customer, Order, Rating


def _next_id(db: Database, table: str) -> int:
    """Return the next available integer id for an auto-keyed table.

    Computed as ``MAX(id) + 1`` so the schema stays portable across SQLite and
    MySQL without relying on backend-specific auto-increment syntax.
    """
    rows = db.query(f"SELECT COALESCE(MAX(id), 0) AS max_id FROM {table}")
    return int(rows[0]["max_id"]) + 1


class CustomerRepository:
    """Persistence for customer accounts (the ``customers`` table)."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def get(self, account_no: int) -> Customer | None:
        """Fetch a customer by account number, or ``None`` if not found."""
        rows = self._db.query(
            "SELECT account_no, name, address, password_hash "
            "FROM customers WHERE account_no = ?",
            (account_no,),
        )
        return self._to_model(rows[0]) if rows else None

    def exists(self, account_no: int) -> bool:
        """Return whether an account number is already registered."""
        return self.get(account_no) is not None

    def add(self, customer: Customer) -> None:
        """Insert a new customer."""
        self._db.execute(
            "INSERT INTO customers (account_no, name, address, password_hash) "
            "VALUES (?, ?, ?, ?)",
            (
                customer.account_no,
                customer.name,
                customer.address,
                customer.password_hash,
            ),
        )

    def update_details(self, account_no: int, name: str, address: str) -> None:
        """Update an existing customer's name and address.

        The original code mistakenly used INSERT here, creating duplicate rows;
        this performs a real UPDATE.
        """
        self._db.execute(
            "UPDATE customers SET name = ?, address = ? WHERE account_no = ?",
            (name, address, account_no),
        )

    def list_all(self) -> list[Customer]:
        """Return every registered customer."""
        rows = self._db.query(
            "SELECT account_no, name, address, password_hash "
            "FROM customers ORDER BY account_no"
        )
        return [self._to_model(row) for row in rows]

    def count(self) -> int:
        """Return the number of registered customers."""
        rows = self._db.query("SELECT COUNT(*) AS total FROM customers")
        return int(rows[0]["total"])

    @staticmethod
    def _to_model(row: dict[str, Any]) -> Customer:
        return Customer(
            account_no=int(row["account_no"]),
            name=str(row["name"]),
            address=str(row["address"]),
            password_hash=str(row["password_hash"]),
        )


class OrderRepository:
    """Persistence for food orders (the ``orders`` table)."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def add(
        self,
        *,
        food_name: str,
        price: Decimal,
        address: str,
        customer_name: str,
        account_no: int,
    ) -> Order:
        """Insert a new order and return it."""
        order_id = _next_id(self._db, "orders")
        self._db.execute(
            "INSERT INTO orders "
            "(id, food_name, price, address, customer_name, account_no) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (order_id, food_name, str(price), address, customer_name, account_no),
        )
        return Order(
            id=order_id,
            food_name=food_name,
            price=price,
            address=address,
            customer_name=customer_name,
            account_no=account_no,
        )

    def list_all(self) -> list[Order]:
        """Return every order placed."""
        rows = self._db.query(
            "SELECT id, food_name, price, address, customer_name, account_no "
            "FROM orders ORDER BY id"
        )
        return [self._to_model(row) for row in rows]

    def list_for_account(self, account_no: int) -> list[Order]:
        """Return the orders belonging to a single account."""
        rows = self._db.query(
            "SELECT id, food_name, price, address, customer_name, account_no "
            "FROM orders WHERE account_no = ? ORDER BY id",
            (account_no,),
        )
        return [self._to_model(row) for row in rows]

    def count(self) -> int:
        """Return the total number of orders."""
        rows = self._db.query("SELECT COUNT(*) AS total FROM orders")
        return int(rows[0]["total"])

    @staticmethod
    def _to_model(row: dict[str, Any]) -> Order:
        return Order(
            id=int(row["id"]),
            food_name=str(row["food_name"]),
            price=Decimal(str(row["price"])),
            address=str(row["address"]),
            customer_name=str(row["customer_name"]),
            account_no=int(row["account_no"]),
        )


class RatingRepository:
    """Persistence for service ratings (the ``ratings`` table)."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def add(self, account_no: int, score: int) -> Rating:
        """Record a rating and return it."""
        rating_id = _next_id(self._db, "ratings")
        self._db.execute(
            "INSERT INTO ratings (id, account_no, score) VALUES (?, ?, ?)",
            (rating_id, account_no, score),
        )
        return Rating(id=rating_id, account_no=account_no, score=score)

    def average(self) -> float | None:
        """Return the average rating, or ``None`` when there are none."""
        rows = self._db.query("SELECT AVG(score) AS avg_score FROM ratings")
        value = rows[0]["avg_score"]
        return float(value) if value is not None else None
