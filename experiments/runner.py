"""Exp.1 — Efficacité de l'attaquant (Sprint 16).

Pour chaque cellule (attaquant × défi × run), déroule la boucle seed→mutate du
moteur RedAgent contre une cible PromptMe, mais le **succès est décidé par
l'ORACLE déterministe** (`experiments.oracle`), PAS par un juge LLM. Le juge est
volontairement absent ici : sa fiabilité est évaluée séparément en Exp.2 (replay
des couples (prompt, réponse, label_oracle) loggés par ce runner).

Sorties (results/) :
  exp1_attempts.jsonl  — une ligne par tentative (prompt, réponse, oracle, coût…)
  exp1_cells.jsonl     — une ligne par cellule terminée (sert de checkpoint/reprise)

Usage :
  # une cellule (smoke)
  .venv\\Scripts\\python -m experiments.runner --challenge LLM02 \\
      --attacker openai/gpt-4o-mini-2024-07-18 --attempts 6
  # matrice complète depuis models.json
  .venv\\Scripts\\python -m experiments.runner --matrix --runs 5
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.attacks import get_attack
from app.llm import (
    AttackerLLM,
    AttackerRefused,
    BudgetExceeded,
    BudgetTracker,
    UsageTracker,
)
from app.recon import profile_target, recon_brief
from app.target_adapter import AdapterConfig, send_prompt
from experiments.configuration import (
    config_dir, results_dir, load_keys as _load_keys, key_for as _key_for,
)
from experiments.oracle import OracleSpec, OracleResult, evaluate, load_specs

ROOT = Path(__file__).resolve().parent
CFG = config_dir()
RESULTS = results_dir()
RESULTS.mkdir(parents=True, exist_ok=True)

TARGETS = json.loads((CFG / "targets.json").read_text(encoding="utf-8"))
SPECS = load_specs(CFG / "targets.json")
MODELS = json.loads((CFG / "models.json").read_text(encoding="utf-8"))
BUDGET_CAP = float(MODELS.get("budget_cap_usd", 2.0))

# défi PromptMe -> module d'attaque RedAgent
CHALLENGE_MODULE = {
    "LLM01": "llm01_prompt_injection",
    "LLM02": "llm02_sensitive_info",
    "LLM06": "llm06_excessive_agency",
    "LLM07": "llm07_system_prompt_leak",
}


# throttle Groq (free tier) : intervalle mini entre appels attaquant + backoff
GROQ_MIN_INTERVAL_S = 2.0
RATELIMIT_BACKOFF_S = (5, 15, 40)


# --------------------------------------------------------------------------- #
# Config d'une cellule
# --------------------------------------------------------------------------- #
@dataclass
class RunConfig:
    challenge: str                 # "LLM02"
    attacker_model: str            # "groq/llama-3.3-70b-versatile"
    max_attempts: int = 8
    mode: str = "single"           # "single" | "conversation"
    mutations_only: bool = False
    recon: bool = False
    run_idx: int = 0

    @property
    def cell_key(self) -> str:
        tag = f"{self.mode}{'+mo' if self.mutations_only else ''}{'+recon' if self.recon else ''}"
        return f"{self.challenge}|{self.attacker_model}|{tag}|r{self.run_idx}"


@dataclass
class CellResult:
    cell_key: str
    challenge: str
    attacker_model: str
    success: bool
    attempts: int
    refusals: int
    winning_attempt: int | None
    evidence: str
    cost_usd: float
    elapsed_s: float


# --------------------------------------------------------------------------- #
# Clés / providers
# --------------------------------------------------------------------------- #
def _adapter(challenge: str) -> AdapterConfig:
    a = TARGETS[challenge]["adapter"]
    return AdapterConfig(
        url=a["url"],
        preset=a.get("preset", "custom"),
        body_template=a.get("body_template"),
        response_path=a.get("response_path"),
        encoding=a.get("encoding", "json"),
        headers=a.get("headers", {}),
    )


# --------------------------------------------------------------------------- #
# Throttle + backoff pour la génération attaquant
# --------------------------------------------------------------------------- #
_last_call: dict[str, float] = {}
# Cache du recon : il ne dépend que de (défi, modèle attaquant), pas du run_idx
# → évite de re-profiler à chaque run (gros gain de tokens sur le free tier Groq).
_RECON_CACHE: dict[tuple[str, str], str | None] = {}


def _is_rate_limit(exc: Exception) -> bool:
    m = str(exc).lower()
    return any(t in m for t in ("rate limit", "rate_limit", "ratelimit", "tpd", "429", "quota"))


async def _generate(coro_factory, model: str):
    """Appelle une génération attaquant en respectant le throttle Groq et en
    réessayant avec backoff sur rate-limit. ``coro_factory`` est une lambda qui
    crée une nouvelle coroutine à chaque tentative."""
    if model.startswith("groq/"):
        wait = GROQ_MIN_INTERVAL_S - (time.time() - _last_call.get(model, 0))
        if wait > 0:
            await asyncio.sleep(wait)
    for i, backoff in enumerate((0, *RATELIMIT_BACKOFF_S)):
        if backoff:
            await asyncio.sleep(backoff)
        try:
            res = await coro_factory()
            _last_call[model] = time.time()
            return res
        except (AttackerRefused, BudgetExceeded):
            raise
        except Exception as exc:  # rate-limit / transient
            msg = str(exc).lower()
            if ("rate" in msg or "429" in msg or "quota" in msg) and i < len(RATELIMIT_BACKOFF_S):
                continue
            raise


# --------------------------------------------------------------------------- #
# Une cellule
# --------------------------------------------------------------------------- #
async def run_cell(cfg: RunConfig, *, keys: dict[str, str], budget: BudgetTracker) -> CellResult:
    module_id = CHALLENGE_MODULE[cfg.challenge]
    module = get_attack(module_id)()
    spec: OracleSpec = SPECS[cfg.challenge]
    target = _adapter(cfg.challenge)
    usage = UsageTracker()
    attacker = AttackerLLM(
        model=cfg.attacker_model,
        api_key=_key_for(cfg.attacker_model, keys),
        usage=usage,
        budget=budget,
    )

    recon_text: str | None = None
    if cfg.recon:
        ckey = (cfg.challenge, cfg.attacker_model)
        if ckey in _RECON_CACHE:
            recon_text = _RECON_CACHE[ckey]
        else:
            async def _noemit(_t, _d):  # recon emits events; on s'en passe ici
                return None
            recon = await _generate(
                lambda: profile_target(
                    target=target, attacker=attacker, emit=_noemit,
                    catalogue=[(module.id, module.title, module.attack_goal)],
                ),
                cfg.attacker_model,
            )
            recon_text = recon_brief(recon)
            _RECON_CACHE[ckey] = recon_text

    t0 = time.time()
    attempts_log: list[dict] = []
    failed: list[tuple[str, str]] = []
    attempt = 0
    refusals = 0
    success = False
    evidence = ""
    winning: int | None = None

    async def _try(name: str, source: str, prompt: str) -> bool:
        nonlocal attempt, success, evidence, winning
        attempt += 1
        c0 = budget.spent_usd
        ti0, to0 = usage.input_tokens, usage.output_tokens
        s = time.time()
        try:
            response, _ = await send_prompt(target, prompt)
            err = None
        except Exception as exc:
            response, err = "", str(exc)
        latency_ms = int((time.time() - s) * 1000)
        res: OracleResult = (
            await evaluate(spec, response) if response else OracleResult(success=False)
        )
        rec = {
            "exp": "1", "cell": cfg.cell_key, "challenge": cfg.challenge,
            "attacker_model": cfg.attacker_model, "mode": cfg.mode,
            "mutations_only": cfg.mutations_only, "recon": cfg.recon,
            "run_idx": cfg.run_idx, "attempt": attempt, "seed": name,
            "source": source, "prompt": prompt, "response": response,
            "oracle_success": res.success, "oracle_evidence": res.evidence,
            "oracle_detail": res.detail, "error": err,
            "tokens_in": usage.input_tokens - ti0,
            "tokens_out": usage.output_tokens - to0,
            "cost_usd": round(budget.spent_usd - c0, 6),
            "latency_ms": latency_ms, "ts": time.time(),
        }
        attempts_log.append(rec)
        if res.success:
            success, evidence, winning = True, res.evidence, attempt
            return True
        failed.append((prompt, response))
        return False

    def _log_status(name: str, source: str, status: str, **extra) -> None:
        rec = {
            "exp": "1", "cell": cfg.cell_key, "challenge": cfg.challenge,
            "attacker_model": cfg.attacker_model, "mode": cfg.mode,
            "mutations_only": cfg.mutations_only, "recon": cfg.recon,
            "run_idx": cfg.run_idx, "attempt": attempt, "seed": name,
            "source": source, "prompt": None, "response": None,
            "oracle_success": False, "oracle_evidence": "", "oracle_detail": "",
            "status": status, "ts": time.time(),
        }
        rec.update(extra)
        attempts_log.append(rec)

    if cfg.mode == "conversation":
        # Multi-tour (crescendo) : l'attaquant lit les réponses et enchaîne.
        # `failed` sert de transcript (message, réponse).
        while attempt < cfg.max_attempts and not budget.exceeded():
            try:
                msg = await _generate(
                    lambda: attacker.next_turn(
                        attack_title=module.title,
                        attack_goal=module.attack_goal,
                        transcript=failed,
                        recon=recon_text,
                    ),
                    cfg.attacker_model,
                )
            except AttackerRefused:
                refusals += 1
                attempt += 1
                _log_status(f"turn_{attempt}", "turn", "attacker_refused")
                continue
            except BudgetExceeded:
                break
            except Exception as exc:
                _log_status(f"turn_{attempt + 1}", "turn", "attacker_error", error=str(exc))
                break
            if await _try(f"turn_{attempt + 1}", "turn", msg):
                break
    else:
        # 1) seeds déterministes
        if not cfg.mutations_only:
            for seed in module.seeds[: cfg.max_attempts]:
                if await _try(seed.name, "seed", seed.prompt):
                    break

        # 2) mutations LLM
        if not success and module.seeds:
            while attempt < cfg.max_attempts and not budget.exceeded():
                try:
                    mutated = await _generate(
                        lambda: attacker.mutate(
                            attack_title=module.title,
                            attack_goal=module.attack_goal,
                            failed_attempts=failed,
                            recon=recon_text,
                        ),
                        cfg.attacker_model,
                    )
                except AttackerRefused:
                    refusals += 1
                    attempt += 1
                    _log_status(f"mutation_{attempt}", "mutation", "attacker_refused")
                    continue
                except BudgetExceeded:
                    break
                except Exception as exc:
                    _log_status(f"mutation_{attempt + 1}", "mutation", "attacker_error", error=str(exc))
                    break
                if await _try(f"mutation_{attempt + 1}", "mutation", mutated):
                    break

    # flush attempts
    with (RESULTS / "exp1_attempts.jsonl").open("a", encoding="utf-8") as f:
        for rec in attempts_log:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    cell = CellResult(
        cell_key=cfg.cell_key, challenge=cfg.challenge,
        attacker_model=cfg.attacker_model, success=success, attempts=attempt,
        refusals=refusals, winning_attempt=winning, evidence=evidence,
        cost_usd=round(budget.spent_usd, 6), elapsed_s=round(time.time() - t0, 1),
    )
    with (RESULTS / "exp1_cells.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(cell.__dict__, ensure_ascii=False) + "\n")
    return cell


def _done_cells() -> set[str]:
    p = RESULTS / "exp1_cells.jsonl"
    if not p.exists():
        return set()
    return {
        json.loads(line)["cell_key"]
        for line in p.read_text(encoding="utf-8").splitlines() if line.strip()
    }


# --------------------------------------------------------------------------- #
# Drivers
# --------------------------------------------------------------------------- #
async def run_matrix(*, runs: int, challenges: list[str], attempts: int,
                     mutations_only: bool, recon: bool, mode: str,
                     only_models: set[str] | None = None) -> None:
    keys = _load_keys()
    budget = BudgetTracker(cap_usd=BUDGET_CAP)
    done = _done_cells()
    exhausted: set[str] = set()
    for att in MODELS["attackers"]:
        model = att["id"]
        if only_models and model not in only_models:
            continue
        if model in exhausted:
            continue
        k = min(att.get("k", runs), runs)
        for ch in challenges:
            if model in exhausted:
                break
            for r in range(k):
                cfg = RunConfig(
                    challenge=ch, attacker_model=model, max_attempts=attempts,
                    mode=mode, mutations_only=mutations_only, recon=recon, run_idx=r,
                )
                if cfg.cell_key in done:
                    _p(f"skip (done) {cfg.cell_key}")
                    continue
                if budget.exceeded():
                    _p(f"!! BUDGET CAP {BUDGET_CAP}$ atteint — arret"); return
                try:
                    cell = await run_cell(cfg, keys=keys, budget=budget)
                except Exception as exc:
                    if _is_rate_limit(exc):
                        _p(f"!! RATE-LIMIT {model} -> skip ce modele aujourd'hui "
                           f"({str(exc)[:90]})")
                        exhausted.add(model)
                        break
                    _p(f"!! ERREUR {cfg.cell_key}: {str(exc)[:130]} -- on continue")
                    continue
                _p(f"{'FLAG' if cell.success else '----'} {cfg.cell_key} "
                   f"att={cell.attempts} ref={cell.refusals} win={cell.winning_attempt} "
                   f"${cell.cost_usd:.4f} {cell.elapsed_s}s")


async def run_single(cfg: RunConfig) -> None:
    keys = _load_keys()
    budget = BudgetTracker(cap_usd=BUDGET_CAP)
    cell = await run_cell(cfg, keys=keys, budget=budget)
    _p(f"{'FLAG' if cell.success else 'NO FLAG'} {cfg.cell_key} | "
       f"attempts={cell.attempts} refusals={cell.refusals} "
       f"winning={cell.winning_attempt} evidence={cell.evidence!r} "
       f"cost=${cell.cost_usd:.4f} {cell.elapsed_s}s")


def _p(s: str) -> None:
    print(str(s).encode("ascii", "replace").decode("ascii"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--challenge", default="LLM02")
    ap.add_argument("--attacker", default="openai/gpt-4o-mini-2024-07-18")
    ap.add_argument("--attempts", type=int, default=8)
    ap.add_argument("--mode", default="single", choices=["single", "conversation"])
    ap.add_argument("--mutations-only", action="store_true")
    ap.add_argument("--recon", action="store_true")
    ap.add_argument("--matrix", action="store_true")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--challenges", default="",
                    help="CSV des défis ; vide = défaut selon --bench")
    ap.add_argument("--attackers", default="",
                    help="matrice: restreint aux ids attaquants (CSV) ; vide = tous")
    ap.add_argument("--bench", default="promptme", choices=["promptme", "gandalf"],
                    help="banc cible : promptme (targets.json) ou gandalf (gandalf.json)")
    ap.add_argument("--tag", default="", help="sous-dossier results/<tag> (isole une ablation)")
    args = ap.parse_args()

    global RESULTS, TARGETS, SPECS, CHALLENGE_MODULE

    if args.bench == "gandalf":
        # 2e cible TIERCE : Gandalf (Lakera). Oracle = guess-password (non écrit
        # par l'auteur). Tous les niveaux utilisent le module GÉNÉRIQUE de fuite
        # de system prompt (le mot de passe est un secret du prompt système) —
        # on teste le TRANSFERT de l'attaquant générique, sans seed spécifique-cible.
        gpath = CFG / "gandalf.json"
        TARGETS = json.loads(gpath.read_text(encoding="utf-8"))
        SPECS = load_specs(gpath)
        CHALLENGE_MODULE = {cid: "llm07_system_prompt_leak" for cid in SPECS}

    if args.challenges:
        challenges = [c.strip() for c in args.challenges.split(",") if c.strip()]
    elif args.bench == "gandalf":
        challenges = list(SPECS.keys())
    else:
        challenges = ["LLM02", "LLM06", "LLM07"]

    if args.tag:
        RESULTS = results_dir() / args.tag
        RESULTS.mkdir(parents=True, exist_ok=True)
        _p(f"[tag] résultats -> {RESULTS}")

    if args.matrix:
        only = {m.strip() for m in args.attackers.split(",") if m.strip()} or None
        asyncio.run(run_matrix(
            runs=args.runs, challenges=challenges,
            attempts=args.attempts, mutations_only=args.mutations_only,
            recon=args.recon, mode=args.mode, only_models=only,
        ))
    else:
        cfg = RunConfig(
            challenge=args.challenge, attacker_model=args.attacker,
            max_attempts=args.attempts, mode=args.mode,
            mutations_only=args.mutations_only, recon=args.recon,
        )
        asyncio.run(run_single(cfg))


if __name__ == "__main__":
    main()

