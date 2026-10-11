"""Shared fixtures for the tests, with fictional judges and cases."""

from __future__ import annotations

import bz2
import copy
import csv
import io
import pathlib
import random
from collections.abc import Iterator
from typing import Any

import chrisjen
import courtpy
import pandas as pd
import pytest

DATE = '2026-09-30'
FIRST = 'U.S. Court of Appeals for the First Circuit'
NINTH = 'U.S. Court of Appeals for the Ninth Circuit'
APPEALS = 'U.S. Court of Appeals'
DISTRICT = 'U.S. District Court'
CLINTON = ('William J. Clinton', 'Democratic')
BUSH = ('George W. Bush', 'Republican')
OBAMA = ('Barack Obama', 'Democratic')
TRUMP = ('Donald J. Trump', 'Republican')
# Fictional judges: id, last, first, and middle names, sex, race or
# ethnicity, year of birth, type of court, court, appointing president, and
# the dates of commission and of senior status.
JUDGES: list[tuple[Any, ...]] = [
    (101, 'Lynch', 'Mary', 'Ann', 'Female', 'White', 1946, APPEALS, FIRST, CLINTON, '1995-03-17', ''),
    (102, 'Howard', 'John', 'Q.', 'Male', 'White', 1955, APPEALS, FIRST, BUSH, '2002-04-23', ''),
    (103, 'Thompson', 'Rita', 'Mae', 'Female', 'African American', 1951, APPEALS, FIRST, OBAMA, '2010-03-17', ''),
    (104, 'Stone', 'Nora', 'H.', 'Female', 'White', 1941, APPEALS, FIRST, BUSH, '2003-04-30', '2012-04-16'),
    (105, 'Baron', 'Dale', 'J.', 'Male', 'White', 1967, APPEALS, FIRST, OBAMA, '2014-05-20', ''),
    (106, 'Kay', 'William', 'J.', 'Male', 'White', 1953, APPEALS, FIRST, OBAMA, '2013-02-13', ''),
    (107, 'Woods', 'Dana', 'Paul', 'Male', 'Hispanic', 1947, DISTRICT, 'U.S. District Court for the District of Massachusetts', CLINTON, '1996-06-16', ''),
    (201, 'Graber', 'Susan', 'P.', 'Female', 'White', 1949, APPEALS, NINTH, CLINTON, '1998-03-19', ''),
    (202, 'Bea', 'Carlos', 'T.', 'Male', 'Hispanic', 1934, APPEALS, NINTH, BUSH, '2003-10-01', ''),
    (203, 'Ikuta', 'Sandra', 'S.', 'Female', 'Asian American', 1954, APPEALS, NINTH, BUSH, '2006-06-23', ''),
    (204, 'Hurwitz', 'Andrew', 'D.', 'Male', 'White', 1947, APPEALS, NINTH, OBAMA, '2012-06-27', ''),
    (205, 'Nelson', 'Ryan', 'D.', 'Male', 'White', 1973, APPEALS, NINTH, OBAMA, '2012-10-18', ''),
    (206, 'Smith', 'Milton', 'Dale', 'Male', 'White', 1942, APPEALS, NINTH, BUSH, '2006-05-18', ''),
    (207, 'Smith', 'Norman', 'Roy', 'Male', 'White', 1949, APPEALS, NINTH, BUSH, '2007-03-19', '')]
BENCHES: dict[str, list[str]] = {
    'ca1': ['Lynch', 'Howard', 'Thompson', 'Stone', 'Baron', 'Kay'],
    'ca9': ['Graber', 'Bea', 'Ikuta', 'Hurwitz', 'Nelson']}
CAREERS: list[tuple[int, str]] = [
    (101, 'Assistant attorney general, State of Massachusetts, 1973-1974'),
    (102, 'Assistant U.S. attorney, District of New Hampshire, 1981-1987'),
    (103, 'Assistant public defender, Rhode Island, 1976-1979'),
    (204, 'Law clerk, Hon. B. Justice, Supreme Court of the United States, 1972-1973'),
    (205, 'Professor, University of the West School of Law, 2005-2010')]
COURT_NAMES: dict[str, str] = {
    'ca1': 'Court of Appeals for the First Circuit',
    'ca9': 'Court of Appeals for the Ninth Circuit'}
