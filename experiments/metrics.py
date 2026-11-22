"""Agrégation des métriques Exp.1 (Sprint 16).

Lit results/exp1_cells.jsonl (+ exp1_attempts.jsonl pour le détail refus/tentatives)
et produit :
  - tableau capture-rate par attaquant × défi,
  - synthèse par attaquant (capture globale, refus, coût),
  - export CSV (results/exp1_summary.csv).

Usage : .venv\\Scripts\\python -m experiments.metrics
"""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from experiments.configuration import results_dir

ROOT = Path(__file__).resolve().parent
# --dir <sous-dossier> pour analyser une ablation (results/<dir>)
_arg = [a for a in sys.argv[1:] if not a.startswith("-")]
RESULTS = (results_dir() / _arg[0]) if _arg else results_dir()


def _load(name: str) -> list[dict]:
    p = RESULTS / name
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _p(s: str) -> None:
    # Affichage seul : UTF-8 si la console le supporte, repli ASCII sinon
    # (aucun effet sur les résultats, seulement sur le rendu des captures).
    try:
        print(str(s))
    except UnicodeEncodeError:
        print(str(s).encode("ascii", "replace").decode("ascii"))


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """IC de Wilson à 95% pour une proportion k/n (honnêteté statistique, n petit)."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def main() -> None:
    cells = _load("exp1_cells.jsonl")
    attempts = _load("exp1_attempts.jsonl")
    if not cells:
        _p("aucune cellule — lance d'abord experiments.runner --matrix")
        return

    challenges = sorted({c["challenge"] for c in cells})
    models = sorted({c["attacker_model"] for c in cells})

    # (model, challenge) -> liste de cellules
    grid: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for c in cells:
        grid[(c["attacker_model"], c["challenge"])].append(c)

    # refus par attaquant (depuis attempts) : tentatives marquées attacker_refused
    refused_by_model: dict[str, int] = defaultdict(int)
    sent_by_model: dict[str, int] = defaultdict(int)
    for a in attempts:
        m = a.get("attacker_model")
        if not m:
            continue
        if a.get("status") == "attacker_refused":
            refused_by_model[m] += 1
        else:
            sent_by_model[m] += 1

    # --- Tableau capture-rate attaquant x défi ---
    _p("\n=== Exp.1 — Taux de capture (flags / runs) par attaquant x defi ===\n")
    head = f"{'attaquant':40} " + " ".join(f"{ch:>10}" for ch in challenges) + f"{'GLOBAL':>10}"
    _p(head)
    _p("-" * len(head))
    rows_csv = []
    for m in models:
        cells_m_total = 0
        flags_m_total = 0
        line = f"{m:40} "
        for ch in challenges:
            cs = grid.get((m, ch), [])
            n = len(cs)
            f = sum(1 for c in cs if c["success"])
            cells_m_total += n
            flags_m_total += f
            line += f"{(str(f)+'/'+str(n)):>10}" if n else f"{'-':>10}"
            rows_csv.append({"attacker": m, "challenge": ch, "runs": n, "flags": f,
                             "capture_rate": round(f / n, 3) if n else ""})
        gr = f"{flags_m_total}/{cells_m_total}"
        line += f"{gr:>10}"
        _p(line)

    # --- Synthèse par attaquant (avec IC de Wilson 95%) ---
    _p("\n=== Synthese par attaquant (capture avec IC Wilson 95%) ===\n")
    _p(f"{'attaquant':40} {'capture':>9} {'taux':>6} {'IC95':>14} {'refus%':>8} {'tent.moy':>9}")
    _p("-" * 90)
    for m in models:
        cs = [c for c in cells if c["attacker_model"] == m]
        n = len(cs); f = sum(1 for c in cs if c["success"])
        lo, hi = _wilson(f, n)
        rate = f / n if n else 0.0
        wins = [c["winning_attempt"] for c in cs if c["success"] and c.get("winning_attempt")]
        mean_win = round(sum(wins) / len(wins), 1) if wins else None
        total_attempts = sent_by_model[m] + refused_by_model[m]
        refus_pct = round(100 * refused_by_model[m] / total_attempts, 1) if total_attempts else 0.0
        ci = f"[{lo:.2f},{hi:.2f}]"
        _p(f"{m:40} {f}/{n:>3} {rate:>6.2f} {ci:>14} {refus_pct:>7}% {str(mean_win):>9}")

    # --- Synthese par defi (avec IC) ---
    _p("\n=== Synthese par defi (tous attaquants, IC Wilson 95%) ===\n")
    for ch in challenges:
        cs = [c for c in cells if c["challenge"] == ch]
        n = len(cs); f = sum(1 for c in cs if c["success"])
        lo, hi = _wilson(f, n)
        capt_models = sorted({c["attacker_model"].split("/")[-1] for c in cs if c["success"]})
        _p(f"{ch}: {f}/{n} flags (taux {f/n if n else 0:.2f}, IC95 [{lo:.2f},{hi:.2f}])"
           f"  | modeles: {', '.join(capt_models) or 'aucun'}")

    # --- Skill (mutation) vs variance/seed : source des captures ---
    # Une capture via SEED = la cible fuit un prompt écrit à la main (variance cible) ;
    # via MUTATION = l'attaquant LLM a GÉNÉRÉ le prompt gagnant (skill autonome).
    _p("\n=== Skill (mutation) vs variance (seed) — source des captures ===\n")
    src_by_ch: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    win_examples: dict[str, list[str]] = defaultdict(list)
    for a in attempts:
        if not a.get("oracle_success"):
            continue
        ch = a.get("challenge"); src = a.get("source", "?")
        bucket = "mutation/turn" if src in ("mutation", "turn") else "seed"
        src_by_ch[ch][bucket] += 1
        win_examples[ch].append(
            f"{a.get('attacker_model','?').split('/')[-1]}:{a.get('seed','?')}")
    for ch in challenges:
        d = src_by_ch.get(ch, {})
        seed_c = d.get("seed", 0); mut_c = d.get("mutation/turn", 0)
        verdict = ("SKILL (mutations)" if mut_c > seed_c
                   else "VARIANCE/seed" if seed_c > mut_c
                   else "mixte" if (seed_c or mut_c) else "aucune capture")
        _p(f"{ch}: seed={seed_c}  mutation/turn={mut_c}  -> {verdict}")
        if win_examples.get(ch):
            _p(f"    captures: {', '.join(win_examples[ch])}")

    # --- Export CSV ---
    out = RESULTS / "exp1_summary.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["attacker", "challenge", "runs", "flags", "capture_rate"])
        w.writeheader(); w.writerows(rows_csv)
    _p(f"\nCSV -> {out}")


if __name__ == "__main__":
    main()

