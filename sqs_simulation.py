"""Simulation einer Schlange mit c Spuren, einer gemeinsamen FIFO-Schlange und (optional) ungeduldigen Kunden mit exponentieller
Geduld (M/M/c+M), dazu die Kiefer-Wolfowitz-Rekursion für den Fall ohne Abbruch (M/M/c). Kopie der benötigten Einheiten aus
mmc-queue-demo und erlang-a-demo (bewusst ohne Import zwischen Repos), mit nur EINER Geduld-Verteilung (exponentiell).

Aufbau nach Einheiten (je Ereignistyp ein Handler, kein versteckter Zustand): `handle_arrival`, `handle_departure`,
`handle_abandon`, `simulate` (Ereignisschleife), `kw_waits` (Wartezeiten ohne Ereignisliste). Zufall nur über übergebene
`SplitMix64`-Generatoren mit getrennten Strömen für Ankünfte, Bedienzeiten und Geduld."""

import heapq
import math
from collections import deque
from dataclasses import dataclass

_MASK = (1 << 64) - 1
ARRIVAL, DEPARTURE, ABANDON = 0, 1, 2
MEAN_SERVICE_MIN = 3.0          # mittlere Abfertigungsdauer je Spur (Minuten)
MU = 1.0 / MEAN_SERVICE_MIN


