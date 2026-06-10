# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Optional web admin dashboard** (`food_processing_system.web`, Flask + Jinja):
  - Overview with stat cards (customers, orders, revenue, average rating) and a
    "top ordered items" chart.
  - Searchable customer and order tables.
  - Secure, CSRF-protected admin login with constant-time credential comparison
    and hardened session cookies (`HttpOnly`, `SameSite=Lax`).
  - Responsive layout with dark/light mode; empty and error states.
  - Reuses the existing service/repository layers — no business logic duplicated.
- `food-processing-dashboard` console script and `python -m food_processing_system.web`.
- `web` install extra (`pip install -e ".[web]"`) and web configuration in
  `config.WebConfig` / `.env.example`.
- Six web tests (`tests/test_web.py`) covering auth, CSRF and page rendering.

## [1.0.0] - 2026-06-10

The first production-ready release. The original single-file script was refactored
into a clean, tested, secure and installable Python package while preserving every
feature.

### Added
- Layered architecture: `cli → services → repositories → database`.
- Pluggable database backends — **SQLite** (default) and **MySQL**.
- Salted **PBKDF2-HMAC-SHA256** password hashing (`security.py`).
- Environment-based configuration with optional `.env` support (`config.py`).
- Typed domain models (`Customer`, `Order`, `Rating`).
- Themed terminal UI: colours, banners, spinner (loading state), empty & error
  states, and an ASCII fallback for legacy consoles.
- Input validation and graceful error handling throughout.
- Automatic schema bootstrapping from `schema.sql`.
- `pytest` test suite (23 tests) runnable without any external services.
- Packaging via `pyproject.toml` with a `food-processing-system` console script.
- Project documentation (`docs/`), CI workflow, issue/PR templates, and full
  open-source meta files.
- Professional footer with contact and social links.

### Fixed
- **Critical:** SQL injection via string-concatenated queries — now fully parameterised.
- **Critical:** hardcoded database credentials — now read from the environment.
- **Critical:** plaintext password storage — now securely hashed.
- **High:** mismatched table schemas (columns did not match the `INSERT`s).
- **High:** "update details" inserted duplicate rows instead of updating.
- **High:** unreliable login check that never verified the password.
- **Medium:** crashes on non-numeric input — now re-prompts.
- **Medium:** duplicated connection logic across files — now centralised.

### Changed
- Consolidated `main program food.py`, `table myc.py` and `table sales.py` into a
  single, importable package. Legacy scripts retained under `legacy/` for reference.

[1.0.0]: https://github.com/aashishbharti04/food-processing-system/releases/tag/v1.0.0
