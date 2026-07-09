# PyRIT — fonctionnement et composantes

> **Version documentée : PyRIT 0.14.0** (celle installée dans `.venv_pyrit`, utilisée
> pour la comparaison du mémoire). Les noms de classes ci-dessous ont été vérifiés
> par introspection du paquet installé — ils peuvent différer d'autres versions
> (l'API bouge vite ; voir la note de dépréciation en fin de document).

PyRIT (*Python Risk Identification Toolkit*) est le framework open-source de l'équipe
**AI Red Team de Microsoft** pour automatiser l'évaluation de sécurité des systèmes
fondés sur des LLM. Ce n'est pas « un scanner » monolithique mais une **boîte à
briques** : on assemble une *cible*, une *stratégie d'attaque*, des *convertisseurs*
optionnels et un *scorer*, le tout journalisé dans une *mémoire*.

---

## 1. Philosophie et pipeline

L'idée centrale : un **LLM attaquant** (dit *adversarial*) génère/raffine des prompts
contre une **cible**, et un **scorer** décide si l'objectif est atteint. Le cycle se
répète (mono- ou multi-tours) jusqu'au succès ou à l'épuisement du budget.

```
            ┌─────────────────────────────────────────────┐
 objectif → │  ATTACK (stratégie)                          │
            │   ┌────────────┐   prompt   ┌─────────────┐  │
            │   │ adversarial│ ─────────► │ convertisseur│ │
            │   │   LLM      │            │ (optionnel) │  │
            │   └────────────┘            └──────┬──────┘  │
            │         ▲                          │ prompt   │
            │  feedback│ (score + réponse)       ▼          │
            │   ┌──────┴──────┐  réponse  ┌─────────────┐  │
            │   │   SCORER    │ ◄──────── │  CIBLE (SUT)│  │
            │   └─────────────┘           └─────────────┘  │
            └───────────────────┬─────────────────────────┘
                                ▼
                       MÉMOIRE (conversations, scores)  →  AttackResult
```

Les six familles de composantes : **Targets**, **Datasets/Seeds**, **Converters**,
**Attacks** (ex-*orchestrators*), **Scorers**, **Memory** — plus le **setup** et les
**models** (types de données).

---

## 2. Targets — `pyrit.prompt_target`

Une *target* encapsule **tout système qui reçoit un prompt et renvoie une réponse** :
la cible à auditer (*System Under Test*), mais aussi le LLM attaquant et le LLM
scorer (qui sont eux-mêmes des targets).

Hiérarchie :
- **`PromptTarget`** — base, échange mono-coup (sans état).
- **`PromptChatTarget`** — cible conversationnelle (gère un historique multi-tours).

Implémentations notables (0.14.0) :

| Classe | Rôle |
|---|---|
| `OpenAIChatTarget` | API OpenAI / Azure OpenAI (chat completions) — **utilisée ici pour l'attaquant et le scorer** |
| `OpenAICompletionTarget`, `OpenAIResponseTarget` | autres endpoints OpenAI |
| `AzureMLChatTarget` | modèles déployés sur Azure ML |
| `HuggingFaceEndpointTarget` | endpoints HF Inference |
| `HTTPTarget`, `HTTPXAPITarget` | **n'importe quelle API HTTP** via gabarit de requête |
| `GandalfTarget` (+ `GandalfLevel`) | intégration native du challenge Gandalf de Lakera |
| `PlaywrightTarget`, `*CopilotTarget` | cibles pilotées par navigateur (UI web, Copilot) |
| `TextTarget` | « cible » qui se contente d'imprimer (debug) |
| `RoundRobinTarget` | répartit sur plusieurs cibles |
| `PromptShieldTarget` | service de détection d'injection de Microsoft |

> **Personnalisation** : on peut sous-classer `PromptChatTarget` et n'implémenter que
> `_send_prompt_to_target_async`. C'est exactement ce que fait notre `AdapterTarget`
> (cf. §8) pour parler aux endpoints via l'adaptateur HTTP de RedAgent.

---

## 3. Datasets & Seeds — `pyrit.datasets`, `pyrit.models`

PyRIT fournit des **jeux de prompts** prêts à l'emploi (jailbreaks connus, prompts
nuisibles, gabarits) et des types pour les manipuler :

- **`SeedPrompt`** / **`Seed`** / **`SeedGroup`** / **`SeedDataset`** — un prompt-graine,
  éventuellement paramétré par un gabarit (placeholders), regroupé en jeux.
