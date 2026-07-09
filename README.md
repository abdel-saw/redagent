# RedAgent — Agent autonome de red teaming pour applications LLM

> **Projet de Fin d'Études (Cycle Ingénieur, Ingénierie Informatique)**
> Auteur : **SAWADOGO S Abdel K N** · Encadrant : **Pr DABOUNOU**
> FST Settat — Université Hassan 1er · Soutenance : 22 juin 2026

RedAgent est un **agent léger de red teaming** (BYOK, observable) qui audite en
boîte-noire des applications fondées sur des LLM contre le **OWASP Top 10 for LLM
Applications (édition 2025)**. Le projet livre **deux artefacts distincts** :

1. **Un outil** — un moteur d'attaque autonome (boucle *seed → mutate*) piloté par
   un LLM attaquant, qui audite une cible via un simple template HTTP/JSON.
2. **Une méthodologie rigoureuse et agnostique à l'outil** pour *évaluer* ce type
   d'agent — c'est la **colonne vertébrale scientifique** du mémoire.

---

## 1. Thèse

> On ne prétend pas avoir construit « l'attaquant le plus fort ». On livre un
> outil **léger, BYOK, observable**, **et** une méthodologie pour évaluer
> honnêtement ce type d'outil, démontrée par (i) la **mesure de fiabilité d'un
> juge LLM** contre une **vérité-terrain déterministe**, et (ii) une **comparaison
> contrôlée et pré-enregistrée contre PyRIT** sur des cibles tierces.

Un compromis mesuré (taux de capture *vs* légèreté / BYOK / observabilité) est un
résultat valide : **RedAgent n'a pas besoin de « gagner »** pour que la
contribution méthodologique tienne.

---

## 2. Contribution centrale : découpler l'oracle du juge

Le cœur scientifique du projet est la **séparation stricte de deux notions de
« succès »** qui étaient confondues dans les travaux antérieurs :

| | **Oracle déterministe** | **Juge LLM** |
|---|---|---|
| Question posée | « Le flag/secret a-t-il été *capturé* ? » | « La réponse *trahit-elle* une vulnérabilité ? » |
| Nature | Mécanique, reproductible (regex + post-step HTTP) | Probabiliste, sujet à erreur |
| Rôle | **Vérité-terrain** de l'évaluation | Composant *audité* |
| Emplacement | `experiments/` uniquement | `app/` (utilisé par l'outil interactif) |

**Découplage vérifié structurellement** : l'orchestrateur interactif n'importe
*jamais* l'oracle. L'oracle ne vit que dans le harnais expérimental. Cela évite la
**validation circulaire** (juger un outil avec son propre juge non validé).

### Deux expériences bâties sur ce découplage

- **Exp.1 — Efficacité de l'attaquant** (`experiments/runner.py`) : pour chaque
  cellule *(attaquant × défi × run)*, on déroule la boucle du moteur contre la
  cible ; **le succès est tranché par l'oracle**, jamais par un juge. Résultat :
  une matrice de taux de capture.
- **Exp.2 — Fiabilité des juges** (`experiments/replay.py`) : on **rejoue** les
  tuples *(prompt, réponse, label_oracle)* loggés par Exp.1 à travers un pool de
  juges LLM, et on compare chaque verdict au label de l'oracle. Coût borné (aucune
  nouvelle attaque). Produit précision / rappel / F1 / FP / FN par juge, plus le
  **κ de Cohen** contre un **gold standard humain**.

> **Validation de l'oracle lui-même** (`experiments/_smoke_oracle.py`) : avant de
> bâtir quoi que ce soit dessus, l'oracle est prouvé sur 3 propriétés / 12 cas —
> **sensibilité** (se déclenche sur les payloads connus-bons, en live), **reconnaissance**
> (repère le flag s'il apparaît), **spécificité** (reste négatif sur un refus
> explicite et sur un leurre `JWT_SECRET`). 12/12 = oracle prouvé.

---

## 3. Périmètre OWASP (verrouillé)

Catégories testables en **boîte-noire JSON**, donc retenues :

| Code | Catégorie | Défi de validation |
|------|-----------|--------------------|
| **LLM01** | Prompt Injection | PromptMe |
| **LLM02** | Sensitive Information Disclosure | PromptMe (RAG + post-step token) |
| **LLM06** | Excessive Agency | PromptMe |
| **LLM07** | System Prompt Leakage | PromptMe |

LLM03/04/08 sont exclus (nécessitent un accès au pipeline / embeddings, hors
boîte-noire). Voir `SPEC.md` pour la justification complète et le statut de
LLM05/09/10.

**Cibles** : PromptMe (CTF à flags déterministes = oracle) et **Gandalf** (Lakera,
cible tierce publique dont l'oracle — `guess-password` — est **indépendant de
l'auteur**, ce qui renforce l'anti-circularité).

---

## 4. Structure du projet

