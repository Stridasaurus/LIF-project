// Plotly rendering for a simulation result.
//
// Two stacked, x-axis-linked subplots:
//   (1) membrane potential V_m(t) with the threshold (dashed) and spike markers
//   (2) input current I(t)

// eslint-disable-next-line no-unused-vars
function renderPlot(result) {
  const { time, voltage, current, threshold, spike_times } = result;

  const vTrace = {
    x: time,
    y: voltage,
    type: "scatter",
    mode: "lines",
    name: "V_m",
    line: { color: "#4f9cff", width: 2 },
    xaxis: "x",
    yaxis: "y",
  };

  const threshTrace = {
    x: time,
    y: threshold,
    type: "scatter",
    mode: "lines",
    name: "Threshold",
    line: { color: "#ff6b6b", width: 1.5, dash: "dash" },
    xaxis: "x",
    yaxis: "y",
  };

  // Spike markers placed at the threshold level for each spike time.
  const spikeY = spike_times.map((st) => {
    const idx = Math.min(
      Math.round(st / (time[1] - time[0] || 0.1)),
      threshold.length - 1
    );
    return threshold[idx];
  });

  const spikeTrace = {
    x: spike_times,
    y: spikeY,
    type: "scatter",
    mode: "markers",
    name: "Spike",
    marker: { color: "#ffd166", size: 9, symbol: "triangle-up" },
    xaxis: "x",
    yaxis: "y",
  };

  const currentTrace = {
    x: time,
    y: current,
    type: "scatter",
    mode: "lines",
    name: "I(t)",
    line: { color: "#3ddc97", width: 1.5 },
    xaxis: "x2",
    yaxis: "y2",
  };

  const layout = {
    paper_bgcolor: "#1a2233",
    plot_bgcolor: "#0f1420",
    font: { color: "#e7ecf3" },
    showlegend: true,
    legend: { orientation: "h", y: 1.12 },
    margin: { t: 30, r: 20, b: 45, l: 60 },
    grid: { rows: 2, columns: 1, pattern: "independent", roworder: "top to bottom" },
    xaxis: { domain: [0, 1], anchor: "y", showticklabels: false, gridcolor: "#2b3650" },
    yaxis: {
      domain: [0.42, 1],
      title: "Membrane potential (mV)",
      gridcolor: "#2b3650",
    },
    xaxis2: {
      domain: [0, 1],
      anchor: "y2",
      title: "Time (ms)",
      gridcolor: "#2b3650",
      matches: "x",
    },
    yaxis2: {
      domain: [0, 0.3],
      title: "Current (nA)",
      gridcolor: "#2b3650",
    },
  };

  const config = { responsive: true, displaylogo: false };

  Plotly.react(
    "plot",
    [vTrace, threshTrace, spikeTrace, currentTrace],
    layout,
    config
  );
}
