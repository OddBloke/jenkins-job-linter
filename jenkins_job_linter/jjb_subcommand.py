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
"""Implement a lint subcommand for the jenkins-job-builder command."""
import argparse
import logging
import sys
import tempfile

import jenkins_jobs.cli.subcommand.test as test
from jenkins_jobs.config import JJBConfig

from jenkins_job_linter import lint_jobs_from_directory

LOGGER = logging.getLogger(__name__)


class LintSubCommand(test.TestSubCommand):
    """
    Class to implement a lint subcommand.

    This wraps the jenkins-job-builder TestSubCommand and redirects the output
    in to a temporary directory which we then perform the lint on.
    """

    def parse_args(self, subparser: argparse._SubParsersAction) -> None:
        """Create a lint subparser and add the necessary options."""
        lint = subparser.add_parser('lint')

        self.parse_option_recursive_exclude(lint)
        self.parse_arg_path(lint)
        self.parse_arg_names(lint)

    def execute(self, options: argparse.Namespace,
                jjb_config: JJBConfig) -> None:
        """Generate output in a tempdir and run our linting against it."""
        options.config_xml = False
        with tempfile.TemporaryDirectory() as tmpdir:
            LOGGER.debug('Compiling jobs to temporary directory: %s', tmpdir)
            options.output_dir = tmpdir

            super(LintSubCommand, self).execute(options, jjb_config)

            if lint_jobs_from_directory(tmpdir, jjb_config.config_parser):
                sys.exit(0)
            sys.exit(1)
