"""Plotly-Abbildungen der Wurzelregel-Demo: Halfin-Whitt-Funktion mit exakten Punkten, Regel gegen exakte Staffelung, Regime über β,
Ziele im Vergleich, Skalierung. Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht zoomen."""

import math

import plotly.graph_objects as go

import sqs_constants as C
import sqs_evaluation as E
import sqs_formulas as F

HW_COLOR = "#f58518"
GOOD_COLOR = "#54a24b"
BAD_COLOR = "#e45756"
A_COLORS = {10: "#9ecae1", 100: "#4c78a8", 1000: "#08306b"}


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height, legend_y=-0.25, top=10):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=top, b=10), legend=dict(orientation="h", y=legend_y),
                      plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_hw_chart(current_beta_eff=None, current_p_wait=None):
    """Wartewahrscheinlichkeit über β: die Halfin-Whitt-Kurve (Formel) und die exakten Erlang-C-Werte für drei Angebote; ein
    Marker zeigt den Wert des gewählten Gates (exakt)."""
    xs = [i / 20 for i in range(1, 81)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[F.hw_p_wait(x) for x in xs], mode="lines", line=dict(color=HW_COLOR, width=3),
                             name="Halfin-Whitt-Formel (a → ∞)"))
    for a in C.HW_CURVE_A:
        pts = E.convergence_points(a)
        fig.add_trace(go.Scatter(x=[b for b, _ in pts], y=[p for _, p in pts], mode="lines+markers" if a <= 100 else "lines",
                                 line=dict(color=A_COLORS[a], width=2), marker=dict(size=5), name=f"exakt, a = {a}",
                                 hovertemplate="β = %{x:.2f}: %{y:.1%}<extra>" + f"a = {a}</extra>"))
    if current_beta_eff is not None and current_beta_eff > 0 and current_p_wait is not None:
        fig.add_trace(go.Scatter(x=[current_beta_eff], y=[current_p_wait], mode="markers",
                                 marker=dict(color=BAD_COLOR, size=13, symbol="diamond", line=dict(color="white", width=1)),
                                 name="gewähltes Gate (exakt)"))
    fig.update_xaxes(title_text="Sicherheitsstufe β = (c − a)/√a", range=[0, 4])
    fig.update_yaxes(title_text="Anteil der Lkw, die warten müssen", tickformat=".0%", range=[0, 1.02])
    return _base(fig, 380, legend_y=-0.3)


def build_rule_chart(table):
    """Aufschlag c − a der exakten Staffelung gegen den der Regel, über dem Angebot (logarithmische Achse)."""
    rows = table["rows"]
    xs = [r["a"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["extra_exact"] for r in rows], mode="markers+lines",
                             line=dict(color=GOOD_COLOR, width=2.5), marker=dict(size=8), name="exakt (Erlang C)"))
    fig.add_trace(go.Scatter(x=xs, y=[r["rule"] - r["a"] for r in rows], mode="lines",
                             line=dict(color=HW_COLOR, width=2, dash="dash"), name=f"Wurzelregel, β = {table['beta']:.2f}"))
    fig.update_xaxes(title_text="Angebot a (log)", type="log", tickmode="array", tickvals=list(C.TABLE_A),
                     ticktext=[str(a) for a in C.TABLE_A])
    fig.update_yaxes(title_text="Aufschlag c − a (Spuren über dem Angebot)", rangemode="tozero")
    return _base(fig, 340)


def build_regime_chart(a, curve, current_beta_eff):
    """Wartewahrscheinlichkeit und Abbruchquote (Erlang A exakt) über β für Angebot a: überlastet, Wurzelregel, überbesetzt."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[b for b, _, _ in curve], y=[w for _, w, _ in curve], mode="lines",
                             line=dict(color="#4c78a8", width=2.5), name="Anteil, der warten muss"))
    fig.add_trace(go.Scatter(x=[b for b, _, _ in curve], y=[p for _, _, p in curve], mode="lines",
                             line=dict(color=BAD_COLOR, width=2.5), name="Abbruchquote"))
    fig.add_vline(x=0, line=dict(color="#888", width=1, dash="dot"), annotation_text="c = a", annotation_position="top")
    fig.add_vline(x=current_beta_eff, line=dict(color=HW_COLOR, width=1.5, dash="dot"))
    fig.update_xaxes(title_text="Sicherheitsstufe β = (c − a)/√a")
    fig.update_yaxes(title_text="Anteil", tickformat=".0%", range=[0, 1.02])
    return _base(fig, 340, top=30)


def build_targets_chart(rows):
    """Aufschlag c − a über dem Angebot für drei Zielarten (Wartewahrscheinlichkeit, mittlere Wartezeit, Abbruchquote)."""
    xs = [r["a"] for r in rows]
    fig = go.Figure()
    for key, label, color, dash in (("wait_prob", "höchstens 20 % müssen warten", "#4c78a8", "solid"),
                                    ("mean_wait", "mittlere Wartezeit höchstens 1 min", GOOD_COLOR, "solid"),
                                    ("abandon", "höchstens 1 % brechen ab (Geduld 5 min)", BAD_COLOR, "solid")):
        fig.add_trace(go.Scatter(x=xs, y=[r[key] for r in rows], mode="lines+markers", line=dict(color=color, width=2.5, dash=dash),
                                 name=label, hovertemplate="a = %{x}: %{y} Spuren über dem Angebot<extra>" + label + "</extra>"))
    fig.add_hline(y=0, line=dict(color="#888", width=1, dash="dot"))
    fig.update_xaxes(title_text="Angebot a (log)", type="log", tickmode="array", tickvals=list(C.TABLE_A),
                     ticktext=[str(a) for a in C.TABLE_A])
    fig.update_yaxes(title_text="Aufschlag c − a (negativ: weniger Spuren als das Angebot)")
    return _base(fig, 380, legend_y=-0.3)


def build_scaling_chart(tables):
    """Skalierte Abbruchquote P(ab)·√a über dem Angebot für feste Sicherheitsstufen (konvergiert bei festem β)."""
    palette = {-1.0: "#e45756", 0.0: "#f58518", 1.0: "#4c78a8", 2.0: "#54a24b"}
    fig = go.Figure()
    for beta, rows in tables.items():
        fig.add_trace(go.Scatter(x=[r["a"] for r in rows], y=[r["p_ab_scaled"] for r in rows], mode="lines+markers",
                                 line=dict(color=palette[beta], width=2.5), name=f"β = {beta:g}",
                                 hovertemplate="a = %{x}: %{y:.3f}<extra>" + f"β = {beta:g}</extra>"))
    fig.update_xaxes(title_text="Angebot a (log)", type="log", tickmode="array", tickvals=list(C.SCALING_A),
                     ticktext=[str(a) for a in C.SCALING_A])
    fig.update_yaxes(title_text="Abbruchquote mal √a", rangemode="tozero")
    return _base(fig, 340)
