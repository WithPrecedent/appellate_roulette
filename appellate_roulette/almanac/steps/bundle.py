"""
Primary class for merging court opinion data from different sources.
"""

import dataclasses

from simplify import timer
from simplify.almanac.steps import Bundle


@timer('Data merging')
@dataclasses.dataclass
class CPBundle(Bundle):

    technique : str = ''
    techniques : object = None
    parameters : object = None
    auto_prepare : bool = True
    name : str = 'bundler'

    def __post_init__(self):
        return