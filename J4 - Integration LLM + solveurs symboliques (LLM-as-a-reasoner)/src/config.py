"""
Configuration centralisée du pipeline.

Source de vérité UNIQUE pour le nombre par défaut de tentatives du LLM
(traduction + corrections). La valeur par défaut est 5, mais elle peut être
surchargée sans toucher au code via la variable d'environnement :

    LLM_REASONER_MAX_ATTEMPTS

Exemples :
    export LLM_REASONER_MAX_ATTEMPTS=8      # Linux / macOS
    set    LLM_REASONER_MAX_ATTEMPTS=8      # Windows (cmd)
    $env:LLM_REASONER_MAX_ATTEMPTS = "8"    # Windows (PowerShell)

La lecture se fait à l'exécution (et non à l'import) : définir la variable
avant de lancer un script suffit. Une valeur absente, non entière ou < 1
retombe silencieusement sur la valeur par défaut.
"""

from __future__ import annotations

import os

#: Nom de la variable d'environnement de surcharge.
ENV_MAX_ATTEMPTS = "LLM_REASONER_MAX_ATTEMPTS"

#: Valeur par défaut si la variable d'environnement n'est pas (correctement) définie.
DEFAULT_MAX_ATTEMPTS = 5


def get_default_max_attempts() -> int:
    """Retourne le nombre de tentatives par défaut.

    Priorité : variable d'environnement `LLM_REASONER_MAX_ATTEMPTS` (si entière
    et >= 1), sinon `DEFAULT_MAX_ATTEMPTS`.
    """
    raw = os.environ.get(ENV_MAX_ATTEMPTS)
    if raw is None:
        return DEFAULT_MAX_ATTEMPTS
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_MAX_ATTEMPTS
    return value if value >= 1 else DEFAULT_MAX_ATTEMPTS
