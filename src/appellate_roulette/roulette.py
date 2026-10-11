"""Tests whether the judges who hear a case change its outcome.

The courts of appeals assign judges to panels, and cases to panels, without
regard to the merits of the cases. So within one court in one year, which
three judges hear an appeal is close to a draw from a wheel: appellate
roulette. If outcomes turned only on what the law requires, the draw would
not matter, and the appeals that any judge hears would come out like the
other appeals of the same court and year, give or take chance.

`spin` measures how far the outcomes depart from that, and then finds out how
large a departure chance alone would make by spinning the wheel again: it
shuffles the outcomes among the cases of each court and year (each "stratum"),
which breaks any tie between an outcome and the judges who reached it while
keeping everything else as it was, and measures the departure again. The
share of shuffles with a departure at least as large as the real one is the
p-value. It makes no assumption about the distribution of outcomes, the
number of cases that a judge hears, or how judges overlap on panels. It
tests two things:

* **The judges.** For each judge, the outcomes of the judge's cases are
  compared with the outcomes of all cases in the same strata. The statistic
  is the sum of the squared, standardized differences of every judge with
  enough cases, so it is large when who is on the panel matters, in either
  direction and for any reason.
* **The composition of the panel.** For each attribute of a panel (such as
  the share of its judges appointed by Democratic presidents), the statistic
  is the difference in the outcome that goes with a difference of one in the
  attribute, among cases of the same stratum. A joint statistic asks whether
  the attributes together explain the outcomes.

Two techniques use it. Both are `amos` describers, which add tables to a
dataset and leave its data unchanged, and both are added to the `amos`
library as soon as appellate_roulette is imported:

* `roulette` tests the outcome (the label of the study).
* `balance` tests the draw itself, by asking the same questions of what was
  true of each case before any judge heard it (such as the crime charged).
  If the judges were drawn at random, the draw cannot predict those things,
  so small p-values here mean that the comparison is not a fair one.

Contents:
    Balance: tests whether the judges who heard each case are related to
        what was true of the case before they heard it.
    Roulette: tests whether the outcome of a case depends on the judges who
        heard it.
    Spin: the results of a test.
    spin: tests whether a column of the cases depends on their judges.
    _ATTRIBUTE_PREFIX: start of the names of the columns that describe the
        composition of a panel, which are tested unless others are named.
    _BATCH: number of shuffles that are made and measured at a time.
    _NOT_COMPOSITION: columns that start with `_ATTRIBUTE_PREFIX` but count
        the judges of a panel rather than describe them.
    _SEPARATOR: the text between names in a list that was saved as text.
    _attributes: returns the columns that describe the composition of each
        panel.
    _center: returns a column with the mean of its stratum taken from it.
    _incidence: returns which judges heard which cases.
    _listify: returns a setting as a list of names.
    _names: returns a cell of a table of cases as a list of names.
    _numbers: returns a column as numbers.
    _p_value: returns the share of shuffles at least as extreme as the data.
    _shuffles: yields the centered outcomes, shuffled within strata.
    _spread: returns how much chance alone would vary the outcomes of each
        judge.

"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterator, Sequence
from typing import Any

import amos
import numpy as np
import pandas as pd
from scipy import sparse

_ATTRIBUTE_PREFIX: str = 'panel_'
_BATCH: int = 50
_NOT_COMPOSITION: frozenset[str] = frozenset({
    'panel_size', 'panel_found', 'panel_ids', 'panel_names', 'panel_judges',
    'panel_text'})
_SEPARATOR: str = '; '


@dataclasses.dataclass
class Spin:
    """The results of a test of whether a column depends on the judges.

    Args:
        tests: a table with a row for each test: "judges", "composition"
            (every attribute together), and each attribute. Its columns are
            "statistic", "expected" (the mean of the statistic over the
            shuffles), "p_value", "cases", "units" (the judges or attributes
            tested), and "simulations".
        judges: a table with a row for each judge with enough cases, sorted
            from the judge whose cases depart most from their strata. Its
            columns are "cases", "rate" (the mean of the column in the
            judge's cases), "expected" (the mean in the strata of those
            cases), "difference", "z" (the difference, in standard
            deviations of what chance alone would make it), and "p_value"
            (the share of shuffles in which the judge's difference was at
            least as large, in either direction).

    """

    tests: pd.DataFrame
    judges: pd.DataFrame


@dataclasses.dataclass
class Roulette(amos.Describer):
    """Tests whether the outcome of a case depends on the judges who heard it.

    The table that it adds ("roulette") has a row for each test (see `Spin`),
    and "roulette_judges" has a row for each judge. A small p-value in the
    "judges" row means that outcomes differ among judges by more than chance
    would make them, and one in the row of an attribute means that the
    outcome goes with that attribute of the panel.

    With hundreds of judges, some have small p-values of their own by chance
    alone, so the table of judges shows where the differences are, and the
    "judges" row says whether there are any.

    """

    def describe(
        self,
        item: amos.Dataset,
        *,
        outcome: str | None = None,
        judges: str = 'panel_names',
        strata: Sequence[str] | str = ('court_num', 'year'),
        attributes: Sequence[str] | str | None = None,
        simulations: int = 2000,
        minimum: int = 20,
        **kwargs: Any) -> pd.DataFrame:
        """Returns the tests of whether the outcome depends on the judges.

        Args:
            item: the dataset of cases.
            outcome: name of the column to test. Defaults to `None`, in which
                case it is the label of the dataset.
            judges: name of the column that lists the judges who heard each
                case. Defaults to "panel_names", which `code_judges` makes.
            strata: names of the columns within which the judges are drawn at
                random. Defaults to "court_num" and "year".
            attributes: names of the columns that describe the composition of
                each panel. Defaults to `None`, in which case they are the
                columns of numbers whose names start with "panel_" (except
                those that count a panel's judges).
            simulations: number of times to shuffle the outcomes. Defaults to
                2,000.
            minimum: fewest cases that a judge must have heard to be tested.
                Defaults to 20.
            **kwargs: not used.

        Raises:
            ValueError: if no outcome is named and the dataset has no label.

        Returns:
            The table of tests. The table of judges is added to the tables of
                `item` as "{name}_judges".

        """
        column = outcome or item.label
        if column is None:
            message = (
                f'{self.name!r} needs an "outcome" to test, or a dataset '
                f'with a label'
            )
            raise ValueError(message)
        result = spin(
            item.data, column, judges = judges, strata = _listify(strata),
            attributes = _attributes(item.data, attributes, column),
            simulations = int(simulations), minimum = int(minimum),
            seed = item.seed)
        item.tables[f'{self.name}_judges'] = result.judges
        return result.tests


@dataclasses.dataclass
class Balance(amos.Describer):
    """Tests whether the judges drawn are related to what a case was about.

    Random assignment is what lets the outcomes of different panels be
    compared. It cannot be seen, but its consequences can: nothing that was
    true of a case before its judges were drawn (its "covariates", such as
    which side appealed or the crime charged) can depend on the draw. The
    table ("balance") has a row for each covariate, with the p-values of the
    tests that `roulette` applies to the outcome: "judges_p" (whether the
    covariate differs among judges) and "composition_p" (whether it goes with
    the composition of the panel), and the p-value of each attribute.

    If assignment is random, the p-values are spread evenly between 0 and 1,
    so about one in twenty is below 0.05. Many small ones mean that cases of
    some kinds reach some judges more than others (as when a court sends
    some kinds of appeals to special panels), and that those kinds should be
    strata or be left out.

    """

    def describe(
        self,
        item: amos.Dataset,
        *,
        covariates: Sequence[str] | str | None = None,
        judges: str = 'panel_names',
        strata: Sequence[str] | str = ('court_num', 'year'),
        attributes: Sequence[str] | str | None = None,
        simulations: int = 1000,
        minimum: int = 20,
        **kwargs: Any) -> pd.DataFrame:
        """Returns the tests of whether each covariate depends on the judges.

        Args:
            item: the dataset of cases.
            covariates: names of the columns that were true of each case
                before its judges were drawn. Defaults to `None`, which is an
                error: they must be named.
            judges: as for `Roulette.describe`.
            strata: as for `Roulette.describe`.
            attributes: as for `Roulette.describe`.
            simulations: number of times to shuffle each covariate. Defaults
                to 1,000.
            minimum: as for `Roulette.describe`.
            **kwargs: not used.

        Raises:
            ValueError: if no covariates are named.

        Returns:
            The table, with a row for each covariate.

        """
        names = _listify(covariates)
        if not names:
            message = (
                f'{self.name!r} needs "covariates": the columns that were '
                f'true of each case before its judges were drawn'
            )
            raise ValueError(message)
        rows = {}
        for position, name in enumerate(names):
            result = spin(
                item.data, name, judges = judges, strata = _listify(strata),
                attributes = _attributes(item.data, attributes, name),
                simulations = int(simulations), minimum = int(minimum),
                seed = None if item.seed is None else item.seed + position)
            tests = result.tests
            row = {
                'cases': tests.loc['judges', 'cases'],
                'judges_p': tests.loc['judges', 'p_value'],
                'composition_p': tests.loc['composition', 'p_value']}
            for attribute in tests.index[2:]:
                row[f'{attribute}_p'] = tests.loc[attribute, 'p_value']
            rows[name] = row
        return pd.DataFrame.from_dict(rows, orient = 'index')


def spin(
    data: pd.DataFrame,
    outcome: str,
    *,
    judges: str = 'panel_names',
    strata: Sequence[str] = ('court_num', 'year'),
    attributes: Sequence[str] = (),
    simulations: int = 2000,
    minimum: int = 20,
    seed: int | None = None) -> Spin:
    """Tests whether a column of the cases depends on their judges.

    Cases with no value in `outcome` or in one of `strata` are left out. A
    case with no value of an attribute is left out of the tests of that
    attribute.

    Args:
        data: the cases, one row for each.
        outcome: name of the column to test: booleans or numbers.
        judges: name of the column that lists the judges who heard each case
            (as lists, or as text with "; " between names). Defaults to
            "panel_names".
        strata: names of the columns within which the judges are drawn at
            random. Defaults to "court_num" and "year".
        attributes: names of the columns of numbers or booleans that describe
            the composition of each panel. Defaults to an empty tuple.
        simulations: number of times to shuffle the outcomes within the
            strata. Defaults to 2,000.
        minimum: fewest cases that a judge must have heard to be tested.
            Defaults to 20.
        seed: seed for the shuffles, so that they can be repeated. Defaults
            to `None`.

    Raises:
        KeyError: if `data` lacks a column that is named.
        ValueError: if there are no cases to test.

    Returns:
        The results (see `Spin`).

    """
    needed = [outcome, judges, *strata, *attributes]
    missing = [name for name in needed if name not in data.columns]
    if missing:
        message = f'the cases have no columns named {missing}'
        raise KeyError(message)
    values = _numbers(data[outcome])
    known = values.notna()
    for name in strata:
        known &= data[name].notna()
    cases = data.loc[known]
    if cases.empty:
        message = f'no case has a value of {outcome!r} and of {list(strata)}'
        raise ValueError(message)
    # The cases are put in the order of their strata, so that a shuffle
    # within the strata is a sort of each stratum's cases by random numbers.
    codes = cases.groupby(list(strata), sort = False).ngroup().to_numpy()
    order = np.argsort(codes, kind = 'stable')
    cases, codes = cases.iloc[order], codes[order]
    y = values.loc[known].to_numpy(dtype = float)[order]
    centered = _center(y, codes)
    names, incidence = _incidence(cases[judges])
    heard = np.asarray(incidence.sum(axis = 1)).ravel()
    spread = _spread(incidence, centered, codes)
    tested = (heard >= minimum) & (spread > 0)
    scale = np.sqrt(np.where(tested, spread, 1.0))
    columns = list(attributes)
    design = np.zeros((len(cases), len(columns)))
    for place, name in enumerate(columns):
        column = _numbers(cases[name]).to_numpy(dtype = float)
        present = ~np.isnan(column)
        design[present, place] = _center(column[present], codes[present])
    varied = np.asarray(design.any(axis = 0))
    sums = (design ** 2).sum(axis = 0)
    sums[~varied] = 1.0
    # The joint statistic is the part of the outcomes that the attributes
    # explain together, which the pseudo-inverse finds even when some
    # attributes are combinations of others.
    solver = np.linalg.pinv(design.T @ design) if columns else np.zeros((0, 0))

    def measure(outcomes: np.ndarray) -> tuple[np.ndarray, ...]:
        """Returns each statistic for each column of (shuffled) outcomes."""
        differences = (incidence @ outcomes) / scale[:, None]
        products = design.T @ outcomes
        return (
            differences,
            (differences[tested] ** 2).sum(axis = 0, keepdims = True),
            products / sums[:, None],
            (products * (solver @ products)).sum(axis = 0, keepdims = True))

    actual = measure(centered[:, None])
    shuffled = [
        measure(batch) for batch in _shuffles(
            centered, codes, simulations, np.random.default_rng(seed))]
    by_judge, dispersion, slopes, joint = (
        np.concatenate([batch[part] for batch in shuffled], axis = -1)
        for part in range(4))
    rows = {
        'judges': (
            actual[1][0, 0], dispersion.mean(),
            _p_value(actual[1], dispersion)[0], int(tested.sum()))}
    rows['composition'] = (
        actual[3][0, 0] if varied.any() else np.nan,
        joint.mean() if varied.any() else np.nan,
        _p_value(actual[3], joint)[0] if varied.any() else np.nan,
        int(varied.sum()))
    slope_p = _p_value(np.abs(actual[2]), np.abs(slopes))
    for place, name in enumerate(columns):
        rows[name] = (
            actual[2][place, 0] if varied[place] else np.nan,
            slopes[place].mean() if varied[place] else np.nan,
            slope_p[place] if varied[place] else np.nan, 1)
    tests = pd.DataFrame.from_dict(
        rows, orient = 'index',
        columns = ['statistic', 'expected', 'p_value', 'units'])
    if not centered.any():
        # Nothing can be learned from a column that is the same in every
        # case of each stratum.
        tests[['statistic', 'expected', 'p_value']] = np.nan
    tests.insert(3, 'cases', len(cases))
    tests['simulations'] = simulations
    totals = incidence @ y
    expected = incidence @ (y - centered)
    table = pd.DataFrame({
        'cases': heard.astype(int),
        'rate': totals / np.maximum(heard, 1),
        'expected': expected / np.maximum(heard, 1),
        'difference': (totals - expected) / np.maximum(heard, 1),
        'z': actual[0][:, 0],
        'p_value': _p_value(np.abs(actual[0]), np.abs(by_judge))},
        index = pd.Index(names, name = 'judge'))
    table = table.loc[tested].sort_values(
        'z', key = lambda column: -column.abs(), kind = 'stable')
    return Spin(tests = tests, judges = table)


""" Private Functions """


def _attributes(
    data: pd.DataFrame,
    attributes: Sequence[str] | str | None,
    outcome: str) -> list[str]:
    """Returns the columns that describe the composition of each panel.

    Args:
        data: the cases.
        attributes: the names that a study gave, or `None` if it gave none.
        outcome: name of the column being tested, which is never one of its
            own attributes.

    Returns:
        `attributes`, or if it is `None`, the columns of numbers or booleans
            whose names start with `_ATTRIBUTE_PREFIX` and are not in
            `_NOT_COMPOSITION`.

    """
    if attributes is not None:
        return [name for name in _listify(attributes) if name != outcome]
    return [
        str(name) for name in data.columns
        if str(name).startswith(_ATTRIBUTE_PREFIX)
        and name not in _NOT_COMPOSITION and name != outcome
        and (
            pd.api.types.is_bool_dtype(data[name].dtype)
            or pd.api.types.is_numeric_dtype(data[name].dtype))]


def _center(values: np.ndarray, codes: np.ndarray) -> np.ndarray:
    """Returns values with the mean of their stratum taken from them.

    Args:
        values: a number for each case.
        codes: the number of the stratum of each case.

    Returns:
        Each value less the mean of the values of its stratum.

    """
    _, compact = np.unique(codes, return_inverse = True)
    means = np.bincount(compact, weights = values) / np.bincount(compact)
    return np.asarray(values - means[compact])


def _incidence(panels: pd.Series) -> tuple[list[str], sparse.csr_matrix]:
    """Returns which judges heard which cases.

    Args:
        panels: the judges of each case (see `_names`).

    Returns:
        The names of the judges, sorted, and a matrix with a row for each of
            them and a column for each case, which is 1 where the judge heard
            the case.

    """
    listed = [_names(panel) for panel in panels]
    names = sorted({name for panel in listed for name in panel})
    places = {name: place for place, name in enumerate(names)}
    rows = [places[name] for panel in listed for name in dict.fromkeys(panel)]
    columns = [
        case for case, panel in enumerate(listed)
        for _ in dict.fromkeys(panel)]
    matrix = sparse.csr_matrix(
        (np.ones(len(rows)), (rows, columns)),
        shape = (len(names), len(listed)))
    return names, matrix


def _listify(item: Sequence[str] | str | None) -> list[str]:
    """Returns a setting as a list of names.

    Args:
        item: `None`, names separated by commas, or a sequence of names.

    Returns:
        The names, without spaces at their ends or blank names.

    """
    if item is None:
        return []
    names = item.split(',') if isinstance(item, str) else item
    return [str(name).strip() for name in names if str(name).strip()]


def _names(value: Any) -> list[str]:
    """Returns a cell of a table of cases as a list of names.

    Args:
        value: a list of names, the text that courtpy saves for one (with
            "; " between the names), or a missing value.

    Returns:
        The names, or an empty `list` if there are none.

    """
    if isinstance(value, str):
        return [name for name in value.split(_SEPARATOR) if name.strip()]
    if isinstance(value, list | tuple | np.ndarray):
        return [str(name) for name in value]
    return []


def _numbers(column: pd.Series) -> pd.Series:
    """Returns a column as numbers.

    Args:
        column: a column of numbers or booleans, which may have missing
            values, or of the text of booleans (as in a table that was loaded
            from a CSV file).

    Returns:
        The column as decimals, with 1 and 0 for true and false, and a
            missing value for anything that is not a number.

    """
    if column.dtype == object or pd.api.types.is_string_dtype(column.dtype):
        column = column.map(
            lambda value: {'true': 1.0, 'false': 0.0}.get(
                str(value).strip().lower(), value))
    return pd.to_numeric(column, errors = 'coerce').astype('float64')


def _p_value(actual: np.ndarray, shuffled: np.ndarray) -> np.ndarray:
    """Returns the share of shuffles at least as extreme as the data.

    The data count as one of the shuffles (which they are, if the judges do
    not matter), so a p-value is never 0.

    Args:
        actual: each statistic of the data, in a column.
        shuffled: each statistic of each shuffle, with a column for each
            shuffle.

    Returns:
        The p-value of each statistic.

    """
    reached = np.asarray((shuffled >= actual - 1e-12).sum(axis = -1))
    return np.asarray((reached + 1) / (shuffled.shape[-1] + 1), dtype = float)


def _spread(
    incidence: sparse.csr_matrix,
    centered: np.ndarray,
    codes: np.ndarray) -> np.ndarray:
    """Returns how much chance alone would vary the outcomes of each judge.

    If the outcomes of a stratum are dealt at random to its cases, the sum
    of the (centered) outcomes of the cases that a judge hears varies as a
    sample drawn without replacement does: by the variance of the outcomes
    in the stratum for each case heard, less the share of the stratum that
    the judge hears (a judge who hears every case of a stratum has its sum,
    whatever the deal).

    Args:
        incidence: which judges heard which cases (see `_incidence`).
        centered: the outcome of each case less the mean of its stratum.
        codes: the number of the stratum of each case.

    Returns:
        The variance of the sum of the centered outcomes of each judge's
            cases, over every way of shuffling the outcomes within strata.

    """
    _, compact = np.unique(codes, return_inverse = True)
    sizes = np.bincount(compact)
    variances = np.bincount(compact, weights = centered ** 2) / sizes
    strata = sparse.csr_matrix(
        (np.ones(len(compact)), (np.arange(len(compact)), compact)),
        shape = (len(compact), len(sizes)))
    counts = np.asarray((incidence @ strata).todense())
    left = (sizes - counts) / np.maximum(sizes - 1, 1)
    return np.asarray((counts * left * variances).sum(axis = 1))


def _shuffles(
    centered: np.ndarray,
    codes: np.ndarray,
    simulations: int,
    rng: np.random.Generator) -> Iterator[np.ndarray]:
    """Yields the centered outcomes, shuffled within strata.

    Args:
        centered: the outcome of each case less the mean of its stratum, in
            the order of the strata.
        codes: the number of the stratum of each case, in that order.
        simulations: number of shuffles to make.
        rng: the source of random numbers.

    Yields:
        Batches of shuffles, each with a row for each case and a column for
            each shuffle.

    """
    for start in range(0, simulations, _BATCH):
        count = min(_BATCH, simulations - start)
        batch = np.empty((len(centered), count))
        for place in range(count):
            # Sorting by stratum and then by a random number shuffles the
            # cases of each stratum among themselves.
            order = np.lexsort((rng.random(len(centered)), codes))
            batch[:, place] = centered[order]
        yield batch
