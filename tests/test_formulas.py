"""Formeln: Halfin-Whitt-Funktion (Handwerte, scipy als unabhängige Referenz für Φ), Regel, exakte Staffelungen, Erlang A gegen die
abgeschnittene Kette."""

import math

import numpy as np
import pytest

import sqs_formulas as F

MU = 1 / 3


def _ctmc(c, a, theta, k_max=500):
    """Stationäre Verteilung der abgeschnittenen Kette (lineares Gleichungssystem, ohne die Formeln des Moduls)."""
    lam, mu = a * MU, MU
    n = k_max + 1
    q = np.zeros((n, n))
    for i in range(n - 1):
        q[i, i + 1] = lam
        q[i + 1, i] = min(i + 1, c) * mu + max(i + 1 - c, 0) * theta
    np.fill_diagonal(q, -q.sum(axis=1))
    mat = np.vstack([q.T[:-1], np.ones(n)])
    rhs = np.zeros(n)
    rhs[-1] = 1.0
    return np.linalg.solve(mat, rhs)


def test_normal_functions_against_scipy_and_hand_values():
    stats = pytest.importorskip("scipy.stats")
    assert F.big_phi(0.0) == pytest.approx(0.5) and F.phi(0.0) == pytest.approx(1 / math.sqrt(2 * math.pi))
    for x in (-2.0, -0.5, 0.3, 1.0, 1.96, 3.0):
        assert F.big_phi(x) == pytest.approx(stats.norm.cdf(x), abs=1e-12)
        assert F.phi(x) == pytest.approx(stats.norm.pdf(x), abs=1e-12)


def test_halfin_whitt_function_by_hand():
    """β = 0 ergibt 1; β = 1: 1/(1 + Φ(1)/φ(1)) = 0.2234; fällt streng und geht gegen 0."""
    assert F.hw_p_wait(0.0) == pytest.approx(1.0)
    assert F.hw_p_wait(1.0) == pytest.approx(1 / (1 + 0.8413447 / 0.2419707), rel=1e-6)
    values = [F.hw_p_wait(b / 4) for b in range(0, 25)]
    assert all(x > y for x, y in zip(values, values[1:])) and values[-1] < 0.005


@pytest.mark.parametrize("alpha", [0.8, 0.5, 0.2, 0.1, 0.05, 0.01])
def test_hw_beta_is_the_inverse_of_the_halfin_whitt_function(alpha):
    assert F.hw_p_wait(F.hw_beta_for(alpha)) == pytest.approx(alpha, abs=1e-9)


def test_hw_beta_rejects_alpha_outside_the_open_unit_interval():
    for bad in (0.0, 1.0, -0.1, 1.5):
        with pytest.raises(ValueError):
            F.hw_beta_for(bad)


def test_rule_and_effective_beta_by_hand():
    """c = ⌈a + β√a⌉: (100, 1) → 110; (10, 1) → ⌈13.16⌉ = 14; (100, −1) → 90; nie unter 1."""
    assert F.rule_servers(100, 1.0) == 110 and F.rule_servers(10, 1.0) == 14 and F.rule_servers(100, -1.0) == 90
    assert F.rule_servers(1, -5.0) == 1 and F.rule_servers(20, F.hw_beta_for(0.2)) == 25
    assert F.beta_eff(110, 100) == pytest.approx(1.0) and F.beta_eff(14, 10) == pytest.approx(4 / math.sqrt(10))


def test_erlang_b_and_c_hand_values():
    """B(1, 1) = 1/2, B(2, 1) = 0.2, C(2, 1) = 1/3; Erlang C verlangt c > a."""
    assert F.erlang_b(2, 1.0) == pytest.approx(0.2) and F.erlang_c(2, 1.0) == pytest.approx(1 / 3)
    assert F.erlang_c_wq(2, 1.0, 1.0) == pytest.approx(1 / 3)
    for c, a in ((2, 2.0), (3, 3.5)):
        with pytest.raises(ValueError):
            F.erlang_c(c, a)


