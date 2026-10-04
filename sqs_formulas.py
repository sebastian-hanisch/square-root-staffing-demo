"""Formeln zur Wurzel-Personalregel c = a + β·√a (Halfin-Whitt-Regime, QED) und zu den exakten Staffelungen, gegen die sie antritt.

Exakt gerechnet werden Erlang C (c Spuren, unendliche Geduld, nur für c > a) und Erlang A (mit Abwanderung, exponentielle Geduld,
auch für c ≤ a). Die Erlang-B/C/A-Formeln sind aus mmc-queue-demo und erlang-a-demo übernommen (bewusst ohne Import zwischen
Repos). Zeiten in Minuten, Raten je Minute; a = λ/μ ist das Angebot (in Erlang)."""

import math

MAX_STATES = 400_000


# --- Erlang B / C / A (Kopie) -----------------------------------------------------------------------------------------

def erlang_b(c, a):
    """Erlang-B-Verlustwahrscheinlichkeit über die stabile Rekursion B_k = a·B_{k-1}/(k + a·B_{k-1})."""
    b = 1.0
    for k in range(1, c + 1):
        b = a * b / (k + a * b)
    return b


def erlang_c(c, a):
    """Erlang C: Wahrscheinlichkeit zu warten bei unendlicher Geduld, C = B/(1 − ρ(1 − B)); nur für c > a."""
    rho = a / c
    if rho >= 1:
        raise ValueError("c ≤ a: bei unendlicher Geduld keine stationäre Verteilung")
    b = erlang_b(c, a)
    return b / (1 - rho * (1 - b))


def erlang_c_wq(c, a, mu):
    """Mittlere Wartezeit bei Erlang C: Wq = C/(cμ − λ) mit λ = aμ."""
    return erlang_c(c, a) / (c * mu - a * mu)


def erlang_a_metrics(c, a, mu, theta):
    """Erlang A (Geburts-Sterbe-Kette mit Sterberate min(n, c)·μ + max(n − c, 0)·θ, in Logarithmen gerechnet): Abbruchquote
    P(ab) = θ·Lq/λ, Wahrscheinlichkeit zu warten, mittlere Wartezeit aller Lkw Wq = Lq/λ (Abbrecher eingerechnet),
    Auslastung der Spuren. Für θ > 0 für jedes c."""
    lam = a * mu
    logs = [0.0]
    peak = 0.0
    for n in range(1, MAX_STATES):
        death = min(n, c) * mu + max(n - c, 0) * theta
        logs.append(logs[-1] + math.log(lam) - math.log(death))
        peak = max(peak, logs[-1])
        if n > c and logs[-1] < peak - 41.5:
            break
    shift = max(logs)
    w = [math.exp(x - shift) for x in logs]
    total = sum(w)
    p = [x / total for x in w]
    lq = sum((n - c) * p[n] for n in range(c, len(p)))
    p_ab = theta * lq / lam
    busy = sum(min(n, c) * p[n] for n in range(len(p)))
    return {"c": c, "p_abandon": p_ab, "p_wait": sum(p[c:]), "Wq": lq / lam, "utilisation": busy / c}


# --- Wurzel-Personalregel und Halfin-Whitt-Funktion -------------------------------------------------------------------

def phi(x):
    """Dichte der Standardnormalverteilung."""
    return math.exp(-x * x / 2.0) / math.sqrt(2.0 * math.pi)


def big_phi(x):
    """Verteilungsfunktion der Standardnormalverteilung (über die Fehlerfunktion)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def hw_p_wait(beta):
    """Halfin-Whitt-Grenzwert der Wartewahrscheinlichkeit bei c = a + β√a (M/M/c, a → ∞): [1 + β·Φ(β)/φ(β)]^-1, für β > 0."""
    return 1.0 / (1.0 + beta * big_phi(beta) / phi(beta))


def hw_beta_for(alpha):
    """Die Sicherheitsstufe β, bei der der Halfin-Whitt-Grenzwert der Wartewahrscheinlichkeit gleich alpha ist (Bisektion; die
    Funktion fällt von 1 bei β = 0 auf 0)."""
    if not 0 < alpha < 1:
        raise ValueError("alpha muss in (0, 1) liegen")
    lo, hi = 0.0, 12.0
    for _ in range(100):
        mid = (lo + hi) / 2.0
        if hw_p_wait(mid) > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def rule_servers(a, beta):
    """Wurzel-Personalregel: c = ⌈a + β·√a⌉ (mindestens 1). β darf negativ sein (dann weniger Spuren als das Angebot)."""
    return max(1, math.ceil(a + beta * math.sqrt(a) - 1e-9))


def beta_eff(c, a):
    """Sicherheitsstufe, die eine ganzzahlige Spurzahl c bei Angebot a verwirklicht: (c − a)/√a."""
    return (c - a) / math.sqrt(a)


def exact_servers_for_wait_prob(a, alpha):
    """Kleinste Spurzahl c > a mit Erlang-C-Wartewahrscheinlichkeit ≤ alpha."""
    c = int(a) + 1
    while erlang_c(c, a) > alpha:
        c += 1
    return c


def exact_servers_for_mean_wait(a, mu, target_wq):
    """Kleinste Spurzahl c > a mit mittlerer Erlang-C-Wartezeit ≤ target_wq (Minuten)."""
    c = int(a) + 1
    while erlang_c_wq(c, a, mu) > target_wq:
        c += 1
    return c


def exact_servers_for_abandon(a, mu, theta, target):
    """Kleinste Spurzahl c mit Erlang-A-Abbruchquote ≤ target. Der Durchsatz λ(1 − P(ab)) ≤ cμ verlangt c ≥ a(1 − target); das ist
    der Startwert der Suche (c darf unter a liegen: Überlast)."""
    c = max(1, math.ceil(a * (1 - target) - 1e-9))
    while erlang_a_metrics(c, a, mu, theta)["p_abandon"] > target:
        c += 1
    return c
