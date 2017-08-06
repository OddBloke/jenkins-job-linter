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
import pytest

from jenkins_job_linter.jjb_subcommand import LintSubCommand


class TestParseArgs:

    def test_parser_named_lint(self, mocker):
        subcommand = LintSubCommand()
        subparser_mock = mocker.Mock()
        subcommand.parse_args(subparser_mock)
        assert 1 == subparser_mock.add_parser.call_count
        assert mocker.call('lint') == subparser_mock.add_parser.call_args

    def test_args_added_to_parser(self, mocker):
        expected_methods = [
            'parse_arg_names', 'parse_arg_path',
            'parse_option_recursive_exclude']
        subcommand = LintSubCommand()
        mocks = []
        for expected_method in expected_methods:
            mock = mocker.Mock()
            setattr(subcommand, expected_method, mock)
            mocks.append(mock)
        subparser_mock = mocker.Mock()
        subcommand.parse_args(subparser_mock)
        for mock in mocks:
            assert 1 == mock.call_count
            assert mocker.call(
                subparser_mock.add_parser.return_value) == mock.call_args


class TestExecute:

    def test_arguments_passed_through(self, mocker):
        mocker.patch('jenkins_job_linter.jjb_subcommand.sys.exit')
        super_execute_mock = mocker.patch(
            'jenkins_job_linter.jjb_subcommand.test.TestSubCommand.execute')
        options, jjb_config = mocker.Mock(), mocker.MagicMock()
        subcommand = LintSubCommand()
        subcommand.execute(options, jjb_config)
        assert 1 == super_execute_mock.call_count
        assert mocker.call(options, jjb_config) == super_execute_mock.call_args

    def test_config_xml_set_to_false(self, mocker):
        mocker.patch('jenkins_job_linter.jjb_subcommand.sys.exit')
        super_execute_mock = mocker.patch(
            'jenkins_job_linter.jjb_subcommand.test.TestSubCommand.execute')
        options = mocker.Mock()
        subcommand = LintSubCommand()
        subcommand.execute(options, mocker.MagicMock())
        assert super_execute_mock.call_args[0][0].config_xml is False

    def _get_tmpdir_mock(self, mocker):
        temporary_directory_mock = mocker.patch(
            'jenkins_job_linter.jjb_subcommand.tempfile.TemporaryDirectory')
        return temporary_directory_mock.return_value.__enter__.return_value

    def test_tmpdir_used_as_output_dir(self, mocker):
        mocker.patch('jenkins_job_linter.jjb_subcommand.sys.exit')
        mocker.patch(
            'jenkins_job_linter.jjb_subcommand.lint_jobs_from_directory')
        super_execute_mock = mocker.patch(
            'jenkins_job_linter.jjb_subcommand.test.TestSubCommand.execute')
        tmpdir_mock = self._get_tmpdir_mock(mocker)
        options = mocker.Mock()
        subcommand = LintSubCommand()
        subcommand.execute(options, mocker.Mock())
        assert super_execute_mock.call_args[0][0].output_dir == tmpdir_mock

    def test_lint_jobs_from_directory_called_with_tmpdir(self, mocker):
        mocker.patch('jenkins_job_linter.jjb_subcommand.sys.exit')
        lint_jobs_mock = mocker.patch(
            'jenkins_job_linter.jjb_subcommand.lint_jobs_from_directory')
        mocker.patch(
            'jenkins_job_linter.jjb_subcommand.test.TestSubCommand.execute')
        tmpdir_mock = self._get_tmpdir_mock(mocker)
        subcommand = LintSubCommand()
        subcommand.execute(mocker.Mock, mocker.Mock())
        assert 1 == lint_jobs_mock.call_count
        assert lint_jobs_mock.call_args[0][0] == tmpdir_mock

    def test_lint_jobs_from_directory_called_with_jjb_config_config_parser(
            self, mocker):
        mocker.patch('jenkins_job_linter.jjb_subcommand.sys.exit')
        lint_jobs_mock = mocker.patch(
            'jenkins_job_linter.jjb_subcommand.lint_jobs_from_directory')
        mocker.patch(
            'jenkins_job_linter.jjb_subcommand.test.TestSubCommand.execute')
        jjb_config = mocker.Mock()
        subcommand = LintSubCommand()
        subcommand.execute(mocker.Mock, jjb_config)
        assert 1 == lint_jobs_mock.call_count
        assert lint_jobs_mock.call_args[0][1] == jjb_config.config_parser

    @pytest.mark.parametrize('expected,result', ((0, True), (1, False)))
    def test_exit_codes(self, expected, mocker, result):
        lint_jobs_mock = mocker.patch(
            'jenkins_job_linter.jjb_subcommand.lint_jobs_from_directory')
        lint_jobs_mock.return_value = result
        mocker.patch(
            'jenkins_job_linter.jjb_subcommand.test.TestSubCommand.execute')
        jjb_config = mocker.Mock()
        subcommand = LintSubCommand()
        with pytest.raises(SystemExit) as exc_info:
            subcommand.execute(mocker.Mock, jjb_config)
        assert expected == exc_info.value.code