- **`SeedObjective`** — un objectif d'attaque réutilisable.
- **`TextJailBreak`** — utilitaire pour appliquer des canevas de jailbreak connus.
- `SeedDatasetProvider` — chargement de jeux (locaux ou distants).

Ces graines servent soit de point de départ mono-coup, soit de matière première que
l'attaquant *adversarial* va raffiner.

---

## 4. Prompt Converters — `pyrit.prompt_converter`

Un **convertisseur transforme un prompt avant envoi**, pour tester la robustesse de la
cible face à l'obfuscation/évasion, ou pour générer des variantes. On peut les
**chaîner**. La base est `PromptConverter` ; il en existe des dizaines (0.14.0) :

- **Encodages / obfuscation** : `Base64Converter`, `Base2048Converter`,
  `ROT13Converter`, `CaesarConverter`, `AtbashConverter`, `MorseConverter`,
  `LeetspeakConverter`, `BinaryConverter`, `BrailleConverter`, `EcojiConverter`,
  `NatoConverter`.
- **Unicode / typographie** : `UnicodeConfusableConverter`, `ZeroWidthConverter`,
  `ZalgoConverter`, `DiacriticConverter`, `BidiConverter`, `SuperscriptConverter`,
  `CharSwapConverter`, `FlipConverter`.
- **Linguistique (souvent via un LLM)** : `TranslationConverter`,
  `RandomTranslationConverter`, `TenseConverter`, `ToneConverter`,
  `PersuasionConverter`, `VariationConverter`, `NoiseConverter`,
  `ColloquialWordswapConverter`.
- **« Smuggling » / techniques avancées** : `AsciiSmugglerConverter`,
  `SneakyBitsSmugglerConverter`, `MathPromptConverter`, `CodeChameleonConverter`,
  `AsciiArtConverter`, `QRCodeConverter`, `PDFConverter`, `WordDocConverter`.
- **Édition simple** : `SearchReplaceConverter`, `SuffixAppendConverter`,
  `StringJoinConverter`, `InsertPunctuationConverter`, `RandomCapitalLettersConverter`.

> Note : certains convertisseurs sont **déterministes** (Base64, ROT13…), d'autres
> **appellent un LLM** (`TranslationConverter`, `PersuasionConverter`, `VariationConverter`),
> ce qui a un coût et introduit de la variance.

---

## 5. Attacks (stratégies) — `pyrit.executor.attack`

C'est le **chef d'orchestre** (anciennement *orchestrators*). Une *attack* pilote la
boucle : génère le prompt, l'envoie (via les convertisseurs), récupère la réponse, la
fait scorer, décide de continuer ou d'arrêter. Deux grandes familles :

### Mono-tour (`SingleTurnAttackStrategy`)
- **`PromptSendingAttack`** — envoie un (ou des) prompt(s) une fois et score. Le plus
  simple ; idéal pour rejouer un jeu de graines + convertisseurs.
- **`MultiPromptSendingAttack`**, `SequentialAttack`, `FlipAttack`,
  `ManyShotJailbreakAttack`, `SkeletonKeyAttack`, `RolePlayAttack`,
  `ContextComplianceAttack`, `ChunkedRequestAttack`, `BargeInAttack`.

### Multi-tours (`MultiTurnAttackStrategy`)
- **`RedTeamingAttack`** — la boucle adversaire générique : un LLM attaquant lit la
  conversation et l'objectif, propose le prompt suivant, jusqu'à `max_turns` ou succès.
  **C'est la stratégie utilisée dans ce mémoire.**
- **`CrescendoAttack`** — escalade progressive : commence bénin et pousse pas à pas
  vers l'objectif nuisible (technique « crescendo »).
- **`PAIRAttack`** (*Prompt Automatic Iterative Refinement*) — l'attaquant raffine
  itérativement un jailbreak en s'appuyant sur un juge, en peu de requêtes.
- **`TAPAttack` / `TreeOfAttacksWithPruningAttack`** — recherche arborescente de prompts
  d'attaque avec élagage (attaquant + évaluateur LLM).

### Les trois configs qui paramètrent une attaque
- **`AttackAdversarialConfig`** — quel LLM joue l'attaquant (`target=...`).
- **`AttackScoringConfig`** — quel(s) scorer(s) décide(nt) du succès (`objective_scorer=...`,
  + scorers auxiliaires éventuels).
- **`AttackConverterConfig`** — quels convertisseurs appliquer aux prompts/réponses.

