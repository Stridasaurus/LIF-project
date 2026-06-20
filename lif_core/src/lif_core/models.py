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

import math
from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Sequence, Tuple

from .expressions import ExpressionError, compile_expression
from .simulation import SimulationResult

__all__ = ["NeuronModel", "LIFNeuron", "run_fi_curve"]


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
        # Refractory period
        t_ref: float = 2.0,
        # Adaptive threshold
        adapt_enabled: bool = False,
        delta_thr: float = 5.0,
        tau_adapt: float = 100.0,
        # Spike-triggered synaptic input
        syn_spikes: Sequence[float] = (),
        syn_weight: float = 1.0,
        syn_tau: float = 5.0,
    ) -> None:
        # Fixed parameters (defaults match the notebook).
        self.V_rest = V_rest
        self.V_reset = V_reset
        self.tau_m = tau_m
        self.dt = dt

        # Refractory period (ms); 0 disables it.
        self.t_ref = t_ref

        # Adaptive threshold parameters.
        self.adapt_enabled = adapt_enabled
        self.delta_thr = delta_thr    # mV bump per spike
        self.tau_adapt = tau_adapt    # ms decay time constant

        # Spike-triggered synaptic input (alpha-function).
        self.syn_spikes: List[float] = list(syn_spikes)
        self.syn_weight = syn_weight  # nA peak per presynaptic spike
        self.syn_tau = syn_tau        # ms alpha-function time constant

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

    def _syn_current(self, t: float) -> float:
        """Alpha-function synaptic current summed over all presynaptic spikes."""
        total = 0.0
        for t_s in self.syn_spikes:
            dt_s = t - t_s
            if dt_s > 0.0:
                # Peak = syn_weight at dt_s = syn_tau; decays to 0 on both sides.
                total += self.syn_weight * (dt_s / self.syn_tau) * math.exp(1.0 - dt_s / self.syn_tau)
        return total

    def simulate(self, simulation_time: float = 100) -> SimulationResult:
        """Run the Euler integration loop (identical semantics to the notebook)."""
        result = SimulationResult()

        V = self.V_rest
        V_thr_adapt = 0.0
        t_since_spike = self.t_ref  # start ready to fire immediately
        t = 0.0

        while t < simulation_time:
            # Evaluate all time-varying parameters at the current time.
            I = self.I_func(t) + self._syn_current(t)
            V_thr_base = self.V_thr_func(t)
            V_thr_eff = V_thr_base + (V_thr_adapt if self.adapt_enabled else 0.0)
            R = self.R_func(t)

            result.current.append(I)
            result.threshold.append(V_thr_eff)
            result.resistance.append(R)

            # Spike check before integration (matches the notebook).
            # Blocked during the absolute refractory period.
            if t_since_spike >= self.t_ref and V >= V_thr_eff:
                result.spike_times.append(t)
                V = self.V_reset
                t_since_spike = 0.0
                if self.adapt_enabled:
                    V_thr_adapt += self.delta_thr
            else:
                t_since_spike += self.dt

            # Forward-Euler integration step.
            dV_dt = (-(V - self.V_rest) + I * R) / self.tau_m
            V += dV_dt * self.dt

            # Adaptive threshold decay (Euler).
            if self.adapt_enabled:
                V_thr_adapt -= V_thr_adapt * (self.dt / self.tau_adapt)

            result.time.append(t)
            result.voltage.append(V)
            t += self.dt

        return result


def run_fi_curve(
    I_range: Tuple[float, float] = (0.0, 5.0),
    steps: int = 50,
    sim_time: float = 500.0,
    t_ref: float = 2.0,
    V_thr_str: str = "-55",
    R_str: str = "10",
    V_rest: float = -70.0,
    V_reset: float = -75.0,
    tau_m: float = 10.0,
    dt: float = 0.1,
) -> Dict[str, list]:
    """Sweep constant drive current and return firing rate vs. current.

    Returns
    -------
    dict with keys ``"currents"`` (nA) and ``"rates"`` (Hz).
    """
    import numpy as np

    currents = list(np.linspace(I_range[0], I_range[1], steps))
    rates: List[float] = []

    for i_val in currents:
        neuron = LIFNeuron(
            V_rest=V_rest, V_reset=V_reset, tau_m=tau_m, dt=dt, t_ref=t_ref
        )
        neuron.I_func = lambda t, iv=i_val: iv
        neuron.set_parameter_function("V_thr", V_thr_str)
        neuron.set_parameter_function("R", R_str)
        result = neuron.simulate(sim_time)
        rates.append(len(result.spike_times) / (sim_time / 1000.0))

    return {"currents": currents, "rates": rates}
