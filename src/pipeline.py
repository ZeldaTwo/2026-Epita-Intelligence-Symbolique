"""
Orchestration bout-en-bout du pipeline LLM-as-a-reasoner :

    [NL] -> traduction (avec boucle de correction)
         -> validation
         -> résolution Z3
         -> interprétation en langage naturel

Renvoie un `PipelineOutput` contenant à la fois la réponse finale et une trace
complète (`PipelineRunRecord`) exploitable par l'analyseur de taxonomie.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from correction_loop import run_correction_loop
from error_taxonomy import PipelineRunRecord
from interpreter import interpret_with_llm, interpret_without_llm
from schema import SolverResult, SymbolicModel
from solver_backend import solve


@dataclass
class PipelineOutput:
    """Sortie complète du pipeline pour un problème."""

    run_record: PipelineRunRecord
    natural_language_answer: str
    symbolic_model: Optional[SymbolicModel] = None
    solver_result: Optional[SolverResult] = None


def run_pipeline(
    problem_id: str,
    problem_text: str,
    translator,
    max_correction_attempts: int = 3,
    use_llm_for_interpretation: bool = True,
) -> PipelineOutput:
    """Exécute le pipeline complet sur un énoncé."""
    correction = run_correction_loop(
        problem_text, translator, max_attempts=max_correction_attempts
    )

    # Cas 1 : on n'a jamais obtenu de modèle valide.
    if not correction.success:
        record = PipelineRunRecord(
            problem_id=problem_id,
            problem_text=problem_text,
            succeeded=False,
            n_attempts=correction.n_attempts,
            error_categories_encountered=correction.error_categories,
            final_status="FAILED_AFTER_RETRIES",
        )
        answer = (
            "Impossible de produire un modèle symbolique valide après "
            f"{correction.n_attempts} tentative(s). "
            f"Dernière erreur : {correction.last_error_message}"
        )
        return PipelineOutput(
            run_record=record,
            natural_language_answer=answer,
            symbolic_model=correction.model,
            solver_result=None,
        )

    # Cas 2 : modèle valide -> résolution.
    model = correction.model
    result = solve(model)

    if result.status == "SAT":
        final_status, succeeded = "SAT", True
    elif result.status == "UNSAT":
        # Réponse définitive et fidèle : le problème n'admet pas de solution.
        final_status, succeeded = "UNSAT", True
    else:
        final_status, succeeded = result.status, False

    # Interprétation en langage naturel.
    if use_llm_for_interpretation:
        try:
            answer = interpret_with_llm(problem_text, result, model, translator)
        except Exception:  # noqa: BLE001 - repli robuste si le LLM échoue
            answer = interpret_without_llm(result, model)
    else:
        answer = interpret_without_llm(result, model)

    record = PipelineRunRecord(
        problem_id=problem_id,
        problem_text=problem_text,
        succeeded=succeeded,
        n_attempts=correction.n_attempts,
        error_categories_encountered=correction.error_categories,
        final_status=final_status,
    )
    return PipelineOutput(
        run_record=record,
        natural_language_answer=answer,
        symbolic_model=model,
        solver_result=result,
    )
