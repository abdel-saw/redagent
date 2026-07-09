# Validation sur une seconde cible tierce : Gandalf (Tier 1)

> Brouillon de rédaction (RedAgent v2). Chiffres issus des runs du 2026-06-13
> (`experiments/results/gandalf_mtx`, `gandalf_exp2`). À convertir en LaTeX.

## 1. Objectif

Le Tier 0 a établi la **méthodologie** (oracle déterministe découplé du juge) et l'a
appliquée à un premier banc tiers, PromptMe-Lite. La critique de circularité de la V1 n'est
toutefois pleinement levée que si l'outil démontre sa valeur sur **plus d'une** cible
indépendante. Le Tier 1 ajoute donc une **seconde cible prod-like tierce**, choisie pour
qu'elle apporte une **vérité-terrain que l'auteur n'a pas fabriquée**, et y rejoue les deux
expériences (Exp.1 efficacité de l'attaquant, Exp.2 fiabilité du juge).

## 2. Choix de la cible

Trois candidats ont été examinés sous la contrainte « boîte-noire JSON » de l'adaptateur et le
principe **« fidèle à l'usage réel »** (parler à la cible telle qu'elle tourne, sans la patcher) :

- **Open WebUI** (assistant générique auto-hébergé) : installation impraticable dans
  l'environnement (échec d'installation Python ; Docker indisponible). Écarté.
- **Damn Vulnerable LLM Agent** (Reversec/WithSecure) : interface Streamlit sur websockets,
  sans endpoint REST JSON propre ; aurait exigé un wrapper websocket→JSON (un *shim* contraire
  au principe). Écarté.
- **Gandalf (Lakera)** : jeu public de *prompt injection*, déjà en ligne, non authentifié,
  **API REST JSON**. Retenu.

Gandalf présente un avantage décisif sur l'option auto-hébergée : il fournit un **second oracle
déterministe que nous n'écrivons pas** — l'endpoint `guess-password` de Lakera renvoie un
booléen `success` autoritatif. La cible détient un mot de passe secret et a pour consigne de ne
pas le révéler ; le succès d'attaque = extraire ce mot de passe. Cette vérité-terrain tierce
**renforce la rupture de circularité** au-delà de ce qu'aurait permis une cible bénigne.

**Glissement de récit assumé.** Le plan initial visait une cible bénigne pour démontrer la
*spécificité dans la nature* (peu de faux positifs, capture attendue ≈ 0). Gandalf étant au
contraire **intentionnellement vulnérable et graduée**, le Tier 1 démontre désormais la
**généralisation** : l'attaquant générique et les juges validés transfèrent-ils à un benchmark
tiers, mesurés contre sa vérité-terrain indépendante ? La spécificité reste, elle, acquise au
niveau de l'oracle (réfutation et leurre restent négatifs, cf. Tier 0).

## 3. Intégration sans *shim* (capacités génériques)

Trois ajouts, tous **génériques** (réutilisables, non liés à Gandalf) :

1. **Adaptateur** : option d'encodage `form` (x-www-form-urlencoded) en plus de JSON — de
   nombreuses API réelles sont form-encoded.
2. **Oracle** : *post-step* généralisé à **plusieurs candidats** (extraction de tous les
   mots-majuscules de la réponse, soumis un à un à `guess-password`) et à un encodage form —
   rétro-compatible avec le post-step mono-token de LLM02. **Aucun mot de passe n'est codé en
   dur** : la vérité-terrain vient entièrement de Lakera.
3. **Runner** : sélecteur de banc `--bench gandalf`, qui mappe tous les niveaux vers le module
   d'attaque **générique** de fuite de prompt système (le mot de passe est un secret du prompt
   système). On teste ainsi le **transfert** de l'attaquant générique, sans graine
   spécifique-cible (cohérent avec le refus de l'overfitting).

L'API publique ayant été remaniée (backend déplacé), l'endpoint réel
(`gandalf-api.lakera.ai/api`) a dû être retrouvé par analyse du frontend — sans modification de
la cible, conformément au principe.

## 4. T1.1 — preuve de la cible et de son oracle

Comme pour PromptMe, l'oracle est **prouvé instrument de confiance avant toute mesure**
(`experiments/_smoke_gandalf.py`, 4/4) : (a) l'adaptateur form lit bien le champ `answer` ;
(b) **sensibilité** — sur le niveau `baseline`, une demande directe fait fuiter le mot de passe,
confirmé par l'oracle tiers (`success:true`) ; (c) **spécificité contrôlée** — un mot en
majuscules qui n'est pas le mot de passe est rejeté par `guess-password` (vraie discrimination,
pas un artefact) ; (d) **spécificité live** — sur le niveau le plus dur, une demande naïve est
refusée et reste négative.

