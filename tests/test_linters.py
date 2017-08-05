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
        (True, 'no-shebang-is-fine'),
        (False, '#!/bin/sh -lolno'),
        (False, '#!/bin/zsh'),
        (True, '#!/usr/bin/env python'),
        (True, ''),
    ] + [(False, '#!/bin/sh -{}'.format(''.join(args)))
         for args in FAILING_SHEBANG_ARGS] +
        [(True, '#!/bin/sh -{}'.format(''.join(args)))
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
        assert result is None

    @pytest.mark.parametrize('expected,shebangs', (
        (True, ('#!/bin/sh -eux', '#!/usr/bin/env python3')),
        (False, ('#!/bin/sh -eux', '#!/bin/sh')),
        (False, ('#!/bin/sh', '#!/bin/sh -eux'))
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

    @pytest.mark.parametrize('expected,script', ((False, ''), (True, '...')))
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
        (False, '<project/>'),
        (True, '''<project>
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

    def test_actual_check_result_passed_through(self, mocker):
        tree = ElementTree.fromstring('<project/>')
        mock_result = mocker.sentinel.result, None
        linter = self.LintTestSubclass(tree, {'_mock_result': mock_result})
        assert mock_result[0] == linter.check()

    def test_none_result_returned_as_success(self):
        tree = ElementTree.fromstring('<project/>')
        mock_result = None, None
        linter = self.LintTestSubclass(tree, {'_mock_result': mock_result})
        assert linter.check() is True

    def test_linters_can_return_text(self):
        tree = ElementTree.fromstring('<project/>')
        mock_result = None, "some text"
        linter = self.LintTestSubclass(tree, {'_mock_result': mock_result})
        linter.check()
