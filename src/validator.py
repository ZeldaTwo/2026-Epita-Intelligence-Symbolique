"""
Validation syntaxique et sémantique d'un `SymbolicModel`.

La validation se fait en plusieurs passes, chacune associée à une catégorie de
la taxonomie d'erreurs :

1. analyse AST des contraintes        -> SYNTAX_ERROR / MISSING_VARIABLE
2. compilation en expressions Z3      -> SYNTAX_ERROR
3. vérification de typage (booléen)   -> TYPE_MISMATCH
4. test de satisfiabilité rapide      -> TRIVIALLY_UNSAT

Les helpers `build_z3_vars`, `compile_constraint` et `add_domain_constraints`
sont réutilisés par `solver_backend.py` pour éviter toute divergence entre la
sémantique validée et la sémantique résolue.
"""

from __future__ import annotations

import ast
from typing import Dict, Optional, Tuple

import z3

from schema import ErrorCategory, SymbolicModel, ValidationResult

# Fonctions Z3 autorisées dans les expressions de contraintes. Les opérateurs
# (+, -, *, ==, <, >, ...) sont gérés nativement par la surcharge d'opérateurs Z3.
Z3_FUNCTIONS = {
    "And": z3.And,
    "Or": z3.Or,
    "Not": z3.Not,
    "Implies": z3.Implies,
    "Xor": z3.Xor,
    "If": z3.If,
    "Sum": z3.Sum,
    "Product": z3.Product,
    "Distinct": z3.Distinct,
    "Abs": lambda e: z3.If(e >= 0, e, -e),
}


def build_z3_vars(model: SymbolicModel) -> Dict[str, z3.ExprRef]:
    """Construit les variables Z3 à partir des déclarations du modèle."""
    z3_vars: Dict[str, z3.ExprRef] = {}
    for v in model.variables:
        if v.type == "Int":
            z3_vars[v.name] = z3.Int(v.name)
        elif v.type == "Real":
            z3_vars[v.name] = z3.Real(v.name)
        elif v.type == "Bool":
            z3_vars[v.name] = z3.Bool(v.name)
        else:  # pragma: no cover - déjà filtré par le schéma Pydantic
            raise ValueError(f"type de variable inconnu : {v.type}")
    return z3_vars


def compile_constraint(expr_str: str, z3_vars: Dict[str, z3.ExprRef]) -> z3.ExprRef:
    """Compile une chaîne de contrainte en expression Z3.

    L'évaluation se fait dans un espace de noms restreint (pas de `__builtins__`)
    contenant uniquement les variables déclarées et les fonctions Z3 autorisées.
    """
    namespace: Dict[str, object] = {"__builtins__": {}}
    namespace.update(Z3_FUNCTIONS)
    namespace.update(z3_vars)
    return eval(expr_str, namespace)  # noqa: S307 - espace de noms contrôlé


def add_domain_constraints(
    solver: z3.Solver, model: SymbolicModel, z3_vars: Dict[str, z3.ExprRef]
) -> None:
    """Ajoute les bornes de domaine [min, max] des variables numériques."""
    for v in model.variables:
        if v.domain is not None and v.type in ("Int", "Real"):
            lo, hi = v.domain
            solver.add(z3_vars[v.name] >= lo)
            solver.add(z3_vars[v.name] <= hi)


def _collect_names(tree: ast.AST) -> set[str]:
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def validate(
    model: SymbolicModel,
) -> Tuple[ValidationResult, Optional[Dict[str, z3.ExprRef]]]:
    """Valide un modèle symbolique.

    Renvoie un couple `(ValidationResult, z3_vars)`. En cas d'échec, `z3_vars`
    vaut `None`. En cas de succès, `z3_vars` contient les variables Z3 prêtes
    à être réutilisées par le solveur.
    """
    declared = {v.name for v in model.variables}
    allowed_names = declared | set(Z3_FUNCTIONS)

    # --- Passe 1 : analyse syntaxique + variables non déclarées ---
    for constraint in model.constraints:
        try:
            tree = ast.parse(constraint, mode="eval")
        except SyntaxError as exc:
            return (
                ValidationResult(
                    is_valid=False,
                    category=ErrorCategory.SYNTAX_ERROR,
                    message=f"contrainte non analysable '{constraint}' : {exc.msg}",
                ),
                None,
            )
        for name in _collect_names(tree):
            if name not in allowed_names:
                return (
                    ValidationResult(
                        is_valid=False,
                        category=ErrorCategory.MISSING_VARIABLE,
                        message=(
                            f"la variable '{name}' utilisée dans "
                            f"'{constraint}' n'est pas déclarée"
                        ),
                    ),
                    None,
                )

    # --- Passe 2 + 3 : compilation Z3 + typage booléen ---
    z3_vars = build_z3_vars(model)
    compiled: list[z3.ExprRef] = []
    for constraint in model.constraints:
        try:
            expr = compile_constraint(constraint, z3_vars)
        except Exception as exc:  # noqa: BLE001 - on classe toute erreur de compile
            return (
                ValidationResult(
                    is_valid=False,
                    category=ErrorCategory.SYNTAX_ERROR,
                    message=f"contrainte non compilable '{constraint}' : {exc}",
                ),
                None,
            )
        if not z3.is_bool(expr):
            return (
                ValidationResult(
                    is_valid=False,
                    category=ErrorCategory.TYPE_MISMATCH,
                    message=(
                        f"la contrainte '{constraint}' ne produit pas une "
                        "expression booléenne"
                    ),
                ),
                None,
            )
        compiled.append(expr)

    # --- Passe 4 : satisfiabilité (contraintes mutuellement contradictoires) ---
    checker = z3.Solver()
    add_domain_constraints(checker, model, z3_vars)
    for expr in compiled:
        checker.add(expr)
    if checker.check() == z3.unsat:
        return (
            ValidationResult(
                is_valid=False,
                category=ErrorCategory.TRIVIALLY_UNSAT,
                message="les contraintes sont mutuellement contradictoires (UNSAT)",
            ),
            None,
        )

    return ValidationResult(is_valid=True, message="modèle valide"), z3_vars
