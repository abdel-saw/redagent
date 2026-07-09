# Figures Mermaid à générer (rapport V2)

Coller chaque bloc dans <https://mermaid.live>, exporter en **PNG**, renommer
selon le nom indiqué et déposer dans `rapport_latex/figures/`. Le `.tex` référence
déjà ces fichiers. Le préambule `%%{init...}%%` force `useMaxWidth:false` pour que
l'export PNG ne soit pas tronqué.

| Fichier à produire | Source | Référencé dans |
|---|---|---|
| `figures/fig_architecture.png` | §1 ci-dessous | Chap. II (fig:archi) |
| `figures/fig_expflow.png` | §2 | Chap. II (fig:expflow) |
| `figures/fig_oracle.png` | §3 | Chap. III (fig:oracle) |
| `figures/fig_usecase.png` | §4 | Chap. II (fig:usecase) |
| `figures/fig_classes.png` | §5 | Chap. II (fig:classes) |
| `figures/fig_sequence.png` | §6 | Chap. II (fig:sequence) |
| `figures/fig_ui_config.png` | capture UI V1 (formulaire `/`) | Chap. IV |
| `figures/fig_ui_live.png` | capture UI V1 (`/run/<id>` en direct) | Chap. IV |
| `figures/fig_report_html.png` | capture rapport HTML V1 | Chap. IV |
| `figures/fig_harness_metrics.png` | capture terminal `metrics` (IC) | Chap. IV |
| `figures/fig_gold_xlsx.png` | capture du classeur gold (anti-ancrage) | Chap. IV |
| `figures/fig_pyrit_gandalf.png` | capture terminal `metrics pyrit_gandalf` (PyRIT seul, 4/9) | PPT (diapo 28bis) |

*(Les logos `logo_uh1.png` / `logo_fsts.png` sont déjà copiés.)*

---

## §1 — Architecture (`fig_architecture.png`)

```mermaid
%%{init: {'theme':'default','themeVariables':{'fontSize':'16px'},'flowchart':{'htmlLabels':true,'useMaxWidth':false,'nodeSpacing':55,'rankSpacing':75,'padding':18,'curve':'basis'}}}%%
flowchart TB
  subgraph Operateur["Operateur (BYOK)"]
    UI["Application interactive<br/>(UI / API)"]
    HAR["Harnais d'experiences<br/>(CLI, iteration 2)"]
  end
  subgraph Moteur["Moteur RedAgent (briques partagees)"]
    ORCH["Orchestrateur / Runner"]
    REC["Recon"]
    ATT["Attaquant LLM<br/>(graines + mutations)"]
    ADP["Adaptateur de cible<br/>(HTTP generique)"]
    JUG["Juge LLM<br/>(verdict generique)"]
  end
  ORA["Oracle deterministe<br/>(flag + post-step)<br/>mesure du succes"]
  TGT[("Cible LLM<br/>boite noire, API JSON/form")]
  LLM[("Fournisseurs LLM<br/>attaquant / juge")]

  UI --> ORCH
  HAR --> ORCH
  ORCH --> REC --> ATT
  ATT -->|prompt| ADP -->|HTTP| TGT
  TGT -->|reponse| ADP --> ORCH
  ORCH -->|"(prompt, reponse)"| JUG
  HAR -.->|"succes objectif (it. 2)"| ORA
  ATT <-->|generation| LLM
  JUG <-->|verdict| LLM
  ORCH --> DB[("SQLite<br/>runs / evenements / findings")]
```

---

## §2 — Factorisation Exp.1 / Exp.2 (`fig_expflow.png`)

```mermaid
%%{init: {'theme':'default','themeVariables':{'fontSize':'16px'},'flowchart':{'htmlLabels':true,'useMaxWidth':false,'nodeSpacing':50,'rankSpacing':70,'padding':18,'curve':'basis'}}}%%
flowchart LR
  subgraph Exp1["Exp.1 -- efficacite attaquant"]
    A["seed -> mutation"] --> T["cible"]
    T --> O["ORACLE (succes objectif)"]
    O --> LG["tuples<br/>(prompt, reponse, label_oracle)"]
  end
  subgraph Exp2["Exp.2 -- fiabilite juge"]
    LG --> J["panel de juges"]
    J --> CMP["juge vs oracle"]
    LG --> H["gold standard HUMAIN<br/>(anti-ancrage)"]
    H --> CMP2["juge & oracle<br/>vs verite humaine"]
  end
  CMP2 --> M["metriques<br/>P / R / F1, kappa, IC Wilson"]
```

