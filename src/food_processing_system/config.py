"""Application configuration.

All settings are read from environment variables so that secrets (database
credentials in particular) never live in source control. A local ``.env`` file
is loaded automatically when present; see ``.env.example`` for the full list.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:  # Optional dependency — the app still works using real environment vars.
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - dotenv is optional.
    pass


def _get_bool(name: str, default: bool = False) -> bool:
    """Read a boolean-ish environment variable."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class DatabaseConfig:
    """Database connection settings.

    ``backend`` selects the driver:

    * ``mysql``  — production backend (requires ``mysql-connector-python``).
    * ``sqlite`` — zero-config backend, ideal for local dev, demos and tests.
    """

    backend: str = "sqlite"
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = "food"
    sqlite_path: str = "food.db"

    @classmethod
    def from_env(cls) -> DatabaseConfig:
        """Build a configuration object from the current environment."""
        return cls(
            backend=os.getenv("DB_BACKEND", "sqlite").strip().lower(),
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "food"),
            sqlite_path=os.getenv("SQLITE_PATH", "food.db"),
        )


@dataclass(frozen=True)
class WebConfig:
    """Configuration for the optional web admin dashboard.

    Defaults let you run the dashboard immediately (log in with ``admin`` /
    ``admin123``), but the app shows an insecure-defaults warning until you set
    ``FLASK_SECRET_KEY`` and ``ADMIN_PASSWORD`` to your own values.
    """

    secret_key: str = "dev-insecure-change-me"
    admin_username: str = "admin"
    admin_password: str = "admin123"
    host: str = "127.0.0.1"
    port: int = 5000

    @property
    def using_insecure_defaults(self) -> bool:
        """Whether the secret key or admin password is still a built-in default."""
        return (
            self.secret_key == "dev-insecure-change-me"
            or self.admin_password == "admin123"
        )

    @classmethod
    def from_env(cls) -> WebConfig:
        """Build the web configuration from the current environment."""
        return cls(
            secret_key=os.getenv("FLASK_SECRET_KEY", "dev-insecure-change-me"),
            admin_username=os.getenv("ADMIN_USERNAME", "admin"),
            admin_password=os.getenv("ADMIN_PASSWORD", "admin123"),
            host=os.getenv("WEB_HOST", "127.0.0.1"),
            port=int(os.getenv("WEB_PORT", "5000")),
        )


@dataclass(frozen=True)
class AppConfig:
    """Top-level application configuration."""

    database: DatabaseConfig
    use_colors: bool = True

    @classmethod
    def from_env(cls) -> AppConfig:
        """Build the full application configuration from the environment."""
        return cls(
            database=DatabaseConfig.from_env(),
            # Respect the de-facto NO_COLOR standard (https://no-color.org).
            use_colors=not _get_bool("NO_COLOR", default=False),
        )


# Absolute path to the bundled SQL schema, used to bootstrap a fresh database.
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
