# Internal API Reference

Although this is a CLI application, its layers expose a clean Python API you can
import and reuse (for example, to build a web or GUI front-end on top of the same
business logic). All examples assume the package is installed (`pip install -e .`).

## Quick start

```python
from food_processing_system.config import DatabaseConfig
from food_processing_system.database import Database
from food_processing_system.repositories import (
    CustomerRepository, OrderRepository, RatingRepository,
)
from food_processing_system.services import CustomerService, OrderService

db = Database.connect(DatabaseConfig(backend="sqlite", sqlite_path=":memory:"))
db.init_schema()

customers = CustomerService(
    CustomerRepository(db), OrderRepository(db), RatingRepository(db)
)
customers.register("Asha", 101, "Mumbai", "secret")
user = customers.authenticate("Asha", 101, "secret")
print(user.public_view())   # {'account_no': 101, 'name': 'Asha', 'address': 'Mumbai'}
```

## `database.Database`

| Method | Signature | Description |
|--------|-----------|-------------|
| `connect` | `connect(config: DatabaseConfig) -> Database` | Open a connection for the configured backend. |
| `init_schema` | `init_schema(schema_path=SCHEMA_PATH) -> None` | Create tables if missing. |
| `execute` | `execute(sql, params=()) -> int` | Run a write; returns the new row id. |
| `query` | `query(sql, params=()) -> list[dict]` | Run a read; returns dict rows. |
| `close` | `close() -> None` | Close the connection (also via context manager). |

> **Always** pass values through `params`; never format them into `sql`.

## `services.CustomerService`

| Method | Description | Raises |
|--------|-------------|--------|
| `register(name, account_no, address, password)` | Create an account (password hashed). | `ValidationError`, `AccountExistsError` |
| `authenticate(name, account_no, password)` | Verify credentials, return `Customer`. | `AuthenticationError` |
| `update_details(account_no, name, address)` | Update profile (real `UPDATE`). | `ValidationError` |
| `all_customers()` | List all customers. | — |
| `customer_count()` | Count registered customers. | — |

## `services.OrderService`

| Method | Description | Raises |
|--------|-------------|--------|
| `place_order(*, food_name, price, address, customer_name, account_no)` | Validate & persist an order, return `Order`. | `ValidationError` |
| `all_orders()` | List all orders. | — |
| `order_count()` | Count all orders. | — |

## `services.RatingService`

| Method | Description | Raises |
|--------|-------------|--------|
| `rate(account_no, score)` | Record a 1–5 rating. | `ValidationError` |
| `average()` | Average rating, or `None`. | — |

## `security`

| Function | Description |
|----------|-------------|
| `hash_password(password) -> str` | Salted PBKDF2-HMAC-SHA256 hash. |
| `verify_password(password, stored) -> bool` | Constant-time verification. |

## Domain models (`models`)

```python
Customer(account_no: int, name: str, address: str, password_hash: str)
Order(id: int, food_name: str, price: Decimal, address: str,
      customer_name: str, account_no: int)
Rating(id: int, account_no: int, score: int)
```

## Web layer (`web`)

The optional web layer exposes a standard Flask app factory, so it works with any
WSGI server:

```python
from food_processing_system.web import create_app

app = create_app()          # reads config from the environment
# gunicorn "food_processing_system.web:create_app()" --bind 0.0.0.0:8000
```

**Customer app** (`customer` blueprint, mounted at `/`):

| Route        | Method   | Auth | Description                                |
|--------------|----------|------|--------------------------------------------|
| `/`          | GET      | —    | Landing page (redirects to dashboard if logged in). |
| `/register`  | GET/POST | —    | Create an account (CSRF-protected).        |
| `/login`     | GET/POST | —    | Customer login (name + account no + password). |
| `/logout`    | POST     | 👤   | Clear the customer session (CSRF-protected). |
| `/dashboard` | GET      | 👤   | Customer overview: stats + recent orders.  |
| `/order`     | GET/POST | 👤   | Place a new order.                         |
| `/my-orders` | GET      | 👤   | The logged-in customer's orders.           |
| `/rate`      | GET/POST | 👤   | Submit a 1–5 star rating.                  |

**Admin dashboard** (`admin` blueprint, mounted at `/admin`):

| Route              | Method   | Auth | Description                            |
|--------------------|----------|------|----------------------------------------|
| `/admin/login`     | GET/POST | —    | Admin login (CSRF-protected form).     |
| `/admin/logout`    | POST     | 🔑   | Clear the admin session.               |
| `/admin/`          | GET      | 🔑   | Overview: stats, chart, recent orders. |
| `/admin/customers` | GET      | 🔑   | Customer table (supports `?q=`).       |
| `/admin/orders`    | GET      | 🔑   | Order table (supports `?q=`).          |

(👤 = customer session · 🔑 = admin session)

## Exceptions (`services`)

```
ServiceError                 # base for all expected, user-facing errors
├── ValidationError          # invalid input
├── AuthenticationError      # bad login credentials
└── AccountExistsError       # duplicate account number

DatabaseError (database)     # infrastructure / driver errors
```
