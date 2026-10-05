"""Orakel-Tests (unabhängiger Rechenweg): Erlang C aus der Poisson-Summe über lgamma, Erlang A in Decimal-Arithmetik ohne Logarithmen, die Staffelungen der Tabelle gegen
eine unabhängige Suche, die Ereignissimulation (mit Abbruch und Einschwingzeit) gegen die Kiefer-Wolfowitz-Rekursion mit Abbruch (kein Ereignisheap, nur freie Zeiten je
Spur), und die Auslastung des Live-Laufs eines großen Gates gegen den exakten Wert (der leere Start verfälschte sie)."""

import math
from decimal import Decimal, getcontext

import numpy as np
import pytest

special = pytest.importorskip("scipy.special")

import sqs_constants as C  # noqa: E402
import sqs_evaluation as E  # noqa: E402
import sqs_formulas as F  # noqa: E402
import sqs_simulation as S  # noqa: E402

MU = 1 / 3


def _erlang_c_lgamma(c, a):
    """Erlang C aus der Poisson-Summe: (aᶜ/c!·1/(1 − ρ)) / (Σ_{k<c} aᵏ/k! + aᶜ/c!·1/(1 − ρ)), alles über lgamma in Logarithmen."""
    k = np.arange(c)
    log_head = k * math.log(a) - special.gammaln(k + 1)
    log_tail = c * math.log(a) - special.gammaln(c + 1) - math.log(1 - a / c)
    m = max(log_head.max(), log_tail)
    head, tail = np.exp(log_head - m).sum(), math.exp(log_tail - m)
    return tail / (head + tail)


def _erlang_a_decimal(c, a, theta):
    """Erlang A in Decimal (60 Stellen, keine Logarithmen): Geburts-Todes-Produkte bis die Terme weit unter dem größten liegen. Gibt (P(ab), P(warten), Wq, Auslastung) zurück."""
    getcontext().prec = 60
    lam, mu, th = Decimal(a) * Decimal(MU), Decimal(MU), Decimal(theta)
    terms, n, biggest = [Decimal(1)], 0, Decimal(1)
    while True:
        n += 1
        t = terms[-1] * lam / (Decimal(min(n, c)) * mu + Decimal(max(n - c, 0)) * th)
        terms.append(t)
        biggest = max(biggest, t)
        if n > c and n > a + 10 and t < biggest * Decimal("1e-45"):
            break
    total = sum(terms)
    p = [x / total for x in terms]
    lq = sum(Decimal(k - c) * p[k] for k in range(c, len(p)))
    return (float(th * lq / lam), float(sum(p[c:])), float(lq / lam), float(sum(Decimal(min(k, c)) * p[k] for k in range(len(p))) / c))


@pytest.mark.parametrize("c,a", [(8, 6.5), (110, 100.0), (1032, 1000.0), (2045, 2000.0), (5076, 5000.0)])
def test_erlang_c_against_the_poisson_sum_in_logarithms(c, a):
    assert F.erlang_c(c, a) == pytest.approx(_erlang_c_lgamma(c, a), rel=1e-9)


@pytest.mark.parametrize("c,a,theta", [(7, 6.0, 0.5), (110, 100.0, 0.2), (90, 100.0, 0.2), (874, 1000.0, 0.2), (1956, 2000.0, 0.2), (4788, 5000.0, 0.2)])
def test_erlang_a_against_decimal_arithmetic(c, a, theta):
    m = F.erlang_a_metrics(c, a, MU, theta)
    ref = _erlang_a_decimal(c, a, theta)
    assert (m["p_abandon"], m["p_wait"], m["Wq"], m["utilisation"]) == pytest.approx(ref, rel=1e-7)


def test_staffing_targets_against_an_independent_search():
    """Aufschläge der Tabelle: Wartewahrscheinlichkeit ≤ 20 %, mittlere Wartezeit ≤ 1 min (je mit der lgamma-Rechnung gesucht), Abbruch ≤ 1 % (mit Decimal), a = 100 / 2000."""
    rows = {r["a"]: r for r in E.target_comparison(a_values=(100, 2000))}
    for a in (100, 2000):
        c = int(a) + 1
        while _erlang_c_lgamma(c, a) > 0.2:
            c += 1
        assert rows[a]["wait_prob"] == c - a
        c = int(a) + 1
        while _erlang_c_lgamma(c, a) / (c * MU - a * MU) > 1.0:
            c += 1
        assert rows[a]["mean_wait"] == c - a
        c = max(1, math.ceil(a * 0.99 - 1e-9))
        while _erlang_a_decimal(c, a, 0.2)[0] > 0.01:
            c += 1
        assert rows[a]["abandon"] == c - a


