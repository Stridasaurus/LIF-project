"""Pydantic request/response models for the simulation API."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from . import config


class SimulationRequest(BaseModel):
    """Parameters for a single LIF simulation run."""

    I: str = Field(default=config.DEFAULT_I, description="Input current I(t), nA.")
    V_thr: str = Field(default=config.DEFAULT_V_THR, description="Spike threshold V_thr(t), mV.")
    R: str = Field(default=config.DEFAULT_R, description="Membrane resistance R(t), MΩ.")

    simulation_time: float = Field(
        default=config.DEFAULT_SIMULATION_TIME, gt=0, le=config.MAX_SIMULATION_TIME,
        description="Total simulated time, ms.",
    )
    dt: float = Field(
        default=config.DEFAULT_DT, ge=config.MIN_DT, le=10.0,
        description="Integration time step, ms.",
    )

    # Fixed neuron parameters.
    V_rest: float = Field(default=config.DEFAULT_V_REST, description="Resting potential, mV.")
    V_reset: float = Field(default=config.DEFAULT_V_RESET, description="Reset potential, mV.")
    tau_m: float = Field(default=config.DEFAULT_TAU_M, gt=0, description="Membrane time constant, ms.")

    # Refractory period.
    t_ref: float = Field(default=config.DEFAULT_T_REF, ge=0, description="Absolute refractory period, ms.")

    # Adaptive threshold.
    adapt_enabled: bool = Field(default=config.DEFAULT_ADAPT_ENABLED, description="Enable adaptive threshold.")
    delta_thr: float = Field(default=config.DEFAULT_DELTA_THR, ge=0, description="Threshold jump per spike, mV.")
    tau_adapt: float = Field(default=config.DEFAULT_TAU_ADAPT, gt=0, description="Adaptation decay time constant, ms.")

    # Spike-triggered synaptic input.
    syn_spikes: List[float] = Field(default_factory=list, description="Presynaptic spike times, ms.")
    syn_weight: float = Field(default=config.DEFAULT_SYN_WEIGHT, description="Synaptic weight (peak current), nA.")
    syn_tau: float = Field(default=config.DEFAULT_SYN_TAU, gt=0, description="Synaptic alpha time constant, ms.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "I": "1.5 + math.sin(t / 10)",
                "V_thr": "-55",
                "R": "10",
                "simulation_time": 200,
            }
        }
    }


class SimulationResponse(BaseModel):
    """Traces and spike times returned from a run."""

    time: List[float]
    voltage: List[float]
    current: List[float]
    threshold: List[float]
    resistance: List[float]
    spike_times: List[float]
    meta: Dict[str, object]


class FICurveRequest(BaseModel):
    """Parameters for an F-I curve sweep."""

    V_thr: str = Field(default=config.DEFAULT_V_THR, description="Threshold expression V_thr(t), mV.")
    R: str = Field(default=config.DEFAULT_R, description="Resistance expression R(t), MΩ.")
    I_min: float = Field(default=config.DEFAULT_FI_I_MIN, description="Minimum sweep current, nA.")
    I_max: float = Field(default=config.DEFAULT_FI_I_MAX, description="Maximum sweep current, nA.")
    steps: int = Field(default=config.DEFAULT_FI_STEPS, ge=2, le=200, description="Number of current steps.")
    sim_time: float = Field(default=config.DEFAULT_FI_SIM_TIME, gt=0, le=config.MAX_SIMULATION_TIME,
                            description="Simulation time per step, ms.")
    t_ref: float = Field(default=config.DEFAULT_T_REF, ge=0)
    V_rest: float = Field(default=config.DEFAULT_V_REST)
    V_reset: float = Field(default=config.DEFAULT_V_RESET)
    tau_m: float = Field(default=config.DEFAULT_TAU_M, gt=0)
    dt: float = Field(default=config.DEFAULT_DT, ge=config.MIN_DT, le=10.0)


class FICurveResponse(BaseModel):
    """F-I curve data."""

    currents: List[float]
    rates: List[float]


class DefaultsResponse(BaseModel):
    """Default values used to pre-fill the frontend form."""

    I: str
    V_thr: str
    R: str
    simulation_time: float
    dt: float
    V_rest: float
    V_reset: float
    tau_m: float
    t_ref: float
    adapt_enabled: bool
    delta_thr: float
    tau_adapt: float
    syn_weight: float
    syn_tau: float
