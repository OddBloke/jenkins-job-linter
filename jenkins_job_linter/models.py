# Copyright (C) 2017  Daniel Watkins <daniel@daniel-watkins.co.uk>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Data classes used in jenkins_job_linter."""
from configparser import SectionProxy
from typing import Iterable
from xml.etree import ElementTree


class LintContext:
    """
    The context in which a linter should run.

    This contains all of the information about the object under test, and the
    environment in which the linter is running.
    """

    def __init__(self,
                 config: SectionProxy,
                 run_ctx: 'RunContext',
                 tree: ElementTree.ElementTree,
                 ) -> None:
        """
        Create a LintContext.

        :param config:
            The configparser.SectionProxy of the parsed configuration for this
            particular linter.
        :param tree:
            A Jenkins XML file parsed in to an ElementTree.
        """
        self.config = config
        self.run_ctx = run_ctx
        self.tree = tree


class RunContext:
    """Run-level data to be passed around and to linters."""

    def __init__(self, object_names: Iterable[str]) -> None:
        """
        Create a RunContext.

        :param object_names:
            An iterable containing the names of Jenkins objects that this run
            is operating against.
        """
        self.object_names = object_names
