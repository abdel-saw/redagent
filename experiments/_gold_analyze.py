"""T0.3-bis — Analyse du gold standard humain (Exp.2).

Joint les labels humains (gold_standard.xlsx) à l'échantillon Exp.2 + verdicts, et
calcule, pour CHAQUE juge ET l'oracle, les métriques vs la **vérité-terrain humaine**
(primaire) : P/R/F1, accuracy, Cohen's κ, IC de Wilson 95% sur P et R.

Vérité-terrain complète sur 118 : labels humains pour les 32 tuples adjugés ;
imputation 'pas_vuln' pour les 86 restants (négatifs oracle jugés négatifs par TOUS).
Cette imputation est VALIDÉE par le set de contrôle C (10 négatifs unanimes adjugés).

Les tuples 'ambigu' (fuite partielle / cas limite) sont EXCLUS du binaire P/R/F1 et
reportés à part. L'angle mort de l'oracle = tuples gold=vuln mais oracle=négatif.

Usage : cd redagentV2 && python -m experiments._gold_analyze
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import openpyxl

from experiments.replay import MODELS, RESULTS, _load_tuples, _sample

NEG, SEED = 100, 42
XLSX = RESULTS / "gold_standard.xlsx"
KEYMAP = json.loads((RESULTS / "gold_keymap.json").read_text(encoding="utf-8"))


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
    pg1 = (n11 + n10) / N   # gold positif
    pj1 = (n11 + n01) / N   # juge positif
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
    """gold ∈ {0,1} (ambigu déjà exclus, alignés par index)."""
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
    sample = _sample(pool, NEG, SEED)
    judges = [j["id"] for j in MODELS["judges"]]
    blocks = _load_blocks(len(judges))
    labels = _load_labels()
    N = len(sample)

    # --- gold complet (118) : humain si adjugé, sinon 'pas_vuln' imputé ---
    gold_lab = ["pas_vuln"] * N
    for i, lab in labels.items():
        gold_lab[i] = lab

    # validation de l'imputation par le set de contrôle C
    ctrl_ids = [int(i) for i, m in KEYMAP.items() if m["set"] == "C"]
    ctrl_bad = [i for i in ctrl_ids if gold_lab[i] != "pas_vuln"]
    _p("=== T0.3-bis — Gold standard humain ===\n")
    _p(f"adjuges={len(labels)} | imputes 'pas_vuln'={N - len(labels)}")
    _p(f"controle C: {len(ctrl_ids)} tuples, {len(ctrl_bad)} non-'pas_vuln' "
       f"-> imputation {'VALIDEE' if not ctrl_bad else 'A REVOIR: '+str(ctrl_bad)}")

    # composition du gold par set
    for setname in ("A", "B", "C"):
        ids = [int(i) for i, m in KEYMAP.items() if m["set"] == setname]
        from collections import Counter
        c = Counter(gold_lab[i] for i in ids)
        _p(f"  set {setname} (n={len(ids)}): {dict(c)}")

    # indices binaires (exclure ambigu)
    bin_idx = [i for i in range(N) if gold_lab[i] in ("vuln", "pas_vuln")]
    gold_bin = [1 if gold_lab[i] == "vuln" else 0 for i in bin_idx]
    n_amb = sum(1 for i in range(N) if gold_lab[i] == "ambigu")
    npos = sum(gold_bin); nneg = len(gold_bin) - npos
    _p(f"\nbinaire: {len(bin_idx)} tuples ({npos} vuln, {nneg} pas_vuln) ; {n_amb} ambigu exclus\n")

    # --- métriques par juge + oracle, vs gold humain ---
    rows = []
    rows.append(_metrics("ORACLE (strict flag)",
                         [sample[i]["oracle"] for i in bin_idx], gold_bin))
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

    # --- angle mort de l'oracle : gold=vuln mais oracle=negatif ---
    blind = [i for i in bin_idx if gold_bin[bin_idx.index(i)] == 1 and not sample[i]["oracle"]]
    false_cap = [i for i in bin_idx if gold_bin[bin_idx.index(i)] == 0 and sample[i]["oracle"]]
    _p(f"\n--- Oracle vs gold humain ---")
    _p(f"angle mort (gold=vuln, oracle rate): {len(blind)}  ids={blind}")
    for i in blind:
        _p(f"   [{sample[i]['challenge']}] prompt: {str(sample[i]['prompt'])[:80]!r}")
    _p(f"fausses captures (gold!=vuln, oracle=succes): {len(false_cap)}  ids={false_cap}")

    # --- cas ambigu (fuites partielles) ---
    amb_ids = [i for i in range(N) if gold_lab[i] == "ambigu"]
    _p(f"\n--- {len(amb_ids)} cas 'ambigu' (zone grise fuite partielle) ---")
    for i in amb_ids:
        km = KEYMAP.get(str(i), {})
        npred = sum(km.get("predicted", {}).values())
        _p(f"   id={i} [{sample[i]['challenge']}] oracle={sample[i]['oracle']} "
           f"juges_succes={npred}/5")

    out = RESULTS / "exp2_gold_summary.json"
    out.write_text(json.dumps({"rows": rows, "n_amb": n_amb,
                               "blind_spot": blind, "false_capture": false_cap},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    _p(f"\nresume -> {out}")


if __name__ == "__main__":
    main()
