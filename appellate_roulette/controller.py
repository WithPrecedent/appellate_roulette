"""Master control script for CourtPy.

Each major module can be called individually or through this class.
The CourtPy class allows the user to call a group of modules through an ad hoc
workflow or run the complete pipeline. The user determines which parts of the
pipeline to invoke by changing the options in courtpy_settings.ini or by
passing a menu when CourtPy is instanced.

If there are any problems with this file or packaged modules, please contact
the creator directly: coreyrayburnyung@gmail.com or post on the GitHub page.
Also, if you find any errors or ways to increase efficiency, please email
or contribute.

If you utilize any code for published work, please use the citation included
on the WithPrecedent Github page. Acknowledgement is greatly appreciated.
"""
from __future__ import annotations
import contextlib
import dataclasses
from typing import Any, ClassVar, Optional, Protocol, Type, TYPE_CHECKING, Union

import bobbie
import nagata

from .almanac import CPAlmanac
from .cookbook import CPCookbook


@dataclasses.dataclass
class CourtPy(object):
    """Prepares, parses, wrangles, merges, and/or analyzes court opinion data
    based upon user selections.

    Args:

            
    """
    idea: object
    clerk: object = None
    dataset: object = None
    name: Optional[str] = None
    identification: Optional[str] = None
    automatic: Optional[bool] = True

    def __post_init__(self) -> None:
        """Initializes and validates class instance attributes."""
        # Calls parent and/or mixin initialization method(s).
        with contextlib.suppress(AttributeError):
            super().__post_init__()
        self.validate()
        self.set_parallelization(project = self.project)
        if self.automatic:
            self.acquire()
            self.wrangle()
            self.analyze()
            self.summarize()
            self.visualize()
        return self
        
    def validate_name(project: Project) -> Project:
        """Creates or validates 'project.name'.
        
        Args:
            project (Project): project to examine and validate.
            
        Returns:
            Project: validated Project instance.
            
        """
        if project.name is None:
            settings_name = workshop.infer_project_name(project = project)
            if settings_name is None:
                project.name = amos.namify(item = project)
            else:
                project.name = settings_name
        return project    
      
    def set_parallelization(self) -> None:
        """Sets multiprocessing method based on 'idea'.
        
        Args:
            project (Project): project containing parallelization idea
            
        """
        if ('general' in self.idea
                and 'parallelize' in self.idea['general'] 
                and self.idea['general']['parallelize']):
            if not globals()['multiprocessing']:
                import multiprocessing
            multiprocessing.set_start_method('spawn') 
        return 

#    def _set_almanac_options(self):
#        # Replaces the default Almanac classes with custom classes specifically
#        # designed for court data.
#        self.options = {'cultivate' : CPCultivate,
#                        'reap' : CPReap,
#                        'thresh' : CPThresh,
#                        'bale' : CPBale,
#                        'clean' : CPClean}
#        return self
#
#    def _set_cookbook_options(self):
#        return self
#
#    def create(self):
#        # Loop through stages based upon stages variable in self.menu
#        for stage in self._listify(self.stages):
#            if stage in ['cultivate', 'reap', 'thresh', 'bale', 'clean']:
#                self.
#                self.menu.localize(instance = self, sections = ['almanac'])
#                self.stage = CPAlmanac[stage](menu = self.menu,
#                                              inventory = self.inventory,
#                                              stages = stage)
#
#        # Calls the regular prepare and create methods, now linked to the
#        # custom classes in self.options
#        self.prepare()
#        self.create()
#            else:
#                self.stage = CPCookbook[stage](menu = self.menu,
#                                               inventory = self.inventory)
#            if self.conserve_memory:
#                del(self.stage)
#        return self