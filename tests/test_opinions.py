"""Tests the opinions module."""

from __future__ import annotations

import json
import pathlib

import amos
import courtpy
import pytest
from conftest import DATE, LocalBucket, write_bulk

from appellate_roulette import opinions

FIRST = (
    'United States Court of Appeals For the First Circuit No. 14-1234 UNITED '
    'STATES OF AMERICA, Appellee, v. JOHN DOE, Defendant, Appellant.')
CLUSTERS = [
    # id, judges, date filed, name, full name, status, docket, source, headmatter
    [1, '', '2015-03-04', 'United States v. Doe', '', 'Published', 10, 'C', ''],
    [2, '', '2016-05-05', 'Smith v. Jones', '', 'Unpublished', 20, 'C', ''],
    [3, 'Katzmann', '2015-02-02', 'United States v. Roe', '', 'Published', 30, 'U',
     '<parties>UNITED STATES v. ROE</parties><court>United States Court of Appeals, Second Circuit.</court>'],
    [4, '', '2015-06-06', 'State v. Poe', '', 'Published', 40, 'C', ''],
    [5, '', '2015-07-07', 'In re Debtor', '', 'Published', 50, 'C', ''],
    [6, '', '2015-08-08', 'In re Farmer', '', 'Published', 60, 'C', ''],
    [7, '', '2009-12-31', 'United States v. Old', '', 'Published', 70, 'C', ''],
    [8, '', '2015-09-09', 'United States v. Remand', '', 'Published', 80, 'C', ''],
    [9, '', '2015-10-10', 'In re Bankrupt', '', 'Published', 90, 'C', ''],
    [10, '', '2015-11-11', 'Apple v. Pear', '', 'Published', 100, 'C', ''],
    [11, '', '2015-12-12', '', '', 'Published', 110, 'C', ''],
    [12, '', '2015-04-04', 'United States v. Lost', '', 'Published', 120, 'U', ''],
    [13, '', '2015-05-05', 'Doe v. United States', '', 'Published', 130, 'U', '']]
OPINIONS = [
    # id, author, per curiam, type, address, plain text, html with citations, harvard xml, cluster
    [11, 'Lynch', 'f', '010combined', 'http://media.ca1.uscourts.gov/pdf.opinions/14-1234P-01A.pdf',
     '', f'<pre>{FIRST} We said "no" and\nwe affirm.</pre>', '', 1],
    [21, '', 't', '010combined', 'https://cdn.ca9.uscourts.gov/datastore/memoranda/2016/05/05/15-10001.pdf', (
        'NOT FOR PUBLICATION FILED UNITED STATES COURT OF APPEALS MAY 5 2016 MOLLY C. DWYER, CLERK '
        'U.S. COURT OF APPEALS FOR THE NINTH CIRCUIT MARY SMITH, Plaintiff-Appellant, v. JONES'), '', '', 2],
    [31, 'Katzmann', 'f', '020lead', '', '', '', '<opinion><p>KATZMANN, Chief Judge: We vacate.</p></opinion>', 3],
    [41, '', 'f', '010combined', 'https://www.txcourts.gov/media/1.pdf', 'IN THE SUPREME COURT OF TEXAS', '', '', 4],
    [51, '', 'f', '010combined', 'https://cdn.ca9.uscourts.gov/datastore/bap/2015/07/07/x.pdf', 'Opinion.', '', '', 5],
    [61, '', 'f', '010combined', 'https://ecf.ca8.uscourts.gov/opndir/15/08/156012P.pdf',
     'United States Bankruptcy Appellate Panel For the Eighth Circuit No. 15-6012 In re Farmer', '', '', 6],
    [71, '', 'f', '010combined', 'http://media.ca1.uscourts.gov/pdf.opinions/09-1.pdf', FIRST, '', '', 7],
    [81, '', 'f', '010combined', '', (
        'UNITED STATES DISTRICT COURT DISTRICT OF MAINE On remand from the United States Court of '
        'Appeals for the First Circuit, the court resentences.'), '', '', 8],
    [91, '', 'f', '010combined', 'http://media.ca1.uscourts.gov/pdf.opinions/15-9001P-01A.pdf', (
        'United States Court of Appeals For the First Circuit No. 15-9001 IN RE BANKRUPT, Debtor. '
        'APPEAL FROM THE BANKRUPTCY APPELLATE PANEL FOR THE FIRST CIRCUIT'), '', '', 9],
    [101, '', 'f', '010combined', 'http://www.cafc.uscourts.gov/sites/default/files/15-1001.pdf',
     'United States Court of Appeals for the Federal Circuit', '', '', 10],
    [12, 'Howard', 'f', '040dissent', '', 'HOWARD, Circuit Judge, dissenting. I would reverse.', '', '', 1],
    [111, '', 'f', '010combined', 'https://www.ca1.uscourts.gov/pdf.opinions/15-2222U.pdf', FIRST, '', '', 11],
    [121, '', 't', '020lead', '', (
        'UNITED STATES COURT OF APPEALS FOR THE FOURTH CIRCUIT PER CURIAM: Lost appeals his '
        'sentence. We affirm.'), '', '', 12],
    [131, '', 'f', '020lead', '', (
        'Petition for writ of certiorari to the United States Court of Appeals for the Fifth '
        'Circuit denied.'), '', '', 13]]