@pytest.mark.parametrize("c", range(1, 21))
def test_erlang_c_matches_the_textbook_sum_formula(c):
    a = 0.85 * c
    head = sum(a ** k / math.factorial(k) for k in range(c))
    tail = a ** c / (math.factorial(c) * (1 - a / c))
    assert F.erlang_c(c, a) == pytest.approx(tail / (head + tail), rel=1e-9)


@pytest.mark.parametrize("c,a,theta", [(4, 5.2, 0.2), (10, 9.5, 0.2), (3, 1.5, 1.0), (8, 6.4, 0.5), (6, 9.0, 0.3)])
def test_erlang_a_matches_the_ctmc_reference(c, a, theta):
    pi = _ctmc(c, a, theta)
    states = np.arange(len(pi))
    lq = (pi[c:] * (states[c:] - c)).sum()
    m = F.erlang_a_metrics(c, a, MU, theta)
    assert m["p_abandon"] == pytest.approx(theta * lq / (a * MU), rel=1e-6)
    assert m["p_wait"] == pytest.approx(pi[c:].sum(), rel=1e-6)
    assert m["Wq"] == pytest.approx(lq / (a * MU), rel=1e-6)
    assert m["utilisation"] == pytest.approx((np.minimum(states, c) * pi).sum() / c, rel=1e-6)


def test_erlang_a_hand_value_and_limit():
    """c = 1, λ = μ = θ = 1 (a = 1, μ = 1): P(ab) = 1/e; Geduld unendlich (θ → 0) mit c > a ist Erlang C."""
    assert F.erlang_a_metrics(1, 1.0, 1.0, 1.0)["p_abandon"] == pytest.approx(1 / math.e)
    m = F.erlang_a_metrics(12, 10.0, MU, 1e-9)
    assert m["Wq"] == pytest.approx(F.erlang_c_wq(12, 10.0, MU), rel=1e-5)
    assert m["p_wait"] == pytest.approx(F.erlang_c(12, 10.0), rel=1e-5)


def test_exact_staffing_for_wait_probability_is_minimal_and_feasible():
    for a, alpha in ((10, 0.5), (100, 0.2), (1000, 0.2), (50, 0.05)):
        c = F.exact_servers_for_wait_prob(a, alpha)
        assert c > a and F.erlang_c(c, a) <= alpha
        assert c - 1 <= a or F.erlang_c(c - 1, a) > alpha


def test_exact_staffing_for_mean_wait_needs_two_or_three_extra_lanes_for_every_size():
    extras = [F.exact_servers_for_mean_wait(a, MU, 1.0) - a for a in (5, 10, 20, 50, 100, 500, 1000, 5000)]
    assert extras == [2, 2, 2, 3, 3, 3, 3, 3]


def test_exact_staffing_for_abandon_is_minimal_and_may_be_below_the_offer():
    theta = 0.2
    for a in (10, 50, 200, 1000, 5000):
        c = F.exact_servers_for_abandon(a, MU, theta, 0.01)
        assert F.erlang_a_metrics(c, a, MU, theta)["p_abandon"] <= 0.01 < F.erlang_a_metrics(c - 1, a, MU, theta)["p_abandon"]
    assert F.exact_servers_for_abandon(5000, MU, theta, 0.01) < 5000 and F.exact_servers_for_abandon(200, MU, theta, 0.01) > 200


def test_convergence_error_of_the_halfin_whitt_formula_shrinks_with_the_offer():
    errors = []
    for a in (10, 100, 1000, 5000):
        c = F.rule_servers(a, 1.0)
        errors.append(abs(F.erlang_c(c, a) - F.hw_p_wait(F.beta_eff(c, a))))
    assert all(x > y for x, y in zip(errors, errors[1:])) and errors[0] > 0.03 and errors[-1] < 0.003
