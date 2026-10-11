# Advanced User Guide

## How the court of an opinion is found

CourtListener records the court of a case on its docket, and this project
does not read the dockets. `OpinionData` finds the court of each opinion with
the rules in `src/appellate_roulette/instructions/courts.csv`, which are rules
of courtpy and can be read, changed, and checked the same way:

```sh
uv run appellate-roulette rules src/appellate_roulette/instructions/courts.csv
```

The rules make one variable, `court`, from three pieces of text:

| Target | What it is | What the rules do with it |
| --- | --- | --- |
| `address` | Where CourtListener collected the opinion from (its `download_url`). | The website of a court of appeals, or its package at govinfo.gov, gives the court. Any other address gives "other". |
| `opening` | The first 3,000 characters of the opinion, as plain text. | A bankruptcy appellate panel named as the court at the top gives "other", since some panels post on the website of their circuit. Nothing else is taken from it. |
| `headmatter` | The start of the case as a printed reporter has it, for the decisions that CourtListener merged with the Harvard Law School Library's scans. | "United States Court of Appeals, First Circuit" gives the court, unless another court, "certiorari", or "certified" comes first. |

The first rule that matches wins, in the order of the file. An opinion that
matches none is skipped, and a decision none of whose opinions match is left
out. A decision whose court is "other" is left out as soon as that is known.

To use other rules, pass a file:

```python
from appellate_roulette import OpinionData

data = OpinionData(rulebook="my_courts.csv")
data.extract("federal_circuits", "2010-01-01", folder="data/court_listener")
```

## How well the rules work

The rules were measured against the dockets of the bulk data of 2026-09-30,
for every opinion of a decision filed since 2010 (3.3 million opinions, of
which 394,881 are of the thirteen courts of appeals).

| | Decisions | |
| --- | ---: | ---: |
| Of the courts of appeals, by the dockets | 375,994 | |
| Found, in the right court | 346,441 | 92.14% |
| Found by the address | 341,725 | |
| Found by the headmatter | 4,716 | |
| Found, in the wrong court of appeals | 0 | |
| Taken for a bankruptcy appellate panel | 66 | 0.02% |
| Not found | 29,487 | 7.84% |

The 66 are opinions of bankruptcy appellate panels that the dockets attribute
to the Sixth and Eighth Circuits. Of the opinions of every other court, 4 were
taken for a court of appeals, 2 of which are opinions of the Sixth Circuit
that the dockets attribute to its bankruptcy appellate panel.

By how CourtListener got the decision (its `source`):

| Source | Found |
| --- | ---: |
| A court's website (`C`) | 99.97% of 188,583 |
| A court's website, merged with Harvard's scan (`CU`) | 100% of 147,703 |
| Harvard's scan only (`U`) | 0% of 29,423 |
| Other combinations | 10,216 of 10,285 |

So the rule of thumb is simple: a decision that CourtListener collected from a
court's website is found, and one that it has only from Harvard's scan is not.
The courts' websites were collected from early 2010, and Harvard's scans end
in 2018 or 2019, so the gap is in those years:

| Year | Found | | Year | Found |
| --- | ---: | --- | --- | ---: |
| 2010 | 83.3% | | 2015 | 87.7% |
| 2011 | 88.5% | | 2016 | 85.4% |
| 2012 | 88.4% | | 2017 | 87.6% |
| 2013 | 89.3% | | 2018 | 91.4% |
| 2014 | 88.3% | | 2019 | 97.5% |

Every later year is above 99.9%.

The decisions that are not found were compared with the decisions of the same
court and day that are found, by the words of their names:

| The Harvard-only decision | Decisions |
| --- | ---: |
| Has the same name as one that is found | 4,964 |
| Has a name within (or around) the name of one that is found, as "United States v. Smith" is within "United States v. John Smith" | 13,341 |
| Shares a word of its name with one that is found | 3,523 |
| Has no counterpart | 7,595 |

Most are second copies of decisions that are found. Of the 7,595 with no
counterpart, 2,506 are attributed to the D.C. Circuit, and many of those are
opinions of the district court. The rest are spread over the circuits, with
the most in 2010 (before the courts' websites were collected) and in 2018.

## Adding the decisions that are left out

courtpy's own downloads save cases in the same form and the same folders, and
skip the cases that are already saved. So either of them fills the gap:

```sh
# The API (a key is needed; about ten hours of requests for every circuit).
uv run appellate-roulette key set
uv run appellate-roulette download api --courts federal_circuits --start 2010-01-01 --end 2019-12-31 --folder data/court_listener

# The bulk data with its dockets.
uv run appellate-roulette download bulk --courts federal_circuits --start 2010-01-01 --end 2019-12-31 --folder data/court_listener
```

The API lists the cases of a court twenty at a time, and asks for the opinions
of a page only if a case on it is missing, so the requests are few for the
years in which nearly every case is saved. It waits when CourtListener asks
it to slow down, and it can be stopped and run again, which resumes it.

Both add the second copies as well as the decisions with no counterpart. The
study's `drop_duplicates` removes a copy only if its name is exactly the name
of the other, so after filling the gap, compare the names of the appeals that
share a court, a day, and a panel before relying on the results.

## The test

For the appeals of one stratum (a circuit in a year), let `y` be the outcome
with the stratum's mean taken from it.

* **Judges.** For judge `j`, `d_j` is the sum of `y` over the judge's
  appeals. If outcomes have nothing to do with judges, `d_j` has a mean of
  zero and a variance that follows from sampling the judge's appeals without
  replacement from each stratum. The statistic is the sum over judges of
  `d_j` squared divided by that variance. Judges with fewer than `minimum`
  appeals are left out of it.
* **An attribute.** With `x` the attribute with its stratum's mean taken
  from it, the statistic is the slope of `y` on `x`.
* **Composition.** The variation in `y` that all of the attributes explain
  together: the explained sum of squares of a regression of `y` on them.

Each is computed for the real outcomes and for each shuffle of the outcomes
within strata. The p-value is the number of shuffles with a statistic at least
as extreme as the real one, plus one, divided by the number of shuffles plus
one, so it is never zero. For the judges and the composition, "extreme" means
large. For an attribute, it means far from zero in either direction.

Shuffling outcomes within a stratum is the same as redrawing the panels among
its appeals. It keeps the number of appeals that each judge heard, the panels
that sat together, and the share of appeals that defendants won in each
circuit and year.

## Changing the study

Everything about the study is in `studies/appellate_roulette.toml`:

| To | Change |
| --- | --- |
| Study another period | `start_date` and `end_date` of `[load_opinions_parameters]` |
| Study every case, and not only those that name the United States | Remove `parties` |
| Study civil appeals | The `query` of `[filter_rows_parameters]`, the `label` of `[general]`, and the covariates of `[balance_parameters]` |
| Compare within finer strata | `strata` of `[balance_parameters]` and `[roulette_parameters]`, with any columns of the appeals |
| Test other attributes of panels | `attributes` of `[roulette_parameters]` (the default is every numeric column that starts with `panel_`) |
| Add issues | Rules in `studies/criminal_issues.csv` |

Delete `data/appeals.csv` after changing the loader's parameters or the rules,
so that the cases are parsed again.
