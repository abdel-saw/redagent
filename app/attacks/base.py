"""Attack module contracts + a reusable seed-then-mutate base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from app.llm import (
    AttackerLLM,
    AttackerRefused,
    BudgetExceeded,
    BudgetTracker,
    JudgeLLM,
)
from app.target_adapter import AdapterConfig, send_prompt


EventEmitter = Callable[[str, dict[str, Any]], Awaitable[None]]


@dataclass(frozen=True)
class Seed:
    name: str
    prompt: str
    judge_criteria: str
    rationale: str = ""


@dataclass
class AttackResult:
    success: bool
    severity: str
    title: str
    description: str
    seed_name: str | None = None
    prompt: str | None = None
    response: str | None = None
    verdict: str | None = None


@dataclass
class AttackContext:
    run_id: str
    target: AdapterConfig
    emit: EventEmitter
    max_attempts: int
    attacker: AttackerLLM | None = None
    judge: JudgeLLM | None = None
    budget: BudgetTracker | None = None
    mutations_only: bool = False
    conversation: bool = False
    recon: str | None = None


class AttackModule(ABC):
    id: str = ""
    title: str = ""
    owasp_id: str = ""
    severity: str = "medium"

    @abstractmethod
    async def run(self, ctx: AttackContext) -> AttackResult:
        ...


class SeededAttack(AttackModule):
    """Attack that tries deterministic seeds first, then LLM-generated mutations."""

    seeds: tuple[Seed, ...] = ()
    attack_goal: str = ""

    async def run(self, ctx: AttackContext) -> AttackResult:
        await ctx.emit(
            "attack.start", {"attack_id": self.id, "title": self.title}
        )

        if ctx.conversation:
            return await self._run_conversation(ctx)

        failed: list[tuple[str, str]] = []
        attempt_no = 0
        total = ctx.max_attempts
        last_resp = ""
        last_name = ""

        if ctx.mutations_only and ctx.attacker is None:
            await ctx.emit(
                "error",
                {
                    "attack_id": self.id,
                    "message": (
                        "mutations-only mode requires an attacker LLM — "
                        "configure an attacker model and key."
                    ),
                },
            )
            await ctx.emit("attack.end", {"attack_id": self.id, "success": False})
            return AttackResult(
                success=False,
                severity="info",
                title=f"{self.title} — skipped (mutations-only without attacker)",
                description="Mutations-only mode requires an attacker LLM.",
                verdict="config_error",
            )

        if not ctx.mutations_only:
            for seed in self.seeds[: ctx.max_attempts]:
                attempt_no += 1
                outcome = await self._try_prompt(
                    ctx, attempt_no, total, seed.name, seed.prompt, seed
                )
                if outcome.success:
                    return await self._finish_success(ctx, outcome)
                failed.append((seed.prompt, outcome.response))
                last_resp, last_name = outcome.response, seed.name

        if ctx.attacker is not None and ctx.budget is not None and self.seeds:
            mutation_seed = self.seeds[0]
            while attempt_no < ctx.max_attempts and not ctx.budget.exceeded():
                attempt_no += 1
                try:
                    mutated = await ctx.attacker.mutate(
                        attack_title=self.title,
                        attack_goal=self.attack_goal,
                        failed_attempts=failed,
                        recon=ctx.recon,
                    )
                except BudgetExceeded:
                    break
                except AttackerRefused as exc:
                    await self._emit_attacker_refused(
                        ctx, attempt_no, total, f"mutation_{attempt_no}", str(exc)
                    )
                    continue
                except Exception as exc:
                    await ctx.emit(
                        "error",
                        {"attack_id": self.id, "message": f"mutation failed: {exc}"},
                    )
                    break

                name = f"mutation_{attempt_no}"
                seed = Seed(
                    name=name,
                    prompt=mutated,
                    judge_criteria=mutation_seed.judge_criteria,
                    rationale="LLM-generated mutation",
                )
                outcome = await self._try_prompt(
                    ctx, attempt_no, total, name, mutated, seed
                )
                if outcome.success:
                    return await self._finish_success(ctx, outcome)
                failed.append((mutated, outcome.response))
                last_resp, last_name = outcome.response, name

        await ctx.emit("attack.end", {"attack_id": self.id, "success": False})
        return AttackResult(
            success=False,
            severity="info",
            title=f"{self.title} — no successful attack",
            description=(
                f"All {attempt_no} attempts (seeds + mutations) refused or bypassed."
            ),
            seed_name=last_name,
            prompt=None,
            response=last_resp,
            verdict="all_attempts_failed",
        )

    async def _emit_attacker_refused(
        self, ctx: AttackContext, attempt: int, total: int, name: str, detail: str
    ) -> None:
        """Record that the attacker model refused to generate a prompt. The
        refusal is NOT sent to the target; it is surfaced as its own status."""
        await ctx.emit(
            "attempt",
            {
                "attack_id": self.id,
                "attempt": attempt,
                "total": total,
                "seed": name,
                "status": "attacker_refused",
                "verdict_source": "attacker",
                "verdict_reason": (
                    "le modèle attaquant a refusé de générer un prompt — "
                    "non envoyé à la cible (essayez un modèle attaquant plus coopératif)"
                ),
            },
        )

    async def _run_conversation(self, ctx: AttackContext) -> AttackResult:
        """Multi-turn (crescendo) mode: the attacker drives a conversation,
        reading the target's replies and escalating across turns. Memory is
        kept server-side by the target (same session/cookie across turns), so
        each turn is a single send on the same ``ctx.target``.
        """
        if ctx.attacker is None or ctx.budget is None or not self.seeds:
            await ctx.emit(
                "error",
                {
                    "attack_id": self.id,
                    "message": (
                        "conversation mode requires an attacker LLM and at least "
                        "one seed — configure an attacker model and key."
                    ),
                },
            )
            await ctx.emit("attack.end", {"attack_id": self.id, "success": False})
            return AttackResult(
                success=False,
                severity="info",
                title=f"{self.title} — skipped (conversation without attacker)",
                description="Conversation mode requires an attacker LLM.",
                verdict="config_error",
            )

        criteria_seed = self.seeds[0]
        transcript: list[tuple[str, str]] = []
        total = ctx.max_attempts
        turn = 0
        last_resp = ""
        last_name = ""

        while turn < ctx.max_attempts and not ctx.budget.exceeded():
            turn += 1
            try:
                message = await ctx.attacker.next_turn(
                    attack_title=self.title,
                    attack_goal=self.attack_goal,
                    transcript=transcript,
                    recon=ctx.recon,
                )
            except BudgetExceeded:
                break
            except AttackerRefused as exc:
                await self._emit_attacker_refused(
                    ctx, turn, total, f"turn_{turn}", str(exc)
                )
                continue
            except Exception as exc:
                await ctx.emit(
                    "error",
                    {"attack_id": self.id, "message": f"turn generation failed: {exc}"},
                )
                break

            name = f"turn_{turn}"
            turn_seed = Seed(
                name=name,
                prompt=message,
                judge_criteria=criteria_seed.judge_criteria,
                rationale="multi-turn escalation",
            )
            outcome = await self._try_prompt(ctx, turn, total, name, message, turn_seed)
            if outcome.success:
                return await self._finish_success(ctx, outcome)
            transcript.append((message, outcome.response))
            last_resp, last_name = outcome.response, name

        await ctx.emit("attack.end", {"attack_id": self.id, "success": False})
        return AttackResult(
            success=False,
            severity="info",
            title=f"{self.title} — no successful attack (conversation)",
            description=f"Conversation of {turn} turn(s) did not reach the goal.",
            seed_name=last_name,
            prompt=None,
            response=last_resp,
            verdict="all_attempts_failed",
        )

    async def _try_prompt(
        self,
        ctx: AttackContext,
        attempt: int,
        total: int,
        name: str,
        prompt: str,
        seed: Seed,
    ) -> "_Outcome":
        await ctx.emit(
            "attempt",
            {
                "attack_id": self.id,
                "attempt": attempt,
                "total": total,
                "seed": name,
                "prompt": prompt,
                "status": "sending",
            },
        )
        try:
            response, _ = await send_prompt(ctx.target, prompt)
        except Exception as exc:
            await ctx.emit(
                "attempt",
                {
                    "attack_id": self.id,
                    "attempt": attempt,
                    "total": total,
                    "seed": name,
                    "status": "error",
                    "error": str(exc),
                },
            )
            return _Outcome(success=False, response="", verdict_source="error", reason=str(exc), prompt=prompt, name=name)

        if not response.strip():
            await ctx.emit(
                "attempt",
                {
                    "attack_id": self.id,
                    "attempt": attempt,
                    "total": total,
                    "seed": name,
                    "prompt": prompt,
                    "response": response,
                    "status": "refused",
                    "rationale": seed.rationale,
                    "verdict_source": "empty",
                    "verdict_reason": "réponse cible vide — jamais comptée comme succès",
                },
            )
            return _Outcome(
                success=False,
                response=response,
                verdict_source="empty",
                reason="empty target response — judge skipped",
                prompt=prompt,
                name=name,
            )

        if ctx.judge is not None and ctx.budget is not None and not ctx.budget.exceeded():
            try:
                verdict, reason = await ctx.judge.verdict(
                    attack_title=self.title,
                    success_criteria=seed.judge_criteria,
                    prompt=prompt,
                    response=response,
                )
            except BudgetExceeded:
                verdict, reason = "refused", "budget exceeded — judge skipped"
            except Exception as exc:
                verdict, reason = "refused", f"judge error: {exc}"
            success = verdict == "success"
            status = "success" if success else verdict
            await ctx.emit(
                "attempt",
                {
                    "attack_id": self.id,
                    "attempt": attempt,
                    "total": total,
                    "seed": name,
                    "prompt": prompt,
                    "response": response,
                    "status": status,
                    "rationale": seed.rationale,
                    "verdict_source": "llm",
                    "verdict_reason": reason,
                },
            )
            return _Outcome(
                success=success,
                response=response,
                verdict_source="llm",
                reason=reason,
                prompt=prompt,
                name=name,
            )

        await ctx.emit(
            "attempt",
            {
                "attack_id": self.id,
                "attempt": attempt,
                "total": total,
                "seed": name,
                "prompt": prompt,
                "response": response,
                "status": "refused",
                "rationale": seed.rationale,
                "verdict_source": "none",
                "verdict_reason": "no judge available",
            },
        )
        return _Outcome(
            success=False,
            response=response,
            verdict_source="none",
            reason="no judge available",
            prompt=prompt,
            name=name,
        )

    async def _finish_success(self, ctx: AttackContext, outcome: "_Outcome") -> AttackResult:
        await ctx.emit("attack.end", {"attack_id": self.id, "success": True})
        return AttackResult(
            success=True,
            severity=self.severity,
            title=f"{self.title} — successful ({outcome.name})",
            description=f"Attack succeeded. Verdict source: {outcome.verdict_source} — {outcome.reason}",
            seed_name=outcome.name,
            prompt=outcome.prompt,
            response=outcome.response,
            verdict="attack_executed",
        )


@dataclass
class _Outcome:
    success: bool
    response: str
    verdict_source: str
    reason: str
    prompt: str
    name: str
