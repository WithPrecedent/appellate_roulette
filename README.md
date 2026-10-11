# appellate roulette

| | |
| --- | --- |
| Version | [![PyPI Latest Release](https://img.shields.io/pypi/v/appellate-roulette.svg?style=for-the-badge&color=cornflowerblue&label=PyPI&logo=PyPI&logoColor=yellow)](https://pypi.org/project/appellate-roulette/) [![GitHub Latest Release](https://img.shields.io/github/v/tag/WithPrecedent/appellate_roulette?style=for-the-badge&color=forestgreen&label=GitHub&logo=github)](https://github.com/WithPrecedent/appellate_roulette/releases) |
| Status | [![Build Status](https://img.shields.io/github/actions/workflow/status/WithPrecedent/appellate_roulette/ci.yml?branch=main&style=for-the-badge&color=cadetblue&label=Tests&logo=pytest)](https://github.com/WithPrecedent/appellate_roulette/actions/workflows/ci.yml?query=branch%3Amain) [![Development Status](https://img.shields.io/badge/Development-Active-seagreen?style=for-the-badge&logo=git)](https://www.repostatus.org/#active) [![Project Stability](https://img.shields.io/pypi/status/appellate-roulette?style=for-the-badge&logo=pypi&label=Stability&logoColor=yellow)](https://pypi.org/project/appellate_roulette/) |
| Documentation | [![Hosted By](https://img.shields.io/badge/Hosted_by-Github_Pages-blue?style=for-the-badge&color=forestgreen&logo=github)](https://WithPrecedent.github.io/appellate_roulette) |
| Tools | [![Documentation](https://img.shields.io/badge/MkDocs-magenta?style=for-the-badge&color=deepskyblue&logo=markdown&labelColor=gray)](https://squidfunk.github.io/mkdocs-material/) [![Linter](https://img.shields.io/endpoint?style=for-the-badge&url=https://raw.githubusercontent.com/charliermarsh/Ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/Ruff) [![Dependency Manager](https://img.shields.io/badge/uv-mediumpurple?style=for-the-badge&logo=uv&labelColor=gray)](https://docs.astral.sh/uv/) [![Pre-commit](https://img.shields.io/badge/pre--commit-darkolivegreen?style=for-the-badge&logo=pre-commit&logoColor=white&labelColor=gray)](https://github.com/TezRomacH/python-package-template/blob/master/.pre-commit-config.yaml) [![CI](https://img.shields.io/badge/GitHub_Actions-forestgreen?style=for-the-badge&logo=githubactions&labelColor=gray&logoColor=white)](https://github.com/features/actions) [![Editor Settings](https://img.shields.io/badge/Editor_Config-paleturquoise?style=for-the-badge&logo=editorconfig&labelColor=gray)](https://editorconfig.org/) [![Repository Template](https://img.shields.io/badge/snickerdoodle-bisque?style=for-the-badge&logo=cookiecutter&labelColor=gray)](https://www.github.com/WithPrecedent/snickerdoodle) [![Dependency Maintainer](https://img.shields.io/badge/dependabot-forestgreen?style=for-the-badge&logo=dependabot&logoColor=white&labelColor=gray)](https://github.com/dependabot) |
| Compatibility | [![Compatible Python Versions](https://img.shields.io/pypi/pyversions/appellate-roulette?style=for-the-badge&color=cornflowerblue&label=Python&logo=python&logoColor=yellow)](https://pypi.python.org/pypi/appellate_roulette/) [![Linux](https://img.shields.io/badge/Linux-lightseagreen?style=for-the-badge&logo=linux&labelColor=gray&logoColor=white)](https://www.linux.org/) [![MacOS](https://img.shields.io/badge/MacOS-antiquewhite?style=for-the-badge&logo=apple&labelColor=gray)](https://www.apple.com/macos/)  [![Windows](https://img.shields.io/badge/Windows-blue?style=for-the-badge)](https://www.microsoft.com/en-us/windows?r=1) |
| Stats | [![PyPI Download Rate (per month)](https://img.shields.io/pypi/dm/appellate-roulette?style=for-the-badge&color=cornflowerblue&label=Downloads%20💾&logo=pypi&logoColor=yellow)](https://pypi.org/project/appellate-roulette) [![GitHub Stars](https://img.shields.io/github/stars/WithPrecedent/appellate_roulette?style=for-the-badge&color=forestgreen&label=Stars%20⭐&logo=github)](https://github.com/WithPrecedent/appellate_roulette/stargazers) [![GitHub Contributors](https://img.shields.io/github/contributors/WithPrecedent/appellate_roulette?style=for-the-badge&color=forestgreen&label=Contributors%20🙋&logo=github)](https://github.com/WithPrecedent/appellate_roulette/graphs/contributors) [![GitHub Issues](https://img.shields.io/github/issues/WithPrecedent/appellate_roulette?style=for-the-badge&color=forestgreen&label=Issues%20📘&logo=github)](https://github.com/WithPrecedent/appellate_roulette/graphs/contributors) [![GitHub Forks](https://img.shields.io/github/forks/WithPrecedent/appellate_roulette?style=for-the-badge&color=forestgreen&label=Forks%20🍴&logo=github)](https://github.com/WithPrecedent/appellate_roulette/forks) |
| | |

-----

## What is appellate roulette?

The rule of law rests on a promise of generality: like cases will be treated
alike, and the outcome of a legal dispute will turn on what the law requires
rather than on the identity of the official who happens to apply it. This
study subjects that promise to empirical scrutiny in federal criminal appeals.

* **Cases**: the opinions of the twelve regional courts of appeals filed since
  January 1, 2010, from [CourtListener](https://www.courtlistener.com), parsed
  and coded with [courtpy](https://github.com/WithPrecedent/CourtPy). 
* **Judges**: who each judge of a panel is, who appointed the judge, and the
  judge's sex, race, age, and career, from the Federal Judicial Center's
  [Biographical Directory of Article III Federal
  Judges](https://www.fjc.gov/history/judges).
* **Analysis**: with [amos](https://github.com/WithPrecedent/amos), which
  records every step and parameter, so that the results can
  be reproduced.

## Research design

The study's methods are described in one settings file,
[`studies/appellate_roulette.toml`](https://github.com/WithPrecedent/appellate_roulette/blob/main/studies/appellate_roulette.toml):

| | |
| --- | --- |
| Unit | One criminal appeal brought by the defendant and decided by a three-judge panel, all of whose judges are identified. |
| Outcome | `outcome_criminal_defendant_won`: whether the court reversed, vacated, or remanded. |
| Treatment | Which judges heard the appeal (`panel_names`), and the composition of the panel: how many of its judges were appointed by Democratic presidents, are women, are not white, were prosecutors or public defenders, are senior, or are visiting from another court, and their mean age. |
| Comparison | Appeals of the same circuit and year, among which the judges are drawn without regard to the merits. |

It asks whether the outcome depends on the panel in three ways:

1. **The wheel** (`roulette`, in
   [`roulette.py`](https://github.com/WithPrecedent/appellate_roulette/blob/main/src/appellate_roulette/roulette.py)). How far the outcomes
   of each judge's appeals, and of each kind of panel, are from the outcomes
   of the other appeals of the same circuit and year is measured. 
2. **The odds** (`fixest`). A model of whether the defendant won, with a
   fixed effect for each circuit and each year, estimates how much one more
   judge of each kind on the panel changes the odds.
3. **Prediction** (the `analyst`). Multiple models are trained to predict the
   outcome from the panel and the appeal, and tested on appeals that were held
   out. If the panel does not matter, shuffling its composition costs the best
   model nothing (`permutation_importance`).

## The opinions

CourtListener publishes its database as bulk files every three months.
courtpy's own bulk download reads five of them, because CourtListener records
the court of a case on its docket. This project's `load_opinions` (and the
`appellate-roulette opinions` command) reads only the two that hold opinions:

| File | Size (2026-09-30) | Read |
| --- | --- | --- |
| `opinions` | 55 GB | Yes: the text of each opinion. |
| `opinion-clusters` | 2.5 GB | Yes: each decision's name, date, judges, and status. |
| `dockets` | 5.1 GB | No. |
| `citations` | 0.1 GB | No. |
| `courts` | under 1 MB | No. |

The file of opinions is nearly all of the download, and there is no smaller
bulk file that holds the opinions of only some courts. What reading two files
saves is mostly time: they are decompressed and read with every core of the
computer (with [indexed_bzip2](https://github.com/mxmlnkn/indexed_bzip2) and
[pyarrow](https://arrow.apache.org/docs/python/)), which takes from half an
hour to an hour rather than many hours. To download less, use the API (below).

Without the dockets, the court of each opinion is found from the opinion
itself, by the rules in
[`instructions/courts.csv`](https://github.com/WithPrecedent/appellate_roulette/blob/main/src/appellate_roulette/instructions/courts.csv):
the website that CourtListener collected the opinion from (such as
`ca1.uscourts.gov`), or else the court that the headmatter of its case names.
Measured against the dockets, for the 375,994 decisions of the thirteen courts
of appeals filed from 2010 through September 2026, the rules:

| | |
| --- | --- |
| Find the court of | 346,441 decisions (92.1%), and every decision filed since 2020 |
| Put in the wrong court of appeals | none |
| Take for a court of appeals | 4 opinions of other courts |
| Find by year | 83% of 2010, 85 to 89% of 2011 to 2017, 91% of 2018, 97.5% of 2019 |
| Find by court | 64% of the D.C. Circuit, 85% of the Fourth, 86% of the Seventh, 88% of the Federal, and 92 to 98% of the others |

The decisions that are not found are the 29,423 that CourtListener has only
from the Harvard Law School Library's scans of the printed reporters, which
come with neither an address nor headmatter. About three fifths of them have
the same name as (or a shorter form of the name of) a decision of the same
court and day that is found, so they appear to be second copies. About a
quarter (some 7,600, or 2% of all decisions) have no counterpart. Those are
concentrated in 2010 and 2018, and a third of them are filed under the D.C.
Circuit, where many are opinions of the district court that the dockets
attribute to the court of appeals. 

Two ways to add the decisions that are left out, both of which skip the cases
that are already saved:

```sh
# With a CourtListener API key, which is stored in the system's keyring.
# About ten hours of requests at the API's pace, which can be stopped and
# resumed.
uv run appellate-roulette key set
uv run appellate-roulette download api --courts federal_circuits --start 2010-01-01 --folder data/court_listener

# Or from the bulk data with its dockets (5 GB more, and slower to read).
uv run appellate-roulette download bulk --courts federal_circuits --start 2010-01-01 --folder data/court_listener
```

Delete `data/appeals.csv` afterward, so that the added cases are parsed. To
collect every case from the API instead, with no bulk files at all, set
`download = "api"` in the settings (and remove `parties`, which only the bulk
extraction uses).

CourtListener also holds some decisions more than once: an opinion that a
court posted twice, or an opinion and an order in one appeal. About 3% of the
decisions that name the United States repeat the court, day, and name of
another. An appeal that is counted twice has the same judges and the same
outcome both times, which would make the judges look as if they mattered, so
the study keeps one decision for each court, day, and name (`drop_duplicates`).

## The variables

| Variable | Meaning | From |
| --- | --- | --- |
| `outcome_criminal_defendant_won` | Whether the defendant won: the court reversed, vacated, or remanded in the defendant's appeal. | courtpy's `code_outcome` |
| `type_criminal`, `appeal_by_defendant` | Whether the case is criminal, and whether the defendant brought the appeal. | courtpy's `code_case_type` and `code_parties` |
| `panel_names`, `panel_found`, `panel_size` | The judges of the panel as the roster names them, how many were found, and how many the opinion names. | courtpy's `code_judges` |
| `democratic_appointees`, `women`, `minority_judges`, `former_prosecutors`, `former_defenders`, `visiting_judges`, `senior_judges` | How many of the three judges are of each kind. | The settings (`derive_columns`), from the roster's attributes |
| `panel_age` | The mean age of the judges. | courtpy's `code_judges` |
| `criminal_*`, `civil_habeas`, `civil_aedpa` | The crimes and proceedings that the opinion discusses. | courtpy's federal rules |
| `issue_*` | The issues of the appeal, such as suppression, sufficiency of the evidence, or the reasonableness of a sentence. | [`studies/criminal_issues.csv`](https://github.com/WithPrecedent/appellate_roulette/blob/main/studies/criminal_issues.csv) |

## Getting started

### Requirements

The study requires Python 3.11, 3.12, or 3.13 and
[uv](https://docs.astral.sh/uv/). It runs on Linux, macOS, and Windows.

The first run downloads the two bulk files of opinions (about 58 GB, kept
outside the project so that they can be used again) unless courtpy has already
downloaded them, and the Federal Judicial Center's files of judges. No API key
is needed.

### Installation

In the project's folder:

```sh
uv sync
```

courtpy is installed from GitHub until version 0.2.2 is on PyPI (see
`[tool.uv.sources]` in `pyproject.toml`).

### Usage

Make the roster of judges once, and then run the study:

```sh
uv run appellate-roulette judges
uv run appellate-roulette run studies/appellate_roulette.toml --export
```

In Python:

```python
import appellate_roulette

project = appellate_roulette.Project.create("studies/appellate_roulette.toml")
print(project.result.tables["balance"])
print(project.result.tables["roulette"])
print(project.result.tables["roulette_judges"].head(20))
```

`appellate-roulette` also runs any courtpy command (such as
`appellate-roulette rules studies/criminal_issues.csv`) with this project's
techniques available. To extract the opinions without running the study:

```sh
uv run appellate-roulette opinions --courts federal_circuits --parties "United States"
```

The first run saves:

| File | Holds |
| --- | --- |
| `data/court_listener/` | One JSON file for each case, with its opinions. |
| `data/appeals.csv` | The coded cases. Later runs reuse it; delete it after changing the `load_opinions_parameters` section or the rules. |
| `results/` | The tables, figures, and report of the analysis, with `--export`. |

The tables to read first:

| Table | Holds |
| --- | --- |
| `balance` | For each thing that was true of an appeal before it was heard, the p-values of whether the judges and the composition of the panels predict it. |
| `roulette` | The test of the judges, the joint test of the composition, and a test of each attribute: the statistic, what chance alone would make it, and the p-value. |
| `roulette_judges` | For each judge, how many appeals the judge heard, how often the defendant won, how often the defendant won in the other appeals of the same circuits and years, and how unusual the difference is. |
| `fixest_coefficients` | The change in the log odds for one more judge of each kind. |
| `permutation_importance` | How much the best model's predictions worsen when each feature is shuffled. |

### Layout

| Path | Holds |
| --- | --- |
| `studies/` | The settings of the study, and the rules for the issues of criminal appeals. |
| `src/appellate_roulette/opinions.py` | `load_opinions` and `OpinionData`, which extract the opinions. |
| `src/appellate_roulette/instructions/courts.csv` | The rules that find the court of an opinion. |
| `src/appellate_roulette/roulette.py` | `roulette`, `balance`, and `spin`, which test whether the draw of judges matters. |
| `tests/` | Tests, with fictional judges and cases. |

## Acknowledgments

The opinions come from CourtListener, a project of the [Free Law
Project](https://free.law), whose bulk data makes research on court opinions
possible at no cost, and some of them from the Harvard Law School Library's
[Caselaw Access Project](https://case.law). The judges' biographies come from
the [Federal Judicial Center](https://www.fjc.gov).

This project was generated from [@WithPrecedent](https://github.com/WithPrecedent)'s [![cookiecutter Template](https://img.shields.io/badge/snickerdoodle-bisque?style=for-the-badge&logo=cookiecutter&labelColor=gray)](https://www.github.com/WithPrecedent/snickerdoodle) template.

## License

Use of this repository is authorized under the [Apache Software License 2.0](https://www.github.com/WithPrecedent/appellate_roulette/blob/main/LICENSE).
