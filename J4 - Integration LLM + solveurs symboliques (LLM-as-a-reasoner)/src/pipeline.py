"""
Orchestration bout-en-bout du pipeline LLM-as-a-reasoner :

    [NL] -> traduction (avec boucle de correction)
         -> validation
         -> résolution
         -> interprétation en langage naturel

Renvoie un `PipelineOutput` contenant à la fois la réponse finale et une trace
complète (`PipelineRunRecord`) exploitable par l'analyseur de taxonomie.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from config import get_default_max_attempts
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
    max_correction_attempts: Optional[int] = None,
    use_llm_for_interpretation: bool = True,
    debug: bool = False,
) -> PipelineOutput:
    """Exécute le pipeline complet sur un énoncé.

    `max_correction_attempts=None` -> valeur par défaut centralisée (config,
    surchargeable par la variable d'environnement LLM_REASONER_MAX_ATTEMPTS).
    """
    if max_correction_attempts is None:
        max_correction_attempts = get_default_max_attempts()

    correction = run_correction_loop(
        problem_text,
        translator,
        max_attempts=max_correction_attempts,
        debug=debug,
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

    # Cas 2 : modèle valide -> résolution selon le formalisme.
    model = correction.model
    result = solve(model)

    # Détermination du statut final avec vérification de cohérence.
    if model.expected_status == "UNSAT":
        if result.status == "UNSAT":
            final_status, succeeded = "UNSAT_PROVEN", True
        elif result.status == "SAT":
            # Le LLM a mal traduit : le modèle est faussement satisfiable
            final_status, succeeded = "UNSAT_BUT_SAT", False
            # Forcer le message d'erreur pour la boucle de correction
            feedback = (
                f"Le modèle est SAT (solution trouvée : {result.assignment}) "
                f"alors que l'énoncé attend UNSAT. Les contraintes sont "
                f"probablement incomplètes. Vérifie que toutes les conditions "
                f"de l'énoncé sont traduites sans simplification."
            )
            # On pourrait relancer la boucle ici, mais pour l'instant on marque l'échec
        else:
            final_status, succeeded = result.status, False
    elif result.status in ("SAT", "PDDL_PARSED"):
        final_status, succeeded = result.status, True
    elif result.status == "UNSAT":
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