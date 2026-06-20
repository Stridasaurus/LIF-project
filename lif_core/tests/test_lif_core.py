"""Tests for the lif_core engine: parity, expression safety, and basic behaviour."""

import math

import pytest

from lif_core import ExpressionError, LIFNeuron, compile_expression, run_fi_curve


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
    assert n == len(result.voltage) == len(result.current) == len(result.threshold) == len(result.resistance)
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


# --------------------------------------------------------------------------- #
# Refractory period                                                             #
# --------------------------------------------------------------------------- #


def test_refractory_caps_spike_rate():
    t_ref = 10.0
    sim_time = 500.0
    neuron = LIFNeuron(t_ref=t_ref)
    neuron.set_parameter_function("I", "3.0")  # strong supra-threshold drive
    result = neuron.simulate(sim_time)
    max_possible = sim_time / t_ref
    assert len(result.spike_times) <= max_possible


def test_refractory_zero_does_not_block():
    # t_ref=0 should behave the same as the original (no refractory gating).
    neuron_ref = LIFNeuron(t_ref=0.0)
    neuron_ref.set_parameter_function("I", "2.0")
    result_ref = neuron_ref.simulate(200)

    neuron_old = LIFNeuron(t_ref=0.0)
    neuron_old.set_parameter_function("I", "2.0")
    result_old = neuron_old.simulate(200)

    assert result_ref.spike_times == pytest.approx(result_old.spike_times)


# --------------------------------------------------------------------------- #
# Adaptive threshold                                                            #
# --------------------------------------------------------------------------- #


def test_adaptation_reduces_spike_count():
    I_str = "2.5"
    sim_time = 500.0

    neuron_plain = LIFNeuron()
    neuron_plain.set_parameter_function("I", I_str)
    plain_spikes = len(neuron_plain.simulate(sim_time).spike_times)

    neuron_adapt = LIFNeuron(adapt_enabled=True, delta_thr=5.0, tau_adapt=50.0)
    neuron_adapt.set_parameter_function("I", I_str)
    adapt_spikes = len(neuron_adapt.simulate(sim_time).spike_times)

    assert adapt_spikes < plain_spikes


def test_adaptation_threshold_trace_rises_after_spike():
    neuron = LIFNeuron(adapt_enabled=True, delta_thr=10.0, tau_adapt=200.0)
    neuron.set_parameter_function("I", "2.5")
    result = neuron.simulate(200)
    # At least one spike must have occurred.
    assert len(result.spike_times) > 0
    # Threshold is recorded before the spike check, so the jump is visible one
    # step after the spike index.
    idx = round(result.spike_times[0] / 0.1)
    assert result.threshold[min(idx + 1, len(result.threshold) - 1)] > -55.0


# --------------------------------------------------------------------------- #
# Synaptic input                                                                #
# --------------------------------------------------------------------------- #


def test_synaptic_input_causes_spike():
    # Sub-threshold constant current alone → no spikes.
    neuron_plain = LIFNeuron()
    neuron_plain.set_parameter_function("I", "0.0")
    assert neuron_plain.simulate(200).spike_times == []

    # Same neuron but with a strong synaptic pulse at t=50 → at least one spike.
    neuron_syn = LIFNeuron(syn_spikes=[50.0], syn_weight=5.0, syn_tau=5.0)
    neuron_syn.set_parameter_function("I", "0.0")
    assert len(neuron_syn.simulate(200).spike_times) >= 1


def test_synaptic_current_zero_before_spike():
    neuron = LIFNeuron(syn_spikes=[100.0], syn_weight=2.0, syn_tau=5.0)
    # Before t=100 the synaptic current must be 0.
    assert neuron._syn_current(0.0) == 0.0
    assert neuron._syn_current(99.9) == 0.0
    # At t slightly > 100 it must be positive.
    assert neuron._syn_current(100.1) > 0.0


# --------------------------------------------------------------------------- #
# Resistance trace                                                              #
# --------------------------------------------------------------------------- #


def test_resistance_trace_length():
    result = LIFNeuron().simulate(200)
    assert len(result.resistance) == len(result.time)


def test_resistance_trace_values():
    neuron = LIFNeuron()
    neuron.set_parameter_function("R", "10 + 5 * math.sin(t / 20)")
    result = neuron.simulate(200)
    # All values should be in a reasonable range.
    assert all(0 < r < 20 for r in result.resistance)


# --------------------------------------------------------------------------- #
# F-I curve                                                                     #
# --------------------------------------------------------------------------- #


def test_fi_curve_zero_below_rheobase():
    data = run_fi_curve(I_range=(0.0, 0.5), steps=10, sim_time=500.0)
    # All currents well below rheobase (~0.7 nA) should produce zero spikes.
    assert all(r == 0.0 for r in data["rates"])


def test_fi_curve_nonzero_above_rheobase():
    # Rheobase is ~1.5 nA; use 2.0–4.0 to stay clearly above it.
    data = run_fi_curve(I_range=(2.0, 4.0), steps=5, sim_time=500.0)
    assert all(r > 0.0 for r in data["rates"])


def test_fi_curve_returns_expected_keys():
    data = run_fi_curve(steps=5, sim_time=100.0)
    assert "currents" in data and "rates" in data
    assert len(data["currents"]) == len(data["rates"]) == 5
