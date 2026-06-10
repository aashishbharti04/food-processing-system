-- Food Processing System — database schema
--
-- Written in portable SQL so it can bootstrap either MySQL or SQLite.
-- The original project shipped two mismatched CREATE TABLE scripts whose
-- columns did not line up with the INSERT statements; this schema is the
-- corrected, single source of truth.

-- Customers (originally the loosely-defined "myc" table).
CREATE TABLE IF NOT EXISTS customers (
    account_no    INTEGER      NOT NULL PRIMARY KEY,
    name          VARCHAR(60)  NOT NULL,
    address       VARCHAR(200) NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

-- Orders (originally the "sales" table).
CREATE TABLE IF NOT EXISTS orders (
    id            INTEGER       NOT NULL PRIMARY KEY,
    food_name     VARCHAR(60)   NOT NULL,
    price         DECIMAL(10,2) NOT NULL,
    address       VARCHAR(200)  NOT NULL,
    customer_name VARCHAR(60)   NOT NULL,
    account_no    INTEGER       NOT NULL
);

-- Ratings collected from the "rate us" menu option.
CREATE TABLE IF NOT EXISTS ratings (
    id         INTEGER NOT NULL PRIMARY KEY,
    account_no INTEGER NOT NULL,
    score      INTEGER NOT NULL
);
