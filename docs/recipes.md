# Recipes

## Extract the opinions of one circuit and year

```sh
uv run appellate-roulette opinions --courts ca9 --start 2023-01-01 --end 2023-12-31 --folder data/ca9_2023
```

## Extract without keeping the bulk files

`--stream` reads the files as they arrive from CourtListener, without saving
them. It needs no room for them, but every run downloads them again, and they
are read with one core.

```sh
uv run appellate-roulette opinions --courts federal_circuits --stream
```

## Use bulk files that are somewhere else

```sh
uv run appellate-roulette opinions --bulk-folder D:/court_listener_bulk --bulk-date 2026-09-30
```

## Collect the cases from the API instead

Store a key once, and then set `download = "api"` in
`[load_opinions_parameters]` (and remove `parties`):

```sh
uv run appellate-roulette key set
```

The API gives the court of each case, so no court has to be found, and nothing
but the opinions of the courts and dates that are asked for is downloaded. It
takes about ten hours of requests for the twelve circuits since 2010.

## Parse the saved cases into a table without running the study

```sh
uv run appellate-roulette parse data/court_listener --output data/cases.csv
```

## Test another outcome

`roulette` tests the study's label unless it is given another column:

```toml
[roulette_parameters]
outcome = "published"
strata = ["court_num", "year"]
```

Whether a panel publishes its opinion is the panel's choice, so this asks
whether the draw of judges changes how often opinions are published.

## Test the judges of one circuit

```python
import pandas as pd

from appellate_roulette import spin

appeals = pd.read_csv("data/appeals.csv", index_col="case_id", low_memory=False)
chosen = appeals[
    (appeals["court"] == "ca5")
    & (appeals["type_criminal"] == True)  # noqa: E712
    & (appeals["appeal_by_defendant"] == True)  # noqa: E712
    & (appeals["panel_size"] == 3)
    & (appeals["panel_found"] == 3)]
chosen = chosen.drop_duplicates(["court", "date_filed", "case_name"])
result = spin(
    chosen, "outcome_criminal_defendant_won", strata=["year"],
    attributes=["panel_party", "panel_woman"], simulations=5000, seed=43)
print(result.tests)
print(result.judges.head(10))
```

## Check how many panels were fully identified

```python
import pandas as pd

appeals = pd.read_csv("data/appeals.csv", index_col="case_id", low_memory=False)
criminal = appeals[(appeals["type_criminal"] == True) & (appeals["panel_size"] == 3)]  # noqa: E712
print((criminal["panel_found"] == 3).groupby(criminal["court"]).mean())
```

## Check the rules that find courts against your own cases

```python
from appellate_roulette import OpinionData
from appellate_roulette.opinions import find_court

book = OpinionData()._book()
print(find_court(book, address="https://www.ca5.uscourts.gov/opinions/pub/23/23-10001-CR0.pdf"))
print(find_court(book, headmatter="UNITED STATES v. DOE. United States Court of Appeals, Second Circuit."))
```
