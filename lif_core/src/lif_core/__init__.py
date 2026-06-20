"""lif_core — canonical neuron simulation engine.

Public API:

    from lif_core import LIFNeuron, NeuronModel, SimulationResult
    from lif_core import compile_expression, ExpressionError
"""

from .expressions import ExpressionError, compile_expression
from .models import LIFNeuron, NeuronModel, run_fi_curve
from .simulation import SimulationResult

__all__ = [
    "LIFNeuron",
    "NeuronModel",
    "SimulationResult",
    "compile_expression",
    "ExpressionError",
    "run_fi_curve",
]

__version__ = "0.1.0"
