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
import sys
from xml.etree import ElementTree

import click

from jenkins_job_linter.linters import LINTERS


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
def main(compiled_job_directory: str) -> None:
    """Take a directory of Jenkins job XML and run some checks against it."""
    result = lint_jobs_from_directory(compiled_job_directory)
    if not result:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()  # pragma: nocover
