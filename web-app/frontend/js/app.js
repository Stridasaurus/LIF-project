// Wires the form to the engine (lif.js or api.js) and the plot renderers.

const form        = document.getElementById("sim-form");
const runBtn      = document.getElementById("run-btn");
const fiBtn       = document.getElementById("fi-btn");
const resetBtn    = document.getElementById("reset-btn");
const errorBanner = document.getElementById("error-banner");
const spikeSummary   = document.getElementById("spike-summary");
const spikeTimesEl   = document.getElementById("spike-times");
const spikeStatsEl   = document.getElementById("spike-stats");
const neuronSvg      = document.getElementById("neuron-svg");
const tabSim         = document.getElementById("tab-sim");
const tabFI          = document.getElementById("tab-fi");
const plotDiv        = document.getElementById("plot");
const fiPlotDiv      = document.getElementById("fi-plot");

let defaults = null;

function showError(message) {
  errorBanner.textContent = message;
  errorBanner.hidden = false;
}

function clearError() {
  errorBanner.hidden = true;
  errorBanner.textContent = "";
}

function applyDefaults() {
  if (!defaults) return;
  document.getElementById("I").value             = defaults.I;
  document.getElementById("V_thr").value         = defaults.V_thr;
  document.getElementById("R").value             = defaults.R;
  document.getElementById("simulation_time").value = defaults.simulation_time;
  document.getElementById("t_ref").value         = defaults.t_ref ?? 2.0;
  document.getElementById("adapt_enabled").checked = defaults.adapt_enabled ?? false;
  document.getElementById("delta_thr").value     = defaults.delta_thr ?? 5.0;
  document.getElementById("tau_adapt").value     = defaults.tau_adapt ?? 100.0;
  document.getElementById("syn_spikes").value    = "";
  document.getElementById("syn_weight").value    = defaults.syn_weight ?? 1.0;
  document.getElementById("syn_tau").value       = defaults.syn_tau ?? 5.0;
}

function parseSynSpikes(raw) {
  const str = raw.trim();
  if (!str) return [];
  return str.split(",").map((s) => {
    const v = Number(s.trim());
    if (Number.isNaN(v)) throw new Error(`Invalid spike time: "${s.trim()}"`);
    return v;
  });
}

function getFieldNum(id, fallback) {
  const el = document.getElementById(id);
  if (!el || el.value.trim() === "") return fallback;
  const v = Number(el.value);
  return Number.isNaN(v) ? fallback : v;
}

function buildPayload() {
  return {
    I:               document.getElementById("I").value.trim()     || defaults.I,
    V_thr:           document.getElementById("V_thr").value.trim() || defaults.V_thr,
    R:               document.getElementById("R").value.trim()     || defaults.R,
    simulation_time: getFieldNum("simulation_time", defaults.simulation_time),
    t_ref:           getFieldNum("t_ref",     defaults.t_ref     ?? 2.0),
    adapt_enabled:   document.getElementById("adapt_enabled")?.checked ?? false,
    delta_thr:       getFieldNum("delta_thr", defaults.delta_thr ?? 5.0),
    tau_adapt:       getFieldNum("tau_adapt", defaults.tau_adapt ?? 100.0),
    syn_spikes:      parseSynSpikes(document.getElementById("syn_spikes")?.value ?? ""),
    syn_weight:      getFieldNum("syn_weight", defaults.syn_weight ?? 1.0),
    syn_tau:         getFieldNum("syn_tau",    defaults.syn_tau   ?? 5.0),
  };
}

// Flash the neuron SVG when spikes occurred.
function animateNeuron(spike_times) {
  if (!neuronSvg || spike_times.length === 0) return;
  neuronSvg.classList.remove("firing");
  // Force reflow so re-adding the class re-triggers the animation.
  void neuronSvg.offsetWidth;
  neuronSvg.classList.add("firing");
  setTimeout(() => neuronSvg.classList.remove("firing"), 600);
}

function renderSpikes(result) {
  const n = result.spike_times.length;
  spikeSummary.textContent = `Total spikes: ${n}`;

  if (n === 0) {
    spikeTimesEl.textContent = "No spikes in this run.";
    spikeStatsEl.textContent = "";
    return;
  }

  const simSecs = (result.meta?.params?.simulation_time ?? 200) / 1000;
  const rate    = (n / simSecs).toFixed(1);
  const isi     = result.spike_times.slice(1).map((t, i) => t - result.spike_times[i]);
  const meanISI = isi.length ? (isi.reduce((a, b) => a + b, 0) / isi.length).toFixed(1) : "—";

  spikeStatsEl.textContent = `Mean rate: ${rate} Hz  ·  Mean ISI: ${meanISI} ms`;
  spikeTimesEl.textContent = result.spike_times.map((t) => `${t.toFixed(1)} ms`).join(", ");
}

// Tab switching.
function showTab(tab) {
  if (tab === "sim") {
    tabSim.classList.add("active");
    tabFI.classList.remove("active");
    plotDiv.hidden   = false;
    fiPlotDiv.hidden = true;
  } else {
    tabFI.classList.add("active");
    tabSim.classList.remove("active");
    plotDiv.hidden   = true;
    fiPlotDiv.hidden = false;
  }
}

async function onSubmit(event) {
  event.preventDefault();
  clearError();
  runBtn.disabled = true;
  runBtn.textContent = "Running…";

  try {
    const payload = buildPayload();
    const result  = await runSimulation(payload);
    showTab("sim");
    renderPlot(result);
    renderSpikes(result);
    animateNeuron(result.spike_times);
  } catch (err) {
    showError(err.message || "Something went wrong.");
  } finally {
    runBtn.disabled = false;
    runBtn.textContent = "Run Simulation";
  }
}

async function onFICurve() {
  clearError();
  fiBtn.disabled = true;
  fiBtn.textContent = "Computing…";

  try {
    const payload = buildPayload();
    const fiPayload = {
      ...payload,
      fi_I_min:   0.0,
      fi_I_max:   5.0,
      fi_steps:   50,
      fi_sim_time: 500,
    };
    const data = await runFICurve(fiPayload);
    showTab("fi");
    renderFICurve(data);
  } catch (err) {
    showError(err.message || "F-I curve failed.");
  } finally {
    fiBtn.disabled = false;
    fiBtn.textContent = "F–I Curve";
  }
}

async function init() {
  try {
    defaults = await getDefaults();
    applyDefaults();
  } catch (err) {
    defaults = { I: "1.5", V_thr: "-55", R: "10", simulation_time: 200,
                 t_ref: 2.0, adapt_enabled: false, delta_thr: 5.0, tau_adapt: 100.0,
                 syn_weight: 1.0, syn_tau: 5.0 };
    applyDefaults();
    showError(`Could not load defaults from server: ${err.message}`);
  }
}

form.addEventListener("submit", onSubmit);
fiBtn.addEventListener("click", onFICurve);
resetBtn.addEventListener("click", () => { clearError(); applyDefaults(); });
tabSim.addEventListener("click", () => showTab("sim"));
tabFI.addEventListener("click",  () => showTab("fi"));

init();
