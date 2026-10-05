# Wurzel-Personalregel – wie viele Spuren braucht ein großes Gate? (Streamlit-Demo)

**[→ Demo live ausprobieren](https://sebastianhanisch-square-root-staffing-demo.streamlit.app/)**

Interaktive Demo zur **Wurzel-Personalregel** c = a + β·√a (Halfin-Whitt-Regime, „QED“) am Terminal-Gate. **Fünftes Stück der
Konzepte-Linie „Warteschlangentheorie und Simulation“** im Portfolio von [Sebastian Hanisch](https://sebastianhanisch.net)
(Operations Research und Machine Learning): ein Verfahren, ein wachsendes Beispiel, jedes Folgestück hebt genau eine Annahme auf.

Stück 3 ([mmc-queue-demo](https://github.com/sebastian-hanisch/mmc-queue-demo)) zeigte, dass große Gates bei gleichem Service
heißer laufen dürfen; Stück 4 ([erlang-a-demo](https://github.com/sebastian-hanisch/erlang-a-demo)) brachte Abwanderung. Hier die
Regel dahinter: Bei Angebot a (so viele Spuren sind im Mittel beschäftigt) genügt ein Puffer von **β·√a** Spuren, und die
Sicherheitsstufe β legt fest, wie viele Lkw warten müssen. Die Demo prüft die Regel gegen die **exakte** Erlang-C- und
Erlang-A-Rechnung, zeigt die Konvergenz der Halfin-Whitt-Formel, die drei Regime und, wo die Regel **nicht** gilt: bei anderen
Zielarten und in Überlast.

## Kernfrage

Wie gut ist die Wurzelregel schon bei kleinen Gates, und welche Zielarten führen zu einem ganz anderen Aufschlag als √a?

## Modell und Methodik

- **Modell:** Poisson-Ankünfte, exponentielle Abfertigung (3 min Mittel je Spur), c Spuren, eine FIFO-Schlange, optional exponentielle
  Geduld (Mittel 1 bis 30 min). Angebot a = 2 bis 2000 (Regler) und bis 5000 (Tabellen), Sicherheitsstufe β = −2 bis 3. Regel:
  c = ⌈a + β·√a⌉, β effektiv = (c − a)/√a. Voreinstellung: a = 100, β = 1 (110 Spuren), Geduld 5 min.
- **Exakt gerechnet** (`sqs_formulas.py`): Erlang C (Erlang-B-Rekursion) für c > a, Erlang A (Geburts-Sterbe-Kette mit Abbruch, in
  Logarithmen gerechnet) für jedes c, exakte Staffelungen für drei Zielarten; dazu die **Halfin-Whitt-Funktion**
  P(warten) → [1 + β·Φ(β)/φ(β)]^-1 und ihre Umkehrung. Unabhängige Referenzen im Test: scipy für Φ und φ, das lineare
  Gleichungssystem der abgeschnittenen Kette für Erlang A, die Lehrbuchsumme für Erlang C.
- **Simulation** (`sqs_simulation.py`): Ereignisliste mit Abbruch-Terminen, ohne Abbruch die Kiefer-Wolfowitz-Rekursion, SplitMix64
  mit getrennten Strömen. Der Lauf startet leer; die ersten 30 Minuten (zehn Abfertigungsdauern) werden nicht ausgewertet, die Auslastung wird
  vom Ende dieser Einschwingzeit bis zur letzten Ankunft gemessen (nicht über das Auslaufen danach). Sie prüft nur das gewählte Gate; Tabellen und Kurven sind exakte Rechnungen (Sekunden, im Browser
  zwischengespeichert), eine vorgerechnete Datei gibt es hier nicht.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`; Zeiten bei 3 min Abfertigung, Geduld 5 min, wo nichts anderes steht.

| Frage | Befund |
|---|---|
| Welches β gehört zu welchem Anteil Wartender? | 80 / 50 / 20 / 10 / 5 % warten bei β = **0.17 / 0.51 / 1.06 / 1.42 / 1.74**. Bei β = 1 sagt die Formel 22.3 %. |
| Trifft die Regel die exakte Staffelung? | **18 von 20** Fällen exakt (Angebot a = 5 bis 5000, Ziel höchstens 50 % und höchstens 20 % Wartende); sonst eine Spur daneben (20 %: a = 20 exakt 26, Regel 25; a = 500 exakt 525, Regel 524). Beispiele: a = 100: 106 (50 %) und 111 (20 %) Spuren; a = 5000: 5036 und 5076. |
| Wie nah ist die Formel an der exakten Kurve? | Bei β ≈ 1 weicht die exakte Wartewahrscheinlichkeit von der Formel ab um **3.8** Prozentpunkte (a = 10, 17.4 gegen 13.6 %: 14 Spuren, β effektiv 1.27), 1.4 (a = 100: 23.7 gegen 22.3 %) und 0.4 (a = 1000: 22.3 gegen 21.9 %). |
| Wächst der Aufschlag wirklich wie √a? | Für „höchstens 20 % warten“: **11** Spuren über dem Angebot bei a = 100, **34** bei a = 1000, **76** bei a = 5000 (geteilt durch √a zwischen 1.07 und 1.10). |
| Und bei einem absoluten Wartezeit-Ziel? | Für „mittlere Wartezeit höchstens 1 min“ bleibt der Aufschlag bei **2** (a ≤ 20) bis **3** (a = 50 bis 5000) Spuren; er wächst nicht mit √a. Das erklärt den konstanten Aufschlag in Stück 3. |
| Und bei einem Abbruch-Ziel? | Für „höchstens 1 % brechen ab“ (Geduld 5 min): Aufschlag 4, 5, 6, 7, 8, 9 (a = 5 bis 200), dann 7 (a = 500), 3 (a = 1000), **−8** (a = 2000) und **−41** (a = 5000): große Gates dürfen **weniger Spuren als das Angebot** haben (Überlast). |
| Drei Regime bei a = 1000? | Bei β ≈ −4 (c = 874) warten praktisch alle (100 %) und **12.7 %** brechen ab (Effizienz zuerst); bei β ≈ −0.2 warten 66 % bei 1.5 % Abbrechern, bei β = 0 genau 57 % bei 1.1 %; bei β ≈ 1.7 noch 5 % und bei β ≈ 2.6 nur 0.5 % (Qualität zuerst). |
| Konvergiert das Verhalten mit Abwanderung bei festem β? | **Ja.** √a·Abbruchquote bei β = 0: 0.346–0.348 für a = 10 bis 5000; β = 1: 0.044 (a = 10), 0.053 (a = 50), 0.067 (a = 100, dort ist β effektiv genau 1.00 statt 1.13 bei a = 50), 0.061 bis 0.064 (a = 500 bis 5000); β = −1: 0.99–1.04; β = 2: 0.006–0.007. Anteil Wartender bei β = 1: 14.5 % (a = 10), 17.5 % (a = 1000 und 5000). Die Abbruchquote selbst fällt wie 1/√a. |
| Stimmt die Simulation? | Langer Lauf (200 000 Lkw): a = 50, c = 57 trifft Abbruchquote auf 0.3 Prozentpunkte, a = 100, c = 90 (Überlast) auf 0.8, a = 100, c = 110 ohne Abbruch den Wartenden-Anteil auf 2 Prozentpunkte. |

## Befunde und Korrekturen gegenüber dem Plan

- **Der Live-Lauf war für große Gates verzerrt.** Er startete leer, wertete aber alle Lkw aus und rechnete die Auslastung bis zum Auslaufen nach
  der letzten Ankunft. Bei a = 1000 (c = 1032, 20 000 Lkw, 60 Minuten Lauf) zeigte die App im Mittel von 12 Läufen eine Auslastung von 72.7 % statt der exakten
  96.7 %, bei a = 2000 (c = 2045) 56.0 % statt 97.7 %; auch Anteil Wartender und Abbruchquote lagen darunter (a = 1000: 12.5 % statt 17.5 % und 0.13 % statt 0.20 %).
  Jetzt werden die ersten 30 Minuten nicht ausgewertet (die dafür nötigen Lkw kommen zusätzlich hinzu), und die Auslastung gilt für das Fenster danach: im Mittel von
  12 Läufen 96.7 % (a = 1000) und 98.1 % (a = 2000) gegen 96.7 % und 97.7 % exakt. Anteil Wartender und Abbruchquote streuen bei kurzen Läufen großer Gates weiter stark
  (a = 1000, 20 000 Lkw: 15.9 ± 2.4 % gegen 17.5 % exakt). Aufgefallen ist das beim Orakel-Abgleich der Simulation gegen die exakten Erlang-A-Werte (Decimal-Rechnung).
- **Die Skalierungszahl bei β = 1 war nur an den Enden genannt.** Dort steigt √a·Abbruchquote nicht gleichmäßig von 0.044 (a = 10) auf 0.064 (a = 5000), sondern liegt
  bei a = 100 mit 0.067 darüber, weil dort das Aufrunden β effektiv genau 1.00 ergibt (a = 50: 1.13, a = 500: 1.03).
- **Aus „14 von 16“ wurde „18 von 20“:** Die Vorab-Messreihe prüfte a = 5 bis 1000; die Demo ergänzt a = 2000 und 5000. Beide ergänzten
  Angebote werden bei beiden Zielen exakt getroffen.
- **Der Abbruch-Aufschlag wird negativ:** Die Vorab-Messreihe endete bei a = 1000 (Aufschlag 3), die Tabelle reicht jetzt bis 5000
  (−41). Das war so nicht erwartet.
- **Keine vorgerechnete Datei nötig:** Der Plan sah (wie bei Stück 2 bis 4) vorgerechnete Messreihen vor; alle Tabellen sind exakte
  Rechnungen und brauchen für a bis 5000 zusammen wenige Sekunden. Nur die Simulation des gewählten Gates läuft live.
- **Für Erlang A gibt es hier keine Halfin-Whitt-Formel,** nur exakte Zahlen; die Näherungsformel für den Fall mit Abwanderung
  (Garnett, Mandelbaum, Reiman 2002) ist nicht nachgebaut.

## Ehrliche Grenzen

- Die Halfin-Whitt-Formel gilt hier nur für Erlang C (unendliche Geduld, β > 0); für Erlang A und für Überlast stehen exakte Werte.
- Die Regel wird mit **aufgerundeter** Spurzahl angewandt; die Sicherheitsstufe, die ein ganzzahliges c wirklich verwirklicht (β
  effektiv), weicht deshalb ab, besonders bei kleinen a (a = 10: 1.27 statt 1.0).
- Geprüft sind zwei Wartewahrscheinlichkeits-Ziele (50 und 20 %); andere Ziele (etwa 5 %) wurden nicht tabelliert.
- Der Skalierungsbefund stammt aus Geduld 5 min; mit anderer Geduld verschieben sich die Zahlen, nicht die Konvergenz (nicht für alle
  Geduld-Werte tabelliert).
- Exponentielle Abfertigung und exponentielle Geduld; die Form der Geduld zählt nahe 100 % Auslastung (siehe erlang-a-demo).
- Die Live-Simulation ist **ein** Lauf und streut um die exakten Werte.

## Verwandte Demos im Portfolio

- [`erlang-a-demo`](https://github.com/sebastian-hanisch/erlang-a-demo) (Stück 4): Abwanderung, Überlast, Form der Geduld.
- [`mmc-queue-demo`](https://github.com/sebastian-hanisch/mmc-queue-demo) (Stück 3): Erlang C, Pooling, Spurbedarf.
- [`mm1-queue-demo`](https://github.com/sebastian-hanisch/mm1-queue-demo) (Stück 1) und
  [`ems-demo`](https://github.com/sebastian-hanisch/ems-demo) (Rettungsdienst, prüft sich an Erlang B).

## Bewusst nicht umgesetzt

Jede dieser Annahmen hebt ein Folgestück der Linie auf:

| Annahme | Folgestück |
|---|---|
| Konstante Ankunftsrate | [Zeitvariable Ankünfte](https://github.com/sebastian-hanisch/time-varying-arrivals-demo) |
| Abfertigungsdauer exponentiell | [M/G/1, Kingman-Näherung](https://github.com/sebastian-hanisch/mg1-kingman-demo) |
| Alle Lkw gleich wichtig | [Prioritätsklassen](https://github.com/sebastian-hanisch/priority-queue-demo) |

Kein Folgestück: Kosten-optimale Besetzung, andere Zielarten als die drei gezeigten, Form der Geduld.

## Tests

134 Tests, rund 20 s: Orakel-Tests (`tests/test_oracle_sqs.py`: Erlang C gegen die Poisson-Summe über lgamma bis a = 5000, Erlang A gegen Decimal-Rechnung ohne Logarithmen, Staffelungen gegen eine unabhängige Suche, Ereignissimulation gegen Kiefer-Wolfowitz mit Abbruch, Auslastung eines großen Gates im Live-Lauf), Φ und φ gegen scipy, Halfin-Whitt-Funktion von Hand (β = 0 ergibt 1, β = 1 ergibt 0.2234) und als Umkehrung,
Regel von Hand, Erlang C gegen die Lehrbuchsumme (c = 1 bis 20), Erlang A gegen die abgeschnittene Kette und die Grenzfälle,
Minimalität aller exakten Staffelungen, Abnahme des Formelfehlers mit dem Angebot, Simulation gegen eine von Hand gerechnete
Vier-Lkw-Instanz mit Abbruch (auch ein verfallener Abbruch-Termin nach dem letzten Abgang), Ereignissimulation gegen Kiefer-Wolfowitz,
Simulation gegen Erlang A (normal, Überlast), Tabellen, Regime und Skalierung, Presets/Permalink, AppTest-Rauchtests, ein Quelltext-Test
gegen Satz-Komma-Fehler und `test_claims.py` für jede Zahl dieser README.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche |
| `sqs_formulas.py` | Erlang B/C/A, Halfin-Whitt-Funktion, Regel, exakte Staffelungen |
| `sqs_simulation.py` | Generator, Ereignissimulation mit Abbruch, Kiefer-Wolfowitz |
| `sqs_evaluation.py` | Gate-Bericht, Konvergenz, Tabellen, Regime, Ziele, Skalierung |
| `sqs_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `sqs_presets.py`, `sqs_constants.py` | Presets, Permalink, Grenzen |
| `tests/` | siehe oben |

## Literatur

- Halfin, S., Whitt, W. (1981): Heavy-traffic limits for queues with many exponential servers. *Operations Research* 29(3), 567–588.
- Garnett, O., Mandelbaum, A., Reiman, M. (2002): Designing a call center with impatient customers. *Manufacturing & Service
  Operations Management* 4(3), 208–227.

## Lokal ausführen

```
pip install -r requirements.txt
streamlit run app.py
```

Tests: `pip install -r requirements-dev.txt` und `python -m pytest tests/ -v`.

Gebaut mit Streamlit und Plotly.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Warteschlangentheorie: M/M/1 bis Surrogat](https://sebastianhanisch.net/konzepte-warteschlangentheorie.html).
