"""Backend configuration: simulation limits and default parameters.

Defaults are kept in one place so the API, the request schema, and the frontend
(`GET /api/defaults`) all agree on a single source of truth.
"""

from __future__ import annotations

# --- Default time-function expressions (match the notebook) ---------------- #
DEFAULT_I = "1.5"
DEFAULT_V_THR = "-55"
DEFAULT_R = "10"

# --- Default fixed parameters (match the notebook) ------------------------- #
DEFAULT_SIMULATION_TIME = 200.0  # ms
DEFAULT_DT = 0.1  # ms
DEFAULT_V_REST = -70.0  # mV
DEFAULT_V_RESET = -75.0  # mV
DEFAULT_TAU_M = 10.0  # ms

# --- New feature defaults -------------------------------------------------- #
DEFAULT_T_REF = 2.0          # ms refractory period
DEFAULT_ADAPT_ENABLED = False
DEFAULT_DELTA_THR = 5.0      # mV threshold jump per spike
DEFAULT_TAU_ADAPT = 100.0    # ms adaptation decay constant
DEFAULT_SYN_WEIGHT = 1.0     # nA synaptic weight
DEFAULT_SYN_TAU = 5.0        # ms synaptic alpha time constant

# --- F-I curve defaults ---------------------------------------------------- #
DEFAULT_FI_I_MIN = 0.0
DEFAULT_FI_I_MAX = 5.0
DEFAULT_FI_STEPS = 50
DEFAULT_FI_SIM_TIME = 500.0  # ms per step

# --- Guard rails ----------------------------------------------------------- #
# Cap the number of integration steps to avoid unbounded memory/CPU from a
# request like simulation_time=10_000_000. steps = simulation_time / dt.
MAX_STEPS = 1_000_000
MIN_DT = 1e-3
MAX_SIMULATION_TIME = 100_000.0  # ms

# CORS origins allowed when the frontend is served separately (dev convenience).
ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]
