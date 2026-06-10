"""Tests for the business-logic services."""

from __future__ import annotations

import pytest

from food_processing_system.services import (
    AccountExistsError,
    AuthenticationError,
    CustomerService,
    OrderService,
    RatingService,
    ValidationError,
)

# -- Registration & authentication ------------------------------------------ #


def test_register_creates_account(customer_service: CustomerService) -> None:
    customer = customer_service.register("Asha", 101, "Mumbai", "pw")
    assert customer.account_no == 101
    assert customer_service.customer_count() == 1


def test_register_hashes_password(customer_service: CustomerService) -> None:
    customer = customer_service.register("Asha", 101, "Mumbai", "pw")
    assert customer.password_hash != "pw"


def test_duplicate_account_rejected(customer_service: CustomerService) -> None:
    customer_service.register("Asha", 101, "Mumbai", "pw")
    with pytest.raises(AccountExistsError):
        customer_service.register("Other", 101, "Delhi", "pw2")


def test_register_requires_name(customer_service: CustomerService) -> None:
    with pytest.raises(ValidationError):
        customer_service.register("  ", 101, "Mumbai", "pw")


def test_authenticate_success(customer_service: CustomerService) -> None:
    customer_service.register("Asha", 101, "Mumbai", "pw")
    customer = customer_service.authenticate("Asha", 101, "pw")
    assert customer.account_no == 101


def test_authenticate_wrong_password(customer_service: CustomerService) -> None:
    customer_service.register("Asha", 101, "Mumbai", "pw")
    with pytest.raises(AuthenticationError):
        customer_service.authenticate("Asha", 101, "wrong")


def test_authenticate_unknown_account(customer_service: CustomerService) -> None:
    with pytest.raises(AuthenticationError):
        customer_service.authenticate("Ghost", 999, "pw")


# -- Profile updates -------------------------------------------------------- #


def test_update_details_changes_row_not_count(
    customer_service: CustomerService,
) -> None:
    customer_service.register("Asha", 101, "Mumbai", "pw")
    customer_service.update_details(101, "Asha B", "Pune")
    assert customer_service.customer_count() == 1  # UPDATE, not INSERT
    updated = customer_service.all_customers()[0]
    assert updated.name == "Asha B"
    assert updated.address == "Pune"


# -- Orders ----------------------------------------------------------------- #


def test_place_order(order_service: OrderService) -> None:
    order = order_service.place_order(
        food_name="Pizza",
        price="12.50",
        address="Mumbai",
        customer_name="Asha",
        account_no=101,
    )
    assert order.food_name == "Pizza"
    assert str(order.price) == "12.50"
    assert order_service.order_count() == 1


def test_order_rejects_bad_price(order_service: OrderService) -> None:
    with pytest.raises(ValidationError):
        order_service.place_order(
            food_name="Pizza",
            price="free",
            address="Mumbai",
            customer_name="Asha",
            account_no=101,
        )


def test_order_rejects_negative_price(order_service: OrderService) -> None:
    with pytest.raises(ValidationError):
        order_service.place_order(
            food_name="Pizza",
            price="-5",
            address="Mumbai",
            customer_name="Asha",
            account_no=101,
        )


def test_orders_get_sequential_ids(order_service: OrderService) -> None:
    first = order_service.place_order(
        food_name="A", price="1", address="x", customer_name="n", account_no=1
    )
    second = order_service.place_order(
        food_name="B", price="2", address="y", customer_name="n", account_no=1
    )
    assert (first.id, second.id) == (1, 2)


# -- Ratings ---------------------------------------------------------------- #


def test_rating_within_range(rating_service: RatingService) -> None:
    rating_service.rate(101, 5)
    assert rating_service.average() == 5.0


def test_rating_out_of_range_rejected(rating_service: RatingService) -> None:
    with pytest.raises(ValidationError):
        rating_service.rate(101, 7)
