"""
appellate_roulette main access point
Corey Rayburn Yung <coreyrayburnyung@gmail.com>
Copyright 2020-2022, Corey Rayburn Yung
License: Apache-2.0

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
    
ToDo:
   
"""
from __future__ import annotations
import sys
from typing import Any

import controller

def dictify_options(item: Any) -> dict[str, str]:
    """Converts command line arguments into 'arguments' dict.

    This handy bit of code, as an alternative to argparse, was adapted from 
    here:
        https://stackoverflow.com/questions/54084892/
        how-to-convert-commandline-key-value-args-to-dictionary

    Args:
        item (Any): passed command line options (should normally be sys.argv).
        
    Returns:
        arguments(dict[str, str]): dictionary of command line options when the 
            options are separated by '='.

    """
    arguments = {}
    for argument in item[1:]:
        if '=' in argument:
            separator = argument.find('=')
            key, value = argument[:separator], argument[separator + 1:]
            trimmed_key = key.strip()
            trimmed_value = value.strip()
            arguments[trimmed_key] = trimmed_value
    return arguments

if __name__ == '__main__':
    # Gets command line arguments and converts them to dict.
    arguments = dictify_options(item = sys.argv)
    # Calls Theory with passed command-line arguments.
    controller.CourtPy(
        idea = arguments.get('-idea'),
        clerk = arguments.get('-clerk', None),
        dataset = arguments.get('-dataset', None))