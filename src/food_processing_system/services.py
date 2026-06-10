"""Business logic layer.

Sits between the CLI and the repositories. Handles validation, password
hashing/verification and the application's rules, with clear exceptions the UI
can turn into friendly messages.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from .models import Customer, Order, Rating
from .repositories import CustomerRepository, OrderRepository, RatingRepository
from .security import hash_password, verify_password


class ServiceError(Exception):
    """Base class for expected, user-facing errors."""


class ValidationError(ServiceError):
    """Raised when user-supplied input fails validation."""


class AuthenticationError(ServiceError):
    """Raised when login credentials are invalid."""


class AccountExistsError(ServiceError):
    """Raised when registering an account number that already exists."""


# --------------------------------------------------------------------------- #
# Validation helpers
# --------------------------------------------------------------------------- #


def _require_text(value: str, field: str, *, max_length: int) -> str:
    """Validate and normalise a free-text field."""
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValidationError(f"{field} is required.")
    if len(cleaned) > max_length:
        raise ValidationError(f"{field} must be at most {max_length} characters.")
    return cleaned


def _require_price(value: str) -> Decimal:
    """Validate and parse a monetary amount."""
    try:
        price = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError("Price must be a valid number.") from exc
    if price <= 0:
        raise ValidationError("Price must be greater than zero.")
    return price.quantize(Decimal("0.01"))


# --------------------------------------------------------------------------- #
# Customer service
# --------------------------------------------------------------------------- #


class CustomerService:
    """Account registration, authentication and profile management."""

    NAME_MAX = 60
    ADDRESS_MAX = 200

    def __init__(
        self,
        customers: CustomerRepository,
        orders: OrderRepository,
        ratings: RatingRepository,
    ) -> None:
        self._customers = customers
        self._orders = orders
        self._ratings = ratings

    # -- Registration & auth --------------------------------------------- #

    def register(
        self, name: str, account_no: int, address: str, password: str
    ) -> Customer:
        """Create a new account with a securely hashed password."""
        name = _require_text(name, "Name", max_length=self.NAME_MAX)
        address = _require_text(address, "Address", max_length=self.ADDRESS_MAX)
        if not password:
            raise ValidationError("Password is required.")
        if self._customers.exists(account_no):
            raise AccountExistsError(
                f"Account number {account_no} is already registered."
            )
        customer = Customer(
            account_no=account_no,
            name=name,
            address=address,
            password_hash=hash_password(password),
        )
        self._customers.add(customer)
        return customer

    def authenticate(self, name: str, account_no: int, password: str) -> Customer:
        """Verify credentials and return the matching customer."""
        customer = self._customers.get(account_no)
        if (
            customer is None
            or customer.name.lower() != name.strip().lower()
            or not verify_password(password, customer.password_hash)
        ):
            raise AuthenticationError("Invalid name, account number or password.")
        return customer

    # -- Profile & listings ---------------------------------------------- #

    def update_details(self, account_no: int, name: str, address: str) -> None:
        """Update a customer's name and address."""
        name = _require_text(name, "Name", max_length=self.NAME_MAX)
        address = _require_text(address, "Address", max_length=self.ADDRESS_MAX)
        if not self._customers.exists(account_no):
            raise ValidationError("Account not found.")
        self._customers.update_details(account_no, name, address)

    def all_customers(self) -> list[Customer]:
        """Return every registered customer."""
        return self._customers.list_all()

    def customer_count(self) -> int:
        """Return the number of registered customers."""
        return self._customers.count()


# --------------------------------------------------------------------------- #
# Order service
# --------------------------------------------------------------------------- #


class OrderService:
    """Placing and listing food orders."""

    FOOD_MAX = 60
    ADDRESS_MAX = 200

    def __init__(self, orders: OrderRepository) -> None:
        self._orders = orders

    def place_order(
        self,
        *,
        food_name: str,
        price: str,
        address: str,
        customer_name: str,
        account_no: int,
    ) -> Order:
        """Validate and persist a new order."""
        food_name = _require_text(food_name, "Food name", max_length=self.FOOD_MAX)
        address = _require_text(address, "Address", max_length=self.ADDRESS_MAX)
        customer_name = _require_text(customer_name, "Name", max_length=60)
        return self._orders.add(
            food_name=food_name,
            price=_require_price(price),
            address=address,
            customer_name=customer_name,
            account_no=account_no,
        )

    def all_orders(self) -> list[Order]:
        """Return every order placed."""
        return self._orders.list_all()

    def order_count(self) -> int:
        """Return the total number of orders."""
        return self._orders.count()


# --------------------------------------------------------------------------- #
# Rating service
# --------------------------------------------------------------------------- #


class RatingService:
    """Collecting service ratings."""

    def __init__(self, ratings: RatingRepository) -> None:
        self._ratings = ratings

    def rate(self, account_no: int, score: int) -> Rating:
        """Record a 1–5 rating."""
        if not 1 <= score <= 5:
            raise ValidationError("Rating must be between 1 and 5.")
        return self._ratings.add(account_no, score)

    def average(self) -> float | None:
        """Return the average rating so far."""
        return self._ratings.average()
