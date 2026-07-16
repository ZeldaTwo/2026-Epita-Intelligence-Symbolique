"""

Métriques produites par puzzle :
  1. formalisme choisi par le LLM         (attendu : "csp")
  2. validité + nombre de tentatives de correction
  3. statut du solveur                    (attendu : SAT)
  4. nombre de solutions / unicité        (attendu : exactement 1)

Un puzzle est compté comme "résolu correctement" ssi : succès de traduction
ET statut SAT ET solution unique.

Usage :
    python benchmarks/logicgrid_benchmark.py --model qwen2.5-coder
    python benchmarks/logicgrid_benchmark.py --model qwen2.5-coder --output logicgrid_results.json
    python benchmarks/logicgrid_benchmark.py --model qwen2.5-coder --debug
    python benchmarks/logicgrid_benchmark.py --check-only   # teste le moteur d'unicité SANS LLM

Prérequis (hors --check-only) : Ollama lancé (`ollama serve`) et le modèle
téléchargé (`ollama pull qwen2.5-coder`).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import z3

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from config import get_default_max_attempts  # noqa: E402
from error_taxonomy import ErrorTaxonomyAnalyzer  # noqa: E402
from pipeline import run_pipeline  # noqa: E402
from schema import SymbolicModel, Variable  # noqa: E402
from translator import LLMTranslator  # noqa: E402
from validator import (  # noqa: E402
    add_domain_constraints,
    build_z3_vars,
    compile_constraint,
)

LOGIC_GRID_PROBLEMS: list[dict] = [
    {
        "id": "LG_01_ANIMALS",
        "category": "logic_grid_easy",
        "text": (
            "Trois amis — Alice, Bob et Chloé — possèdent chacun un animal "
            "différent parmi : chat, chien, oiseau. Alice ne possède pas le "
            "chat. Bob possède le chien. Attribue à chaque personne son animal."
        ),
        "solution": "Alice=oiseau, Bob=chien, Chloé=chat",
    },
    {
        "id": "LG_02_HOUSES_COLORS",
        "category": "logic_grid_positions",
        "text": (
            "Quatre maisons occupent les positions 1 à 4 de gauche à droite. "
            "Chaque maison a une couleur unique parmi rouge, bleue, verte, "
            "jaune. La maison bleue est en position 1. La maison jaune est en "
            "position 4. La maison rouge est immédiatement à gauche de la "
            "maison verte. Donne la position de chaque couleur."
        ),
        "solution": "bleue=1, rouge=2, verte=3, jaune=4",
    },
    {
        "id": "LG_03_DRINKS",
        "category": "logic_grid_easy",
        "text": (
            "Trois personnes — Paul, Marie, Sophie — boivent chacune une "
            "boisson différente : café, thé, jus. Marie boit le café. Sophie "
            "ne boit pas le thé. Attribue chaque boisson à chaque personne."
        ),
        "solution": "Marie=café, Sophie=jus, Paul=thé",
    },
    {
        "id": "LG_04_RACE_RANKING",
        "category": "logic_grid_ordering",
        "text": (
            "Quatre coureurs — A, B, C, D — terminent une course aux places 1 "
            "à 4 (pas d'ex æquo). A termine avant B. C termine juste après B. "
            "D termine dernier. Donne le classement de chaque coureur."
        ),
        "solution": "A=1, B=2, C=3, D=4",
    },
    {
        "id": "LG_05_EINSTEIN_MINI",
        "category": "logic_grid_multi_attribute",
        "text": (
            "Trois maisons alignées (positions 1, 2, 3). Dans chacune vit une "
            "personne de nationalité différente : Français, Anglais, Espagnol. "
            "Chacune boit une boisson différente : eau, vin, lait. Le Français "
            "vit en position 1. La personne qui boit du lait vit en position 2. "
            "L'Anglais boit du vin. L'Espagnol ne vit pas en position 3. "
            "Détermine, pour chaque position, la nationalité et la boisson."
        ),
        "solution": "pos1=Français/eau, pos2=Espagnol/lait, pos3=Anglais/vin",
    },
    {
        "id": "LG_06_MEETINGS",
        "category": "logic_grid_ordering",
        "text": (
            "Quatre réunions — R1, R2, R3, R4 — sont planifiées à des créneaux "
            "distincts numérotés de 1 à 4. R1 a lieu avant R2. R3 a lieu après "
            "R2. R4 a lieu au créneau 1. Donne le créneau de chaque réunion."
        ),
        "solution": "R4=1, R1=2, R2=3, R3=4",
    },
]


def count_solutions(model: SymbolicModel, limit: int = 2) -> int | None:
    """Compte les solutions distinctes d'un modèle Z3, bornées par `limit`.

    On énumère par la technique classique de la « clause de blocage » : après
    chaque modèle trouvé, on ajoute une contrainte interdisant exactement cette
    affectation, puis on re-résout. Un puzzle logic-grid bien traduit renvoie 1.
    Renvoie `None` pour les modèles PDDL (non applicable).

    Attention : `limit` borne le comptage — on ne cherche PAS à énumérer tout
    l'espace (potentiellement énorme), seulement à distinguer 0 / 1 / « ≥ 2 ».
    """
    if model.formalism == "pddl":
        return None

    z3_vars = build_z3_vars(model)
    solver = z3.Solver()
    add_domain_constraints(solver, model, z3_vars)
    for constraint in model.constraints:
        solver.add(compile_constraint(constraint, z3_vars))

    count = 0
    while count < limit and solver.check() == z3.sat:
        count += 1
        m = solver.model()
        blocking = []
        for v in model.variables:
            zv = z3_vars[v.name]
            val = m.eval(zv, model_completion=True)
            blocking.append(zv != val)
        if not blocking:
            break
        solver.add(z3.Or(*blocking))
    return count


def run_logicgrid_benchmark(
    model_name: str,
    max_correction_attempts: int | None = None,
    host: str | None = None,
    debug: bool = False,
) -> tuple[list[dict], ErrorTaxonomyAnalyzer]:
    if max_correction_attempts is None:
        max_correction_attempts = get_default_max_attempts()
    translator = LLMTranslator(model_name=model_name, host=host)
    analyzer = ErrorTaxonomyAnalyzer()
    detailed: list[dict] = []

    for problem in LOGIC_GRID_PROBLEMS:
        print(f"\n[{problem['id']}] {problem['text'][:90]}...")
        t0 = time.time()
        try:
            output = run_pipeline(
                problem_id=problem["id"],
                problem_text=problem["text"],
                translator=translator,
                max_correction_attempts=max_correction_attempts,
                # On évalue la TRADUCTION, pas la reformulation NL : on coupe
                # l'interprétation LLM (plus rapide, moins d'appels au modèle).
                use_llm_for_interpretation=False,
                debug=debug,
            )
            elapsed = time.time() - t0
            analyzer.add(output.run_record)

            formalism = output.symbolic_model.formalism if output.symbolic_model else None
            status = output.solver_result.status if output.solver_result else None

            # Test d'unicité (uniquement si on a un modèle SAT non-PDDL).
            n_solutions: int | None = None
            unique: bool | None = None
            uniqueness_error: str | None = None
            if output.symbolic_model is not None and status == "SAT":
                try:
                    n_solutions = count_solutions(output.symbolic_model, limit=2)
                    unique = n_solutions == 1
                except Exception as exc:  # noqa: BLE001
                    uniqueness_error = str(exc)

            correct = bool(output.run_record.succeeded and status == "SAT" and unique)

            detail = {
                "id": problem["id"],
                "category": problem["category"],
                "expected_solution": problem["solution"],
                "succeeded_translation": output.run_record.succeeded,
                "n_attempts": output.run_record.n_attempts,
                "formalism": formalism,
                "expected_formalism": "csp",
                "solver_status": status,
                "n_solutions_capped": n_solutions,
                "unique_solution": unique,
                "correct": correct,
                "elapsed_seconds": round(elapsed, 2),
            }
            if uniqueness_error:
                detail["uniqueness_error"] = uniqueness_error
            if output.solver_result is not None:
                detail["assignment"] = output.solver_result.assignment
            detailed.append(detail)

            if correct:
                print(
                    f"  ->  [OK] formalism={formalism}, SAT, solution UNIQUE "
                    f"({output.run_record.n_attempts} tentative(s), {elapsed:.1f}s)"
                )
            elif output.run_record.succeeded and unique is False:
                print(
                    f"  ->  [SOUS-SPÉCIFIÉ] formalism={formalism}, SAT mais "
                    f"solutions multiples (≥2) : contrainte omise à la traduction."
                )
            else:
                print(
                    f"  ->  [ÉCHEC] succeeded={output.run_record.succeeded}, "
                    f"formalism={formalism}, status={status}, "
                    f"erreurs={', '.join(output.run_record.error_categories_encountered) or '—'}"
                )

        except Exception as exc:  # noqa: BLE001
            print(f"  ->  [ERREUR SYSTÈME] : {exc}")
            detailed.append({
                "id": problem["id"],
                "category": problem["category"],
                "succeeded_translation": False,
                "correct": False,
                "error": str(exc),
            })

    return detailed, analyzer


def build_summary(detailed: list[dict], analyzer: ErrorTaxonomyAnalyzer) -> dict:
    n = len(detailed)
    n_correct = sum(1 for d in detailed if d.get("correct"))
    n_right_formalism = sum(1 for d in detailed if d.get("formalism") == "csp")
    n_sat = sum(1 for d in detailed if d.get("solver_status") == "SAT")
    n_unique = sum(1 for d in detailed if d.get("unique_solution") is True)
    n_underspecified = sum(1 for d in detailed if d.get("unique_solution") is False)

    return {
        "n_puzzles": n,
        "translation_success_rate": round(analyzer.success_rate_with_correction(), 3),
        "correct_formalism_rate_csp": round(n_right_formalism / n, 3) if n else 0.0,
        "sat_rate": round(n_sat / n, 3) if n else 0.0,
        "unique_solution_rate": round(n_unique / n, 3) if n else 0.0,
        "underspecified_count": n_underspecified,
        "fully_correct_rate": round(n_correct / n, 3) if n else 0.0,
        "average_attempts": round(analyzer.average_attempts(), 2),
        "error_category_distribution": dict(analyzer.category_distribution()),
    }



def self_check() -> None:
    """Prouve que le moteur d'unicité distingue bien 1 solution de plusieurs."""
    print("=== Auto-test du moteur d'unicité (aucun LLM requis) ===\n")

    # Modèle BIEN spécifié (une seule solution) : x+y==10, x==3  ->  y==7.
    well_specified = SymbolicModel(
        variables=[Variable(name="x", type="Int", domain=[0, 10]),
                   Variable(name="y", type="Int", domain=[0, 10])],
        constraints=["x + y == 10", "x == 3"],
    )
    n1 = count_solutions(well_specified, limit=2)
    print(f"Modèle bien spécifié      -> {n1} solution(s) "
          f"(attendu 1)  {'[OK]' if n1 == 1 else '[KO]'}")

    # Modèle SOUS-spécifié (contrainte omise) : x+y==10 seul -> plusieurs.
    under_specified = SymbolicModel(
        variables=[Variable(name="x", type="Int", domain=[0, 10]),
                   Variable(name="y", type="Int", domain=[0, 10])],
        constraints=["x + y == 10"],
    )
    n2 = count_solutions(under_specified, limit=2)
    print(f"Modèle sous-spécifié      -> {n2}+ solution(s) "
          f"(attendu ≥2)  {'[OK]' if n2 == 2 else '[KO]'}")

    # Modèle IMPOSSIBLE : x>5 et x<2 -> 0 solution.
    impossible = SymbolicModel(
        variables=[Variable(name="x", type="Int", domain=[0, 10])],
        constraints=["x > 5", "x < 2"],
    )
    n3 = count_solutions(impossible, limit=2)
    print(f"Modèle impossible (UNSAT) -> {n3} solution(s) "
          f"(attendu 0)  {'[OK]' if n3 == 0 else '[KO]'}")

    ok = (n1 == 1 and n2 == 2 and n3 == 0)
    print(f"\nMoteur d'unicité : {'VALIDE' if ok else 'DÉFAILLANT'}")
    sys.exit(0 if ok else 1)


