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
import configparser
import os
from xml.etree import ElementTree

import pytest
from click.testing import CliRunner

from jenkins_job_linter import (
    lint_job_xml,
    lint_jobs_from_directory,
    lint_jobs_from_running_jenkins,
    main,
)
from jenkins_job_linter.linters import Linter, LintResult

from .mocks import create_mock_for_class, get_config, mock_LINTERS


class TestLintJobXML:

    def test_all_linters_called_with_tree_and_run_ctx(self, mocker):
        linter_mocks = [create_mock_for_class(Linter) for _ in range(3)]
        mock_LINTERS(mocker, linter_mocks)
        lint_context_mock = mocker.patch('jenkins_job_linter.LintContext')
        run_ctx = mocker.Mock()
        lint_job_xml(run_ctx, 'job_name', mocker.sentinel.tree, get_config())
        for linter_mock in linter_mocks:
            assert linter_mock.call_count == 1
            assert linter_mock.call_args == mocker.call(
                lint_context_mock.return_value)
        for call_args in lint_context_mock.call_args_list:
            assert mocker.call(
                mocker.ANY, run_ctx, mocker.sentinel.tree) == call_args

    def test_lintcontext_passed_filtered_config(self, mocker):
        linters = mock_LINTERS(mocker, [create_mock_for_class(Linter)])
        config = get_config()
        section_name = 'job_linter:{}'.format(list(linters.keys())[0])
        config[section_name]['k'] = 'v'
        lint_context_mock = mocker.patch('jenkins_job_linter.LintContext')
        lint_job_xml(mocker.Mock(), 'job_name', mocker.sentinel.tree, config)
        lint_context_config = lint_context_mock.call_args[0][0]
        assert 'v' == lint_context_config['k']

    @pytest.mark.parametrize('expected,results', (
        (True, (LintResult.PASS,)),
        (True, (LintResult.PASS, LintResult.PASS)),
        (False, (LintResult.PASS, LintResult.FAIL)),
        (False, (LintResult.PASS, LintResult.FAIL, LintResult.PASS)),
    ))
    def test_result_aggregation(self, mocker, expected, results):
        linter_mocks = []
        for result in results:
            mock = create_mock_for_class(Linter, check_result=result)
            linter_mocks.append(mock)
        mock_LINTERS(mocker, linter_mocks)
        assert lint_job_xml(mocker.Mock(), 'job_name', mocker.sentinel.tree,
                            get_config()) is expected

    def test_linters_can_return_text(self, mocker):
        mock_LINTERS(mocker, [
            create_mock_for_class(
                Linter, check_result=LintResult.FAIL, check_msg='msg')])
        assert lint_job_xml(mocker.Mock(), 'job_name', mocker.sentinel.tree,
                            get_config()) is False

    def test_disable_linters_config(self, mocker):
        linters = {
            'disable_me': create_mock_for_class(Linter),
            'not_me': create_mock_for_class(Linter),
        }
        mocker.patch('jenkins_job_linter.LINTERS', linters)
        mocker.patch('jenkins_job_linter.config.LINTERS', linters)
        config = get_config()
        config['job_linter']['disable_linters'] = 'disable_me'
        lint_job_xml(mocker.Mock(), 'job_name', mocker.Mock(), config)
        assert 0 == linters['disable_me'].call_count
        assert 1 == linters['not_me'].call_count

    def test_disable_linters_overlapping_linter_prefixes(self, mocker):
        linters = {
            'do': create_mock_for_class(Linter),
            'dont': create_mock_for_class(Linter),
        }
        mocker.patch('jenkins_job_linter.LINTERS', linters)
        mocker.patch('jenkins_job_linter.config.LINTERS', linters)
        config = get_config()
        config['job_linter']['disable_linters'] = 'dont,another'
        lint_job_xml(mocker.Mock(), 'job_name', mocker.Mock(), config)
        assert 1 == linters['do'].call_count
        assert 0 == linters['dont'].call_count

    def test_only_run_config(self, mocker):
        linters = {
            'only_me': create_mock_for_class(Linter),
            'not_me': create_mock_for_class(Linter),
            'or_me': create_mock_for_class(Linter),
        }
        mocker.patch('jenkins_job_linter.LINTERS', linters)
        mocker.patch('jenkins_job_linter.config.LINTERS', linters)
        config = get_config()
        config['job_linter']['only_run'] = 'only_me'
        lint_job_xml(mocker.Mock(), 'job_name', mocker.Mock(), config)
        assert 0 == linters['not_me'].call_count
        assert 0 == linters['or_me'].call_count
        assert 1 == linters['only_me'].call_count

    def test_only_run_overlapping_linter_prefixes(self, mocker):
        linters = {
            'do': create_mock_for_class(Linter),
            'dont': create_mock_for_class(Linter),
        }
        mocker.patch('jenkins_job_linter.LINTERS', linters)
        mocker.patch('jenkins_job_linter.config.LINTERS', linters)
        config = get_config()
        config['job_linter']['only_run'] = 'dont'
        lint_job_xml(mocker.Mock(), 'job_name', mocker.Mock(), config)
        assert 0 == linters['do'].call_count
        assert 1 == linters['dont'].call_count


