"""
Tests unitaires pour schema.py et validator.py.
Ne nécessitent PAS Ollama : ils testent uniquement la partie symbolique
(validation + résolution), indépendamment du LLM.

Lancer avec : pytest tests/ -v
"""

import sys
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from schema import ErrorCategory, SymbolicModel, Variable  # noqa: E402
from validator import validate  # noqa: E402


def test_valid_arithmetic_model():
    model = SymbolicModel(
        variables=[Variable(name="x", type="Int", domain=[0, 100]),
                   Variable(name="y", type="Int", domain=[0, 100])],
        constraints=["x + y == 10", "x > 0"],
    )
    result, z3_vars = validate(model)
    assert result.is_valid
    assert z3_vars is not None


def test_missing_variable_detected():
    model = SymbolicModel(
        variables=[Variable(name="x", type="Int", domain=[0, 100])],
        constraints=["x + z == 10"],
    )
    result, _ = validate(model)
    assert not result.is_valid
    assert result.category == ErrorCategory.MISSING_VARIABLE


def test_trivially_unsat_detected():
    model = SymbolicModel(
        variables=[Variable(name="x", type="Int", domain=[0, 100])],
        constraints=["x > 50", "x < 10"],
    )
    result, _ = validate(model)
    assert not result.is_valid
    assert result.category == ErrorCategory.TRIVIALLY_UNSAT


def test_invalid_identifier_rejected_by_pydantic():
    with pytest.raises(Exception):
        SymbolicModel(
            variables=[Variable(name="2x", type="Int")],  # identifiant invalide
            constraints=["2x > 0"],
        )


def test_boolean_model_valid():
    model = SymbolicModel(
        variables=[Variable(name="a", type="Bool"), Variable(name="b", type="Bool")],
        constraints=["Or(a, b)", "Not(And(a, b))"],
        problem_type="sat_boolean",
    )
    result, _ = validate(model)
    assert result.is_valid
