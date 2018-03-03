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
from typing import Optional, cast
from xml.etree import ElementTree

import click
import jenkins

from jenkins_job_linter.config import _filter_config, GetListConfigParser
from jenkins_job_linter.linters import LINTERS
from jenkins_job_linter.models import LintContext, RunContext


def lint_job_xml(ctx: RunContext, job_name: str, tree: ElementTree.ElementTree,
                 config: GetListConfigParser) -> bool:
    """Run all the linters against an XML tree."""
    success = True
    for linter_name, linter in LINTERS.items():
        if linter_name in config.getlist('job_linter', 'disable_linters'):
            continue
        only_run = config.getlist('job_linter', 'only_run')
        if only_run and linter_name not in only_run:
            continue
        section = config['job_linter:{}'.format(linter_name)]
        result, text = linter(LintContext(section, ctx, tree)).check()
        if not result.value:
            success = False
            output = '{}: {}: FAIL'.format(job_name, linter.description)
            if text is not None:
                output += ': {}'.format(text)
            print(output)
    return success


def lint_jobs_from_directory(compiled_job_directory: str,
                             config: ConfigParser) -> bool:
    """Load jobs from a directory and run linters against each one."""
    config = _filter_config(config)
    success = True
    filenames = os.listdir(compiled_job_directory)
    for job_file in filenames:
        job_path = os.path.join(compiled_job_directory, job_file)
        result = lint_job_xml(RunContext(filenames), job_file,
                              ElementTree.parse(job_path), config)
        success = success and result
    return success


def lint_jobs_from_running_jenkins(jenkins_url: str, jenkins_username: str,
                                   jenkins_password: str,
                                   config: ConfigParser) -> bool:
    """Load jobs from a running Jenkins and run linters against each one."""
    config = _filter_config(config)
    server = jenkins.Jenkins(
        jenkins_url, username=jenkins_username, password=jenkins_password)
    success = True
    job_names = [j['name'] for j in server.get_jobs()]
    for job_name in job_names:
        job_xml = server.get_job_config(job_name)
        element_tree = ElementTree.ElementTree(ElementTree.fromstring(job_xml))
        result = lint_job_xml(RunContext(job_names), job_name,
                              element_tree, config)
        success = success and result
    return success


@click.group()
@click.option('--conf', type=click.Path(exists=True, dir_okay=False))
@click.pass_context
def main(ctx: click.Context, conf: Optional[str] = None) -> None:
    """jenkins-job-linter: check your Jenkins jobs for common errors."""
    config = ConfigParser()
    if conf is not None:
        config.read(conf)
    ctx.obj = config


# Required until https://github.com/python/typeshed/issues/1918 is fixed
main = cast(click.Group, main)


@main.command(name='lint-directory')
@click.argument('compiled_job_directory',
                type=click.Path(exists=True, file_okay=False))
@click.pass_context
def lint_directory(ctx: click.Context, compiled_job_directory: str) -> None:
    """Take a directory of Jenkins job XML and run some checks against it."""
    result = lint_jobs_from_directory(compiled_job_directory, ctx.obj)
    if not result:
        sys.exit(1)
    sys.exit(0)


@main.command(name='lint-jenkins')
@click.option('--jenkins-url', required=True, envvar='JENKINS_URL',
              help='The URL of the running Jenkins to connect to (can be'
                   ' passed as JENKINS_URL in the environment).')
@click.option('--jenkins-username', required=True, envvar='JENKINS_USERNAME',
              help='The Jenkins username to connect with (can be passed as'
                   ' JENKINS_USERNAME in the environment).')
@click.option('--jenkins-password', required=True, envvar='JENKINS_PASSWORD',
              help='The password of the Jenkins user (can be passed as'
                   ' JENKINS_PASSWORD in the environment).')
@click.pass_context
def lint_jenkins(ctx: click.Context, jenkins_url: str, jenkins_username: str,
                 jenkins_password: str) -> None:
    """Lint all the jobs in a running Jenkins."""
    result = lint_jobs_from_running_jenkins(jenkins_url, jenkins_username,
                                            jenkins_password, ctx.obj)
    if not result:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()  # pragma: nocover
