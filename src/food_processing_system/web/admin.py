"""Admin dashboard blueprint (mounted at ``/admin``).

A read-focused management view over all customers, orders and ratings.
"""

from __future__ import annotations

import hmac
from collections import Counter
from decimal import Decimal
from typing import Any

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from .common import admin_required, require_csrf, services

bp = Blueprint("admin", __name__, url_prefix="/admin")

# Navigation shown in the admin sidebar.
NAV = [
    {
        "key": "dashboard",
        "label": "Overview",
        "icon": "📊",
        "endpoint": "admin.dashboard",
    },
    {
        "key": "customers",
        "label": "Customers",
        "icon": "👥",
        "endpoint": "admin.customers",
    },
    {"key": "orders", "label": "Orders", "icon": "🧾", "endpoint": "admin.orders"},
]


@bp.context_processor
def _inject_nav() -> dict[str, Any]:
    """Expose admin navigation + logout target to admin templates."""
    return {"nav": NAV, "logout_url": url_for("admin.logout"), "area": "admin"}


@bp.route("/login", methods=["GET", "POST"])
def login() -> Any:
    config = current_app.config["WEB_CONFIG"]
    if request.method == "POST":
        require_csrf()
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        # Constant-time comparison to avoid leaking credential length/content.
        ok_user = hmac.compare_digest(username, config.admin_username)
        ok_pass = hmac.compare_digest(password, config.admin_password)
        if ok_user and ok_pass:
            session.clear()
            session["admin"] = True
            return redirect(request.args.get("next") or url_for("admin.dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("admin/login.html")


@bp.route("/logout", methods=["POST"])
def logout() -> Any:
    require_csrf()
    session.clear()
    return redirect(url_for("admin.login"))


@bp.route("/")
@admin_required
def dashboard() -> Any:
    customers_svc, orders_svc, ratings_svc = services()
    orders = orders_svc.all_orders()
    total_revenue = sum((o.price for o in orders), Decimal("0"))
    avg_rating = ratings_svc.average()

    # Aggregate orders per food item for the chart (top 8 by count).
    top_foods = Counter(o.food_name for o in orders).most_common(8)

    stats = {
        "customers": customers_svc.customer_count(),
        "orders": len(orders),
        "revenue": f"{total_revenue:.2f}",
        "avg_rating": f"{avg_rating:.1f}" if avg_rating is not None else "—",
    }
    recent = sorted(orders, key=lambda o: o.id, reverse=True)[:8]
    return render_template(
        "admin/dashboard.html",
        active="dashboard",
        stats=stats,
        recent=recent,
        chart_labels=[name for name, _ in top_foods],
        chart_values=[count for _, count in top_foods],
    )


@bp.route("/customers")
@admin_required
def customers() -> Any:
    customers_svc, _, _ = services()
    query = request.args.get("q", "").strip().lower()
    rows = customers_svc.all_customers()
    if query:
        rows = [
            c for c in rows if query in c.name.lower() or query in str(c.account_no)
        ]
    return render_template(
        "admin/customers.html", active="customers", customers=rows, query=query
    )


@bp.route("/orders")
@admin_required
def orders() -> Any:
    _, orders_svc, _ = services()
    query = request.args.get("q", "").strip().lower()
    rows = sorted(orders_svc.all_orders(), key=lambda o: o.id, reverse=True)
    if query:
        rows = [
            o
            for o in rows
            if query in o.food_name.lower() or query in o.customer_name.lower()
        ]
    return render_template(
        "admin/orders.html", active="orders", orders=rows, query=query
    )
