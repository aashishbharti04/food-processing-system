"""Flask application factory and routes for the admin dashboard."""

from __future__ import annotations

import hmac
import secrets
from collections import Counter
from collections.abc import Callable
from decimal import Decimal
from functools import wraps
from typing import Any

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ..config import AppConfig, WebConfig
from ..database import Database
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
# Per-request database / services
# --------------------------------------------------------------------------- #


def _get_db() -> Database:
    """Open (once per request) a database connection bound to ``flask.g``."""
    if "db" not in g:
        config = AppConfig.from_env()
        db = Database.connect(config.database)
        db.init_schema()
        g.db = db
    return g.db  # type: ignore[no-any-return]


def _services() -> tuple[CustomerService, OrderService, RatingService]:
    db = _get_db()
    customers = CustomerRepository(db)
    orders = OrderRepository(db)
    ratings = RatingRepository(db)
    return (
        CustomerService(customers, orders, ratings),
        OrderService(orders),
        RatingService(ratings),
    )


# --------------------------------------------------------------------------- #
# Authentication & CSRF
# --------------------------------------------------------------------------- #


def login_required(view: Callable[..., Any]) -> Callable[..., Any]:
    """Redirect to the login page when the session is not authenticated."""

    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def _csrf_token() -> str:
    """Return the session CSRF token, creating one if needed."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


# --------------------------------------------------------------------------- #
# Application factory
# --------------------------------------------------------------------------- #


def create_app(web_config: WebConfig | None = None) -> Flask:
    """Build and configure the Flask application."""
    config = web_config or WebConfig.from_env()
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=config.secret_key,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    # Make helpers available inside every template.
    app.jinja_env.globals.update(csrf_token=_csrf_token, footer=FOOTER)

    @app.teardown_appcontext
    def _close_db(_exc: BaseException | None) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.context_processor
    def _inject_flags() -> dict[str, Any]:
        return {"insecure_defaults": config.using_insecure_defaults}

    # -- Routes ---------------------------------------------------------- #

    @app.route("/login", methods=["GET", "POST"])
    def login() -> Any:
        if request.method == "POST":
            if not hmac.compare_digest(
                request.form.get("csrf_token", ""), _csrf_token()
            ):
                abort(400, "Invalid CSRF token.")
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            # Constant-time comparison to avoid leaking credential length/content.
            ok_user = hmac.compare_digest(username, config.admin_username)
            ok_pass = hmac.compare_digest(password, config.admin_password)
            if ok_user and ok_pass:
                session.clear()
                session["logged_in"] = True
                return redirect(request.args.get("next") or url_for("dashboard"))
            flash("Invalid username or password.", "error")
        return render_template("login.html")

    @app.route("/logout", methods=["POST"])
    def logout() -> Any:
        if not hmac.compare_digest(request.form.get("csrf_token", ""), _csrf_token()):
            abort(400, "Invalid CSRF token.")
        session.clear()
        return redirect(url_for("login"))

    @app.route("/")
    @login_required
    def dashboard() -> Any:
        customers_svc, orders_svc, ratings_svc = _services()
        orders = orders_svc.all_orders()
        total_revenue = sum((o.price for o in orders), Decimal("0"))
        avg_rating = ratings_svc.average()

        # Aggregate orders per food item for the chart (top 8 by count).
        counts = Counter(o.food_name for o in orders)
        top_foods = counts.most_common(8)

        stats = {
            "customers": customers_svc.customer_count(),
            "orders": len(orders),
            "revenue": f"{total_revenue:.2f}",
            "avg_rating": f"{avg_rating:.1f}" if avg_rating is not None else "—",
        }
        recent = sorted(orders, key=lambda o: o.id, reverse=True)[:8]
        return render_template(
            "dashboard.html",
            active="dashboard",
            stats=stats,
            recent=recent,
            chart_labels=[name for name, _ in top_foods],
            chart_values=[count for _, count in top_foods],
        )

    @app.route("/customers")
    @login_required
    def customers() -> Any:
        customers_svc, _, _ = _services()
        query = request.args.get("q", "").strip().lower()
        rows = customers_svc.all_customers()
        if query:
            rows = [
                c for c in rows if query in c.name.lower() or query in str(c.account_no)
            ]
        return render_template(
            "customers.html", active="customers", customers=rows, query=query
        )

    @app.route("/orders")
    @login_required
    def orders() -> Any:
        _, orders_svc, _ = _services()
        query = request.args.get("q", "").strip().lower()
        rows = sorted(orders_svc.all_orders(), key=lambda o: o.id, reverse=True)
        if query:
            rows = [
                o
                for o in rows
                if query in o.food_name.lower() or query in o.customer_name.lower()
            ]
        return render_template("orders.html", active="orders", orders=rows, query=query)

    @app.errorhandler(404)
    def not_found(_exc: Any) -> Any:
        return render_template("error.html", code=404, message="Page not found"), 404

    return app


def main() -> int:
    """Run the development server. Returns a process exit code."""
    config = WebConfig.from_env()
    app = create_app(config)
    if config.using_insecure_defaults:
        print(
            "[!] Using insecure default credentials (admin / admin123). "
            "Set FLASK_SECRET_KEY and ADMIN_PASSWORD before deploying."
        )
    print(f"==> Admin dashboard: http://{config.host}:{config.port}")
    app.run(host=config.host, port=config.port)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