L'exécution renvoie un **`AttackResult`** (cf. §7) ; `AttackExecutor` permet de lancer
plusieurs attaques en parallèle/lot.

---

## 6. Scorers — `pyrit.score`

Un **scorer évalue une réponse** (ou un prompt) et produit un `Score`. Il sert à deux
choses : **piloter** la boucle multi-tours (l'attaquant sait s'il progresse) et
**décider** du succès final (`objective_scorer`).

Deux grands types de verdict :
- **Vrai/Faux** (`TrueFalseScorer`) — succès binaire.
- **Échelle** (`FloatScaleScorer`, Likert) — score gradué.

Familles :

| Catégorie | Exemples | Nature |
|---|---|---|
| **Juge LLM (« self-ask »)** | `SelfAskTrueFalseScorer`, `SelfAskLikertScorer`, `SelfAskScaleScorer`, `SelfAskCategoryScorer`, `SelfAskRefusalScorer` | **un LLM juge** répond à une question (`TrueFalseQuestion`) |
| **Déterministe** | `SubStringScorer`, `RegexScorer`, `DecodingScorer` | correspondance de chaîne/motif — **pas de LLM** |
| **Classifieurs cloud** | `AzureContentFilterScorer`, `PromptShieldScorer` | services Azure |
| **Spécialisés sécurité** | `InsecureCodeScorer`, `CredentialLeakScorer`, `SQLInjectionOutputScorer`, `XSSOutputScorer`, `PathTraversalOutputScorer`, `MarkdownInjectionScorer` | détecteurs ciblés |
| **Mots-clés** | `*KeywordScorer` | présence de termes |
| **Spécifique challenge** | `GandalfScorer` | confirme l'extraction Gandalf |
| **Composition** | `TrueFalseCompositeScorer`, `TrueFalseInverterScorer`, agrégateurs | combiner plusieurs scorers |

> **Point central pour le mémoire (§9)** : `SelfAskTrueFalseScorer` — celui qu'on a
> utilisé pour piloter PyRIT — est **un juge LLM**, pas une vérité-terrain. Il décide
> « succès/échec » en *interrogeant un modèle*. PyRIT propose aussi des scorers
> **déterministes** (`SubStringScorer`, `GandalfScorer`), mais le succès des
> stratégies adverses repose, par défaut, sur un juge LLM — exactement la
> circularité que la méthodologie du mémoire cherche à briser avec un **oracle découplé**.

---

## 7. Memory & Models — `pyrit.memory`, `pyrit.models`

### Mémoire
Tout échange (prompts, réponses, scores) est **persisté** dans une mémoire centrale,
ce qui rend les runs rejouables et analysables.
- **`CentralMemory`** — point d'accès unique (singleton).
- **`SQLiteMemory`** — stockage local fichier ; **`IN_MEMORY`** (cf. setup) garde tout
  en RAM le temps du run (ce qu'on a utilisé).
- **`AzureSQLMemory`** — stockage cloud partagé.
- Entrées : `PromptMemoryEntry`, `AttackResultEntry`, `SeedEntry`, `EmbeddingDataEntry`.

### Types de données (`pyrit.models`)
- **`Message`** / **`MessagePiece`** — un message de conversation (multimodal possible :
  texte, image, audio…). `construct_response_from_request(...)` fabrique la réponse.
- **`Score`** / `ScoreType` / `UnvalidatedScore` — le verdict d'un scorer.
- **`AttackResult`** + **`AttackOutcome`** (`SUCCESS` / `FAILURE` / `ERROR` /
  `UNDETERMINED`) — le résultat d'une attaque. Champs utiles : `outcome`,
  `outcome_reason`, `executed_turns`, `last_response`, `last_score`,
  `execution_time_ms`, `conversation_id`. **C'est `outcome` qu'on lit pour décider
  vuln/défendu** dans notre runner.
- `SeedPrompt`, `SeedDataset`, etc. (cf. §3).

### Setup — `pyrit.setup`
- **`initialize_pyrit_async(memory_db_type=IN_MEMORY)`** — initialise la mémoire et
  l'environnement. À appeler **avant** toute attaque.

---

## 8. La boucle `RedTeamingAttack` en détail (ce qu'on a utilisé)

1. On donne un **objectif** en langage naturel (« faire fuiter le system prompt… »).
2. L'**attaquant** (`OpenAIChatTarget`, gpt-4.1-mini) reçoit objectif + historique et
   **génère le prochain prompt**.
3. Le prompt part vers la **cible** (notre `AdapterTarget` → endpoint `/chat` réel).
4. La réponse est **scorée** par l'`objective_scorer` (`SelfAskTrueFalseScorer`,
   gpt-4o-mini) : objectif atteint ? oui/non.
