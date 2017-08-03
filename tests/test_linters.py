from xml.etree import ElementTree

import pytest

from jenkins_job_linter.linters import CheckShebang, EnsureTimestamps, Linter


class TestCheckShebang(object):

    @pytest.mark.parametrize('expected,shell_string', (
        (True, '#!/bin/sh -eux'),
        (True, 'no-shebang-is-fine'),
        (False, '#!/bin/sh -lolno'),
        (False, '#!/bin/zsh'),
        (True, '#!/usr/bin/env python'),
        (True, ''),
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

    def test_none_result_returned_as_success(self):
        tree = ElementTree.fromstring('<project/>')
        linter = self.LintTestSubclass(tree)
        linter._mock_result = None, None
        assert linter.check() is True

    def test_linters_can_return_text(self):
        tree = ElementTree.fromstring('<project/>')
        linter = self.LintTestSubclass(tree)
        linter._mock_result = None, "some text"
        linter.check()
