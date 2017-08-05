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
import itertools
from xml.etree import ElementTree

import pytest

from jenkins_job_linter.linters import (
    CheckForEmptyShell,
    CheckShebang,
    EnsureTimestamps,
    Linter,
    LintResult,
)

FAILING_SHEBANG_ARGS = ['e', 'u', 'x'] + list(itertools.combinations('eux', 2))
PASSING_SHEBANG_ARGS = itertools.permutations('eux')


class ShellTest:

    _xml_template = '''\
        <project>
            <builders>
                {builders}
            </builders>
        </project>'''

    _shell_builder_template = '''\
        <hudson.tasks.Shell>
            <command>{shell_script}</command>
        </hudson.tasks.Shell>'''


class TestCheckShebang(ShellTest):

    @pytest.mark.parametrize('expected,shell_string', [
        (LintResult.PASS, 'no-shebang-is-fine'),
        (LintResult.FAIL, '#!/bin/sh -lolno'),
        (LintResult.FAIL, '#!/bin/zsh'),
        (LintResult.PASS, '#!/usr/bin/env python'),
        (LintResult.PASS, ''),
    ] + [(LintResult.FAIL, '#!/bin/sh -{}'.format(''.join(args)))
         for args in FAILING_SHEBANG_ARGS] +
        [(LintResult.PASS, '#!/bin/sh -{}'.format(''.join(args)))
         for args in PASSING_SHEBANG_ARGS]
    )
    def test_project_with_shell(self, expected, shell_string):
        xml_string = self._xml_template.format(
            builders=self._shell_builder_template.format(
                shell_script=shell_string))
        tree = ElementTree.fromstring(xml_string)
        linter = CheckShebang(tree, {})
        result, _ = linter.actual_check()
        assert result is expected

    def test_project_with_no_shell_part_skipped(self):
        tree = ElementTree.fromstring('<project/>')
        linter = CheckShebang(tree, {})
        result, _ = linter.actual_check()
        assert result is LintResult.SKIP

    @pytest.mark.parametrize('expected,shebangs', (
        (LintResult.PASS, ('#!/bin/sh -eux', '#!/usr/bin/env python3')),
        (LintResult.FAIL, ('#!/bin/sh -eux', '#!/bin/sh')),
        (LintResult.FAIL, ('#!/bin/sh', '#!/bin/sh -eux'))
    ))
    def test_multiple_shell_parts(self, expected, shebangs):
        builders = ''.join(
            self._shell_builder_template.format(shell_script=shebang)
            for shebang in shebangs)
        tree = ElementTree.fromstring(self._xml_template.format(
            builders=builders))
        linter = CheckShebang(tree, {})
        result, _ = linter.actual_check()
        assert result is expected


class TestCheckForEmptyShell(ShellTest):

    @pytest.mark.parametrize('expected,script', (
        (LintResult.FAIL, ''), (LintResult.PASS, '...')))
    def test_actual_check(self, expected, script):
        tree = ElementTree.fromstring(
            self._xml_template.format(
                builders=self._shell_builder_template.format(
                    shell_script=script)))
        linter = CheckForEmptyShell(tree, {})
        result, _ = linter.actual_check()
        assert result is expected


class TestEnsureTimestamps:

    @pytest.mark.parametrize('expected,xml_string', (
        (LintResult.FAIL, '<project/>'),
        (LintResult.PASS, '''\
            <project>
                <buildWrappers>
                    <hudson.plugins.timestamper.TimestamperBuildWrapper />
                </buildWrappers>
            </project>''')))
    def test_linter(self, expected, xml_string):
        tree = ElementTree.fromstring(xml_string)
        linter = EnsureTimestamps(tree, {})
        result, _ = linter.actual_check()
        assert result is expected


class TestLinter:

    class LintTestSubclass(Linter):

        description = 'test description'

        def actual_check(self):
            return self._config['_mock_result']

    def test_check_and_text_passed_through(self, mocker):
        tree = ElementTree.fromstring('<project/>')
        mock_result = mocker.sentinel.result, mocker.sentinel.text
        linter = self.LintTestSubclass(tree, {'_mock_result': mock_result})
        assert mock_result == linter.check()
