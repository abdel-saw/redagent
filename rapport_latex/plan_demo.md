# Plan de démo — captures d'écran pour le rapport

But : produire les figures `fig_ui_*`, `fig_report_html`, `fig_harness_metrics`,
`fig_gold_xlsx` (cf. `figures.md`). Deux parties : l'**outil interactif** (UI web,
côté V1 où réside l'interface) et le **harnais scientifique** (V2).

---

## Partie A — UI web (outil « produit », projet V1)

L'interface FastAPI/SSE/HTMX se trouve dans `C:\Users\HP\Desktop\redagent\`
(`app/main.py`, `docker-compose.yml`).

### A.1 Lancer l'application
- **Option Docker (recommandée)** : dans `...\redagent\`, exécuter
  `docker compose up` (toi, dans un terminal — l'app écoute sur `http://localhost:8000`).
- **Option locale** : créer un venv, `pip install -r requirements.txt`, puis
  `uvicorn app.main:app --port 8000`.
> À vérifier de ton côté (deps/Docker). Si l'UI ne démarre pas, on capture la
> partie B (harnais) qui suffit à illustrer la contribution scientifique.

### A.2 Captures à prendre
1. **`fig_ui_config.png`** — page d'accueil `/` : le formulaire de configuration
   d'un audit (URL cible, gabarit de corps, modèles attaquant/juge BYOK, plafond,
   sélection des modules OWASP, profondeur). *Légende : « Configuration d'un audit (BYOK, OWASP). »*
2. **`fig_ui_live.png`** — page `/run/<id>` pendant un audit : le flux SSE des
   tentatives, verdicts et findings qui s'affichent en direct.
   *Légende : « Suivi d'un audit en temps réel (SSE). »*
3. **`fig_report_html.png`** — le rapport HTML téléchargeable (haut de page :
   synthèse exécutive + un finding détaillé). *Légende : « Rapport d'audit généré. »*

> Pour une démo propre, cible un endpoint qui réagit (un des PromptMe, ou un
> petit assistant à toi). Masque toute clé API avant la capture.

---

## Partie B — Harnais scientifique (V2)

Dans `C:\Users\HP\Desktop\redagentV2\`. Les résultats sont déjà calculés ; ces
commandes ré-affichent des sorties propres à capturer.

### B.0 Prérequis (pour les smokes « live »)
Cibles PromptMe relancées (WSL) : `wsl -d Ubuntu -- bash -lc 'cd /root/promptme-lite && python3 _run_targets.py'`.
(Gandalf est en ligne, rien à lancer.)

### B.1 Preuve de l'oracle (12/12)
```
python -m experiments._smoke_oracle
```
*Capture → illustration de la section « Preuve de l'oracle ». Légende : « Validation de l'oracle : sensibilité + spécificité (12/12). »*

### B.2 Métriques Exp.1 (PromptMe) avec IC de Wilson
```
python -m experiments.metrics mtxA_seedmut
```
**`fig_harness_metrics.png`** — *Légende : « Exp.1 : taux de capture et intervalles de Wilson. »*

### B.3 Gold standard humain (PromptMe) — oracle + juges vs humain
```
python -m experiments._gold_analyze
```
*Capture du tableau (κ, IC) → section Exp.2.*

### B.4 Cible tierce Gandalf
```
python -m experiments._smoke_gandalf          # preuve cible+oracle (4/4)
python -m experiments.metrics gandalf_mtx      # Exp.1 sur Gandalf
python -m experiments._gold_analyze_gandalf    # gold humain Gandalf
```

### B.5 Comparaison à PyRIT (3 tableaux)
```
python -m experiments.metrics pyrit_promptme
python -m experiments.metrics pyrit_gandalf
python -m experiments.metrics mtxA_seedmut     # côté RedAgent (rappel)
```
*Capture côte à côte → section « Comparaison pré-enregistrée ».*

### B.6 Classeur d'adjudication anti-ancrage
Ouvrir `experiments\results\gandalf_exp2\gold_gandalf.xlsx`, onglet *adjudication*.
**`fig_gold_xlsx.png`** — *Légende : « Classeur d'adjudication humaine (oracle et verdicts masqués). »*

---

## Conseils de capture
- Terminal en thème clair, police lisible, fenêtre assez large (pas de retour à la ligne sauvage).
- Recadrer sur la zone utile ; PNG.
- **Masquer toute clé/API** sur chaque capture (UI comme terminal).
