# Chapitre I — Contexte et problématique

> Brouillon de rédaction (RedAgent v2, mémoire PFE). À relire/amender et convertir en LaTeX.
> Les références (Auteur, année) sont à consolider dans la webographie finale.

## 1. Contexte général

Les grands modèles de langage (LLM) sont passés en quelques années du laboratoire à la
production : assistants conversationnels, génération augmentée par récupération (RAG), et
surtout **agents** capables d'appeler des outils, d'interroger des bases ou d'exécuter des
actions. Cette intégration rapide dans des applications réelles crée une **surface d'attaque
inédite** : l'entrée du système est du **langage naturel**, le comportement est **non
déterministe**, et les instructions de confiance (prompt système) cohabitent, dans la même
fenêtre de contexte, avec des données potentiellement hostiles fournies par l'utilisateur.

Contrairement à la sécurité applicative classique — où les frontières (code/données, requête/
réponse) sont nettes — une application LLM **n'a pas de séparation forte** entre instructions et
données. C'est la source d'une famille de vulnérabilités spécifiques (injection de prompt, fuite
du prompt système, agentivité excessive) que les contrôles traditionnels (pare-feu, validation
de schéma) ne couvrent pas.

## 2. Problématique de sécurité des applications LLM

Tester la sécurité d'une application LLM est difficile pour trois raisons :

1. **Non-déterminisme** : une même attaque réussit un essai sur trois ; le succès est
   *probabiliste*, pas binaire — il faut raisonner en taux et en intervalles de confiance.
2. **Espace d'attaque en langage naturel** : infiniment plus vaste qu'un jeu de payloads SQL ou
   XSS ; les attaques se reformulent, se traduisent, s'encodent.
3. **Définition du succès ambiguë** : « la réponse est-elle une fuite ? » est souvent une
   question de jugement. D'où la tentation d'utiliser un **autre LLM comme juge** — dont la
   fiabilité, elle, est rarement établie.

Le **red teaming** — l'attaque offensive contrôlée d'un système pour en révéler les faiblesses —
s'impose donc comme la pratique centrale de la sécurité des LLM. Vu l'ampleur de l'espace
d'attaque, il doit être **automatisé**, au moins partiellement.

## 3. Le problème adressé par ce PFE

Deux manques motivent ce travail.

**(a) Un manque d'accessibilité.** Les frameworks de red teaming existants (cf. chapitre II) sont
puissants mais **lourds** : courbe d'apprentissage, configuration experte, dépendances. Il
manque un outil **léger, mono-conteneur, BYOK** (l'utilisateur fournit ses propres clés de
modèle, conservées en mémoire uniquement), **observable** (l'attaque se suit en direct) et
**utilisable par un public non expert**, qui mappe ses tests sur un référentiel reconnu
(OWASP LLM Top 10).

**(b) Un manque de rigueur dans l'évaluation des outils eux-mêmes.** C'est le verrou central.
La première version de ce projet (V1) souffrait de deux faiblesses méthodologiques, fréquentes
dans le domaine :
- **Validation circulaire** : l'outil n'était évalué que sur des cibles que l'auteur avait
  lui-même rendues vulnérables — aucune valeur démontrée face à une référence indépendante.
- **Juge LLM jamais validé** : tous les résultats reposaient sur le verdict d'un juge LLM dont
  la fiabilité n'avait jamais été mesurée. Le juge était l'oracle implicite, sans contrôle.

## 4. Objectif et contributions

Ce PFE recentre le projet : la contribution n'est **pas** la force brute de l'attaquant (ne pas
chercher à « battre » les frameworks de référence), mais l'**instrumentation de la mesure**.
Deux livrables :

1. **RedAgent** — un agent de red teaming semi-autonome, léger, BYOK, observable, mappé OWASP,
   utilisable par un non-expert.
2. **Une méthodologie d'évaluation rigoureuse et *tool-agnostic*** : un **oracle déterministe**
   (vérité-terrain objective du succès, par détection de flag/secret) **découplé** d'un **juge
   LLM** dont la fiabilité est **mesurée** contre une vérité-terrain humaine, puis utilisée pour
   évaluer **n'importe quel** outil (RedAgent comme un framework tiers) dans les mêmes conditions.

Ces deux livrables répondent frontalement aux deux manques du §3 : accessibilité d'une part,
rigueur de la mesure d'autre part.

## 5. Démarche et plan du mémoire

Le travail suit une démarche **par paliers de revendication** (tiers), chacun validé et testé
avant le suivant : fondations méthodologiques (oracle/juge + gold standard humain), validation
sur une seconde cible **tierce** indépendante, puis **comparaison pré-enregistrée** à un
framework de référence (PyRIT). Cette progression garantit que chaque affirmation du mémoire est
**adossée à une mesure**, et non postulée.

Le mémoire est organisé comme suit : le **chapitre II** dresse l'état de l'art (taxonomie OWASP,
méthodes d'attaque automatisées, outils, bancs d'évaluation et verrou de la mesure) ; le
**chapitre III** présente la conception (architecture, oracle découplé, harnais d'expériences) ;
le **chapitre IV** détaille la réalisation et les expériences (efficacité de l'attaquant,
fiabilité du juge, comparaison tierce) ; la conclusion discute la portée et les limites.
