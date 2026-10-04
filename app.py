"""Wurzel-Personalregel - wie viele Spuren braucht ein großes Gate? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Fünftes Stück der Konzepte-Linie "Warteschlangentheorie und Simulation": Bei Angebot a (Erlang) reicht ein Puffer von β·√a Spuren
über dem Angebot (Halfin-Whitt-Regime, QED). Die Demo vergleicht die Regel c = a + β√a mit der exakten Erlang-C- und Erlang-A-
Rechnung, zeigt die Konvergenz der Halfin-Whitt-Formel, die drei Regime und warum ein absolutes Wartezeit-Ziel einen ganz
anderen Aufschlag verlangt. Siehe README für die Einordnung in die Linie.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import sqs_constants as C
import sqs_formulas as F
from sqs_evaluation import (gate_report, regime_curve, scaling_table, simulate_gate, simulate_gate_no_abandon,
                            staffing_table, target_comparison)
from sqs_presets import (apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed,
                         sync_query_params)
from sqs_visualization import (build_hw_chart, build_regime_chart, build_rule_chart, build_scaling_chart,
                               build_targets_chart)

st.set_page_config(page_title="Wurzel-Personalregel – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _report(a, beta, patience):
    return gate_report(a, beta, patience)


@st.cache_data(show_spinner=False)
def _sim(a, c, patience, n, seed):
    return simulate_gate(a, c, patience, n, seed)


@st.cache_data(show_spinner=False)
def _sim_c(a, c, n, seed):
    return simulate_gate_no_abandon(a, c, n, seed)


@st.cache_data(show_spinner=False)
def _table(alpha):
    return staffing_table(alpha)


@st.cache_data(show_spinner=False)
def _regime(a, patience):
    return regime_curve(a, patience)


@st.cache_data(show_spinner=False)
def _targets():
    return target_comparison()


@st.cache_data(show_spinner=False)
def _scaling(patience):
    return {b: scaling_table(b, patience) for b in C.SCALING_BETAS}


def _min(x):
    return f"{x:.2f} min" if x < 10 else f"{x:.1f} min"


st.title("🧮 Wurzel-Personalregel: wie viele Spuren braucht ein großes Gate?")
st.markdown(
    """
Stück 3 zeigte, dass große Gates bei gleichem Service heißer laufen dürfen. Die Regel dahinter heißt
**Wurzel-Personalregel**: Bei einem **Angebot** a (so viele Spuren sind im Mittel beschäftigt) braucht man
**c = a + β·√a** Spuren. Der Sicherheitspuffer β·√a wächst nur mit der Wurzel des Angebots, und die **Sicherheitsstufe β**
legt fest, wie viele Lkw warten müssen. Halfin und Whitt (1981) zeigten: Für wachsendes a und festes β nähert sich der Anteil der
Wartenden einer **festen Kurve** (**QED-Regime**: Qualität und Effizienz zugleich). Hier wird geprüft, **wie gut die Regel
gegen die exakte Rechnung ist**, schon bei kleinen Gates, **wo sie nicht gilt** (andere Zielarten, Überlast) und wie sich das
mit Abwanderung ändert.
"""
)
st.caption(
    "Fünftes Stück der Linie „Warteschlangentheorie und Simulation“, aufbauend auf "
    "[erlang-a-demo](https://sebastianhanisch-erlang-a-demo.streamlit.app/) (Abwanderung), "
    "[mmc-queue-demo](https://sebastianhanisch-mmc-queue-demo.streamlit.app/) (Erlang C) und "
    "[mm1-queue-demo](https://sebastianhanisch-mm1-queue-demo.streamlit.app/). Jedes Folgestück hebt eine der Annahmen unter "
    "„Wo die Annahmen enden“ auf."
)

with st.expander("So funktioniert die Wurzelregel", expanded=True):
    st.markdown(
        """
- **Angebot a = λ/μ:** so viele Spuren sind im Mittel gleichzeitig mit Abfertigen beschäftigt. Mit c = a Spuren wäre jede Spur
  im Mittel ausgelastet (ρ = 100 %), die Schlange wüchse ohne Grenze (ohne Abbruch).
- **Puffer β·√a:** schon wenige Spuren mehr als a halten die Schlange kurz. **Ein β von 1 bis 2** bedeutet, dass nur noch jeder
  vierte bis zehnte Lkw warten muss, bei Auslastungen von 90 % und mehr.