class SplitMix64:
    """Kleiner, gut gemischter 64-Bit-Zufallsgenerator (Vigna); reine Ganzzahl-Arithmetik."""

    def __init__(self, seed):
        self.state = seed & _MASK

    def next(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & _MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK
        return z ^ (z >> 31)

    def uniform(self):
        """Gleichverteilt auf [0, 1) mit 53 Bit."""
        return (self.next() >> 11) * (1.0 / (1 << 53))

    def expovariate(self, rate):
        """Exponentiell mit Mittel 1/rate (Inversion; 1 − u liegt in (0, 1], der Logarithmus ist endlich)."""
        return -math.log(1.0 - self.uniform()) / rate


def streams(seed):
    """Die drei Zufallsströme eines Laufs: Ankünfte, Bedienzeiten, Geduld."""
    return SplitMix64(seed), SplitMix64(seed + 7_777_777), SplitMix64(seed + 15_555_555)


@dataclass
class SimResult:
    c: int
    n_customers: int
    end_time: float
    n_abandoned: int
    n_waited: int                    # Lkw, die nicht sofort bedient wurden
    wait_sum: float                  # Summe der Wartezeiten ALLER Lkw (Abbrecher bis zum Abbruch)
    busy_integral: float             # ∫ (Zahl beschäftigter Spuren) dt

    @property
    def abandon_rate(self):
        return self.n_abandoned / self.n_customers

    @property
    def share_waiting(self):
        return self.n_waited / self.n_customers

    @property
    def mean_wait_all(self):
        return self.wait_sum / self.n_customers

    @property
    def utilisation(self):
        return self.busy_integral / (self.c * self.end_time)


class _State:
    __slots__ = ("c", "t", "queue", "busy", "events", "seq", "n_customers", "lam", "mu", "busy_integral", "status",
                 "service_time", "arrival_time", "patience", "n_abandoned", "n_waited", "wait_sum")


def _advance_clock(s, t_new):
    """Zeit auf t_new vorstellen und das Integral der beschäftigten Spuren fortschreiben."""
    s.busy_integral += s.busy * (t_new - s.t)
    s.t = t_new


def _start_service(s, cid):
    """Kunde cid beginnt die Bedienung jetzt: Wartezeit festhalten, Abgang einplanen."""
    s.status[cid] = "served"
    s.wait_sum += s.t - s.arrival_time[cid]
    s.busy += 1
    s.seq += 1
    heapq.heappush(s.events, (s.t + s.service_time[cid], s.seq, DEPARTURE, cid))


def handle_arrival(s, cid, gap_rng, svc_rng, pat_rng, theta):
    """Ein Lkw kommt an: Bedienzeit und Geduld werden gezogen (eigene Ströme, Geduld nur bei θ > 0), die nächste Ankunft
    eingeplant. Freie Spur: sofort bedient; sonst Schlange mit Abbruch-Termin."""
    s.arrival_time[cid] = s.t
    s.service_time[cid] = svc_rng.expovariate(s.mu)
    s.patience[cid] = pat_rng.expovariate(theta) if theta > 0 else math.inf
    if s.busy < s.c:
        _start_service(s, cid)
    else:
        s.status[cid] = "waiting"
        s.n_waited += 1
        s.queue.append(cid)
        if s.patience[cid] != math.inf:
            s.seq += 1
            heapq.heappush(s.events, (s.t + s.patience[cid], s.seq, ABANDON, cid))
    if cid + 1 < s.n_customers:
        s.seq += 1
        heapq.heappush(s.events, (s.t + gap_rng.expovariate(s.lam), s.seq, ARRIVAL, cid + 1))


def handle_departure(s, cid):
    """Ein Lkw ist abgefertigt und gibt seine Spur frei; der nächste Wartende (FIFO) rückt nach, wer schon abgebrochen hat, wird
    übersprungen."""
    s.busy -= 1
    while s.queue:
        nxt = s.queue.popleft()
        if s.status[nxt] == "waiting":
            _start_service(s, nxt)
            break


def handle_abandon(s, cid):
    """Der Abbruch-Termin eines Lkw ist erreicht: war er noch in der Schlange, verlässt er sie ohne Bedienung."""
    s.status[cid] = "gone"
    s.n_abandoned += 1
    s.wait_sum += s.t - s.arrival_time[cid]


def simulate(c, lam, mu, theta, n_customers, seed, gap_rng=None, svc_rng=None, pat_rng=None):
    """Simuliert `n_customers` Ankünfte (Rate lam) an c Spuren (Bedienrate mu je Spur) mit Abbruchrate theta (0 = unendliche
    Geduld) und läuft, bis alle bedient sind oder abgebrochen haben. Start leer; `*_rng` ersetzen die Ströme aus `seed`."""
    if gap_rng is None or svc_rng is None or pat_rng is None:
        gap_rng, svc_rng, pat_rng = streams(seed)
    s = _State()
    s.c, s.t, s.queue, s.busy = c, 0.0, deque(), 0
    s.events, s.seq, s.n_customers, s.lam, s.mu = [], 0, n_customers, lam, mu
    s.busy_integral = 0.0
    s.status = [""] * n_customers
    s.service_time, s.arrival_time, s.patience = [0.0] * n_customers, [0.0] * n_customers, [0.0] * n_customers
    s.n_abandoned, s.n_waited, s.wait_sum = 0, 0, 0.0
    heapq.heappush(s.events, (gap_rng.expovariate(lam), 0, ARRIVAL, 0))
    while s.events:
        t, _, ev, cid = heapq.heappop(s.events)
        if ev == ABANDON and s.status[cid] != "waiting":
            continue            # Termin eines Lkw, der schon in Bedienung ist: Uhr bleibt unberührt
        _advance_clock(s, t)
        if ev == ARRIVAL:
            handle_arrival(s, cid, gap_rng, svc_rng, pat_rng, theta)
        elif ev == DEPARTURE:
            handle_departure(s, cid)
        else:
            handle_abandon(s, cid)
    return SimResult(c, n_customers, s.t, s.n_abandoned, s.n_waited, s.wait_sum, s.busy_integral)


def kw_waits(c, lam, mu, n_customers, gap_rng, svc_rng):
    """Wartezeiten ohne Abbruch per Kiefer-Wolfowitz-Rekursion (FIFO, c Server): ein ankommender Lkw nimmt die Spur, die am
    frühesten frei wird; Wartezeit = max(0, früheste Freizeit − Ankunftszeit)."""
    free = [0.0] * c
    heapq.heapify(free)
    t, out = 0.0, [0.0] * n_customers
    for k in range(n_customers):
        t += gap_rng.expovariate(lam)
        earliest = heapq.heappop(free)
        start = t if t > earliest else earliest
        out[k] = start - t
        heapq.heappush(free, start + svc_rng.expovariate(mu))
    return out
