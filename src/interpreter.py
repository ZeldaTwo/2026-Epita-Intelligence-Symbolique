"""
Interprète un SolverResult en réponse en langage naturel, via le LLM.

Important : le LLM ne fait QUE reformuler des valeurs déjà calculées par Z3.
Il ne lui est jamais demandé de recalculer ou deviner quoi que ce soit,
ce qui élimine une source classique d'hallucination.
"""

from __future__ import annotations

from schema import SolverResult, SymbolicModel

INTERPRETER_SYSTEM_PROMPT = """Tu reformules en français le résultat d'un solveur \
logique pour répondre à la question initiale de l'utilisateur. Tu disposes du résultat \
brut du solveur (statut + valeurs des variables). Tu DOIS te baser strictement sur ces \
valeurs, sans en inventer ni en recalculer d'autres. Sois concis et réponds directement \
à la question posée par l'énoncé original."""


def _format_result_for_prompt(result: SolverResult, model: SymbolicModel) -> str:
    if result.status == "UNSAT":
        return "Le solveur a déterminé qu'AUCUNE solution n'existe (UNSAT) : les contraintes sont incompatibles."
    if result.status != "SAT":
        return f"Le solveur n'a pas pu conclure (statut: {result.status}). Erreur éventuelle : {result.error_message}"

    lines = ["Le solveur a trouvé une solution (SAT) avec les valeurs suivantes :"]
    for name, value in (result.assignment or {}).items():
        lines.append(f"  - {name} = {value}")
    if result.objective_value is not None:
        lines.append(f"Valeur optimale de l'objectif ({model.objective}) = {result.objective_value}")
    return "\n".join(lines)


def interpret_with_llm(
    problem_text: str, result: SolverResult, model: SymbolicModel, translator
) -> str:
    """
    translator: instance de LLMTranslator (réutilisée pour son client Ollama),
    évite de dupliquer la logique de connexion au modèle local.
    """
    client = translator._get_client()
    result_summary = _format_result_for_prompt(result, model)

    response = client.chat(
        model=translator.model_name,
        messages=[
            {"role": "system", "content": INTERPRETER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Question initiale : {problem_text}\n\n"
                    f"Résultat du solveur :\n{result_summary}\n\n"
                    "Donne la réponse en français, en une à trois phrases."
                ),
            },
        ],
        options={"temperature": 0.2},
    )
    return response["message"]["content"].strip()


def interpret_without_llm(result: SolverResult, model: SymbolicModel) -> str:
    """Repli simple sans appel LLM, utile pour les tests et le mode debug."""
    return _format_result_for_prompt(result, model)
