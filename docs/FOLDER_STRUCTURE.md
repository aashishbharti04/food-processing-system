# Folder Structure

```
food-processing-system/
├── src/
│   └── food_processing_system/        # The installable package
│       ├── __init__.py                # Version & metadata
│       ├── __main__.py                # `python -m food_processing_system`
│       ├── cli.py                     # Menus, prompts, App wiring (presentation)
│       ├── ui.py                      # Themed console: colours, spinner, states
│       ├── config.py                  # Env-based configuration (dataclasses)
│       ├── database.py                # SQLite/MySQL abstraction (persistence)
│       ├── repositories.py            # One repo per table (data access)
│       ├── services.py                # Business logic & validation
│       ├── models.py                  # Typed domain models (Customer/Order/Rating)
│       ├── security.py                # PBKDF2 password hashing
│       └── schema.sql                 # Canonical database schema
│
├── tests/                             # Pytest suite (runs on in-memory SQLite)
│   ├── conftest.py                    # Shared fixtures
│   ├── test_database.py               # DB abstraction + injection-safety tests
│   ├── test_security.py               # Password hashing tests
│   └── test_services.py               # Business-logic tests
│
├── docs/                              # Project documentation
│   ├── ARCHITECTURE.md
│   ├── FOLDER_STRUCTURE.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── DEVELOPMENT.md
│
├── legacy/                            # Original scripts, kept for reference
│   ├── main program food.py
│   ├── table myc.py
│   └── table sales.py
│
├── .github/
│   ├── workflows/ci.yml               # Lint, type-check, test, build
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── config.yml
│   └── PULL_REQUEST_TEMPLATE.md
│
├── assets/                            # Screenshots & media for the README
│
├── .env.example                       # Configuration template (copy to .env)
├── .gitignore
├── pyproject.toml                     # Packaging, dependencies, tool config
├── requirements.txt                   # Optional runtime extras
├── README.md
├── LICENSE                            # MIT
├── CONTRIBUTING.md
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
└── SECURITY.md
```

## Why `src/` layout?

The package lives under `src/` so that tests run against the **installed** package
rather than the working directory. This catches packaging mistakes early (e.g. a file
that isn't included in the distribution) and is the recommended modern Python layout.

## Naming conventions

- Modules: lowercase, single word where possible (`services.py`, not `Services.py`).
- Classes: `PascalCase` (`CustomerService`).
- Functions & variables: `snake_case`.
- Private helpers: prefixed with `_` (`_require_text`).
- Constants: `UPPER_SNAKE_CASE` (`PROJECT_NAME`).
