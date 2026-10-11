"""Runs the study's commands, and courtpy's with this project's techniques.

`python -m appellate_roulette` (or `appellate-roulette`) has two commands of
its own:

* `appellate-roulette opinions` extracts the opinions of the federal courts of
  appeals from the two bulk files of CourtListener that hold opinions (see
  `appellate_roulette.opinions`).
* `appellate-roulette judges` makes the roster of judges that courtpy uses to
  identify the judges of each panel, from the Federal Judicial Center's
  files, and saves it where courtpy looks for it.

Every other command is courtpy's (such as `run`, `parse`, and `rules`), with
this project's techniques (`load_opinions`, `roulette`, and `balance`)
available, because importing appellate_roulette adds them to the `amos`
library. So `appellate-roulette run studies/appellate_roulette.toml --export`
works like `courtpy run ...`, except that the study's settings can name them.
And `appellate-roulette key set` and `appellate-roulette download api ...`
store a CourtListener API key and download cases with it, which adds the
cases that cannot be found in the bulk data without its dockets.

Contents:
    main: runs a command.
    _COMMANDS: the commands that are this project's own, with what each does.
    _judges: makes and saves the roster of judges.
    _opinions: extracts opinions from CourtListener's bulk data.
    _parser: builds the parser of this project's own commands.

"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence

import requests
from courtpy import cli, judges

from . import opinions

_COMMANDS: dict[str, str] = {
    'opinions': 'extract the opinions of the courts of appeals from '
                "CourtListener's bulk data",
    'judges': 'make the roster of judges from the Federal Judicial '
              "Center's files"}


def main(argv: Sequence[str] | None = None) -> int:
    """Runs one of this project's commands, or else a courtpy command.

    Args:
        argv: the command's arguments. Defaults to `None`, in which case the
            arguments of the program are used.

    Returns:
        0 if the command succeeded, and 1 if it failed.

    """
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0] in {'-h', '--help'}:
        print('appellate-roulette has two commands of its own:')
        for name, purpose in _COMMANDS.items():
            print(f'  {name:10}{purpose}')
        print('Every other command is one of courtpy:\n')
    if arguments[:1] and arguments[0] in _COMMANDS:
        parsed = _parser().parse_args(arguments)
        logging.basicConfig(
            level = logging.INFO, format = '%(levelname)s: %(message)s')
        try:
            return int(parsed.command(parsed) or 0)
        except (
            FileNotFoundError, KeyError, LookupError, OSError, ValueError,
            requests.RequestException) as error:
            print(f'appellate-roulette: {error}', file = sys.stderr)
            return 1
    return cli.main(arguments)


""" Commands """


def _judges(arguments: argparse.Namespace) -> int:
    """Makes and saves the roster of judges ("appellate-roulette judges").

    Args:
        arguments: the parsed arguments: "update" (whether to download the
            Federal Judicial Center's files again).

    Returns:
        0.

    """
    roster = judges.Roster.from_fjc(update = arguments.update)
    path = roster.save()
    people = roster.data['nid'].nunique()
    print(f'A roster of {people} judges was saved to {path}')
    return 0


def _opinions(arguments: argparse.Namespace) -> int:
    """Extracts opinions from the bulk data ("appellate-roulette opinions").

    Args:
        arguments: the parsed arguments: "courts", "start", "end", "folder",
            "parties", "max_cases", "overwrite", "bulk_folder", "bulk_date",
            and "stream".

    Returns:
        0.

    """
    data = opinions.OpinionData(
        folder = arguments.bulk_folder,
        date = arguments.bulk_date,
        stream = arguments.stream)
    saved = data.extract(
        courts = arguments.courts,
        start_date = arguments.start,
        end_date = arguments.end,
        folder = arguments.folder,
        max_cases = arguments.max_cases,
        overwrite = arguments.overwrite,
        parties = arguments.parties)
    print(f'{len(saved)} cases saved in {arguments.folder}')
    return 0


""" Private Functions """


def _parser() -> argparse.ArgumentParser:
    """Builds the parser of this project's own commands.

    Returns:
        The parser. The function for each command is its "command".

    """
    parser = argparse.ArgumentParser(
        prog = 'appellate-roulette',
        description = 'Collect the opinions and judges of the study.')
    commands = parser.add_subparsers(title = 'commands', required = True)
    extract = commands.add_parser('opinions', help = _COMMANDS['opinions'])
    extract.add_argument(
        '--courts', nargs = '+', default = ['federal_appellate'],
        help = 'ids of courts of appeals (such as ca1) or groups (such as '
               'federal_circuits). Default: federal_appellate')
    extract.add_argument(
        '--start', default = '2010-01-01',
        help = 'earliest date filed (YYYY-MM-DD). Default: 2010-01-01')
    extract.add_argument('--end', help = 'latest date filed (YYYY-MM-DD)')
    extract.add_argument(
        '--folder', default = 'data/court_listener',
        help = 'folder to save the cases in. Default: data/court_listener')
    extract.add_argument(
        '--parties',
        help = '"United States" to save only the cases that name the United '
               'States, or a pattern that the name of a case must match')
    extract.add_argument(
        '--max-cases', type = int,
        help = 'most cases to save, for trying things out')
    extract.add_argument(
        '--overwrite', action = 'store_true',
        help = 'save cases that the folder already has')
    extract.add_argument(
        '--bulk-folder', help = 'folder to keep the bulk files in')
    extract.add_argument(
        '--bulk-date', help = 'date of the bulk files. Default: the newest')
    extract.add_argument(
        '--stream', action = 'store_true',
        help = 'read the bulk files without saving them')
    extract.set_defaults(command = _opinions)
    roster = commands.add_parser('judges', help = _COMMANDS['judges'])
    roster.add_argument(
        '--update', action = 'store_true',
        help = "download the Federal Judicial Center's files again")
    roster.set_defaults(command = _judges)
    return parser


if __name__ == '__main__':
    sys.exit(main())
