# Rapport PFE — RedAgent v2 (LaTeX)

Projet LaTeX du mémoire, calqué sur le gabarit FSTS/UH1 du rapport précédent.

## Compilation
- **Overleaf** : déposer le dossier, compiler avec **pdfLaTeX** (compiler 2 fois
  pour la table des matières / les références croisées). `main.tex` est la racine.
- **Local** : `latexmk -pdf main.tex` (ou `pdflatex main.tex` deux fois).

## Structure
- `main.tex` — préambule + ordre des inclusions.
- `chapitres/` — page de titre, front-matter, introduction, chapitres I–IV, conclusion, webographie.
- `figures/` — logos (déjà présents) + figures à générer.

## Avant de compiler proprement
1. **Générer les figures Mermaid** : suivre `figures.md` (3 diagrammes →
   `fig_architecture.png`, `fig_expflow.png`, `fig_oracle.png`).
2. **Captures d'écran** : suivre `plan_demo.md` (UI V1 + harnais V2).
   *Tant qu'une image manque, LaTeX affiche un cadre vide « file not found » mais
   compile quand même si on remplace temporairement les `\includegraphics` ; le
   plus simple est de produire les figures avant la version finale.*
3. **Réécriture personnelle** : voir `A_REECRIRE_TOI_MEME.md` — les passages
   marqués `% >>> À RÉÉCRIRE` dans les `.tex` (dédicace, remerciements, intro,
   conclusion, encadrés « retour d'expérience »).

## Identité (page de titre)
SAWADOGO S Abdel K N — Cycle Ingénieur, Ingénierie Informatique — encadrant
Pr DABOUNOU — FST Settat / Université Hassan 1er — 2025/2026.
