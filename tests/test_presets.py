"""Presets: Vollständigkeit, gültige Werte, Permalink-Konstanten."""

import pytest

import sqs_constants as C
import sqs_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) == set(C.PRESET_ORDER) and len(C.PRESETS) == 4
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS) and C.PRESET_HELP[name]


def test_preset_values_are_valid_and_match_the_setting_specs():
    for preset in C.PRESETS.values():
        assert preset["a"] in C.A_OPTIONS and C.BETA_MIN <= preset["beta"] <= C.BETA_MAX and preset["n"] in C.N_OPTIONS
        assert C.PATIENCE_MIN <= preset["patience"] <= C.PATIENCE_MAX
        assert P.snap_beta(preset["beta"]) == preset["beta"]
        for key, state_key in P.PRESET_KEYS.items():
            P.SETTING_SPECS[state_key].caster(preset[key])


def test_preset_names_state_the_values_they_set():
    for name, preset in C.PRESETS.items():
        if "a = " in name:
            assert f"a = {preset['a']}" in name
        if "β = " in name:
            assert f"β = {preset['beta']:g}".replace("-", "−") in name
    assert C.PRESETS["Knapp besetzt (β = −1)"]["beta"] < 0


def test_default_preset_equals_the_default_settings():
    p = C.PRESETS["Normalfall (a = 100, β = 1)"]
    assert (p["a"], p["beta"], p["patience"], p["n"], p["seed"]) == (C.DEFAULT_A, C.DEFAULT_BETA, C.DEFAULT_PATIENCE, C.DEFAULT_N, C.DEFAULT_SEED)


def test_bounds_and_url_params():
    assert P.bounds("beta_slider") == (C.BETA_MIN, C.BETA_MAX) and P.bounds("seed_input") == (0, C.SEED_MAX)
    assert len({spec.url_param for spec in P.SETTING_SPECS.values()}) == len(P.SETTING_SPECS)


@pytest.mark.parametrize("value,expected", [(5, 5), (7, 5), (8, 10), (150, 100), (151, 200), (10**6, 2000), (1, 5)])
def test_a_snaps_to_the_nearest_option(value, expected):
    assert P.snap_to_option("a_select", value) == expected


@pytest.mark.parametrize("value,expected", [(0.0, 0.0), (0.1, 0.0), (0.13, 0.25), (1.37, 1.25), (-5, -2.0), (9, 3.0), (-1.9, -2.0)])
def test_beta_snaps_to_the_step_inside_the_bounds(value, expected):
    assert P.snap_beta(value) == pytest.approx(expected)


def test_formatters():
    assert C.fmt_int(10000) == "10.000" and C.fmt_pct(0.223, 1) == "22.3 %" and C.fmt_pct(0.5) == "50 %"