---

## §3 — Logique de l'oracle (`fig_oracle.png`)

```mermaid
%%{init: {'theme':'default','themeVariables':{'fontSize':'16px'},'flowchart':{'htmlLabels':true,'useMaxWidth':false,'nodeSpacing':45,'rankSpacing':65,'padding':20,'curve':'basis'}}}%%
flowchart TD
  R(["Reponse cible"]) --> D{"detect<br/>(motif flag/secret) ?"}
  D -- non --> F0(["echec"])
  D -- oui --> P{"post-step requis ?"}
  P -- non --> S1(["SUCCES"])
  P -- oui --> E["extraire candidat(s)"]
  E --> Q["resoumettre a l'endpoint<br/>de confirmation"]
  Q --> C{"confirme ?"}
  C -- oui --> S2(["SUCCES<br/>(verite-terrain tierce)"])
  C -- non --> F1(["echec"])
```

---

## §4 — Cas d'utilisation (`fig_usecase.png`)

> Périmètre : l'**outil d'audit (itération 1)**, vu par son acteur unique,
> l'Auditeur. L'oracle déterministe et le rejeu des tentatives n'y figurent
> **pas** : ce ne sont pas des usages interactifs du produit, mais les
> instruments de la mesure de fiabilité (itération 2, cf. §2/§3). Seul le
> *verdict du juge* — le résultat réellement exposé à l'auditeur — est inclus
> par « Lancer un audit ».
>
> **Variante recommandée : PlantUML** (vrai diagramme use-case, formalisme UML
> strict — acteur bonhomme, cas en ellipses, frontière système, `<<include>>`).
> Rendu sur planttext.com ou l'extension VS Code *PlantUML* → export PNG →
> `fig_usecase.png`. La variante Mermaid (flowchart) plus bas reste un repli.

```plantuml
@startuml fig_usecase
left to right direction
skinparam packageStyle rectangle
skinparam shadowing false
skinparam usecase {
  BackgroundColor #FDFDFD
  BorderColor #333333
}
title Cas d'utilisation — RedAgent (outil d'audit, itération 1)

actor "Auditeur" as Aud

rectangle "Système RedAgent" {
  usecase "Configurer la cible" as U1
  usecase "Tester la connectivité" as U2
  usecase "Configurer modèles\nattaquant / juge (BYOK)" as U3
  usecase "Définir budget\net modules OWASP" as U4
  usecase "Lancer un audit" as U5
  usecase "Suivre l'audit\nen direct (SSE)" as U6
  usecase "Consulter / télécharger\nle rapport" as U7
  usecase "Rendre un verdict\npar le juge" as O2
}

Aud --> U1
Aud --> U2
Aud --> U3
Aud --> U4
Aud --> U5
Aud --> U6
Aud --> U7

U5 ..> O2 : <<include>>
@enduml
```

### Repli Mermaid (flowchart)

> Si PlantUML n'est pas disponible. Mermaid n'a pas de use-case natif~; l'acteur
> est relié aux cas, le lien pointillé `inclut` joue le rôle d'`<<include>>`.

```mermaid
%%{init: {'theme':'default','themeVariables':{'fontSize':'15px'},'flowchart':{'htmlLabels':true,'useMaxWidth':false,'nodeSpacing':40,'rankSpacing':70,'curve':'basis'}}}%%
flowchart LR
  A(["Auditeur"])
  subgraph SYS["Systeme RedAgent"]
    U1(["Configurer la cible"])
    U2(["Tester la connectivite"])
    U3(["Configurer modeles attaquant/juge (BYOK)"])
    U4(["Definir budget et modules OWASP"])
    U5(["Lancer un audit"])
    U6(["Suivre l'audit en direct (SSE)"])
    U7(["Consulter / telecharger le rapport"])
    O2(["Rendre un verdict par le juge"])
  end
  A --- U1
  A --- U2
  A --- U3
  A --- U4
  A --- U5
  A --- U6
  A --- U7
  U5 -.->|inclut| O2
```

