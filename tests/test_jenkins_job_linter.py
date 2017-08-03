import os

import pytest
from click.testing import CliRunner

from jenkins_job_linter import lint_job_xml, lint_jobs_from_directory, main


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


class TestLintJobsFromDirectory(object):

    def test_empty_directory(self, mocker):
        listdir_mock = mocker.patch('jenkins_job_linter.os.listdir')
        listdir_mock.return_value = []
        assert lint_jobs_from_directory('dir')

    def test_parsed_tree_passed_to_lint_job_xml(self, mocker):
        listdir_mock = mocker.patch('jenkins_job_linter.os.listdir')
        listdir_mock.return_value = ['some', 'files']
        et_parse_mock = mocker.patch('jenkins_job_linter.ElementTree.parse')
        lint_job_xml_mock = mocker.patch('jenkins_job_linter.lint_job_xml')
        lint_jobs_from_directory('dir')
        assert len(listdir_mock.return_value) == lint_job_xml_mock.call_count
        for call_args in lint_job_xml_mock.call_args_list:
            assert mocker.call(et_parse_mock.return_value) == call_args

    def test_passed_directory_is_used_for_listing(self, mocker):
        listdir_mock = mocker.patch('jenkins_job_linter.os.listdir')
        listdir_mock.return_value = []
        dirname = 'dir'
        lint_jobs_from_directory(dirname)
        assert mocker.call(dirname) == listdir_mock.call_args

    def test_constructed_paths_used_for_parsing(self, mocker):
        listdir_mock = mocker.patch('jenkins_job_linter.os.listdir')
        listdir_mock.return_value = ['some', 'files']
        et_parse_mock = mocker.patch('jenkins_job_linter.ElementTree.parse')
        mocker.patch('jenkins_job_linter.lint_job_xml')
        dirname = 'dir'
        lint_jobs_from_directory(dirname)
        expected_paths = set(
            os.path.join(dirname, f) for f in listdir_mock.return_value)
        assert expected_paths == set(
            [call_args[0][0] for call_args in et_parse_mock.call_args_list])


class TestMain(object):

    def test_argument_passed_through(self, mocker):
        runner = CliRunner()
        dirname = 'some_dir'
        lint_jobs_mock = mocker.patch(
            'jenkins_job_linter.lint_jobs_from_directory')

        with runner.isolated_filesystem():
            os.mkdir(dirname)
            runner.invoke(main, [dirname])

        assert 1 == lint_jobs_mock.call_count
        assert mocker.call(dirname) == lint_jobs_mock.call_args

    @pytest.mark.parametrize('return_value,exit_code', ((False, 1), (True, 0)))
    def test_exit_code(self, mocker, exit_code, return_value):
        runner = CliRunner()
        lint_jobs_mock = mocker.patch(
            'jenkins_job_linter.lint_jobs_from_directory')
        lint_jobs_mock.return_value = return_value
        dirname = 'some_dir'
        with runner.isolated_filesystem():
            os.mkdir(dirname)
            result = runner.invoke(main, [dirname])
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
            result = runner.invoke(main, [dirname])
        assert result.exit_code != 0
        assert lint_jobs_mock.call_count == 0
