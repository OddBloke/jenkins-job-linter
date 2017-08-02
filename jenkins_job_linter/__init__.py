#!/usr/bin/env python3
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
"""
Run a series of checks against compiled job XML.
"""
import os
import re
import sys
from typing import Optional, Tuple
from xml.etree import ElementTree

import click


class Linter(object):
    """A super-class capturing the common linting pattern."""

    def __init__(self, tree: ElementTree.ElementTree) -> None:
        self._tree = tree

    def actual_check(self) -> Tuple[Optional[bool], Optional[str]]:
        """This is where the actual check should happen."""
        raise NotImplementedError  # pragma: nocover

    @property
    def description(self) -> str:
        """The output-friendly description of what this Linter does."""
        raise NotImplementedError  # pragma: nocover

    def check(self) -> bool:
        """Wrap actual_check in nice output."""
        print(' ... {}:'.format(self.description), end='')
        result, text = self.actual_check()
        if result is None:
            print(' N/A')
            result = True
        else:
            print(' OK' if result else ' FAILURE')
        if text:
            print('     {}'.format(text))
        return result


class EnsureTimestamps(Linter):

    description = 'checking for timestamps'
    _xpath = (
        './buildWrappers/hudson.plugins.timestamper.TimestamperBuildWrapper')

    def actual_check(self) -> Tuple[bool, Optional[str]]:
        """Check that the TimestamperBuildWrapper element is present."""
        return self._tree.find(self._xpath) is not None, None


class CheckShebang(Linter):

    description = 'checking shebang of shell builders'

    def actual_check(self) -> Tuple[Optional[bool], Optional[str]]:
        shell_parts = self._tree.findall(
            './builders/hudson.tasks.Shell/command')
        if not shell_parts:
            return None, None
        for shell_part in shell_parts:
            script = shell_part.text
            first_line = script.splitlines()[0]
            if not first_line.startswith('#!'):
                # This will use Jenkins' default
                continue
            if re.match(r'#!/bin/[a-z]*sh', first_line) is None:
                # This has a non-shell shebang
                continue
            line_parts = first_line.split(' ')
            if (len(line_parts) < 2
                    or re.match(r'-[eux]+', line_parts[1]) is None):
                return False, 'Shebang is {}'.format(first_line)
        return True, None


LINTERS = [CheckShebang, EnsureTimestamps]


def lint_job_xml(tree: ElementTree.ElementTree) -> bool:
    """Run all the linters against an XML tree."""
    results = [linter(tree).check() for linter in LINTERS]
    return all(results)


def lint_jobs_from_directory(compiled_job_directory: str) -> bool:
    """Load jobs from a directory and run linters against each one."""
    success = True
    for job_file in os.listdir(compiled_job_directory):
        print('Linting', job_file)
        job_path = os.path.join(compiled_job_directory, job_file)
        result = lint_job_xml(ElementTree.parse(job_path))
        success = success and result
    return success


@click.command()
@click.argument('compiled_job_directory',
                type=click.Path(exists=True, file_okay=False))
def main(compiled_job_directory) -> None:
    """Take a directory of Jenkins job XML and run some checks against it."""
    result = lint_jobs_from_directory(compiled_job_directory)
    if not result:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()  # pragma: nocover