---

## §5 — Diagramme de classes (`fig_classes.png`)

> Vue statique. Montre les **quatre** modules d'attaque dans le périmètre
> (pas sept), l'`Oracle` et le `Juge` **découplés**, l'adaptateur et le harnais.
> La note centrale énonce le principe ; ne pas la retirer.

```mermaid
%%{init: {'theme':'default','themeVariables':{'fontSize':'14px'}}}%%
classDiagram
    class Orchestrateur {
        +run_audit(cible, modules, attaquant, juge, budget)
    }
    class AdapterConfig {
        +url
        +body_template
        +encoding
        +response_path
        +send_prompt(prompt) reponse
    }
    class AttackModule {
        <<abstract>>
        +owasp_id
        +run(ctx) AttackResult
    }
    class SeededAttack {
        +seeds
        +run(ctx) AttackResult
    }
    class AttackerLLM {
        +mutate(prompt, reponse) prompt
    }
    class OracleSpec {
        +detect_regex
        +post_step
        +evaluate(prompt, reponse) OracleResult
    }
    class JudgeLLM {
        +criteria
        +verdict(prompt, reponse) Verdict
    }
    class Harnais {
        +exp1_runner()
        +exp2_replay()
        +metrics()
    }
    AttackModule <|-- SeededAttack
    SeededAttack <|-- LLM01_PromptInjection
    SeededAttack <|-- LLM02_SensitiveInfo
    SeededAttack <|-- LLM06_ExcessiveAgency
    SeededAttack <|-- LLM07_SystemPromptLeak
    Orchestrateur --> AdapterConfig
    Orchestrateur --> AttackModule
    Orchestrateur --> JudgeLLM : verdict
    SeededAttack --> AttackerLLM : mutations
    Harnais --> Orchestrateur
    Harnais --> OracleSpec : succes objectif
    Harnais --> JudgeLLM
    note for OracleSpec "Oracle mobilise par le HARNAIS seul (iteration 2).<br/>Decouplage : Oracle et Juge evaluent le meme (prompt, reponse) mais NE se referencent PAS."
```

---

## §6 — Diagramme de séquence d'un audit (`fig_sequence.png`)

> Vue dynamique du déroulé d'un audit **côté auditeur (itération 1)**~: pour
> chaque tentative, l'attaquant produit un prompt, l'adaptateur interroge la
> cible en boîte noire, et le juge rend le verdict qui alimente les *findings*.
> L'oracle n'intervient **pas** ici~: c'est l'instrument de mesure de
> l'itération 2, qui rejoue ensuite les mêmes tuples journalisés (cf. §2).

```mermaid
%%{init: {'theme':'default','themeVariables':{'fontSize':'14px'}}}%%
sequenceDiagram
    actor Aud as Auditeur
    participant Orch as Orchestrateur
    participant Att as Attaquant (LLM)
    participant Adp as Adaptateur HTTP
    participant Tgt as Cible (boite noire)
    participant Jug as Juge (LLM)
    Aud->>Orch: run_audit(cible, modules, budget)
    loop chaque tentative (graine puis mutation)
        Att->>Orch: prompt d'attaque
        Orch->>Adp: send_prompt(prompt)
        Adp->>Tgt: HTTP (JSON / form)
        Tgt-->>Adp: reponse
        Adp-->>Orch: reponse
        Orch->>Jug: verdict(prompt, reponse)
        Jug-->>Orch: verdict (vuln / pas_vuln)
        Orch->>Orch: journaliser (prompt, reponse, verdict)
    end
    Orch-->>Aud: findings + rapport
```

---

## Conseils d'export
1. Coller le bloc **complet** (préambule inclus) dans mermaid.live.
2. Vérifier l'aperçu entier, puis **Actions → PNG**.
3. Si du texte est tronqué : monter `fontSize` à `18px` ou les espacements.
