"""Tests the roulette module."""

from __future__ import annotations

import amos
import numpy as np
import pandas as pd
import pytest

from appellate_roulette import roulette


def deal(
    seed: int,
    spread: float = 0.0,
    *,
    courts: int = 3,
    years: int = 3,
    cases: int = 150,
    bench: int = 9,
    party: float = 0.0) -> tuple[pd.DataFrame, dict[str, float]]:
    """Returns fictional cases whose judges are drawn at random.

    A defendant's chance of winning depends on the court and year, on the
    "lean" of each judge of the panel (which has the standard deviation
    `spread`), and on the party of the judges (by `party` for each).

    """
    rng = np.random.default_rng(seed)
    leans, parties = {}, {}
    for court in range(courts):
        for seat in range(bench):
            name = f'Judge {court}-{seat}'
            leans[name] = rng.normal(0, spread) if spread else 0.0
            parties[name] = -1 if seat % 2 else 1
    rows = []
    for court in range(courts):
        names = [f'Judge {court}-{seat}' for seat in range(bench)]
        for year in range(2010, 2010 + years):
            base = 0.2 + 0.05 * court + 0.02 * (year - 2010)
            for _ in range(cases):
                panel = [str(name) for name in rng.choice(names, 3, replace = False)]
                chance = base + sum(leans[n] + party * parties[n] for n in panel)
                rows.append({
                    'court_num': court + 1, 'year': year, 'panel_names': panel,
                    'panel_party': np.mean([parties[n] for n in panel]),
                    'panel_noise': rng.normal(),
                    'panel_size': 3,
                    'won': bool(rng.random() < np.clip(chance, 0.01, 0.99)),
                    'drugs': bool(rng.random() < 0.3)})
    return pd.DataFrame(rows), leans


def test_techniques_are_in_the_library() -> None:
    assert amos.library.classify('roulette') == 'describer'
    assert amos.library.classify('balance') == 'describer'


def test_spin_when_judges_do_not_matter() -> None:
    data, _ = deal(1)
    result = roulette.spin(
        data, 'won', attributes = ['panel_party', 'panel_noise'],
        simulations = 400, seed = 5)
    tests = result.tests
    assert list(tests.index) == ['judges', 'composition', 'panel_party', 'panel_noise']
    assert list(tests.columns) == [
        'statistic', 'expected', 'p_value', 'cases', 'units', 'simulations']
    assert (tests['cases'] == len(data)).all() and (tests['simulations'] == 400).all()
    assert list(tests['units']) == [27, 2, 1, 1]
    assert (tests['p_value'] > 0.02).all()
    # The statistic of the judges is the sum of their squared differences, in
    # standard deviations, so chance alone makes it about one for each judge.
    assert 15 < tests.loc['judges', 'expected'] < 40
    judges = result.judges
    assert list(judges.columns) == ['cases', 'rate', 'expected', 'difference', 'z', 'p_value']
    assert len(judges) == 27 and judges.index.name == 'judge'
    assert judges['cases'].sum() == 3 * len(data)
    assert np.allclose(judges['rate'] - judges['expected'], judges['difference'])
    assert list(judges['z'].abs()) == sorted(judges['z'].abs(), reverse = True)
    assert 0.6 < judges['z'].std() < 1.4


def test_spin_finds_judges_who_matter() -> None:
    data, leans = deal(2, 0.06)
    result = roulette.spin(data, 'won', attributes = ['panel_noise'], simulations = 400, seed = 5)
    assert result.tests.loc['judges', 'p_value'] < 0.01
    assert result.tests.loc['judges', 'statistic'] > 2 * result.tests.loc['judges', 'expected']
    assert result.tests.loc['panel_noise', 'p_value'] > 0.02
    truth = pd.Series(leans).loc[result.judges.index]
    assert np.corrcoef(result.judges['z'], truth)[0, 1] > 0.7
    assert (result.judges['p_value'] >= 1 / 401).all()


def test_spin_finds_composition_that_matters() -> None:
    data, _ = deal(3, party = 0.04)
    result = roulette.spin(
        data, 'won', attributes = ['panel_party', 'panel_noise'],
        simulations = 400, seed = 5)
    tests = result.tests
    assert tests.loc['panel_party', 'p_value'] < 0.01
    assert tests.loc['composition', 'p_value'] < 0.01
    assert tests.loc['panel_noise', 'p_value'] > 0.02
    # Each judge of the president's party adds 0.04 to the chance, and a
    # panel of three of one party differs from one of the other by 2 in
    # "panel_party", so the difference for each unit is about 0.12.
    assert 0.06 < tests.loc['panel_party', 'statistic'] < 0.18
    assert abs(tests.loc['panel_party', 'expected']) < 0.02


def test_p_values_are_even_when_judges_do_not_matter() -> None:
    values = []
    for seed in range(30):
        data, _ = deal(100 + seed, courts = 2, years = 2, cases = 80, bench = 7)
        result = roulette.spin(
            data, 'won', attributes = ['panel_party'], simulations = 99,
            minimum = 10, seed = seed)
        values.append(result.tests['p_value'].to_numpy())
    means = np.mean(values, axis = 0)
    assert ((means > 0.3) & (means < 0.7)).all()


