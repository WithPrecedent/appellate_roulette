# Tutorial

This walks through the study from an empty folder to its results. Every
command is run in the project's folder.

## 1. Install

```sh
uv sync
```

## 2. Make the roster of judges

courtpy identifies the judges of each panel with a roster that it builds from
the Federal Judicial Center's files. Make it once:

```sh
uv run appellate-roulette judges
```

The command prints where the roster was saved (courtpy's data folder, outside
the project). Run it with `--update` to download the files again, which adds
judges who have joined the bench since.

## 3. Try the extraction on a few cases

The opinions come from two of CourtListener's bulk files, which are about 58
GB together. They are downloaded the first time they are needed and kept in
courtpy's data folder, so every later run (of this project, or of anything
else that uses courtpy) reads the same copies.

To see what the extraction saves before committing to all of it, stop it after
a thousand cases:

```sh
uv run appellate-roulette opinions --courts federal_circuits --parties "United States" --max-cases 1000 --folder data/sample
```

Each case is one JSON file, in a folder named for its court:

```text
data/sample/ca4/167431.json
data/sample/ca5/78912.json
...
```

A case holds the decision (its name, date, judges, and status), its opinions,
and nothing else. It has no docket and no citations, because the files that
hold them are not read.

## 4. Run the study

```sh
uv run appellate-roulette run studies/appellate_roulette.toml --export
```

The first run:

1. Extracts the cases of the twelve regional circuits that name the United
   States, filed since 2010, into `data/court_listener` (half an hour to an
   hour, once the bulk files are downloaded).
2. Parses each case with courtpy's federal rules and the rules in
   `studies/criminal_issues.csv`, finds its parties, whether it is criminal,
   who appealed, and who won, and identifies its judges. The coded cases are
   saved in `data/appeals.csv`.
3. Keeps the criminal appeals by defendants that three identified judges
   decided, once each.
4. Tests whether the draw of judges is unrelated to the appeals (`balance`),
   and whether it changes their outcomes (`roulette`).
5. Fits the logit model, trains and tests the three predictive models, and
   draws the figures.
6. Saves everything in `results`.

Later runs start at step 3, because they reuse `data/appeals.csv`.

## 5. Read the results

Start with `results/tables/balance.csv`. Each row is something that was true
of an appeal before any judge heard it, and each column is a p-value: whether
the judges (`judges_p`), the composition of the panels taken together
(`composition_p`), or one attribute of the panels predicts it. Under a random
draw, these are spread evenly between 0 and 1. A table full of small values
means that the draw was not random with respect to the appeals, and that
`roulette` cannot be read as the effect of the judges.

Then read `results/tables/roulette.csv`:

| Column | Meaning |
| --- | --- |
| `statistic` | For `judges`, the sum over the judges of the squared difference between the outcomes of a judge's appeals and those of the other appeals of the same circuits and years, in standard deviations. For an attribute, the difference in the share of appeals that the defendant wins that goes with a difference of one in the attribute. For `composition`, how much of the variation in outcomes the attributes explain together. |
| `expected` | The mean of the statistic when the outcomes are shuffled. For `judges` it is about the number of judges tested. |
| `p_value` | The share of shuffles with a statistic at least as far from what chance makes as the real one. |
| `cases`, `units`, `simulations` | How many appeals, how many judges (or attributes), and how many shuffles. |

`results/tables/roulette_judges.csv` has a row for each judge who heard enough
appeals: how many, how often the defendant won (`rate`), how often the
defendant won in the other appeals of the same circuits and years
(`expected`), and how unusual the difference is (`z` and `p_value`). With a
few hundred judges, a dozen with p-values under 0.05 are expected by chance,
so the test of all the judges together is the one to rely on.

## 6. Use the test on its own

`spin` takes any table of cases with a column of the judges of each case, the
columns that define the strata, and an outcome:

```python
import numpy as np
import pandas as pd

from appellate_roulette import spin

rng = np.random.default_rng(1)
judges = [f"Judge {letter}" for letter in "ABCDEFGHI"]
# Each judge leans a little toward or away from defendants.
lean = dict(zip(judges, rng.normal(0, 0.08, len(judges))))
rows = []
for year in (2015, 2016, 2017):
    for _ in range(300):
        panel = [str(name) for name in rng.choice(judges, 3, replace=False)]
        chance = 0.15 + sum(lean[judge] for judge in panel)
        rows.append({
            "court_num": 1, "year": year, "panel_names": panel,
            "panel_senior": rng.integers(0, 4) / 3,
            "won": bool(rng.random() < chance)})
result = spin(
    pd.DataFrame(rows), "won", attributes=["panel_senior"],
    simulations=2000, seed=43)
print(result.tests.round(3))
print(result.judges.round(3).head(4))
```

```text
              statistic  expected  p_value  cases  units  simulations
judges           32.031     9.131    0.001    900      9         2000
composition       0.024     0.163    0.724    900      1         2000
panel_senior     -0.014     0.001    0.724    900      1         2000
         cases   rate  expected  difference      z  p_value
judge
Judge D    273  0.139     0.208      -0.069 -3.347    0.001
Judge G    310  0.161     0.208      -0.046 -2.484    0.016
Judge B    316  0.247     0.207       0.040  2.159    0.038
Judge I    317  0.240     0.207       0.033  1.789    0.082
```

The judges matter in these fictional appeals, and the test finds it: the
statistic is more than three times what chance makes. Whether a judge is
senior was drawn at random, and the test finds nothing there.
