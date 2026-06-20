// Plotly rendering for simulation results and F-I curves.
//
// renderPlot(result)   — 4 stacked subplots, linked x-axis
// renderFICurve(data)  — single firing-rate vs. current plot

const PLOT_COLORS = {
  voltage:    "#4f9cff",   // axon blue
  threshold:  "#ff6b6b",   // action-potential red
  spike:      "#ffd166",   // spike marker gold
  current:    "#3ddc97",   // synapse green
  resistance: "#ff9100",   // myelin orange
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

  // --- Panel 1: Membrane potential + threshold ---
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

  // --- Panel 2: Input current ---
  const currentTrace = {
    x: time, y: current, type: "scatter", mode: "lines", name: "I(t)",
    line: { color: PLOT_COLORS.current, width: 1.5 },
    xaxis: "x2", yaxis: "y2",
  };

  // --- Panel 3: Resistance ---
  const resistanceTrace = {
    x: time, y: resistance, type: "scatter", mode: "lines", name: "R(t)",
    line: { color: PLOT_COLORS.resistance, width: 1.5 },
    xaxis: "x3", yaxis: "y3",
  };

  const sharedAxisStyle = { gridcolor: PLOT_COLORS.grid, color: PLOT_COLORS.text };

  const layout = {
    paper_bgcolor: PLOT_COLORS.bg,
    plot_bgcolor:  PLOT_COLORS.axes_bg,
    font: { color: PLOT_COLORS.text, family: "monospace" },
    showlegend: true,
    legend: { orientation: "h", y: 1.04, x: 0 },
    margin: { t: 20, r: 20, b: 45, l: 65 },

    // x-axes (all share the same range via "matches")
    xaxis:  { ...sharedAxisStyle, domain: [0,1], anchor: "y",  showticklabels: false },
    xaxis2: { ...sharedAxisStyle, domain: [0,1], anchor: "y2", showticklabels: false, matches: "x" },
    xaxis3: { ...sharedAxisStyle, domain: [0,1], anchor: "y3", title: "Time (ms)", matches: "x" },

    // y-axes (voltage gets ~half the height; current and resistance split the rest)
    yaxis:  { ...sharedAxisStyle, domain: [0.54, 1.00], title: "V_m (mV)" },
    yaxis2: { ...sharedAxisStyle, domain: [0.28, 0.50], title: "I (nA)" },
    yaxis3: { ...sharedAxisStyle, domain: [0.00, 0.24], title: "R (MΩ)" },
  };

  const config = { responsive: true, displaylogo: false };
  Plotly.react("plot", [vTrace, threshTrace, spikeTrace, currentTrace, resistanceTrace], layout, config);
}

// eslint-disable-next-line no-unused-vars
function renderFICurve(data) {
  const { currents, rates } = data;

  // Find rheobase (first non-zero rate).
  let rheobase = null;
  for (let i = 0; i < rates.length; i++) {
    if (rates[i] > 0) { rheobase = currents[i]; break; }
  }

  const lineTrace = {
    x: currents, y: rates, type: "scatter", mode: "lines",
    name: "Firing rate", line: { color: PLOT_COLORS.fi_fill, width: 2.5 },
  };

  const fillTrace = {
    x: currents, y: rates, type: "scatter", mode: "none",
    fill: "tozeroy", fillcolor: `${PLOT_COLORS.fi_fill}22`,
    showlegend: false, hoverinfo: "skip",
  };

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
    paper_bgcolor: PLOT_COLORS.bg,
    plot_bgcolor:  PLOT_COLORS.axes_bg,
    font: { color: PLOT_COLORS.text, family: "monospace" },
    margin: { t: 30, r: 20, b: 55, l: 65 },
    xaxis: { title: "Input Current  I (nA)", gridcolor: PLOT_COLORS.grid, color: PLOT_COLORS.text },
    yaxis: { title: "Firing Rate (Hz)",      gridcolor: PLOT_COLORS.grid, color: PLOT_COLORS.text },
    shapes,
    annotations,
  };

  const config = { responsive: true, displaylogo: false };
  Plotly.react("fi-plot", [fillTrace, lineTrace], layout, config);
}
