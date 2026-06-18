// Client-side LIF engine.
//
// This is a faithful JavaScript port of the Python `lif_core` engine so the app
// can run entirely in the browser (GitHub Pages, no backend). The integration
// loop mirrors `lif_core/models.py` step-for-step — same forward-Euler update,
// same spike-check-before-integrate ordering — so results match the Python
// engine (both use IEEE-754 doubles).
//
// The same function names used by the backend client (`getDefaults`,
// `runSimulation`) are provided here so `app.js` is unchanged whether the engine
// is local or remote.

// Default parameters (match the notebook / lif_core).
const DEFAULTS = {
  I: "1.5",
  V_thr: "-55",
  R: "10",
  simulation_time: 200,
  dt: 0.1,
  V_rest: -70.0,
  V_reset: -75.0,
  tau_m: 10.0,
};

// `math.*` shim: Python's `math` names mapped onto JS equivalents (incl. pi/e,
// which JS spells Math.PI / Math.E).
const MATH = {
  pi: Math.PI,
  e: Math.E,
  tau: Math.PI * 2,
  sin: Math.sin, cos: Math.cos, tan: Math.tan,
  asin: Math.asin, acos: Math.acos, atan: Math.atan, atan2: Math.atan2,
  sinh: Math.sinh, cosh: Math.cosh, tanh: Math.tanh,
  exp: Math.exp, log: Math.log, log2: Math.log2, log10: Math.log10,
  sqrt: Math.sqrt, pow: Math.pow, fabs: Math.abs,
  floor: Math.floor, ceil: Math.ceil, trunc: Math.trunc,
};

// `np.*` shim: just the handful of helpers useful for scalar time-functions.
// `np.where(cond, a, b)` is the common one (piecewise input currents).
const NP = {
  pi: Math.PI,
  e: Math.E,
  where: (cond, a, b) => (cond ? a : b),
  maximum: Math.max, minimum: Math.min, clip: (x, lo, hi) => Math.min(Math.max(x, lo), hi),
  sin: Math.sin, cos: Math.cos, tan: Math.tan,
  exp: Math.exp, log: Math.log, sqrt: Math.sqrt, abs: Math.abs,
  floor: Math.floor, ceil: Math.ceil,
};

// Compile a user expression string (in terms of `t`) into a function f(t).
// Note: this runs in the visitor's own browser sandbox — there is no server or
// other user to affect — so a plain `Function` constructor is acceptable here.
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

  // Smoke-evaluate once so obvious mistakes surface immediately, not mid-run.
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

// Run the LIF simulation. `params` may override any of DEFAULTS.
// Returns the same shape as the backend's /api/run_simulation response.
function simulate(params) {
  const p = { ...DEFAULTS, ...params };

  const I_func = compileExpression(p.I);
  const V_thr_func = compileExpression(p.V_thr);
  const R_func = compileExpression(p.R);

  const V_rest = Number(p.V_rest);
  const V_reset = Number(p.V_reset);
  const tau_m = Number(p.tau_m);
  const dt = Number(p.dt);
  const simulation_time = Number(p.simulation_time);

  const time = [];
  const voltage = [];
  const current = [];
  const threshold = [];
  const spike_times = [];

  let V = V_rest;
  let t = 0.0;

  while (t < simulation_time) {
    const I = I_func(t);
    const V_thr = V_thr_func(t);
    const R = R_func(t);

    current.push(I);
    threshold.push(V_thr);

    // Spike check before integration (matches lif_core).
    if (V >= V_thr) {
      spike_times.push(t);
      V = V_reset;
    }

    const dV_dt = (-(V - V_rest) + I * R) / tau_m;
    V += dV_dt * dt;

    time.push(t);
    voltage.push(V);
    t += dt;
  }

  return {
    time,
    voltage,
    current,
    threshold,
    spike_times,
    meta: { n_spikes: spike_times.length, n_steps: time.length, params: p },
  };
}

// --- Backend-client-compatible API (so app.js stays engine-agnostic) -------- //

// eslint-disable-next-line no-unused-vars
async function getDefaults() {
  return { ...DEFAULTS };
}

// eslint-disable-next-line no-unused-vars
async function runSimulation(payload) {
  // Errors thrown here (invalid expressions) propagate to app.js's catch, which
  // shows them in the error banner — same contract as the remote client.
  return simulate(payload);
}

// Allow Node to import this module for parity tests; harmless in the browser.
if (typeof module !== "undefined" && module.exports) {
  module.exports = { DEFAULTS, compileExpression, simulate, getDefaults, runSimulation };
}
