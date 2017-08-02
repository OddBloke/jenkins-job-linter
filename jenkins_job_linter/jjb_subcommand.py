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
import argparse
import logging
import tempfile

import jenkins_jobs.cli.subcommand.test as test

from jenkins_job_linter import lint_jobs_from_directory

LOGGER = logging.getLogger(__name__)


class LintSubCommand(test.TestSubCommand):

    def parse_args(self, subparser):
        lint = subparser.add_parser('lint')

        self.parse_option_recursive_exclude(lint)
        self.parse_arg_path(lint)
        self.parse_arg_names(lint)

    def execute(self, options, jjb_config):
        options.config_xml = False
        with tempfile.TemporaryDirectory() as tmpdir:
            LOGGER.debug('Compiling jobs to temporary directory: %s', tmpdir)
            options.output_dir = tmpdir

            super(LintSubCommand, self).execute(options, jjb_config)

            lint_jobs_from_directory(tmpdir, jjb_config.config_parser)
