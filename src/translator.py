"""
Traduction d'un énoncé en langage naturel vers un `SymbolicModel` (JSON),
via un LLM local servi par Ollama.

Le LLM ne génère JAMAIS de code exécutable : il remplit un objet JSON conforme
au schéma. Le `format="json"` d'Ollama force déjà une sortie JSON, mais on
parse et valide systématiquement côté Python (Pydantic) pour ne rien supposer.
"""

from __future__ import annotations

import json
from typing import Optional, Tuple

from pydantic import ValidationError

from schema import SymbolicModel

SYSTEM_PROMPT = """Tu es un traducteur qui convertit un problème énoncé en langage \
naturel en un MODÈLE SYMBOLIQUE au format JSON STRICT, destiné au solveur Z3.

Réponds UNIQUEMENT par un objet JSON (aucun texte, aucune balise Markdown).

Schéma attendu :
{
  "variables": [
    {"name": "<identifiant>", "type": "Int" | "Real" | "Bool", "domain": [min, max]}
  ],
  "constraints": ["<expression booléenne>", ...],
  "problem_type": "smt_arithmetic" | "sat_boolean",
  "objective": "maximize <expr>" | "minimize <expr>" | null
}

Règles impératives :
- "name" doit être un identifiant valide (lettres/chiffres/underscore, ne commence pas par un chiffre).
- "domain" est obligatoire pour les variables Int/Real (bornes raisonnables), omis pour Bool.
- Les contraintes sont des expressions Python/Z3 : opérateurs +, -, *, ==, !=, <, <=, >, >=.
- Pour la logique booléenne, utilise les fonctions Z3 : And(...), Or(...), Not(...), Implies(a, b), Xor(a, b).
- N'écris JAMAIS de comparaison chaînée (ex: 0 < x < 10). Écris "And(x > 0, x < 10)".
- Chaque contrainte DOIT être une expression booléenne (pas "x + y", mais "x + y == 10").
- Utilise uniquement des variables déclarées dans "variables".
- Mets "objective" à null s'il n'y a pas d'optimisation.

Exemple :
Énoncé : "Alice a 3 fois plus de billes que Bob, ensemble 40 billes."
Réponse :
{"variables": [{"name": "alice", "type": "Int", "domain": [0, 1000]},
               {"name": "bob", "type": "Int", "domain": [0, 1000]}],
 "constraints": ["alice == 3 * bob", "alice + bob == 40"],
 "problem_type": "smt_arithmetic", "objective": null}
"""


def parse_symbolic_model(raw: str) -> Tuple[Optional[SymbolicModel], Optional[str]]:
    """Parse une sortie LLM brute en `SymbolicModel`.

    Renvoie `(model, None)` en cas de succès, `(None, message)` sinon.
    Tolère un éventuel encadrement Markdown ```json ... ```.
    """
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        return None, f"JSON invalide : {exc}"
    try:
        return SymbolicModel(**data), None
    except (ValidationError, TypeError) as exc:
        return None, f"non conforme au schéma : {exc}"


class LLMTranslator:
    """Encapsule le client Ollama et la logique de traduction NL -> JSON."""

    def __init__(self, model_name: str = "qwen2.5-coder", host: Optional[str] = None):
        self.model_name = model_name
        self.host = host
        self._client = None

    def _get_client(self):
        """Client Ollama instancié paresseusement (import différé pour les tests)."""
        if self._client is None:
            import ollama  # import local : non requis pour les tests mockés

            self._client = ollama.Client(host=self.host) if self.host else ollama.Client()
        return self._client

    def translate(self, problem_text: str, error_feedback: Optional[str] = None) -> str:
        """Appelle le LLM et renvoie sa réponse JSON brute (chaîne).

        `error_feedback` permet le re-prompting : on rappelle au modèle pourquoi
        sa tentative précédente a échoué.
        """
        client = self._get_client()
        user_content = f"Énoncé : {problem_text}"
        if error_feedback:
            user_content += (
                "\n\nTa réponse précédente a été rejetée pour la raison suivante :\n"
                f"{error_feedback}\n"
                "Corrige le modèle et renvoie un JSON valide conforme au schéma."
            )
        response = client.chat(
            model=self.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            format="json",
            options={"temperature": 0.1},
        )
        return response["message"]["content"]
