"""
Backend de résolution.

Gère quatre cas via la même API :
  - satisfiabilité booléenne (`formalism="sat"`)
  - satisfiabilité arithmétique SMT / CSP (`formalism="smt"` ou `"csp"`)
  - optimisation (champ `objective`)
  - planification PDDL (`formalism="pddl"`)

Réutilise les helpers de `validator.py` pour garantir que la sémantique
résolue est identique à la sémantique validée.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Set

import z3

from schema import SolverResult, SymbolicModel, Variable
from validator import add_domain_constraints, build_z3_vars, compile_constraint, _safe_pddl_parse


def _num_to_float(val: z3.ExprRef) -> float:
    """Convertit une valeur numérique Z3 (entier, rationnel, algébrique) en float."""
    if z3.is_int_value(val):
        return float(val.as_long())
    if z3.is_rational_value(val):
        return float(val.as_fraction())
    return float(val.as_decimal(12).rstrip("?"))


def _extract_value(z3_model: z3.ModelRef, var: Variable, z3_var: z3.ExprRef):
    """Extrait la valeur d'une variable du modèle Z3 dans un type Python natif."""
    val = z3_model.eval(z3_var, model_completion=True)
    if var.type == "Bool":
        return z3.is_true(val)
    if var.type == "Real":
        return _num_to_float(val)
    return val.as_long()


# --------------------------------------------------------------------------- #
# Z3 backend (SAT / SMT / CSP)
# --------------------------------------------------------------------------- #

def _solve_z3(model: SymbolicModel) -> SolverResult:
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


# --------------------------------------------------------------------------- #
# PDDL backend (forward search)
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class _GroundedAction:
    name: str
    precondition: tuple
    effect: tuple


def _substitute_pddl(expr, binding: Dict[str, str]):
    """Substitue les variables ?x par leur valeur dans binding."""
    if isinstance(expr, str):
        return binding.get(expr, expr)
    if isinstance(expr, tuple):
        return tuple(_substitute_pddl(e, binding) for e in expr)
    return expr


def _ground_actions(model: SymbolicModel) -> List[_GroundedAction]:
    """Génère toutes les instances groundées des actions PDDL."""
    objects = [v.name for v in model.variables if v.type == "Object"]
    grounded: List[_GroundedAction] = []
    for action in (model.actions or []):
        params = list(action.parameters.keys())
        if not params:
            pre = _safe_pddl_parse(action.precondition)
            eff = _safe_pddl_parse(action.effect)
            grounded.append(_GroundedAction(name=action.name, precondition=pre, effect=eff))
            continue
        import itertools
        for combo in itertools.product(objects, repeat=len(params)):
            binding = dict(zip(params, combo))
            name_ground = f"{action.name}({', '.join(combo)})"
            pre = _substitute_pddl(_safe_pddl_parse(action.precondition), binding)
            eff = _substitute_pddl(_safe_pddl_parse(action.effect), binding)
            grounded.append(_GroundedAction(name=name_ground, precondition=pre, effect=eff))
    return grounded


def _pddl_expr_holds(state: Set[tuple], expr) -> bool:
    """Vérifie si une expression PDDL est satisfaite dans un état."""
    if isinstance(expr, tuple):
        if expr[0] == "AND":
            return all(_pddl_expr_holds(state, e) for e in expr[1:])
        if expr[0] == "OR":
            return any(_pddl_expr_holds(state, e) for e in expr[1:])
        if expr[0] == "NOT":
            return not _pddl_expr_holds(state, expr[1])
        # Prédicat positif
        return expr in state
    if isinstance(expr, str):
        return expr in state
    return False


def _apply_pddl_effect(state: Set[tuple], expr) -> Set[tuple]:
    """Applique un effet PDDL à un état."""
    new_state = set(state)
    if isinstance(expr, tuple):
        if expr[0] == "AND":
            for e in expr[1:]:
                new_state = _apply_pddl_effect(new_state, e)
            return new_state
        if expr[0] == "NOT":
            pred = expr[1]
            if pred in new_state:
                new_state.remove(pred)
            return new_state
        # Ajout de prédicat
        new_state.add(expr)
        return new_state
    return new_state


def _solve_pddl(model: SymbolicModel) -> SolverResult:
    """Planificateur forward-search (BFS) pour problèmes PDDL."""
    try:
        # État initial
        init_state: Set[tuple] = set()
        for pred_str in (model.init or []):
            init_state.add(_safe_pddl_parse(pred_str))
        init_frozen = frozenset(init_state)

        # But
        goal_expr = _safe_pddl_parse(model.goal) if model.goal else ("AND",)

        # Actions groundées
        grounded = _ground_actions(model)

        # BFS
        queue = deque([(init_frozen, [])])
        visited: Set[frozenset] = {init_frozen}
        max_depth = 15  # limite de sécurité

        while queue:
            state, plan = queue.popleft()
            if len(plan) > max_depth:
                continue

            if _pddl_expr_holds(set(state), goal_expr):
                return SolverResult(
                    status="PDDL_PARSED",
                    assignment={"plan": plan},
                )

            for action in grounded:
                if _pddl_expr_holds(set(state), action.precondition):
                    new_state = frozenset(_apply_pddl_effect(set(state), action.effect))
                    if new_state not in visited:
                        visited.add(new_state)
                        queue.append((new_state, plan + [action.name]))

        # Aucun plan trouvé dans la limite de profondeur
        return SolverResult(status="UNSAT")

    except Exception as exc:  # noqa: BLE001
        return SolverResult(status="ERROR", error_message=f"erreur PDDL : {exc}")


# --------------------------------------------------------------------------- #
# API publique
# --------------------------------------------------------------------------- #

def solve(model: SymbolicModel) -> SolverResult:
    """Résout (ou optimise / planifie) un modèle symbolique."""
    if model.formalism == "pddl":
        return _solve_pddl(model)
    # sat, smt, csp -> Z3
    return _solve_z3(model)