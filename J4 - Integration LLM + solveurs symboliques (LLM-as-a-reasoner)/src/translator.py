"""
Traduction d'un énoncé en langage naturel vers un `SymbolicModel` (JSON) multi-formalismes.
"""

from __future__ import annotations

import json
from typing import Optional, Tuple

from pydantic import ValidationError
from schema import ErrorCategory, SymbolicModel

SYSTEM_PROMPT = """Tu es un expert en méthodes formelles et ingénierie symbolique. Ton rôle est de traduire un énoncé en langage naturel vers le MODÈLE SYMBOLIQUE intermédiaire au format JSON STRICT le plus adapté.

### DIRECTIVE STRATÉGIQUE DE SÉLECTION DU FORMALISME ("formalism")
Regarde attentivement l'énoncé et choisis l'UNIQUE outil adéquat :
1. "sat"  : Logique booléenne pure (Vrai/Faux), circuits combinatoires, énigmes de menteurs/vérités (Chevaliers & Valets). Aucune variable numérique ici.
2. "smt"  : Problèmes impliquant de l'arithmétique infinie ou réelle, des calculs de coûts, ou des objectifs d'optimisation ("maximize", "minimize").
3. "csp"  : Énigmes d'associations complexes à attributs multiples (ex: Énigme d'Einstein, grilles de Sudoku, planification de tables). Utilise des variables "Int" associées à un "domain" [min, max] strict et restreint.
4. "pddl" : Planification d'actions séquentielles d'un agent. À utiliser dès que l'énoncé mentionne des déplacements, un état initial, des actions modifiant l'environnement et un but à atteindre (ex: Robot navigant, Tours de Hanoï).

---

### DIRECTIVES DE SYNTAXE ET RÈGLES CRITIQUES
- INTERDICTION DES COMPARAISONS CHAÎNÉES : Ne génère JAMAIS d'expressions comme "0 < x < 10". Traduis-les obligatoirement par des conjonctions explicites : "And(x > 0, x < 10)".
- TYPES DE VARIABLES : Les types de variables doivent être strictement : {"Int", "Real", "Bool", "Object"}. Aucun autre type n'est accepté par le schéma. 
- IDENTIFIANTS VALIDES : Les noms de variables doivent être de parfaits identifiants Python/Z3 (pas de tirets, pas d'espaces, pas de caractères spéciaux, ne commencent pas par un chiffre).
- BIAIS D'OPTIMISME INTERDIT : Si un problème est intrinsèquement IMPOSSIBLE (UNSAT), n'altère pas les contraintes pour forcer une solution. Traduis les règles de l'énoncé fidèlement. Le fait que le solveur conclue à une insatisfiabilité est un résultat scientifique valide.
- PROBLÈMES UNSAT / IMPOSSIBLES : Si l'énoncé décrit une situation mathématiquement
  impossible (ex: principe des tiroirs, paradoxe), tu DOIS quand même produire un
  modèle fidèle aux contraintes de l'énoncé. Ajoute "expected_status": "UNSAT" au JSON.
  Le solveur prouvera l'impossibilité — c'est un résultat scientifique valide.
  N'altère JAMAIS les contraintes pour forcer une solution.

---

### EXEMPLES DE STRUCTURES PAR FORMALISME

#### Exemple 1 : Énigme Logique Booléenne -> "formalism": "sat"
Énoncé : "Si Paul vient (P), alors Julie vient (J). Paul vient."

{
  "formalism": "sat",
  "variables": [
    {"name": "P", "type": "Bool"},
    {"name": "J", "type": "Bool"}
  ],
  "constraints": [
    "Implies(P, J)",
    "P"
  ],
  "objective": null,
  "init": null, "goal": null, "actions": null
}

# Exemple 1b : Problème impossible (UNSAT)
{
  "formalism": "sat",
  "expected_status": "UNSAT",
  "variables": [
    {"name": "P1", "type": "Int", "domain": [1, 3]},
    {"name": "P2", "type": "Int", "domain": [1, 3]},
    {"name": "P3", "type": "Int", "domain": [1, 3]},
    {"name": "P4", "type": "Int", "domain": [1, 3]}
  ],
  "constraints": [
    "Distinct(P1, P2, P3, P4)"
  ],
  ...
}

Exemple 2 : Optimisation Mathématique -> "formalism": "smt"

Énoncé : "Maximiser le profit 3x + 4y sachant que x et y sont positifs, x inférieur à 10 et y inférieur à 5."

{
  "formalism": "smt",
  "variables": [
    {"name": "x", "type": "Int", "domain": [0, 100]},
    {"name": "y", "type": "Int", "domain": [0, 100]}
  ],
  "constraints": [
    "x >= 0",
    "y >= 0",
    "x < 10",
    "y < 5"
  ],
  "objective": "maximize 3*x + 4*y",
  "init": null, "goal": null, "actions": null
}

Exemple 3 : Énigme à attributs (Einstein/Sudoku) -> "formalism": "csp"

Énoncé : "Deux maisons côte à côte (positions 1 et 2). La maison de l'Anglais (A) est à la position 1."

{
  "formalism": "csp",
  "variables": [
    {"name": "Anglais", "type": "Int", "domain": [1, 2]}
  ],
  "constraints": [
    "Anglais == 1"
  ],
  "objective": null,
  "init": null, "goal": null, "actions": null
}

Exemple 4 : Planification d'un Agent -> "formalism": "pddl"

Énoncé : "Un robot part de la pièce A pour aller en pièce B. L'action de bouger change sa pièce."

{
  "formalism": "pddl",
  "variables": [
    {"name": "robot", "type": "Object"},
    {"name": "pieceA", "type": "Object"},
    {"name": "pieceB", "type": "Object"}
  ],
  "constraints": [],
  "objective": null,
  "init": [
    "At(robot, pieceA)",
    "Connected(pieceA, pieceB)"
  ],
  "goal": "At(robot, pieceB)",
  "actions": [
    {
      "name": "move",
      "parameters": {"?r": "Object", "?from": "Object", "?to": "Object"},
      "precondition": "And(At(?r, ?from), Connected(?from, ?to))",
      "effect": "And(Not(At(?r, ?from)), At(?r, ?to))"
    }
  ]
}


"""


def parse_symbolic_model(raw: str) -> Tuple[Optional[SymbolicModel], Optional[str], Optional[ErrorCategory]]:
    """Parse la réponse brute du LLM en SymbolicModel.
    
    Retourne un tuple (model, error_message, error_category).
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
        return None, f"JSON invalide : {exc}", ErrorCategory.LLM_MALFORMED_JSON
    try:
        return SymbolicModel(**data), None, None
    except (ValidationError, TypeError) as exc:
        return None, f"non conforme au schéma : {exc}", ErrorCategory.SEMANTIC_MISMATCH


class LLMTranslator:
    def __init__(self, model_name: str = "qwen2.5-coder", host: Optional[str] = None):
        self.model_name = model_name
        self.host = host
        self._client = None

    def _get_client(self):
        if self._client is None:
            import ollama
            self._client = ollama.Client(host=self.host) if self.host else ollama.Client()
        return self._client

    def translate(self, problem_text: str, error_feedback: Optional[str] = None) -> str:
        client = self._get_client()
        user_content = f"Énoncé : {problem_text}"
        if error_feedback:
            user_content += f"\n\nTa réponse précédente a été rejetée :\n{error_feedback}\nCorrige et renvoie le JSON."
        
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