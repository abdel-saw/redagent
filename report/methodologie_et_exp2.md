# Méthodologie d'évaluation et fiabilité du juge (Exp.2)

> Brouillon de rédaction (RedAgent v2). Chiffres issus des runs du 2026-06-11/12
> (`experiments/results/`). À convertir en LaTeX pour le rapport final.

## 1. Problématique et critique de la première version

L'objectif de RedAgent est un outil de red teaming d'applications LLM **léger, BYOK,
observable et utilisable par un public non expert**, tout en restant **effectif**. La
première version (V1) a fait l'objet de deux critiques méthodologiques majeures, que
cette version corrige frontalement :

1. **Validation circulaire** — l'outil n'était évalué que sur trois cibles que l'auteur
   avait lui-même rendues vulnérables. Aucune valeur n'était démontrée face à une
   référence indépendante.
2. **Juge LLM jamais validé** — tous les résultats reposaient sur le verdict d'un juge
   LLM dont la fiabilité n'avait jamais été mesurée. Le juge était l'oracle implicite,
   sans contrôle.

La contribution scientifique de cette version n'est donc pas la performance brute de
l'attaquant, mais **l'instrumentation de la mesure** : rendre le succès d'attaque
*objectivement* décidable, et rendre le juge LLM *mesurable*.

## 2. Contribution méthodologique : le découplage oracle / juge

Nous séparons strictement deux notions habituellement confondues :

- **L'oracle** — détection **déterministe** de la capture (un motif de flag/secret connu
  dans la réponse de la cible, éventuellement confirmé par une étape de soumission). Il
  ne dépend d'aucun LLM ; il est reproductible et constitue une **vérité-terrain
  objective** du succès d'attaque.
- **Le juge** — verdict d'un LLM (« la réponse exhibe-t-elle la vulnérabilité ? »). C'est
  l'instrument *générique* utilisable sur une cible **sans flag** ; mais sa fiabilité doit
  être établie, pas postulée.

Ce découplage répond directement aux deux critiques : la capture de flag casse la
circularité (vérité-terrain tierce), et il devient possible de **mesurer le juge contre
l'oracle**, puis contre une vérité-terrain humaine.

## 3. Banc de validation tiers : PromptMe

