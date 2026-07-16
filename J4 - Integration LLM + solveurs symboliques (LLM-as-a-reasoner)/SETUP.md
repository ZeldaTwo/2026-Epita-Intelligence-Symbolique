# SETUP — J4 : Intégration LLM + solveurs symboliques (LLM-as-a-reasoner)

Pipeline neuro-symbolique qui prend un **énoncé en langage naturel**, le fait
**traduire par un LLM** en un modèle symbolique intermédiaire (JSON), **valide**
et **corrige** cette traduction, la **résout** avec le solveur adapté, puis
**réinterprète** le résultat en langage naturel.

```
[Énoncé NL] → traduction (LLM) → validation → boucle de correction
            → résolution (Z3 / planificateur) → interprétation NL
```

Le pipeline choisit automatiquement l'un des **quatre formalismes** :

| Formalisme | Usage | Backend |
|------------|-------|---------|
| `sat`  | logique booléenne pure (énigmes de vérité, circuits) | Z3 |
| `smt`  | arithmétique, coûts, optimisation (`maximize` / `minimize`) | Z3 / Z3-Optimize |
| `csp`  | énigmes à attributs multiples (Einstein, carrés latins, plannings) | Z3 |
| `pddl` | planification d'actions d'un agent | planificateur BFS maison |

---

## 1. Prérequis

- **Python 3.10+**
- **[Ollama](https://ollama.com/)** installé et lancé localement (fournit le LLM)
- Système : Linux, macOS ou Windows

---

## 2. Installation

```bash
# 1. Se placer dans le dossier du projet
cd "J4 - Integration LLM + solveurs symboliques (LLM-as-a-reasoner)"

# 2. (Recommandé) créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt
```

Dépendances (`requirements.txt`) : `z3-solver`, `pydantic`, `ollama`,
`pytest`, `streamlit`.

---

## 3. Configuration d'Ollama

Le pipeline appelle un modèle local via Ollama. Le modèle par défaut est
`qwen2.5-coder`.

```bash
# Démarrer le serveur (dans un terminal dédié)
ollama serve

# Télécharger le modèle (une seule fois)
ollama pull qwen2.5-coder
```

> Tout autre modèle installé fonctionne : passez son nom via `--model`.
> Un serveur distant se cible avec `--host` (ex. `--host http://192.168.1.10:11434`).

---

## 4. Exécution

### a) Démo en ligne de commande

Pose une question, affiche la réponse.

```bash
python demo.py --model qwen2.5-coder "Alice a 3 fois plus de billes que Bob, ensemble 40 billes. Combien Bob en a ?"
```

Options utiles : `--verbose` (affiche le modèle symbolique et le résultat brut
du solveur), `--max-attempts N` (nombre de tentatives de correction),
`--host URL`.

### b) Interface graphique (Streamlit)

UI de chat pour tester interactivement.

```bash
streamlit run app.py
```

Le modèle, le nombre de tentatives et l'interprétation LLM se règlent dans la
barre latérale.

### c) Benchmark général (les 4 formalismes)

Exécute le pipeline sur `benchmarks/datasets/sample_problems.json`
(20 problèmes : 5 SAT, 5 SMT, 5 CSP, 5 PDDL) et produit métriques + taxonomie
d'erreurs agrégée.

```bash
python benchmarks/benchmark_runner.py --model qwen2.5-coder
# Sauvegarder les résultats détaillés :
python benchmarks/benchmark_runner.py --model qwen2.5-coder --output results.json
# Voir les réponses brutes du LLM :
python benchmarks/benchmark_runner.py --model qwen2.5-coder --debug
```

Options : `--dataset CHEMIN`, `--max-attempts N`, `--no-llm-interpretation`
(repli textuel, plus rapide), `--host URL`.

### d) Benchmark LogicGrid (unicité de solution)

Évalue la **qualité de traduction** sur des grilles logiques : une grille bien
traduite a **exactement une** solution. Le script vérifie automatiquement
l'unicité (énumération Z3 par clause de blocage), indépendamment du nommage des
variables choisi par le LLM.

```bash
python benchmarks/logicgrid_benchmark.py --model qwen2.5-coder --output logicgrid_results.json
```

**Mode hors-ligne** (teste le moteur d'unicité sans Ollama ni LLM) :

```bash
python benchmarks/logicgrid_benchmark.py --check-only
```

### e) Tests unitaires

Testent la partie symbolique (validation + résolution + boucle de correction)
**sans dépendance à Ollama** (le LLM est mocké).

```bash
pytest tests/ -v
```

---

## 5. Structure du projet

```
.
├── src/
│   ├── schema.py           # modèle symbolique intermédiaire (Pydantic) + types
│   ├── translator.py       # prompt système + appel LLM + parsing JSON
│   ├── validator.py        # validation syntaxique/sémantique (AST + Z3)
│   ├── solver_backend.py   # résolution Z3 (sat/smt/csp) + planificateur PDDL
│   ├── correction_loop.py  # re-prompting sur erreur, jusqu'à N tentatives
│   ├── interpreter.py      # reformulation NL du résultat du solveur
│   ├── error_taxonomy.py   # agrégation des erreurs de traduction (livrable central)
│   └── pipeline.py         # orchestration bout-en-bout
├── benchmarks/
│   ├── benchmark_runner.py      # banc d'essai multi-formalismes
│   ├── logicgrid_benchmark.py   # banc d'essai grilles logiques (unicité)
│   └── datasets/
│       └── sample_problems.json # 20 problèmes (5 par formalisme)
├── tests/                  # tests unitaires (sans Ollama)
├── app.py                  # interface Streamlit
├── demo.py                 # démo CLI
├── architecture.txt
├── ProjetREADME.md         # énoncé du sujet J4
└── requirements.txt
```

---

## 6. Dépannage

| Symptôme | Cause probable / solution |
|----------|---------------------------|
| `Impossible d'importer les modules` (Streamlit) | Lancez `streamlit run app.py` **depuis la racine** du projet. |
| Erreur de connexion Ollama | Vérifiez que `ollama serve` tourne et que le port (11434) est accessible ; sinon précisez `--host`. |
| `model ... not found` | Téléchargez-le : `ollama pull qwen2.5-coder`. |
| Benchmark très lent | Utilisez `--no-llm-interpretation`, réduisez `--max-attempts`, ou un modèle plus léger. |

> **État des tests** : `pytest` renvoie actuellement **13/14 réussis**. L'unique
> échec, `test_trivially_unsat_detected`, correspond à une passe de détection
> d'insatisfiabilité déclarée dans la taxonomie mais non encore implémentée dans
> `validator.py` (piste d'amélioration connue, sans impact sur l'exécution du
> pipeline).
