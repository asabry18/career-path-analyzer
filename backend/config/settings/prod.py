"""Production — Postgres required; DEBUG off."""

import os
from urllib.parse import urlparse

from .base import *  # noqa: F403

DEBUG = False

_hosts = os.environ.get("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for h in _hosts.split(",") if h.strip()]
if not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS must be set in production.")


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


url = os.environ.get("DATABASE_URL")
if url:
    DATABASES = {"default": _postgres_from_url(url)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["DB_NAME"],
            "USER": os.environ.get("DB_USER", ""),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }
