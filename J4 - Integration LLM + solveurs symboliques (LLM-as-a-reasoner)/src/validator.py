"""
Validation syntaxique et sémantique d'un `SymbolicModel`.

La validation se fait en plusieurs passes, chacune associée à une catégorie de
la taxonomie d'erreurs :

1. analyse AST des contraintes        -> SYNTAX_ERROR / MISSING_VARIABLE
2. compilation en expressions Z3      -> SYNTAX_ERROR
3. vérification de typage (booléen)   -> TYPE_MISMATCH
"""

from __future__ import annotations

import ast
import re
from typing import Dict, Optional, Tuple

import z3

from schema import ErrorCategory, SymbolicModel, ValidationResult

# Fonctions Z3 autorisées dans les expressions de contraintes.
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
        elif v.type == "Object":
            raise ValueError(
                f"type 'Object' non supporté par le backend Z3 (formalism='{model.formalism}' "
                f"devrait être 'pddl')"
            )
        else:
            raise ValueError(f"type de variable inconnu : {v.type}")
    return z3_vars


def compile_constraint(expr_str: str, z3_vars: Dict[str, z3.ExprRef]) -> z3.ExprRef:
    """Compile une chaîne de contrainte en expression Z3."""
    namespace: Dict[str, object] = {"__builtins__": {}}
    namespace.update(Z3_FUNCTIONS)
    namespace.update(z3_vars)
    return eval(expr_str, namespace)


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


# Mots-clés booléens Python -> fonction Z3 équivalente.
# Ces mots-clés ne fonctionnent PAS sur des expressions Z3 symboliques : Python
# tente de les convertir en booléen concret et lève
# « Symbolic expressions cannot be cast to concrete Boolean values ».
_PYTHON_BOOL_OP_HINTS = {
    ast.And: "'and' -> utilise And(a, b, ...)",
    ast.Or: "'or' -> utilise Or(a, b, ...)",
    ast.Not: "'not' -> utilise Not(a)",
}


def _detect_python_bool_operators(tree: ast.AST) -> list[str]:
    """Repère l'usage des mots-clés booléens Python (and / or / not).

    Renvoie la liste (ordonnée, sans doublon) des indices de correction à
    fournir au LLM. Cette détection en amont transforme une erreur Z3 cryptique
    (levée plus tard à la compilation) en un message ACTIONNABLE, ce qui permet
    à la boucle de correction de converger.
    """
    hints: list[str] = []
    for node in ast.walk(tree):
        op_type = None
        if isinstance(node, ast.BoolOp):  # 'and' / 'or'
            op_type = type(node.op)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):  # 'not'
            op_type = ast.Not
        if op_type is not None:
            hint = _PYTHON_BOOL_OP_HINTS[op_type]
            if hint not in hints:
                hints.append(hint)
    return hints


# --------------------------------------------------------------------------- #
# Helpers PDDL (partagés avec solver_backend)
# --------------------------------------------------------------------------- #

def _safe_pddl_parse(expr_str: str):
    """Parse une expression PDDL en remplaçant temporairement les variables ?x."""
    mapping: Dict[str, str] = {}

    def repl(m: re.Match) -> str:
        var = m.group(0)
        safe = "_VAR_" + var[1:]
        mapping[safe] = var
        return safe

    safe_str = re.sub(r"\?\w+", repl, expr_str)
    tree = ast.parse(safe_str.strip(), mode="eval")

    def ast_to_pddl(node):
        if isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else str(node.func)
            args = [ast_to_pddl(arg) for arg in node.args]
            if func_name in ("And", "Or", "Not"):
                return (func_name.upper(),) + tuple(args)
            return (func_name,) + tuple(args)
        if isinstance(node, ast.Name):
            return mapping.get(node.id, node.id)
        if isinstance(node, ast.Constant):
            return node.value
        raise ValueError(f"noeud AST non supporté : {type(node)}")

    return ast_to_pddl(tree.body)


