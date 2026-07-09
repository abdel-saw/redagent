# PROJECT_BRIEF.md — RedAgent v2 (reconstruction sur bases rigoureuses)

> **Contrat de travail + charte projet à destination de Claude Code.**
> Lis ce document en entier. Puis applique strictement les *modalités de travail* (§6).
> Ta toute première action est décrite au §10 : **proposer, ne pas coder**.

---

## 0. Mode d'emploi de ce document
- Ceci est la référence unique du projet. En cas de doute, on revient ici.
- **Aucune ligne de code n'est écrite sans validation humaine préalable** (voir §6).
- **On ne passe pas à l'étape suivante tant que l'étape courante n'a pas été testée et prouvée fonctionnelle** devant l'humain.

---

## 1. Qui / contexte
- PFE cycle ingénieur, spécialité ingénierie informatique. Auteur : Abdel. En solo. Encadrant : Pr Dabounou.
- Sujet : **RedAgent** — agent autonome de red teaming pour l'audit de sécurité d'applications LLM (OWASP Top 10 for LLM Applications, édition 2025).
- Ce projet est une **reconstruction** ("détruire pour mieux reconstruire") informée par deux critiques successives. On garde ce qui marche, on rebâtit ce qui était faible.
- **Budget temps : 72h de réalisation + 24h de rédaction.** Très serré → la priorisation (§7) est non négociable.

---

## 2. Historique & les deux critiques qu'on répond
**Critique V1 :**
1. **Validation circulaire** — l'outil n'était testé que sur 3 cibles que l'auteur avait lui-même rendues vulnérables. Aucune valeur démontrée face à l'état de l'art.
2. **Juge LLM jamais validé** — tous les résultats reposaient sur un oracle (le juge) dont la fiabilité n'était pas mesurée.

**Acquis du Sprint 16 (à conserver) :**
- **Découplage oracle / juge** : oracle déterministe (capture de flag) vs juge LLM (vulnérabilité perçue). C'est la bonne idée centrale.
- Pivot vers **PromptMe** (CTF tiers) comme banc de validation → casse la circularité.
- Exp.1 (efficacité attaquants) + amorce Exp.2 (fiabilité juges).

**Faiblesses résiduelles surfacées (à corriger cette fois) :**
- **n minuscule** : Exp.2 ne repose que sur 18 positifs oracle (9 LLM02, 9 LLM07, **0 LLM06**) → P/R/F1 fragiles, rappel non mesurable sur LLM06.
- **Cible unique** : PromptMe est un CTF pédagogique, peu représentatif d'une app de prod → validité externe faible.
- **Attaquant faible en absolu** (meilleur 4/15, naïf 0) → la thèse "attaquant fort" est intenable.

---

## 3. Thèse reformulée — **À RATIFIER EN PREMIER avec l'humain**
- **ANCIENNE (indéfendable)** : « on a construit un attaquant autonome performant ».
- **NOUVELLE (défendable)** :
  > « On livre un outil de red teaming **léger, BYOK, observable**, ET une **méthodologie rigoureuse et agnostique à l'outil** pour évaluer ce type d'outil — démontrée par (i) la **mesure de fiabilité du juge** contre une vérité-terrain déterministe, et (ii) une **comparaison contrôlée et pré-enregistrée contre PyRIT** sur des cibles tierces, dont une de type prod. »
- La **colonne vertébrale scientifique = méthodologie + comparaison**, pas la force brute de l'attaquant.
- **Conséquence assumée : RedAgent n'a pas besoin de "gagner".** Un compromis mesuré (taux de capture vs légèreté / BYOK / observabilité) est un résultat valide et honnête.
- **Tâche d'ouverture** : critiquer/affiner cette thèse avec l'humain, puis l'inscrire en SPEC.md §1.

---

