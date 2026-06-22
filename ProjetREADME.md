# EPITA 2026 — Intelligence Symbolique

## Liste des sujets de projet

Ce document presente les sujets de projet pour le cours d'Intelligence Symbolique (SCIA). Chaque sujet inclut une description detaillee, des references academiques et pratiques, des liens vers les notebooks CoursIA pertinents, et les technologies a utiliser.

> **Consignes de choix** : Chaque groupe doit forker ce depot et creer un dossier pour son projet contenant le code source, un notebook explicatif OU une UI/demo fonctionnelle (au choix), et les slides de soutenance. Les livraisons se font via des pull requests regulieres.
>
> **Inscription** : Inscrivez-vous et choisissez votre sujet dans la [feuille d'inscription des projets de groupe](https://docs.google.com/spreadsheets/d/1xmxEJcOyTegIhjW8LEqYewkCJ7m8_vK4/edit?usp=sharing). Chaque etudiant renseigne sa ligne (onglet `eleves`, colonne *Sujet Projet IA Symbolique*, menu deroulant) ; le catalogue complet des sujets est sur l'onglet `Sujets`.

### Du cours de Programmation par Contraintes a l'Intelligence Symbolique

Ce cours d'Intelligence Symbolique **ne prolonge pas** le cours de Programmation par Contraintes. Il ouvre un espace conceptuel different :

| Aspect | Programmation par Contraintes | Intelligence Symbolique |
|--------|-------------------------------|------------------------|
| **Questions** | Comment resoudre un probleme combinatoire ? | Comment representer et raisonner sur des connaissances ? |
| **Paradigme** | Espaces de recherche, propagation, optimisation | Logiques, argumentation, ontologies, preuves formelles |
| **Solveur** | CP-SAT, SAT, SMT comme boites noires | Z3/Lean comme assistants de raisonnement |
| **Sortie** | Une solution optimale ou faisable | Une preuve, un argument, une ontologie, un plan |
| **Evaluation** | Performance (temps, optimalite) | Correction (validite logique, coherence) |

Les solveurs SAT/SMT (Z3, PySAT) apparaissent dans les deux cours, mais avec des usages differents : en PC, ce sont des moteurs d'optimisation ; en IS, ce sont des verificateurs de proprietes logiques, des outils de preuve, ou des backend pour le raisonnement formel. Les sujets de ce depot exploitent SAT/SMT comme couches de verification au service de taches symboliques de plus haut niveau (demonstration automatique, model checking, verification de smart contracts, encodage de theoremes d'impossibilite).

---

## Modalites du projet

### Taille des groupes

| Taille | Bonus/Malus |
|--------|-------------|
| 3 personnes | Standard |
| 2 personnes | +1 point |
| 1 personne (solo) | +3 points |
| 4 personnes | -1 point |

### Soutenance — Evaluation collegiale

La soutenance finale est evaluee de maniere **collegiale** (pairs + enseignants). Chaque groupe est note sur **4 criteres** (0-10 chacun) :

| Critere | Description |
|---------|-------------|
| **Qualite de la presentation** | Communication, clarte, pedagogie, qualite des slides, demonstrations |
| **Qualite theorique** | Principes utilises, classes d'algorithmes, contexte historique, explication des performances et limitations |
| **Qualite technique** | Livrables (code, notebook, UI), qualite du code, commits Git, demonstrations, resultats, perspectives |
| **Organisation** | Planning, repartition des taches, collaboration, activite Git, documentation |

**Note finale = somme des 4 criteres / 2 (echelle /20), ajustee du bonus/malus taille de groupe.**

### Livrables attendus

- **Code source** documente dans un sous-dossier dedie (`groupe-XX-nom-sujet/`)
- **Notebook Jupyter** explicatif avec analyse et visualisations **OU** **UI/demo fonctionnelle** (au choix — un notebook tres complet peut tenir lieu de demo, et inversement)
- **Slides de soutenance** (PDF ou lien)
- **Pull Request** soumise au plus tard **2 jours avant la soutenance**

### Echeances

- **Date de soutenance** : en cours de confirmation avec la scolarite
- **Deadline PR** : 2 jours avant la soutenance

---

## Ressources communes a tous les sujets

