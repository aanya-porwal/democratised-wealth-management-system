"""Base engine — the plugin architecture core.

* ``BaseEvaluator`` — abstract template-method pipeline every evaluator
  implements.
* ``BaseProviderSet`` — the provider dependency bundle injected into
  evaluators.
* ``EvaluatorRegistry`` — maps a :class:`TargetAssetClass` to concrete
  evaluators so the core engine never knows how an asset class works.
"""

from security_selection.base.evaluator import BaseEvaluator
from security_selection.base.provider import BaseProviderSet
from security_selection.base.registry import EvaluatorRegistry, RegistryError

__all__ = ["BaseEvaluator", "BaseProviderSet", "EvaluatorRegistry", "RegistryError"]

