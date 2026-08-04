"""Synthetic Population Generator (PART 1).

Generates 100k+ realistic Indian household financial profiles using
statistical distributions and correlations rather than random values.
Each profile describes a person's age, income, expenses, savings, debt,
investments, insurance, behaviour, goals and more.
"""

from ml.synthetic_population.personas import (  # noqa: F401
    PERSONA_REGISTRY,
    build_personas,
    get_persona,
    list_persona_names,
)
from ml.synthetic_population.generator import (  # noqa: F401
    PopulationGenerator,
    generate_population,
)

__all__ = [
    "PERSONA_REGISTRY",
    "build_personas",
    "get_persona",
    "list_persona_names",
    "PopulationGenerator",
    "generate_population",
]