## 4. Périmètre (verrouillé sauf décision humaine contraire)
- **Catégories OWASP** : testables en boîte-noire JSON → **LLM01 / LLM02 / LLM06 / LLM07**. Reprendre la justification V1 d'exclusion de LLM03/04/08 (accès pipeline/embeddings requis). Statuer explicitement en SPEC sur LLM05/09/10 (dans le périmètre ou non, et pourquoi).
- **Cibles** :
  1. **PromptMe** (CTF, flags déterministes = oracle).
  2. **Une seconde cible tierce plus "prod"** (auto-hébergée ; candidats à arbitrer en SPEC : Damn Vulnerable LLM Agent, `gandalf_vs_gandalf`, ou un assistant open-source par défaut déployé tel quel). Justifier en quoi elle est "prod-like".
  - **Les deux doivent être autorisées** (auto-hébergées ou explicitement ouvertes à l'attaque). **Documenter l'autorisation de chaque cible** dans le rapport.
- **Configuration des cibles** : on garde le **template JSON paramétrable** (`{{prompt}}` / `{{prompt_json}}`, en-têtes libres, chemin pointé d'extraction). **Aucun shim de confort dans l'outil** : on force l'environnement/config au lancement (principe "fidèle à l'usage réel").
- **Comparateur** : **PyRIT** (pair orchestré par LLM). garak en option stretch (baseline catalogue statique).

---

## 5. Engagements méthodologiques (NON négociables — c'est là qu'on a échoué)
1. **Découplage oracle/juge conservé.** Oracle = détection déterministe du flag. Juge = verdict de vulnérabilité perçue.
2. **Gold standard manuel pour Exp.2.** Annoter **à la main** les tuples échantillonnés (au minimum tous les désaccords juge/oracle) pour obtenir une vraie vérité-terrain humaine. Reporter le juge en **P/R/F1 contre ce gold**, avec le flag-oracle en référence secondaire. Mettre en avant la distinction **capture-de-flag vs vulnérabilité-perçue** (fuites partielles classées négatives par l'oracle strict).
3. **Honnêteté statistique.** n petit → reporter des **intervalles de confiance**, ne jamais surinterpréter un classement, dire explicitement quand un écart est dans le bruit. **Séparer skill-attaquant et variance-cible** (cible à temp 0.7) en montrant la consistance sur K runs.
4. **Protocole de comparaison pré-enregistré.** Figer AVANT de lancer : qualité d'adapter identique pour chaque outil, **même modèle attaquant là où applicable**, **même budget de requêtes/tokens par outil**, mapping probe→catégorie figé, oracle commun. Écrire le protocole en SPEC et le geler. Ne **pas** présenter la comparaison comme un palmarès « RedAgent bat X » mais comme un protocole contrôlé dont on rapporte les résultats tels quels.
5. **Pas de seeding réactif/spécifique-cible** dans l'attaquant. Améliorations **génériques uniquement** (préserve la revendication d'autonomie).
6. **Reproductibilité.** Snapshots de modèles datés, seeds fixes, configs loggées. Dire honnêtement : **le harnais est reproductible ; les chiffres absolus sont dépendants du snapshot** (modèles hébergés évolutifs).
7. **Maîtrise du coût.** Budget cap par expérience (~$2). Épuisement gracieux (try/except par cellule, backoff, caching de recon, checkpoints).

---

## 6. Modalités de travail (le contrat de collaboration)
- **Rôles** : l'humain est **lead engineer + décideur** ; toi (Claude Code) es **pair engineer**. Boucle : **proposer → l'humain valide → coder → journaliser**.
- **Portes STOP-ET-VALIDE** : avant d'écrire le code d'une étape, présenter la conception et **attendre un "go" explicite**. Avant de passer à l'étape suivante, **lancer l'existant et prouver qu'il marche** (montrer la sortie de test).
- **Une étape à la fois.** Incréments petits et testables. Pas de gros commit big-bang.
- **journal.md** : chaque étape a une entrée — objectif, décisions + justification, livrables, plan de test + résultat, bugs + corrections. C'est à la fois la traçabilité et la matière première du rapport.
- **Ne pas sur-ingénier.** Réutiliser les internals V1 prouvés (FastAPI / LiteLLM / httpx / adapter / SQLite) là où ils sont sains ; **reconstruire le cadrage, le harnais d'expé et le rapport**. Ne **pas** réécrire du code qui marche par souci de pureté — le budget est de 72h.
- **Fidèle à l'usage réel** : ne jamais patcher la source de la cible pour faire passer une attaque ; forcer l'env/config au lancement et documenter la friction.

---

## 7. Budget temps & triage (72h build + 24h rapport) — **PROTÉGER LE CŒUR**
Très ambitieux. On protège un cœur minimal défendable ; le reste est du stretch avec lignes de coupe explicites.

- **TIER 0 — doit livrer (suffit à un PFE défendable à lui seul)** : thèse reformulée + SPEC ; harnais oracle/juge fonctionnel sur PromptMe ; **Exp.2 avec gold standard MANUEL** sur les tuples existants (consolide le résultat qui a coûté la V1) ; rédaction honnête.
- **TIER 1 — forte valeur** : seconde cible prod-like branchée via template JSON ; Exp.1 rejoué sur les deux cibles avec reporting des IC.
- **TIER 2 — le gain "valeur vs SOTA"** : comparaison PyRIT pré-enregistrée sur PromptMe (+ seconde cible si le temps le permet).
- **TIER 3 — bonus** : baseline statique garak ; étude multi-modèles attaquant/juge.

**Règle d'or** : ne jamais démarrer un tier supérieur tant qu'un tier inférieur n'est pas fini ET testé. À chaque porte, si le temps manque, **livrer le tier courant propre** plutôt que laisser deux tiers à moitié faits.

---

## 8. Pièges d'environnement connus (front-loadés pour ne pas les redécouvrir)
- **Windows / WSL** : `UnicodeEncodeError` cp1252 (forcer UTF-8) ; expansion de variables dans `wsl bash -lc` ; conversion de chemins MSYS ; jobs background qui meurent à la sortie du one-shot (gérer les process proprement).
- **Groq** : free-tier rate-limit + **TPD ~100k tokens/jour** — atteint en plein milieu de la matrice en V1. Cacher la recon, try/except par cellule, router la recon via le backoff, **checkpointer** pour qu'un crash ne perde pas le run.
- **Bizarreries PromptMe (documentées, NE PAS patcher la source)** :
  - LLM06 retombe sur Ollama si l'env n'est pas résolu → forcer `LLM_PROVIDER=openai` au lancement.
  - LLM07 renvoie du vide sur les prompts contenant `{}` (bug de template).
  - LLM02 : `JWT_SECRET` est un **leurre** → vrai flag = token + `POST /submit-token`.

---

## 9. Livrables
- **SPEC.md** : thèse, périmètre, positionnement SOTA (vs PyRIT/garak/promptfoo), protocole pré-enregistré, métriques.
- **Harnais** : `oracle.py`, `runner.py` (Exp.1), `metrics.py`, `replay.py` (Exp.2), `targets.json`, `models.json`, lanceur de cibles, **adapter PyRIT**.
- **journal.md** : continu.
- **Rapport (24h)** : structure calquée sur la SPEC ; mettre en avant méthodo + comparaison ; reporter les IC ; section limites honnête.

---

## 10. Ta première réponse à l'humain (ne code pas encore)
1. Confirme que tu as lu et compris ce brief.
2. Propose : (a) une thèse affinée en un paragraphe, (b) le squelette de SPEC.md, (c) la **première étape du Tier 0** et son test de validation.
3. Puis **STOP** : attends la validation explicite de l'humain avant d'écrire la moindre ligne de code.