@pytest.fixture
def bucket(tmp_path: pathlib.Path) -> pathlib.Path:
    """Returns a folder with the two bulk files of opinions, and no others."""
    folder = tmp_path / 'bulk'
    write_bulk(folder, 'opinion-clusters', [
        'id', 'judges', 'date_filed', 'case_name', 'case_name_full',
        'precedential_status', 'docket_id', 'source', 'headmatter',
        'date_created', 'citation_count', 'attorneys'], [
            [*row, '2020-01-01 10:00:00+00', 0, ''] for row in CLUSTERS])
    write_bulk(folder, 'opinions', [
        'id', 'author_str', 'per_curiam', 'type', 'download_url',
        'plain_text', 'html_with_citations', 'xml_harvard', 'cluster_id'],
        OPINIONS)
    return folder


def data(bucket: pathlib.Path, **kwargs: object) -> opinions.OpinionData:
    """Returns the bulk data in `bucket`."""
    return opinions.OpinionData(
        folder = bucket, date = DATE, session = LocalBucket(bucket), **kwargs)


def saved(folder: pathlib.Path) -> dict[str, list[int]]:
    """Returns the ids of the saved cases of each court."""
    return {
        court.name: sorted(int(path.stem) for path in court.glob('*.json'))
        for court in sorted(folder.iterdir()) if court.is_dir()}


def extract(
    source: opinions.OpinionData,
    folder: pathlib.Path,
    courts: str | list[str],
    start: str | None = None,
    end: str | None = None,
    **kwargs: object) -> dict[str, list[int]]:
    """Extracts cases to a folder and returns the ids saved for each court."""
    source.extract(courts, start, end, folder, **kwargs)
    return saved(folder)


def test_loader_is_in_the_library() -> None:
    assert amos.library.classify('load_opinions') == 'case_loader'
    assert issubclass(opinions.LoadOpinions, courtpy.loaders.LoadCourtListener)


