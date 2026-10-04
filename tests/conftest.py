import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class ScriptedRng:
    """Liefert vorgegebene Werte statt Zufall (Mini-Instanzen von Hand gerechnet). `expovariate(rate)` ignoriert die Rate und
    gibt der Reihe nach die Werte zurück."""

    def __init__(self, exp_values=()):
        self.exp_values = list(exp_values)
        self.n_exp = 0

    def expovariate(self, rate):
        v = self.exp_values[self.n_exp]
        self.n_exp += 1
        return v


@pytest.fixture
def mini_streams():
    """Vier Lkw an EINER Spur: Zwischenankünfte 1 / 0.5 / 0.5 / 3.5 (Ankünfte bei 1, 1.5, 2, 5.5), Bedienzeiten 3 / 9 / 1 / 2,
    Geduld 99 / 1 / 5 / 99. Von Hand: Lkw 1 startet bei 1 (Abgang 4); Lkw 2 wartet ab 1.5 und bricht bei 2.5 ab (Wartezeit 1);
    Lkw 3 startet bei 4 (Wartezeit 2, Abgang 5; sein Abbruch-Termin bei 7 verfällt); Lkw 4 startet bei 5.5 (Abgang 7.5)."""
    return (ScriptedRng(exp_values=[1, 0.5, 0.5, 3.5]), ScriptedRng(exp_values=[3, 9, 1, 2]),
            ScriptedRng(exp_values=[99, 1.0, 5.0, 99]))
