// Plotly rendering for simulation results and F-I curves.
//
// renderPlot(result)        — 3 stacked subplots, linked x-axis (voltage largest)
// renderISIHistogram(times) — ISI distribution histogram
// renderPhasePortrait(V,dt) — phase-plane V vs dV/dt
// renderFICurve(data)       — firing rate vs. current

const PLOT_COLORS = {
  voltage:    "#4f9cff",
  threshold:  "#ff6b6b",
  spike:      "#ffd166",
  current:    "#3ddc97",
  resistance: "#ff9100",
  fi_fill:    "#4f9cff",
  rheobase:   "#ff6b6b",
  bg:         "#1a2233",
  axes_bg:    "#0f1420",
  grid:       "#2b3650",
  text:       "#e7ecf3",
};

// eslint-disable-next-line no-unused-vars
function renderPlot(result) {
  const { time, voltage, current, threshold, resistance, spike_times } = result;

  // Panel 1: Membrane potential + threshold + spike markers
  const vTrace = {
    x: time, y: voltage, type: "scatter", mode: "lines", name: "V_m",
    line: { color: PLOT_COLORS.voltage, width: 2 },
    xaxis: "x", yaxis: "y",
  };
  const threshTrace = {
    x: time, y: threshold, type: "scatter", mode: "lines", name: "V_thr",
    line: { color: PLOT_COLORS.threshold, width: 1.5, dash: "dash" },
    xaxis: "x", yaxis: "y",
  };
  const dt = time.length > 1 ? time[1] - time[0] : 0.1;
  const spikeY = spike_times.map((st) => {
    const idx = Math.min(Math.round(st / dt), threshold.length - 1);
    return threshold[idx];
  });
  const spikeTrace = {
    x: spike_times, y: spikeY, type: "scatter", mode: "markers", name: "Spike",
    marker: { color: PLOT_COLORS.spike, size: 9, symbol: "triangle-up" },
    xaxis: "x", yaxis: "y",
  };

  // Panel 2: Input current
  const currentTrace = {
    x: time, y: current, type: "scatter", mode: "lines", name: "I(t)",
    line: { color: PLOT_COLORS.current, width: 1.5 },
    xaxis: "x2", yaxis: "y2",
  };

  // Panel 3: Resistance
  const resistanceTrace = {
    x: time, y: resistance, type: "scatter", mode: "lines", name: "R(t)",
    line: { color: PLOT_COLORS.resistance, width: 1.5 },
    xaxis: "x3", yaxis: "y3",
  };

  const ax = { gridcolor: PLOT_COLORS.grid, color: PLOT_COLORS.text };

  const layout = {
    paper_bgcolor: PLOT_COLORS.bg,
    plot_bgcolor:  PLOT_COLORS.axes_bg,
    font: { color: PLOT_COLORS.text, family: "monospace" },
    showlegend: true,
    legend: { orientation: "h", y: 1.04, x: 0 },
    margin: { t: 20, r: 20, b: 45, l: 65 },
    xaxis:  { ...ax, domain: [0, 1], anchor: "y",  showticklabels: false },
    xaxis2: { ...ax, domain: [0, 1], anchor: "y2", showticklabels: false, matches: "x" },
    xaxis3: { ...ax, domain: [0, 1], anchor: "y3", title: "Time (ms)", matches: "x" },
    // Voltage gets ~46% of height; current and resistance split the rest
    yaxis:  { ...ax, domain: [0.54, 1.00], title: "V_m (mV)" },
    yaxis2: { ...ax, domain: [0.28, 0.50], title: "I (nA)" },
    yaxis3: { ...ax, domain: [0.00, 0.24], title: "R (MΩ)" },
  };

  Plotly.react("plot", [vTrace, threshTrace, spikeTrace, currentTrace, resistanceTrace], layout,
    { responsive: true, displaylogo: false });
}

