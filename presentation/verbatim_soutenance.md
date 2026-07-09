# Verbatim minuté — Soutenance RedAgent (~16 min)

> ⚠️ Mise à jour : le deck ouvre désormais chaque partie par un **carton
> intercalaire** (5 au total, ~3 s chacun) et comporte une diapo **28bis
> PyRIT × Gandalf** (~25 s). Ces ajouts décalent les `cumul` indiqués plus bas
> d'environ +40 s sur la fin ; vise donc ~16 min plein. Les cartons sont des
> respirations : on les passe vite.

> Débit visé ≈ 140 mots/min. Les timings sont indicatifs ; `cumul` = temps écoulé
> en fin de diapo. Les passages entre **[crochets]** sont à dire avec TES mots
> (surtout la phrase personnelle de la diapo 30). Marqueurs ⏱ = durée de la diapo.

---

## I · CONTEXTE & PROBLÉMATIQUE

> Le deck ouvre chaque partie par un **carton intercalaire** (gros chiffre romain).
> Le passer en ~3 s, muet ou avec la phrase de transition indiquée. L'intercalaire I
> arrive après le plan, juste avant la diapo « surface d'attaque ».

### Diapo 1 — Titre ⏱25s · cumul 0:25
« Madame, Monsieur les membres du jury, bonjour. Je vais vous présenter mon projet
de fin d'études : **RedAgent**. C'est à la fois un outil de *red teaming* pour les
applications fondées sur les grands modèles de langage, et — surtout — une
**méthodologie pour mesurer honnêtement** si une attaque a réussi. C'est ce
déplacement, de l'attaque vers la mesure, qui est le cœur de mon travail. »

### Diapo 2 — Plan ⏱20s · cumul 0:45
« Je suivrai cinq temps : d'abord le contexte et la faille de méthode que j'ai
voulu corriger ; ensuite l'outil RedAgent et sa conception ; puis le *pivot* de mon
projet ; le harnais d'évaluation ; et enfin les résultats, les limites et la
conclusion. »

> **Intercalaire I — Contexte & problématique** (~3 s) : « Commençons par le contexte. »

### Diapo 3 — Surface d'attaque ⏱30s · cumul 1:15
« Les applications LLM ont fait surgir une surface d'attaque d'un type nouveau.
La sécurité classique repose sur une frontière nette entre code et données. Une
application LLM n'a pas cette frontière : l'instruction de confiance — le prompt
système — et la donnée utilisateur, parfois hostile, **cohabitent dans la même
fenêtre de contexte**, en langage naturel. Rien, au niveau du modèle, ne les
distingue. C'est la racine des vulnérabilités propres aux LLM. »

### Diapo 4 — Trois obstacles ⏱30s · cumul 1:45
« Évaluer ces applications se heurte à trois obstacles. Le **non-déterminisme** :
une même attaque réussit une fois sur trois — on raisonne donc en taux et en
intervalles de confiance. L'**espace en langage naturel**, infini : il faut
automatiser. Et surtout, le **succès est souvent affaire de jugement** — « est-ce
une fuite ? » n'a pas toujours de réponse mécanique. D'où la tentation de confier
l'arbitrage à un autre LLM. Retenez ce dernier point : il revient bientôt. »

### Diapo 5 — OWASP ⏱30s · cumul 2:15
« Pour structurer le travail, je m'appuie sur le référentiel de fait : l'**OWASP
Top 10 for LLM Applications**. J'en retiens quatre classes, en rouge : celles qui
sont testables en boîte noire, via une API, et dont le succès est **objectivement
décidable** — injection de prompt, fuite d'information sensible, agentivité
excessive, fuite de prompt système. Ce périmètre n'est pas une commodité : il me
garantit une vérité-terrain sans ambiguïté. »

---

## II · REDAGENT — L'OUTIL ET SA CONCEPTION

> **Intercalaire II — RedAgent : l'outil et sa conception** (~3 s) : « Voyons d'abord l'outil lui-même. »

### Diapo 6 — Vision ⏱30s · cumul 2:45
« RedAgent, comme outil, est pensé pour être **réellement utilisé** : léger,
mono-conteneur ; *Bring Your Own Key*, les clés restent en mémoire ; observable, on
suit l'audit en direct ; et aligné OWASP. Là où PyRIT ou garak visent l'ingénieur
sécurité, RedAgent offre un point d'entrée accessible. C'est un outil
complémentaire, pas un concurrent. »

### Diapo 7 — Cas d'utilisation ⏱30s · cumul 3:15
« Côté conception de l'**outil** — ma première itération — un acteur unique :
l'auditeur. Tout gravite autour d'un cas pivot, « **Lancer un audit** », qui
*inclut* le **verdict du juge** : c'est le seul résultat exposé à l'utilisateur,
la sévérité des *findings* et le rapport. L'oracle, lui, n'est pas un usage
interactif : c'est l'instrument de ma seconde itération, la mesure de fiabilité —
j'y reviens dans un instant. »

