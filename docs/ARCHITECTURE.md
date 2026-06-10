# Architecture

Food Processing System follows a **layered architecture**. Each layer has a single
responsibility and only talks to the layer directly beneath it. This keeps the code
testable, swappable, and easy to reason about.

```
┌─────────────────────────────────────────────┐
│                   cli.py                      │  Presentation
│   menus, prompts, input handling, App wiring  │
└───────────────────────┬───────────────────────┘
                        │ uses
┌───────────────────────▼───────────────────────┐
│                 services.py                    │  Business logic
│  validation, hashing, rules, domain exceptions │
└───────────────────────┬───────────────────────┘
                        │ uses
┌───────────────────────▼───────────────────────┐
│               repositories.py                  │  Data access
│   parameterised SQL → typed domain models      │
└───────────────────────┬───────────────────────┘
                        │ uses
┌───────────────────────▼───────────────────────┐
│                 database.py                    │  Persistence
│   backend abstraction (SQLite / MySQL)         │
└────────────────────────────────────────────────┘

         supporting modules:
         config.py · models.py · security.py · ui.py · schema.sql

┌────────────────────────────────────────────────┐
│        web/  (optional Flask dashboard)         │  Alternative front-end
│  reuses services + repositories + database      │  ──────────────────────►
└────────────────────────────────────────────────┘   (no logic duplicated)
```

The optional **web dashboard** (`web/`) is a second presentation layer. It plugs
into the *same* services and repositories the CLI uses, which is the whole point
of the layered design — business logic is written once and consumed by both the
terminal and the browser. The dashboard adds only web concerns: routing, session
auth, CSRF protection, and HTML templates.

## Layer responsibilities

| Layer | Module(s) | Responsibility | Depends on |
|-------|-----------|----------------|------------|
| Presentation | `cli.py`, `ui.py` | Menus, prompts, themed output, input validation/re-prompting | services |
| Business logic | `services.py` | Validation, password hashing/verification, rules, domain exceptions | repositories, security, models |
| Data access | `repositories.py` | One class per table; parameterised SQL; maps rows → models | database, models |
| Persistence | `database.py` | Connect to SQLite/MySQL; placeholder translation; schema bootstrap | config |
| Cross-cutting | `config.py`, `models.py`, `security.py`, `schema.sql` | Configuration, typed models, hashing, SQL schema | — |

## Key design decisions

### 1. Backend abstraction (`database.py`)
A single `Database` class wraps either driver. Queries are written once using the
canonical `?` placeholder and translated to `%s` for MySQL. Rows are normalised to
`dict` so repositories are backend-agnostic. **All queries are parameterised**, which
eliminates SQL injection.

### 2. Repository pattern (`repositories.py`)
`CustomerRepository`, `OrderRepository` and `RatingRepository` encapsulate all SQL.
Auto-increment ids are computed portably as `MAX(id) + 1`, avoiding backend-specific
syntax differences.

### 3. Service layer (`services.py`)
Holds the business rules and raises typed, user-facing exceptions (`ValidationError`,
`AuthenticationError`, `AccountExistsError`) that the CLI turns into friendly messages.

### 4. Security by default (`security.py`)
Passwords are salted and hashed with PBKDF2-HMAC-SHA256 using only the standard
library — no plaintext, and no third-party dependency.

### 5. Configuration via environment (`config.py`)
Frozen dataclasses built from environment variables (with optional `.env` support),
so no secrets ever live in source control.

## Data flow example — placing an order

```
User → cli._order_food()
     → OrderService.place_order()      # validates name, price, address
     → OrderRepository.add()           # parameterised INSERT
     → Database.execute()              # commits, returns new id
     → Order model returned up the stack → success state rendered by ui.Console
```

## Error handling strategy

- **Expected** errors (bad input, duplicate account, auth failure) are typed
  `ServiceError` subclasses, caught in the CLI and shown as friendly messages.
- **Infrastructure** errors are normalised to `DatabaseError` at the persistence
  boundary and reported with a non-zero exit code.
- Non-numeric menu/number input is re-prompted instead of crashing.
