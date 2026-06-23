"""
Tests unitaires pour solver_backend.py.
"""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from schema import SymbolicModel, Variable  # noqa: E402
from solver_backend import solve  # noqa: E402


def test_simple_sat():
    model = SymbolicModel(
        variables=[Variable(name="x", type="Int", domain=[0, 100]),
                   Variable(name="y", type="Int", domain=[0, 100])],
        constraints=["x + y == 10", "x > 0"],
    )
    result = solve(model)
    assert result.status == "SAT"
    assert result.assignment["x"] + result.assignment["y"] == 10
    assert result.assignment["x"] > 0


def test_unsat():
    model = SymbolicModel(
        variables=[Variable(name="x", type="Int", domain=[0, 100])],
        constraints=["x > 50", "x < 10"],
    )
    # NB: validate() détecterait ce cas en amont (TRIVIALLY_UNSAT), mais le
    # solveur doit aussi être capable de répondre UNSAT s'il est appelé directement.
    result = solve(model)
    assert result.status == "UNSAT"


def test_optimization():
    model = SymbolicModel(
        variables=[Variable(name="x", type="Int", domain=[0, 20]),
                   Variable(name="y", type="Int", domain=[0, 20])],
        constraints=["x + y <= 20", "x >= 2"],
        objective="maximize x + y",
    )
    result = solve(model)
    assert result.status == "SAT"
    assert result.objective_value == 20.0


def test_boolean_sat():
    model = SymbolicModel(
        variables=[Variable(name="a", type="Bool"), Variable(name="b", type="Bool")],
        constraints=["Or(a, b)", "Not(And(a, b))"],
        problem_type="sat_boolean",
    )
    result = solve(model)
    assert result.status == "SAT"
    assert result.assignment["a"] != result.assignment["b"]  # XOR garanti par les contraintes


def test_classic_word_problem():
    """Alice a 3x plus de billes que Bob, ensemble 40 billes."""
    model = SymbolicModel(
        variables=[Variable(name="alice", type="Int", domain=[0, 1000]),
                   Variable(name="bob", type="Int", domain=[0, 1000])],
        constraints=["alice == 3 * bob", "alice + bob == 40"],
    )
    result = solve(model)
    assert result.status == "SAT"
    assert result.assignment["bob"] == 10
    assert result.assignment["alice"] == 30
