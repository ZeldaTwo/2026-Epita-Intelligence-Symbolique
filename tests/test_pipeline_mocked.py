"""
Tests d'intégration du pipeline complet AVEC un LLM mocké.

Aucune dépendance à Ollama : on injecte un faux traducteur qui renvoie des
réponses JSON prédéfinies. On valide ainsi la boucle de correction de bout en
bout (succès direct, succès après correction, échec définitif) ainsi que le
chemin d'interprétation LLM.

Lancer avec : pytest tests/ -v
"""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from pipeline import run_pipeline  # noqa: E402
from schema import ErrorCategory  # noqa: E402


class _FakeClient:
    """Faux client Ollama : renvoie une interprétation canonique fixe."""

    def chat(self, *args, **kwargs):
        return {"message": {"content": "Réponse interprétée par le LLM mocké."}}


class FakeTranslator:
    """Traducteur mocké : dépile des réponses JSON brutes à chaque appel.

    Reproduit l'interface attendue par le pipeline :
      - `model_name`
      - `translate(problem_text, error_feedback=None)`
      - `_get_client()` (pour l'interprétation)
    """

    def __init__(self, responses):
        self.model_name = "fake-model"
        self._responses = list(responses)
        self.calls = []

    def translate(self, problem_text, error_feedback=None):
        self.calls.append(error_feedback)
        if not self._responses:
            raise RuntimeError("plus de réponse mockée disponible")
        return self._responses.pop(0)

    def _get_client(self):
        return _FakeClient()


VALID_JSON = (
    '{"variables": ['
    '{"name": "alice", "type": "Int", "domain": [0, 1000]},'
    '{"name": "bob", "type": "Int", "domain": [0, 1000]}],'
    '"constraints": ["alice == 3 * bob", "alice + bob == 40"],'
    '"problem_type": "smt_arithmetic", "objective": null}'
)

MALFORMED_JSON = "ceci n'est pas du JSON {{{"

MISSING_VAR_JSON = (
    '{"variables": [{"name": "bob", "type": "Int", "domain": [0, 1000]}],'
    '"constraints": ["alice + bob == 40"], "problem_type": "smt_arithmetic"}'
)

PROBLEM = "Alice a 3 fois plus de billes que Bob, ensemble 40 billes. Combien Bob ?"


def test_pipeline_success_first_attempt():
    translator = FakeTranslator([VALID_JSON])
    out = run_pipeline(
        problem_id="t1",
        problem_text=PROBLEM,
        translator=translator,
        use_llm_for_interpretation=False,
    )
    assert out.run_record.succeeded
    assert out.run_record.n_attempts == 1
    assert out.run_record.final_status == "SAT"
    assert out.solver_result.assignment["bob"] == 10
    assert out.solver_result.assignment["alice"] == 30
    assert out.run_record.error_categories_encountered == []


def test_pipeline_recovers_after_correction():
    # 1re tentative : JSON malformé -> 2e : variable manquante -> 3e : valide.
    translator = FakeTranslator([MALFORMED_JSON, MISSING_VAR_JSON, VALID_JSON])
    out = run_pipeline(
        problem_id="t2",
        problem_text=PROBLEM,
        translator=translator,
        max_correction_attempts=3,
        use_llm_for_interpretation=False,
    )
    assert out.run_record.succeeded
    assert out.run_record.n_attempts == 3
    assert ErrorCategory.LLM_MALFORMED_JSON in out.run_record.error_categories_encountered
    assert ErrorCategory.MISSING_VARIABLE in out.run_record.error_categories_encountered
    # Le retour d'erreur a bien été transmis lors des re-prompts.
    assert translator.calls[0] is None
    assert translator.calls[1] is not None
    assert translator.calls[2] is not None


def test_pipeline_fails_after_retries():
    translator = FakeTranslator([MALFORMED_JSON, MALFORMED_JSON])
    out = run_pipeline(
        problem_id="t3",
        problem_text=PROBLEM,
        translator=translator,
        max_correction_attempts=2,
        use_llm_for_interpretation=False,
    )
    assert not out.run_record.succeeded
    assert out.run_record.final_status == "FAILED_AFTER_RETRIES"
    assert out.run_record.n_attempts == 2
    assert out.solver_result is None


def test_pipeline_uses_llm_interpretation():
    translator = FakeTranslator([VALID_JSON])
    out = run_pipeline(
        problem_id="t4",
        problem_text=PROBLEM,
        translator=translator,
        use_llm_for_interpretation=True,
    )
    assert out.run_record.succeeded
    assert out.natural_language_answer == "Réponse interprétée par le LLM mocké."
