from xml.etree import ElementTree

import pytest

from jenkins_job_linter import (
    CheckShebang, EnsureTimestamps, Linter, lint_job_xml)


class TestCheckShebang(object):

    @pytest.mark.parametrize('expected,shell_string', (
        (True, '#!/bin/sh -eux'),
        (True, 'no-shebang-is-fine'),
        (False, '#!/bin/sh -lolno'),
        (False, '#!/bin/zsh'),
        (True, '#!/usr/bin/env python'),
    ))
    def test_project_with_shell(self, expected, shell_string):
        xml_template = '''\
        <project>
          <builders>
            <hudson.tasks.Shell>
              <command>{}</command>
            </hudson.tasks.Shell>
          </builders>
        </project>'''
        xml_string = xml_template.format(shell_string)
        tree = ElementTree.fromstring(xml_string)
        linter = CheckShebang(tree)
        result, _ = linter.actual_check()
        assert result is expected

    def test_project_with_no_shell_part_skipped(self):
        tree = ElementTree.fromstring('<project/>')
        linter = CheckShebang(tree)
        result, _ = linter.actual_check()
        assert result is None


class TestEnsureTimestamps(object):

    @pytest.mark.parametrize('expected,xml_string', (
        (False, '<project/>'),
        (True, '''<project>
                    <buildWrappers>
                        <hudson.plugins.timestamper.TimestamperBuildWrapper />
                    </buildWrappers>
                  </project>''')))
    def test_linter(self, expected, xml_string):
        tree = ElementTree.fromstring(xml_string)
        linter = EnsureTimestamps(tree)
        result, _ = linter.actual_check()
        assert result is expected


class TestLinter(object):

    class LintTestSubclass(Linter):

        description = 'test description'

        def actual_check(self):
            return self._mock_result

    def test_actual_check_result_passed_through(self, mocker):
        tree = ElementTree.fromstring('<project/>')
        linter = self.LintTestSubclass(tree)
        linter._mock_result = mocker.sentinel.result, None
        assert mocker.sentinel.result == linter.check()


class TestLintJobXML(object):

    def test_all_linters_called_with_tree(self, mocker):
        linter_mocks = [mocker.Mock() for _ in range(3)]
        mocker.patch('jenkins_job_linter.LINTERS', linter_mocks)
        lint_job_xml(mocker.sentinel.tree)
        for linter_mock in linter_mocks:
            assert linter_mock.call_count == 1
            assert linter_mock.call_args == mocker.call(mocker.sentinel.tree)

    @pytest.mark.parametrize('expected,results', (
        (True, (True,)),
        (True, (True, True)),
        (False, (True, False)),
        (False, (True, False, True)),
    ))
    def test_result_aggregation(self, mocker, expected, results):
        linter_mocks = []
        for result in results:
            mock = mocker.Mock()
            mock.return_value.check.return_value = result
            linter_mocks.append(mock)
        mocker.patch('jenkins_job_linter.LINTERS', linter_mocks)
        assert lint_job_xml(mocker.sentinel.tree) is expected