### Diapo 8 — Architecture ⏱25s · cumul 3:40
« L'architecture est volontairement légère et sans build côté client : au back,
FastAPI servi par Uvicorn, LiteLLM pour l'accès multi-fournisseurs, httpx vers la
cible, Pydantic, et SQLite pour la persistance des audits ; au front, une interface
HTMX et Tailwind rendue par Jinja2, avec un flux SSE pour le suivi en direct. Le moteur se décompose en briques indépendantes
— et point important : ce sont les
**mêmes briques** qui servent à l'outil interactif et au harnais d'expériences. Ce
que je mesure est donc exactement ce que l'outil exécute. »

### Diapo 9 — Diagramme de classes ⏱25s · cumul 4:05
« La vue statique le confirme. On y voit les **quatre** modules d'attaque, dérivés
d'une base commune *graine-puis-mutation*. Et surtout l'`Oracle` et le `Juge`
apparaissent comme **deux classes distinctes** : elles opèrent sur le même couple,
mais ne se référencent jamais. »

### Diapo 10 — Diagramme de séquence ⏱40s · cumul 4:45
« Et voici la vue dynamique, un audit tel que l'auditeur le déclenche. Pour chaque
tentative, l'attaquant produit un prompt, l'adaptateur interroge la cible en boîte
noire, et le **juge** rend le verdict qui alimente les *findings*. Remarquez :
l'oracle n'intervient **pas** ici — l'audit interactif s'appuie sur le seul juge.
C'est ma seconde itération qui fera intervenir l'oracle, en lui soumettant *les
mêmes* tuples journalisés, en parallèle du juge ; et c'est cette confrontation, pas
l'audit lui-même, qui me permettra de mesurer le juge. »

### Diapo 11 — Modules d'attaque ⏱30s · cumul 5:15
« Concrètement, chaque module part d'une **graine générique** — par exemple
« énumère ta configuration » pour la fuite d'information — que le LLM attaquant
**mute** ensuite à partir des réponses observées. Le point crucial : ces graines
sont génériques par classe, **jamais taillées pour une cible précise**. C'est ce
qui me permettra de distinguer, à l'analyse, ce qui relève du talent de l'agent de
ce qui relève d'une simple fuite de la cible. »

### Diapo 12 — UI configurer ⏱20s · cumul 5:35
« Voici l'outil en action. D'abord la configuration : on saisit l'endpoint, le
gabarit de corps de requête, le chemin d'extraction, et on coche les modules. On
parle à la cible **telle qu'elle tourne** — je ne la modifie jamais. »

### Diapo 13 — UI modèles/budget ⏱20s · cumul 5:55
« Ensuite les modèles attaquant et juge, en *Bring Your Own Key* : l'auditeur
fournit ses clés, conservées en mémoire seulement. Et un plafond de dépense en
dollars : le coût est borné. »

### Diapo 14 — UI live ⏱20s · cumul 6:15
« Une fois lancé, l'audit se suit **en direct** : chaque tentative, chaque verdict,
chaque *finding* s'affiche par flux d'événements, sans rechargement.
L'observabilité est immédiate. »

### Diapo 15 — Rapport synthèse ⏱20s · cumul 6:35
« À la fin, un rapport HTML autonome : d'abord une synthèse exécutive des
*findings*, prête à être archivée ou partagée. »

### Diapo 16 — Rapport finding ⏱20s · cumul 6:55
« Et le détail de chaque *finding* : le prompt, la réponse de la cible, le verdict.
Tout est tracé et reproductible. Voilà pour l'outil. »

---

## III · LE PIVOT

> **Intercalaire III — Le pivot : de l'attaque à la mesure** (~3 s) : « J'en viens maintenant au cœur du travail. »

### Diapo 17 — La faille ⏱35s · cumul 7:30
« Mais — et c'est le tournant de mon projet — cet outil, seul, portait une **faille
de méthode**. Ma première version cherchait à « rivaliser » avec les frameworks
existants. Or elle se validait en rond, de deux façons. **Un** : une validation
circulaire — je ne testais l'outil que sur des cibles que j'avais moi-même rendues
vulnérables. **Deux** : un juge LLM jamais validé — le verdict de succès venait
d'un modèle dont je n'avais jamais mesuré la fiabilité. Le juge était l'oracle
implicite, sans contrôle. »

### Diapo 18 — Pivot ⏱25s · cumul 7:55
« J'ai donc fait un choix : abandonner l'ambition « d'attaquer plus fort » pour
celle de « **mesurer juste** ». L'objectif n'est plus de gagner, mais
d'instrumenter honnêtement le succès. Tout ce qui suit découle de cette décision. »

