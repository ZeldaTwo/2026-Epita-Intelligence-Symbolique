"""
Modèle symbolique intermédiaire (Pydantic) et types partagés par tout le pipeline.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

# Types de variables supportés par les backends Z3 + PDDL.
SUPPORTED_TYPES = {"Int", "Real", "Bool", "Object"}
# Types de problème reconnus (purement informatif côté solveur générique Z3).
SUPPORTED_PROBLEM_TYPES = {"smt_arithmetic", "sat_boolean"}


class ErrorCategory(str, Enum):
    """Catégories d'erreur de la taxonomie (cf. README)."""

    LLM_MALFORMED_JSON = "llm_malformed_json"
    LLM_RESPONSE_ERROR = "llm_response_error"
    MISSING_VARIABLE = "missing_variable"
    SYNTAX_ERROR = "syntax_error"
    TYPE_MISMATCH = "type_mismatch"
    TRIVIALLY_UNSAT = "trivially_unsat"
    SEMANTIC_MISMATCH = "semantic_mismatch"


class Variable(BaseModel):
    """Une variable de décision déclarée dans le modèle symbolique."""

    name: str
    type: str = "Int"  # "Int" | "Real" | "Bool" | "Object"
    # Bornes [min, max] pour les variables numériques (ignorées pour Bool/Object).
    domain: Optional[List[int]] = None

    @field_validator("name")
    @classmethod
    def _name_must_be_identifier(cls, v: str) -> str:
        if not v.isidentifier():
            raise ValueError(f"'{v}' n'est pas un identifiant valide pour une variable")
        return v

    @field_validator("type")
    @classmethod
    def _type_must_be_supported(cls, v: str) -> str:
        if v not in SUPPORTED_TYPES:
            raise ValueError(
                f"type '{v}' non supporté (attendu: {sorted(SUPPORTED_TYPES)})"
            )
        return v

    @field_validator("domain")
    @classmethod
    def _domain_must_be_pair(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is None:
            return v
        if len(v) != 2:
            raise ValueError("domain doit être une paire [min, max]")
        if v[0] > v[1]:
            raise ValueError("domain invalide : min > max")
        return v


class PDDLAction(BaseModel):
    """Action PDDL pour la planification."""

    name: str
    parameters: Dict[str, str] = Field(default_factory=dict)
    precondition: str
    effect: str


class SymbolicModel(BaseModel):
    """Représentation symbolique intermédiaire d'un problème en langage naturel."""

    formalism: str = "smt"  # "sat" | "smt" | "csp" | "pddl"
    variables: List[Variable]
    constraints: List[str] = Field(default_factory=list)
    problem_type: str = "smt_arithmetic"  # "smt_arithmetic" | "sat_boolean"
    # Objectif d'optimisation optionnel, ex: "maximize 20*x + 50*y".
    objective: Optional[str] = None
    # Champs spécifiques PDDL.
    init: Optional[List[str]] = None
    goal: Optional[str] = None
    actions: Optional[List[PDDLAction]] = None
    expected_status: Optional[str] = Field(
    default=None,
    description="Statut attendu du solveur (ex: 'UNSAT' pour prouver l'impossibilité)"
)

    @field_validator("formalism")
    @classmethod
    def _formalism_known(cls, v: str) -> str:
        if v not in {"sat", "smt", "csp", "pddl"}:
            raise ValueError(f"formalism '{v}' inconnu (attendu: sat, smt, csp, pddl)")
        return v

    @field_validator("problem_type")
    @classmethod
    def _problem_type_known(cls, v: str) -> str:
        if v not in SUPPORTED_PROBLEM_TYPES:
            raise ValueError(
                f"problem_type '{v}' inconnu (attendu: {sorted(SUPPORTED_PROBLEM_TYPES)})"
            )
        return v


class ValidationResult(BaseModel):
    """Résultat d'une validation syntaxique + sémantique d'un `SymbolicModel`."""

    is_valid: bool
    category: Optional[ErrorCategory] = None
    message: str = ""


class SolverResult(BaseModel):
    """Résultat brut renvoyé par le backend de résolution."""

    status: str  # "SAT" | "UNSAT" | "UNKNOWN" | "ERROR" | "PDDL_PARSED"
    assignment: Optional[Dict[str, Any]] = None
    objective_value: Optional[float] = None
    error_message: Optional[str] = None