"""Runs the study on fictional appeals."""

from __future__ import annotations

import pathlib

import chrisjen
import courtpy
from conftest import make_case, write_cases

import appellate_roulette

STUDIES = pathlib.Path(__file__).parents[1] / 'studies'


def test_appellate_roulette_study(
    roster: courtpy.judges.Roster,
    tmp_path: pathlib.Path) -> None:
    # Two judges lean toward defendants and one away from them, so the draw
    # of judges matters in these appeals.
    write_cases(
        tmp_path / 'data' / 'court_listener', 420,
        lean = {'Lynch': 0.25, 'Graber': 0.25, 'Howard': -0.05})
    # CourtListener holds one appeal twice.
    for number in (9001, 9002):
        courtpy.courtlistener.save_case(
            courtpy.courtlistener.case_path(
                tmp_path / 'data' / 'court_listener', 'ca1', number),
            make_case(
                number, 'ca1', ['Lynch', 'Howard', 'Thompson'],
                name = 'United States v. Twice'))
    idea = chrisjen.Idea.create(STUDIES / 'appellate_roulette.toml')
    loader = idea['load_opinions_parameters']
    loader['download'] = 'none'
    loader['workers'] = 1
    loader['rulebooks'] = f'federal, {(STUDIES / "criminal_issues.csv").as_posix()}'
    idea['balance_parameters']['simulations'] = 99
    idea['roulette_parameters']['simulations'] = 499
    idea['roulette_parameters']['minimum'] = 20
    idea['random_forest_parameters']['n_estimators'] = 20
    project = appellate_roulette.Project.create(idea, clerk = tmp_path)
    result = project.result
    assert result.label == 'outcome_criminal_defendant_won'
    techniques = [entry['technique'] for entry in result.history]
    assert techniques[:5] == [
        'load_opinions', 'code_parties', 'code_case_type', 'code_outcome',
        'code_judges']
    assert {'balance', 'roulette', 'fixest'} <= set(techniques)
    assert (tmp_path / 'data' / 'appeals.csv').is_file()
    # Every fictional appeal is a criminal appeal by the defendant, decided
    # by three judges who are in the roster, and the appeal that is there
    # twice is kept once.
    assert 'drop_duplicates' in techniques
    assert len(result.data) == 421
    assert {
        'democratic_appointees', 'women', 'former_prosecutors', 'year',
        'court_ca1'} <= set(result.data.columns)
    assert 'panel_names' not in result.data.columns
    assert set(result.data['democratic_appointees'].unique()) <= {0, 1, 2, 3}
    tables = result.tables
    assert {
        'balance', 'roulette', 'roulette_judges', 'summarize',
        'label_balance', 'fixest_coefficients', 'analyst_comparison',
        'scorecard', 'permutation_importance'} <= set(tables)
    # The judges matter, and the judges who lean are found.
    wheel = tables['roulette']
    assert wheel.loc['judges', 'p_value'] < 0.05
    assert wheel.loc['judges', 'cases'] == 421
    assert wheel.loc['judges', 'units'] == 11
    assert {'composition', 'panel_party', 'panel_woman'} <= set(wheel.index)
    judges = tables['roulette_judges']
    assert {'Lynch, Mary Ann', 'Graber, Susan P.'} <= set(judges.index[:3])
    assert judges.loc['Lynch, Mary Ann', 'difference'] > 0
    # The draw was random, so it is not related to the crimes charged.
    balance = tables['balance']
    assert balance.loc['criminal_firearm', 'judges_p'] > 0.001
    assert (balance['judges_p'].dropna() > 0.001).all()
    # A crime that no fictional appeal is about cannot be tested.
    assert balance['judges_p'].isna().any()
    assert 'democratic_appointees' in tables['fixest_coefficients'].index
    assert {'coefficient_plot', 'roc_curve'} <= set(result.figures)
    assert 0 <= result.metrics['roc_auc'] <= 1
    folder = project.export()
    assert (folder / 'tables' / 'roulette.csv').is_file()
