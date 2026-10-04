"""Konstanten der Wurzelregel-Demo: Regler, Voreinstellungen, Tabellen-Achsen. Zeiten in Minuten."""


def fmt_int(n):
    """Ganzzahl mit Punkt als Tausendertrenner (10000 -> 10.000)."""
    return f"{n:,}".replace(",", ".")


def fmt_pct(x, digits=0):
    """Anteil als Prozent mit Leerzeichen (0.086 -> "9 %", mit digits=1 "8.6 %")."""
    return f"{x:.{digits}%}".replace("%", " %")


A_OPTIONS = (5, 10, 20, 50, 100, 200, 500, 1000, 2000)       # Angebot a = λ/μ (Erlang)
DEFAULT_A = 100
BETA_MIN, BETA_MAX, BETA_STEP, DEFAULT_BETA = -2.0, 3.0, 0.25, 1.0
PATIENCE_MIN, PATIENCE_MAX, DEFAULT_PATIENCE = 1, 30, 5      # mittlere Geduld (Minuten) für Erlang A
N_OPTIONS = (5000, 20000, 50000)                              # Lkw je Simulationslauf
DEFAULT_N = 20000
SEED_MAX = 999999
DEFAULT_SEED = 35

# Tabellen (nur Formeln, werden live gerechnet und zwischengespeichert)
TABLE_A = (5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000)
TABLE_ALPHAS = (0.5, 0.2)                 # Ziel-Wartewahrscheinlichkeit
HW_CURVE_A = (10, 100, 1000)              # Angebote der Konvergenz-Kurven
TARGET_WAIT_MIN = 1.0                     # absolutes Ziel: mittlere Wartezeit höchstens 1 min
TARGET_ABANDON = 0.01                     # Ziel: Abbruchquote höchstens 1 %
TARGET_PATIENCE = 5                       # Geduld für das Abbruch-Ziel
SCALING_BETAS = (-1.0, 0.0, 1.0, 2.0)
SCALING_A = (10, 50, 100, 500, 1000, 5000)

PRESET_ORDER = ("Normalfall (a = 100, β = 1)", "Kleines Gate (a = 10)", "Großes Gate (a = 1000)", "Knapp besetzt (β = −1)")


def _preset(a=DEFAULT_A, beta=DEFAULT_BETA, patience=DEFAULT_PATIENCE, n=DEFAULT_N):
    return {"a": a, "beta": beta, "patience": patience, "n": n, "seed": DEFAULT_SEED}


PRESETS = {
    "Normalfall (a = 100, β = 1)": _preset(),
    "Kleines Gate (a = 10)": _preset(a=10),
    "Großes Gate (a = 1000)": _preset(a=1000),
    "Knapp besetzt (β = −1)": _preset(beta=-1.0),
}
# Formelwerte bei 3 min Abfertigung je Spur, Geduld 5 min (exakt; tests/test_claims.py rechnet sie nach)
PRESET_HELP = {
    "Normalfall (a = 100, β = 1)": "Angebot 100 und β = 1: 110 Spuren. Ohne Abbruch müssen exakt 23.7 % der Lkw warten (Halfin-Whitt-Formel: 22.3 %); mit Geduld 5 min brechen 0.7 % ab.",
    "Kleines Gate (a = 10)": "Angebot 10 und β = 1 ergibt aufgerundet 14 Spuren (β effektiv 1.27). Ohne Abbruch müssen exakt 17.4 % warten, die Halfin-Whitt-Formel sagt 13.6 %: bei so kleinem Gate liegt sie etwas daneben.",
    "Großes Gate (a = 1000)": "Angebot 1000 und β = 1: 1032 Spuren, nur 3 % mehr als das Angebot, und trotzdem müssen ohne Abbruch nur 22.3 % warten (Formel 21.9 %); mit Geduld 5 min brechen 0.2 % ab.",
    "Knapp besetzt (β = −1)": "Angebot 100, aber nur 90 Spuren (Überlast, ρ = 111 %): Ohne Abbruch gäbe es keine stationäre Verteilung, mit Abbruch gibt es sie: 91.9 % müssen warten, 10.4 % brechen ab, die Spuren sind zu 99.5 % ausgelastet.",
}
