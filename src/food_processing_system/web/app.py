"""Flask application factory for the web layer.

Composes two blueprints that share the same services and database:

* :mod:`food_processing_system.web.customer` — the customer-facing app at ``/``.
* :mod:`food_processing_system.web.admin`     — the admin dashboard at ``/admin``.
"""

from __future__ import annotations

from typing import Any

from flask import Flask, g, render_template

from ..config import WebConfig
from . import admin, customer
from .common import FOOTER, csrf_token


def create_app(web_config: WebConfig | None = None) -> Flask:
    """Build and configure the Flask application."""
    config = web_config or WebConfig.from_env()
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=config.secret_key,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        WEB_CONFIG=config,
    )

    # Helpers available inside every template.
    app.jinja_env.globals.update(csrf_token=csrf_token, footer=FOOTER)

    app.register_blueprint(customer.bp)
    app.register_blueprint(admin.bp)

    @app.teardown_appcontext
    def _close_db(_exc: BaseException | None) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.context_processor
    def _inject_flags() -> dict[str, Any]:
        return {"insecure_defaults": config.using_insecure_defaults}

    @app.errorhandler(404)
    def not_found(_exc: Any) -> Any:
        return render_template("error.html", code=404, message="Page not found"), 404

    @app.errorhandler(400)
    def bad_request(_exc: Any) -> Any:
        return render_template("error.html", code=400, message="Bad request"), 400

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
    print(f"==> Customer app:     http://{config.host}:{config.port}/")
    print(f"==> Admin dashboard:  http://{config.host}:{config.port}/admin")
    app.run(host=config.host, port=config.port)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
