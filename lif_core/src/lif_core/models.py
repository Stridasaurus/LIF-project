"""Neuron models.

``NeuronModel`` is a thin abstract base so that future models (Izhikevich,
Hodgkin-Huxley, adaptive-exponential, ...) can be added without changing the web
API or the frontend: each just implements ``simulate()`` and exposes its
configurable parameter functions.

``LIFNeuron`` reproduces the exact numerics of the original notebook
(``LIF Model.ipynb``) so results match bit-for-bit: forward-Euler integration,
spike check *before* the integration step, and the same default parameters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Dict

from .expressions import ExpressionError, compile_expression
from .simulation import SimulationResult

__all__ = ["NeuronModel", "LIFNeuron"]


class NeuronModel(ABC):
    """Abstract base for single-compartment neuron models."""

    #: Parameter names that ``set_parameter_function`` accepts for this model.
    PARAMETERS: tuple[str, ...] = ()

    @abstractmethod
    def set_parameter_function(self, param_name: str, func_str: str) -> None:
        """Set a model parameter as a (compiled, validated) function of time."""

    @abstractmethod
    def simulate(self, simulation_time: float = 100) -> SimulationResult:
        """Integrate the model and return a :class:`SimulationResult`."""


class LIFNeuron(NeuronModel):
    """Leaky Integrate-and-Fire neuron.

    Governing equation (forward Euler):
        ``tau_m * dV/dt = -(V - V_rest) + R(t) * I(t)``

    Time-varying parameters ``I(t)``, ``V_thr(t)`` and ``R(t)`` are supplied as
    callables (use :meth:`set_parameter_function` to compile them from strings).
    """

    PARAMETERS = ("I", "V_thr", "R")

    def __init__(
        self,
        V_rest: float = -70.0,
        V_reset: float = -75.0,
        tau_m: float = 10.0,
        dt: float = 0.1,
    ) -> None:
        # Fixed parameters (defaults match the notebook).
        self.V_rest = V_rest
        self.V_reset = V_reset
        self.tau_m = tau_m
        self.dt = dt

        # Time-varying parameters default to the notebook's constants.
        self.I_func: Callable[[float], float] = lambda t: 1.5
        self.V_thr_func: Callable[[float], float] = lambda t: -55.0
        self.R_func: Callable[[float], float] = lambda t: 10.0

    def set_parameter_function(self, param_name: str, func_str: str) -> None:
        """Compile ``func_str`` and bind it to ``param_name``.

        Parameters
        ----------
        param_name:
            One of ``'I'``, ``'V_thr'``, ``'R'``.
        func_str:
            A time-function expression (see :func:`lif_core.compile_expression`).

        Raises
        ------
        ExpressionError
            If ``param_name`` is unknown or ``func_str`` is invalid/unsafe.
        """
        func = compile_expression(func_str)

        if param_name == "I":
            self.I_func = func
        elif param_name == "V_thr":
            self.V_thr_func = func
        elif param_name == "R":
            self.R_func = func
        else:
            raise ExpressionError(
                f"Unknown parameter '{param_name}'. Expected one of {self.PARAMETERS}."
            )

    def parameter_functions(self) -> Dict[str, Callable[[float], float]]:
        """Return the current time-function callables keyed by parameter name."""
        return {"I": self.I_func, "V_thr": self.V_thr_func, "R": self.R_func}

    def simulate(self, simulation_time: float = 100) -> SimulationResult:
        """Run the Euler integration loop (identical semantics to the notebook)."""
        result = SimulationResult()

        V = self.V_rest
        t = 0.0

        while t < simulation_time:
            # Evaluate all time-varying parameters at the current time.
            I = self.I_func(t)
            V_thr = self.V_thr_func(t)
            R = self.R_func(t)

            result.current.append(I)
            result.threshold.append(V_thr)

            # Spike check happens before integration (matches the notebook).
            if V >= V_thr:
                result.spike_times.append(t)
                V = self.V_reset

            # Forward-Euler integration step.
            dV_dt = (-(V - self.V_rest) + I * R) / self.tau_m
            V += dV_dt * self.dt

            result.time.append(t)
            result.voltage.append(V)
            t += self.dt

        return result
