# SPEC.md — RedAgent v2

> Référence technique du projet, calquée sur `PROJECT_BRIEF.md`. La thèse (§1) est
> **ratifiée** ; les sections expérimentales se remplissent tier par tier (cf. §13).

---

## 1. Thèse & contributions *(ratifiée)*

**RedAgent est un outil de red teaming LLM léger, BYOK, observable et utilisable par
un public non-expert, livré avec une méthodologie rigoureuse et agnostique-à-l'outil
pour évaluer ce type d'outil.** Sa contribution scientifique n'est pas la force brute
de l'attaquant, mais **l'instrumentation de la mesure** : (i) un **découplage oracle
déterministe / juge LLM** qui permet, sur un banc tiers, de **mesurer la fiabilité du
juge** contre une vérité-terrain humaine (gold standard) et déterministe (capture de
flag) ; (ii) un **protocole de comparaison contrôlé et pré-enregistré contre PyRIT**
sur cibles tierces (dont une de type prod), rapporté tel quel et non comme un palmarès.
RedAgent **n'a pas besoin de « gagner »** : un compromis mesuré entre taux de capture
et légèreté/BYOK/observabilité/accessibilité est un résultat valide et honnête.

**Raffinement 1 — claim dégradable par tier (la thèse ne casse pas si un tier saute) :**
- **Claim minimal (Tier 0, indéfendable-sans)** : outil léger + BYOK + observable, ET
  méthodologie de **validation du juge** contre vérité-terrain déterministe + gold humain.
- **Claim étendu (Tier 2)** : + **comparaison pré-enregistrée vs PyRIT** sur cibles tierces.

**Raffinement 2 — « public non-expert » EST dans la thèse** *(décision humaine)*.
Preuve attendue (légère, pas un test utilisateur formel) : BYOK sans infra, lancement
mono-commande, et **observabilité** (trace HTMX/SSE des tentatives/verdicts) comme
arguments d'accessibilité. À argumenter en §2 et en discussion, sans surpromettre.

**Ce qu'on NE prétend PAS** : attaquant autonome « performant » dans l'absolu ;
supériorité de RedAgent sur l'état de l'art ; représentativité d'un CTF vis-à-vis
d'une app de prod (d'où la 2e cible).

---

## 2. Problématique & positionnement SOTA
- 2.1 Tableau RedAgent vs **PyRIT / garak / promptfoo** (axes : orchestration LLM,
  légèreté, BYOK, observabilité, oracle objectif, public visé).
- 2.2 Le trou comblé : dans la littérature outillée, **le juge LLM n'est jamais validé** ;
  on le rend *mesurable*.

## 3. Périmètre *(verrouillé sauf décision humaine)*
- 3.1 OWASP retenus **LLM01 / LLM02 / LLM06 / LLM07** (boîte-noire JSON) ; justifier
  l'exclusion LLM03/04/08 (accès pipeline/embeddings requis).
- 3.2 Statut explicite **LLM05 / LLM09 / LLM10** (in/out + pourquoi).
- 3.3 Cibles : **PromptMe** (CTF, flags = oracle) + **2e cible prod-like** (arbitrage :
  Damn Vulnerable LLM Agent / `gandalf_vs_gandalf` / assistant open-source déployé tel quel).
