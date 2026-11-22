# RedAgent

**Red teaming d'applications LLM et évaluation de la fiabilité des juges.**

RedAgent est un projet de fin d'études en ingénierie informatique à la FST
Settat. Il associe un moteur d'attaque Python à un protocole expérimental :
mesurer la capture d'un secret avec un oracle déterministe, puis évaluer
séparément les verdicts d'un juge LLM.

*English summary: a Python research project for black-box LLM red teaming,
with deterministic outcome checks, separate LLM judge evaluation, and
comparison experiments against PyRIT.*

[Explorer les résultats](#explorer-les-résultats-sans-clé-api) ·
[Architecture](#architecture) ·
[Protocole](SPEC.md) ·
[Mémoire PDF](rapport_latex/main.pdf) ·
[Présentation](presentation/soutenance_redagent.pptx)

## Ce que contient ce dépôt

- **Moteur d'attaque** : scénarios initiaux, mutations générées par LLM,
  adaptateurs HTTP/JSON et suivi de consommation.
- **Évaluation de l'attaquant** : capture décidée par un oracle déterministe,
  avec journaux par tentative et par exécution.
- **Évaluation des juges** : rejeu des réponses, précision, rappel, F1,
  faux positifs, faux négatifs et accord de Cohen.
- **Comparaison avec PyRIT** : expériences sur des cibles et des critères
  d'évaluation communs, avec [protocole pré-enregistré](report/tier2_preregistration_pyrit.md).
- **Résultats consultables** : fichiers JSONL/CSV, synthèses et documents
  académiques inclus dans le dépôt.

**État de cette version.** Le dépôt contient le moteur et les scripts
d'expérimentation. Il ne contient pas de point d'entrée web FastAPI ni de
templates HTMX permettant de lancer l'interface présentée dans le mémoire.
Certains scripts conservent des chemins propres à l'environnement d'origine ;
les expériences live demandent donc une adaptation de configuration.
La consultation et l'agrégation des résultats ci-dessous ne nécessitent
ni serveur, ni clé API, ni accès aux cibles.

## Architecture

![Architecture du projet RedAgent](fig_architecture.png)

| Composant | Fichiers | Rôle |
| --- | --- | --- |
| Moteur | [app/attacks/](app/attacks/), [app/llm.py](app/llm.py) | Générer et muter les tentatives ; suivre les appels aux modèles |
| Adaptateur | [app/target_adapter.py](app/target_adapter.py) | Envoyer les requêtes et extraire la réponse d'une cible |
| Expérience 1 | [experiments/runner.py](experiments/runner.py), [oracle.py](experiments/oracle.py) | Mesurer la capture selon les critères du banc d'essai |
| Expérience 2 | [experiments/replay.py](experiments/replay.py) | Comparer les verdicts des juges aux labels de l'oracle |
| Analyse | [experiments/metrics.py](experiments/metrics.py) | Agréger les captures et calculer les intervalles de Wilson |
| Comparaison | [experiments/pyrit_compare.py](experiments/pyrit_compare.py) | Exécuter le protocole comparatif avec PyRIT |

### Pourquoi séparer l'oracle du juge

Un juge LLM peut reconnaître une vulnérabilité à tort ou manquer une fuite.
Sur les défis à secret vérifiable, l'oracle fournit un critère de capture
distinct du verdict du juge. L'expérience 1 mesure l'attaquant avec cet oracle ;
l'expérience 2 réutilise les réponses pour mesurer le juge.

Cette séparation évite de valider le moteur uniquement avec son propre juge.
La validité de chaque oracle reste limitée au défi et aux vérifications
implémentées ; réussir un smoke test ne constitue pas une preuve générale.
Les analyses contre les annotations humaines sont également disponibles dans
les [résultats](experiments/results/) et le [rapport méthodologique](report/methodologie_et_exp2.md).

## Explorer les résultats sans clé API

Prérequis : Python 3.11+ et Git. Depuis un terminal :

```bash
git clone https://github.com/abdel-saw/redagent.git
cd redagent
python -m experiments.metrics mtxA_seedmut
```

Cette commande utilise uniquement la bibliothèque standard Python. Elle lit
les journaux déjà publiés, affiche les taux de capture et les intervalles
de Wilson à 95 %, puis régénère
`experiments/results/mtxA_seedmut/exp1_summary.csv`.
Elle ne lance aucune attaque et ne fait aucun appel à un fournisseur.

Autres jeux de résultats :

```bash
python -m experiments.metrics mtxB_mutonly
python -m experiments.metrics gandalf_mtx
python -m experiments.metrics pyrit_promptme
python -m experiments.metrics pyrit_gandalf
```

### Exemple issu des journaux publiés

L'agrégation du jeu `mtxA_seedmut` donne :

| Défi | Captures / exécutions |
| --- | --- |
| LLM02 | 5 / 33 |
| LLM06 | 4 / 33 |
| LLM07 | 5 / 28 |

Ces nombres agrègent plusieurs modèles attaquants. Les effectifs diffèrent
selon les cellules ; ils ne constituent ni un classement général des modèles,
ni une estimation de la sécurité de toutes les applications LLM.
Pour les paramètres et les détails, consulter les
[journaux](experiments/results/mtxA_seedmut/) et le
[rapport de l'expérience 1](report/exp1_efficacite_attaquant.md).

Les captures LLM07 de ce jeu proviennent de scénarios initiaux, tandis que
les captures LLM02 et LLM06 proviennent de mutations. Cette distinction permet
d'étudier la contribution de la génération adaptative sans attribuer toute
capture au modèle attaquant.

## Périmètre des expériences

| Code | Catégorie | Banc documenté |
| --- | --- | --- |
| LLM01 | Prompt Injection | PromptMe |
| LLM02 | Sensitive Information Disclosure | PromptMe |
| LLM06 | Excessive Agency | PromptMe |
| LLM07 | System Prompt Leakage | PromptMe et Gandalf |

Le moteur ne couvre pas l'ensemble de l'OWASP Top 10. Les expériences
PromptMe par défaut du runner portent sur LLM02, LLM06 et LLM07 ; les niveaux
Gandalf utilisent le module LLM07. Voir [SPEC.md](SPEC.md) pour le périmètre
et les exclusions.

## Préparer les expériences live

Les dépendances du moteur incluent `httpx`, `litellm` et `pydantic`.
Dans un environnement virtuel :

```bash
python -m venv .venv
```

Activer l'environnement :

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

```bash
python -m pip install httpx litellm pydantic
```

Il n'existe pas encore de fichier de dépendances verrouillé dans ce dépôt.
Les scripts de génération de documents et d'analyse des annotations humaines
peuvent demander des dépendances supplémentaires.

Avant tout appel live :

1. Adapter les endpoints dans [targets.json](experiments/config/targets.json)
   ou [gandalf.json](experiments/config/gandalf.json).
2. Vérifier les modèles et le budget dans [models.json](experiments/config/models.json).
3. Adapter le chargement des clés : `runner.py`, `replay.py` et
   `pyrit_compare.py` lisent actuellement un fichier `.env` à un chemin WSL
   propre à la machine d'origine. Définir uniquement des variables
   d'environnement ne remplace pas ce chargeur.
4. Utiliser des cibles dont le test est autorisé et vérifier les quotas
   des fournisseurs. Les appels live peuvent être facturés.
5. Employer un nouveau `--tag` pour isoler les nouvelles sorties des
   résultats publiés.

Après cette adaptation, les commandes du protocole comprennent :

```bash
# Une cellule PromptMe, sorties isolées
python -m experiments.runner --challenge LLM02 --attempts 6 --tag local_check

# Rejouer les réponses de cette cellule avec les juges configurés
python -m experiments.replay --source local_check --tag local_judges --neg 100

# Agréger les résultats de l'attaquant
python -m experiments.metrics local_check
```

Le rejeu ne lance pas de nouvelles attaques, mais appelle les modèles juges.
Le script [experiments/_smoke_oracle.py](experiments/_smoke_oracle.py)
contient les vérifications de l'oracle ; son exécution requiert les cibles
configurées.

La comparaison PyRIT utilise la version `0.14.0` dans le protocole d'origine.
Prévoir un environnement virtuel séparé et consulter le
[rapport de comparaison](report/tier2_comparaison_pyrit.md) avant de l'exécuter.

## Limites et prochaines améliorations

- Rendre les chemins de configuration et le chargement des clés portables.
- Ajouter un fichier de dépendances reproductible et des tests automatisés.
- Documenter séparément les composants d'interface décrits dans le mémoire.
- Interpréter les mesures avec leurs effectifs, leurs incertitudes et les
  conditions des bancs d'essai.

## Auteur et cadre académique

**SAWADOGO S Abdel K N** · Projet de fin d'études, cycle ingénieur en informatique  
**FST Settat — Université Hassan 1er** · Encadrant : **Pr DABOUNOU**  
Soutenance : **22 juin 2026**

Projet destiné à l'évaluation autorisée d'applications LLM. Le dépôt ne
contient actuellement pas de fichier de licence ; aucune licence open source
particulière n'est revendiquée ici.
