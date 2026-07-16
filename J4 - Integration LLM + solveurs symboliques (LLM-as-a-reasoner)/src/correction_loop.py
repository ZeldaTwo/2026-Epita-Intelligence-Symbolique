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

from config import get_default_max_attempts
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


def _debug_print(debug: bool, *args, **kwargs):
    if debug:
        print(*args, **kwargs)


def run_correction_loop(
    problem_text: str,
    translator,
    max_attempts: Optional[int] = None,
    debug: bool = False,
) -> CorrectionResult:
    """Traduit + valide avec re-prompting jusqu'à obtenir un modèle valide.

    `max_attempts=None` -> valeur par défaut centralisée (config, surchargeable
    par la variable d'environnement LLM_REASONER_MAX_ATTEMPTS).
    """
    if max_attempts is None:
        max_attempts = get_default_max_attempts()
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
            _debug_print(
                debug,
                f"    [DEBUG T{attempt}] Réponse brute du LLM :\n{'-'*60}",
            )
            _debug_print(debug, raw)
            _debug_print(debug, f"{'-'*60}")
        except Exception as exc:
            errors.append(ErrorCategory.LLM_RESPONSE_ERROR)
            last_message = f"échec d'appel au modèle : {exc}"
            _debug_print(debug, f"    [DEBUG T{attempt}] Échec appel LLM : {last_message}")
            feedback = last_message
            continue

        # 2. Parsing JSON + conformité Pydantic.
        model, parse_error, parse_category = parse_symbolic_model(raw)
        if model is None:
            category = parse_category or ErrorCategory.LLM_MALFORMED_JSON
            errors.append(category)
            last_message = parse_error or "réponse non conforme"
            _debug_print(debug, f"    [DEBUG T{attempt}] Échec parsing : {last_message}")
            feedback = last_message
            continue
        last_model = model

        # 3. Validation symbolique (syntaxe / variables / typage / satisfiabilité).
        result, z3_vars = validate(model)
        if not result.is_valid:
            if result.category is not None:
                errors.append(result.category)
            last_message = result.message
            _debug_print(debug, f"    [DEBUG T{attempt}] Échec validation : {last_message}")
            feedback = (
                f"Le modèle est invalide ({result.category.value if result.category else '?'}) : "
                f"{result.message}"
            )
            continue

        # Succès : modèle valide obtenu.
        _debug_print(debug, f"    [DEBUG T{attempt}] Modèle valide accepté.")
        return CorrectionResult(
            success=True,
            n_attempts=attempt,
            error_categories=errors,
            model=model,
            z3_vars=z3_vars,
            last_error_message="",
        )

    # Échec après épuisement des tentatives.
    _debug_print(debug, f"    [DEBUG] Échec définitif après {attempt} tentative(s).")
    return CorrectionResult(
        success=False,
        n_attempts=attempt,
        error_categories=errors,
        model=last_model,
        z3_vars=None,
        last_error_message=last_message,
    )