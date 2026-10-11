"""Collects the opinions of the federal courts of appeals from CourtListener.

CourtListener publishes its whole database as bulk files every three months.
courtpy's `BulkData` reads five of them, because CourtListener records the
court of each case with its docket: the dockets file (about 5 GB, with a row
for every case that CourtListener knows of, most of which have no opinion),
the citations, and the courts, as well as the two files that hold the
opinions. `OpinionData` reads only those two:

| File | Size (2026) | Holds |
| --- | --- | --- |
| opinion-clusters | about 2.5 GB | Each decision's parties, judges, date, and status. |
| opinions | about 55 GB | The text of each opinion. |

Without the dockets, the court of each opinion is found from the opinion
itself, by the rules in "instructions/courts.csv" (which can be read and
changed in a spreadsheet, like courtpy's rules): the website that the
opinion was collected from, or else the court that the headmatter of its
case names. Only the federal courts of appeals can be found this way,
because CourtListener collects their opinions from their own websites. An
opinion whose court cannot be found is left out.

Measured against the dockets of the bulk data of 2026-09-30, for the
decisions of the thirteen courts filed since 2010, the rules find 92.1% of
the 375,994 decisions (and every one filed since 2020), put none in the
wrong court, and take 4 opinions of other courts for a court of appeals.
The decisions that they do not find are those that CourtListener has only
from the Harvard Law School Library's scans of the reporters (8 to 17% of
each year from 2010 to 2018), which come with neither an address nor
headmatter. Most of them repeat a decision that was also collected from a
court's website, and is found. The opening words of an opinion are not
used to find its court, because they name the court below far more often
than its own (as an order of the Supreme Court that denies certiorari
does). The cases that are left out can be added to the same folder with
courtpy, which skips the cases that are already there: from the API
(`courtpy download api`, with a key) or from the bulk data with its
dockets (`courtpy download bulk`).

Each case is saved in the form that courtpy's parser reads (see
`courtpy.courtlistener`), with the decision, the opinions, and nothing else:
no docket and no citations.

The files are read with pyarrow and decompressed with indexed_bzip2, which
use every core of the computer, so reading them takes about half an hour
rather than several. Without those packages, the files are read as courtpy
reads them.

`load_opinions` is an `amos` loader, which is added to the `amos` library as
soon as appellate_roulette is imported. It is courtpy's `load_court_listener`
with one more way to download: "opinions".

Contents:
    COURTS: what CourtListener records about each federal court of appeals,
        by its id.
    LoadOpinions: collects, parses, and codes the opinions of the federal
        courts of appeals.
    OpinionData: extracts cases from the two bulk files that hold opinions.
    find_court: returns the federal court of appeals that decided an opinion.
    logger: the module's logger, which reports the progress of reading the
        files.
    _BLOCK: how many bytes of a bulk file pyarrow reads at a time, which
        must be more than the longest row.
    _CHUNK: how many rows of a bulk file are read at a time without pyarrow.
    _CLUSTER_KEPT: the columns of the opinion clusters file that are saved
        with each case, which are those that courtpy's parser reads.
    _INSTRUCTIONS: the folder of the rules that find courts.
    _KINDS: the bulk files that `OpinionData` uses, in the order `extract`
        reads them.
    _NAME_LENGTH: how many characters at the end of the text that names a
        court are kept, which is more than the longest name of a court.
    _NAMES: pattern for the names that CourtListener gives the United States
        as a party.
    _OPENING: how many characters of an opinion or of the headmatter of a
        case (before and after its markup is removed) the rules read.
    _OTHER: the value that the rules give an opinion of a court that is not
        a court of appeals.
    _Part: a part of a bulk file: the values of one column, and a function
        that returns chosen rows.
    _SPACES: pattern for any run of whitespace.
    _TAGS: pattern for a tag of HTML or XML.
    _court_named: returns the words of a headmatter that say which court
        decided a case.
    _opening: returns the start of an opinion as plain text.
    _party_pattern: returns the pattern that the names of the cases to save
        must match.
    _rows_arrow: returns chosen rows of a part of a bulk file that pyarrow
        read.
    _rows_csv: returns chosen rows of a part of a bulk file that Python
        read.
    _saved: returns the ids of the cases that a folder already holds.

"""

