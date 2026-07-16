"""
Démo en ligne de commande : pose une question en langage naturel, le pipeline
la traduit, la résout, et renvoie une réponse.

Usage :
    python demo.py --model qwen2.5-coder "Alice a 3 fois plus de billes que Bob, ensemble 40 billes. Combien Bob en a ?"

Prérequis : Ollama installé et lancé (`ollama serve`), avec le modèle choisi
téléchargé (`ollama pull qwen2.5-coder`).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from config import get_default_max_attempts  # noqa: E402
from pipeline import run_pipeline  # noqa: E402
from translator import LLMTranslator  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Démo du pipeline LLM-as-a-reasoner")
    parser.add_argument("problem", help="Énoncé du problème en langage naturel")
    parser.add_argument("--model", default="qwen2.5-coder", help="Modèle Ollama à utiliser")
    parser.add_argument("--host", default=None, help="URL du serveur Ollama")
    parser.add_argument("--max-attempts", type=int, default=get_default_max_attempts(),
                        help="Tentatives de correction (défaut : env LLM_REASONER_MAX_ATTEMPTS ou 5)")
    parser.add_argument("--verbose", action="store_true", help="Affiche le modèle symbolique et le résultat brut")
    args = parser.parse_args()

    translator = LLMTranslator(model_name=args.model, host=args.host)

    print(f"Question : {args.problem}\n")
    print("Traduction et résolution en cours...\n")

    output = run_pipeline(
        problem_id="cli_demo",
        problem_text=args.problem,
        translator=translator,
        max_correction_attempts=args.max_attempts,
    )

    if args.verbose:
        print("--- Modèle symbolique ---")
        print(output.symbolic_model.model_dump_json(indent=2) if output.symbolic_model else "Aucun (échec de traduction)")
        print("\n--- Résultat solveur ---")
        print(output.solver_result)
        print(f"\n--- Tentatives : {output.run_record.n_attempts} ---")
        print(f"--- Erreurs rencontrées : {output.run_record.error_categories_encountered} ---\n")

    print("Réponse :")
    print(output.natural_language_answer)


if __name__ == "__main__":
    main()