def main():
    parser = argparse.ArgumentParser(description="Benchmark LogicGrid (LLM-as-a-reasoner)")
    parser.add_argument("--model", default="qwen2.5-coder", help="Modèle Ollama installé")
    parser.add_argument("--host", default=None, help="URL du serveur Ollama")
    parser.add_argument("--max-attempts", type=int, default=get_default_max_attempts(),
                        help="Nombre max de tentatives de correction (défaut : env LLM_REASONER_MAX_ATTEMPTS ou 5)")
    parser.add_argument("--debug", action="store_true",
                        help="Affiche les réponses brutes du LLM")
    parser.add_argument("--output", default=None, help="Fichier JSON de sortie")
    parser.add_argument("--check-only", action="store_true",
                        help="Teste seulement le moteur d'unicité (sans LLM)")
    args = parser.parse_args()

    if args.check_only:
        self_check()
        return

    detailed, analyzer = run_logicgrid_benchmark(
        model_name=args.model,
        max_correction_attempts=args.max_attempts,
        host=args.host,
        debug=args.debug,
    )

    summary = build_summary(detailed, analyzer)
    print("\n" + "=" * 60)
    print("RÉSUMÉ DU BENCHMARK LOGICGRID")
    print("=" * 60)
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "details": detailed}, f,
                      indent=2, ensure_ascii=False)
        print(f"\nRésultats détaillés écrits dans {args.output}")


if __name__ == "__main__":
    main()