- **Halfin-Whitt-Funktion:** Wächst a bei festem β, geht die Wartewahrscheinlichkeit gegen
  **1/(1 + β·Φ(β)/φ(β))** (Φ, φ: Verteilungsfunktion und Dichte der Normalverteilung).
- **Drei Regime:** viel weniger Spuren als a (**Effizienz zuerst**: fast alle warten), um a plus β√a (**QED**), viel mehr
  (**Qualität zuerst**: fast niemand wartet, aber viele Spuren stehen still).
- **Hier gemessen:** exakte Erlang-C-/Erlang-A-Rechnung gegen die Regel und die Formel; die Simulation prüft das gewählte Gate.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_cols = st.columns(len(C.PRESET_ORDER))
for i, name in enumerate(C.PRESET_ORDER):
    with preset_cols[i]:
        st.button(name, key=f"preset_{name}", width="stretch", on_click=apply_preset, args=(name,),
                  help=C.PRESET_HELP[name])

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    a = st.select_slider("Angebot a (Erlang)", options=C.A_OPTIONS, key="a_select",
                         help="Ankunftsrate geteilt durch die Abfertigungsrate einer Spur: so viele Spuren sind im Mittel "
                              "gleichzeitig beschäftigt. Die mittlere Abfertigungsdauer je Spur ist fest 3 min.")
    beta = st.slider("Sicherheitsstufe β", *bounds("beta_slider"), step=C.BETA_STEP, key="beta_slider", format="%.2f",
                     help="Die Regel c = ⌈a + β·√a⌉. Negativ: weniger Spuren als das Angebot (Überlast, nur mit Abbruch "
                          "ein Gleichgewicht).")
    patience = st.slider("Mittlere Geduld (Minuten)", *bounds("patience_slider"), key="patience_slider",
                         help="Für die Erlang-A-Kennzahlen: nach so langer Wartezeit bricht ein Lkw im Mittel ab.")
    n = st.select_slider("Simulierte Lkw je Lauf", options=C.N_OPTIONS, key="n_select",
                         help="Länge des Simulationslaufs für das gewählte Gate.")
    seed = st.number_input("Zufalls-Seed", min_value=bounds("seed_input")[0], max_value=bounds("seed_input")[1],
                           step=1, key="seed_input", help="Bestimmt alle Zufallszahlen des Laufs.")
    st.button("🎲 Neuen Lauf würfeln", on_click=randomize_seed)

a, patience, n, seed = int(a), int(patience), int(n), int(seed)
beta = float(beta)
sync_query_params({"a_select": a, "beta_slider": beta, "patience_slider": patience, "n_select": n, "seed_input": seed})

report = _report(a, beta, patience)
c, be = report["c"], report["beta_eff"]
ea = report["erlang_a"]

with st.spinner("Simuliere das Gate …"):
    sim = _sim(a, c, patience, n, seed)
    sim_c = _sim_c(a, c, n, seed) if not report["overload"] else None

st.markdown("---")
st.markdown("## 🧮 Das Gate bei c = a + β·√a")
st.caption(
    f"Angebot a = {a}, β = {beta:.2f}: c = ⌈{a} + {beta:.2f}·√{a}⌉ = **{c} Spuren** (β effektiv {be:.2f}, Auslastung je Spur "
    f"{C.fmt_pct(report['rho'], 1)}), 3 min Abfertigung, mittlere Geduld {patience} min, {C.fmt_int(n)} simulierte Lkw."
)
r1 = st.columns(3)
r1[0].metric("Spuren c (Regel)", c)
r1[1].metric("β effektiv = (c − a)/√a", f"{be:.2f}")
r1[2].metric("Auslastung je Spur ρ = a/c", C.fmt_pct(report["rho"], 1))
r2 = st.columns(3)
ec = report["erlang_c"]
r2[0].metric("Anteil, der warten muss: Erlang C (exakt)", C.fmt_pct(ec["p_wait"], 1) if ec else "gilt nicht (c ≤ a)")
r2[1].metric("… Halfin-Whitt-Formel", C.fmt_pct(report["hw_p_wait"], 1) if report["hw_p_wait"] is not None else "nur für β > 0",
             delta=f"{100 * (report['hw_p_wait'] - ec['p_wait']):+.1f} Prozentpunkte gegen exakt" if (ec and report["hw_p_wait"] is not None) else None,
             delta_color="off")
