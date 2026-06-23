"""
Backend de résolution Z3.

Gère trois cas via la même API :
  - satisfiabilité booléenne (`problem_type="sat_boolean"`)
  - satisfiabilité arithmétique SMT
  - optimisation (champ `objective`, ex: "maximize 20*x + 50*y")

Réutilise les helpers de `validator.py` pour garantir que la sémantique
résolue est identique à la sémantique validée.
"""

from __future__ import annotations

import z3

from schema import SolverResult, SymbolicModel, Variable
from validator import add_domain_constraints, build_z3_vars, compile_constraint


def _num_to_float(val: z3.ExprRef) -> float:
    """Convertit une valeur numérique Z3 (entier, rationnel, algébrique) en float."""
    if z3.is_int_value(val):
        return float(val.as_long())
    if z3.is_rational_value(val):
        return float(val.as_fraction())
    # Valeur algébrique (racines, etc.) : approximation décimale.
    return float(val.as_decimal(12).rstrip("?"))


def _extract_value(z3_model: z3.ModelRef, var: Variable, z3_var: z3.ExprRef):
    """Extrait la valeur d'une variable du modèle Z3 dans un type Python natif."""
    val = z3_model.eval(z3_var, model_completion=True)
    if var.type == "Bool":
        return z3.is_true(val)
    if var.type == "Real":
        return _num_to_float(val)
    return val.as_long()


def solve(model: SymbolicModel) -> SolverResult:
    """Résout (ou optimise) un modèle symbolique et renvoie un `SolverResult`."""
    try:
        z3_vars = build_z3_vars(model)
        constraints = [compile_constraint(c, z3_vars) for c in model.constraints]
    except Exception as exc:  # noqa: BLE001
        return SolverResult(status="ERROR", error_message=str(exc))

    is_optimization = model.objective is not None
    solver = z3.Optimize() if is_optimization else z3.Solver()

    add_domain_constraints(solver, model, z3_vars)
    for constraint in constraints:
        solver.add(constraint)

    obj_expr = None
    direction = ""
    if is_optimization:
        direction, _, expr_str = model.objective.partition(" ")
        direction = direction.lower()
        expr_str = expr_str.strip()
        if not expr_str:
            return SolverResult(
                status="ERROR",
                error_message=f"objectif mal formé : '{model.objective}'",
            )
        try:
            obj_expr = compile_constraint(expr_str, z3_vars)
        except Exception as exc:  # noqa: BLE001
            return SolverResult(
                status="ERROR", error_message=f"objectif invalide : {exc}"
            )
        if direction.startswith("max"):
            solver.maximize(obj_expr)
        elif direction.startswith("min"):
            solver.minimize(obj_expr)
        else:
            return SolverResult(
                status="ERROR",
                error_message=f"direction d'objectif inconnue : '{direction}'",
            )

    check = solver.check()
    if check == z3.sat:
        z3_model = solver.model()
        assignment = {
            v.name: _extract_value(z3_model, v, z3_vars[v.name])
            for v in model.variables
        }
        objective_value = None
        if obj_expr is not None:
            objective_value = _num_to_float(z3_model.eval(obj_expr, model_completion=True))
        return SolverResult(
            status="SAT", assignment=assignment, objective_value=objective_value
        )
    if check == z3.unsat:
        return SolverResult(status="UNSAT")
    return SolverResult(status="UNKNOWN", error_message=str(solver.reason_unknown()))
