// Wires the form to the API and the plot. Depends on api.js and plot.js.

const form = document.getElementById("sim-form");
const runBtn = document.getElementById("run-btn");
const resetBtn = document.getElementById("reset-btn");
const errorBanner = document.getElementById("error-banner");
const spikeSummary = document.getElementById("spike-summary");
const spikeTimesEl = document.getElementById("spike-times");

let defaults = null;

function showError(message) {
  errorBanner.textContent = message;
  errorBanner.hidden = false;
}

function clearError() {
  errorBanner.hidden = true;
  errorBanner.textContent = "";
}

// Populate the form fields from server defaults (single source of truth).
function applyDefaults() {
  if (!defaults) return;
  document.getElementById("I").value = defaults.I;
  document.getElementById("V_thr").value = defaults.V_thr;
  document.getElementById("R").value = defaults.R;
  document.getElementById("simulation_time").value = defaults.simulation_time;
}

function buildPayload() {
  return {
    I: document.getElementById("I").value.trim() || defaults.I,
    V_thr: document.getElementById("V_thr").value.trim() || defaults.V_thr,
    R: document.getElementById("R").value.trim() || defaults.R,
    simulation_time: Number(
      document.getElementById("simulation_time").value || defaults.simulation_time
    ),
  };
}

function renderSpikes(result) {
  const n = result.spike_times.length;
  spikeSummary.textContent = `Total spikes: ${n}`;
  if (n === 0) {
    spikeTimesEl.textContent = "No spikes in this run.";
    return;
  }
  spikeTimesEl.textContent = result.spike_times
    .map((t) => `${t.toFixed(1)} ms`)
    .join(", ");
}

async function onSubmit(event) {
  event.preventDefault();
  clearError();
  runBtn.disabled = true;
  runBtn.textContent = "Running…";

  try {
    const result = await runSimulation(buildPayload());
    renderPlot(result);
    renderSpikes(result);
  } catch (err) {
    showError(err.message || "Something went wrong.");
  } finally {
    runBtn.disabled = false;
    runBtn.textContent = "Run Simulation";
  }
}

async function init() {
  try {
    defaults = await getDefaults();
    applyDefaults();
  } catch (err) {
    // Fall back to hard-coded notebook defaults if the API is unreachable.
    defaults = { I: "1.5", V_thr: "-55", R: "10", simulation_time: 200 };
    applyDefaults();
    showError(`Could not load defaults from server: ${err.message}`);
  }
}

form.addEventListener("submit", onSubmit);
resetBtn.addEventListener("click", () => {
  clearError();
  applyDefaults();
});

init();