r2[2].metric("… mit Abbruch: Erlang A (exakt)", C.fmt_pct(ea["p_wait"], 1))
r3 = st.columns(3)
r3[0].metric("Abbruchquote: Erlang A (exakt)", C.fmt_pct(ea["p_abandon"], 1))
r3[1].metric("Abbruchquote (simuliert)", C.fmt_pct(sim.abandon_rate, 1),
             delta=f"{100 * (sim.abandon_rate - ea['p_abandon']):+.1f} Prozentpunkte gegen Formel", delta_color="off")
r3[2].metric("Wartezeit aller Lkw: Erlang A (exakt)", _min(ea["Wq"]))
sim_line = (f"Simulation mit Abbruch: {C.fmt_pct(sim.share_waiting, 1)} müssen warten (Formel {C.fmt_pct(ea['p_wait'], 1)}), "
            f"Wartezeit aller Lkw {_min(sim.mean_wait_all)} (Formel {_min(ea['Wq'])}), Auslastung {C.fmt_pct(sim.utilisation, 1)} "
            f"(Formel {C.fmt_pct(ea['utilisation'], 1)}).")
if sim_c is not None:
    sim_line += (f" Ohne Abbruch (Erlang C): {C.fmt_pct(sim_c['p_wait'], 1)} müssen warten (exakt {C.fmt_pct(ec['p_wait'], 1)}), "
                 f"mittlere Wartezeit {_min(sim_c['Wq'])} (exakt {_min(ec['Wq'])}).")
st.caption(sim_line + " Ein einzelner Lauf streut um die Formel (siehe Stück 1 bis 4).")
if report["overload"]:
    st.warning(
        f"**c ≤ a: Überlast.** Ohne Abbruch (Erlang C) gäbe es hier keine stationäre Verteilung; die Erlang-A-Werte gelten, weil "
        f"Abbrecher die Schlange begrenzen ({C.fmt_pct(ea['p_abandon'], 1)} brechen ab)."
    )

st.markdown("### Die Halfin-Whitt-Funktion")
st.plotly_chart(build_hw_chart(be, ec["p_wait"] if ec else None), width="stretch", key=f"hw_{be:.3f}")
st.caption(
    "Orange: die Halfin-Whitt-Kurve. Blau: die exakten Erlang-C-Werte für Angebote 10, 100 und 1000 (Punkte: ganze Spurzahlen). "
    "Je größer das Angebot, desto näher liegen die exakten Werte an der Kurve."
)

st.markdown("---")
st.subheader("📐 Regel gegen exakte Staffelung")
alpha = st.select_slider("Ziel: höchstens so viele Lkw müssen warten", options=C.TABLE_ALPHAS, value=0.2,
                         format_func=lambda v: f"{v:.0%}", key="table_alpha")
table = _table(alpha)
st.plotly_chart(build_rule_chart(table), width="stretch", key=f"rule_{alpha}")
header = "| Angebot a | exakt (Erlang C) | Wurzelregel | Differenz | Wartewahrscheinlichkeit bei der Regel |\n|---|---|---|---|---|\n"
body = "".join(
    f"| {r['a']} | {r['exact']} | {r['rule']} | {r['diff']:+d} | {C.fmt_pct(r['p_wait_rule'], 1)} |\n" for r in table["rows"])
st.markdown(header + body)
exact_hits = sum(1 for r in table["rows"] if r["diff"] == 0)
st.info(
    f"Mit β = {table['beta']:.2f} (Halfin-Whitt-Umkehrfunktion für {alpha:.0%}) trifft die Regel die exakte Spurzahl in "
    f"**{exact_hits} von {len(table['rows'])}** Angeboten; sonst liegt sie "
    f"{max(abs(r['diff']) for r in table['rows'])} Spur(en) daneben. Das gilt auch für sehr kleine Gates."
)

st.markdown("---")
st.subheader("🔬 Drei Regime")
st.markdown(f"Wartewahrscheinlichkeit und Abbruchquote (Erlang A, Geduld {patience} min) über der Sicherheitsstufe, für Angebot {a}.")
curve = _regime(a, patience)
st.plotly_chart(build_regime_chart(a, curve, be), width="stretch", key=f"regime_{a}_{patience}_{be:.3f}")


