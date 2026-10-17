"""Whether the judges who happen to hear a federal criminal appeal change its outcome

The rule of law promises that like cases will be treated alike. This study
tests that promise in federal criminal appeals. The courts of appeals assign
judges to panels without regard to the cases, so if outcomes turned only on
what the law requires, it would not matter which three judges heard an
appeal.

The opinions come from CourtListener (see `opinions`), and are parsed and
coded by courtpy, which also identifies the judges of each panel from the
Federal Judicial Center's directory. The tests of whether the draw of judges
matters are in `roulette`, and amos analyzes the result.

Importing appellate_roulette adds its techniques to the `amos` library, so
that they can be named in a study's settings. It also sets pandas to keep
text as Python does (the "mode.string_storage" option), which is what pandas
does without pyarrow.

Contents:
    Balance: tests whether the judges who heard each case are related to
        what was true of the case before they heard it.
    LoadOpinions: collects, parses, and codes the opinions of the federal
        courts of appeals.
    OpinionData: extracts cases from the two bulk files of CourtListener
        that hold opinions.
    Project: `amos.Project` (which courtpy offers under the same name), which
        loads and analyzes the cases that a settings file describes.
    Roulette: tests whether the outcome of a case depends on the judges who
        heard it.
    spin: tests whether a column of the cases depends on their judges.

"""

from __future__ import annotations

__version__ = '0.0.2'

__author__: str = 'Corey Rayburn Yung'

__all__: list[str] = [
    'Balance',
    'LoadOpinions',
    'OpinionData',
    'Project',
    'Roulette',
    'opinions',
    'roulette',
    'spin',
]

import pandas as pd
from courtpy import Project

from . import opinions, roulette
from .opinions import LoadOpinions, OpinionData
from .roulette import Balance, Roulette, spin

# pandas keeps text with pyarrow when pyarrow is installed (as it is here, to
# read the bulk files), and scikit-learn cannot split rows that are labeled
# by such text, which the "stratified" splitter of amos 0.2.6 asks it to do
# with the ids of the cases. Text that Python keeps behaves the same way, and
# is what pandas uses without pyarrow, so the study does not depend on which
# is installed.
pd.set_option('mode.string_storage', 'python')
