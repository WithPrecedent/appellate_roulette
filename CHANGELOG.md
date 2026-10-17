# Changelog

All notable changes to this project will be documented in this file.

<!-- insertion marker -->

## 0.0.2

* Updated to the `snickerdoodle` 0.4.0 template
* Made `ruff` prefer single quotes
* Made `ruff` ignore boolean default positional arguments (`FBT002`)
* Fixed typos in the contributing guide and noted that the project does not use a code formatter

## 0.0.1

The project was rewritten as a study of whether the composition of the panel
that hears a federal criminal appeal affects its outcome, on the snickerdoodle
template, with courtpy and amos. The code that it replaces (a parser of court
opinions, and tables of judges and of political context) is in courtpy.

### Added

* `load_opinions` and `OpinionData`, which extract the opinions of the federal
  courts of appeals from the two bulk files of CourtListener that hold
  opinions, and not from its dockets, citations, or courts. The court of each
  opinion is found by the rules in `instructions/courts.csv`. The files are
  read with every core of the computer.
* `roulette` and `balance`, which test by randomization inference whether the
  judges who hear a case, and the composition of its panel, are related to
  its outcome and to what was true of the case before it was heard. `spin` is
  the function that they use.
* `studies/appellate_roulette.toml`, the settings of the study, and
  `studies/criminal_issues.csv`, rules for the issues of criminal appeals.
* The `appellate-roulette` command, with `opinions` and `judges` commands of
  its own and every command of courtpy.