def _at(target_beta):
    return min(curve, key=lambda p: abs(p[0] - target_beta))


lo_pt, mid_pt, hi_pt = _at(-3.0), _at(0.0), _at(2.5)
st.info(
    f"Bei Angebot {a}: bei β ≈ {lo_pt[0]:.1f} (c = a − {abs(lo_pt[0]) * a ** 0.5:.0f}) müssen {C.fmt_pct(lo_pt[1])} warten und "
    f"{C.fmt_pct(lo_pt[2], 1)} brechen ab (**Effizienz zuerst**); bei β ≈ {mid_pt[0]:.1f} (c = a) {C.fmt_pct(mid_pt[1])} und "
    f"{C.fmt_pct(mid_pt[2], 1)}; bei β ≈ {hi_pt[0]:.1f} nur noch {C.fmt_pct(hi_pt[1])} und {C.fmt_pct(hi_pt[2], 1)} "
    "(**Qualität zuerst**). Die Wurzelregel liegt dazwischen: wenige Spuren mehr, spürbar weniger Wartende."
)

st.markdown("---")
st.subheader("🔬 Welches Ziel, welcher Aufschlag?")
st.markdown(
    "Der Aufschlag c − a hängt davon ab, **was** man erreichen will: ein fester **Anteil Wartender** verlangt einen Aufschlag, der "
    "wie √a wächst. Ein **absolutes Wartezeit-Ziel** in Minuten verlangt dagegen bei großen Gates **fast nichts** mehr, und bei einem "
    "Abbruch-Ziel kann der Aufschlag sogar **negativ** werden."
)
target_rows = _targets()
st.plotly_chart(build_targets_chart(target_rows), width="stretch", key="targets")
big = target_rows[-1]
mid = next(r for r in target_rows if r["a"] == 100)
st.info(
    f"Bei Angebot {mid['a']}: {mid['wait_prob']} Spuren über dem Angebot für „höchstens 20 % warten“, {mid['mean_wait']} für „mittlere "
    f"Wartezeit höchstens 1 min“, {mid['abandon']} für „höchstens 1 % Abbrecher“. Bei Angebot {big['a']}: {big['wait_prob']}, "
    f"{big['mean_wait']} und {big['abandon']}. Die Wurzelregel passt zum ersten Ziel; die beiden anderen führen in andere Regime."
)

st.markdown("---")
st.subheader("🔬 Skalierung: konvergiert das Verhalten bei festem β?")
scaling = _scaling(patience)
st.plotly_chart(build_scaling_chart(scaling), width="stretch", key=f"scaling_{patience}")
one = scaling[1.0]
st.info(
    f"Bei β = 1 und Geduld {patience} min: Abbruchquote mal √a = {one[0]['p_ab_scaled']:.3f} (a = {one[0]['a']}), "
    f"{one[3]['p_ab_scaled']:.3f} (a = {one[3]['a']}), {one[-1]['p_ab_scaled']:.3f} (a = {one[-1]['a']}); der Anteil der Wartenden "
    f"sinkt von {C.fmt_pct(one[0]['p_wait'], 1)} auf {C.fmt_pct(one[-1]['p_wait'], 1)}. Die Abbruchquote selbst fällt wie 1/√a: "
    "große Gates haben bei gleicher Sicherheitsstufe weniger Abbrecher."
)

