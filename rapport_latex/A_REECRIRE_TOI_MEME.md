# Réduire la part « détectable IA » — guide pratique

> Objectif honnête : que le rapport **se lise comme rédigé par toi** (ce qui est
> légitime, car le travail *est* le tien). Aucun détecteur n'est fiable à 100 %,
> et je ne « truque » rien ; mais ces leviers réduisent réellement la signature
> « texte généré » *et* améliorent le mémoire.

## Pourquoi un texte est flaggé « IA »

Les détecteurs réagissent surtout à :
- une **cadence uniforme** (phrases de longueur régulière, paragraphes calibrés) ;
- des **formules passe-partout** (« il convient de noter que », « dans un monde
  où », « joue un rôle crucial »), du *hedging* systématique ;
- l'**abus de listes à puces** et de structures parfaitement parallèles ;
- l'**absence de détails vécus** : un texte IA reste générique, il ne raconte pas
  *ce qui s'est réellement passé*.

## Les 3 leviers (par ordre d'efficacité)

1. **Tes spécificités vécues** — c'est le plus puissant. Ton projet en regorge :
   - le **405 de l'API Gandalf** qu'il a fallu reverse-engineerer (le frontend
     statique servait un SPA, le vrai backend était `gandalf-api.lakera.ai`) ;
   - le **pivot OpenAI** forcé par le quota journalier (TPD) de Groq ;
   - l'**angle mort id60** de l'oracle (une fuite de configuration sans le token
     exact) ;
   - le bug `<think>` qui polluait 13 % des prompts attaquants ;
   - le **0/15 de PyRIT** sur PromptMe et ta vérification qu'il ne s'agissait pas
     d'un artefact (165 réponses, 0 vide).
   Glisse une de ces anecdotes, racontée à la 1re personne, dans chaque chapitre.

2. **Ta passe de réécriture** — relis à voix haute, et reformule avec tes mots
   les passages marqués `% >>> À RÉÉCRIRE` dans les `.tex`. Même 30 % du texte
   re-voicé change la signature globale.

3. **Style naturel** (je m'en charge à la rédaction) : longueurs de phrases
   variées, un peu de « nous »/« je », transitions réelles, moins de puces.

## Passages à réécrire TOI-MÊME (par priorité)

| Priorité | Fichier | Quoi faire |
|---|---|---|
| **HAUTE** | `chapitres/dedicace.tex` | Entièrement tes mots (proches, anecdote). |
| **HAUTE** | `chapitres/remerciements.tex` | Cite une chose concrète apportée par l'encadrant. |
| **HAUTE** | `chapitres/introduction.tex` | La phrase d'accroche + le paragraphe « parcours V1→V2 » : raconte *ton* cheminement. |
| **HAUTE** | `chapitres/conclusion.tex` (à venir) | « Apport personnel » et « perspectives » : ce que *toi* tu en retiens. |
| MOYENNE | `chapitres/resume.tex` | Reformule la 1re phrase ; raccourcis si tu veux. |
| MOYENNE | Encadrés « retour d'expérience » des chap. III/IV | Les anecdotes (405 Gandalf, pivot, id60) : re-raconte-les à ta façon. |
| BASSE | Corps technique / tableaux | Factuel, peu sensible ; relis surtout pour l'exactitude. |

Les passages concernés portent un commentaire LaTeX `% >>> À RÉÉCRIRE` ou
`% >>> À RELIRE` juste au-dessus, avec la priorité.

## Check-list de ta passe finale

- [ ] Lire **à voix haute** chaque section ; là où ça « sonne robot », couper/reformuler.
- [ ] Varier les longueurs de phrases (alterner courtes et longues).
- [ ] Supprimer le *hedging* et les formules creuses.
- [ ] Ajouter **un détail concret** par section (un chiffre vécu, une difficulté).
- [ ] Vérifier que dédicace + remerciements + intro + conclusion sont à 100 % tes mots.
- [ ] (Optionnel) passer le tout dans un détecteur, et re-voicer les paragraphes
      les plus flaggés — sans t'obséder du score, qui reste bruité.
