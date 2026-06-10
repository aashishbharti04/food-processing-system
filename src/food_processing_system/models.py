"""Typed domain models.

Plain dataclasses that describe the shape of the data the application works
with. Keeping these explicit (instead of passing raw tuples around, as the
original code did) makes the rest of the codebase self-documenting and far
easier to test.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Customer:
    """A registered customer account."""

    account_no: int
    name: str
    address: str
    password_hash: str

    def public_view(self) -> dict[str, object]:
        """Return customer details without exposing the password hash."""
        return {
            "account_no": self.account_no,
            "name": self.name,
            "address": self.address,
        }


@dataclass(frozen=True, slots=True)
class Order:
    """A single food order."""

    id: int
    food_name: str
    price: Decimal
    address: str
    customer_name: str
    account_no: int


@dataclass(frozen=True, slots=True)
class Rating:
    """A service rating submitted by a customer (1–5)."""

    id: int
    account_no: int
    score: int
