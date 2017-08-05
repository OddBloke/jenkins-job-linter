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
"""Run a series of checks against compiled job XML."""
import os
import sys
from configparser import ConfigParser
from typing import Optional
from xml.etree import ElementTree

import click

from jenkins_job_linter.linters import LINTERS


def lint_job_xml(job_name: str, tree: ElementTree.ElementTree,
                 config: ConfigParser) -> bool:
    """Run all the linters against an XML tree."""
    success = True
    for linter in LINTERS:
        result, text = linter(tree, config).check()
        if not result.value:
            success = False
            output = '{}: {}: FAIL'.format(job_name, linter.description)
            if text is not None:
                output += ': {}'.format(text)
            print(output)
    return success


def _filter_config(config: ConfigParser) -> ConfigParser:
    """
    Return a ConfigParser with only the job_linter section of the one passed.

    This creates a new ConfigParser and removes sections from that, so the one
    passed in remains unmodified.
    """
    filtered_config = ConfigParser()
    filtered_config.read_dict(config)
    for section in filtered_config.sections():
        if section != 'job_linter':
            filtered_config.remove_section(section)
    return filtered_config


def lint_jobs_from_directory(compiled_job_directory: str,
                             config: ConfigParser) -> bool:
    """Load jobs from a directory and run linters against each one."""
    config = _filter_config(config)
    success = True
    for job_file in os.listdir(compiled_job_directory):
        job_path = os.path.join(compiled_job_directory, job_file)
        result = lint_job_xml(job_file, ElementTree.parse(job_path), config)
        success = success and result
    return success


@click.command()
@click.argument('compiled_job_directory',
                type=click.Path(exists=True, file_okay=False))
@click.option('--conf', type=click.Path(exists=True, dir_okay=False))
def main(compiled_job_directory: str, conf: Optional[str] = None) -> None:
    """Take a directory of Jenkins job XML and run some checks against it."""
    config = ConfigParser()
    if conf is not None:
        config.read(conf)
    result = lint_jobs_from_directory(compiled_job_directory, config)
    if not result:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()  # pragma: nocover