st.markdown("---")
st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Konstante Ankunftsrate** | Echte Gates haben Morgenspitzen: die Regel mit dem Tagesmittel unterschätzt die Spitze; sie muss für jeden Zeitpunkt mit der aktuellen Last angewandt werden. | **[Zeitvariable Ankünfte](https://sebastianhanisch-time-varying-arrivals-demo.streamlit.app/)** |
| **Abfertigungsdauer exponentiell** | Halfin-Whitt gilt für beliebige Bedienzeiten nur mit angepasstem Puffer; die Streuung der Dauer geht ein. | **[M/G/1, Kingman-Näherung](https://sebastianhanisch-mg1-kingman-demo.streamlit.app/)** |
| **Das Ziel ist ein Anteil Wartender** | Bei absolutem Wartezeit-Ziel oder Abbruch-Ziel ist der Aufschlag nicht √a-proportional (Abschnitt oben). | kein Folgestück |
| **Exponentielle Geduld** | Die Form der Geduld verschiebt Abbruchquote und Wartezeit nahe 100 % Auslastung (siehe erlang-a-demo). | kein Folgestück |
| **Alle Lkw gleich wichtig** | Eilige Lkw brauchen Vorfahrt; das verschiebt Warten zwischen den Klassen. | **Prioritätsklassen** (Folgestück) |
| **Kosten spielen keine Rolle** | Die kostenminimale Besetzung wählt β aus dem Verhältnis von Spurkosten und Wartekosten. | kein Folgestück |
"""
)
st.caption(
    "Verwandt im Portfolio: [erlang-a-demo](https://sebastianhanisch-erlang-a-demo.streamlit.app/) (Stück 4: Abwanderung), "
    "[mmc-queue-demo](https://sebastianhanisch-mmc-queue-demo.streamlit.app/) (Stück 3: Erlang C und Spurbedarf), "
    "[mm1-queue-demo](https://sebastianhanisch-mm1-queue-demo.streamlit.app/) (Stück 1) und die Rettungsdienst-Demo "
    "[ems-demo](https://sebastianhanisch-ems-demo.streamlit.app/) (Erlang B)."
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell.** M/M/c: Poisson-Ankünfte (Rate $\lambda$), exponentielle Abfertigung (Rate $\mu$ je Spur), $c$ Spuren, eine
FIFO-Schlange; Angebot $a = \lambda/\mu$, Auslastung je Spur $\rho = a/c$. Erlang C: $C(c, a)$ ist der Anteil der Lkw, die warten
müssen (nur für $c > a$); mit Abwanderung (Erlang A) mit Abbruchrate $\theta$ für jedes $c$.

**Wurzel-Personalregel.** $c = \lceil a + \beta\sqrt a\,\rceil$ mit der **Sicherheitsstufe** $\beta = (c-a)/\sqrt a$.

**Halfin-Whitt-Grenzwert.** Für $a \to \infty$ bei festem $\beta > 0$ gilt (Halfin und Whitt 1981)
$$C\bigl(a + \beta\sqrt a,\ a\bigr) \;\to\; \Bigl[\,1 + \beta\,\frac{\Phi(\beta)}{\varphi(\beta)}\Bigr]^{-1},$$
wobei $\Phi$ und $\varphi$ Verteilungsfunktion und Dichte der Standardnormalverteilung sind. Die Funktion fällt von 1 bei
$\beta = 0$ auf 0 für $\beta \to \infty$; die Umkehrfunktion liefert zu einer Ziel-Wartewahrscheinlichkeit $\alpha$ die
Sicherheitsstufe $\beta(\alpha)$ und damit $c = \lceil a + \beta(\alpha)\sqrt a\,\rceil$.

**Exakte Staffelung.** Die kleinste ganze Zahl $c > a$ mit $C(c, a) \le \alpha$ (Erlang-B-Rekursion
$B_k = \frac{aB_{k-1}}{k + aB_{k-1}}$, $C = \frac{B_c}{1 - \rho(1 - B_c)}$); für mittlere Wartezeit
$W_q = C/(c\mu - \lambda) \le w$ entsprechend; für Erlang A die kleinste Spurzahl mit Abbruchquote $\le$ Ziel, wobei der Durchsatz
$\lambda(1 - P(\text{ab})) \le c\mu$ die Untergrenze $c \ge a(1 - \text{Ziel})$ liefert.

**Skalierung mit Abwanderung.** Bei festem $\beta$ und wachsendem $a$ konvergieren $P(\text{warten})$ und $\sqrt a\,P(\text{ab})$
(QED-Skalierung für Erlang A, Garnett, Mandelbaum und Reiman 2002): die Abbruchquote selbst fällt wie $1/\sqrt a$.

**Simulation.** Ereignisliste mit Ankünften, Abgängen und Abbruch-Terminen (SplitMix64, getrennte Ströme); ohne Abbruch die
Kiefer-Wolfowitz-Rekursion. Die Tabellen und Kurven sind exakte Rechnungen, nur das gewählte Gate wird zusätzlich simuliert.

Implementiert in `sqs_formulas.py` (Erlang B/C/A, Halfin-Whitt-Funktion, Regel, exakte Staffelungen), `sqs_simulation.py`
(Ereignissimulation mit Abbruch, Kiefer-Wolfowitz), `sqs_evaluation.py` (Kennzahlen, Tabellen, Regime, Skalierung).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html))."
)
