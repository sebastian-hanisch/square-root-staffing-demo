"""AppTest-Rauchtests: Voreinstellung, jedes Preset, Überlast, Randwerte, Würfel-Knopf, Permalink-Grenzen, Abschnitte, Footer."""

import random
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import sqs_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(**state):
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def _metric(at, label):
    return next(m.value for m in at.metric if m.label == label)


def test_default_run_has_no_exception_and_shows_exact_and_formula_values():
    at = _run()
    _ok(at)
    assert _metric(at, "Spuren c (Regel)") == "110" and _metric(at, "β effektiv = (c − a)/√a") == "1.00"
    assert _metric(at, "Anteil, der warten muss: Erlang C (exakt)") == "23.7 %"
    assert _metric(at, "… Halfin-Whitt-Formel") == "22.3 %" and _metric(at, "Abbruchquote: Erlang A (exakt)") == "0.7 %"


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_button_runs(name):
    at = _run()
    next(b for b in at.button if b.key == f"preset_{name}").click().run()
    _ok(at)
    p = C.PRESETS[name]
    assert at.session_state["a_select"] == p["a"] and at.session_state["beta_slider"] == p["beta"]
    assert at.metric


def test_overload_shows_a_warning_and_no_erlang_c():
    at = _run(beta_slider=-1.0)
    _ok(at)
    assert _metric(at, "Anteil, der warten muss: Erlang C (exakt)") == "gilt nicht (c ≤ a)"
    assert _metric(at, "… Halfin-Whitt-Formel") == "nur für β > 0"
    assert any("Überlast" in w.value for w in at.warning)
    assert _metric(at, "Abbruchquote: Erlang A (exakt)") == "10.4 %"


def test_beta_zero_means_exactly_the_offer_and_is_overload():
    at = _run(beta_slider=0.0)
    _ok(at)
    assert _metric(at, "Spuren c (Regel)") == "100" and any("Überlast" in w.value for w in at.warning)


@pytest.mark.parametrize("kw", [dict(a_select=5), dict(a_select=2000), dict(a_select=2000, beta_slider=3.0, n_select=50000),
                                 dict(beta_slider=C.BETA_MIN), dict(beta_slider=C.BETA_MAX),
                                 dict(patience_slider=C.PATIENCE_MIN), dict(patience_slider=C.PATIENCE_MAX),
                                 dict(a_select=5, beta_slider=-2.0), dict(table_alpha=0.5)])
def test_extreme_settings_run(kw):
    _ok(_run(**kw))


def test_the_halfin_whitt_formula_is_closer_for_larger_gates():
    small, large = _run(a_select=10), _run(a_select=1000)
    gap = lambda at: abs(float(_metric(at, "… Halfin-Whitt-Formel").split()[0]) - float(_metric(at, "Anteil, der warten muss: Erlang C (exakt)").split()[0]))
    assert gap(small) > gap(large)


def test_dice_button_changes_the_seed_and_the_simulated_result(monkeypatch):
    """Der Würfel zieht sonst einen unseeded Zufalls-Seed; bei gerundeten Kennzahlen kollidiert ein Zufallsseed manchmal mit dem
    Standard-Seed (gemessen: 40 Würfe, bis zu 9 gleiche Anzeigen), deshalb ist der gewürfelte Seed im Test fest."""
    monkeypatch.setattr(random, "randint", lambda a, b: 508145)
    at = _run()
    old_seed, old = at.session_state["seed_input"], _metric(at, "Abbruchquote (simuliert)")
    next(b for b in at.button if b.label == "🎲 Neuen Lauf würfeln").click().run()
    _ok(at)
    assert at.session_state["seed_input"] == 508145            # der feste Seed ist wirklich verwendet worden
    assert at.session_state["seed_input"] != old_seed and _metric(at, "Abbruchquote (simuliert)") != old


def test_permalink_values_are_clamped_and_snapped():
    at = AppTest.from_file(APP, default_timeout=300)
    at.query_params["a"] = "150"
    at.query_params["beta"] = "1.37"
    at.query_params["pat"] = "999"
    at.query_params["n"] = "30000"
    at.run()
    _ok(at)
    assert at.session_state["a_select"] == 100 and at.session_state["beta_slider"] == pytest.approx(1.25)
    assert at.session_state["patience_slider"] == C.PATIENCE_MAX and at.session_state["n_select"] == 20000


def test_permalink_ignores_garbage():
    at = AppTest.from_file(APP, default_timeout=300)
    at.query_params["beta"] = "viel"
    at.query_params["a"] = "nan"
    at.run()
    _ok(at)
    assert at.session_state["beta_slider"] == C.DEFAULT_BETA and at.session_state["a_select"] == C.DEFAULT_A


def test_charts_sections_and_limits_table_are_present():
    at = _run()
    _ok(at)
    assert len(at.get("plotly_chart")) == 5
    headers = [s.value for s in at.subheader]
    for part in ("Regel gegen exakte Staffelung", "Drei Regime", "Welches Ziel", "Skalierung", "Wo die Annahmen enden"):
        assert any(part in h for h in headers), part
    table = next(m.value for m in at.markdown if "Wer setzt an" in m.value)
    for name in ("Zeitvariable Ankünfte", "Kingman", "Prioritätsklassen"):
        assert name in table
    assert "geplant" not in table      # die Linie wird erst vollständig veröffentlicht, kein Status-Zusatz


def test_rule_table_shows_the_exact_comparison():
    at = _run(table_alpha=0.2)
    _ok(at)
    assert any("| 20 | 26 | 25 | -1 |" in m.value for m in at.markdown)
    assert any("8 von 10" in i.value for i in at.info)


def test_seed_control_uses_the_portfolio_wording():
    at = _run()
    assert [n.label for n in at.number_input] == ["Zufalls-Seed"]


def test_related_demos_are_linked_and_footer_is_present():
    at = _run()
    text = " ".join(c.value for c in at.caption)
    for name in ("erlang-a-demo", "mmc-queue-demo", "mm1-queue-demo", "ems-demo"):
        assert name in text
    assert "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in text


def test_no_sentence_wide_comma_replacement_in_the_app_source():
    """Regressionsschutz: `.replace(",", ".")` auf einem ganzen (verketteten) Satz macht aus Kommas im Fließtext Punkte; Tausender
    nur über `fmt_int`."""
    source = Path(APP).read_text(encoding="utf-8")
    assert '.replace(",", ".")' not in source.replace('f"{n:,}".replace(",", ".")', "")