ADDRESSES: dict[str, str] = {
    'ca1': 'http://media.ca1.uscourts.gov/pdf.opinions/{number}P-01A.pdf',
    'ca9': 'https://cdn.ca9.uscourts.gov/datastore/opinions/2015/06/15/{number}.pdf'}


@pytest.fixture(autouse = True)
def restore_library() -> Iterator[None]:
    """Removes the classes that a test adds to the library."""
    saved = copy.deepcopy(chrisjen.library.contents)
    yield
    chrisjen.library.contents.clear()
    chrisjen.library.contents.update(saved)


@pytest.fixture(autouse = True)
def private_folders(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch) -> None:
    """Keeps tests away from the user's real key, bulk files, and roster."""
    monkeypatch.delenv(courtpy.options._ENV_API_KEY, raising = False)
    monkeypatch.setenv(courtpy.options._ENV_CONFIG, str(tmp_path / 'config'))
    monkeypatch.setenv(courtpy.options._ENV_DATA, str(tmp_path / 'courtpy'))
    monkeypatch.setattr(courtpy.secrets, '_keyring', lambda: None)


def fjc_tables() -> dict[str, pd.DataFrame]:
    """Returns the fictional judges as the Federal Judicial Center's files."""
    service, people = [], []
    for nid, last, first, middle, sex, race, born, kind, court, appointer, began, senior in JUDGES:
        president, party = appointer
        service.append({
            'nid': nid, 'Sequence': 1, 'Judge Name': f'{last}, {first} {middle}',
            'Court Type': kind, 'Court Name': court,
            'Appointing President': president,
            'Party of Appointing President': party,
            'ABA Rating': 'Well Qualified', 'Recess Appointment Date': '',
            'Senate Vote Type': 'Voice', 'Ayes/Nays': '',
            'Commission Date': began, 'Senior Status Date': senior,
            'Termination Date': ''})
        people.append({
            'nid': nid, 'Last Name': last, 'First Name': first,
            'Middle Name': middle, 'Suffix': '', 'Birth Year': born,
            'Gender': sex, 'Race or Ethnicity': race})
    return {
        'service': pd.DataFrame(service),
        'demographics': pd.DataFrame(people),
        'career': pd.DataFrame(CAREERS, columns = ['nid', 'Professional Career'])}


@pytest.fixture
def roster() -> courtpy.judges.Roster:
    """Returns a roster of the fictional judges, saved where courtpy looks."""
    made = courtpy.judges.Roster(courtpy.judges.build_roster(**fjc_tables()))
    made.save()
    return made


def make_case(
    number: int,
    court: str,
    panel: list[str],
    *,
    year: int = 2015,
    won: bool = False,
    dissenter: str | None = None,
    name: str = 'United States v. Doe',
    issue: str = 'possession of a firearm') -> dict[str, Any]:
    """Returns a fictional criminal appeal, as courtpy saves a case."""
    decision = 'VACATED AND REMANDED.' if won else 'AFFIRMED.'
    text = (
        f'<p>United States Court of Appeals For the {COURT_NAMES[court].split()[-2]} Circuit</p>'
        f'<p>No. 14-{number:04d}</p>'
        '<p>UNITED STATES OF AMERICA, Plaintiff-Appellee, v. JOHN DOE, Defendant-Appellant.</p>'
        '<p>Appeal from the United States District Court</p>'
        f'<p>Before {panel[0].upper()}, {panel[1].upper()}, and {panel[2].upper()}, Circuit Judges.</p>'
        f'<p>{panel[0].upper()}, Circuit Judge. John Doe appeals his conviction for {issue}. '
        'An Assistant United States Attorney argued for the government. '
        f'We review de novo.</p><p>{decision}</p>')
    opinions = [{
        'id': number * 10, 'cluster_id': number, 'type': '010combined',
        'author_id': None, 'author_str': panel[0], 'per_curiam': False,
        'joined_by_str': '',
        'download_url': ADDRESSES[court].format(number = f'14-{number:04d}'),
        'html_with_citations': text}]
    if dissenter:
        opinions.append({
            'id': number * 10 + 1, 'cluster_id': number, 'type': '040dissent',
            'author_id': None, 'author_str': dissenter, 'per_curiam': False,
            'joined_by_str': '', 'download_url': '',
            'html_with_citations': f'<p>{dissenter.upper()}, Circuit Judge, dissenting. I would not.</p>'})
    return {
        'source': 'court_listener',
        'court': {'id': court, 'full_name': COURT_NAMES[court], 'jurisdiction': 'F'},
        'cluster': {
            'id': number, 'docket_id': number + 5000, 'case_name': name,
            'case_name_full': '', 'date_filed': f'{year}-06-15', 'judges': '',
            'precedential_status': 'Published', 'disposition': '',
            'attorneys': '', 'citation_count': 0},
        'docket': None,
        'citations': [],
        'opinions': opinions}