```
redagentV2/
├── app/                          # LE MOTEUR (itération 1 — l'outil ; utilise le JUGE)
│   ├── config.py                 #   réglages centraux (budget, modèles, BYOK)
│   ├── llm.py                    #   wrapper LiteLLM : suivi coût + JUGE LLM
│   ├── target_adapter.py         #   adaptateur HTTP générique ({{prompt_json}}, response_path)
│   ├── recon.py                  #   reconnaissance opt-in, pilotée par LLM (générique)
│   └── attacks/                  #   catalogue d'attaques (une par catégorie OWASP)
│       ├── base.py               #     AttackModule abstrait + SeededAttack (seed→mutate)
│       ├── llm01_prompt_injection.py
│       ├── llm02_sensitive_info.py
│       ├── llm06_excessive_agency.py
│       └── llm07_system_prompt_leak.py
│
├── experiments/                  # LE HARNAIS (itération 2 — la méthode ; utilise l'ORACLE)
│   ├── oracle.py                 #   oracle déterministe (regex + post-step HTTP)
│   ├── runner.py                 #   Exp.1 — efficacité attaquant (tranchée par l'oracle)
│   ├── replay.py                 #   Exp.2 — fiabilité des juges (rejoue les tuples)
│   ├── metrics.py                #   agrégation : capture-rate, Wilson CI, κ de Cohen
│   ├── pyrit_compare.py          #   Tier 2 — comparaison head-to-head vs PyRIT
│   ├── _smoke_oracle.py          #   T0.1 — preuve de l'oracle (3 propriétés / 12 cas)
│   ├── config/                   #   targets.json, gandalf.json, models.json
│   └── results/                  #   sorties expérimentales + gold standard humain
│
├── SPEC.md                       # spécification verrouillée (thèse, périmètre, protocole)
└── PROJECT_BRIEF.md              # charte projet (contrat de travail)
```

---

## 5. Installation

**Prérequis** : Python 3.11+, et une cible à auditer (p. ex. PromptMe-Lite en
local, ou Gandalf en ligne).

```bash
git clone <URL_DU_DEPOT>
cd redagentV2
python -m venv .venv
# Windows :  .venv\Scripts\activate      Linux/macOS :  source .venv/bin/activate
pip install httpx litellm pydantic
# Pour la comparaison PyRIT (venv isolé recommandé) : pip install pyrit==0.14.0
```

---

## 6. Configuration & clés (BYOK)

RedAgent est **BYOK (Bring Your Own Key)** : vous fournissez vos propres clés de
fournisseur (OpenAI, Groq…). **Les clés ne sont jamais persistées ni journalisées
par l'outil** — elles restent en mémoire le temps de l'exécution.

Fournissez-les par variable d'environnement :

```bash
export OPENAI_API_KEY="sk-..."
export GROQ_API_KEY="gsk-..."
```

> ⚠️ **Ne commitez jamais vos clés.** Le fichier `config.txt` (clés locales) est
> volontairement exclu par `.gitignore`. Utilisez `.env` / variables
> d'environnement.

Les cibles se configurent par un **template JSON** (principe *« fidèle à l'usage
réel »* : l'outil ne patche jamais la cible). Exemple (`experiments/config/targets.json`) :

```json
{
  "adapter": {
    "url": "http://localhost:5007/ask",
    "body_template": "{\"message\": {{prompt_json}}}",
    "response_path": "response"
  }
}
```

- `{{prompt_json}}` est remplacé par le prompt encodé en JSON (ne pas rajouter de
  guillemets), `{{prompt}}` par le prompt brut.
- `response_path` : chemin pointé pour extraire le texte de l'assistant.

---

## 7. Reproduire les expériences

```bash
# T0.1 — prouver l'oracle avant tout (cibles PromptMe live requises)
python -m experiments._smoke_oracle

# Exp.1 — efficacité de l'attaquant (succès décidé par l'ORACLE)
python -m experiments.runner  ...       # voir l'en-tête du module pour les options

# Exp.2 — fiabilité des juges (rejoue les tuples d'Exp.1)
python -m experiments.replay --neg 100

# Agrégation des métriques Exp.1 (capture-rate, CSV)
python -m experiments.metrics

# Tier 2 — comparaison contrôlée vs PyRIT (venv isolé)
python -m experiments.pyrit_compare --bench promptme --tag pyrit_promptme
```

---

## 8. Principes de conception (non négociables)

- **Fidèle à l'usage réel** — l'outil ne patche jamais la cible ; pas de shim de
  confort. On force l'environnement/config au lancement.
- **Générique, non réactif** — aucune connaissance spécifique à une cible n'est
  codée en dur (préserve la revendication d'autonomie).
- **BYOK strict** — les clés ne sont ni persistées, ni affichées, ni fabriquées.
- **Anti-circularité** — l'outil est évalué contre des oracles **tiers et
  déterministes**, pas contre son propre juge.

---

## 9. Pile technique

FastAPI · Uvicorn · **LiteLLM** (accès multi-fournisseur) · httpx · Pydantic ·
SQLite · Jinja2 · Tailwind (CDN) · HTMX + SSE. Comparateur : **PyRIT** (v0.14.0).

---

## Licence & autorisation d'audit

Projet académique. Toutes les cibles auditées sont **auto-hébergées ou
explicitement ouvertes à l'attaque** (PromptMe, Gandalf). N'utilisez RedAgent que
contre des systèmes que vous êtes **autorisé** à tester.
