"""Simulation: Generator, Vier-Lkw-Instanz mit Abbruch von Hand, verfallener Abbruch-Termin, Ereignissimulation gegen
Kiefer-Wolfowitz (ohne Abbruch) und gegen die Erlang-A-Formel."""

import pytest

import sqs_formulas as F
import sqs_simulation as S
from conftest import ScriptedRng


def test_splitmix64_matches_the_reference_sequence():
    rng = S.SplitMix64(0)
    assert [rng.next() for _ in range(3)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4, 0x06C45D188009454F]


def test_expovariate_has_the_right_mean_and_streams_are_distinct():
    rng = S.SplitMix64(5)
    ex = [rng.expovariate(0.5) for _ in range(20000)]
    assert min(ex) > 0 and sum(ex) / len(ex) == pytest.approx(2.0, rel=0.05)
    g, s, p = S.streams(7)
    assert len({g.state, s.state, p.state}) == 3


def test_mini_instance_with_abandonment_by_hand(mini_streams):
    """Von Hand (siehe conftest): 2 Lkw warten (Lkw 2 und 3), einer bricht nach 1.0 ab; Wartezeiten aller Lkw 0 + 1 + 2 + 0 = 3;
    Ende bei 7.5; beschäftigte Spuren ∫ = 3 + 1 + 2 = 6, Auslastung 0.8."""
    gap, svc, pat = mini_streams
    r = S.simulate(1, 1.0, 1.0, 0.2, 4, seed=0, gap_rng=gap, svc_rng=svc, pat_rng=pat)
    assert r.n_abandoned == 1 and r.n_waited == 2 and r.wait_sum == pytest.approx(3.0)
    assert r.end_time == pytest.approx(7.5) and r.busy_integral == pytest.approx(6.0) and r.utilisation == pytest.approx(0.8)
    assert r.abandon_rate == pytest.approx(0.25) and r.share_waiting == pytest.approx(0.5) and r.mean_wait_all == pytest.approx(0.75)


def test_a_stale_abandon_deadline_after_the_last_departure_does_not_move_the_clock(mini_streams):
    """Geduld des bedienten Lkw 3 = 20: sein Abbruch-Termin bei 22 liegt nach dem letzten Abgang (7.5) und darf Ende und Auslastung
    nicht verändern."""
    gap, svc, _ = mini_streams
    pat = ScriptedRng(exp_values=[99, 1.0, 20.0, 99])
    r = S.simulate(1, 1.0, 1.0, 0.2, 4, seed=0, gap_rng=gap, svc_rng=svc, pat_rng=pat)
    assert r.end_time == pytest.approx(7.5) and r.utilisation == pytest.approx(0.8) and r.n_abandoned == 1


def test_handle_abandon_by_hand():
    s = S._State()
    s.status, s.t, s.arrival_time, s.n_abandoned, s.wait_sum = ["waiting", "waiting"], 5.0, [1.0, 2.5], 0, 0.0
    S.handle_abandon(s, 1)
    assert s.status == ["waiting", "gone"] and s.n_abandoned == 1 and s.wait_sum == pytest.approx(2.5)


def test_without_patience_the_event_simulation_equals_kiefer_wolfowitz():
    """θ = 0 (unendliche Geduld): Ereignissimulation und Kiefer-Wolfowitz-Rekursion liefern aus denselben Strömen dieselbe mittlere
    Wartezeit und denselben Anteil Wartender."""
    a, c, n = 8.0, 10, 20000
    sim = S.simulate(c, a * S.MU, S.MU, 0.0, n, 3)
    g, s, _ = S.streams(3)
    waits = S.kw_waits(c, a * S.MU, S.MU, n, g, s)
    assert sim.n_abandoned == 0
    assert sim.mean_wait_all == pytest.approx(sum(waits) / n, rel=1e-9)
    assert sim.share_waiting == pytest.approx(sum(1 for w in waits if w > 0) / n)


def test_same_seed_same_result_and_a_different_seed_differs():
    a, b, other = S.simulate(5, 4.0 * S.MU, S.MU, 0.2, 800, 11), S.simulate(5, 4.0 * S.MU, S.MU, 0.2, 800, 11), S.simulate(5, 4.0 * S.MU, S.MU, 0.2, 800, 12)
    assert (a.wait_sum, a.n_abandoned) == (b.wait_sum, b.n_abandoned) and a.wait_sum != other.wait_sum


def test_long_run_matches_erlang_a():
    """a = 50, c = 57 (β ≈ 1), Geduld 5 min: 200 000 Lkw liegen nahe an Abbruchquote, Wartezeit und Wartewahrscheinlichkeit."""
    a, c = 50, 57
    sim = S.simulate(c, a * S.MU, S.MU, 0.2, 200_000, 1)
    f = F.erlang_a_metrics(c, a, S.MU, 0.2)
    assert sim.abandon_rate == pytest.approx(f["p_abandon"], abs=0.003)
    assert sim.share_waiting == pytest.approx(f["p_wait"], abs=0.015)
    assert sim.mean_wait_all == pytest.approx(f["Wq"], rel=0.15)
    assert sim.utilisation == pytest.approx(f["utilisation"], abs=0.01)


def test_overload_run_matches_erlang_a():
    """a = 100, c = 90 (ρ = 111 %): es gibt dank Abbruch ein Gleichgewicht, die Simulation trifft die Formel."""
    sim = S.simulate(90, 100 * S.MU, S.MU, 0.2, 150_000, 2)
    assert sim.abandon_rate == pytest.approx(F.erlang_a_metrics(90, 100, S.MU, 0.2)["p_abandon"], abs=0.008)


def test_run_without_abandonment_matches_erlang_c():
    a, c = 100, 110
    g, s, _ = S.streams(4)
    waits = S.kw_waits(c, a * S.MU, S.MU, 200_000, g, s)
    assert sum(1 for w in waits if w > 0) / len(waits) == pytest.approx(F.erlang_c(c, a), abs=0.02)
    assert sum(waits) / len(waits) == pytest.approx(F.erlang_c_wq(c, a, S.MU), rel=0.15)
