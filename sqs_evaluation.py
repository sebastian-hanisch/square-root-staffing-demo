"""Auswertung: Kennzahlen bei c = a + β√a (Erlang C exakt, Halfin-Whitt-Näherung, Erlang A exakt, Simulation), Konvergenz, Regel gegen
exakte Staffelung, Regime über β, Ziele im Vergleich, Skalierung. Alles Formeln außer dem Einzellauf der Simulation; die Tabellen
rechnen für Angebote bis 5000 Lkw-Abfertigungen in Sekunden und werden in der App zwischengespeichert."""

import math

import sqs_constants as C
import sqs_formulas as F
from sqs_simulation import MU, kw_waits, simulate, streams


def theta_of(mean_patience):
    """Abbruchrate θ = 1/mittlere Geduld (je Minute)."""
    return 1.0 / mean_patience


def gate_report(a, beta, mean_patience):
    """Kennzahlen des Gates mit c = ⌈a + β√a⌉ Spuren: Erlang C exakt (nur c > a), Halfin-Whitt-Näherung (nur β_eff > 0),
    Erlang A exakt (immer)."""
    c = F.rule_servers(a, beta)
    be = F.beta_eff(c, a)
    out = {"a": a, "beta": beta, "c": c, "beta_eff": be, "rho": a / c, "overload": c <= a,
           "erlang_a": F.erlang_a_metrics(c, a, MU, theta_of(mean_patience))}
    out["erlang_c"] = None
    if c > a:
        out["erlang_c"] = {"p_wait": F.erlang_c(c, a), "Wq": F.erlang_c_wq(c, a, MU)}
    out["hw_p_wait"] = F.hw_p_wait(be) if be > 0 else None
    return out


def simulate_gate(a, c, mean_patience, n_customers, seed):
    """Ein Simulationslauf des Gates (c Spuren, Angebot a, Geduld mit Mittel `mean_patience`): Rückgabe SimResult."""
    return simulate(c, a * MU, MU, theta_of(mean_patience), n_customers, seed)


def simulate_gate_no_abandon(a, c, n_customers, seed):
    """Simulationslauf ohne Abbruch (nur c > a): Anteil der Wartenden und mittlere Wartezeit aus der Kiefer-Wolfowitz-Rekursion."""
    g, s, _ = streams(seed)
    waits = kw_waits(c, a * MU, MU, n_customers, g, s)
    return {"p_wait": sum(1 for w in waits if w > 0) / n_customers, "Wq": sum(waits) / n_customers}


def convergence_points(a):
    """Exakte Erlang-C-Wartewahrscheinlichkeit für alle Spurzahlen c von a + 1 bis a + 3.5√a bei Angebot a, als Punkte
    (β effektiv, P(warten)): zeigt, wie nah die exakten Werte an der Halfin-Whitt-Kurve liegen."""
    top = math.ceil(a + 3.5 * math.sqrt(a))
    return [(F.beta_eff(c, a), F.erlang_c(c, a)) for c in range(int(a) + 1, top + 1)]


def staffing_table(alpha, a_values=C.TABLE_A):
    """Regel gegen exakte Staffelung für das Ziel „höchstens alpha der Lkw müssen warten“: je Angebot die exakte Spurzahl (Erlang C),
    die der Regel mit β = Halfin-Whitt-Umkehrfunktion(alpha) und die Wartewahrscheinlichkeit bei der Regel."""
    beta = F.hw_beta_for(alpha)
    rows = []
    for a in a_values:
        exact = F.exact_servers_for_wait_prob(a, alpha)
        rule = F.rule_servers(a, beta)
        rows.append({"a": a, "exact": exact, "rule": rule, "diff": rule - exact, "extra_exact": exact - a,
                     "p_wait_rule": F.erlang_c(rule, a) if rule > a else None})
    return {"alpha": alpha, "beta": beta, "rows": rows}


def regime_curve(a, mean_patience):
    """Wartewahrscheinlichkeit und Abbruchquote (Erlang A exakt) über der Sicherheitsstufe für alle Spurzahlen von a − 4√a bis
    a + 3√a: zeigt die drei Regime (überlastet, Wurzelregel, überbesetzt). Liste von (β effektiv, P(warten), P(abbrechen))."""
    lo = max(1, math.floor(a - 4 * math.sqrt(a)))
    hi = math.ceil(a + 3 * math.sqrt(a))
    step = max(1, (hi - lo) // 60)
    theta = theta_of(mean_patience)
    out = []
    for c in range(lo, hi + 1, step):
        m = F.erlang_a_metrics(c, a, MU, theta)
        out.append((F.beta_eff(c, a), m["p_wait"], m["p_abandon"]))
    return out


def target_comparison(a_values=C.TABLE_A):
    """Aufschlag c − a bei drei Zielarten: Wartewahrscheinlichkeit höchstens 20 % (Erlang C), mittlere Wartezeit höchstens 1 min
    (Erlang C), Abbruchquote höchstens 1 % bei Geduld 5 min (Erlang A). Je Angebot ein Dict."""
    theta = theta_of(C.TARGET_PATIENCE)
    rows = []
    for a in a_values:
        rows.append({"a": a,
                     "wait_prob": F.exact_servers_for_wait_prob(a, 0.2) - a,
                     "mean_wait": F.exact_servers_for_mean_wait(a, MU, C.TARGET_WAIT_MIN) - a,
                     "abandon": F.exact_servers_for_abandon(a, MU, theta, C.TARGET_ABANDON) - a})
    return rows


def scaling_table(beta, mean_patience, a_values=C.SCALING_A):
    """Skalierte Kennzahlen bei c = ⌈a + β√a⌉ für wachsendes Angebot (Erlang A): P(warten), P(abbrechen)·√a und Wq·μ·√a. Bei festem
    β konvergieren sie (QED-Skalierung). Liste von Dicts."""
    theta = theta_of(mean_patience)
    rows = []
    for a in a_values:
        c = F.rule_servers(a, beta)
        m = F.erlang_a_metrics(c, a, MU, theta)
        rows.append({"a": a, "c": c, "beta_eff": F.beta_eff(c, a), "p_wait": m["p_wait"],
                     "p_ab_scaled": m["p_abandon"] * math.sqrt(a), "wq_scaled": m["Wq"] * MU * math.sqrt(a)})
    return rows
