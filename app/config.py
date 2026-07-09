"""Central settings for RedAgent (v2 — porté tel quel depuis V1, internal sain)."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB = _PROJECT_ROOT / "data" / "redagent.db"


class Settings(BaseModel):
    sqlite_path: str = os.getenv("REDAGENT_DB", str(_DEFAULT_DB))
    attacker_model_default: str = os.getenv(
        "REDAGENT_ATTACKER_MODEL", "groq/llama-3.3-70b-versatile"
    )
    judge_model_default: str = os.getenv(
        "REDAGENT_JUDGE_MODEL", "openai/gpt-4o-mini-2024-07-18"
    )
    budget_usd_default: float = float(os.getenv("REDAGENT_BUDGET_USD", "1.0"))
    max_attempts_per_module: int = int(os.getenv("REDAGENT_MAX_ATTEMPTS", "5"))
    request_timeout_s: float = float(os.getenv("REDAGENT_TIMEOUT_S", "60"))


settings = Settings()