from __future__ import annotations

import array
import bz2
import contextlib
import csv
import dataclasses
import functools
import importlib.resources
import io
import itertools
import json
import logging
import os
import pathlib
import re
import tempfile
from collections.abc import Callable, Iterable, Iterator, Sequence
from typing import IO, Any, TypeAlias

import pandas as pd
from courtpy import bulk, courtlistener, loaders, options, rules, utilities

try:
    import indexed_bzip2
except ImportError:  # pragma: no cover
    indexed_bzip2 = None
try:
    import pyarrow as pa
    from pyarrow import csv as arrow_csv
except ImportError:  # pragma: no cover
    pa = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)
COURTS: dict[str, dict[str, str]] = {
    court: {
        'id': court,
        'full_name': f'Court of Appeals for the {name} Circuit',
        'short_name': f'{name} Circuit',
        'citation_string': f'{citation} Cir.',
        'jurisdiction': 'F'}
    for court, name, citation in (
        ('ca1', 'First', '1st'), ('ca2', 'Second', '2d'),
        ('ca3', 'Third', '3rd'), ('ca4', 'Fourth', '4th'),
        ('ca5', 'Fifth', '5th'), ('ca6', 'Sixth', '6th'),
        ('ca7', 'Seventh', '7th'), ('ca8', 'Eighth', '8th'),
        ('ca9', 'Ninth', '9th'), ('ca10', 'Tenth', '10th'),
        ('ca11', 'Eleventh', '11th'), ('cadc', 'D.C.', 'D.C.'),
        ('cafc', 'Federal', 'Fed.'))}
_BLOCK: int = 256 * 1024 * 1024
_CHUNK: int = 2000
_CLUSTER_KEPT: tuple[str, ...] = (
    'id', 'docket_id', 'case_name', 'case_name_short', 'case_name_full',
    'date_filed', 'judges', 'precedential_status', 'disposition',
    'procedural_history', 'history', 'posture', 'syllabus', 'attorneys',
    'nature_of_suit', 'citation_count', 'source')
_INSTRUCTIONS: pathlib.Path = pathlib.Path(
    str(importlib.resources.files('appellate_roulette'))) / 'instructions'
_KINDS: tuple[str, ...] = ('opinion-clusters', 'opinions')
_NAME_LENGTH: int = 200
_NAMES: re.Pattern[str] = re.compile(
    r'\b(?:United\s+States|U\.\s?S\.(?:\s?A\.)?|USA|US)(?![\w.])',
    re.IGNORECASE)
_OPENING: int = 3000
_OTHER: str = 'other'
_Part: TypeAlias = tuple[
    list[str], Callable[[Sequence[int]], list[dict[str, str]]]]
_SPACES: re.Pattern[str] = re.compile(r'\s+')
_TAGS: re.Pattern[str] = re.compile(r'<[^>]+>')


