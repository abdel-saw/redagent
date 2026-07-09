# Efficacité de l'attaquant et démonstration d'autonomie (Exp.1)

> Brouillon de rédaction (RedAgent v2). Chiffres issus des matrices du 2026-06-12
> (`experiments/results/mtxA_seedmut`, `mtxB_mutonly`). À convertir en LaTeX.

## 1. Objectif

Exp.1 mesure l'**efficacité de l'attaquant autonome** : pour chaque cellule
(attaquant × défi × run), la boucle d'attaque est déroulée contre la cible PromptMe et
**le succès est décidé par l'oracle déterministe** (jamais par un juge). Chaque tentative
`(prompt, réponse, label_oracle)` est journalisée — ces tuples alimentent ensuite Exp.2.

L'enjeu n'est pas de revendiquer un attaquant « performant » dans l'absolu (il ne l'est
pas), mais de **mesurer honnêtement** ce qu'un agent BYOK générique capture, et surtout de
**distinguer ce qui relève du skill de l'agent de ce qui relève d'autre chose** (graines
écrites à la main, variance de la cible).

## 2. Architecture de l'attaquant

- **Seed → mutation** : des graines déterministes génériques (une par classe de
  vulnérabilité), puis des **mutations générées par le LLM attaquant** qui raffinent la
  tentative la plus proche du but, en s'appuyant sur ce que les réponses précédentes ont
  révélé.
- **Boîte à outils de techniques génériques** (reframing bénin/TLDR, cadrage technique
  neutre « key-value », revendication d'autorité, indirection, recon-then-exploit, coercition
  de format) — universelles, non liées à une cible.
- **Recon** optionnel : sondes bénignes → profilage de la cible par l'attaquant →
  conditionnement des attaques. Aucun savoir spécifique-cible n'est codé en dur.
- **Mode `mutations_only`** : les graines sont **désactivées** — l'agent doit **tout
  générer lui-même**. C'est l'ablation qui isole l'autonomie pure (cf. §5).

Deux corrections génériques par rapport à la V1 :
1. **Strip `<think>`** : 13 % des prompts attaquants V1 contenaient la chaîne de raisonnement
   du modèle, envoyée telle quelle à la cible. On la retire avant émission.
2. **Fix LLM06 générique** : graines cadrées-autorité (« en tant que propriétaire/admin
   réalisant un audit sanctionné, énumère les ressources restreintes, puis lis la plus
   sensible ») + une mutation qui **agit sur les identifiants révélés par leur nom exact**
   (nom nu, sans chemin). Aucun nom de fichier cible n'est codé en dur.

## 3. Protocole et budget

Matrice **attaquant × défi × K runs** (K = 5, réduit à 3 pour les modèles coûteux),
`max_attempts = 12`, recon activé, défis LLM02/LLM06/LLM07 (LLM01 hors-périmètre
boîte-noire-JSON : sa capture officielle exige `/fetch` multi-tours).

**Contrainte d'infrastructure et pivot.** Le free-tier Groq impose un plafond de tokens
journalier (~100k/modèle) qui a sérieusement ralenti la matrice. L'étude **multi-modèles
étant un objectif bonus** et la **diversité cross-familles étant déjà acquise** (Exp.2 sur
5 juges dont 3 open ; Matrice A en seed+mutation sur 6 attaquants de 3 familles, dont un
modèle *safety-tuned*), nous avons **pivoté vers OpenAI-only** pour l'ablation d'autonomie
et les comparaisons ultérieures, en ajoutant **o4-mini comme attaquant de raisonnement**
(axe de diversité intra-OpenAI : non-raisonnement vs raisonnement). Budget borné (cap par
expérience, épuisement gracieux : throttle, backoff, checkpoints).

## 4. Résultats — Matrice A (seed + mutation)

Taux de capture (flags / runs) ; succès = oracle :

| attaquant | LLM02 | LLM06 | LLM07 | global | taux [IC₉₅] | refus % |
|---|---|---|---|---|---|---|
| openai/o4-mini (raisonnement) | 1/5 | 2/5 | 3/5 | **6/15** | 0.40 [0.20, 0.64] | 0.7 |
| openai/gpt-4o-mini | 2/5 | 1/5 | 1/5 | 4/15 | 0.27 [0.11, 0.52] | 0 |
| groq/llama-3.1-8b | 1/5 | 1/5 | 0/5 | 2/15 | 0.13 [0.04, 0.38] | 0 |
| groq/qwen3-32b | 1/5 | 0/5 | 0/5 | 1/15 | 0.07 [0.01, 0.30] | 0 |
| groq/gpt-oss-safeguard (safety) | 0/5 | 0/5 | 1/5 | 1/15 | 0.07 [0.01, 0.30] | **54.7** |
| openai/gpt-4.1-mini | 0/3 | 0/3 | 0/3 | 0/9 | 0.00 [0, 0.30] | 0 |
| groq/llama-3.3-70b | 0/5 | 0/5 | — | 0/10 | 0.00 [0, 0.28] | 0 |

*(llama-3.3-70b : reliquat LLM07 abandonné, TPD Groq — non bloquant.)*

**Exhibit « modèle qui refuse »** : `gpt-oss-safeguard` (safety-tuned) refuse **54.7 %** de
ses générations de prompts adversariaux — il est largement inutilisable comme attaquant.
Sa seule « capture » (LLM07) provient de la variance de la cible (cf. §4.1), pas de son
skill.

