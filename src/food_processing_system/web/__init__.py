"""Optional web admin dashboard (Flask + Jinja).

A read-focused management view over the same data the CLI uses. It reuses the
existing service and repository layers verbatim — no business logic is
duplicated here.

Run it with::

    food-processing-dashboard         # or: python -m food_processing_system.web
"""

from __future__ import annotations

from .app import create_app, main

__all__ = ["create_app", "main"]