class _Draws:
    """Gibt vorgegebene Werte statt Zufall zurück."""

    def __init__(self, values):
        self.it = iter(values)

    def expovariate(self, rate):
        return next(self.it)


def _kiefer_wolfowitz_with_abandonment(c, gaps, services, patience, warm_time):
    """FIFO mit Abbruch ohne Ereignisheap: Wer bei Ankunft keine freie Spur findet, wartet bis zur frühesten freien Spur, wenn das höchstens seine Geduld ist, sonst bricht er nach
    der Geduld ab und belegt nie eine Spur. Gibt (Abbrecher, Wartende, Summe der Wartezeiten, Zahl ausgewertet, Ende, ∫ beschäftigt im Fenster) zurück."""
    arrivals = np.cumsum(gaps)
    free = np.zeros(c)
    aband = waited = evaluated = 0
    wait_sum = end = 0.0
    served_intervals = []
    for k, t in enumerate(arrivals):
        j = int(np.argmin(free))
        counted = t >= warm_time
        evaluated += counted
        if free[j] <= t:
            free[j] = t + services[k]
            served_intervals.append((t, t + services[k]))
            end = max(end, free[j], t)
            continue
        waited += counted
        w = free[j] - t
        if w <= patience[k]:
            wait_sum += w if counted else 0.0
            served_intervals.append((free[j], free[j] + services[k]))
            free[j] += services[k]
            end = max(end, free[j])
        else:
            aband += counted
            wait_sum += patience[k] if counted else 0.0
            end = max(end, t + patience[k])
    lo, hi = warm_time, arrivals[-1]
    busy = sum(max(0.0, min(b, hi) - max(a, lo)) for a, b in served_intervals)
    return aband, waited, wait_sum, evaluated, max(end, arrivals[-1]), busy


@pytest.mark.parametrize("c,rho,theta,n,warm", [(1, 0.9, 0.5, 200, 0.0), (3, 1.2, 0.2, 300, 20.0), (6, 0.8, 1.0, 400, 10.0), (4, 1.5, 0.05, 250, 0.0)])
def test_event_simulation_against_kiefer_wolfowitz_with_abandonment(c, rho, theta, n, warm):
    rng = np.random.default_rng(c + n)
    lam = rho * c * MU
    gaps, services, patience = rng.exponential(1 / lam, n), rng.exponential(1 / MU, n), rng.exponential(1 / theta, n)
    res = S.simulate(c, lam, MU, theta, n, 0, gap_rng=_Draws(gaps), svc_rng=_Draws(services), pat_rng=_Draws(patience), warm_time=warm)
    aband, waited, wait_sum, evaluated, end, busy = _kiefer_wolfowitz_with_abandonment(c, gaps, services, patience, warm)
    assert (res.n_abandoned, res.n_waited, res.n_customers) == (aband, waited, evaluated)
    assert res.wait_sum == pytest.approx(wait_sum, abs=1e-9) and res.end_time == pytest.approx(end, abs=1e-9)
    assert res.busy_integral == pytest.approx(busy, abs=1e-8) and res.window == pytest.approx(np.cumsum(gaps)[-1] - warm, abs=1e-9)


def test_live_run_of_a_large_gate_reproduces_the_exact_utilisation_and_wait_probability():
    """a = 400, c = 420 (β = 1), Geduld 5 min, 8000 ausgewertete Lkw: der Lauf dauert nur etwa 60 Minuten, der leere Start und das Auslaufen nach der letzten Ankunft drückten die
    gemessene Auslastung vorher auf rund 78 % (exakt 94.9 %); bei a = 1000 und 2000 lagen auch Anteil Wartender und Abbruchquote bei der Hälfte bis einem Drittel des exakten Werts."""
    a, c = 400, 420
    exact = F.erlang_a_metrics(c, a, MU, 0.2)
    runs = [E.simulate_gate(a, c, 5, 8000, seed) for seed in (1, 2, 3)]
    assert float(np.mean([r.utilisation for r in runs])) == pytest.approx(exact["utilisation"], abs=0.03)
    assert float(np.mean([r.share_waiting for r in runs])) == pytest.approx(exact["p_wait"], abs=0.06)
    assert all(abs(r.n_customers - 8000) < 6 * math.sqrt(8000) for r in runs)
    assert C.WARM_MIN == 30.0
