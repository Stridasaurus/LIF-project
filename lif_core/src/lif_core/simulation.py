"""Structured result type for a single neuron simulation run."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SimulationResult:
    """Output of a neuron ``simulate()`` call.

    All traces are parallel lists indexed by time step. ``spike_times`` holds the
    times (ms) at which a threshold crossing was detected.
    """

    time: List[float] = field(default_factory=list)
    voltage: List[float] = field(default_factory=list)
    current: List[float] = field(default_factory=list)
    threshold: List[float] = field(default_factory=list)
    resistance: List[float] = field(default_factory=list)
    spike_times: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable dict (used by the web API)."""
        return {
            "time": self.time,
            "voltage": self.voltage,
            "current": self.current,
            "threshold": self.threshold,
            "resistance": self.resistance,
            "spike_times": self.spike_times,
        }