// eslint-disable-next-line no-unused-vars
function renderISIHistogram(spike_times) {
  const emptyLayout = {
    paper_bgcolor: PLOT_COLORS.bg, plot_bgcolor: PLOT_COLORS.axes_bg,
    font: { color: PLOT_COLORS.text, family: "monospace" },
    margin: { t: 20, r: 20, b: 20, l: 20 },
    xaxis: { visible: false }, yaxis: { visible: false },
    annotations: [{ text: "Run a simulation with ≥ 2 spikes to see the ISI distribution.",
      xref: "paper", yref: "paper", x: 0.5, y: 0.5, showarrow: false,
      font: { color: PLOT_COLORS.grid, size: 14 } }],
  };

  if (spike_times.length < 2) {
    Plotly.react("isi-plot", [], emptyLayout, { responsive: true, displaylogo: false });
    return;
  }

  const isis = spike_times.slice(1).map((t, i) => t - spike_times[i]);
  const mean = isis.reduce((a, b) => a + b, 0) / isis.length;
  const std  = Math.sqrt(isis.map(x => (x - mean) ** 2).reduce((a, b) => a + b, 0) / isis.length);
  const cv   = mean > 0 ? (std / mean).toFixed(3) : "—";

  const layout = {
    paper_bgcolor: PLOT_COLORS.bg, plot_bgcolor: PLOT_COLORS.axes_bg,
    font: { color: PLOT_COLORS.text, family: "monospace" },
    margin: { t: 45, r: 20, b: 55, l: 65 },
    title: { text: `ISI Distribution  ·  mean ${mean.toFixed(1)} ms  ·  CV ${cv}`,
             font: { size: 12, color: PLOT_COLORS.text }, x: 0 },
    xaxis: { title: "Inter-Spike Interval (ms)", gridcolor: PLOT_COLORS.grid, color: PLOT_COLORS.text },
    yaxis: { title: "Count", gridcolor: PLOT_COLORS.grid, color: PLOT_COLORS.text },
    showlegend: false,
  };

  Plotly.react("isi-plot",
    [{ x: isis, type: "histogram", autobinx: true,
       marker: { color: PLOT_COLORS.voltage, opacity: 0.85,
                 line: { color: PLOT_COLORS.bg, width: 1 } } }],
    layout, { responsive: true, displaylogo: false });
}

// eslint-disable-next-line no-unused-vars
function renderPhasePortrait(voltage, dt) {
  if (!voltage || voltage.length < 2) return;

  const dvdt   = voltage.slice(1).map((v, i) => (v - voltage[i]) / dt);
  const v_plot = voltage.slice(0, -1);

  const layout = {
    paper_bgcolor: PLOT_COLORS.bg, plot_bgcolor: PLOT_COLORS.axes_bg,
    font: { color: PLOT_COLORS.text, family: "monospace" },
    margin: { t: 20, r: 20, b: 55, l: 70 },
    xaxis: { title: "V (mV)", gridcolor: PLOT_COLORS.grid, color: PLOT_COLORS.text },
    yaxis: { title: "dV/dt (mV/ms)", gridcolor: PLOT_COLORS.grid, color: PLOT_COLORS.text },
    showlegend: true,
    legend: { orientation: "h", y: 1.06, x: 0 },
  };

  Plotly.react("phase-plot", [
    { x: v_plot, y: dvdt, type: "scatter", mode: "lines", name: "Trajectory",
      line: { color: PLOT_COLORS.voltage, width: 1.5 } },
    { x: [v_plot[0]], y: [dvdt[0]], type: "scatter", mode: "markers", name: "Start",
      marker: { color: PLOT_COLORS.current, size: 10, symbol: "circle" } },
  ], layout, { responsive: true, displaylogo: false });
}

// eslint-disable-next-line no-unused-vars
function renderFICurve(data) {
  const { currents, rates } = data;

  let rheobase = null;
  for (let i = 0; i < rates.length; i++) {
    if (rates[i] > 0) { rheobase = currents[i]; break; }
  }

  const shapes = rheobase !== null ? [{
    type: "line", x0: rheobase, x1: rheobase, y0: 0, y1: 1,
    xref: "x", yref: "paper",
    line: { color: PLOT_COLORS.rheobase, width: 1.5, dash: "dash" },
  }] : [];

  const annotations = rheobase !== null ? [{
    x: rheobase, y: 1, xref: "x", yref: "paper",
    text: `Rheobase ≈ ${rheobase.toFixed(2)} nA`,
    showarrow: false, yanchor: "bottom",
    font: { color: PLOT_COLORS.rheobase, size: 11 },
  }] : [];

  const layout = {
    paper_bgcolor: PLOT_COLORS.bg, plot_bgcolor: PLOT_COLORS.axes_bg,
    font: { color: PLOT_COLORS.text, family: "monospace" },
    margin: { t: 30, r: 20, b: 55, l: 65 },
    xaxis: { title: "Input Current  I (nA)", gridcolor: PLOT_COLORS.grid, color: PLOT_COLORS.text },
    yaxis: { title: "Firing Rate (Hz)",      gridcolor: PLOT_COLORS.grid, color: PLOT_COLORS.text },
    showlegend: false,
    shapes, annotations,
  };

  Plotly.react("fi-plot", [
    { x: currents, y: rates, type: "scatter", mode: "none",
      fill: "tozeroy", fillcolor: `${PLOT_COLORS.fi_fill}22`, hoverinfo: "skip" },
    { x: currents, y: rates, type: "scatter", mode: "lines",
      line: { color: PLOT_COLORS.fi_fill, width: 2.5 } },
  ], layout, { responsive: true, displaylogo: false });
}