@pytest.mark.parametrize('test_type', ('directory', 'jenkins'))
class TestCommonConfigParsing:
    """Tests config parsing for lint_jobs_from_* functions."""

    def _setup_mocks(self, test_type, mocker):
        if test_type == 'jenkins':
            jenkins_mock = mocker.patch('jenkins_job_linter.jenkins.Jenkins')
            jenkins_mock.return_value.get_jobs.return_value = [
                {'name': 'a'}, {'name': 'b'}]
            mocker.patch('jenkins_job_linter.ElementTree')
            return mocker.patch('jenkins_job_linter.lint_job_xml')
        elif test_type == 'directory':
            listdir_mock = mocker.patch('jenkins_job_linter.os.listdir')
            listdir_mock.return_value = ['some', 'files']
            mocker.patch('jenkins_job_linter.ElementTree.parse')
            return mocker.patch('jenkins_job_linter.lint_job_xml')
        raise Exception('unknown test_type')

    def _do_call(self, test_type, mocker, config):
        if test_type == 'jenkins':
            return lint_jobs_from_running_jenkins(
                'url', 'user', 'password', config)
        elif test_type == 'directory':
            return lint_jobs_from_directory('dirname', config)
        raise Exception('unknown test_type')

    def test_filtered_config_passed_to_lint_job_xml(self, test_type, mocker):
        mocker.patch('jenkins_job_linter.config.LINTERS', {})
        mocker.patch('jenkins_job_linter.config.GLOBAL_CONFIG_DEFAULTS', {})
        config = configparser.ConfigParser()
        config.read_dict({'jenkins': {},
                          'job_builder': {},
                          'something_else': {},
                          'job_linter': {}})
        lint_job_xml_mock = self._setup_mocks(test_type, mocker)
        self._do_call(test_type, mocker, config)
        passed_config = lint_job_xml_mock.call_args[0][3]
        assert ['job_linter'] == passed_config.sections()

    def test_config_passed_in_isnt_modified(self, test_type, mocker):
        self._setup_mocks(test_type, mocker)
        config = configparser.ConfigParser()
        config.read_dict({'jenkins': {},
                          'job_builder': {},
                          'something_else': {},
                          'job_linter': {}})
        expected_sections_after = config.sections()
        self._do_call(test_type, mocker, config)
        assert expected_sections_after == config.sections()

    def test_defaults_used(self, test_type, mocker):
        lint_job_xml_mock = self._setup_mocks(test_type, mocker)
        defaults = {'test': 'this'}
        mocker.patch('jenkins_job_linter.config.GLOBAL_CONFIG_DEFAULTS',
                     defaults)
        self._do_call(test_type, mocker, configparser.ConfigParser())
        passed_config = lint_job_xml_mock.call_args[0][3]
        assert passed_config['job_linter']['test'] == 'this'


