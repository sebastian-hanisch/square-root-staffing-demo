"""Auswertung: Gate-Bericht, Konvergenzpunkte, Tabellen, Regime, Ziele, Skalierung."""

import math

import pytest

import sqs_constants as C
import sqs_evaluation as E
import sqs_formulas as F
from sqs_simulation import MU


def test_gate_report_normal_case():
    r = E.gate_report(100, 1.0, 5)
    assert r["c"] == 110 and r["beta_eff"] == pytest.approx(1.0) and not r["overload"] and r["rho"] == pytest.approx(100 / 110)
    assert r["erlang_c"]["p_wait"] == pytest.approx(F.erlang_c(110, 100)) and r["hw_p_wait"] == pytest.approx(F.hw_p_wait(1.0))
    assert r["erlang_a"]["p_abandon"] == pytest.approx(F.erlang_a_metrics(110, 100, MU, 0.2)["p_abandon"])


def test_gate_report_overload_has_no_erlang_c_and_no_halfin_whitt_value():
    r = E.gate_report(100, -1.0, 5)
    assert r["c"] == 90 and r["overload"] and r["erlang_c"] is None and r["hw_p_wait"] is None and r["rho"] > 1
    assert r["erlang_a"]["p_abandon"] > 0.1
    at_zero = E.gate_report(100, 0.0, 5)
    assert at_zero["c"] == 100 and at_zero["overload"] and at_zero["erlang_c"] is None        # c = a: ρ = 100 %


def test_simulation_wrappers_return_matching_shapes():
    sim = E.simulate_gate(50, 57, 5, 5000, 3)
    assert sim.c == 57 and 0 <= sim.abandon_rate < 1
    no_abandon = E.simulate_gate_no_abandon(50, 57, 5000, 3)
    assert set(no_abandon) == {"p_wait", "Wq"} and 0 < no_abandon["p_wait"] < 1


def test_convergence_points_cover_the_beta_range_and_follow_the_exact_values():
    pts = E.convergence_points(100)
    betas = [b for b, _ in pts]
    assert betas[0] == pytest.approx(0.1) and betas[-1] == pytest.approx((math.ceil(100 + 35) - 100) / 10)
    assert all(x > y for (_, x), (_, y) in zip(pts, pts[1:]))
    assert dict((round(b, 3), p) for b, p in pts)[1.0] == pytest.approx(F.erlang_c(110, 100))


def test_staffing_table_by_hand_and_rule_hits():
    t = E.staffing_table(0.2, a_values=(10, 20, 100))
    assert t["beta"] == pytest.approx(1.0615, abs=0.0005)
    rows = {r["a"]: r for r in t["rows"]}
    assert (rows[10]["exact"], rows[10]["rule"]) == (14, 14) and (rows[20]["exact"], rows[20]["rule"]) == (26, 25)
    assert rows[20]["diff"] == -1 and rows[100]["diff"] == 0 and rows[100]["extra_exact"] == 11
    assert rows[20]["p_wait_rule"] > 0.2 > rows[100]["p_wait_rule"] - 0.01          # die Regel verfehlt das Ziel bei a = 20 knapp


def test_regime_curve_is_monotone_in_beta():
    curve = E.regime_curve(200, 5)
    betas = [b for b, _, _ in curve]
    assert betas == sorted(betas) and betas[0] < -3 and betas[-1] > 2.5
    waits = [w for _, w, _ in curve]
    abandons = [p for _, _, p in curve]
    assert all(x >= y - 1e-12 for x, y in zip(waits, waits[1:])) and all(x >= y - 1e-12 for x, y in zip(abandons, abandons[1:]))
    assert waits[0] > 0.99 and waits[-1] < 0.05


def test_target_comparison_by_hand():
    rows = {r["a"]: r for r in E.target_comparison(a_values=(100, 1000, 5000))}
    assert (rows[100]["wait_prob"], rows[100]["mean_wait"], rows[100]["abandon"]) == (11, 3, 8)
    assert rows[1000]["mean_wait"] == 3 and rows[1000]["abandon"] == 3
    assert rows[5000]["abandon"] < 0 < rows[5000]["wait_prob"]


def test_scaling_table_converges_at_fixed_beta():
    rows = E.scaling_table(1.0, 5, a_values=(100, 500, 1000, 5000))
    scaled = [r["p_ab_scaled"] for r in rows]
    assert max(scaled) / min(scaled) < 1.15 and all(0.055 < s < 0.075 for s in scaled)
    zero = E.scaling_table(0.0, 5, a_values=(10, 100, 5000))
    assert max(r["p_ab_scaled"] for r in zero) - min(r["p_ab_scaled"] for r in zero) < 0.005
    assert all(r["beta_eff"] == 0 for r in zero)


def test_constants_axes_are_consistent():
    assert set(C.HW_CURVE_A) <= set(C.TABLE_A) | {10, 100, 1000} and C.DEFAULT_A in C.A_OPTIONS
    assert C.DEFAULT_BETA == C.BETA_MIN + C.BETA_STEP * round((C.DEFAULT_BETA - C.BETA_MIN) / C.BETA_STEP)