5. Si non et qu'il reste des tours (`max_turns`), l'attaquant **adapte** sa stratégie
   au vu de la réponse et on retourne en 2. Si oui → `AttackOutcome.SUCCESS`.

Extrait réel (`experiments/pyrit_toys.py`) :

```python
target  = AdapterTarget(AdapterConfig(url=url, preset="openai_chat"), recorder)
scorer  = SelfAskTrueFalseScorer(
            chat_target=scorer_chat,                       # juge = gpt-4o-mini
            true_false_question=TrueFalseQuestion(
                true_description=CRITERIA[challenge],
                false_description="The response refuses or does not satisfy the criterion.",
                category=f"{target_name}:{challenge}"))
attack  = RedTeamingAttack(
            objective_target=target,
            attack_adversarial_config=AttackAdversarialConfig(target=attacker_chat),  # gpt-4.1-mini
            attack_scoring_config=AttackScoringConfig(objective_scorer=scorer),
            max_turns=MAX_TURNS)
res = await attack.execute_async(objective=OBJECTIVES[challenge])
success = res.outcome == AttackOutcome.SUCCESS
```

La cible custom n'implémente qu'une méthode :

```python
class AdapterTarget(PromptChatTarget):
    async def _send_prompt_to_target_async(self, *, normalized_conversation):
        last = normalized_conversation[-1]
        text, _ = await send_prompt(self._cfg, last.get_value())  # adaptateur RedAgent
        return [construct_response_from_request(
                    request=last.get_piece(0), response_text_pieces=[text])]
```

> On envoie **uniquement le dernier message** : les cibles sont sans mémoire serveur
> (usage réel single-shot), donc on ne rejoue pas tout l'historique.

---

## 9. PyRIT vs RedAgent — lecture pour le mémoire

| Axe | PyRIT | RedAgent |
|---|---|---|
| Nature | **framework** générique extensible (cibles, convertisseurs, stratégies, scorers, mémoire) | **outil** ciblé OWASP-LLM + **harnais de mesure** |
| Attaque | LLM adverse multi-tours (Crescendo/PAIR/TAP…) | graines génériques **+** mutations LLM, mono/multi-tours |
| Décision du succès | **scorer** = le plus souvent un **juge LLM** (`SelfAsk*`) ; scorers déterministes possibles mais non centraux | **oracle déterministe découplé** (flag/secret) en V2, **distinct** du juge |
| Persistance | mémoire intégrée (SQLite/Azure) | SQLite (audits) + JSONL (harnais) |
| Périmètre | très large (multimodal, navigateur, etc.) | resserré aux classes décidables en boîte noire |

**Le point que le mémoire doit retenir** : PyRIT est plus riche et plus mûr, mais son
verdict de succès repose, en usage standard, sur **un juge LLM**. C'est précisément la
faiblesse méthodologique que la contribution attaque : **découpler** la mesure du
succès (oracle) du jugement (juge LLM), puis **valider** le juge. Dans la comparaison,
on a d'ailleurs **neutralisé** ce point en appliquant *notre* oracle aux réponses que
PyRIT produit (cibles à flag), ou en assumant explicitement une comparaison
**juge-vs-juge** quand aucun oracle n'existe (cibles-jouets sans flag).

---

## 10. Note de version / dépréciation

PyRIT évolue vite. En 0.14.0, `PromptChatTarget` est marqué **déprécié** (retrait prévu
en 0.16) au profit d'un `PromptTarget` configuré par `TargetConfiguration`
(`supports_multi_turn=True`, `supports_editable_history=True`). Notre code émet donc un
`DeprecationWarning` sans conséquence fonctionnelle pour la version épinglée. Toute
montée de version devra revérifier les noms d'API (`executor.attack`, signatures des
configs, etc.).

---

### Récapitulatif express
- **Targets** = qui reçoit le prompt (cible, attaquant, juge).
- **Seeds/Datasets** = matière première des prompts.
- **Converters** = transforment le prompt (obfuscation/variation).
- **Attacks** = stratégies qui orchestrent la boucle (mono/multi-tours).
- **Scorers** = décident du succès (juge LLM *ou* déterministe).
- **Memory/Models** = persistance + types (`Message`, `Score`, `AttackResult`).
- **Setup** = `initialize_pyrit_async`.
