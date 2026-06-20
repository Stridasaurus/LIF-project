"""Simulation API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from lif_core import ExpressionError, LIFNeuron, run_fi_curve

from .. import config
from ..schemas import (
    DefaultsResponse,
    FICurveRequest,
    FICurveResponse,
    SimulationRequest,
    SimulationResponse,
)

router = APIRouter(prefix="/api", tags=["simulation"])


@router.get("/health")
def health() -> dict:
    """Liveness probe."""
    return {"status": "ok"}


@router.get("/defaults", response_model=DefaultsResponse)
def get_defaults() -> DefaultsResponse:
    """Return the default parameters used to pre-fill the frontend form."""
    return DefaultsResponse(
        I=config.DEFAULT_I,
        V_thr=config.DEFAULT_V_THR,
        R=config.DEFAULT_R,
        simulation_time=config.DEFAULT_SIMULATION_TIME,
        dt=config.DEFAULT_DT,
        V_rest=config.DEFAULT_V_REST,
        V_reset=config.DEFAULT_V_RESET,
        tau_m=config.DEFAULT_TAU_M,
        t_ref=config.DEFAULT_T_REF,
        adapt_enabled=config.DEFAULT_ADAPT_ENABLED,
        delta_thr=config.DEFAULT_DELTA_THR,
        tau_adapt=config.DEFAULT_TAU_ADAPT,
        syn_weight=config.DEFAULT_SYN_WEIGHT,
        syn_tau=config.DEFAULT_SYN_TAU,
    )


@router.post("/run_simulation", response_model=SimulationResponse)
def run_simulation(req: SimulationRequest) -> SimulationResponse:
    """Run a single LIF simulation and return its traces + spike times."""
    n_steps = req.simulation_time / req.dt
    if n_steps > config.MAX_STEPS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Requested {int(n_steps):,} steps exceeds the limit of "
                f"{config.MAX_STEPS:,}. Increase dt or reduce simulation_time."
            ),
        )

    neuron = LIFNeuron(
        V_rest=req.V_rest,
        V_reset=req.V_reset,
        tau_m=req.tau_m,
        dt=req.dt,
        t_ref=req.t_ref,
        adapt_enabled=req.adapt_enabled,
        delta_thr=req.delta_thr,
        tau_adapt=req.tau_adapt,
        syn_spikes=req.syn_spikes,
        syn_weight=req.syn_weight,
        syn_tau=req.syn_tau,
    )

    try:
        neuron.set_parameter_function("I", req.I)
        neuron.set_parameter_function("V_thr", req.V_thr)
        neuron.set_parameter_function("R", req.R)
    except ExpressionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        result = neuron.simulate(req.simulation_time)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Simulation failed: {exc}") from exc

    data = result.to_dict()
    data["meta"] = {
        "n_spikes": len(result.spike_times),
        "n_steps": len(result.time),
        "params": {
            "I": req.I, "V_thr": req.V_thr, "R": req.R,
            "simulation_time": req.simulation_time, "dt": req.dt,
            "V_rest": req.V_rest, "V_reset": req.V_reset, "tau_m": req.tau_m,
            "t_ref": req.t_ref, "adapt_enabled": req.adapt_enabled,
        },
    }
    return SimulationResponse(**data)


@router.post("/fi_curve", response_model=FICurveResponse)
def fi_curve(req: FICurveRequest) -> FICurveResponse:
    """Sweep constant input current and return firing rate vs. current."""
    try:
        data = run_fi_curve(
            I_range=(req.I_min, req.I_max),
            steps=req.steps,
            sim_time=req.sim_time,
            t_ref=req.t_ref,
            V_thr_str=req.V_thr,
            R_str=req.R,
            V_rest=req.V_rest,
            V_reset=req.V_reset,
            tau_m=req.tau_m,
            dt=req.dt,
        )
    except ExpressionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"F-I curve failed: {exc}") from exc

    return FICurveResponse(**data)