### Diapo 19 — La contribution ⏱45s · cumul 8:40
« Ma contribution centrale tient en une idée : **découpler** l'oracle et le juge.
L'**oracle** détecte de façon déterministe la capture — un flag, un secret,
éventuellement confirmé par une étape de soumission. Il ne dépend d'aucun LLM, il
est reproductible : c'est ma **vérité-terrain objective**. Le **juge**, lui, est un
LLM qui rend un verdict générique à partir du seul couple (prompt, réponse), sans
voir le flag — c'est l'instrument utilisable sur une cible *sans* flag. Les deux
sont indépendants. Et c'est précisément parce qu'ils sont indépendants que je peux
enfin **mesurer le juge** : contre l'oracle, puis contre un jugement humain. »

---

## IV · LE HARNAIS D'ÉVALUATION

> **Intercalaire IV — Le harnais d'évaluation (V2)** (~3 s) : « Place au harnais de mesure. »

### Diapo 20 — Factorisation ⏱30s · cumul 9:10
« Ce découplage factorise la mesure en deux expériences. L'**Exp. 1** mesure
l'efficacité de l'attaquant, le succès étant décidé par l'**oracle**, jamais par le
juge ; chaque tentative est journalisée. L'**Exp. 2** mesure la fiabilité du juge :
je **rejoue** les tuples déjà enregistrés à travers un panel de juges, sans lancer
une seule nouvelle attaque — le coût reste borné. »

### Diapo 21 — Logique de l'oracle ⏱25s · cumul 9:35
« Voici la logique de l'oracle : il détecte un motif de secret, et si nécessaire le
confirme par une étape tierce — par exemple en resoumettant un mot de passe à un
endpoint de validation. Déterministe, reproductible, sans aucun LLM. »

### Diapo 22 — Preuve de l'oracle ⏱30s · cumul 10:05
« Mais avant d'utiliser cet instrument, je le **prouve**. Un test dédié vérifie
qu'il est sensible — il se déclenche sur les charges connues-bonnes — et
spécifique : sur un **leurre**, une fausse valeur `JWT_SECRET`, il reste négatif,
il ne se laisse pas tromper. Les douze cas passent. **On valide l'instrument avant
de mesurer.** Un mot sur le périmètre, si on me pose la question : l'outil couvre
quatre classes, mais la matrice d'attaque n'en tourne que trois. LLM01 ne sert
qu'ici, à valider l'oracle — sa détection de flag est identique à celle de LLM07 ;
il reste hors matrice non par absence de flag, mais parce qu'un succès *live*
demanderait une session authentifiée et un payload externe, que le harnais
n'automatise pas. »

### Diapo 23 — Exp. 1 ⏱45s · cumul 10:50
« Exp. 1, l'efficacité de l'attaquant. Premier constat d'honnêteté : les taux sont
faibles et les intervalles de confiance larges — **il n'y a pas de palmarès**.
Mais deux analyses comptent. D'abord, je sépare le **talent** de la **variance** :
quand c'est la cible qui fuit une graine écrite à la main, je ne le porte pas au
crédit de l'agent. Ensuite, une **ablation** : si je coupe les graines, gpt-4o-mini
passe de 4 sur 15 à **zéro sur 15**. Son efficacité reposait sur l'échafaudage.
Cette ablation transforme « l'agent est autonome » d'une affirmation en une
mesure. »

### Diapo 24 — Exp. 2 ⏱50s · cumul 11:40
« Exp. 2, le juge contre une vérité-terrain **humaine**, établie en aveugle. Trois
enseignements. D'abord, quatre juges sur cinq sont quasi indiscernables de l'humain
— un kappa d'environ 0,97. J'insiste : à ce petit échantillon, ces quatre sont
**interchangeables**, je ne les classe pas. Ensuite, le modèle spécialisé en
*sûreté* est le **pire** juge : il refuse, mais ne reconnaît pas la vulnérabilité.
Enfin — et c'est ma trouvaille — j'ai découvert que **mon propre oracle a un angle
mort** : un cas, le id60, où une vraie fuite de configuration se produit sans le
token exact. Un bon juge la rattrape ; l'oracle strict, non. Capture de flag n'est
pas vulnérabilité. »

### Diapo 25 — Anti-ancrage ⏱30s · cumul 12:10
« Un mot sur la méthode de ce jugement humain, car c'est un point sensible. Je l'ai
rendu dans un classeur où l'oracle et les verdicts des machines sont **masqués**.
Ainsi, ma vérité-terrain n'est pas ancrée sur les machines qu'elle sert justement à
évaluer. C'est un garde-fou contre le biais d'ancrage. »

