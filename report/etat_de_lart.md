# Chapitre II — État de l'art

> Brouillon de rédaction (RedAgent v2, mémoire PFE). À relire/amender et convertir en LaTeX.
> Références (Auteur, année) à consolider en webographie ; URLs dans le texte à vérifier.

## 1. Taxonomie des vulnérabilités : OWASP Top 10 for LLM Applications (2025)

Le référentiel de fait pour la sécurité des applications LLM est le **OWASP Top 10 for LLM
Applications**, dont l'édition **2025** compte dix catégories :

| Code | Catégorie |
|---|---|
| LLM01 | Prompt Injection |
| LLM02 | Sensitive Information Disclosure |
| LLM03 | Supply Chain Vulnerabilities |
| LLM04 | Data and Model Poisoning |
| LLM05 | Improper Output Handling |
| LLM06 | Excessive Agency |
| LLM07 | System Prompt Leakage |
| LLM08 | Vector and Embedding Weaknesses |
| LLM09 | Misinformation |
| LLM10 | Unbounded Consumption |

L'édition 2025 introduit notamment **System Prompt Leakage (LLM07)**, **Vector and Embedding
Weaknesses (LLM08)** et **Unbounded Consumption (LLM10)**, et fusionne l'ancienne *Overreliance*
dans **Misinformation (LLM09)** (OWASP GenAI Security Project, 2025).

**Périmètre de RedAgent.** Le projet cible les catégories testables en **boîte noire, via une API
JSON** et dont le succès est **objectivement décidable** : **LLM01** (injection), **LLM02**
(divulgation d'information sensible), **LLM06** (agentivité excessive) et **LLM07** (fuite de
prompt système). Les catégories hors de ce cadre sont documentées comme telles : LLM03/04
(chaîne d'approvisionnement, empoisonnement — phase d'entraînement, non boîte-noire-runtime),
LLM05 (souvent côté intégration applicative), LLM08 (interne au RAG), LLM09 (jugement de
véracité, sans flag objectif), LLM10 (déni de service / consommation).

## 2. Méthodes d'attaque automatisées

On distingue deux grandes familles.

**Attaques à accès interne (white-box).** **GCG — Greedy Coordinate Gradient** (Zou et al., 2023)
optimise par **gradient** un suffixe adversarial qui maximise la probabilité d'une réponse
nuisible. Très efficace mais nécessite l'**accès aux poids** : inapplicable à une cible de
production en boîte noire.

**Attaques en boîte noire pilotées par LLM.** Elles utilisent un **LLM attaquant** qui raffine
itérativement ses prompts à partir des réponses de la cible, sans gradient :
- **PAIR — Prompt Automatic Iterative Refinement** (Chao et al., 2023) : boucle attaquant↔cible
  avec retour, en très peu de requêtes.
- **TAP — Tree of Attacks with Pruning** (Mehrotra et al., 2024) : étend PAIR à une **recherche
  arborescente** avec élagage des branches peu prometteuses.
- **Crescendo** (Russinovich et al., 2024) : attaque **multi-tours** qui escalade
  progressivement d'une demande bénigne vers l'objectif, exploitant la cohérence
  conversationnelle du modèle.

**Positionnement de RedAgent.** RedAgent opère en **boîte noire** et combine des **graines
génériques** (une par classe OWASP, encodant des techniques connues : vidage de configuration,
« répète ce qui précède », TLDR, cadrage d'autorité) avec des **mutations générées par un LLM
attaquant** qui raffinent la tentative la plus proche du but. C'est une approche **semi-autonome**
plus simple que TAP/PAIR — un choix assumé : l'objectif du projet n'est pas la sophistication de
l'attaque mais la **rigueur de la mesure** (cf. §5). Le mémoire est explicite sur cette limite.

## 3. Outils et frameworks de red teaming

| Outil | Éditeur | Profil |
|---|---|---|
| **PyRIT** | Microsoft | Framework extensible (orchestrateurs multi-tours RedTeaming/Crescendo/TAP/PAIR, converters, scorers, mémoire). Puissant, orienté ingénieur sécurité. |
| **garak** | NVIDIA (Derczynski et al.) | Scanner à *probes* (familles d'attaques prédéfinies : encodage, suffixes GCG, injection, hallucination de paquets…). |
| **promptfoo** | open source | Tests/évaluations de prompts et red teaming, orienté CI/CD. |
| **Giskard / GOAT** | Giskard | Red teaming automatisé multi-tours. |

Ces outils sont matures mais **lourds** pour un usage ponctuel ou non expert (installation,
configuration, abstractions nombreuses). **Le créneau de RedAgent** est complémentaire :
**léger, mono-conteneur, BYOK (clés en mémoire seulement), observable (SSE en direct), mappé
OWASP, pensé pour un public non expert**. RedAgent ne prétend pas remplacer PyRIT ou garak, mais
offrir un point d'entrée accessible — et surtout porter une **contribution de méthode**.

## 4. Bancs d'évaluation et vérité-terrain

Évaluer un outil de red teaming suppose une **vérité-terrain du succès**. Plusieurs ressources
existent :
- **Gandalf** (Lakera) : jeu public d'injection de prompt à niveaux, où l'extraction d'un mot de
  passe fournit une **vérité-terrain tierce** (un endpoint confirme le mot de passe deviné).
- **CTF OWASP-LLM** (type **PromptMe-Lite**) : défis à **flags** déterministes, par classe de
  vulnérabilité.
- **HarmBench, AdvBench** : jeux de prompts nuisibles pour mesurer des taux de jailbreak, mais
  dont le succès est souvent évalué… par un **classifieur/juge LLM**.

C'est précisément là qu'apparaît le **verrou méthodologique**.

## 5. Le verrou de la mesure et la contribution de ce travail

Deux écueils récurrents fragilisent les évaluations publiées et avaient fragilisé la V1 de ce
projet :
1. **Validation circulaire** : n'évaluer que sur des cibles construites par l'auteur lui-même.
2. **Juge LLM non validé** : décider du succès avec un LLM-juge dont la justesse n'est jamais
   mesurée contre une vérité-terrain indépendante.

La littérature multiplie les méthodes d'attaque (§2) et les outils (§3), mais traite la
**mesure** du succès comme acquise. **La contribution de ce mémoire se situe à cet endroit** :

- **Découplage oracle / juge** : un **oracle déterministe** (détection de flag/secret,
  éventuellement confirmée par un *post-step*) fournit une vérité-terrain objective, **distincte**
  du **juge LLM** générique.
- **Validation du juge** : le juge est **mesuré** (précision, rappel, F1, κ de Cohen, intervalles
  de Wilson) contre l'oracle, puis contre un **gold standard humain** anti-ancrage.
- **Évaluation *tool-agnostic*** : le même oracle mesure RedAgent **et** un framework de référence
  (PyRIT) dans des conditions identiques, via une **comparaison pré-enregistrée** — ce qui rend
  l'instrument réutilisable au-delà de RedAgent.

Ce positionnement — déplacer l'effort de la *force de l'attaque* vers la *rigueur de la mesure* —
distingue ce travail des outils et benchmarks existants, et structure les expériences du
chapitre IV.
