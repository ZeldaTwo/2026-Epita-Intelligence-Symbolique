"""
Lance le pipeline LLM-as-a-reasoner sur l'ensemble du dataset de benchmark
et produit un rapport de métriques + la taxonomie d'erreurs agrégée.

Usage :
    python benchmarks/benchmark_runner.py --model qwen2.5-coder
    python benchmarks/benchmark_runner.py --model qwen2.5-coder --output results.json
    python benchmarks/benchmark_runner.py --model qwen2.5-coder --debug
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from config import get_default_max_attempts  # noqa: E402
from error_taxonomy import ErrorTaxonomyAnalyzer  # noqa: E402
from pipeline import run_pipeline  # noqa: E402
from translator import LLMTranslator  # noqa: E402

DEFAULT_DATASET = Path(__file__).resolve().parent / "datasets" / "sample_problems.json"


def load_dataset(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_benchmark(
    dataset_path: Path,
    model_name: str,
    max_correction_attempts: int | None = None,
    use_llm_for_interpretation: bool = True,
    host: str | None = None,
    debug: bool = False,
) -> tuple[list[dict], ErrorTaxonomyAnalyzer]:
    if max_correction_attempts is None:
        max_correction_attempts = get_default_max_attempts()
    problems = load_dataset(dataset_path)
    translator = LLMTranslator(model_name=model_name, host=host)
    analyzer = ErrorTaxonomyAnalyzer()
    detailed_results = []

    for problem in problems:
        print(f"\n[{problem['id']}] {problem['text'][:100]}...")
        t0 = time.time()
        try:
            output = run_pipeline(
                problem_id=problem["id"],
                problem_text=problem["text"],
                translator=translator,
                max_correction_attempts=max_correction_attempts,
                use_llm_for_interpretation=use_llm_for_interpretation,
                debug=debug,
            )
            elapsed = time.time() - t0
            analyzer.add(output.run_record)

            detail = {
                "id": problem["id"],
                "category": problem["category"],
                "succeeded": output.run_record.succeeded,
                "n_attempts": output.run_record.n_attempts,
                "final_status": output.run_record.final_status,
                "natural_language_answer": output.natural_language_answer,
                "elapsed_seconds": round(elapsed, 2),
            }
            if output.solver_result is not None:
                detail["solver_result"] = output.solver_result.model_dump()
            if output.symbolic_model is not None:
                detail["formalism"] = output.symbolic_model.formalism
            detailed_results.append(detail)

            record = output.run_record

            if record.succeeded:
                print(f"  ->  [OK] ({record.final_status}, {record.n_attempts} tentative(s), {elapsed:.1f}s)")

                if record.final_status == "PDDL_PARSED" and output.solver_result and output.solver_result.assignment:
                    plan = output.solver_result.assignment.get("plan", [])
                    print(f"       Plan trouvé ({len(plan)} action(s)) :")
                    for i, action in enumerate(plan, 1):
                        print(f"         {i}. {action}")

                elif record.final_status == "SAT" and output.solver_result:
                    assign = output.solver_result.assignment
                    if assign:
                        print(f"       Assignment : {assign}")
                    if output.solver_result.objective_value is not None:
                        print(f"       Valeur objectif : {output.solver_result.objective_value}")

                print(f"       Réponse finale : {output.natural_language_answer}")

            else:
                print(f"  ->  [ÉCHEC] ({record.final_status}, {record.n_attempts} tentative(s), {elapsed:.1f}s)")

                if record.error_categories_encountered:
                    last_error = record.error_categories_encountered[-1]
                    print(f"       Dernière catégorie d'erreur : {last_error}")
                    print(f"       Historique complet des erreurs : {', '.join(record.error_categories_encountered)}")
                else:
                    print(f"       Détail : Aucune catégorie d'erreur enregistrée.")

        except Exception as exc:
            print(f"  ->  [ERREUR SYSTEME CRITIQUE] : {exc}")
            detailed_results.append({
                "id": problem["id"],
                "category": problem["category"],
                "succeeded": False,
                "error": str(exc),
            })

    return detailed_results, analyzer


def main():
    parser = argparse.ArgumentParser(description="Benchmark du pipeline LLM-as-a-reasoner")
    parser.add_argument("--model", default="qwen2.5-coder", help="Nom du modèle Ollama installé")
    parser.add_argument("--host", default=None, help="URL du serveur Ollama (défaut: localhost:11434)")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET), help="Chemin du dataset JSON")
    parser.add_argument("--max-attempts", type=int, default=get_default_max_attempts(),
                        help="Nombre max de tentatives de correction (défaut : env LLM_REASONER_MAX_ATTEMPTS ou 5)")
    parser.add_argument("--no-llm-interpretation", action="store_true",
                         help="Désactive l'interprétation LLM (repli textuel brut, plus rapide pour les tests)")
    parser.add_argument("--debug", action="store_true",
                         help="Active l'affichage des réponses brutes du LLM pour le debugging")
    parser.add_argument("--output", default=None, help="Fichier JSON de sortie pour les résultats détaillés")
    args = parser.parse_args()

    detailed_results, analyzer = run_benchmark(
        dataset_path=Path(args.dataset),
        model_name=args.model,
        max_correction_attempts=args.max_attempts,
        use_llm_for_interpretation=not args.no_llm_interpretation,
        host=args.host,
        debug=args.debug,
    )

    summary = analyzer.summary()
    print("\n" + "=" * 60)
    print("RÉSUMÉ GÉNERAL DU BENCHMARK")
    print("=" * 60)
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "details": detailed_results}, f, indent=2, ensure_ascii=False)
        print(f"\nRésultats détaillés écrits dans {args.output}")


if __name__ == "__main__":
    main()