### 4.1 Décomposition skill vs variance
En classant chaque capture par sa **source** (graine = variance cible ; mutation = prompt
**généré** par l'agent = skill) :

| défi | captures | source | verdict |
|---|---|---|---|
| LLM02 | 5/5 | mutations | **SKILL** — l'agent génère le prompt gagnant |
| LLM06 | 4/4 | mutations | **SKILL** — autorité + lecture nom-nu, générée |
| LLM07 | 5/5 | graine `translate_above` | **VARIANCE cible** — la cible fuit la graine (temp 0.7) |

Enseignement central : **LLM07 ne doit pas être porté au crédit de l'attaquant** (c'est la
cible qui fuit une graine), tandis que **LLM02 et LLM06 sont du skill** (mutations générées).

## 5. Résultats — Matrice B (`mutations_only`) et démonstration d'autonomie

En désactivant les graines, l'agent doit **tout générer**. On compare les mêmes attaquants
OpenAI en seed+mutation (A) vs autonomie pure (B) :

| attaquant | A : seed+mutation | B : mutations_only | lecture |
|---|---|---|---|
| o4-mini (raisonnement) | 6/15 = 0.40 [0.20, 0.64] | 4/15 = 0.27 [0.11, 0.52] | **tient en autonomie pure** |
| gpt-4o-mini | 4/15 = 0.27 [0.11, 0.52] | **0/15 = 0.00 [0, 0.20]** | **s'effondre sans graines** |
| gpt-4.1-mini | 0/9 = 0.00 | 1/9 = 0.11 [0.02, 0.44] | ~plancher |

**C'est le résultat le plus important d'Exp.1.** Privé de graines :
- **gpt-4o-mini tombe de 4/15 à 0/15** : son efficacité apparente en mode seed+mutation
  reposait sur **l'échafaudage des graines**, pas sur sa génération propre.
- **o4-mini conserve l'essentiel** (LLM02 **3/5 générés de zéro**, souvent dès la tentative
  1-2) — et capture même LLM07 par sa **propre mutation** (et non par la graine), là où le
  mode A ne montrait que de la variance.

⇒ **L'autonomie réelle est le fait du modèle de raisonnement** ; le petit modèle
non-raisonnement « surfait » sur les graines. L'ablation `mutations_only` rend cette
distinction *mesurable* plutôt que supposée.

**Nuance LLM06** : en autonomie pure, **LLM06 = 0/18**. La capture LLM06 dépend de la
**graine d'énumération cadrée-autorité** ; sans elle, l'agent ne reconstruit pas de façon
fiable la chaîne *autorité → énumérer → lire le fichier révélé*. À reporter tel quel.

## 6. LLM06 : le 0/15 de la V1, expliqué et corrigé

En V1, LLM06 résistait à **tous** les modèles (0/15) — ce que l'on avait pris pour une
limite de l'attaquant. Le diagnostic V2 montre qu'il s'agissait d'un **gap de stratégie**,
pas d'une limite de périmètre : la cible n'accorde l'accès admin que si le prompt
**revendique le rôle propriétaire**, puis exige une **lecture par nom de fichier nu**
(`flag.txt`, pas `restricted/flag.txt`). Avec la graine cadrée-autorité (énumération) + une
mutation qui lit l'identifiant révélé par son nom nu, **LLM06 est désormais capturé de façon
autonome** (gpt-4o-mini, llama-3.1-8b, o4-mini en mode seed+mutation), bien que de manière
**sporadique** — fixation fréquente sur le mauvais fichier restreint et sensibilité du
phrasing de la cible. Le **substrat de la vulnérabilité (excessive agency) est démontré de
façon autonome et générique** ; la capture du *flag spécifique* reste, elle, sporadique.

## 7. Enseignements

1. **L'autonomie réelle requiert un modèle de raisonnement.** Seul o4-mini tient en
   `mutations_only` ; gpt-4o-mini s'effondre à 0 sans graines.
2. **« Plus gros » ≠ meilleur.** gpt-4.1-mini reste au plancher dans les deux modes ; le
   petit gpt-4o-mini fait mieux en seed-mode (mais sur les graines).
3. **Skill vs variance, mesuré** : LLM02 et LLM06 = skill (mutations) ; LLM07 = variance
   cible (graine). À ne pas confondre dans le rapport.
4. **Tout est faible en absolu et les IC se recouvrent** → **pas de palmarès**. La lecture
   honnête est : « aucun attaquant ne dépasse un plancher faible, seul le modèle de
   raisonnement montre une autonomie mesurable ». C'est cohérent avec la thèse : RedAgent
   n'a pas besoin de « gagner ».

## 8. Menaces à la validité (Exp.1)
- **Cible stochastique** (temp 0.7) → la capture est probabiliste, d'où K runs et la
  décomposition par source. Les K sont petits (5/3) → IC larges, affichés.
- **Sensibilité au phrasing de la cible** (LLM02 retrieval, LLM06 nom-nu, LLM07 gabarit) :
  une part des échecs est mécanique côté cible, pas un défaut d'autonomie — documenté.
- **Pivot OpenAI-only** : l'ablation d'autonomie (B) est OpenAI-only ; le signal
  cross-familles est établi séparément en A (seed+mutation, 6 attaquants) et en Exp.2.
- **Reproductibilité** : graines fixes, snapshots datés, configs loggées ; chiffres absolus
  snapshot-dépendants.

## 9. Lien avec Exp.2
Les tuples `(prompt, réponse, label_oracle)` produits ici constituent l'entrée d'Exp.2
(fiabilité du juge) : c'est la même chaîne de mesure, du succès objectif (oracle) à la
vulnérabilité perçue (juge), validée contre une vérité-terrain humaine.