@dataclasses.dataclass
class OpinionData(bulk.BulkData):
    """Extracts cases from the two bulk files that hold opinions.

    It is a `courtpy.BulkData` that never reads the dockets, citations, or
    courts files, and that reads the two others with every core of the
    computer. It takes the arguments of `courtpy.BulkData` ("folder", where
    the downloaded bulk files are kept, which is courtpy's own folder unless
    another is given, so that files that either one downloaded are used by
    both; "date", the date of the files to use, which is the newest unless
    another is given; "stream", whether to read the files straight from
    CourtListener instead of downloading them; and "base_url", "timeout",
    and "session") and two of its own.

    Args:
        rulebook: the rules that find the court of an opinion: a rulebook, or
            the path of a CSV file of rules. Defaults to `None`, in which case
            the rules in "instructions/courts.csv" are used.
        processes: number of processes to decompress the files with. Defaults
            to `None`, in which case every core is used.

    """

    rulebook: rules.Rulebook | pathlib.Path | str | None = None
    processes: int | None = None

    """ Public Methods """

    def extract(
        self,
        courts: str | Iterable[str] = 'federal_appellate',
        start_date: str | None = None,
        end_date: str | None = None,
        folder: pathlib.Path | str = 'court_listener',
        *,
        max_cases: int | None = None,
        overwrite: bool = False,
        parties: str | None = None) -> list[pathlib.Path]:
        """Saves the cases of `courts` filed between two dates.

        The opinion clusters file is read first, for the decisions filed
        between the dates. The opinions file is read next. The court of each
        opinion of those decisions is found (see `find_court`), and each case
        of `courts` is saved in a folder named for its court.

        Args:
            courts: CourtListener ids of federal courts of appeals (such as
                "ca1" or "cadc") or names of groups of them (such as
                "federal_circuits"). Defaults to "federal_appellate".
            start_date: earliest date filed, as YYYY-MM-DD. Defaults to `None`
                (no earliest date).
            end_date: latest date filed, as YYYY-MM-DD. Defaults to `None` (no
                latest date).
            folder: folder to save the cases in. Defaults to "court_listener".
            max_cases: most cases to save, for trying things out. Reading
                stops as soon as that many are found, so a case with several
                opinions may be saved without all of them. Defaults to `None`
                (every case).
            overwrite: whether to save cases that the folder already has.
                Defaults to `False`.
            parties: "United States" to save only the cases that name the
                United States as a party (as every federal criminal case
                does), or any other regular expression that the name of a
                case must match. Defaults to `None` (every case).

        Raises:
            ValueError: if one of `courts` is not a federal court of appeals.

        Returns:
            The paths of the cases saved by this call.

        """
        folder = pathlib.Path(folder)
        wanted = utilities.expand_courts(courts)
        unknown = [court for court in wanted if court not in COURTS]
        if unknown:
            message = (
                f'{unknown} cannot be collected without the dockets, since '
                f'only the federal courts of appeals ({list(COURTS)}) can be '
                f'found from their opinions. Use `courtpy.BulkData` for '
                f'other courts.'
            )
            raise ValueError(message)
        date = self.resolve_date()
        logger.info('extracting opinions from the bulk data of %s', date)
        named = _party_pattern(parties)
        skipped = set() if overwrite else _saved(folder)
        book = self._book()
        with tempfile.TemporaryFile() as spool:
            offsets = self._spool_decisions(
                spool, book, start_date, end_date, named)
            return self._save_opinions(
                spool, offsets, book = book, wanted = set(wanted),
                folder = folder, date = date, skipped = skipped,
                max_cases = max_cases)

    def parts(
        self,
        kind: str,
        key: str,
        columns: Sequence[str]) -> Iterator[_Part]:
        """Yields the parts of a bulk file, with a way to get chosen rows.

        Most rows of a bulk file are not wanted, and making Python text of
        an opinion that is not wanted is most of the work of reading one. So
        each part of the file comes as one column to choose rows by, and a
        function that returns only the rows that are chosen.

        Args:
            kind: "opinion-clusters" or "opinions".
            key: name of the column to choose rows by.
            columns: names of the columns of the rows to return. Those that
                the file does not have are left out.

        Yields:
            For each part of the file, the values of `key` (as text, in the
                order of the rows), and a function that takes the places of
                rows in that part and returns each as a `dict` of `columns`,
                with an empty `str` for a missing value.

        """
        csv.field_size_limit(bulk._FIELD_LIMIT)
        with self._open(kind) as text:
            header = next(csv.reader(text, **bulk._DIALECT))
        kept = [name for name in columns if name in header]
        count = 0
        for values, rows in (
            self._parts_arrow(kind, key, kept) if pa is not None
            else self._parts_csv(kind, key, kept)):
            before, count = count, count + len(values)
            if before // bulk._REPORT_EVERY != count // bulk._REPORT_EVERY:
                logger.info('%s: %d rows read', kind, count)
            yield values, rows

    def resolve_date(self) -> str:
        """Returns `date`, finding the newest files of opinions if needed.

        Raises:
            LookupError: if no date has both files of opinions.

        Returns:
            The date of the files to use, as YYYY-MM-DD.

        """
        if self.date is None:
            common: set[str] | None = None
            for kind in _KINDS:
                dates = set(self.available(kind))
                common = dates if common is None else common & dates
            if not common:
                message = 'no date in the bulk data has both files of opinions'
                raise LookupError(message)
            self.date = max(common)
        return self.date

    """ Private Methods """

    def _book(self) -> rules.Rulebook:
        """Returns the rules that find the court of an opinion.

        Returns:
            `rulebook`, loaded if it is the path of a file, or the rules in
                "instructions/courts.csv" if it is `None`.

        """
        if isinstance(self.rulebook, rules.Rulebook):
            return self.rulebook
        return rules.Rulebook.load(self.rulebook or _INSTRUCTIONS / 'courts.csv')

    @contextlib.contextmanager
    def _bytes(self, kind: str) -> Iterator[IO[bytes]]:
        """Opens one bulk file as decompressed bytes.

        The file is read from CourtListener as it arrives if `stream` is
        true, and is otherwise downloaded first (or found in `folder`) and
        decompressed with every core, if indexed_bzip2 is installed.

        Args:
            kind: the kind of bulk file.

        Yields:
            The decompressed file.

        """
        if self.stream:
            name = self._name(kind)
            url = f'{self.base_url}{options._BULK_PREFIX}{name}'
            response = self.session.get(
                url, stream = True, timeout = self.timeout)
            response.raise_for_status()
            try:
                with bz2.open(response.raw, 'rb') as raw:
                    yield raw
            finally:
                response.close()
        elif indexed_bzip2 is None:
            with bz2.open(self.fetch(kind), 'rb') as raw:
                yield raw
        else:
            cores = self.processes or os.cpu_count() or 1
            with indexed_bzip2.open(
                str(self.fetch(kind)), parallelization = cores) as raw:
                yield raw

    @contextlib.contextmanager
    def _open(self, kind: str) -> Iterator[io.TextIOBase]:
        """Opens one bulk file as text.

        Args:
            kind: the kind of bulk file.

        Yields:
            The decompressed file, as UTF-8 text.

        """
        with self._bytes(kind) as raw, io.TextIOWrapper(
            raw, encoding = 'utf-8', newline = '') as text:
            yield text

    def _parts_arrow(
        self,
        kind: str,
        key: str,
        columns: Sequence[str]) -> Iterator[_Part]:
        """Yields the parts of a bulk file that pyarrow reads (see `parts`).

        Args:
            kind: the kind of bulk file.
            key: name of the column to choose rows by.
            columns: names of the columns of the rows to return.

        Yields:
            The values of `key` in each part, and a function that returns
                chosen rows.

        """
        included = list(dict.fromkeys([key, *columns]))
        with self._bytes(kind) as raw:
            reader = arrow_csv.open_csv(
                raw,
                read_options = arrow_csv.ReadOptions(
                    block_size = _BLOCK, use_threads = True),
                # The bulk files are written by PostgreSQL, with a backslash
                # before a quote in a value, and line breaks in values.
                parse_options = arrow_csv.ParseOptions(
                    quote_char = '"', double_quote = False,
                    escape_char = '\\', newlines_in_values = True),
                convert_options = arrow_csv.ConvertOptions(
                    include_columns = included,
                    column_types = dict.fromkeys(
                        included, pa.large_string()),
                    strings_can_be_null = False))
            for batch in reader:
                yield batch.column(key).to_pylist(), functools.partial(
                    _rows_arrow, batch.select(list(columns)))

    def _parts_csv(
        self,
        kind: str,
        key: str,
        columns: Sequence[str]) -> Iterator[_Part]:
        """Yields the parts of a bulk file that Python reads (see `parts`).

        Args:
            kind: the kind of bulk file.
            key: name of the column to choose rows by.
            columns: names of the columns of the rows to return.

        Yields:
            The values of `key` in each part, and a function that returns
                chosen rows.

        """
        with self._open(kind) as text:
            reader = csv.reader(text, **bulk._DIALECT)
            at = {name: place for place, name in enumerate(next(reader))}
            while True:
                chunk = list(itertools.islice(reader, _CHUNK))
                if not chunk:
                    return
                yield [row[at[key]] for row in chunk], functools.partial(
                    _rows_csv, chunk, {name: at[name] for name in columns})

    def _save_opinions(
        self,
        spool: IO[bytes],
        offsets: array.array[int],
        *,
        book: rules.Rulebook,
        wanted: set[str],
        folder: pathlib.Path,
        date: str,
        skipped: set[int],
        max_cases: int | None) -> list[pathlib.Path]:
        """Saves the opinions of the decisions of the courts in `wanted`.

        The opinions file is not sorted by case, so a case's opinions can be
        anywhere in it. Opinions are held in memory (with one field of text
        each, see `courtpy.courtlistener.slim_opinion`) until their text
        reaches courtpy's limit, and then written to their cases.

        Args:
            spool: the temporary file of decisions from `_spool_decisions`.
            offsets: where each decision is in `spool`, from
                `_spool_decisions`.
            book: the rules that find the court of an opinion.
            wanted: ids of the courts to save.
            folder: folder to save the cases in.
            date: the date of the bulk files, which is saved with each case.
            skipped: ids of clusters that are not to be saved.
            max_cases: most cases to save, or `None` for every case.

        Returns:
            The paths of the cases that were saved.

        """
        columns = [*courtlistener._OPINION_KEPT, *options._TEXT_FIELDS]
        courts: dict[int, str] = {}
        records: dict[int, dict[str, Any]] = {}
        buffer: dict[int, list[dict[str, Any]]] = {}
        paths: dict[int, pathlib.Path] = {}
        # A decision whose court is not known yet may be of a court in
        # `wanted`.
        possible = wanted | {''}
        size = 0

        def flush() -> None:
            """Writes the opinions in the buffer to their cases."""
            for number, opinions in buffer.items():
                if number in records:
                    court = courts[number]
                    paths[number] = courtlistener.case_path(folder, court, number)
                    courtlistener.save_case(paths[number], {
                        'source': 'court_listener',
                        'bulk_date': date,
                        'court': COURTS[court],
                        'cluster': records.pop(number),
                        'docket': None,
                        'citations': [],
                        'opinions': opinions})
                else:
                    courtlistener.add_opinions(paths[number], opinions)
            buffer.clear()

        def kept(value: str) -> bool:
            """Returns whether an opinion is of a decision that may be saved."""
            number = bulk._integer(value)
            return (
                number is not None and number < len(offsets)
                and bool(offsets[number]) and number not in skipped
                and courts.get(number, '') in possible)

        full = False
        for values, rows in self.parts('opinions', 'cluster_id', columns):
            places = [place for place, value in enumerate(values) if kept(value)]
            for row in rows(places) if places else []:
                number = int(row['cluster_id'])
                court = courts.get(number)
                if court is None:
                    if max_cases is not None and len(paths) + len(records) >= max_cases:
                        full = True
                        break
                    spool.seek(offsets[number] - 1)
                    cluster = json.loads(spool.readline())
                    text = next(
                        (row[name] for name in options._TEXT_FIELDS
                         if row.get(name)), '')
                    court = find_court(
                        book, address = row.get('download_url', ''),
                        headmatter = cluster.pop('_headmatter', ''),
                        opening = _opening(text))
                    if court is None:
                        continue
                    courts[number] = court
                    if court in wanted:
                        records[number] = cluster
                if court not in wanted:
                    continue
                opinion = courtlistener.slim_opinion(bulk._convert(row))
                buffer.setdefault(number, []).append(opinion)
                size += sum(len(v) for v in opinion.values() if isinstance(v, str))
                if size >= bulk._BUFFER_BYTES:
                    flush()
                    size = 0
            if full:
                break
        flush()
        logger.info('saved %d cases', len(paths))
        return list(paths.values())

    def _spool_decisions(
        self,
        spool: IO[bytes],
        book: rules.Rulebook,
        start_date: str | None,
        end_date: str | None,
        named: re.Pattern[str] | None) -> array.array[int]:
        """Saves the decisions filed between two dates in a temporary file.

        The court of a decision is not known until its opinions are read, so
        every decision between the dates is kept, as a line of JSON in
        `spool`, where it takes no memory. Dates are compared as text, which
        works because they are written as YYYY-MM-DD.

        Args:
            spool: a temporary file, opened for reading and writing bytes.
            book: the rules that find the court of an opinion.
            start_date: earliest date filed, or `None` for no earliest date.
            end_date: latest date filed, or `None` for no latest date.
            named: a pattern that the name of a case must match, or `None`
                for every case.

        Returns:
            For each id of a cluster, one more than the place in `spool`
                where its line starts, or 0 if the cluster was not kept.

        """
        offsets = array.array('q')
        count = 0
        columns = [*_CLUSTER_KEPT, 'headmatter']
        for dates, rows in self.parts('opinion-clusters', 'date_filed', columns):
            places = [
                place for place, filed in enumerate(dates)
                if not (start_date and filed < start_date)
                and not (end_date and filed > end_date)]
            for row in rows(places) if places else []:
                names = f'{row.get("case_name", "")} {row.get("case_name_full", "")}'
                if named is not None and names.strip() and not named.search(names):
                    continue
                # The headmatter (the start of a case as a reporter printed
                # it) is not kept: only the court that it names.
                head = row.pop('headmatter', '')
                cluster = bulk._convert(row)
                cluster['_headmatter'] = (
                    _court_named(book, _opening(head)) if head else '')
                number = int(row['id'])
                if number >= len(offsets):
                    offsets.extend([0] * (number + 1 - len(offsets)))
                offsets[number] = spool.seek(0, os.SEEK_END) + 1
                spool.write(json.dumps(cluster).encode('utf-8') + b'\n')
                count += 1
        logger.info('found %d decisions between the dates', count)
        return offsets