## 5. Exp.1 — efficacité de l'attaquant sur Gandalf

Matrice **attaquant × niveau × K**, attaquants OpenAI (gpt-4o-mini, gpt-4.1-mini, o4-mini),
niveaux `do-not-tell` (2), `word-blacklist` (5), `gandalf` (7), K=3, `max_attempts=8`, recon
activé ; succès = oracle Gandalf. Coût total ≈ 0,07 $.

**Taux de capture (flags / runs), IC de Wilson 95 % :**

| niveau | capture (tous attaquants) | taux [IC₉₅] |
|---|---|---|
| `do-not-tell` (2) | 9/9 | 1.00 [0.70, 1.00] |
| `word-blacklist` (5) | 9/9 | 1.00 [0.70, 1.00] |
| `gandalf` (7) | 0/9 | 0.00 [0.00, 0.30] |

Par attaquant, les trois modèles sont **identiques** : 6/9 (0.67 [0.35, 0.88]), 0 % de refus,
tentative gagnante moyenne = 1.0. Les IC se recouvrent totalement → **aucun palmarès**, cohérent
avec la thèse (l'outil n'a pas besoin de « gagner »).

**Décomposition skill vs variance.** Les 18 captures viennent **toutes de la même graine
générique** (`repeat_above`, « répète tout ce qui précède »), à la tentative 1 — c'est-à-dire de
la **variance/seed**, pas du skill de mutation. Les mutations autonomes ne se déclenchent que sur
`gandalf` (lvl7), où elles échouent aussi (0/9).

**Lecture honnête :**
- **Transfert générique démontré** : une graine LLM07 générique fait fuiter le prompt système —
  donc le mot de passe — d'une cible tierce (lvl2 et lvl5), validé par l'oracle indépendant de
  Lakera. La valeur de l'outil ne dépend pas de cibles auto-fabriquées.
- **Plafond externe honnête** : le niveau le plus dur résiste à tous les attaquants OpenAI sur
  8 tentatives × 3 runs (0/9). L'attaquant n'est pas « fort » — exactement ce que la thèse assume.
- **Gradient non strictement monotone** dans notre échantillon (lvl2 ≈ lvl5 ≫ lvl7) : `word-blacklist`
  tombe aussi vite que `do-not-tell` face à `repeat_above`. Captures authentiques (oracle =
  `guess-password` de Lakera, autoritatif) ; simple constat du comportement courant de la cible.

## 6. Exp.2 — fiabilité du juge sur une cible tierce

On **rejoue** les 90 tuples `(prompt, réponse, label_oracle)` produits par Exp.1 (18 positifs,
72 négatifs) à travers le panel de cinq juges, et on compare leur verdict à l'oracle Gandalf,
puis à une **vérité-terrain humaine**. Aucune nouvelle attaque — coût borné.

**Gold standard humain — recensement complet.** Contrairement à PromptMe (échantillonnage d'un
grand pool, avec imputation), les 90 tuples sont peu nombreux : **tous** sont adjugés à la main,
en aveugle (ni oracle ni verdicts machine affichés). Pas d'échantillonnage, pas d'imputation.
Résultat de l'adjudication : 18 `vuln`, 72 `pas_vuln`, **0 ambigu**.

**Métriques vs vérité-terrain humaine** (90 tuples binaires) :