@pytest.mark.parametrize(('evidence', 'court'), [
    ({'address': 'http://media.ca1.uscourts.gov/pdf.opinions/14-1234P-01A.pdf'}, 'ca1'),
    ({'address': 'https://www.ca2.uscourts.gov/decisions/isysquery/1/doc/14-1.pdf'}, 'ca2'),
    ({'address': 'https://www.govinfo.gov/content/pkg/USCOURTS-ca4-24-01234/pdf/USCOURTS-ca4-24-01234-0.pdf'}, 'ca4'),
    ({'address': 'http://www.opn.ca6.uscourts.gov/opinions.pdf/15a0001p-06.pdf'}, 'ca6'),
    ({'address': 'https://www.ca10.uscourts.gov/opinions/14/14-1234.pdf'}, 'ca10'),
    ({'address': 'https://www.cadc.uscourts.gov/internet/opinions.nsf/x/$file/14-1234.pdf'}, 'cadc'),
    ({'address': 'http://www.cafc.uscourts.gov/sites/default/files/15-1001.pdf'}, 'cafc'),
    # The website of any other court, though the name of a bankruptcy
    # court's starts the same way.
    ({'address': 'http://www.cacb.uscourts.gov/opinions/x.pdf'}, 'other'),
    ({'address': 'https://www.govinfo.gov/content/pkg/USCOURTS-cand-3_15-cv-1/pdf/x.pdf'}, 'other'),
    ({'address': 'https://www.txcourts.gov/media/1.pdf'}, 'other'),
    # Bankruptcy appellate panels: a website or folder of their own, a "b"
    # in the name of a file of the Sixth Circuit, or their name at the top
    # of an opinion on the website of their circuit.
    ({'address': 'https://cdn.ca9.uscourts.gov/datastore/bap/2015/07/07/x.pdf'}, 'other'),
    ({'address': 'https://www.bap10.uscourts.gov/opinions/x.pdf'}, 'other'),
    ({'address': 'http://www.opn.ca6.uscourts.gov/opinions.pdf/21b0001n-06.pdf'}, 'other'),
    ({'address': 'https://ecf.ca8.uscourts.gov/opndir/15/08/156012P.pdf', 'opening': OPINIONS[5][5]}, 'other'),
    ({'address': 'http://www.opn.ca6.uscourts.gov/opinions.pdf/x.pdf', 'opening': (
        'RECOMMENDED FOR PUBLICATION File Name: 23b0001p.06 BANKRUPTCY APPELLATE PANEL OF THE '
        'SIXTH CIRCUIT In re: DEBTOR')}, 'other'),
    ({'address': 'http://www.opn.ca6.uscourts.gov/opinions.pdf/x.pdf', 'opening': (
        'By order of the Bankruptcy Appellate Panel, the precedential effect of this decision is '
        'limited to the case and parties')}, 'other'),
    # A court of appeals that reviews a panel names itself first, or only
    # mentions the panel.
    ({'address': 'http://media.ca1.uscourts.gov/pdf.opinions/15-9001P-01A.pdf', 'opening': OPINIONS[8][5]}, 'ca1'),
    ({'address': 'http://www.ca10.uscourts.gov/opinions/12/12-1087.pdf', 'opening': (
        'ORDER AND JUDGMENT HOLMES, Circuit Judge. George Castro appeals pro se from a Bankruptcy '
        'Appellate Panel (BAP) decision that affirmed the bankruptcy court.')}, 'ca10'),
    ({'address': 'http://www.ca10.uscourts.gov/opinions/10/10-3268.pdf', 'opening': (
        'Fuller appeals the dismissal of the appeal she filed with the Bankruptcy Appellate Panel '
        'of the Tenth Circuit (BAP).')}, 'ca10'),
    # The headmatter of a case names its court.
    ({'headmatter': 'UNITED STATES v. ROE United States Court of Appeals, Second Circuit.'}, 'ca2'),
    ({'headmatter': 'DOE v. ROE. No. 19-4001. United States Court of Appeals for the Fourth Circuit.'}, 'ca4'),
    ({'headmatter': 'In re DOE. No. 10-5. United States Court of Appeals, District of Columbia Circuit.'}, 'cadc'),
    ({'headmatter': 'DOE v. ROE U.S. Court of Appeals for the D.C. Circuit'}, 'cadc'),
    # A clerk's stamp comes between the court and its circuit.
    ({'headmatter': 'DOE v. ROE FILED United States Court of Appeals PUBLISH Tenth Circuit'}, 'ca10'),
    # Where an opinion came from is believed before the headmatter.
    ({'address': 'https://www.ca5.uscourts.gov/x.pdf', 'headmatter': 'United States Court of Appeals, Second Circuit.'}, 'ca5'),
    # Other courts name the courts of appeals that they review, answer, or
    # are reviewed by.
    ({'headmatter': 'DOLAN v. UNITED STATES CERTIORARI TO THE UNITED STATES COURT OF APPEALS FOR THE TENTH CIRCUIT'}, None),
    ({'headmatter': (
        'RIVERA v. LEW. Supreme Court of Texas. On certified question from the United States Court '
        'of Appeals for the Fifth Circuit.')}, None),
    ({'headmatter': (
        'UNITED STATES v. DOE. United States District Court, D. Maine. On remand from the United '
        'States Court of Appeals for the First Circuit.')}, None),
    ({'headmatter': 'In re DOE. United States Bankruptcy Appellate Panel of the Ninth Circuit.'}, None),
    ({'headmatter': 'United States Court of Appeals for the Armed Forces'}, None),
    ({'address': 'https://www.supremecourt.gov/opinions/09pdf/09-367.pdf', 'headmatter': (
        'DOLAN v. UNITED STATES United States Court of Appeals, Tenth Circuit')}, 'other'),
    # The opening of an opinion is not believed: it names the court below
    # far more often than its own.
    ({'opening': FIRST}, None),
    ({'opening': OPINIONS[12][5]}, None),
    ({'opening': OPINIONS[13][5]}, None),
    ({'opening': OPINIONS[7][5]}, None),
    ({}, None)])
