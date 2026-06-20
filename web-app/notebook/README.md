# LIF Model — Original Class Notebook

This is the original final project submitted for **CSE1505 – Intro to Programming (Python), Fall 2025**.

It is preserved here unchanged. The simulation logic has since been extracted into the [`lif_core`](../../lif_core) engine and rebuilt as a browser-based web app in [`web-app/frontend`](../frontend).

## Running the notebook

```bash
conda activate base
jupyter notebook "LIF Model.ipynb"
```

Select the `sandbox-env` kernel from the kernel dropdown. See the [root CLAUDE.md](../../CLAUDE.md) for first-time conda setup.

## What it does

Prompts for time-varying parameter functions at runtime:

```
Enter I(t)     [default: 1.5]:
Enter V_thr(t) [default: -55]:
Enter R(t)     [default: 10]:
```

Inputs are evaluated as Python expressions with `t` (ms), `math`, and `np` in scope. Produces a 3-panel matplotlib figure: membrane potential + threshold, input current, and threshold over time.