### Solveurs et outils
- **Z3 SMT Solver** : solveur SMT de reference pour verification formelle et raisonnement symbolique. [Documentation](https://z3prover.github.io/api/html/namespacez3py.html), [Tutoriel Python](https://ericpony.github.io/z3py-tutorial/guide-examples.htm)
- **Google OR-Tools CP-SAT** : solveur CP pour problemes combinatoires. [Documentation](https://developers.google.com/optimization/cp/cp_solver)
- **CVC5 SMT Solver** : solveur SMT alternatif. [Documentation](https://cvc5.github.io/)
- **TweetyProject** : librairie Java pour logique formelle, argumentation et raisonnement probabiliste. [Documentation](https://tweetyproject.org/)

### Frameworks et plateformes
- **Semantic Kernel** : orchestration d'agents IA avec plugins. [GitHub](https://github.com/microsoft/semantic-kernel)
- **Fast Downward** : planificateur PDDL de reference. [Site](https://www.fast-downward.org/)
- **Solidity / Foundry** : developpement et test de smart contracts. [Documentation](https://docs.soliditylang.org/)
- **PySAT** : interface Python pour solveurs SAT. [Documentation](https://pysathq.github.io/)
- **QuantConnect Lean** : plateforme de backtest et trading algorithmique (partenariat educatif sponsorise par Jared Broad, CEO QC). [Site](https://www.quantconnect.com/), [Documentation](https://www.quantconnect.com/docs/)

### Notebooks du cours CoursIA
Les notebooks suivants sont disponibles dans le depot CoursIA ([jsboige/CoursIA](https://github.com/jsboige/CoursIA)) et constituent des prerequis ou des points de depart pour les projets :

#### Demonstration automatique et typage dependant (Lean 4)
- **SymbolicAI/Lean/** : 12 notebooks — Lean-1 (Setup), Lean-2 (Dependent Types), Lean-3 (Propositions & Proofs), Lean-4 (Quantifiers), Lean-5 (Tactics), Lean-6 (Mathlib), Lean-7 (LLM Integration), Lean-8 (Agentic Proving), Lean-9 (Semantic Kernel Multi-Agents), Lean-10 (LeanDojo), Lean-11 (Neural Theorem Proving)

#### Logique formelle, SAT/SMT et solveurs
- **SymbolicAI/Linq2Z3.ipynb** : Z3 SMT Solver en C#
- **SymbolicAI/OR-tools-Stiegler.ipynb** : OR-Tools CP en C#
- **Sudoku/** : 18 notebooks couvrant Sudoku avec multiples solveurs (backtracking, DLX, GA, SA, PSO, Norvig, OR-Tools, Choco, Z3, BDD, neural, LLM)

#### TweetyProject — Logique et Argumentation
- **SymbolicAI/Tweety/** : 11 notebooks — Tweety-1 (Setup), Tweety-2 (Basic Logics), Tweety-3 (Advanced Logics), Tweety-4 (Belief Revision/AGM), Tweety-5 (Abstract Argumentation/Dung), Tweety-6 (Structured Argumentation/ASPIC+), Tweety-7a (Extended Frameworks), Tweety-7b (Ranking & Probabilistic), Tweety-8 (Agent Dialogues), Tweety-9 (Preferences)

#### Web Semantique et Graphes de Connaissances
- **SymbolicAI/SemanticWeb/** : 13 notebooks — SW-1 (Setup C#/Python), SW-2 (RDF), SW-3 (Graph Operations), SW-4 (SPARQL), SW-5 (Linked Data), SW-6 (RDFS), SW-7 (OWL), SW-8 (SHACL), SW-9 (JSON-LD), SW-10 (RDF*), SW-11 (Knowledge Graphs), SW-12 (GraphRAG), SW-13 (Reasoners)

#### Smart Contracts et Blockchain
- **SymbolicAI/SmartContracts/** : 27 notebooks (SC-0 a SC-26) — cypherpunk, Solidity, Foundry, ERC-20/721, DeFi, DAO Governance, Account Abstraction, LLM-assisted contracts, fuzz testing (SC-13), formal verification (SC-14), ZKP (SC-15), homomorphic encryption (SC-16), voting, Vyper, Bitcoin Script, Move/Sui, Solana/Anchor, cross-chain, deployment

#### Analyse d'Argumentation (Agentic)
- **SymbolicAI/Argument_Analysis/** : 7 notebooks — Agentic-0 (Init), Agentic-1 (Informal Argument Agent), Agentic-2 (Planning-Based Agent), Agentic-3 (Orchestration multi-agent)

#### Planification
- **SymbolicAI/Planners/** : 12 notebooks — Planners-1 (Intro), Planners-2 (PDDL), Planners-3 (State Space), Planners-4 (Fast Downward), Planners-5 (Heuristics), Planners-6 (Domains), Planners-7 (OR-Tools), Planners-8 (Temporal), Planners-9 (HTN), Planners-10 (LLM Planning), Planners-11 (Unified Planning), Planners-12 (LOOP)

#### Theorie des Jeux et Choix Social
- **GameTheory/** : 27 notebooks — forme normale, equilibres de Nash, zero-sum/minimax, evolution & trust, forme extensive, jeux combinatoires, induction, jeux bayesiens, reputation, information imparfaite/CFR, jeux cooperatifs/Shapley, mechanism design, choix social (Arrow SAT/Z3), multi-agent RL

#### Recherche et Metaheuristiques
- **Search/Part1-Foundations/** : 11 notebooks — StateSpace, uninformed, A*/heuristiques, local search, GA, adversarial/minimax, MCTS, Dancing Links, PL, automates symboliques, metaheuristiques

#### Programmation par Contraintes
- **Search/Part2-CSP/** : 9 notebooks — CSP-1 (Fondamentaux), CSP-2 (Consistency), CSP-3 (Advanced), CSP-4 (Scheduling), CSP-5 (Optimization), CSP-6 (Hybridation CP+SAT, LLM+CSP), CSP-7 (Soft Constraints), CSP-8 (Temporal CSP), CSP-9 (Distributed CSP)
- **Search/Applications/CSP/** : 11 notebooks — N-Queens, Graph Coloring, Nurse Scheduling, Job-Shop, Timetabling, Minesweeper, Wordle, MiniZinc, Picross, Sports Scheduling, Crossword
- **Search/Applications/Hybrid/** : 7 notebooks — Edge Detection, Portfolio Optimization, Connect Four, TSP Metaheuristics, VRP Logistics

#### Raisonnement Probabiliste et Decision

- **Research/** : 20 notebooks — Infer.NET (programmation probabiliste), melanges gaussiens, graphes de facteurs, reseaux bayesiens, modeles de Markov caches, LDA, crowdsourcing, recommandation, reseaux de decision, MDP/bandits/POMDP, TrueSkill, IRT

#### Reinforcement Learning

- **RL/** : 6 notebooks — MDP, Q-learning, DQN, policy gradient, multi-agent RL (NFSP, PSRO), Stable Baselines3, Gym wrappers, HER

#### Trading Algorithmique (QuantConnect)

- **QuantConnect/Python/** : 40+ notebooks — QC-Py-01 a QC-Py-34 couvrant la plateforme, backtesting, indicateurs techniques, modeles alpha, ML (classification, regression, LSTM, Transformer, RL DQN/PPO/SAC), detection de regimes, LLM trading signals, et paper trading Binance/IBKR

---

## Index des Sujets

### Categorie A : Demonstration Automatique et Typage Dependant (Lean 4)

| # | Sujet | Difficulte |
|---|-------|------------|
| [A1](#a1--preuve-formelle-dalgorithme-par-lean-4) | Preuve formelle d'algorithme par Lean 4 | 3/5 |
| [A2](#a2--agent-llm-assiste-pour-la-preuve-formelle) | Agent LLM-assiste pour la preuve formelle | 4/5 |
| [A3](#a3--theoreme-darrow-par-preuve-automatisee-satz3lean) | Theoreme d'Arrow par preuve automatisee (SAT/Z3/Lean) | 5/5 |
| [A4](#a4--bibliotheque-de-preuves-mathlib--extensions) | Bibliotheque de preuves Mathlib — extensions | 3/5 |
| [A5](#a5--mariages-stables-gale-shapley--preuve-formelle-et-extensions-en-lean-4) | Mariages stables Gale-Shapley : preuve formelle et extensions en Lean 4 | 3/5 |
| [A6](#a6--preuve-de-lexistence-de-nash-par-point-fixe-en-lean-4) | Preuve de l'existence de Nash par point fixe en Lean 4 | 5/5 |

### Categorie B : Logique Formelle, SAT et Demonstration Automatique

| # | Sujet | Difficulte |
|---|-------|------------|
| [B1](#b1--resolution-automatique-de-theoremes-par-sat) | Resolution automatique de theoremes par SAT | 3/5 |
| [B2](#b2--synthese-de-programmes-par-programming-by-sketching) | Synthese de programmes par Programming-by-Sketching | 4/5 |
| [B3](#b3--model-checking-de-protocoles-de-communication) | Model checking de protocoles de communication | 3/5 |
| [B4](#b4--resolution-de-puzzles-logiques-par-smt) | Resolution de puzzles logiques par SMT | 2/5 |
| [B5](#b5--demonstration-automatique-en-geometrie) | Demonstration automatique en geometrie | 4/5 |
| [B6](#b6--programmation-par-ensembles-de-reponses-asp-avec-clingo) | Programmation par ensembles de reponses (ASP) avec Clingo | 3/5 |
| [B7](#b7--resolution-de-problemes-pspace-par-qbf-quantified-booleans) | Resolution de problemes PSPACE par QBF (Quantified Booleans) | 3/5 |
| [B8](#b8--solveur-satsmt-certifiant--certificats-unsat-verifies-dratlrat-et-checker-prouve-en-lean-4) | Solveur SAT/SMT certifiant : certificats UNSAT verifies (DRAT/LRAT) et checker prouve en Lean 4 | 5/5 |

### Categorie C : Verification Formelle et Surete des Logiciels

| # | Sujet | Difficulte |
|---|-------|------------|
| [C1](#c1--verification-formelle-de-smart-contracts-solidity-par-smt) | Verification formelle de smart contracts Solidity par SMT | 3/5 |
| [C2](#c2--fuzzing-guide-par-contraintes-constraint-based-fuzzing) | Fuzzing guide par contraintes (constraint-based fuzzing) | 4/5 |
| [C3](#c3--analyse-statique-et-detection-de-vulnerabilites-par-abstraction) | Analyse statique et detection de vulnerabilites par abstraction | 3/5 |
| [C4](#c4--preuves-de-correcteur-zero-knowledge-zk-snarks) | Preuves de correcteur Zero-Knowledge (zk-SNARKs) | 4/5 |
| [C5](#c5--synthese-de-programmes-corrects-par-construction-par-cegis-et-verification-deductive) | Synthese de programmes corrects-par-construction par CEGIS et verification deductive | 5/5 |

### Categorie D : Planification et Ordonnancement

| # | Sujet | Difficulte |
|---|-------|------------|
| [D1](#d1--planification-robotique-avec-pddl-et-integration-capteurs) | Planification robotique avec PDDL et integration capteurs | 3/5 |
| [D2](#d2--planification-htn-pour-jeux-video) | Planification HTN pour jeux video | 3/5 |
| [D3](#d3--ordonnancement-multi-agent-par-csp-distribue) | Ordonnancement multi-agent par CSP distribue | 4/5 |
| [D4](#d4--planification-temporelle-pour-systemes-cyber-physiques) | Planification temporelle pour systemes cyber-physiques | 4/5 |
| [D5](#d5--planification-neuro-symbolique-certifiee--llm-heuristiques-unified-planning-et-validation-formelle-de-plans) | Planification neuro-symbolique certifiee : LLM-heuristiques, Unified Planning et validation formelle de plans | 5/5 |

### Categorie E : Theorie des Jeux et Mechanism Design

| # | Sujet | Difficulte |
|---|-------|------------|
| [E1](#e1--comptabilite-maximin-et-equilibres-de-nash-par-programmation-lineaire) | Comptabilite maximin et equilibres de Nash par programmation lineaire | 3/5 |
| [E2](#e2--encheres-combinatoires-et-allocation-de-biens-publics) | Encheres combinatoires et allocation de biens publics | 4/5 |
| [E3](#e3--jeux-cooperatifs-et-valeur-de-shapley) | Jeux cooperatifs et valeur de Shapley | 3/5 |
| [E4](#e4--conception-de-mecanismes-resistants-a-la-manipulation) | Conception de mecanismes resistants a la manipulation | 4/5 |
| [E5](#e5--counterfactual-regret-minimization-cfr-et-poker-ia) | Counterfactual Regret Minimization (CFR) et poker IA | 3/5 |
| [E6](#e6--conception-automatisee-de-mecanismes--optimisation-sous-incentive-compatibility-et-verification-formelle-smtlean) | Conception automatisee de mecanismes : optimisation sous incentive-compatibility et verification formelle (SMT/Lean) | 5/5 |

### Categorie F : Smart Contracts et Blockchain Symbolique

| # | Sujet | Difficulte |
|---|-------|------------|
| [F1](#f1--super-optimisation-de-gas-solidity-par-max-smt) | Super-optimisation de gas Solidity par Max-SMT | 4/5 |
| [F2](#f2--ordonnancement-mev-resistant-de-transactions-on-chain) | Ordonnancement MEV-resistant de transactions on-chain | 3/5 |
| [F3](#f3--circuits-zero-knowledge-sous-contraintes-arithmetiques) | Circuits Zero-Knowledge sous contraintes arithmetiques | 4/5 |
| [F4](#f4--governance-decentralisee-et-vote-quadratique) | Governance decentralisee et vote quadratique | 3/5 |
| [F5](#f5--coffre-defi-verifie-de-bout-en-bout--synthese-dinvariants-preuve-certoracvl-et-execution-symbolique) | Coffre DeFi verifie de bout en bout : synthese d'invariants, preuve Certora/CVL et execution symbolique | 5/5 |

### Categorie G : Web Semantique et Graphes de Connaissances

| # | Sujet | Difficulte |
|---|-------|------------|
| [G1](#g1--construction-et-interrogation-dun-graphe-de-connaissances-par-sparql) | Construction et interrogation d'un graphe de connaissances par SPARQL | 3/5 |
| [G2](#g2--raisonnement-owl-et-verification-de-coherence-dontologie) | Raisonnement OWL et verification de coherence d'ontologie | 3/5 |
| [G3](#g3--graphrag--combine-knowledge-graphs-et-llm-pour-le-rag) | GraphRAG — combine Knowledge Graphs et LLM pour le RAG | 4/5 |
| [G4](#g4--validation-de-donnees-par-shacl-shapes-constraint-language) | Validation de donnees par SHACL (Shapes Constraint Language) | 3/5 |
| [G5](#g5--architecture-agentique-semantique-pour-le-traitement-de-documents-rdf) | Architecture agentique semantique pour le traitement de documents RDF | 3/5 |
| [G6](#g6--graphrag-verifie--reponses-tracees-ancrees-dans-le-graphe-et-garanties-par-raisonnement-owlshacl) | GraphRAG verifie : reponses tracees, ancrees dans le graphe et garanties par raisonnement OWL/SHACL | 5/5 |

### Categorie H : Representation des Connaissances et Raisonnement

| # | Sujet | Difficulte |
|---|-------|------------|
| [H1](#h1--systeme-de-maintenance-de-verite-jtms) | Systeme de maintenance de verite (JTMS) | 3/5 |
| [H2](#h2--ontologies-et-raisonnement-semantique-owl-reasoning) | Ontologies et raisonnement semantique (OWL Reasoning) | 3/5 |
| [H3](#h3--graphes-de-connaissances-et-reponse-a-des-questions) | Graphes de connaissances et reponse a des questions | 3/5 |
| [H4](#h4--logique-de-description-et-raisonnement-sur-des-domaines-medicaux) | Logique de description et raisonnement sur des domaines medicaux | 4/5 |
| [H5](#h5--apprentissage-dontologies-par-programmation-logique-inductive--induction-daxiomes-sroiq-verifies-par-raisonneur-dl) | Apprentissage d'ontologies par programmation logique inductive : induction d'axiomes SROIQ verifies par raisonneur DL | 5/5 |

### Categorie I : Argumentation et Raisonnement Debateur

| # | Sujet | Difficulte |
|---|-------|------------|
| [I1](#i1--analyse-et-detection-de-sophismes-par-apprentissage-symbolique) | Analyse et detection de sophismes par apprentissage symbolique | 3/5 |
| [I2](#i2--generation-de-contre-arguments-par-raisonnement-formel) | Generation de contre-arguments par raisonnement formel | 3/5 |
| [I3](#i3--argumentation-dialogique-multi-agents) | Argumentation dialogique multi-agents | 4/5 |
| [I4](#i4--evaluation-automatique-de-la-qualite-argumentative) | Evaluation automatique de la qualite argumentative | 3/5 |
| [I5](#i5--benchmarks-iccma--solveurs-dargumentation-de-dung) | Benchmarks ICCMA — solveurs d'argumentation de Dung | 2/5 |
| [I6](#i6--argumentation-structuree-aspic-et-logique-defaisable-delpaba) | Argumentation structuree ASPIC+ et logique defaisable (DeLP/ABA) | 3/5 |
| [I7](#i7--du-texte-au-verdict-argumentatif-certifie--extraction-llm--solveur-de-dung-avec-certificat-dextension-verifiable) | Du texte au verdict argumentatif certifie : extraction LLM + solveur de Dung avec certificat d'extension verifiable | 5/5 |

### Categorie J : Agents Symboliques et Architecture Cognitive

| # | Sujet | Difficulte |
|---|-------|------------|
| [J1](#j1--systeme-multi-agents-de-resolution-de-problemes-par-planification) | Systeme multi-agents de resolution de problemes par planification | 3/5 |
| [J2](#j2--agent-cognitif-hybride-symbolique--subsymbolique) | Agent cognitif hybride (symbolique + subsymbolique) | 4/5 |
| [J3](#j3--serveur-mcp-doutils-danalyse-symbolique) | Serveur MCP d'outils d'analyse symbolique | 3/5 |
| [J4](#j4--integration-llm--solveurs-symboliques-llm-as-a-reasoner) | Integration LLM + solveurs symboliques (LLM-as-a-reasoner) | 4/5 |
| [J5](#j5--apprentissage-par-renforcement-multi-agents-marl-et-emergence-de-cooperation) | Apprentissage par renforcement multi-agents (MARL) et emergence de cooperation | 4/5 |
| [J6](#j6--diagnostic-medical-multi-paradigme-par-agents-symboliques) | Diagnostic medical multi-paradigme par agents symboliques | 4/5 |
| [J7](#j7--architecture-cognitive-a-noyau-symbolique-verifie--agent-llm-pilote-par-planificateur-pddl-et-garde-fou-shield-formel) | Architecture cognitive a noyau symbolique verifie : agent LLM pilote par planificateur PDDL et garde-fou (shield) formel | 5/5 |

### Categorie K : Cryptographie Symbolique et Securite

| # | Sujet | Difficulte |
|---|-------|------------|
| [K1](#k1--cryptanalyse-par-contraintes-de-chiffrements-classiques) | Cryptanalyse par contraintes de chiffrements classiques | 3/5 |
| [K2](#k2--verification-de-protocoles-cryptographiques-par-model-checking) | Verification de protocoles cryptographiques par model checking | 4/5 |
| [K3](#k3--chiffrement-homomorphe-et-calcul-sur-donnees-chiffrees) | Chiffrement homomorphe et calcul sur donnees chiffrees | 4/5 |
| [K4](#k4--vote-electronique-verifiable-de-bout-en-bout--chiffrement-homomorphe-preuves-zero-knowledge-et-verification-symbolique-du-protocole) | Vote electronique verifiable de bout en bout : chiffrement homomorphe, preuves zero-knowledge et verification symbolique du protocole | 5/5 |

### Categorie L : Puzzles, Jeux et Problemes Combinatoires

| # | Sujet | Difficulte |
|---|-------|------------|
| [L1](#l1--resolution-de-sudoku-par-multiples-solveurs-sat-cp-lll) | Resolution de Sudoku par multiples solveurs (SAT, CP, LLL) | 2/5 |
| [L2](#l2--generation-procedurale-par-contraintes-de-niveaux-de-jeu) | Generation procedurale par contraintes de niveaux de jeu | 3/5 |
| [L3](#l3--resolution-de-jeux-combinatoires-par-minimax-et-alpha-beta-symbolique) | Resolution de jeux combinatoires par minimax et alpha-beta symbolique | 3/5 |
| [L4](#l4--benchmark-cross-paradigme-de-solveurs-de-jeux-sudoku-connect-four-wordle) | Benchmark cross-paradigme de solveurs de jeux (Sudoku, Connect Four, Wordle) | 3/5 |
| [L5](#l5--generateur-de-puzzles-a-unicite-certifiee--synthese-sous-contraintes-preuve-dunicite-de-solution-et-calibration-de-difficulte) | Generateur de puzzles a unicite certifiee : synthese sous contraintes, preuve d'unicite de solution et calibration de difficulte | 5/5 |

---

### Categorie M : IA Neuro-Symbolique

> L'IA neuro-symbolique combine le raisonnement formel (logique, contraintes) avec l'apprentissage profond (LLM, reseaux de neurones). Domaine en pleine expansion avec des applications en raisonnement verifiable, generation guidee par contraintes, et interpretabilite.

| # | Sujet | Difficulte |
|---|-------|------------|
| [M1](#m1--pipeline-llm--verificateur-symbolique-pour-la-generation-fiable) | Pipeline LLM + verificateur symbolique pour la generation fiable | 3/5 |
| [M2](#m2--reseau-de-neurones-logique-logical-neural-networks) | Reseau de neurones logique (Logical Neural Networks) | 4/5 |
| [M3](#m3--regression-symbolique--decouvrir-des-equations-a-partir-de-donnees) | Regression symbolique -- decouvrir des equations a partir de donnees | 3/5 |
| [M4](#m4--decouverte-scientifique-automatisee-par-regression-symbolique-et-llm) | Decouverte scientifique automatisee par regression symbolique et LLM | 4/5 |
| [M5](#m5--evaluation-comparee-llm-vs-approches-symboliques-sur-un-benchmark) | Evaluation comparee LLM vs. approches symboliques sur un benchmark | 2/5 |
| [M6](#m6--theorie-de-linformation-integree-iit-et-conscience-artificielle-par-pyphi) | Theorie de l'Information Integree (IIT) et conscience artificielle par PyPhi | 3/5 |
| [M7](#m7--generation-de-contenu-neuro-symbolique-par-semantic-kernel--validation-csp) | Generation de contenu neuro-symbolique par Semantic Kernel + validation CSP | 4/5 |
| [M8](#m8--demonstration-automatique-neuro-symbolique--agent-llm-pour-lean-4) | Demonstration automatique neuro-symbolique : agent LLM pour Lean 4 | 5/5 |
| [M9](#m9--compresseur-sans-perte-neuro-symbolique--llm-decouvreur-decodeur-certifie-et-registre-de-recettes-signees) | Compresseur sans perte neuro-symbolique : LLM-decouvreur, decodeur certifie et registre de recettes signees | 5/5 |

### Categorie N : Raisonnement Causal et Decision

> Le raisonnement causal (Pearl, 2009) depasse la correlation pour raisonner sur les interventions et les contrefactuels. Fondamental pour la prise de decision dans les systemes IA, la medecine, et l'analyse de politiques.

| # | Sujet | Difficulte |
|---|-------|------------|
| [N1](#n1--decouverte-causale-a-partir-de-donnees-observationnelles) | Decouverte causale a partir de donnees observationnelles | 3/5 |
| [N2](#n2--raisonnement-causal-par-le-do-calculus-avec-dowhy) | Raisonnement causal par le do-calculus avec DoWhy | 3/5 |
| [N3](#n3--diagnostic-abductif--raisonnement-par-abduction) | Diagnostic abductif — raisonnement par abduction | 3/5 |
| [N4](#n4--evaluation-du-raisonnement-causal-des-llm) | Evaluation du raisonnement causal des LLM | 4/5 |
| [N5](#n5--planification-oncologique-symbolique-ontologies-z3-et-modeles-probabilistes) | Planification oncologique symbolique (ontologies, Z3 et modeles probabilistes) | 5/5 |

### Categorie O : Raisonnement Qualitatif et Bon Sens

> Le raisonnement qualitatif manipule des representations symboliques de l'espace, du temps, et du bon sens sans recourir a des modeles numeriques. Inclut les calculs relationnels spatiaux (RCC8), temporels (Allen), et le raisonnement de sens commun.

| # | Sujet | Difficulte |
|---|-------|------------|
| [O1](#o1--raisonnement-spatial-qualitatif-par-les-calculs-rcc8) | Raisonnement spatial qualitatif par les calculs RCC8 | 3/5 |
| [O2](#o2--raisonnement-temporel-qualitatif--algebres-dallen-et-stp) | Raisonnement temporel qualitatif — Algebres d'Allen et STP | 3/5 |
| [O3](#o3--raisonnement-de-bon-sens-par-graphe-de-connaissances-commonsense) | Raisonnement de bon sens par graphe de connaissances (Commonsense) | 3/5 |
| [O4](#o4--raisonnement-par-analogie--theorie-du-mapping-structurel) | Raisonnement par analogie — theorie du mapping structurel | 3/5 |
| [O5](#o5--raisonneur-spatio-temporel-qualitatif-integre--composition-rcc8-x-allen-coherence-par-csp-et-extraction-depuis-le-langage-naturel) | Raisonneur spatio-temporel qualitatif integre : composition RCC8 x Allen, coherence par CSP et extraction depuis le langage naturel | 5/5 |

### Categorie P : Verification Formelle des Systemes IA

> La verification formelle des systemes d'IA est un domaine emergent critique pour la surete. Il s'agit de prouver formellement qu'un systeme d'IA (reseau de neurones, agent LLM, politique RL) satisfait des proprietes de surete, equite, ou robustesse.

| # | Sujet | Difficulte |
|---|-------|------------|
| [P1](#p1--verification-de-robustesse-de-reseaux-de-neurones-par-abstraction) | Verification de robustesse de reseaux de neurones par abstraction | 4/5 |
| [P2](#p2--verification-de-politiques-rl-par-contraintes-formelles) | Verification de politiques RL par contraintes formelles | 4/5 |
| [P3](#p3--specification-et-verification-de-securite-dagents-llm-par-logique-temporelle) | Specification et verification de securite d'agents LLM par logique temporelle | 4/5 |
| [P4](#p4--robustesse-formelle-des-reseaux-de-neurones-binaires-par-le-sensitivity-theorem) | Robustesse formelle des reseaux de neurones binaires par le Sensitivity Theorem | 5/5 |

### Categorie Q : Raisonnement Ethique et Normatif

> Le raisonnement ethique et normatif utilise la logique deontique (obligations, permissions, interdictions) et les cadres d'argumentation pour raisonner formellement sur les normes, les valeurs, et l'alignement des systemes d'IA.

| # | Sujet | Difficulte |
|---|-------|------------|
| [Q1](#q1--raisonneur-deontique--logique-des-normes-et-obligations) | Raisonneur deontique — logique des normes et obligations | 3/5 |
| [Q2](#q2--verification-dalignement-de-valeurs-par-methodes-formelles) | Verification d'alignement de valeurs par methodes formelles | 4/5 |
| [Q3](#q3--raisonnement-juridique-formel-par-argumentation-et-logique) | Raisonnement juridique formel par argumentation et logique | 3/5 |
| [Q4](#q4--agent-conforme-par-construction--raisonneur-deontique-garde-fou-normatif-shield-et-tracabilite-reglementaire-ai-act--rgpd) | Agent conforme par construction : raisonneur deontique, garde-fou normatif (shield) et tracabilite reglementaire (AI Act / RGPD) | 5/5 |

### Categorie R : Raisonnement sous Incertitude et Revision des Croyances

> La revision des croyances et le raisonnement sous incertitude sont au coeur des systemes symboliques devant mettre a jour leurs connaissances face a de nouvelles informations contradictoires. Inclut les postulats AGM, les croyances probabilistes, et la programmation probabiliste.

| # | Sujet | Difficulte |
|---|-------|------------|
| [R1](#r1--revision-des-croyances-par-les-postulats-agm) | Revision des croyances par les postulats AGM | 3/5 |
| [R2](#r2--programmation-probabiliste-avec-infernet) | Programmation probabiliste avec Infer.NET | 3/5 |
| [R3](#r3--raisonnement-epistemique-et-logique-multi-agents) | Raisonnement epistemique et logique multi-agents | 4/5 |
| [R4](#r4--agent-de-decision-sequentielle-a-croyances-revisees--fusion-agm-symbolique-et-inference-bayesienne-sous-information-contradictoire) | Agent de decision sequentielle a croyances revisees : fusion AGM symbolique et inference bayesienne sous information contradictoire | 5/5 |

### Categorie S : Trading Algorithmique Symbolique

> Les sujets de la categorie S combinent un **noyau IA Symbolique** (logique epistemique, web semantique, verification formelle SMT, programmation probabiliste) avec une validation pratique via la plateforme [QuantConnect Lean](https://www.quantconnect.com/). Chaque projet est fondamentalement symbolique et utilise le backtest QuantConnect uniquement comme couche de validation sur donnees reelles de marche. Les etudiants ayant rejoint l'organisation QuantConnect sponsorisee par Jared Broad (CEO QC) sont encourages a choisir en priorite ces sujets.
>
> **Attention** : Si votre objectif est d'optimiser un portefeuille par programmation par contraintes (CP-SAT, MiniZinc, CPMpy, MIP), consultez la [Categorie M du cours Programmation par Contraintes](https://github.com/jsboigeEpita/2026-Epita-Programmation-par-Contraintes#categorie-m--finance-quantitative-et-trading-algorithmique). La categorie S vise le **raisonnement symbolique formel** sur acteurs, contrats et regimes de marche — pas l'optimisation numerique.

| # | Sujet | Difficulte |
|---|-------|------------|
| [S1](#s1--raisonnement-epistemique-pour-le-trading-multi-agents) | Raisonnement epistemique pour le trading multi-agents | 4/5 |
| [S2](#s2--ontologies-financieres-et-web-semantique-pour-le-screening-dactifs) | Ontologies financieres et Web Semantique pour le screening d'actifs | 3/5 |
| [S3](#s3--verification-formelle-de-protocoles-defi-par-smt) | Verification formelle de protocoles DeFi par SMT | 4/5 |
| [S4](#s4--programmation-probabiliste-symbolique-pour-la-detection-de-regimes-de-marche) | Programmation probabiliste symbolique pour la detection de regimes de marche | 3/5 |
| [S5](#s5--enumeration-asp-des-strategies-doptions-multi-jambes-et-backtest-quantconnect) | Enumeration ASP des strategies d'options multi-jambes et backtest QuantConnect | 4/5 |
| [S6](#s6--safe-rl-shielding-smt-des-politiques-de-trading-rl-et-deployment-quantconnect-live) | Safe RL : shielding SMT des politiques de trading RL et deployment QuantConnect Live | 5/5 |
| [S7](#s7--fusion-de-signaux-multi-strategie-par-argumentation-dung-sur-le-research-executor-quantconnect) | Fusion de signaux multi-strategie par argumentation Dung sur le Research-Executor QuantConnect | 5/5 |
| [S8](#s8--model-checking-ctl-dun-trading-bot-avant-deployment-live-quantconnect) | Model checking CTL d'un trading bot avant deployment live QuantConnect | 4/5 |

### Categorie T : Sciences Sociales Computationnelles et Choix Collectif

> Les sujets de la categorie T appliquent les outils de l'IA symbolique (verification formelle SAT/SMT, preuve Lean, argumentation structuree, revision des croyances AGM, logique epistemique) a des problemes de sciences sociales et de choix collectif. Chaque sujet repose sur un **noyau symbolique implementable** (solveur, raisonneur, module de preuve) et utilise la theorie des jeux, les modeles probabilistes ou les donnees reelles comme contexte d'application. Les sources de donnees sont publiques et verifiables (data.gouv.fr, assemblee-nationale.fr, election resources).

| # | Sujet | Difficulte |
|---|-------|------------|
| [T1](#t1--pouvoir-de-coalition-par-verification-formelle-shapley-banzhaf-et-donnees-electorales-reelles) | Pouvoir de coalition par verification formelle (Shapley, Banzhaf et donnees electorales reelles) | 3/5 |
| [T2](#t2--choix-social-et-procedures-de-vote-analyse-formelle-par-satsmt) | Choix social et procedures de vote : analyse formelle par SAT/SMT | 4/5 |
| [T3](#t3--information-asymetrique-et-capture-modelisation-par-argumentation-et-logique-epistemique) | Information asymetrique et capture : modelisation par argumentation et logique epistemique | 4/5 |
| [T4](#t4--decision-publique-sous-incertitude-revision-des-croyances-et-argumentation) | Decision publique sous incertitude : revision des croyances et argumentation | 3/5 |
| [T5](#t5--decouverte-automatique-de-theoremes-dimpossibilite-en-choix-social--recherche-sat-de-contre-exemples-et-certification-lean) | Decouverte automatique de theoremes d'impossibilite en choix social : recherche SAT de contre-exemples et certification Lean | 5/5 |

---

> **Note** : Les descriptions detaillees de chaque sujet, les references academiques et les notebooks CoursIA associes seront enrichis progressivement. Cette premiere version est un draft soumis pour revue et enrichissement par l'equipe pedagogique.

---

#### J4 — Integration LLM + solveurs symboliques (LLM-as-a-reasoner)

Implementer un pipeline complet ou un LLM traduit des problemes enoncees en langage naturel en modeles symboliques (SAT, SMT, CSP, PDDL), appelle un solveur approprie, puis interprete les resultats en langage naturel. Le pipeline inclut une etape de validation de la traduction (verification syntaxique et semantique du modele genere) et des strategies de correction automatique lorsque la traduction echoue. L'etude systematique des erreurs de traduction (variables manquantes, contraintes incorrectes, formulation sous-optimale) constitue un livrable central du projet. L'evaluation se fait sur des benchmarks de raisonnement logique et mathematique.

### Objectifs
- Construire un pipeline LLM-to-symbolique avec traduction, resolution et interpretation des resultats
- Implementer une validation automatique de la traduction (syntaxe et semantique du modele symbolique)
- Developper des strategies de re-prompting et de correction pour les traductions erronees
- Realiser une taxonomie systematique des erreurs de traduction LLM vers modeles symboliques
- Evaluer sur des benchmarks de raisonnement (LogicGrid, ProofWriter, GSM8K)

### Notebooks CoursIA pertinents

| Notebook | Chemin | Pertinence |
|----------|--------|------------|
| CSP-6 LLM+CSP | [Search/Part2-CSP/CSP-6-Hybridization.ipynb](https://github.com/jsboige/CoursIA/blob/main/MyIA.AI.Notebooks/Search/Part2-CSP/CSP-6-Hybridization.ipynb) | Pipeline LLM vers solveur CSP |
| Planners-10 LLM Planning | [SymbolicAI/Planners/04-NeuroSymbolic/Planners-10-LLM-Planning.ipynb](https://github.com/jsboige/CoursIA/blob/main/MyIA.AI.Notebooks/SymbolicAI/Planners/04-NeuroSymbolic/Planners-10-LLM-Planning.ipynb) | Traduction LLM vers PDDL |
| Planners-12 LOOP | [SymbolicAI/Planners/04-NeuroSymbolic/Planners-12-LOOP.ipynb](https://github.com/jsboige/CoursIA/blob/main/MyIA.AI.Notebooks/SymbolicAI/Planners/04-NeuroSymbolic/Planners-12-LOOP.ipynb) | Boucle observation-planification-action |
| Linq2Z3 | [SymbolicAI/Linq2Z3.ipynb](https://github.com/jsboige/CoursIA/blob/main/MyIA.AI.Notebooks/SymbolicAI/Linq2Z3.ipynb) | Solveur Z3 SMT, traduction de contraintes |

### References externes
- Pan, L. et al. (2023). "Logic-LM: Faithful Logical Reasoning with Large Language Models." *EMNLP 2023*. [ACL Anthology](https://aclanthology.org/2023.emnlp-main..pe/)
- Katz, M. et al. (2024). "Duality in LLM-assisted Planning." *ICAPS 2024*. [AAAI](https://aaai.org/)
- Shunyu, Y. et al. (2023). "ReAct: Synergizing Reasoning and Acting in Language Models." *ICLR 2023*. [OpenReview](https://openreview.net/forum?id=WE_vluYUL-X)
- Gao, L. et al. (2023). "PAL: Program-Aided Language Models." *ICML 2023*. [arXiv](https://arxiv.org/abs/2212.10573)

### Difficulte : 4/5

---