@dataclasses.dataclass
class LoadOpinions(loaders.LoadCourtListener):
    """Collects, parses, and codes the opinions of the courts of appeals.

    It is courtpy's `load_court_listener`, with the same parameters, and one
    more way to "download": "opinions", which extracts the cases from the two
    bulk files that hold opinions (see `OpinionData`) and not from the
    dockets, citations, or courts files. With "opinions", it also takes:

    | Parameter | Meaning |
    | --- | --- |
    | `courts` | Ids or groups of federal courts of appeals. Defaults to "federal_appellate" (all thirteen). |
    | `parties` | "United States" to collect only the cases that name the United States as a party, or another regular expression that the name of a case must match. |

    """

    def load(
        self,
        source: Any,
        *,
        download: Any = None,
        courts: Any = None,
        start_date: Any = None,
        end_date: Any = None,
        max_cases: Any = None,
        overwrite: Any = False,
        bulk_folder: Any = None,
        bulk_date: Any = None,
        stream: Any = False,
        parties: Any = None,
        **kwargs: Any) -> pd.DataFrame:
        """Extracts the opinions (if asked) and parses the folder `source`.

        Args:
            source: the folder of saved cases, found with the clerk.
            download: "opinions", or one of the ways that courtpy's loader
                downloads ("bulk", "api", or "none"). Defaults to `None`
                (none).
            courts: ids or groups of courts to download. Defaults to `None`,
                in which case "opinions" downloads every federal court of
                appeals.
            start_date: earliest date filed to download (YYYY-MM-DD).
                Defaults to `None`.
            end_date: latest date filed to download (YYYY-MM-DD). Defaults to
                `None`.
            max_cases: most cases to download. Defaults to `None` (every
                case).
            overwrite: whether to download cases that were already saved.
                Defaults to `False`.
            bulk_folder: the folder to keep the bulk files in, found with the
                clerk. Defaults to `None`, in which case "bulk" in
                `courtpy.utilities.data_folder()` is used.
            bulk_date: the date of the bulk files to use. Defaults to `None`
                (the newest).
            stream: whether to read the bulk files without saving them.
                Defaults to `False`.
            parties: for "opinions", a pattern that the name of a case must
                match. Defaults to `None` (every case).
            **kwargs: other parameters of courtpy's loader, such as
                "rulebooks", "keep_text", "limit", and "workers".

        Returns:
            The table of parsed cases, labeled by "case_id".

        """
        method = str(download or '').strip().lower()
        if method == 'opinions':
            data = OpinionData(
                folder = self._locate(bulk_folder) if bulk_folder else None,
                date = loaders._date(bulk_date),
                stream = utilities.to_bool(stream))
            data.extract(
                courts = courts or 'federal_appellate',
                start_date = loaders._date(start_date),
                end_date = loaders._date(end_date),
                folder = pathlib.Path(source),
                max_cases = loaders._integer(max_cases),
                overwrite = utilities.to_bool(overwrite),
                parties = str(parties) if parties else None)
            download = None
        return super().load(
            source, download = download, courts = courts,
            start_date = start_date, end_date = end_date,
            max_cases = max_cases, overwrite = overwrite,
            bulk_folder = bulk_folder, bulk_date = bulk_date, stream = stream,
            **kwargs)


