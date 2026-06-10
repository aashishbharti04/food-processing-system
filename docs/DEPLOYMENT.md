# Deployment Guide

This is a command-line application, so "deployment" primarily means **building and
distributing** the package, and optionally provisioning a production MySQL database.

## 1. Build distributable artifacts

```bash
pip install build
python -m build
# produces dist/food_processing_system-1.0.0-py3-none-any.whl
#          dist/food_processing_system-1.0.0.tar.gz
```

Install the built wheel on any machine with Python 3.10+:

```bash
pip install food_processing_system-1.0.0-py3-none-any.whl
food-processing-system
```

## 2. Publish to PyPI (optional)

```bash
pip install twine
twine upload dist/*
```

Then anyone can install it with `pip install food-processing-system`.

## 3. Production MySQL setup

```bash
# Create the database and a least-privilege user
mysql -u root -p <<'SQL'
CREATE DATABASE IF NOT EXISTS food;
CREATE USER 'food_app'@'%' IDENTIFIED BY 'change-me';
GRANT SELECT, INSERT, UPDATE ON food.* TO 'food_app'@'%';
FLUSH PRIVILEGES;
SQL
```

Configure the app via environment variables (or a `.env` file):

```bash
export DB_BACKEND=mysql
export DB_HOST=your-db-host
export DB_PORT=3306
export DB_USER=food_app
export DB_PASSWORD=change-me
export DB_NAME=food

pip install "food-processing-system[mysql]"
food-processing-system   # schema is created automatically on first run
```

## 4. Running MySQL with Docker (local/staging)

```bash
docker run --name food-mysql \
  -e MYSQL_ROOT_PASSWORD=secret \
  -e MYSQL_DATABASE=food \
  -p 3306:3306 -d mysql:8

export DB_BACKEND=mysql DB_USER=root DB_PASSWORD=secret DB_NAME=food
food-processing-system
```

## 5. Deploying the web admin dashboard

The dashboard ships a Flask app factory (`food_processing_system.web:create_app`).
The bundled `food-processing-dashboard` command runs Flask's **development** server
— fine for local use, but in production run it behind a WSGI server:

```bash
pip install "food-processing-system[web]" gunicorn

export FLASK_SECRET_KEY="$(python -c 'import secrets;print(secrets.token_hex(32))')"
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD="a-strong-password"
export DB_BACKEND=mysql DB_USER=food_app DB_PASSWORD=... DB_NAME=food

gunicorn "food_processing_system.web:create_app()" --bind 0.0.0.0:8000 --workers 3
```

Always terminate TLS in front of it (a reverse proxy such as Nginx/Caddy), and
**never** ship the default `FLASK_SECRET_KEY` or `ADMIN_PASSWORD` — the dashboard
shows an insecure-defaults banner until both are set.

## 6. Environment checklist

- [ ] `DB_BACKEND` set correctly (`sqlite` or `mysql`).
- [ ] MySQL credentials provided via env/secret manager — **never** committed.
- [ ] Database created and reachable from the host.
- [ ] App installed with the `[mysql]` extra when using MySQL.
- [ ] `.env` is present locally and listed in `.gitignore` (it is by default).
- [ ] (Dashboard) `FLASK_SECRET_KEY` and `ADMIN_PASSWORD` set to strong values.
- [ ] (Dashboard) Served behind a WSGI server + TLS, not the dev server.

## Notes

- The schema is **idempotent** (`CREATE TABLE IF NOT EXISTS`), so first-run
  bootstrapping is safe to repeat.
- For SQLite deployments, ensure the process has write access to `SQLITE_PATH`.
