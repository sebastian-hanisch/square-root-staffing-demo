"""JEDE Zahl aus README und App-Texten wird hier nachgerechnet (alles exakte Rechnungen; Simulationen nur mit Marge)."""

import pytest

import sqs_constants as C
import sqs_evaluation as E
import sqs_formulas as F
from sqs_simulation import MU


def test_preset_help_numbers():
    """PRESET_HELP: a=100/β=1: 110 Spuren, exakt 23.7 % (Formel 22.3 %), 0.7 % Abbrecher; a=10/β=1: 14 Spuren, 17.4 % gegen 13.6 %;
    a=1000/β=1: 1032 Spuren, 22.3 % (Formel 21.9 %), 0.2 %; a=100/β=−1: 90 Spuren, ρ = 111 %, 91.9 % warten, 10.4 % Abbrecher, 99.5 %."""
    r = E.gate_report(100, 1.0, 5)
    assert r["c"] == 110 and r["erlang_c"]["p_wait"] == pytest.approx(0.237, abs=0.0005)
    assert r["hw_p_wait"] == pytest.approx(0.223, abs=0.0005) and r["erlang_a"]["p_abandon"] == pytest.approx(0.0067, abs=0.0005)
    s = E.gate_report(10, 1.0, 5)
    assert s["c"] == 14 and s["beta_eff"] == pytest.approx(1.265, abs=0.0005)
    assert s["erlang_c"]["p_wait"] == pytest.approx(0.174, abs=0.0005) and s["hw_p_wait"] == pytest.approx(0.136, abs=0.0005)
    b = E.gate_report(1000, 1.0, 5)
    assert b["c"] == 1032 and b["erlang_c"]["p_wait"] == pytest.approx(0.223, abs=0.0005)
    assert b["hw_p_wait"] == pytest.approx(0.219, abs=0.0005) and b["erlang_a"]["p_abandon"] == pytest.approx(0.0020, abs=0.0003)
    assert b["c"] / 1000 == pytest.approx(1.032)
    o = E.gate_report(100, -1.0, 5)
    assert o["c"] == 90 and o["rho"] == pytest.approx(1.111, abs=0.0005)
    assert o["erlang_a"]["p_wait"] == pytest.approx(0.919, abs=0.0005) and o["erlang_a"]["p_abandon"] == pytest.approx(0.1044, abs=0.0005)
    assert o["erlang_a"]["utilisation"] == pytest.approx(0.995, abs=0.0005)


def test_halfin_whitt_betas_quoted_in_readme():
    """README: β für 80 / 50 / 20 / 10 / 5 % Wartende: 0.17 / 0.51 / 1.06 / 1.42 / 1.74; HW(1) = 22.3 %."""
    for alpha, beta in ((0.8, 0.17), (0.5, 0.51), (0.2, 1.06), (0.1, 1.42), (0.05, 1.74)):
        assert F.hw_beta_for(alpha) == pytest.approx(beta, abs=0.006)
    assert F.hw_p_wait(1.0) == pytest.approx(0.223, abs=0.0005)


def test_rule_versus_exact_staffing_quoted_in_readme():
    """README: Die Regel trifft die exakte Staffelung für ≤ 50 % in 10 von 10 Angeboten und für ≤ 20 % in 8 von 10 (a = 20: exakt 26,
    Regel 25; a = 500: exakt 525, Regel 524); a = 5000: 5036 (50 %), 5076 (20 %)."""
    t50, t20 = E.staffing_table(0.5), E.staffing_table(0.2)
    assert sum(1 for r in t50["rows"] if r["diff"] == 0) == 10 and sum(1 for r in t20["rows"] if r["diff"] == 0) == 8
    miss = {r["a"]: (r["exact"], r["rule"]) for r in t20["rows"] if r["diff"] != 0}
    assert miss == {20: (26, 25), 500: (525, 524)}
    rows50, rows20 = {r["a"]: r for r in t50["rows"]}, {r["a"]: r for r in t20["rows"]}
    assert rows50[5000]["exact"] == 5036 and rows20[5000]["exact"] == 5076
    assert rows20[100]["exact"] == 111 and rows20[1000]["exact"] == 1034 and rows50[100]["exact"] == 106
    assert all(abs(r["diff"]) <= 1 for r in t50["rows"] + t20["rows"])


def test_extra_lanes_grow_like_the_square_root_for_a_wait_probability_target():
    """README: Aufschlag c − a bei „höchstens 20 % warten“: 11 (a = 100), 34 (a = 1000), 76 (a = 5000); geteilt durch √a bleibt er
    zwischen 1.0 und 1.4."""
    rows = {r["a"]: r["wait_prob"] for r in E.target_comparison()}
    assert (rows[100], rows[1000], rows[5000]) == (11, 34, 76)
    for a, extra in rows.items():
        assert 0.9 < extra / a ** 0.5 < 1.45, a


