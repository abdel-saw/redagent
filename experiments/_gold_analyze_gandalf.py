"""Tier 1 — Analyse du gold standard humain Gandalf (Exp.2 sur cible tierce).

Joint les labels humains (gold_gandalf.xlsx) au recensement complet des 90 tuples
+ verdicts juges, et calcule, pour CHAQUE juge ET l'oracle Gandalf, les métriques
vs la **vérité-terrain humaine** : P/R/F1, accuracy, Cohen's κ, IC Wilson 95%.

Recensement COMPLET (90) : pas d'imputation — chaque ligne doit être adjugée.
Les 'ambigu' (fuite partielle / indice / encodé) sont EXCLUS du binaire et
reportés. Angle mort de l'oracle = gold=vuln mais oracle=négatif (fuite ratée).

Usage : cd redagentV2 && python -m experiments._gold_analyze_gandalf
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import openpyxl

import experiments.replay as replay
from experiments.replay import MODELS, _load_tuples, _sample

ROOT = Path(__file__).resolve().parent
SEED = 42
replay.SOURCES = [ROOT / "results" / "gandalf_mtx"]
RESULTS = ROOT / "results" / "gandalf_exp2"
XLSX = RESULTS / "gold_gandalf.xlsx"
KEYMAP = json.loads((RESULTS / "gold_gandalf_keymap.json").read_text(encoding="utf-8"))


def _p(s: str) -> None:
    # Affichage seul : UTF-8 si la console le supporte, repli ASCII sinon
    # (aucun effet sur les résultats, seulement sur le rendu des captures).
    try:
        print(str(s))
    except UnicodeEncodeError:
        print(str(s).encode("ascii", "replace").decode("ascii"))


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def _kappa(n11: int, n10: int, n01: int, n00: int) -> float:
    N = n11 + n10 + n01 + n00
    if N == 0:
        return 0.0
    po = (n11 + n00) / N
    pg1 = (n11 + n10) / N
    pj1 = (n11 + n01) / N
    pe = pg1 * pj1 + (1 - pg1) * (1 - pj1)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def _load_labels() -> dict[int, str]:
    wb = openpyxl.load_workbook(XLSX)
    ws = wb["adjudication"]
    out = {}
    for r in range(2, ws.max_row + 1):
        i = ws.cell(r, 1).value
        lab = ws.cell(r, 6).value
        if i is None or lab is None or str(lab).strip() == "":
            continue
        out[int(i)] = str(lab).strip().lower()
    return out


def _load_blocks(n_judges: int) -> dict[str, list[dict]]:
    lines = [json.loads(l) for l in
             (RESULTS / "exp2_verdicts.jsonl").read_text(encoding="utf-8").splitlines()
             if l.strip()]
    judges = [j["id"] for j in MODELS["judges"]]
    n = len(lines) // n_judges
    return {jid: lines[k * n:(k + 1) * n] for k, jid in enumerate(judges)}


def _metrics(name: str, preds: list[bool], gold: list[int]) -> dict:
    n11 = n10 = n01 = n00 = 0
    for pr, g in zip(preds, gold):
        if pr and g == 1: n11 += 1
        elif pr and g == 0: n01 += 1
        elif (not pr) and g == 0: n00 += 1
        else: n10 += 1
    tp, fp, tn, fn = n11, n01, n00, n10
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    acc = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) else 0.0
    pl, ph = _wilson(tp, tp + fp)
    rl, rh = _wilson(tp, tp + fn)
    return {"name": name, "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "precision": round(prec, 3), "recall": round(rec, 3),
            "f1": round(f1, 3), "accuracy": round(acc, 3),
            "kappa": round(_kappa(n11, n10, n01, n00), 3),
            "prec_ci": [round(pl, 3), round(ph, 3)],
            "recall_ci": [round(rl, 3), round(rh, 3)]}


def main() -> None:
    pool = _load_tuples()
    sample = _sample(pool, 1000, SEED)   # ordre identique au replay (seed=42)
    judges = [j["id"] for j in MODELS["judges"]]
    blocks = _load_blocks(len(judges))
    labels = _load_labels()
    N = len(sample)

    # sanity : verdicts alignés par position au sample
    for jid in judges:
        assert len(blocks[jid]) == N, f"bloc {jid} != {N}"
        for i, (s, v) in enumerate(zip(sample, blocks[jid])):
            assert s["challenge"] == v["challenge"] and s["oracle"] == v["oracle"], \
                f"desync {jid} @ {i}"

    _p("=== Tier 1 — Gold standard humain Gandalf (Exp.2 cible tierce) ===\n")
    missing = [i for i in range(N) if i not in labels]
    if missing:
        _p(f"!! ATTENTION : {len(missing)} lignes NON adjugees (ids={missing[:20]}...). "
           f"Recensement incomplet -> remplis le classeur avant analyse.\n")
    _p(f"adjuges={len(labels)}/{N} | distribution: {dict(Counter(labels.values()))}")

    gold_lab = [labels.get(i, "?") for i in range(N)]

    # binaire (exclure ambigu et non-adjugés)
    bin_idx = [i for i in range(N) if gold_lab[i] in ("vuln", "pas_vuln")]
    gold_bin = [1 if gold_lab[i] == "vuln" else 0 for i in bin_idx]
    n_amb = sum(1 for i in range(N) if gold_lab[i] == "ambigu")
    npos = sum(gold_bin); nneg = len(gold_bin) - npos
    _p(f"binaire: {len(bin_idx)} tuples ({npos} vuln, {nneg} pas_vuln) ; {n_amb} ambigu exclus\n")

    rows = [_metrics("ORACLE Gandalf (guess-password)",
                     [sample[i]["oracle"] for i in bin_idx], gold_bin)]
    for jid in judges:
        preds = [blocks[jid][i]["predicted"] for i in bin_idx]
        rows.append(_metrics(jid, preds, gold_bin))

    _p(f"{'rater (vs GOLD humain)':40} {'P':>5} {'R':>5} {'F1':>5} {'acc':>5} "
       f"{'kappa':>6} {'FP':>3} {'FN':>3}  {'R 95% IC':>14}")
    _p("-" * 100)
    for r in rows:
        ci = f"[{r['recall_ci'][0]:.2f},{r['recall_ci'][1]:.2f}]"
        _p(f"{r['name']:40} {r['precision']:>5} {r['recall']:>5} {r['f1']:>5} "
           f"{r['accuracy']:>5} {r['kappa']:>6} {r['fp']:>3} {r['fn']:>3}  {ci:>14}")

    # angle mort de l'oracle : gold=vuln mais oracle rate
    blind = [i for i, g in zip(bin_idx, gold_bin) if g == 1 and not sample[i]["oracle"]]
    false_cap = [i for i, g in zip(bin_idx, gold_bin) if g == 0 and sample[i]["oracle"]]
    _p(f"\n--- Oracle Gandalf vs gold humain ---")
    _p(f"angle mort (gold=vuln, oracle rate): {len(blind)}  ids={blind}")
    for i in blind:
        _p(f"   [{sample[i]['challenge']}] resp: {str(sample[i]['response'])[:90]!r}")
    _p(f"fausses captures (gold!=vuln, oracle=succes): {len(false_cap)}  ids={false_cap}")

    # cas ambigu
    amb_ids = [i for i in range(N) if gold_lab[i] == "ambigu"]
    _p(f"\n--- {len(amb_ids)} cas 'ambigu' (zone grise) ---")
    for i in amb_ids:
        npred = sum(blocks[j][i]["predicted"] for j in judges)
        _p(f"   id={i} [{sample[i]['challenge']}] oracle={sample[i]['oracle']} "
           f"juges_succes={npred}/{len(judges)}")
        _p(f"      resp: {str(sample[i]['response'])[:90]!r}")

    out = RESULTS / "exp2_gold_gandalf_summary.json"
    out.write_text(json.dumps({"rows": rows, "n_amb": n_amb,
                               "blind_spot": blind, "false_capture": false_cap},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    _p(f"\nresume -> {out}")


if __name__ == "__main__":
    main()
