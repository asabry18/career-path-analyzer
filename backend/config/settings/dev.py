"""Local development — SQLite by default; set DATABASE_URL or DB_* to use Postgres."""

import os
from urllib.parse import urlparse

from .base import *  # noqa: F403

DEBUG = os.environ.get("DEBUG", "True").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]


def _postgres_from_url(url: str) -> dict:
    parsed = urlparse(url)
    path = (parsed.path or "").lstrip("/")
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": path,
        "USER": parsed.username or "",
        "PASSWORD": parsed.password or "",
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or 5432),
    }


def _postgres_from_env() -> dict | None:
    url = os.environ.get("DATABASE_URL")
    if url:
        return _postgres_from_url(url)
    name = os.environ.get("DB_NAME")
    if not name:
        return None
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": name,
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }


_pg = _postgres_from_env()
if _pg:
    DATABASES = {"default": _pg}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
        }
    }