class TestLintJobsFromDirectory:

    def test_empty_directory(self, mocker):
        listdir_mock = mocker.patch('jenkins_job_linter.os.listdir')
        listdir_mock.return_value = []
        assert lint_jobs_from_directory('dir', mocker.MagicMock())

    def test_context_job_name_and_tree_passed_to_lint_job_xml(self, mocker):
        listdir_mock = mocker.patch('jenkins_job_linter.os.listdir')
        listdir_mock.return_value = ['some', 'files']
        et_parse_mock = mocker.patch('jenkins_job_linter.ElementTree.parse')
        lint_job_xml_mock = mocker.patch('jenkins_job_linter.lint_job_xml')
        runcontext_mock = mocker.patch('jenkins_job_linter.RunContext')
        lint_jobs_from_directory('dir', mocker.MagicMock())
        assert len(listdir_mock.return_value) == lint_job_xml_mock.call_count
        for filename in listdir_mock.return_value:
            assert (
                mocker.call(runcontext_mock.return_value, filename,
                            et_parse_mock.return_value, mocker.ANY)
                in lint_job_xml_mock.call_args_list)

    def test_passed_directory_is_used_for_listing(self, mocker):
        listdir_mock = mocker.patch('jenkins_job_linter.os.listdir')
        listdir_mock.return_value = []
        dirname = 'dir'
        lint_jobs_from_directory(dirname, mocker.MagicMock())
        assert mocker.call(dirname) == listdir_mock.call_args

    def test_constructed_paths_used_for_parsing(self, mocker):
        listdir_mock = mocker.patch('jenkins_job_linter.os.listdir')
        listdir_mock.return_value = ['some', 'files']
        et_parse_mock = mocker.patch('jenkins_job_linter.ElementTree.parse')
        mocker.patch('jenkins_job_linter.lint_job_xml')
        dirname = 'dir'
        lint_jobs_from_directory(dirname, mocker.MagicMock())
        expected_paths = set(
            os.path.join(dirname, f) for f in listdir_mock.return_value)
        assert expected_paths == set(
            [call_args[0][0] for call_args in et_parse_mock.call_args_list])

    def test_listdir_return_used_as_object_list(self, mocker):
        listdir_mock = mocker.patch('jenkins_job_linter.os.listdir')
        listdir_mock.return_value = ['some', 'files']
        mocker.patch('jenkins_job_linter.ElementTree.parse')
        lint_job_xml_mock = mocker.patch('jenkins_job_linter.lint_job_xml')
        lint_jobs_from_directory('dir', mocker.MagicMock())
        passed_ctx = lint_job_xml_mock.call_args[0][0]
        assert listdir_mock.return_value == passed_ctx.object_names


class TestLintJobsFromRunningJenkins:

    def test_parameters_passed_through_to_jenkins(self, mocker):
        jenkins_mock = mocker.patch('jenkins_job_linter.jenkins.Jenkins')
        url, username, password = 'url', 'username', 'password'

        lint_jobs_from_running_jenkins(
            url, username, password, mocker.MagicMock())

        assert 1 == jenkins_mock.call_count
        assert mocker.call(url, username=username,
                           password=password) == jenkins_mock.call_args

    def test_empty_jenkins(self, mocker):
        jenkins_mock = mocker.patch('jenkins_job_linter.jenkins.Jenkins')
        jenkins_mock.return_value.get_jobs.return_value = []

        assert lint_jobs_from_running_jenkins(
            'url', 'username', 'password', mocker.MagicMock())

    def test_context_job_name_and_tree_passed_to_lint_job_xml(self, mocker):
        job_names = ['a job', 'another job']
        jenkins_mock = mocker.patch('jenkins_job_linter.jenkins.Jenkins')
        jenkins_mock.return_value.get_jobs.return_value = [
            {'name': name} for name in job_names]
        et_mock = mocker.patch('jenkins_job_linter.ElementTree')
        lint_job_xml_mock = mocker.patch('jenkins_job_linter.lint_job_xml')
        runcontext_mock = mocker.patch('jenkins_job_linter.RunContext')

        lint_jobs_from_running_jenkins(
            'url', 'username', 'password', mocker.MagicMock())

        assert len(job_names) == lint_job_xml_mock.call_count
        for job_name in job_names:
            assert (
                mocker.call(runcontext_mock.return_value, job_name,
                            et_mock.ElementTree.return_value, mocker.ANY)
                in lint_job_xml_mock.call_args_list)

    def test_job_xml_parsed_and_passed(self, mocker):
        job_names = ['a job']
        jenkins_mock = mocker.patch('jenkins_job_linter.jenkins.Jenkins')
        jenkins_mock.return_value.get_jobs.return_value = [
            {'name': name} for name in job_names]
        xml_string = b'<element />'
        jenkins_mock.return_value.get_job_config.return_value = xml_string
        lint_job_xml_mock = mocker.patch('jenkins_job_linter.lint_job_xml')

        lint_jobs_from_running_jenkins(
            'url', 'username', 'password', mocker.MagicMock())

        element_tree = lint_job_xml_mock.call_args[0][2]
        assert xml_string == ElementTree.tostring(element_tree.getroot())

    def test_returned_job_list_used_as_object_list(self, mocker):
        job_names = ['a job', 'another job']
        jenkins_mock = mocker.patch('jenkins_job_linter.jenkins.Jenkins')
        jenkins_mock.return_value.get_jobs.return_value = [
            {'name': name} for name in job_names]
        mocker.patch('jenkins_job_linter.ElementTree')
        lint_job_xml_mock = mocker.patch('jenkins_job_linter.lint_job_xml')

        lint_jobs_from_running_jenkins(
            'url', 'username', 'password', mocker.MagicMock())

        passed_ctx = lint_job_xml_mock.call_args[0][0]
        assert job_names == passed_ctx.object_names


