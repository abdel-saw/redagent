"""Portable paths and credentials for experiment entry points.

Path overrides are relative to the repository root unless absolute. Importing
this module does not read credentials or require third-party packages.
"""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
KEY_NAMES = ("OPENAI_API_KEY", "GROQ_API_KEY")


def _path(name: str, default: Path) -> Path:
    value = os.environ.get(name, "").strip()
    path = Path(value).expanduser() if value else default
    return path if path.is_absolute() else PROJECT_ROOT / path


def config_dir() -> Path:
    return _path("REDAGENT_CONFIG_DIR", PROJECT_ROOT / "experiments" / "config")


def results_dir() -> Path:
    return _path("REDAGENT_RESULTS_DIR", PROJECT_ROOT / "experiments" / "results")


def load_keys() -> dict[str, str]:
    """Read project .env, then prefer process environment (including blanks).

    An explicitly selected missing file is an error. No values are logged or
    written, interpolated, or copied into the process environment.
    """
    env_file = _path("REDAGENT_ENV_FILE", PROJECT_ROOT / ".env")
    if os.environ.get("REDAGENT_ENV_FILE", "").strip() and not env_file.is_file():
        raise FileNotFoundError("REDAGENT_ENV_FILE must point to an existing file")

    values: dict[str, str | None] = {}
    if env_file.is_file():
        from dotenv import dotenv_values

        values = dotenv_values(env_file, encoding="utf-8-sig", interpolate=False)
    return {
        name: (os.environ[name] if name in os.environ else values.get(name) or "").strip()
        for name in KEY_NAMES
    }


def key_for(model: str, keys: dict[str, str]) -> str:
    """Require the correct provider key before a model request is attempted."""
    if model.startswith("groq/"):
        name = "GROQ_API_KEY"
    elif model.startswith("openai/") or "/" not in model:
        name = "OPENAI_API_KEY"
    else:
        raise ValueError("Unsupported provider: configure an openai/ or groq/ model")
    key = keys.get(name, "").strip()
    if not key:
        raise ValueError(f"Missing {name}; set it in the environment or the project .env")
    return key
