# Pré-enregistrement — Baseline garak (Tier 3, bonus)

> **Statut : FIGÉ le 2026-06-13, avant toute exécution de garak.**
> Toute déviation sera journalisée, datée et justifiée dans `journal.md`, sans réécriture.

## 1. Nature et objectif (exploratoire, pas un head-to-head)

Le Tier 3 ajoute **garak** (NVIDIA, scanner de vulnérabilités LLM) comme **troisième outil**
mesuré par **notre oracle déterministe**. Objectif : étendre la démonstration que l'instrument de
mesure est **tool-agnostic** à un outil de **paradigme différent** de RedAgent et PyRIT.

**garak n'est pas comparable à budget égal** : c'est un scanner à **probes fixes, single-turn**,
sans attaquant LLM itératif ni boucle guidée par scorer ; ses probes visent surtout le **contenu
nuisible / jailbreak / extraction de données d'entraînement**, **pas l'extraction d'un flag CTF**.
Cette étude est donc **exploratoire** (caractérisation de couverture), explicitement **distincte**
de la comparaison pré-enregistrée confirmatoire RedAgent↔PyRIT (Tier 2).

## 2. Hypothèse (déclarée avant exécution)

- **Attendu** : taux de capture (oracle) de garak **proche de 0** sur ces cibles, car ses probes
  ne sont pas conçues pour extraire les flags/secrets spécifiques de PromptMe.
- **Engagement** : le résultat est rapporté **quel qu'il soit**. Un taux nul **n'est pas un échec**
  de garak — c'est un constat de **non-recouvrement** entre son paradigme (probes génériques) et
  la classe de tâches « extraction de flag en boîte-noire JSON ».

## 3. Cible et périmètre (figés)

- **Banc** : **PromptMe** uniquement, défis `LLM02`, `LLM06`, `LLM07` (endpoints JSON propres).
- **Gandalf EXCLU** de garak : le *generator REST* de garak est orienté **JSON** ; Gandalf est
  **form-urlencoded** et l'injection de `$INPUT` dans un corps form casserait l'échappement.
  Conformément au principe « fidèle à l'usage réel », on **ne bricole pas** de contournement →
  garak hors-périmètre Gandalf, documenté comme friction.
- **Connexion** : *generator REST* de garak → mêmes endpoints live que RedAgent/PyRIT
  (un fichier de config REST par défi : URL, `req_template` JSON avec `$INPUT`, `response_json_field`).
  Aucune modification de la cible.

## 4. Probes (figées)

Ensemble fixe, choisi pour sa proximité avec le périmètre (injection / fuite) :
`promptinject`, `latentinjection`, `leakreplay`. (Liste exacte des sous-probes selon la version
épinglée ; ajustements de nommage journalisés.) Générations par défaut de garak (on ne gonfle
pas artificiellement le volume).

## 5. Mesure du succès (commune)

Le succès n'est PAS décidé par les *detectors* de garak. On parse le **rapport JSONL** de garak
(un enregistrement par prompt : prompt + outputs) et on applique **notre oracle** déterministe à
**chaque** couple (prompt, output) — même définition de succès qu'Exp.1 / Tier 2. Sorties au
schéma `exp1_*.jsonl` → `metrics.py` réutilisable.

## 6. Métriques et analyse (figées)

- **Primaire** : taux de capture (oracle) par défi et global, IC de Wilson 95 %.
- **Tableau à trois outils** : RedAgent / PyRIT / garak sur PromptMe (même oracle), en rappelant
  que les budgets et paradigmes diffèrent (lecture **qualitative**, pas de test de supériorité).
- **Secondaire (descriptif)** : nombre de prompts envoyés par garak, et part éventuellement
  capturée. Aucune analyse conditionnée au résultat.

## 7. Arrêt, exclusions, reproductibilité

- garak en venv **isolé** (`.venv_garak`), version **épinglée** (notée à l'installation).
- Erreurs de transport / probes en échec d'outillage : journalisées, exclues des résultats.
- Cibles PromptMe live (lanceur WSL). Graines/seeds de garak par défaut (déterministes si garak
  l'est ; sinon, run unique documenté). Configs loggées.

## 8. Risques connus

- API/CLI garak évolutive → version épinglée ; noms de probes ajustés.
- Paradigme non itératif → comparaison **exploratoire** uniquement (cf. §1).
- *Generator REST* JSON-orienté → Gandalf hors-périmètre (cf. §3).

---

*Fin du pré-enregistrement. Ensuite : install garak (venv isolé), configs REST PromptMe, smoke
1 probe, run, parse → oracle → tableau 3 outils — sans modifier ce protocole.*