def test_find_court(evidence: dict[str, str], court: str | None) -> None:
    book = opinions.OpinionData()._book()
    assert opinions.find_court(book, **evidence) == court


def test_extract(bucket: pathlib.Path, tmp_path: pathlib.Path) -> None:
    source = data(bucket)
    output = tmp_path / 'cases'
    paths = source.extract('federal_circuits', '2010-01-01', None, output)
    # Case 3 is found by its headmatter, and the others by where their
    # opinions came from. The state court, the bankruptcy panels, the
    # district court, the Federal Circuit, and the case before 2010 are
    # left out. So are cases 12 and 13, which have neither an address nor
    # headmatter: one is of a court of appeals and one is an order of the
    # Supreme Court, and their openings do not tell them apart.
    assert saved(output) == {'ca1': [1, 9, 11], 'ca2': [3], 'ca9': [2]}
    assert sorted(paths) == sorted(output.rglob('*.json'))
    record = json.loads((output / 'ca1' / '1.json').read_text(encoding = 'utf-8'))
    assert record['source'] == 'court_listener'
    assert record['bulk_date'] == DATE
    assert record['court'] == {
        'id': 'ca1', 'full_name': 'Court of Appeals for the First Circuit',
        'short_name': 'First Circuit', 'citation_string': '1st Cir.',
        'jurisdiction': 'F'}
    # The decision and its opinions are saved, and nothing else.
    assert record['docket'] is None and record['citations'] == []
    assert record['cluster'] == {
        'id': 1, 'docket_id': 10, 'case_name': 'United States v. Doe',
        'case_name_full': None, 'date_filed': '2015-03-04', 'judges': None,
        'precedential_status': 'Published', 'attorneys': None,
        'citation_count': 0, 'source': 'C'}
    assert [o['id'] for o in record['opinions']] == [11, 12]
    assert record['opinions'][0]['html_with_citations'].endswith('We said "no" and\nwe affirm.</pre>')
    assert record['opinions'][1]['type'] == '040dissent'
    harvard = json.loads((output / 'ca2' / '3.json').read_text(encoding = 'utf-8'))
    assert harvard['court']['id'] == 'ca2'
    assert 'headmatter' not in harvard['cluster'] and '_headmatter' not in harvard['cluster']
    assert harvard['opinions'][0]['xml_harvard'].startswith('<opinion>')


def test_only_the_files_of_opinions_are_read(bucket: pathlib.Path, tmp_path: pathlib.Path) -> None:
    # The folder has no dockets, citations, or courts files at all.
    session = LocalBucket(bucket)
    source = opinions.OpinionData(folder = bucket, session = session)
    assert source.resolve_date() == DATE
    source.extract('ca1', '2010-01-01', None, tmp_path / 'cases')
    assert set(session.requested) == {
        f'opinion-clusters-{DATE}.csv.bz2', f'opinions-{DATE}.csv.bz2'}
    with pytest.raises(LookupError, match = 'every file'):
        courtpy.BulkData(folder = bucket, session = session).resolve_date()
    empty = tmp_path / 'empty'
    empty.mkdir()
    with pytest.raises(LookupError, match = 'files of opinions'):
        opinions.OpinionData(folder = empty, session = LocalBucket(empty)).resolve_date()


def test_extract_courts_dates_and_parties(bucket: pathlib.Path, tmp_path: pathlib.Path) -> None:
    source = data(bucket)
    assert extract(source, tmp_path / 'a', 'federal_appellate', '2015-01-01', '2015-12-31') == {
        'ca1': [1, 9, 11], 'ca2': [3], 'cafc': [10]}
    assert extract(source, tmp_path / 'b', ['ca9', 'ca2']) == {'ca2': [3], 'ca9': [2]}
    # Only the cases that name the United States (and one with no name).
    assert extract(source, tmp_path / 'c', 'federal_circuits', parties = 'United States') == {
        'ca1': [1, 7, 11], 'ca2': [3]}
    assert extract(source, tmp_path / 'd', 'federal_circuits', parties = 'smith|bankrupt') == {
        'ca1': [9, 11], 'ca9': [2]}
    with pytest.raises(ValueError, match = 'scotus'):
        source.extract(['ca1', 'scotus'], folder = tmp_path / 'e')