### Diapo 26 — Gandalf Exp. 1 ⏱30s · cumul 12:40
« Pour briser la circularité, je rejoue tout sur une cible que je n'ai **pas**
fabriquée : Gandalf, de Lakera, dont l'oracle de confirmation appartient à
l'éditeur, pas à moi. En efficacité, l'attaquant générique transfère sur les
niveaux faible et moyen, et bute sur le plus dur — un plafond externe honnête. »

### Diapo 27 — Gandalf Exp. 2 ⏱35s · cumul 13:15
« Et en fiabilité, sur cette cible indépendante, l'oracle obtient un kappa de
**1,00** — aucun angle mort. Pourquoi cette différence avec PromptMe ? Parce que le
critère est **discret** : un mot de passe unique fait un flag quasi parfait, là où
« information sensible » crée une zone grise. **C'est mon enseignement le plus
transférable** : la fiabilité d'un oracle dépend du caractère discret de son
critère. »

### Diapo 28 — PyRIT ⏱45s · cumul 14:00
« Dernier palier : une comparaison à PyRIT, le framework de Microsoft. Le protocole
a été **figé à l'avance** : même attaquant, même oracle, même budget ; seul
l'orchestrateur diffère. À première vue les chiffres me flattent — 4 sur 15 contre
0 sur 15. **Mais cette lecture serait fausse** : les intervalles de confiance se
recouvrent, donc, selon ma règle pré-enregistrée, **aucune différence n'est
déclarable**, et je refuse de conclure que RedAgent bat PyRIT. Le vrai acquis est
ailleurs : un même oracle a pu mesurer équitablement deux outils différents. C'est
la preuve que mon instrument est indépendant de l'outil. »

### Diapo 28bis — PyRIT × Gandalf ⏱25s · cumul 14:25
« Et ce n'est pas isolé à PromptMe. Sur la seconde cible tierce, Gandalf, le
**même oracle de Lakera** classe les deux outils : RedAgent 6 sur 9, PyRIT 4 sur 9.
Là encore, les intervalles de confiance se recouvrent — je ne déclare **aucune**
différence. Ce qui compte n'est pas le score, c'est qu'un seul et même oracle a su
mesurer équitablement deux orchestrateurs sur deux cibles. »

---

## V · CLÔTURE

> **Intercalaire V — Résultats, limites & conclusion** (~3 s) : « Je termine par les limites et la conclusion. »

### Diapo 29 — Limites ⏱35s · cumul 14:35
« Mes limites, je les assume plutôt que de les masquer. Les échantillons sont
petits — d'où l'interchangeabilité des juges. Mon *gold standard* repose sur un
annotateur unique, moi : la première amélioration sera une double adjudication avec
accord inter-annotateurs. Et mes deux cibles sont des jeux, conçus pour être
résolus : c'est ce qu'il fallait pour briser la circularité, mais cela borne la
portée. Il faut donc distinguer la **méthode**, qui transfère, des **chiffres
absolus**, qui non. »

### Diapo 30 — Conclusion ⏱35s · cumul 15:10
« En conclusion : ma contribution n'est pas la force de l'attaque, c'est
**l'instrument de mesure** — réutilisable au-delà de RedAgent. J'ai brisé la
circularité avec deux cibles tierces, validé le juge contre l'humain, prouvé mon
oracle *et* trouvé son angle mort, et démontré une mesure indépendante de l'outil.
**[Et personnellement — à dire avec tes mots — ce projet m'a moins appris à
attaquer qu'à douter de mes propres résultats : un résultat n'a de valeur que si
l'on a sérieusement tenté de le réfuter.]** »

### Diapo 31 — Merci ⏱15s · cumul 15:25
« Je vous remercie de votre attention, et je suis à votre disposition pour vos
questions. »

---

## Réserves de temps (si tu dépasses)
- Diapos **12 à 16** (UI/rapport) : compressibles à ~12 s chacune en disant juste
  « configurer / suivre / rapporter » → gagne ~40 s.
- Diapos **8 et 21** : une phrase suffit → gagne ~20 s.
- Ne jamais raccourcir : **10 (séquence), 19 (découplage), 24 (Exp.2), 28 (PyRIT)**
  — ce sont tes temps forts.

## Questions probables — réponses prêtes (annexes)
1. **Annotateur unique ?** → critères pré-spécifiés + anti-ancrage ; 1er ajout =
   double adjudication + kappa inter-annotateurs (annexe A1).
2. **Oracle aveugle sur LLM02 → sous-comptage ?** → erreur conservatrice
   (précision 1,00) ⇒ mes taux sont un **plancher** (annexe A2).
3. **Pourquoi un seul attaquant chez PyRIT ?** → pour isoler l'orchestrateur ;
   deux attaquants ré-introduiraient la variable « force du LLM ».
