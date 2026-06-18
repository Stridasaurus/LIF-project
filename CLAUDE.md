# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

Jupyter is installed in the `base` conda env. Project dependencies (numpy, matplotlib) live in `sandbox-env`, which is registered as a Jupyter kernel.

To launch Jupyter:

```bash
conda activate base
jupyter notebook "LIF Model.ipynb"
```

Then select the `sandbox-env` kernel from the kernel dropdown in the Jupyter UI.

### First-time setup on a new machine

```bash
conda env create -f environment.yml        # recreates sandbox-env
conda run -n sandbox-env python -m ipykernel install --user --name=sandbox-env --display-name="sandbox-env"
git config core.hooksPath .githooks        # activates the pre-commit hook
chmod +x .githooks/pre-commit
```

## Running the Simulation

Open and run `LIF Model.ipynb` in Jupyter. The simulation is interactive — it prompts for parameter functions at runtime:

```
Enter I(t) [default: 1.5]:
Enter V_thr(t) [default: -55]:
Enter R(t) [default: 10]:
```

Leave any field blank to use the default constant. Inputs are evaluated as Python expressions with `t` (time in ms), `math`, and `np` in scope.

## Architecture

All code lives in a single notebook cell. The two main components are:

**`LIFNeuron` class** — holds neuron parameters and runs the Euler-method integration loop.
- `set_parameter_function(param_name, func_str)` — compiles a user-supplied string into a lambda via `eval`. Valid `param_name` values: `'I'`, `'V_thr'`, `'R'`.
- `simulate(simulation_time=100)` — steps forward by `dt` each iteration, checks for threshold crossing, resets membrane potential on spike, and returns traces + spike times.

**`run_simulation()`** — top-level entry point; collects user input, calls `simulate(200)`, and renders a 3-panel matplotlib figure (membrane potential + threshold, input current, threshold over time).

## Key Parameters and Units

| Parameter | Unit | Default |
|-----------|------|---------|
| `V_rest` | mV | -70.0 |
| `V_reset` | mV | -75.0 |
| `tau_m` | ms | 10.0 |
| `dt` | ms | 0.1 |
| `I(t)` | nA | 1.5 |
| `V_thr(t)` | mV | -55.0 |
| `R(t)` | MΩ | 10.0 |

The governing equation is `τ_m × dV/dt = -(V - V_rest) + R(t) × I(t)`, integrated with the forward Euler method.
