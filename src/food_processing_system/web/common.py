"""Shared helpers for the web layer.

Database access, service construction, CSRF protection and auth decorators used
by both the customer-facing app and the admin dashboard blueprints.
"""

from __future__ import annotations

import hmac
import secrets
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import abort, g, redirect, request, session, url_for

from ..config import AppConfig
from ..database import Database
from ..models import Customer
from ..repositories import CustomerRepository, OrderRepository, RatingRepository
from ..services import CustomerService, OrderService, RatingService

# Branding reused from the CLI footer.
FOOTER = {
    "project": "Food Processing System",
    "email": "aashish@marketdoctorsonline.com",
    "links": {
        "LinkedIn": "https://in.linkedin.com/in/aashana1012",
        "GitHub": "https://github.com/aashishbharti04",
        "YouTube": "https://www.youtube.com/@CodeWithAsur",
        "Instagram": "https://www.instagram.com/asurwave1012",
    },
}


# --------------------------------------------------------------------------- #
# Database & services (one connection per request, bound to flask.g)
# --------------------------------------------------------------------------- #


def get_db() -> Database:
    """Open (once per request) a database connection bound to ``flask.g``."""
    if "db" not in g:
        config = AppConfig.from_env()
        db = Database.connect(config.database)
        db.init_schema()
        g.db = db
    return g.db  # type: ignore[no-any-return]


def services() -> tuple[CustomerService, OrderService, RatingService]:
    """Build the service objects for the current request."""
    db = get_db()
    customers = CustomerRepository(db)
    orders = OrderRepository(db)
    ratings = RatingRepository(db)
    return (
        CustomerService(customers, orders, ratings),
        OrderService(orders),
        RatingService(ratings),
    )


# --------------------------------------------------------------------------- #
# CSRF protection
# --------------------------------------------------------------------------- #


def csrf_token() -> str:
    """Return the session CSRF token, creating one if needed."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def require_csrf() -> None:
    """Abort with 400 if the submitted CSRF token is missing or invalid."""
    submitted = request.form.get("csrf_token", "")
    if not hmac.compare_digest(submitted, csrf_token()):
        abort(400, "Invalid CSRF token.")


# --------------------------------------------------------------------------- #
# Authentication
# --------------------------------------------------------------------------- #


def admin_required(view: Callable[..., Any]) -> Callable[..., Any]:
    """Require an authenticated admin session."""

    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if not session.get("admin"):
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def customer_required(view: Callable[..., Any]) -> Callable[..., Any]:
    """Require an authenticated customer session."""

    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if "customer_account" not in session:
            return redirect(url_for("customer.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def current_customer() -> Customer | None:
    """Return the logged-in customer, or ``None`` if not authenticated."""
    account_no = session.get("customer_account")
    if account_no is None:
        return None
    customers, _, _ = services()
    return customers.get(int(account_no))
