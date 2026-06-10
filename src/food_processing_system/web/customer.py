"""Customer-facing app blueprint (mounted at ``/``).

The browser equivalent of the CLI flow: register, log in, place orders, view
your own orders and rate the service — all reusing the same services.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ..services import ServiceError
from .common import (
    current_customer,
    customer_required,
    require_csrf,
    services,
)

bp = Blueprint("customer", __name__)

# Navigation shown to a logged-in customer.
NAV = [
    {
        "key": "home",
        "label": "Dashboard",
        "icon": "🏠",
        "endpoint": "customer.dashboard",
    },
    {"key": "order", "label": "Order food", "icon": "🍔", "endpoint": "customer.order"},
    {
        "key": "orders",
        "label": "My orders",
        "icon": "🧾",
        "endpoint": "customer.my_orders",
    },
    {"key": "rate", "label": "Rate us", "icon": "⭐", "endpoint": "customer.rate"},
]


@bp.context_processor
def _inject_nav() -> dict[str, Any]:
    """Expose customer navigation + logout target to customer templates."""
    return {
        "nav": NAV,
        "logout_url": url_for("customer.logout"),
        "area": "customer",
        "me": current_customer(),
    }


def _int_or_none(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- #
# Public pages
# --------------------------------------------------------------------------- #


@bp.route("/")
def home() -> Any:
    if "customer_account" in session:
        return redirect(url_for("customer.dashboard"))
    return render_template("customer/home.html")


@bp.route("/register", methods=["GET", "POST"])
def register() -> Any:
    if request.method == "POST":
        require_csrf()
        customers, _, _ = services()
        account_no = _int_or_none(request.form.get("account_no", ""))
        if account_no is None:
            flash("Account number must be a whole number.", "error")
        else:
            try:
                customers.register(
                    request.form.get("name", ""),
                    account_no,
                    request.form.get("address", ""),
                    request.form.get("password", ""),
                )
                flash("Account created — please log in.", "success")
                return redirect(url_for("customer.login"))
            except ServiceError as exc:
                flash(str(exc), "error")
    return render_template("customer/register.html")


@bp.route("/login", methods=["GET", "POST"])
def login() -> Any:
    if request.method == "POST":
        require_csrf()
        customers, _, _ = services()
        account_no = _int_or_none(request.form.get("account_no", ""))
        if account_no is None:
            flash("Account number must be a whole number.", "error")
        else:
            try:
                customer = customers.authenticate(
                    request.form.get("name", ""),
                    account_no,
                    request.form.get("password", ""),
                )
                session.clear()
                session["customer_account"] = customer.account_no
                return redirect(
                    request.args.get("next") or url_for("customer.dashboard")
                )
            except ServiceError as exc:
                flash(str(exc), "error")
    return render_template("customer/login.html")


@bp.route("/logout", methods=["POST"])
def logout() -> Any:
    require_csrf()
    session.clear()
    return redirect(url_for("customer.home"))


# --------------------------------------------------------------------------- #
# Authenticated pages
# --------------------------------------------------------------------------- #


@bp.route("/dashboard")
@customer_required
def dashboard() -> Any:
    customer = current_customer()
    if customer is None:  # account vanished — force re-login.
        session.clear()
        return redirect(url_for("customer.login"))
    _, orders_svc, _ = services()
    my_orders = orders_svc.orders_for_account(customer.account_no)
    total_spent = sum((o.price for o in my_orders), Decimal("0"))
    stats = {
        "orders": len(my_orders),
        "spent": f"{total_spent:.2f}",
        "last": my_orders[-1].food_name if my_orders else "—",
    }
    recent = sorted(my_orders, key=lambda o: o.id, reverse=True)[:5]
    return render_template(
        "customer/dashboard.html", active="home", stats=stats, recent=recent
    )


@bp.route("/order", methods=["GET", "POST"])
@customer_required
def order() -> Any:
    customer = current_customer()
    if customer is None:
        session.clear()
        return redirect(url_for("customer.login"))
    _, orders_svc, _ = services()
    if request.method == "POST":
        require_csrf()
        try:
            placed = orders_svc.place_order(
                food_name=request.form.get("food_name", ""),
                price=request.form.get("price", ""),
                address=request.form.get("address", "") or customer.address,
                customer_name=customer.name,
                account_no=customer.account_no,
            )
            flash(f"Order placed: {placed.food_name} (₹{placed.price}).", "success")
            return redirect(url_for("customer.my_orders"))
        except ServiceError as exc:
            flash(str(exc), "error")
    return render_template("customer/order.html", active="order", customer=customer)


@bp.route("/my-orders")
@customer_required
def my_orders() -> Any:
    customer = current_customer()
    if customer is None:
        session.clear()
        return redirect(url_for("customer.login"))
    _, orders_svc, _ = services()
    rows = sorted(
        orders_svc.orders_for_account(customer.account_no),
        key=lambda o: o.id,
        reverse=True,
    )
    return render_template("customer/my_orders.html", active="orders", orders=rows)


@bp.route("/rate", methods=["GET", "POST"])
@customer_required
def rate() -> Any:
    customer = current_customer()
    if customer is None:
        session.clear()
        return redirect(url_for("customer.login"))
    _, _, ratings_svc = services()
    if request.method == "POST":
        require_csrf()
        score = _int_or_none(request.form.get("score", ""))
        try:
            if score is None:
                raise ServiceError("Please choose a rating.")
            ratings_svc.rate(customer.account_no, score)
            flash("Thanks for rating us!", "success")
            return redirect(url_for("customer.dashboard"))
        except ServiceError as exc:
            flash(str(exc), "error")
    return render_template("customer/rate.html", active="rate")
