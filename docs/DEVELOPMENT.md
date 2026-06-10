# Development Setup Guide

A step-by-step guide to getting a working development environment.

## 1. Prerequisites

- **Python 3.10 or newer** (`python --version`)
- **git**
- (Optional) **MySQL 8+** if you want to develop against the MySQL backend

## 2. Clone and create a virtual environment

```bash
git clone https://github.com/aashishbharti04/food-processing-system.git
cd food-processing-system

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
```

## 3. Install in editable mode with dev tools

```bash
pip install -e ".[dev]"
```

This installs the package plus `pytest`, `pytest-cov`, `ruff` and `mypy`.

## 4. Configure the environment

```bash
cp .env.example .env
# The defaults use SQLite, so no edits are required to get started.
```

## 5. Run the app

```bash
food-processing-system
# or
python -m food_processing_system
```

## 6. Quality gates

Run these before every commit (CI runs the same checks):

```bash
pytest                                   # run the test suite
pytest --cov=food_processing_system      # with coverage
ruff check .                             # lint
ruff format .                            # auto-format
mypy                                     # static type checking
```

## 7. Project layout

See [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md) and [ARCHITECTURE.md](ARCHITECTURE.md)
for how the code is organised and why.

## 8. Writing tests

- Tests live in `tests/` and run against an **in-memory SQLite** database, so they
  need no external services.
- Reuse the fixtures in `tests/conftest.py` (`db`, `customer_service`,
  `order_service`, `rating_service`).
- Keep tests fast, isolated and deterministic.

Example:

```python
def test_register_creates_account(customer_service):
    customer = customer_service.register("Asha", 101, "Mumbai", "pw")
    assert customer.account_no == 101
```

## 9. Common tasks

| Task | Command |
|------|---------|
| Run a single test file | `pytest tests/test_services.py` |
| Run a single test | `pytest tests/test_services.py::test_place_order` |
| Reset local SQLite DB | `rm food.db` (recreated on next run) |
| Build the package | `python -m build` |

## 10. Troubleshooting

- **`ModuleNotFoundError: food_processing_system`** — run `pip install -e .` again,
  and make sure your virtual environment is activated.
- **MySQL connection errors** — verify `DB_*` env vars and that the server is
  reachable; install the backend with `pip install -e ".[mysql]"`.
- **Garbled symbols in the terminal** — the UI auto-falls back to ASCII on legacy
  encodings; you can also set `NO_COLOR=1`.
