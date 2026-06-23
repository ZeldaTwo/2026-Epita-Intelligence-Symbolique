"""
Taxonomie des erreurs de traduction LLM -> modèle symbolique.

C'est un livrable central du projet J4 : ce module ne fait pas que classer
une erreur isolée, il agrège des statistiques sur un ensemble d'exécutions
du pipeline pour produire l'analyse demandée dans le sujet.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from schema import ErrorCategory


@dataclass
class PipelineRunRecord:
    """Trace complète d'une exécution du pipeline sur un problème, pour analyse a posteriori."""

    problem_id: str
    problem_text: str
    succeeded: bool
    n_attempts: int
    error_categories_encountered: list[ErrorCategory] = field(default_factory=list)
    final_status: str = ""  # "SAT" / "UNSAT" / "FAILED_AFTER_RETRIES" / "PIPELINE_ERROR"


class ErrorTaxonomyAnalyzer:
    def __init__(self):
        self.records: list[PipelineRunRecord] = []

    def add(self, record: PipelineRunRecord) -> None:
        self.records.append(record)

    def category_distribution(self) -> Counter:
        """Répartition de toutes les catégories d'erreur rencontrées, tous essais confondus."""
        counter = Counter()
        for r in self.records:
            counter.update(r.error_categories_encountered)
        return counter

    def success_rate_direct(self) -> float:
        """Taux de succès dès la première tentative (sans correction)."""
        if not self.records:
            return 0.0
        direct_successes = sum(1 for r in self.records if r.succeeded and r.n_attempts == 1)
        return direct_successes / len(self.records)

    def success_rate_with_correction(self) -> float:
        """Taux de succès final, après les éventuelles tentatives de correction."""
        if not self.records:
            return 0.0
        return sum(1 for r in self.records if r.succeeded) / len(self.records)

    def average_attempts(self) -> float:
        if not self.records:
            return 0.0
        return sum(r.n_attempts for r in self.records) / len(self.records)

    def summary(self) -> dict:
        return {
            "n_problems": len(self.records),
            "success_rate_direct": round(self.success_rate_direct(), 3),
            "success_rate_with_correction": round(self.success_rate_with_correction(), 3),
            "average_attempts": round(self.average_attempts(), 2),
            "error_category_distribution": dict(self.category_distribution()),
            "failed_problems": [r.problem_id for r in self.records if not r.succeeded],
        }
