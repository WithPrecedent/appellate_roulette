"""Tests the commands."""

from __future__ import annotations

import pathlib

import courtpy
import pytest
from conftest import DATE, LocalBucket, fjc_tables
from test_opinions import bucket  # noqa: F401

import appellate_roulette
from appellate_roulette import __main__ as commands

ROOT = pathlib.Path(__file__).parents[1]


def test_package() -> None:
    assert appellate_roulette.__version__ == '0.0.1'
    assert appellate_roulette.Project is courtpy.Project
    for name in appellate_roulette.__all__:
        assert hasattr(appellate_roulette, name)


def test_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stopped:
        commands.main(['--help'])
    assert stopped.value.code == 0
    shown = capsys.readouterr().out
    assert 'opinions' in shown and 'judges' in shown
    # courtpy's commands follow this project's own.
    assert 'run' in shown and 'rules' in shown
    with pytest.raises(SystemExit):
        commands.main(['opinions', '--help'])
    assert '--parties' in capsys.readouterr().out


def test_opinions_command(
    bucket: pathlib.Path,  # noqa: F811
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(courtpy.bulk.requests, 'Session', lambda: LocalBucket(bucket))
    output = tmp_path / 'cases'
    code = commands.main([
        'opinions', '--courts', 'ca1', 'ca2', '--folder', str(output),
        '--bulk-folder', str(bucket), '--bulk-date', DATE,
        '--parties', 'United States'])
    assert code == 0
    assert '3 cases saved' in capsys.readouterr().out
    assert sorted(p.name for p in output.rglob('*.json')) == ['1.json', '11.json', '3.json']
    # The study starts in 2010 unless another date is given.
    code = commands.main([
        'opinions', '--courts', 'ca1', '--folder', str(tmp_path / 'old'),
        '--bulk-folder', str(bucket), '--bulk-date', DATE,
        '--start', '2009-01-01', '--end', '2009-12-31'])
    assert code == 0
    assert [p.name for p in (tmp_path / 'old').rglob('*.json')] == ['7.json']


def test_opinions_command_errors(
    bucket: pathlib.Path,  # noqa: F811
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(courtpy.bulk.requests, 'Session', lambda: LocalBucket(bucket))
    code = commands.main([
        'opinions', '--courts', 'scotus', '--folder', str(tmp_path / 'cases'),
        '--bulk-folder', str(bucket), '--bulk-date', DATE])
    assert code == 1
    assert 'scotus' in capsys.readouterr().err


def test_judges_command(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str]) -> None:
    asked = []

    def download(folder: object = None, *, overwrite: bool = False, **kwargs: object) -> dict[str, pathlib.Path]:
        """Saves the fictional judges as the files that are downloaded."""
        asked.append(overwrite)
        paths = {}
        for kind, table in fjc_tables().items():
            paths[kind] = tmp_path / f'{kind}.csv'
            table.to_csv(paths[kind], index = False)
        return paths

    monkeypatch.setattr(courtpy.judges, 'download', download)
    assert commands.main(['judges', '--update']) == 0
    assert asked == [True]
    assert 'A roster of 14 judges' in capsys.readouterr().out
    roster = courtpy.judges.Roster.load()
    assert roster.match('LYNCH', 1, 2015) is not None


def test_courtpy_commands(capsys: pytest.CaptureFixture[str]) -> None:
    # The rules of this project are valid rules of courtpy.
    assert commands.main(['rules', str(ROOT / 'studies' / 'criminal_issues.csv')]) == 0
    assert 'issue_suppression' in capsys.readouterr().out
    courts = ROOT / 'src' / 'appellate_roulette' / 'instructions' / 'courts.csv'
    assert commands.main(['rules', str(courts)]) == 0
    assert 'court' in capsys.readouterr().out
    assert commands.main(['rules', 'no_such_file.csv']) == 1
