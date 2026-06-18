# lif_core

Canonical, framework-agnostic simulation engine for the LIF neuron project.

This package extracts the numerics originally prototyped in `LIF Model.ipynb`
(kept untouched, for posterity) into a clean, importable module so that both the
web backend and any future consumer (notebooks, CLIs, batch jobs) share one
implementation instead of copy-pasting it.

## Layout

- `expressions.py` — `compile_expression()`, a safe, AST-allow-listed compiler that
  turns a user string like `"1.5 + math.sin(t/10)"` into a callable `f(t)`.
- `models.py` — `NeuronModel` (abstract base) and `LIFNeuron` (the concrete model).
  New models (Izhikevich, Hodgkin-Huxley, ...) subclass `NeuronModel`.
- `simulation.py` — `SimulationResult`, the structured output of a run.

## Quick start

```python
from lif_core import LIFNeuron

neuron = LIFNeuron()
neuron.set_parameter_function("I", "1.5 + math.sin(t / 10)")
result = neuron.simulate(simulation_time=200)
print(len(result.spike_times), "spikes")
```

## Install (editable)

```bash
pip install -e .
```
