"""
Interprète un SolverResult en réponse en langage naturel, via le LLM.
"""

from __future__ import annotations
from schema import SolverResult, SymbolicModel

INTERPRETER_SYSTEM_PROMPT = """Tu reformules en français le résultat d'un solveur \
symbolique pour répondre à la question initiale. Tu te bases strictement sur les \
valeurs fournies, sans en inventer. Sois concis (1 à 3 phrases)."""

def _format_result_for_prompt(result: SolverResult, model: SymbolicModel) -> str:
    if result.status == "PDDL_PARSED":
        plan = (result.assignment or {}).get("plan", [])
        lines = ["Un plan de planification PDDL a été trouvé :"]
        lines.append(f"  - État initial : {model.init}")
        lines.append(f"  - Objectif : {model.goal}")
        if plan:
            lines.append(f"  - Plan ({len(plan)} action(s)) :")
            for i, action in enumerate(plan, 1):
                lines.append(f"      {i}. {action}")
        else:
            lines.append(
                "  - Aucune action nécessaire : l'objectif est déjà satisfait "
                "dans l'état initial."
            )
        return "\n".join(lines)
    
    if model.expected_status == "UNSAT" and result.status == "UNSAT":
        return (
            "Le solveur a confirmé que le problème est bien IMPOSSIBLE (UNSAT), "
            "comme attendu par l'énoncé. Les contraintes sont contradictoires."
        )
    
    if model.expected_status == "UNSAT" and result.status == "SAT":
        return (
            f"ERREUR DE TRADUCTION : Le modèle produit est satisfiable "
            f"(solution : {result.assignment}), mais l'énoncé attendait UNSAT. "
            f"Les contraintes sont incomplètes — le LLM a omis des conditions."
        )
        
    if result.status == "UNSAT":
        return "Le solveur a déterminé qu'AUCUNE solution n'existe (UNSAT)."
    if "SAT" not in result.status:
        return f"Le solveur n'a pas pu conclure ({result.status}). Erreur : {result.error_message}"

    lines = [f"Le solveur a trouvé une configuration valide ({result.status}) :"]
    for name, value in (result.assignment or {}).items():
        lines.append(f"  - {name} = {value}")
    if result.objective_value is not None:
        lines.append(f"Objectif atteint ({model.objective}) = {result.objective_value}")
    return "\n".join(lines)

def interpret_with_llm(problem_text: str, result: SolverResult, model: SymbolicModel, translator) -> str:
    client = translator._get_client()
    result_summary = _format_result_for_prompt(result, model)

    response = client.chat(
        model=translator.model_name,
        messages=[
            {"role": "system", "content": INTERPRETER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Question initiale : {problem_text}\n\nRésultat du solveur :\n{result_summary}\n\nDonne la réponse en français.",
            },
        ],
        options={"temperature": 0.2},
    )
    return response["message"]["content"].strip()

def interpret_without_llm(result: SolverResult, model: SymbolicModel) -> str:
    return _format_result_for_prompt(result, model)