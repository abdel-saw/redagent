"""Registry of available attack modules (v2 — périmètre boîte-noire JSON :
LLM01/02/06/07. LLM03/04/05/08/09/10 hors-périmètre, cf. SPEC §3)."""

from __future__ import annotations

from app.attacks.base import AttackModule
from app.attacks.llm01_prompt_injection import PromptInjection
from app.attacks.llm02_sensitive_info import SensitiveInfoDisclosure
from app.attacks.llm06_excessive_agency import ExcessiveAgency
from app.attacks.llm07_system_prompt_leak import SystemPromptLeakage


_REGISTRY: dict[str, type[AttackModule]] = {
    cls.id: cls
    for cls in (
        PromptInjection,
        SensitiveInfoDisclosure,
        ExcessiveAgency,
        SystemPromptLeakage,
    )
}


def all_attacks() -> list[type[AttackModule]]:
    return list(_REGISTRY.values())


def get_attack(attack_id: str) -> type[AttackModule] | None:
    return _REGISTRY.get(attack_id)
