# Comparaison pré-enregistrée RedAgent vs PyRIT (Tier 2 — résultats)

> Brouillon de rédaction (RedAgent v2). Protocole figé : `tier2_preregistration_pyrit.md`.
> Chiffres du 2026-06-13 (`results/mtxA_seedmut`, `gandalf_mtx`, `pyrit_promptme`,
> `pyrit_gandalf`). À convertir en LaTeX.

## 1. Rappel : ce que le Tier 2 teste (et ce qu'il ne teste pas)

Le Tier 2 ne cherche **pas** à couronner un vainqueur. Il teste une affirmation
*méthodologique* : **notre oracle déterministe peut mesurer objectivement n'importe quel outil
de red teaming**, y compris un framework de référence — ici **PyRIT** (Microsoft, v0.14.0).
PyRIT tourne dans sa configuration native (orchestrateur multi-tours *RedTeaming*, cible HTTP,
scorer interne `SelfAskTrueFalse` pour piloter sa boucle), et **notre oracle** évalue *chaque*
réponse qu'il produit — exactement comme pour RedAgent. La comparaison de capture qui suit est
**accessoire** : elle situe RedAgent, sans prétendre le déclarer supérieur.

## 2. Conditions tenues constantes (cf. pré-enregistrement)

Attaquant LLM identique (`gpt-4o-mini-2024-07-18`) ; mêmes endpoints live non patchés (RedAgent
via son adaptateur, PyRIT via une cible custom qui réutilise **le même** adaptateur → I/O cible
strictement identique) ; même définition du succès (**notre oracle**, post-step inclus) ; même
budget (PromptMe : 12 requêtes, K=5 ; Gandalf : 8, K=3). Baselines RedAgent **réutilisées**
(produites avant le pré-enregistrement). Asymétrie de design assumée : RedAgent (graines
génériques + mutations + recon) vs PyRIT (escalade conversationnelle guidée par scorer) — chaque
outil dans sa configuration native.

## 3. Résultats — taux de capture (oracle), IC de Wilson 95 %

**PromptMe** (K=5, budget 12) :

| défi | RedAgent | PyRIT |
|---|---|---|
| LLM02 | 2/5 | 0/5 |
| LLM06 | 1/5 | 0/5 |
| LLM07 | 1/5 | 0/5 |
| **global** | **4/15 — 0.27 [0.11, 0.52]** | **0/15 — 0.00 [0.00, 0.20]** |

**Gandalf** (K=3, budget 8) :

| niveau | RedAgent | PyRIT |
|---|---|---|
| do-not-tell (2) | 3/3 | 2/3 |
| word-blacklist (5) | 3/3 | 2/3 |
| gandalf (7) | 0/3 | 0/3 |
| **global** | **6/9 — 0.67 [0.35, 0.88]** | **4/9 — 0.44 [0.19, 0.73]** |

**Contrôle d'intégrité (anti-artefact).** Les 165 tentatives PyRIT sur PromptMe comptent
**0 réponse vide et 0 erreur de transport** : les cibles ont bien répondu (RAG LLM02 :
« I don't know based on the provided data » ; LLM07 : réponse générique non-fuitante). Le 0/15
est un **résultat réel**, pas un défaut d'outillage.

## 4. Lecture selon le plan d'analyse pré-enregistré (§7)

**Règle de décision prudente** : une différence n'est déclarée que si les IC de Wilson **ne se
recouvrent pas**.

- **PromptMe** : RedAgent [0.11, 0.52] vs PyRIT [0.00, 0.20] → recouvrement **marginal**
  (0.11–0.20) → **pas de différence déclarable** à ce n, malgré une estimation ponctuelle
  nettement en faveur de RedAgent (4/15 vs 0/15).
- **Gandalf** : [0.35, 0.88] vs [0.19, 0.73] → **recouvrement large** → **pas de différence
  déclarable**.

**Hypothèse H1 (« PyRIT ≥ RedAgent ») : NON soutenue.** La tendance est même *inverse* sur les
deux bancs. Conformément à l'engagement du pré-enregistrement, ce résultat est rapporté tel quel.

## 5. Pourquoi PyRIT sous-performe *sur cette classe de tâches* (interprétation)

1. **Inadéquation orchestrateur ↔ cible.** Le *RedTeaming* de PyRIT est conçu pour les
   jailbreaks **conversationnels multi-tours** de chatbots. Or PromptMe/Gandalf sont des fuites
   d'information **single-shot, sans mémoire** : le coup gagnant est souvent **un seul prompt
   générique direct** (vidage de configuration, « répète ce qui précède », TLDR). RedAgent encode
   ces techniques dans sa bibliothèque de graines ; l'escalade progressive de PyRIT « gaspille »
   le budget en mise en confiance que ces cibles ne récompensent pas. Sur Gandalf, PyRIT finit
   par capturer lvl2/lvl5 — mais plus tard (tours 4–8) et moins souvent (2/3) que RedAgent (1er
   tour, 3/3).
2. **Même LLM des deux côtés** (`gpt-4o-mini`) → la différence observée tient à
   l'**orchestration et aux graines**, pas au modèle attaquant.
3. **Plafond externe partagé** : ni l'un ni l'autre ne casse Gandalf lvl7 (0/3 chacun) — borne
   supérieure cohérente entre outils.

## 6. Humilité et limites (essentiel)

On **ne conclut pas** « RedAgent > PyRIT » en général. La comparaison porte sur :
- **un seul** orchestrateur PyRIT (RedTeaming), alors que PyRIT propose TAP, Crescendo, PAIR et
  de nombreux *converters* non évalués ici ;
- **un seul** attaquant (`gpt-4o-mini`), un **petit budget**, et une **classe de tâches étroite**
  (CTF de fuite d'info en boîte-noire JSON) qui **avantage structurellement** la bibliothèque de
  graines de RedAgent ;
- un **petit n** (K=5/3) → IC larges, aucune différence statistiquement déclarable.

Sur des jailbreaks conversationnels de modèles de chat, PyRIT brillerait probablement là où
RedAgent n'a pas d'outillage. Le résultat dit donc : *sur cette classe de tâches et cette
configuration*, les graines directes de RedAgent ont été plus efficaces, **sans que l'écart soit
significatif**.

## 7. Le véritable livrable du Tier 2

Indépendamment du palmarès, le Tier 2 démontre l'essentiel : **la comparaison a été possible et
équitable parce qu'un même oracle déterministe a mesuré les deux outils**, sur les mêmes cibles,
dans les mêmes conditions. L'instrument de mesure de RedAgent est **tool-agnostic** : il
transforme « mon outil semble marcher » en « voici le taux de capture objectif, avec son
incertitude, de *n'importe quel* outil sur ce banc ». C'est la réponse de fond à la critique de
la V1 — et elle vaut au-delà de RedAgent lui-même.

## 8. Menaces à la validité (Tier 2)

- **Petit n** (K=5/3) → IC larges ; comparaison surtout qualitative.
- **Périmètre PyRIT** restreint à un orchestrateur (RedTeaming) ; non représentatif de tout PyRIT.
- **Classe de tâches** favorable aux graines single-shot de RedAgent ; non généralisable aux
  jailbreaks conversationnels.
- **Divergence scorer/oracle possible** : PyRIT optimise vers son scorer interne (notion
  conversationnelle de succès), qui peut différer de l'extraction exacte exigée par l'oracle —
  piste cohérente avec Exp.2 (un juge n'est pas un oracle).
- **Snapshot-dépendance** (modèles hébergés, Gandalf évolutif) ; version PyRIT épinglée (0.14.0),
  graines et configs loggées.