class TestLintDirectory:

    def test_argument_passed_through(self, mocker):
        runner = CliRunner()
        dirname = 'some_dir'
        lint_jobs_mock = mocker.patch(
            'jenkins_job_linter.lint_jobs_from_directory')

        with runner.isolated_filesystem():
            os.mkdir(dirname)
            runner.invoke(main, ['lint-directory', dirname])

        assert 1 == lint_jobs_mock.call_count
        assert mocker.call(dirname, mocker.ANY) == lint_jobs_mock.call_args

    def test_config_parsed_and_passed(self, mocker):
        runner = CliRunner()
        lint_jobs_mock = mocker.patch(
            'jenkins_job_linter.lint_jobs_from_directory')
        dirname = 'dirname'
        config = '[job_linter]\nkey=value'
        with runner.isolated_filesystem():
            os.mkdir(dirname)
            with open('config.ini', 'w') as config_ini:
                config_ini.write(config)
            runner.invoke(
                main, ['--conf', 'config.ini', 'lint-directory', dirname])

        assert 1 == lint_jobs_mock.call_count
        config = lint_jobs_mock.call_args[0][1]
        assert config['job_linter']['key'] == 'value'

    @pytest.mark.parametrize('return_value,exit_code', ((False, 1), (True, 0)))
    def test_exit_code(self, mocker, exit_code, return_value):
        runner = CliRunner()
        lint_jobs_mock = mocker.patch(
            'jenkins_job_linter.lint_jobs_from_directory')
        lint_jobs_mock.return_value = return_value
        dirname = 'some_dir'
        with runner.isolated_filesystem():
            os.mkdir(dirname)
            result = runner.invoke(main, ['lint-directory', dirname])
        assert exit_code == result.exit_code

    @pytest.mark.parametrize('func', [
        # Non-existent directory
        lambda dirname: None,
        # Directory is a file
        lambda dirname: open(dirname, 'a').close(),
        # Directory isn't readable ("or" because os.mkdir returns None)
        lambda dirname: os.mkdir(dirname) or os.chmod(dirname, 0o000),
    ])
    def test_bad_directory_input(self, func, mocker):
        runner = CliRunner()
        lint_jobs_mock = mocker.patch(
            'jenkins_job_linter.lint_jobs_from_directory')
        dirname = 'dirname'
        with runner.isolated_filesystem():
            func(dirname)
            result = runner.invoke(main, ['lint-directory', dirname])
        assert result.exit_code != 0
        assert lint_jobs_mock.call_count == 0

    @pytest.mark.parametrize('func', [
        # Non-existent conf file
        lambda conf: None,
        # Conf file is a directory
        lambda conf: os.mkdir(conf),
        # File isn't readable ("or" because .close() returns None)
        lambda conf: open(conf, 'a').close() or os.chmod(conf, 0o000),
    ])
    def test_bad_config_input(self, func, mocker):
        runner = CliRunner()
        lint_jobs_mock = mocker.patch(
            'jenkins_job_linter.lint_jobs_from_directory')
        dirname = 'dirname'
        conf = 'conf.ini'
        with runner.isolated_filesystem():
            os.mkdir(dirname)
            func(conf)
            result = runner.invoke(
                main, ['--conf', conf, 'lint-directory', dirname])
        assert result.exit_code != 0
        assert lint_jobs_mock.call_count == 0