def find_court(
    rulebook: rules.Rulebook,
    *,
    address: str = '',
    headmatter: str = '',
    opening: str = '') -> str | None:
    """Returns the federal court of appeals that decided an opinion.

    Args:
        rulebook: rules that make the variable "court" from the sections
            "address", "headmatter", and "opening" (see
            "instructions/courts.csv").
        address: where CourtListener collected the opinion from (its
            "download_url"). Defaults to an empty `str`.
        headmatter: the start of the case as a reporter printed it, as plain
            text. Defaults to an empty `str`.
        opening: the start of the opinion, as plain text, which shows
            whether a bankruptcy appellate panel wrote it. Defaults to an
            empty `str`.

    Returns:
        The CourtListener id of the court (such as "ca1"), "other" if the
            rules find that it is not a court of appeals, or `None` if they
            find no court.

    """
    sections = {
        name: text for name, text in (
            ('address', address), ('headmatter', headmatter),
            ('opening', opening)) if text}
    court = rulebook.apply(sections).get('court')
    return str(court) if court else None


""" Private Functions """


def _court_named(rulebook: rules.Rulebook, headmatter: str) -> str:
    """Returns the words of a headmatter that say which court decided a case.

    Args:
        rulebook: the rules that find the court of an opinion.
        headmatter: the start of a case as a reporter printed it, as plain
            text.

    Returns:
        The name of the court of appeals (the end of the "named" section
            that the rules make), the whole text if the rules find that the
            court is not a court of appeals, or an empty `str` if they find
            no court.

    """
    found = rulebook.apply({'headmatter': headmatter})
    if found.get('court') == _OTHER:
        return headmatter
    # The court's name is at the end of the section that the rules make.
    return str(found.get('named') or '')[-_NAME_LENGTH:]


