// Client-side LIF engine — faithful JS port of lif_core/models.py.
//
// Provides the same getDefaults / runSimulation / runFICurve API as api.js so
// app.js is engine-agnostic (works with or without the FastAPI backend).

const DEFAULTS = {
  I: "1.5",
  V_thr: "-55",
  R: "10",
  simulation_time: 200,
  dt: 0.1,
  V_rest: -70.0,
  V_reset: -75.0,
  tau_m: 10.0,
  // Refractory period
  t_ref: 2.0,
  // Adaptive threshold
  adapt_enabled: false,
  delta_thr: 5.0,
  tau_adapt: 100.0,
  // Synaptic input
  syn_spikes: [],
  syn_weight: 1.0,
  syn_tau: 5.0,
};

// `math.*` shim — Python's math names mapped onto JS equivalents.
const MATH = {
  pi: Math.PI, e: Math.E, tau: Math.PI * 2,
  sin: Math.sin, cos: Math.cos, tan: Math.tan,
  asin: Math.asin, acos: Math.acos, atan: Math.atan, atan2: Math.atan2,
  sinh: Math.sinh, cosh: Math.cosh, tanh: Math.tanh,
  exp: Math.exp, log: Math.log, log2: Math.log2, log10: Math.log10,
  sqrt: Math.sqrt, pow: Math.pow, fabs: Math.abs,
  floor: Math.floor, ceil: Math.ceil, trunc: Math.trunc,
};

// `np.*` shim — scalar helpers useful for time-functions.
const NP = {
  pi: Math.PI, e: Math.E,
  where: (cond, a, b) => (cond ? a : b),
  maximum: Math.max, minimum: Math.min,
  clip: (x, lo, hi) => Math.min(Math.max(x, lo), hi),
  sin: Math.sin, cos: Math.cos, tan: Math.tan,
  exp: Math.exp, log: Math.log, sqrt: Math.sqrt, abs: Math.abs,
  floor: Math.floor, ceil: Math.ceil,
};

// Compile a user expression string into f(t). Runs in the visitor's own
// browser sandbox, so a plain Function constructor is acceptable here.
function compileExpression(expr) {
  if (expr === null || expr === undefined || !String(expr).trim()) {
    throw new Error("Expression is empty.");
  }
  expr = String(expr).trim();

  let fn;
  try {
    // eslint-disable-next-line no-new-func
    fn = new Function("t", "math", "np", "pi", "e", `"use strict"; return (${expr});`);
  } catch (err) {
    throw new Error(`Invalid syntax: ${err.message}`);
  }

  const wrapped = (t) => fn(t, MATH, NP, Math.PI, Math.E);

  let probe;
  try {
    probe = wrapped(0);
  } catch (err) {
    throw new Error(`Expression failed to evaluate: ${err.message}`);
  }
  if (typeof probe !== "number" || Number.isNaN(probe)) {
    throw new Error("Expression did not evaluate to a number.");
  }
  return wrapped;
}

// Alpha-function synaptic current from a list of presynaptic spike times.
function _synCurrent(t, synSpikes, synWeight, synTau) {
  let total = 0.0;
  for (const t_s of synSpikes) {
    const dt_s = t - t_s;
    if (dt_s > 0) {
      total += synWeight * (dt_s / synTau) * Math.exp(1.0 - dt_s / synTau);
    }
  }
  return total;
}

// Run the LIF simulation. `params` may override any key from DEFAULTS.
// Returns the same shape as the backend's /api/run_simulation response.
function simulate(params) {
  const p = { ...DEFAULTS, ...params };

  const I_func     = compileExpression(p.I);
  const V_thr_func = compileExpression(p.V_thr);
  const R_func     = compileExpression(p.R);

  const V_rest   = Number(p.V_rest);
  const V_reset  = Number(p.V_reset);
  const tau_m    = Number(p.tau_m);
  const dt       = Number(p.dt);
  const sim_time = Number(p.simulation_time);
  const t_ref    = Number(p.t_ref);
  const synSpikes  = Array.isArray(p.syn_spikes) ? p.syn_spikes.map(Number) : [];
  const synWeight  = Number(p.syn_weight);
  const synTau     = Number(p.syn_tau);
  const adaptEnabled = Boolean(p.adapt_enabled);
  const deltaThr   = Number(p.delta_thr);
  const tauAdapt   = Number(p.tau_adapt);

  const time = [], voltage = [], current = [], threshold = [], resistance = [], spike_times = [];

  let V = V_rest;
  let vThrAdapt = 0.0;
  let tSinceSpike = t_ref;  // start ready to fire
  let t = 0.0;

  while (t < sim_time) {
    const I       = I_func(t) + _synCurrent(t, synSpikes, synWeight, synTau);
    const V_thr_base = V_thr_func(t);
    const V_thr_eff  = V_thr_base + (adaptEnabled ? vThrAdapt : 0.0);
    const R       = R_func(t);

    current.push(I);
    threshold.push(V_thr_eff);
    resistance.push(R);

    // Spike check before integration (matches lif_core); blocked during refractory.
    if (tSinceSpike >= t_ref && V >= V_thr_eff) {
      spike_times.push(t);
      V = V_reset;
      tSinceSpike = 0.0;
      if (adaptEnabled) vThrAdapt += deltaThr;
    } else {
      tSinceSpike += dt;
    }

    const dV_dt = (-(V - V_rest) + I * R) / tau_m;
    V += dV_dt * dt;

    if (adaptEnabled) {
      vThrAdapt -= vThrAdapt * (dt / tauAdapt);
    }

    time.push(t);
    voltage.push(V);
    t += dt;
  }

  return {
    time, voltage, current, threshold, resistance, spike_times,
    meta: { n_spikes: spike_times.length, n_steps: time.length, params: p },
  };
}

// Sweep constant I and return { currents, rates } — mirrors run_fi_curve() in lif_core.
function fICurve(params) {
  const p = { ...DEFAULTS, ...params };
  const I_min  = Number(p.fi_I_min  ?? 0.0);
  const I_max  = Number(p.fi_I_max  ?? 5.0);
  const steps  = Number(p.fi_steps  ?? 50);
  const sim_time = Number(p.fi_sim_time ?? 500);

  const currents = [];
  const rates    = [];

  for (let i = 0; i < steps; i++) {
    const i_val = I_min + (I_max - I_min) * (i / (steps - 1));
    currents.push(i_val);
    const result = simulate({ ...p, I: String(i_val), simulation_time: sim_time });
    rates.push(result.spike_times.length / (sim_time / 1000.0));
  }

  return { currents, rates };
}

// --------------------------------------------------------------------------- //
// Backend-client-compatible API (so app.js stays engine-agnostic)             //
// --------------------------------------------------------------------------- //

// eslint-disable-next-line no-unused-vars
async function getDefaults() {
  return { ...DEFAULTS };
}

// eslint-disable-next-line no-unused-vars
async function runSimulation(payload) {
  return simulate(payload);
}

// eslint-disable-next-line no-unused-vars
async function runFICurve(payload) {
  return fICurve(payload);
}

// Allow Node to import for parity tests.
if (typeof module !== "undefined" && module.exports) {
  module.exports = { DEFAULTS, compileExpression, simulate, fICurve, getDefaults, runSimulation, runFICurve };
}
