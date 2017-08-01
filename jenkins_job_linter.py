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
import argparse
import os
import sys
from xml.etree import ElementTree


class Linter(object):
    """A super-class capturing the common linting pattern."""

    def __init__(self, tree: ElementTree) -> None:
        self._tree = tree

    def actual_check(self) -> bool:
        """This is where the actual check should happen."""
        raise NotImplementedError

    @property
    def description(self) -> str:
        """The output-friendly description of what this Linter does."""
        raise NotImplementedError

    def check(self) -> bool:
        """Wrap actual_check in nice output."""
        print(' ... {}:'.format(self.description), end='')
        result = self.actual_check()
        print(' OK' if result else ' FAILURE')
        return result


class EnsureTimestamps(Linter):

    description = 'checking for timestamps'
    _xpath = (
        './buildWrappers/hudson.plugins.timestamper.TimestamperBuildWrapper')

    def actual_check(self) -> bool:
        """Check that the TimestamperBuildWrapper element is present."""
        return self._tree.find(self._xpath) is not None


def lint_job_xml(tree: ElementTree) -> bool:
    """Run all the linters against an XML tree."""
    linters = [EnsureTimestamps]
    results = [linter(tree).check() for linter in linters]
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


def main() -> None:
    """Take a directory of Jenkins job XML and run some checks against it."""
    parser = argparse.ArgumentParser()
    parser.add_argument('compiled_job_directory')
    args = parser.parse_args()
    result = lint_jobs_from_directory(args.compiled_job_directory)
    if not result:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