def test_spin_can_be_repeated() -> None:
    data, _ = deal(4, 0.05)
    first = roulette.spin(data, 'won', simulations = 100, seed = 9)
    again = roulette.spin(data, 'won', simulations = 100, seed = 9)
    other = roulette.spin(data, 'won', simulations = 100, seed = 10)
    pd.testing.assert_frame_equal(first.tests, again.tests)
    pd.testing.assert_frame_equal(first.judges, again.judges)
    assert first.tests.loc['judges', 'statistic'] == other.tests.loc['judges', 'statistic']
    assert first.tests.loc['judges', 'expected'] != other.tests.loc['judges', 'expected']
    # The order of the cases does not change the statistics.
    shuffled = roulette.spin(data.sample(frac = 1, random_state = 3), 'won', simulations = 100, seed = 9)
    assert np.isclose(shuffled.tests.loc['judges', 'statistic'], first.tests.loc['judges', 'statistic'])


def test_spin_reads_what_it_is_given() -> None:
    data, _ = deal(5, 0.05, courts = 2, years = 2, cases = 100)
    expected = roulette.spin(data, 'won', attributes = ['panel_party'], simulations = 50, seed = 1)
    # Names saved as text, outcomes as the text of booleans, and cases that
    # cannot be used.
    saved = data.copy()
    saved['panel_names'] = saved['panel_names'].map('; '.join)
    saved['won'] = saved['won'].map(str)
    extra = pd.DataFrame({
        'court_num': [1, None, 1], 'year': [2010, 2010, 2010],
        'panel_names': ['Judge 0-1; Judge 0-2; Judge 0-3'] * 3,
        'panel_party': [0.0, 0.0, 0.0], 'won': [None, 'True', 'maybe']})
    result = roulette.spin(
        pd.concat([saved, extra], ignore_index = True), 'won',
        attributes = ['panel_party'], simulations = 50, seed = 1)
    pd.testing.assert_frame_equal(result.tests, expected.tests)
    # A case with no value of an attribute is left out of that attribute.
    partial = data.copy()
    partial.loc[partial.index[:40], 'panel_party'] = np.nan
    result = roulette.spin(partial, 'won', attributes = ['panel_party'], simulations = 50, seed = 1)
    assert pd.notna(result.tests.loc['panel_party', 'p_value'])
    assert result.tests.loc['judges', 'statistic'] == expected.tests.loc['judges', 'statistic']


def test_spin_leaves_out_what_cannot_be_tested() -> None:
    data, _ = deal(6, courts = 2, years = 2, cases = 60)
    data['panel_same'] = 1.0
    data['constant'] = True
    result = roulette.spin(data, 'won', attributes = ['panel_same'], simulations = 50, minimum = 1000)
    assert result.judges.empty and result.tests.loc['judges', 'units'] == 0
    assert pd.isna(result.tests.loc['panel_same', 'p_value'])
    assert pd.isna(result.tests.loc['composition', 'p_value'])
    # Something that is the same in every case of each stratum.
    same = roulette.spin(data, 'constant', attributes = ['panel_party'], simulations = 50)
    assert same.tests['p_value'].isna().all()
    with pytest.raises(KeyError, match = 'no_such'):
        roulette.spin(data, 'no_such')
    with pytest.raises(KeyError, match = 'circuit'):
        roulette.spin(data, 'won', strata = ['circuit'])
    with pytest.raises(ValueError, match = 'no case'):
        roulette.spin(data.assign(won = None), 'won')


def test_roulette_describer() -> None:
    data, _ = deal(7, 0.06)
    dataset = amos.Dataset(data, label = 'won', seed = 43)
    roulette.Roulette().apply(dataset, simulations = 200, strata = 'court_num, year')
    tests = dataset.tables['roulette']
    # The attributes are the columns of numbers that start with "panel_",
    # except those that count the judges.
    assert list(tests.index) == ['judges', 'composition', 'panel_party', 'panel_noise']
    assert tests.loc['judges', 'p_value'] < 0.05
    assert len(dataset.tables['roulette_judges']) == 27
    assert dataset.history[-1] == {'technique': 'roulette', 'table': 'roulette'}
    assert list(dataset.data.columns) == list(data.columns)
    # The same seed gives the same shuffles.
    again = amos.Dataset(data, label = 'won', seed = 43)
    roulette.Roulette().apply(again, simulations = 200)
    pd.testing.assert_frame_equal(again.tables['roulette'], tests)
    other = amos.Dataset(data, seed = 43)
    roulette.Roulette().apply(
        other, outcome = 'drugs', attributes = 'panel_party', simulations = 50, minimum = 60)
    assert list(other.tables['roulette'].index) == ['judges', 'composition', 'panel_party']
    assert (other.tables['roulette_judges']['cases'] >= 60).all()
    with pytest.raises(ValueError, match = 'outcome'):
        roulette.Roulette().apply(amos.Dataset(data))


def test_balance_describer() -> None:
    data, _ = deal(8, 0.06)
    # Appeals of one kind reach one judge more often than chance would send
    # them, so the draw is not random for that kind.
    stacked = data['panel_names'].map(lambda panel: 'Judge 0-0' in panel)
    data['steered'] = stacked & (np.random.default_rng(1).random(len(data)) < 0.7)
    dataset = amos.Dataset(data, label = 'won', seed = 43)
    roulette.Balance().apply(
        dataset, covariates = ['drugs', 'steered'], simulations = 200)
    table = dataset.tables['balance']
    assert list(table.index) == ['drugs', 'steered']
    assert list(table.columns) == [
        'cases', 'judges_p', 'composition_p', 'panel_party_p', 'panel_noise_p']
    assert table.loc['drugs', 'judges_p'] > 0.01
    assert table.loc['steered', 'judges_p'] < 0.01
    assert (table['cases'] == len(data)).all()
    assert 'balance_judges' not in dataset.tables
    with pytest.raises(ValueError, match = 'covariates'):
        roulette.Balance().apply(amos.Dataset(data, label = 'won'))