def _validate_pddl(model: SymbolicModel) -> Tuple[ValidationResult, Optional[Dict[str, z3.ExprRef]]]:
    """Valide un modèle PDDL (syntaxe des actions, présence des champs)."""
    msgs = []
    if not model.init:
        msgs.append("init manquant ou vide")
    if not model.goal:
        msgs.append("goal manquant ou vide")
    if not model.actions:
        msgs.append("actions manquantes ou vides")

    for action in (model.actions or []):
        try:
            _safe_pddl_parse(action.precondition)
            _safe_pddl_parse(action.effect)
        except Exception as exc:
            msgs.append(f"action '{action.name}' : syntaxe invalide ({exc})")

    if msgs:
        return (
            ValidationResult(
                is_valid=False,
                category=ErrorCategory.SYNTAX_ERROR,
                message="; ".join(msgs),
            ),
            None,
        )

    return ValidationResult(is_valid=True, message="modèle PDDL valide"), None


# --------------------------------------------------------------------------- #
# Validation principale
# --------------------------------------------------------------------------- #

def validate(
    model: SymbolicModel,
) -> Tuple[ValidationResult, Optional[Dict[str, z3.ExprRef]]]:
    """Valide un modèle symbolique.

    Renvoie un couple `(ValidationResult, z3_vars)`. En cas d'échec, `z3_vars`
    vaut `None`. En cas de succès, `z3_vars` contient les variables Z3 prêtes
    à être réutilisées par le solveur.
    """
    if model.formalism == "pddl":
        return _validate_pddl(model)

    # Cohérence type/formalisme : le type 'Object' est réservé à PDDL. S'il
    # apparaît dans un modèle sat/smt/csp, c'est une erreur de traduction. On la
    # rend explicite et CORRIGEABLE (message actionnable pour la boucle de
    # correction) au lieu de laisser build_z3_vars lever une exception qui
    # ferait planter tout le pipeline.
    object_vars = [v.name for v in model.variables if v.type == "Object"]
    if object_vars:
        return (
            ValidationResult(
                is_valid=False,
                category=ErrorCategory.TYPE_MISMATCH,
                message=(
                    f"la/les variable(s) {object_vars} sont de type 'Object', "
                    f"réservé au formalisme 'pddl'. Pour un modèle "
                    f"'{model.formalism}', déclare chaque variable en 'Int' "
                    f"(avec un 'domain' [min, max] pour un CSP), 'Bool' ou 'Real'."
                ),
            ),
            None,
        )

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

        # Détection des opérateurs booléens Python (and / or / not) AVANT la
        # compilation Z3 : sans ça, l'erreur remonte sous une forme cryptique
        # (« cannot be cast to concrete Boolean values ») qui n'indique pas au
        # LLM quoi corriger, et la boucle de correction tourne en rond.
        bool_op_hints = _detect_python_bool_operators(tree)
        if bool_op_hints:
            return (
                ValidationResult(
                    is_valid=False,
                    category=ErrorCategory.SYNTAX_ERROR,
                    message=(
                        f"contrainte '{constraint}' : les mots-clés booléens "
                        f"Python sont interdits. Remplace-les par les fonctions "
                        f"Z3 correspondantes ({'; '.join(bool_op_hints)})."
                    ),
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
    try:
        z3_vars = build_z3_vars(model)
    except Exception as exc:  # noqa: BLE001 - filet de sécurité anti-crash
        return (
            ValidationResult(
                is_valid=False,
                category=ErrorCategory.TYPE_MISMATCH,
                message=f"construction des variables Z3 impossible : {exc}",
            ),
            None,
        )
    compiled: list[z3.ExprRef] = []
    for constraint in model.constraints:
        try:
            expr = compile_constraint(constraint, z3_vars)
        except Exception as exc:  # noqa: BLE001
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

    return ValidationResult(is_valid=True, message="modèle valide"), z3_vars