def write_cases(
    folder: pathlib.Path,
    count: int = 240,
    *,
    seed: int = 7,
    lean: dict[str, float] | None = None) -> pathlib.Path:
    """Saves fictional criminal appeals whose judges are drawn at random.

    A defendant's chance of winning is a tenth, plus the "lean" of each judge
    on the panel.

    """
    rng = random.Random(seed)
    lean = lean or {}
    for number in range(1, count + 1):
        court = rng.choice(list(BENCHES))
        panel = rng.sample(BENCHES[court], 3)
        chance = 0.1 + sum(lean.get(judge, 0.0) for judge in panel)
        won = rng.random() < chance
        case = make_case(
            number, court, panel, year = rng.choice([2014, 2015, 2016]),
            won = won,
            name = f'United States v. Doe {number}',
            dissenter = panel[2] if rng.random() < 0.1 else None,
            issue = rng.choice([
                'possession of a firearm', 'conspiracy to distribute cocaine',
                'wire fraud', 'bank robbery']))
        path = courtpy.courtlistener.case_path(folder, court, number)
        courtpy.courtlistener.save_case(path, case)
    return folder


def write_bulk(
    folder: pathlib.Path,
    kind: str,
    header: list[str],
    rows: list[list[Any]]) -> pathlib.Path:
    """Writes a bulk file the way PostgreSQL does, with backslash escapes."""
    text = io.StringIO()
    writer = csv.writer(
        text, escapechar = '\\', doublequote = False, lineterminator = '\n')
    writer.writerow(header)
    writer.writerows(rows)
    folder.mkdir(parents = True, exist_ok = True)
    path = folder / f'{kind}-{DATE}.csv.bz2'
    path.write_bytes(bz2.compress(text.getvalue().encode('utf-8')))
    return path


class Response:
    """A response like those from `requests`."""

    def __init__(self, content: bytes = b'', headers: dict[str, str] | None = None) -> None:
        self.content = content
        self.headers = headers or {}
        self.status_code = 200

    def raise_for_status(self) -> None:
        """Does nothing, since every response of the bucket succeeds."""


class LocalBucket:
    """A session that serves the bulk files in a folder and lists them."""

    def __init__(self, folder: pathlib.Path) -> None:
        self.folder = folder
        self.headers: dict[str, str] = {}
        self.requested: list[str] = []
        self.streamed: list[str] = []

    def head(self, url: str, **kwargs: Any) -> Response:
        """Returns the size of a bulk file."""
        self.requested.append(url.rsplit('/', 1)[-1])
        path = self.folder / url.rsplit('/', 1)[-1]
        return Response(headers = {'Content-Length': str(path.stat().st_size)})

    def get(self, url: str, params: dict[str, Any] | None = None, **kwargs: Any) -> Response:
        """Lists the bulk files whose names start with a prefix, or sends one."""
        if url.endswith('.csv.bz2'):
            self.streamed.append(url.rsplit('/', 1)[-1])
            response = Response()
            response.raw = (self.folder / url.rsplit('/', 1)[-1]).open('rb')
            response.close = response.raw.close
            return response
        prefix = (params or {}).get('prefix', '').removeprefix('bulk-data/')
        keys = ''.join(
            f'<Contents><Key>bulk-data/{p.name}</Key></Contents>'
            for p in sorted(self.folder.glob('*.bz2')) if p.name.startswith(prefix))
        return Response((
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
            f'{keys}<IsTruncated>false</IsTruncated></ListBucketResult>').encode())
