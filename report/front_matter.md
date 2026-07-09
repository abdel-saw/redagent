# Front-matter du mémoire

> Brouillon (RedAgent v2, mémoire PFE). Dédicace et remerciements sont des trames **à
> personnaliser** par l'auteur. Résumé/Abstract sont rédigés sur le fond. À convertir en LaTeX
> (pages liminaires, avant le sommaire).

---

## Dédicace

> *(à personnaliser — trame proposée)*

À ma famille, pour son soutien indéfectible tout au long de ces années d'études.

À toutes celles et ceux qui m'ont accompagné, de près ou de loin, dans la réalisation de ce
travail.

---

## Remerciements

> *(à personnaliser — trame proposée)*

Je tiens à exprimer ma profonde gratitude à mon encadrant, **Pr DABOUNOU**, pour sa
disponibilité, ses conseils éclairés et la rigueur qu'il a su m'inculquer tout au long de ce
projet de fin d'études.

Je remercie l'ensemble du corps enseignant de la filière **Ingénierie Informatique** pour la
qualité de la formation reçue, ainsi que les membres du jury qui me font l'honneur d'évaluer ce
travail.

Mes remerciements vont enfin à ma famille et à mes camarades de promotion, pour leurs
encouragements constants.

---

## Résumé

Les applications fondées sur les grands modèles de langage (LLM) sont déployées à un rythme
soutenu, exposant une surface d'attaque inédite — l'entrée du système est du langage naturel et
les instructions de confiance cohabitent avec des données hostiles. Le *red teaming* automatisé
s'impose, mais deux faiblesses méthodologiques récurrentes en fragilisent l'évaluation : une
**validation circulaire** (tests menés uniquement sur des cibles fabriquées par l'auteur) et un
**juge LLM jamais validé**, dont le verdict sert pourtant d'arbitre du succès.

Ce mémoire propose **RedAgent**, un agent de red teaming semi-autonome **léger, BYOK et
observable**, mappé sur l'**OWASP Top 10 for LLM Applications (2025)**, accompagné d'une
**méthodologie d'évaluation rigoureuse et indépendante de l'outil**. La contribution centrale est
le **découplage** d'un **oracle déterministe** — vérité-terrain objective du succès d'attaque, par
détection de flag/secret — et d'un **juge LLM** générique, dont la **fiabilité est mesurée** (et
non postulée) contre l'oracle puis contre une **vérité-terrain humaine** construite en aveugle
(*gold standard* anti-ancrage).

La démarche est validée sur des cibles **tierces** indépendantes (un CTF OWASP-LLM et le jeu
public *Gandalf* de Lakera, dont l'oracle de confirmation n'est pas écrit par l'auteur), brisant
la circularité. Les résultats montrent que **quatre juges LLM légers sur cinq** reproduisent
quasi parfaitement le jugement humain (κ de Cohen ≈ 0,97), qu'un modèle **spécialisé sûreté** est
au contraire le **pire juge** (il refuse mais ne reconnaît pas la vulnérabilité), et que l'**oracle
déterministe lui-même** peut avoir un angle mort, fonction du caractère discret du critère de
succès. Enfin, une **comparaison pré-enregistrée** à **PyRIT** (Microsoft) démontre que le même
oracle peut évaluer objectivement un framework tiers dans des conditions identiques : la
contribution n'est pas la force brute de l'attaque, mais l'**instrumentation tool-agnostic de la
mesure**.

**Mots-clés :** sécurité des LLM, red teaming, OWASP LLM Top 10, injection de prompt, fuite de
prompt système, oracle déterministe, juge LLM, validation, intervalle de confiance, κ de Cohen.

---

## Abstract

Applications built on large language models (LLMs) are being deployed at pace, exposing a novel
attack surface: the system's input is natural language, and trusted instructions share the
context window with hostile data. Automated *red teaming* has become essential, yet two recurring
methodological weaknesses undermine its evaluation: **circular validation** (testing only on
targets the author made vulnerable) and an **unvalidated LLM judge**, whose verdict nonetheless
arbitrates success.

This thesis presents **RedAgent**, a **lightweight, BYOK, observable** semi-autonomous
red-teaming agent mapped to the **OWASP Top 10 for LLM Applications (2025)**, together with a
**rigorous, tool-agnostic evaluation methodology**. The core contribution is the **decoupling** of
a **deterministic oracle** — an objective ground truth of attack success via flag/secret detection
— from a generic **LLM judge** whose **reliability is measured** (not assumed) against the oracle
and then against a blind **human gold standard**.

The approach is validated on independent **third-party** targets (an OWASP-LLM CTF and Lakera's
public *Gandalf* game, whose confirmation oracle is not authored by us), breaking circularity.
Results show that **four of five lightweight LLM judges** match human judgment almost perfectly
(Cohen's κ ≈ 0.97), that a **safety-tuned model** is in fact the **worst judge** (it refuses but
fails to recognise the vulnerability), and that the **deterministic oracle itself** can have a
blind spot depending on how discrete the success criterion is. Finally, a **pre-registered
comparison** with **PyRIT** (Microsoft) shows that the same oracle can objectively evaluate a
third-party framework under identical conditions: the contribution is not raw attack strength but
the **tool-agnostic instrumentation of measurement**.

**Keywords:** LLM security, red teaming, OWASP LLM Top 10, prompt injection, system prompt
leakage, deterministic oracle, LLM-as-a-judge, validation, confidence interval, Cohen's kappa.