def _opening(text: str) -> str:
    """Returns the start of an opinion as plain text.

    Args:
        text: an opinion (or the headmatter of a case), which may be HTML or
            XML.

    Returns:
        The first `_OPENING` characters, without tags and with single spaces.

    """
    start = _TAGS.sub(' ', text[:_OPENING * 4])
    return _SPACES.sub(' ', start).strip()[:_OPENING]


def _party_pattern(parties: str | None) -> re.Pattern[str] | None:
    """Returns the pattern that the names of the cases to save must match.

    Args:
        parties: "United States", another regular expression, or `None`.

    Returns:
        A pattern for the ways that CourtListener names the United States
            (such as "United States", "U.S.", and "USA") if `parties` is
            "United States", a pattern that ignores case for any other
            expression, or `None` if `parties` is blank.

    """
    if not parties or not parties.strip():
        return None
    if parties.strip().lower() == 'united states':
        return _NAMES
    return re.compile(parties, re.IGNORECASE)


def _rows_arrow(batch: Any, places: Sequence[int]) -> list[dict[str, str]]:
    """Returns chosen rows of a part of a bulk file that pyarrow read.

    Args:
        batch: the part of the file, as a `pyarrow.RecordBatch` of text.
        places: the places of the rows to return.

    Returns:
        Each row, as a `dict` of its columns.

    """
    chosen = batch.take(pa.array(places, type = pa.int64()))
    return list(chosen.to_pylist())


def _rows_csv(
    chunk: Sequence[Sequence[str]],
    at: dict[str, int],
    places: Sequence[int]) -> list[dict[str, str]]:
    """Returns chosen rows of a part of a bulk file that Python read.

    Args:
        chunk: the rows of the part of the file.
        at: the place in a row of each column to return, by its name.
        places: the places of the rows to return.

    Returns:
        Each row, as a `dict` of its columns.

    """
    return [
        {name: chunk[place][column] for name, column in at.items()}
        for place in places]


def _saved(folder: pathlib.Path) -> set[int]:
    """Returns the ids of the cases that a folder already holds.

    Args:
        folder: a folder of saved cases, which may not exist.

    Returns:
        The id of each case, from the name of its file.

    """
    if not folder.is_dir():
        return set()
    return {
        int(path.stem) for path in folder.rglob('*.json')
        if path.stem.isdigit()}