class TestLintJenkins:

    def test_arguments_passed_through(self, mocker):
        runner = CliRunner()
        lint_jobs_mock = mocker.patch(
            'jenkins_job_linter.lint_jobs_from_running_jenkins')

        url, username, password = 'url', 'username', 'password'

        with runner.isolated_filesystem():
            runner.invoke(main, ['lint-jenkins',
                                 '--jenkins-url', url,
                                 '--jenkins-username', username,
                                 '--jenkins-password', password])

        assert 1 == lint_jobs_mock.call_count
        assert mocker.call(
            url, username, password, mocker.ANY) == lint_jobs_mock.call_args

    def test_envvars_passed_through(self, mocker, monkeypatch):
        runner = CliRunner()
        lint_jobs_mock = mocker.patch(
            'jenkins_job_linter.lint_jobs_from_running_jenkins')

        url, username, password = 'url', 'username', 'password'
        monkeypatch.setenv('JENKINS_URL', url)
        monkeypatch.setenv('JENKINS_USERNAME', username)
        monkeypatch.setenv('JENKINS_PASSWORD', password)

        with runner.isolated_filesystem():
            runner.invoke(main, ['lint-jenkins'])

        assert 1 == lint_jobs_mock.call_count
        assert mocker.call(
            url, username, password, mocker.ANY) == lint_jobs_mock.call_args

    def test_config_parsed_and_passed(self, mocker):
        runner = CliRunner()
        lint_jobs_mock = mocker.patch(
            'jenkins_job_linter.lint_jobs_from_running_jenkins')

        config = '[job_linter]\nkey=value'
        with runner.isolated_filesystem():
            with open('config.ini', 'w') as config_ini:
                config_ini.write(config)
            runner.invoke(
                main, ['--conf', 'config.ini', 'lint-jenkins',
                       '--jenkins-url', 'url',
                       '--jenkins-username', 'username',
                       '--jenkins-password', 'password'])

        assert 1 == lint_jobs_mock.call_count
        config = lint_jobs_mock.call_args[0][-1]
        assert config['job_linter']['key'] == 'value'

    @pytest.mark.parametrize('return_value,exit_code', ((False, 1), (True, 0)))
    def test_exit_code(self, mocker, exit_code, return_value):
        runner = CliRunner()
        lint_jobs_mock = mocker.patch(
            'jenkins_job_linter.lint_jobs_from_running_jenkins')
        lint_jobs_mock.return_value = return_value
        with runner.isolated_filesystem():
            result = runner.invoke(main, ['lint-jenkins',
                                          '--jenkins-url', 'url',
                                          '--jenkins-username', 'username',
                                          '--jenkins-password', 'password'])
        assert exit_code == result.exit_code

    @pytest.mark.parametrize('func', [
        # Non-existent conf file
        lambda conf: None,
        # Conf file is a directory
        lambda conf: os.mkdir(conf),
        # File isn't readable ("or" because .close() returns None)
        lambda conf: open(conf, 'a').close() or os.chmod(conf, 0o000),
    ])
    def test_bad_config_input(self, func, mocker):
        runner = CliRunner()
        lint_jobs_mock = mocker.patch(
            'jenkins_job_linter.lint_jobs_from_running_jenkins')
        conf = 'conf.ini'
        with runner.isolated_filesystem():
            func(conf)
            result = runner.invoke(
                main, ['--conf', conf, 'lint-jenkins',
                       '--jenkins-url', 'url',
                       '--jenkins-username', 'username',
                       '--jenkins-password', 'password'])
        assert result.exit_code != 0
        assert lint_jobs_mock.call_count == 0
