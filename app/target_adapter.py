"""HTTP adapter for the target LLM application under audit (v2 — porté de V1).

The default preset `openai_chat` matches the wire shape of typical FastAPI +
LiteLLM targets. For any other endpoint, supply a JSON body template containing
the literal placeholder `{{prompt_json}}` (JSON-encoded) or `{{prompt}}` (raw),
plus optional headers and a dotted `response_path` to extract the assistant text.

Principe "fidèle à l'usage réel" : l'outil ne patche jamais la cible ; il parle
HTTP à la cible telle qu'elle tourne, via ce template paramétrable.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.config import settings


_OPENAI_BODY_TEMPLATE = (
    '{"messages": [{"role": "user", "content": {{prompt_json}}}], "stream": false}'
)
_OPENAI_RESPONSE_PATH = "choices.0.message.content"


class AdapterConfig(BaseModel):
    url: str
    preset: str = "openai_chat"
    body_template: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    response_path: str | None = None
    # "json" (corps application/json, défaut) ou "form" (x-www-form-urlencoded).
    # Capacité générique : de nombreuses API réelles (dont Gandalf) sont form-encoded.
    encoding: str = "json"
    timeout_s: float = Field(default_factory=lambda: settings.request_timeout_s)


def _render_body(template: str, prompt: str) -> dict[str, Any]:
    prompt_json = json.dumps(prompt, ensure_ascii=False)
    rendered = template.replace("{{prompt_json}}", prompt_json).replace(
        "{{prompt}}", prompt
    )
    return json.loads(rendered)


def _walk_path(obj: Any, path: str) -> Any:
    cur: Any = obj
    for part in path.split("."):
        if cur is None:
            return None
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def _effective(cfg: AdapterConfig) -> tuple[str, str]:
    if cfg.preset == "openai_chat":
        return (
            cfg.body_template or _OPENAI_BODY_TEMPLATE,
            cfg.response_path or _OPENAI_RESPONSE_PATH,
        )
    if not cfg.body_template or not cfg.response_path:
        raise ValueError(
            "custom preset requires both body_template and response_path"
        )
    return cfg.body_template, cfg.response_path


async def send_prompt(
    cfg: AdapterConfig, prompt: str
) -> tuple[str, dict[str, Any]]:
    """Send a single user-turn prompt to the target.

    Returns ``(assistant_text, raw_response_json)``. Raises ``httpx`` errors
    on transport failures.
    """
    template, path = _effective(cfg)
    body = _render_body(template, prompt)
    async with httpx.AsyncClient(timeout=cfg.timeout_s) as client:
        if cfg.encoding == "form":
            # Corps form-encoded : on laisse httpx poser le Content-Type.
            r = await client.post(cfg.url, data=body, headers=cfg.headers)
        else:
            headers = {"Content-Type": "application/json", **cfg.headers}
            r = await client.post(cfg.url, json=body, headers=headers)
        r.raise_for_status()
        data = r.json()
    text = _walk_path(data, path)
    return ("" if text is None else str(text)), data
