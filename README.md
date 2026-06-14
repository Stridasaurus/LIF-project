# Leaky Integrate-and-Fire Neuron Simulator
*Author: Strider Settgast* 
#### A Python simulation of a leaky integrate-and-fire (LIF) neuron model, implemented as a final project for CSE1505 – Intro to Programming (Python), Fall 2025.

## Overview

The LIF model treats a neuron as an RC electrical circuit. Input current causes charge to accumulate across the cell membrane; when the membrane potential crosses a threshold, the neuron "fires" (an action potential) and resets. This simulator lets you configure all neuron parameters as arbitrary functions of time and visualizes the results.

The membrane potential is governed by:

```
τ_m × (dV/dt) = -(V - V_rest) + R(t) × I(t)
```

integrated numerically via the Euler method.

## Features

- Configurable neuron parameters as functions of time (`t`, `math`, `np` supported)
- Spike detection and automatic membrane potential reset
- Plots of membrane potential, input current, spike threshold, and resistance over time
- Spike time reporting

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `V_rest`  | -70.0 mV | Resting membrane potential |
| `V_reset` | -75.0 mV | Post-spike reset potential |
| `tau_m`   | 10.0 ms  | Membrane time constant |
| `dt`      | 0.1 ms   | Simulation time step |
| `I(t)`    | 1.5 nA   | Input current (function of time) |
| `V_thr(t)`| -55.0 mV | Spike threshold (function of time) |
| `R(t)`    | 10.0 MΩ  | Membrane resistance (function of time) |

## Usage

Run the notebook or script and enter parameter functions when prompted. Leave a field blank to use the default constant value.

```
=== Leaky Integrate and Fire Neuron Simulator ===
Enter functions using t (time), math.*, np.*
Leave blank to use constant default values (default at rheobase)

Enter I(t) (nA) [default: 1.5]:
Enter V_thr(t) (mV) [default: -55]:
Enter R(t) (MΩ) [default: 10]:
```

**Example inputs:**

```python
I(t):     2*np.sin(t)**2       # Oscillating current
V_thr(t): -55+np.sin(t)        # Time-varying threshold
R(t):     10*np.sin(t)         # Time-varying resistance

# Conditional logic is also supported:
I(t):     1.5*np.random.normal()**2 if t > 100 else 1.5*np.random.normal()**2
```

## Project Structure

```
LIF_Model.ipynb   # Main simulation notebook
README.md
```

## Dependencies

- Python 3.11+
- NumPy
- Matplotlib

Install dependencies with:

```bash
pip install numpy matplotlib
```

## References

- Gerstner, W., Kistler, W. M., Naud, R., & Paninski, L. (2014). *Neuronal Dynamics*. Cambridge University Press.
- Gerstner, W., & Kistler, W. M. (2008). *Spiking Neuron Models*, Ch. 4.1.1. Cambridge University Press.
- [NumPy Documentation](https://numpy.org/doc/)
- [Matplotlib Documentation](https://matplotlib.org/stable/index.html)
- [Neuroscience Online – UT Houston](https://nba.uth.tmc.edu/neuroscience)
