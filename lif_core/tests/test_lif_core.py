"""Tests for the lif_core engine: parity, expression safety, and basic behaviour."""

import math

import pytest

from lif_core import ExpressionError, LIFNeuron, compile_expression


# --------------------------------------------------------------------------- #
# Expression compiler — allow-listed expressions work                          #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "expr, t, expected",
    [
        ("1.5", 0.0, 1.5),
        ("-55", 10.0, -55.0),
        ("1.5 + math.sin(t / 10)", 0.0, 1.5),
        ("2 * t", 3.0, 6.0),
        ("t ** 2", 4.0, 16.0),
        ("np.where(t > 50, 2.0, 0.5)", 100.0, 2.0),
        ("np.where(t > 50, 2.0, 0.5)", 10.0, 0.5),
        ("3.0 if t > 100 else 0.5", 200.0, 3.0),
        ("pi", 0.0, math.pi),
    ],
)
def test_compile_expression_accepts_valid(expr, t, expected):
    func = compile_expression(expr)
    assert func(t) == pytest.approx(expected)


# --------------------------------------------------------------------------- #
# Expression compiler — malicious / invalid expressions are rejected           #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "expr",
    [
        '__import__("os").system("ls")',
        "open('/etc/passwd')",
        "t.__class__",
        "foo",
        "exec('x=1')",
        "(lambda: 1)()",
        "[x for x in range(3)]",
        "'a string'",
        "os.getcwd()",
        "t)",  # syntax error
        "",  # empty
        "   ",  # blank
    ],
)
def test_compile_expression_rejects_unsafe(expr):
    with pytest.raises(ExpressionError):
        compile_expression(expr)


# --------------------------------------------------------------------------- #
# LIFNeuron — parity with the notebook numerics                                #
# --------------------------------------------------------------------------- #


def _reference_simulate(simulation_time=200):
    """Verbatim re-implementation of the notebook loop, used as a parity oracle."""
    V_rest, V_reset, tau_m, dt = -70.0, -75.0, 10.0, 0.1
    I_func = lambda t: 1.5
    V_thr_func = lambda t: -55.0
    R_func = lambda t: 10.0

    V = V_rest
    t = 0.0
    spike_times, time_points, voltage_trace = [], [], []
    while t < simulation_time:
        I, V_thr, R = I_func(t), V_thr_func(t), R_func(t)
        if V >= V_thr:
            spike_times.append(t)
            V = V_reset
        dV_dt = (-(V - V_rest) + I * R) / tau_m
        V += dV_dt * dt
        time_points.append(t)
        voltage_trace.append(V)
        t += dt
    return time_points, voltage_trace, spike_times


def test_lif_default_matches_reference():
    result = LIFNeuron().simulate(200)
    ref_time, ref_voltage, ref_spikes = _reference_simulate(200)

    assert result.time == pytest.approx(ref_time)
    assert result.voltage == pytest.approx(ref_voltage)
    assert result.spike_times == pytest.approx(ref_spikes)


def test_lif_default_traces_consistent():
    result = LIFNeuron().simulate(200)
    n = len(result.time)
    assert n == len(result.voltage) == len(result.current) == len(result.threshold)
    # The defaults sit exactly at rheobase (steady state V = -70 + 1.5*10 = -55,
    # equal to threshold), so the neuron asymptotes toward threshold without
    # crossing it: zero spikes. This matches the notebook.
    assert result.spike_times == []


def test_lif_suprathreshold_drive_spikes():
    neuron = LIFNeuron()
    neuron.set_parameter_function("I", "2.0")  # steady state -50 mV > -55 threshold
    result = neuron.simulate(200)
    n = len(result.time)
    assert n == len(result.voltage) == len(result.current) == len(result.threshold)
    # Constant supra-threshold drive should produce periodic spiking.
    assert len(result.spike_times) > 1


def test_set_parameter_function_changes_output():
    neuron = LIFNeuron()
    neuron.set_parameter_function("I", "0.0")
    result = neuron.simulate(200)
    # With no input current the neuron should never reach threshold.
    assert result.spike_times == []


def test_set_parameter_function_rejects_unknown_param():
    with pytest.raises(ExpressionError):
        LIFNeuron().set_parameter_function("bogus", "1.0")