La validation s'appuie sur **PromptMe-Lite**, un CTF tiers (non produit par l'auteur)
exposant des défis OWASP-LLM en boîte noire JSON, dont les **flags servent d'oracle
déterministe**. Quatre défis sont dans le périmètre boîte-noire-JSON : LLM01 (prompt
injection), LLM02 (divulgation d'information sensible), LLM06 (excessive agency),
LLM07 (fuite de system prompt). L'outil parle à la cible **telle qu'elle tourne**, via un
adaptateur HTTP paramétrable (gabarit JSON), sans jamais patcher la cible (principe
« fidèle à l'usage réel »).

L'oracle a été **prouvé instrument de confiance** avant toute mesure
(`experiments/_smoke_oracle.py`, 12/12) : sensibilité (déclenche sur les payloads
connus-bons des writeups officiels, via le vrai adaptateur), reconnaissance synthétique
des quatre flags, et **spécificité** (reste négatif sur une réfutation explicite et sur le
leurre `JWT_SECRET` — qu'il ne confond pas avec le vrai token).

## 4. Factorisation Exp.1 / Exp.2

- **Exp.1 — efficacité de l'attaquant.** Pour chaque cellule (attaquant × défi × run), la
  boucle seed→mutation est déroulée contre la cible ; **le succès est décidé par
  l'oracle**, jamais par un juge. Chaque tentative `(prompt, réponse, label_oracle)` est
  journalisée.
- **Exp.2 — fiabilité du juge.** On **rejoue** les tuples loggés par Exp.1 à travers un
  panel de juges et on compare leur verdict au label de l'oracle, puis à une vérité-terrain
  **humaine**. Aucune nouvelle attaque n'est lancée → coût borné.

Cette factorisation évite la contamination : l'attaquant est évalué sur un succès
objectif, le juge est évalué séparément sur sa capacité à reproduire ce jugement.

## 5. Exp.2 — protocole

### 5.1 Panel de juges
Cinq juges, couvrant trois familles et trois régimes : `gpt-4o-mini` et `gpt-4.1-mini`
(OpenAI, non-raisonnement), `o4-mini` (OpenAI, raisonnement), `llama-3.3-70b` et
`qwen3-32b` (open, dont un à raisonnement), et `gpt-oss-safeguard-20b` (open,
*safety-tuned* — candidat « naturel » au rôle de juge de sécurité). Le juge reçoit
uniquement `(titre d'attaque, critère générique, prompt, réponse)` ; il n'a **pas** accès
au flag ni à l'oracle.

> **Remarque d'ingénierie (rigueur).** Une première exécution donnait `o4-mini` et
> `qwen3-32b` à des scores nuls. Le diagnostic a montré une cause purement **mécanique** :
> les modèles à raisonnement rejettent `temperature=0` et/ou épuisent le budget de tokens
> dans leur chaîne `<think>…</think>` avant d'émettre le verdict JSON. Après correction
> (ne pas forcer la température, élargir le budget de tokens, retirer `<think>`), les deux
> modèles produisent des verdicts valides. Enseignement reportable : **un juge « nul »
> peut n'être qu'un défaut d'intégration** — d'où le suivi explicite d'un compteur d'erreurs.

### 5.2 Gold standard humain (vérité-terrain)
L'oracle strict (flag exact) est lui-même une vérité-terrain **imparfaite** : il manque les
**fuites partielles**. Mesurer le juge *uniquement* contre l'oracle reviendrait à mesurer
un « accord avec un oracle biaisé », pas la justesse du juge. Nous construisons donc une
**vérité-terrain humaine** :

- **Échantillon** : 118 tuples (tous les positifs oracle, rares ; + un échantillon de
  négatifs, graine fixe), à coût maîtrisé pour le juge le plus cher.
- **Adjudication humaine anti-ancrage** : l'humain (l'auteur) tranche un classeur ne
  montrant **que** `défi + critère + prompt + réponse` — **ni l'oracle ni les verdicts
  machine** ne sont affichés. Les cas adjugés couvrent tous les positifs oracle, tous les
  désaccords juge↔oracle, et un set de contrôle de négatifs « faciles ».
- **Vérité-terrain complète** : labels humains pour les tuples adjugés ; imputation
  `pas_vuln` pour les non-adjugés (négatifs oracle ET unanimement négatifs côté juges).
  Cette imputation est **validée par le set de contrôle** (0/10 contrôles non-`pas_vuln`),
  et elle ne peut jamais créer de faux positif (les non-adjugés ne sont flaggés par aucun
  juge) → **rappel et précision robustes à l'imputation**.
- **C'est l'humain qui adjuge, pas un LLM** — sans quoi on recréerait la circularité que
  l'on combat.

### 5.3 Métriques
Pour chaque juge **et pour l'oracle lui-même** (traité comme un « rater »), vs gold humain
(primaire) et vs oracle (secondaire) : précision, rappel, F1, exactitude, **coefficient κ
de Cohen** (accord inter-annotateurs, métrique adaptée à une étude d'accord plutôt qu'à un
palmarès), et **intervalle de confiance de Wilson à 95 %** sur précision et rappel. Les
cas jugés *ambigus* par l'humain (fuites partielles) sont reportés à part et exclus du
binaire.

## 6. Résultats Exp.2

### 6.1 Juge vs oracle (accord automatique)
Sur 118 tuples (18 positifs oracle, 100 négatifs) :

| juge | P | R | F1 | FP | FN |
|---|---|---|---|---|---|
| gpt-4o-mini | 0.90 | 1.00 | 0.947 | 2 | 0 |
| llama-3.3-70b | 0.90 | 1.00 | 0.947 | 2 | 0 |
| qwen3-32b | 0.944 | 0.944 | 0.944 | 1 | 1 |
| o4-mini | 0.857 | 1.00 | 0.923 | 3 | 0 |
| gpt-oss-safeguard | 0.857 | 0.333 | 0.48 | 1 | 12 |

Les « faux positifs » des juges vs l'oracle se révèlent, à l'examen, être en partie des
**vraies vulnérabilités que l'oracle strict a manquées** — ce qui motive le passage à la
vérité-terrain humaine.

### 6.2 Juge vs gold humain (vérité-terrain)
Après adjudication humaine — 117 tuples binaires (19 `vuln`, 98 `pas_vuln`) ; 1 cas
ambigu exclu :

| rater (vs **gold humain**) | P | R | F1 | acc | κ | FP | FN | IC₉₅ rappel |
|---|---|---|---|---|---|---|---|---|
| **ORACLE (flag strict)** | 1.00 | 0.947 | 0.973 | 0.991 | 0.968 | 0 | 1 | [0.75, 0.99] |
| gpt-4o-mini | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0 | 0 | [0.83, 1.00] |
| llama-3.3-70b | 0.95 | 1.00 | 0.974 | 0.991 | 0.969 | 1 | 0 | [0.83, 1.00] |
| o4-mini | 0.95 | 1.00 | 0.974 | 0.991 | 0.969 | 1 | 0 | [0.83, 1.00] |
| qwen3-32b | 1.00 | 0.947 | 0.973 | 0.991 | 0.968 | 0 | 1 | [0.75, 0.99] |
| gpt-oss-safeguard | 1.00 | 0.368 | 0.538 | 0.897 | 0.494 | 0 | 12 | [0.19, 0.59] |

### 6.3 Trois enseignements
1. **Un juge LLM léger peut tenir lieu d'humain — et c'est mesuré.** Quatre juges sur cinq
   sont quasi indiscernables du jugement humain (κ ≥ 0.97). On se garde toutefois de
   surinterpréter : `gpt-4o-mini` atteint F1 = 1.0 *sur cet échantillon*, mais l'IC₉₅ du
   rappel reste [0.83, 1.00] et l'échantillon est petit et enrichi en cas difficiles — la
   conclusion défendable est « accord quasi total, à confirmer sur un n plus grand », non
   « juge parfait ».
2. **L'oracle déterministe lui-même n'est pas parfait** (κ 0.968 ; il manque un cas — une
   divulgation réelle de configuration sensible, identifiants de base de données, sans le
   token exact). Cela matérialise, *chiffres à l'appui*, la distinction
   **capture-de-flag ≠ vulnérabilité** : un juge bien calibré peut détecter une vraie
   vulnérabilité que l'oracle strict laisse passer.
3. **Le modèle *safety* est le pire juge.** `gpt-oss-safeguard`, pourtant *safety-tuned*,
   sous-déclare massivement (rappel 0.368, κ 0.494 ; il manque 12 vraies vulnérabilités sur
   19, `err=0` → comportement réel, pas un bug). Un modèle de sécurité n'est pas un bon
   détecteur de vulnérabilité : il refuse, mais ne reconnaît pas.

## 7. Menaces à la validité (assumées)
- **Petit n** : 19 positifs, **0 sur LLM06** → le rappel n'est pas estimable sur la
  catégorie la plus critique, et les IC sont larges. Affiché, pas masqué.
- **Annotateur unique** : un seul adjudicateur humain (1 erreur d'annotation détectée et
  corrigée, id 116 ; quelques zones grises). Une seconde adjudication renforcerait la
  vérité-terrain.
- **Pollution `<think>`** : 13 % des prompts attaquants de la V1 contenaient la chaîne de
  raisonnement du modèle (corrigé en V2) — sans fuite cachée (réponses = refus).
- **Imputation** : la vérité-terrain complète impute les non-adjugés ; imputation validée
  par le set de contrôle, et neutre pour précision/rappil (jamais de FP induit).
- **Dépendance au snapshot** : les modèles hébergés évoluent ; **le harnais est
  reproductible, les chiffres absolus sont snapshot-dépendants** (modèles datés, graines
  fixes, configs loggées).

## 8. Synthèse
La circularité est cassée (oracle tiers déterministe) et le juge est désormais *mesurable*
contre une vérité-terrain humaine. Le résultat n'est pas « notre juge est parfait » mais,
plus solide : **on sait lesquels des juges LLM sont fiables, à quel degré, et avec quelle
incertitude** — et l'on montre que l'oracle objectif lui-même a un angle mort. C'est la
réponse directe à la critique qui avait fragilisé la V1.