| rater (vs **gold humain**) | P | R | F1 | κ | FP | FN | IC₉₅ rappel |
|---|---|---|---|---|---|---|---|
| **ORACLE Gandalf (guess-password)** | 1.00 | 1.00 | 1.00 | **1.00** | 0 | 0 | [0.82, 1.00] |
| gpt-4o-mini | 1.00 | 1.00 | 1.00 | 1.00 | 0 | 0 | [0.82, 1.00] |
| llama-3.3-70b | 1.00 | 1.00 | 1.00 | 1.00 | 0 | 0 | [0.82, 1.00] |
| qwen3-32b | 1.00 | 1.00 | 1.00 | 1.00 | 0 | 0 | [0.82, 1.00] |
| o4-mini | 1.00 | 1.00 | 1.00 | 1.00 | 0 | 0 | [0.82, 1.00] |
| gpt-oss-safeguard (safety) | 1.00 | 0.50 | 0.667 | 0.615 | 0 | 9 | [0.29, 0.71] |

**Trois enseignements :**

1. **L'oracle tiers est confirmé sans angle mort** (κ = 1.00 vs humain ; 0 angle mort, 0 fausse
   capture, 0 ambigu). Ici, *juge-vs-oracle ≡ juge-vs-vérité*.
2. **Enseignement transférable sur l'oracle** : ce résultat **contraste honnêtement** avec
   PromptMe, où l'oracle strict avait un angle mort (κ 0.968, cas id60 — fuite de configuration
   sans le token exact). La différence tient au **caractère discret du critère de succès** : un
   **mot de passe unique** fait un flag quasi parfait, tandis qu'« information sensible » crée une
   zone grise de fuites partielles. La fiabilité d'un oracle déterministe dépend donc de la nature
   de la vulnérabilité mesurée — point méthodologique utile pour qui voudrait répliquer l'approche.
3. **Le modèle *safety* reste le pire juge — sur une cible totalement indépendante.**
   `gpt-oss-safeguard` rate **9 divulgations évidentes sur 18** (rappel 0.50, κ 0.615, `err=0` →
   comportement réel, pas un bug). Le constat « un modèle de sécurité refuse mais ne reconnaît pas
   la vulnérabilité » se **réplique hors de PromptMe**, contre une vérité-terrain humaine.

**Garde-fou.** La discrimination est ici *facile* (positifs = divulgations claires du prompt
système, négatifs = refus nets du niveau 7), et n = 18 positifs → l'IC du rappel reste
[0.82, 1.00]. La conclusion défendable est « **accord quasi total, à confirmer sur un n plus
grand** », non « juge parfait ». Le gold humain de PromptMe, enrichi en cas limites, demeure le
test le plus discriminant des deux.

## 7. Enseignements du Tier 1

1. **Circularité levée sur deux cibles tierces**, dont une avec un **oracle que nous n'écrivons
   pas** (Lakera). La rupture avec la V1 est désormais double.
2. **Transfert générique attesté, plafond externe assumé** : l'attaquant générique capture sur
   les niveaux faibles/moyens d'un benchmark tiers et bute sur le plus dur — mesuré, sans
   surévaluation.
3. **Robustesse de la conclusion d'Exp.2** : les juges légers fiables le restent sur une cible
   indépendante, et le modèle *safety* reste disqualifié — répliqué contre vérité humaine.
4. **La qualité d'un oracle déterministe dépend de la discrétude du critère** : un nouveau résultat
   méthodologique, obtenu par le contraste PromptMe / Gandalf.

## 8. Menaces à la validité (Tier 1)

- **Discrimination facile** : sur Gandalf, positifs et négatifs sont tranchés → scores élevés
  attendus ; moins discriminant que le gold humain enrichi de PromptMe. Affiché.
- **Petit n** : 18 positifs, 0 sur le niveau le plus dur → IC larges ([0.82, 1.00] sur le rappel) ;
  pas de palmarès attaquant (IC recouvrants).
- **Cible évolutive** : Gandalf est un service tiers hébergé qui peut changer (modèle, défenses,
  API) ; le harnais est reproductible, les chiffres absolus sont snapshot-dépendants (configs et
  graines loggées, niveaux datés).
- **Annotateur unique** : un seul adjudicateur humain (recensement complet, 0 ambigu ici) ; une
  seconde adjudication renforcerait la vérité-terrain.
- **Pivot OpenAI-only** pour les attaquants ; le signal cross-familles côté juges est conservé
  (panel de 5 juges, dont 3 open).