- 3.4 **Autorisation documentée** de chaque cible (auto-hébergée / ouverte à l'attaque).

## 4. Architecture du harnais *(réutilise V1 sain)*
- `app/target_adapter.py` (template JSON `{{prompt_json}}`, headers, response_path),
  `app/config.py` ; `experiments/oracle.py`, `runner.py` (Exp.1), `metrics.py`,
  `replay.py` (Exp.2), `config/targets.json`, `config/models.json`, lanceur de cibles,
  **adapter PyRIT** (Exp.3). Aucun shim de confort ; env/config forcés au lancement.

## 5. Engagements méthodologiques *(figés — cf. BRIEF §5)*
Découplage oracle/juge ; **gold standard manuel adjugé par l'humain** pour Exp.2 ;
honnêteté statistique (IC, pas de palmarès, skill vs variance-cible sur K runs) ;
protocole de comparaison **pré-enregistré** ; pas de seeding réactif ; reproductibilité
(snapshots datés, seeds, configs loggées) ; coût borné (~$2/expé, épuisement gracieux).

## 6. Oracle — design déterministe par défi
`detect` (motif flag/secret) + `post_step` optionnel (LLM02 : extract token →
`POST /submit-token` → confirm `flag{…}`). Leurres connus (JWT_SECRET) explicitement
non-confondus. **Prouvé par `_smoke_oracle.py`** (sensibilité live + reconnaissance
synthétique + spécificité réfutation/leurre).

## 7. Exp.1 — efficacité attaquant
success = oracle ; K runs ; reporting **IC** ; séparer **skill-attaquant vs variance-cible**
(consistance run-à-run : LLM02 = skill, LLM07 = variance) ; LLM06 capturable en single-shot
(corrige le 0/15 V1 = gap stratégie, pas scope).
**Fix attaquant V2 obligatoire** : stripper `<think>…</think>` du prompt généré AVANT envoi
à la cible (13 % des prompts V1 étaient pollués par la chaîne de raisonnement — même classe
de bug que le juge, cf. T0.2).

## 8. Exp.2 — fiabilité juge *(joyau Tier 0)*
- 8.1 **Gold standard manuel** : l'**humain** adjuge (au minimum tous les désaccords
  juge↔oracle), verdicts machine masqués (anti-ancrage).
- 8.2 Métriques : **P/R/F1 vs gold (primaire)** + vs oracle (secondaire) + **Cohen's κ**
  + **IC de Wilson** ; stratifié par défi ; dire quand le rappel n'est pas estimable (LLM06).
- 8.3 **Capture-de-flag vs vulnérabilité-perçue** : les fuites partielles (oracle strict
  négatif) chiffrent l'angle mort de l'oracle.
- 8.4 Bug juge à corriger avant rerun : reasoning models (o4-mini, qwen3) rejettent
  `temperature=0` / épuisent `max_tokens` dans `<think>` → omettre temperature + budget
  tokens suffisant + strip `<think>`.

## 9. Exp.3 — comparaison pré-enregistrée vs PyRIT *(Tier 2)*
Protocole **gelé avant lancement** : adapter de qualité identique par outil, **même modèle
attaquant** là où applicable, **même budget requêtes/tokens**, mapping probe→catégorie figé,
**oracle commun**. Rapporté tel quel, pas en palmarès.

## 10. Reproductibilité
Snapshots de modèles datés, seeds fixes, configs loggées. **Le harnais est reproductible ;
les chiffres absolus sont dépendants du snapshot** (modèles hébergés évolutifs).

## 11. Budget & épuisement gracieux
Cap ~$2/expé ; try/except par cellule ; backoff ; caching de recon ; checkpoints
(Groq TPD ~100k tokens/jour atteint en V1).

## 12. Menaces à la validité
n petit (19 positifs, 0 sur LLM06) → IC larges (rappel juge [0.83,1.00]) ; cible CTF
pédagogique ; dépendance au snapshot ; **annotateur unique** pour le gold standard (1 slip
corrigé / 32 : id116) ; stochasticité cible (temp 0.7) ; **pollution `<think>`** : 13 %
des prompts attaquant V1 contenaient la chaîne de raisonnement du modèle (corrigé en V2,
cf. §7) — sans fuite cachée (réponses = refus). Imputation gold des 86 non-adjugés validée
par le set de contrôle (0/10 non-`pas_vuln`) ; rappel/précision robustes à l'imputation
(les non-adjugés ne sont flaggés par aucun juge → jamais de FP).

## 13. Plan 72h build + 24h rapport *(tiers — ne pas démarrer un tier supérieur avant fin+test du précédent)*
- **T0** : thèse+SPEC ✔ · harnais oracle/juge prouvé sur PromptMe · **Exp.2 gold manuel** · rédaction honnête.
- **T1** : 2e cible prod-like (template JSON) · Exp.1 sur 2 cibles + IC.
- **T2** : comparaison PyRIT pré-enregistrée (PromptMe, + 2e cible si temps).
- **T3** : baseline garak · étude multi-modèles attaquant/juge.