def test_mean_wait_target_needs_two_or_three_extra_lanes_for_every_size():
    """README: Ziel „mittlere Wartezeit höchstens 1 min“: Aufschlag 2 (a bis 20), 3 (a ab 50 bis 5000)."""
    rows = {r["a"]: r["mean_wait"] for r in E.target_comparison()}
    assert [rows[a] for a in C.TABLE_A] == [2, 2, 2, 3, 3, 3, 3, 3, 3, 3]


def test_abandon_target_has_a_hump_and_turns_negative():
    """README: Ziel „höchstens 1 % Abbrecher“ (Geduld 5 min): Aufschlag 4, 5, 6, 7, 8, 9 (a = 5 bis 200), dann 7 (a = 500), 3 (a = 1000),
    −8 (a = 2000), −41 (a = 5000)."""
    rows = {r["a"]: r["abandon"] for r in E.target_comparison()}
    assert [rows[a] for a in (5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000)] == [4, 5, 6, 7, 8, 9, 7, 3, -8, -41]


def test_scaling_quoted_in_readme():
    """README (Geduld 5 min): √a·P(ab) bei β = 0: 0.346–0.348 für a = 10 bis 5000; β = 1: 0.044 (a = 10) bis 0.064 (a = 5000);
    β = −1: 0.99–1.04; β = 2: 0.006–0.007; P(warten) bei β = 1: 14.5 % (a = 10), 17.5 % (a = 1000 und 5000)."""
    zero = E.scaling_table(0.0, 5)
    assert all(0.344 < r["p_ab_scaled"] < 0.349 for r in zero)
    one = {r["a"]: r for r in E.scaling_table(1.0, 5)}
    assert one[10]["p_ab_scaled"] == pytest.approx(0.044, abs=0.0006) and one[5000]["p_ab_scaled"] == pytest.approx(0.064, abs=0.0006)
    assert one[10]["p_wait"] == pytest.approx(0.145, abs=0.0006) and one[1000]["p_wait"] == pytest.approx(0.175, abs=0.0006)
    assert one[5000]["p_wait"] == pytest.approx(0.175, abs=0.0006)
    neg = E.scaling_table(-1.0, 5)
    assert all(0.985 < r["p_ab_scaled"] < 1.045 for r in neg)
    two = E.scaling_table(2.0, 5)
    assert all(0.0055 < r["p_ab_scaled"] < 0.0075 for r in two)


def test_regimes_quoted_in_readme():
    """README (a = 1000, Geduld 5 min): bei β ≈ −4 (c = 874) warten 100 % und 12.7 % brechen ab; bei β ≈ 0 warten 66 % (1.5 % Abbrecher); bei
    β ≈ 1.7 noch 5 % und bei β ≈ 2.6 0.5 %."""
    curve = E.regime_curve(1000, 5)
    at = lambda b: min(curve, key=lambda p: abs(p[0] - b))
    assert at(-4.0)[1] > 0.999 and at(-4.0)[2] == pytest.approx(0.127, abs=0.003)
    assert at(-0.2)[1] == pytest.approx(0.664, abs=0.02) and at(-0.2)[2] == pytest.approx(0.015, abs=0.002)
    assert at(1.7)[1] == pytest.approx(0.053, abs=0.01) and at(2.6)[1] == pytest.approx(0.005, abs=0.003)


def test_formula_gap_quoted_in_readme():
    """README: Abweichung der exakten Wartewahrscheinlichkeit von der Formel bei β ≈ 1: 3.8 Punkte (a = 10, c = 14), 1.4 (a = 100), 0.4 (a = 1000);
    bei β = 0 warten (Erlang A, a = 1000) genau 57 % bei 1.1 % Abbrechern."""
    gaps = {}
    for a in (10, 100, 1000):
        r = E.gate_report(a, 1.0, 5)
        gaps[a] = 100 * (r["erlang_c"]["p_wait"] - r["hw_p_wait"])
    assert gaps[10] == pytest.approx(3.8, abs=0.06) and gaps[100] == pytest.approx(1.4, abs=0.06) and gaps[1000] == pytest.approx(0.4, abs=0.06)
    zero = {r["a"]: r for r in E.scaling_table(0.0, 5)}[1000]
    assert zero["p_wait"] == pytest.approx(0.567, abs=0.0006) and zero["p_ab_scaled"] / 1000 ** 0.5 == pytest.approx(0.0110, abs=0.0004)


def test_extra_lane_ratio_for_the_three_reference_offers():
    """README: Aufschlag geteilt durch √a bei „höchstens 20 % warten“: 1.10 (a = 100), 1.08 (a = 1000), 1.07 (a = 5000)."""
    rows = {r["a"]: r["wait_prob"] for r in E.target_comparison()}
    assert [round(rows[a] / a ** 0.5, 2) for a in (100, 1000, 5000)] == [1.1, 1.08, 1.07]
