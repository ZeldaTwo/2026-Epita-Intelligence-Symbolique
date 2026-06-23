"""
Boucle de correction (re-prompting).

Tente de traduire un énoncé en un `SymbolicModel` VALIDE. À chaque échec
(JSON malformé, variable manquante, erreur de syntaxe/type, contraintes
contradictoires), on renvoie un retour d'erreur au LLM et on retente, jusqu'à
`max_attempts`.

Chaque catégorie d'erreur rencontrée est tracée : c'est la matière première de
la taxonomie d'erreurs (`error_taxonomy.py`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from schema import ErrorCategory, SymbolicModel
from translator import parse_symbolic_model
from validator import validate


@dataclass
class CorrectionResult:
    """Résultat de la boucle de correction."""

    success: bool
    n_attempts: int
    error_categories: List[ErrorCategory] = field(default_factory=list)
    model: Optional[SymbolicModel] = None
    z3_vars: Optional[Dict] = None
    last_error_message: str = ""


def run_correction_loop(
    problem_text: str, translator, max_attempts: int = 3
) -> CorrectionResult:
    """Traduit + valide avec re-prompting jusqu'à obtenir un modèle valide."""
    errors: List[ErrorCategory] = []
    feedback: Optional[str] = None
    last_model: Optional[SymbolicModel] = None
    last_message = ""
    attempt = 0

    while attempt < max_attempts:
        attempt += 1

        # 1. Appel au LLM (la traduction elle-même peut échouer).
        try:
            raw = translator.translate(problem_text, error_feedback=feedback)
        except Exception as exc:  # noqa: BLE001
            errors.append(ErrorCategory.LLM_MALFORMED_JSON)
            last_message = f"échec d'appel au modèle : {exc}"
            feedback = last_message
            continue

        # 2. Parsing JSON + conformité Pydantic.
        model, parse_error = parse_symbolic_model(raw)
        if model is None:
            errors.append(ErrorCategory.LLM_MALFORMED_JSON)
            last_message = parse_error or "réponse non conforme"
            feedback = last_message
            continue
        last_model = model

        # 3. Validation symbolique (syntaxe / variables / typage / satisfiabilité).
        result, z3_vars = validate(model)
        if not result.is_valid:
            if result.category is not None:
                errors.append(result.category)
            last_message = result.message
            feedback = (
                f"Le modèle est invalide ({result.category.value if result.category else '?'}) : "
                f"{result.message}"
            )
            continue

        # Succès : modèle valide obtenu.
        return CorrectionResult(
            success=True,
            n_attempts=attempt,
            error_categories=errors,
            model=model,
            z3_vars=z3_vars,
            last_error_message="",
        )

    # Échec après épuisement des tentatives.
    return CorrectionResult(
        success=False,
        n_attempts=attempt,
        error_categories=errors,
        model=last_model,
        z3_vars=None,
        last_error_message=last_message,
    )
