"""Pydantic request/response models for the simulation API."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from . import config


class SimulationRequest(BaseModel):
    """Parameters for a single LIF simulation run.

    The three time functions are plain strings (e.g. ``"1.5 + math.sin(t/10)"``)
    compiled safely on the server. Fixed parameters are optional and fall back to
    the notebook defaults.
    """

    I: str = Field(default=config.DEFAULT_I, description="Input current I(t), nA.")
    V_thr: str = Field(
        default=config.DEFAULT_V_THR, description="Spike threshold V_thr(t), mV."
    )
    R: str = Field(default=config.DEFAULT_R, description="Membrane resistance R(t), MΩ.")

    simulation_time: float = Field(
        default=config.DEFAULT_SIMULATION_TIME,
        gt=0,
        le=config.MAX_SIMULATION_TIME,
        description="Total simulated time, ms.",
    )
    dt: float = Field(
        default=config.DEFAULT_DT,
        ge=config.MIN_DT,
        le=10.0,
        description="Integration time step, ms.",
    )

    # Optional fixed-parameter overrides (default to notebook values).
    V_rest: float = Field(default=config.DEFAULT_V_REST, description="Resting potential, mV.")
    V_reset: float = Field(default=config.DEFAULT_V_RESET, description="Reset potential, mV.")
    tau_m: float = Field(default=config.DEFAULT_TAU_M, gt=0, description="Membrane time constant, ms.")

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
    spike_times: List[float]
    meta: Dict[str, object]


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