def test_extract_resumes(bucket: pathlib.Path, tmp_path: pathlib.Path) -> None:
    source = data(bucket)
    output = tmp_path / 'cases'
    assert len(source.extract('ca1', '2010-01-01', folder = output)) == 3
    (output / 'ca1' / '9.json').unlink()
    # Cases that the folder has are not saved again unless asked.
    assert source.extract('ca1', '2010-01-01', folder = output) == [output / 'ca1' / '9.json']
    assert len(source.extract('ca1', '2010-01-01', folder = output, overwrite = True)) == 3
    assert saved(output) == {'ca1': [1, 9, 11]}
    limited = source.extract('federal_circuits', '2010-01-01', folder = tmp_path / 'few', max_cases = 2)
    assert len(limited) == 2


def test_readers_agree(
    bucket: pathlib.Path,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch) -> None:
    # The files are read with pyarrow and indexed_bzip2, or without either,
    # or as they arrive from CourtListener, and the cases are the same.
    data(bucket, processes = 2).extract('federal_appellate', folder = tmp_path / 'fast')
    session = LocalBucket(bucket)
    opinions.OpinionData(folder = tmp_path / 'none', date = DATE, session = session, stream = True).extract(
        'federal_appellate', folder = tmp_path / 'streamed')
    assert set(session.streamed) == {f'opinion-clusters-{DATE}.csv.bz2', f'opinions-{DATE}.csv.bz2'}
    assert not (tmp_path / 'none').exists()
    monkeypatch.setattr(opinions, 'pa', None)
    data(bucket).extract('federal_appellate', folder = tmp_path / 'plain')
    monkeypatch.setattr(opinions, 'indexed_bzip2', None)
    monkeypatch.setattr(opinions, '_CHUNK', 3)
    data(bucket).extract('federal_appellate', folder = tmp_path / 'slow')
    names = sorted(p.relative_to(tmp_path / 'fast') for p in (tmp_path / 'fast').rglob('*.json'))
    assert len(names) == 7
    for name in names:
        expected = (tmp_path / 'fast' / name).read_text(encoding = 'utf-8')
        for other in ('streamed', 'plain', 'slow'):
            assert (tmp_path / other / name).read_text(encoding = 'utf-8') == expected


def test_rules_can_be_changed(bucket: pathlib.Path, tmp_path: pathlib.Path) -> None:
    rules = tmp_path / 'courts.csv'
    rules.write_text(
        'target,variable,kind,pattern,value,ignorecase,dotall,note\n'
        'address,court,label,ca1\\.uscourts,ca1,TRUE,FALSE,\n', encoding = 'utf-8')
    source = data(bucket, rulebook = rules)
    assert extract(source, tmp_path / 'cases', 'federal_circuits', '2010-01-01') == {
        'ca1': [1, 9, 11]}


def test_load_opinions(
    bucket: pathlib.Path,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(courtpy.bulk.requests, 'Session', lambda: LocalBucket(bucket))
    dataset = opinions.LoadOpinions().apply(
        source = tmp_path / 'cases', download = 'opinions',
        courts = 'federal_circuits', start_date = '2010-01-01',
        parties = 'United States', bulk_folder = str(bucket),
        bulk_date = DATE, label = 'outcome_reversal')
    table = dataset.data
    assert sorted(table.index) == ['1', '11', '3']
    assert [e['technique'] for e in dataset.history] == [
        'load_opinions', 'code_parties', 'code_case_type', 'code_outcome']
    assert table.loc['1', 'court'] == 'ca1' and table.loc['1', 'court_num'] == 1
    assert table.loc['3', 'court_num'] == 2 and table.loc['3', 'year'] == 2015
    assert table.loc['1', 'published'] and table.loc['1', 'dissents'] == 1
    assert not table.loc['1', 'outcome_reversal'] and table.loc['3', 'outcome_reversal']
    # Without "opinions", it is courtpy's loader of the cases in the folder.
    again = opinions.LoadOpinions().apply(source = tmp_path / 'cases', coders = 'none')
    assert len(again.data) == 3
