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
import inspect
import os
import subprocess
from collections import namedtuple

import pytest
import yaml


JJB_CONFIG = '''\
[job_builder]
ignore_cache=True

[jenkins]
url=http://0.0.0.0:8080/
user=XXX
password=XXX
'''


def _direct_runner(tmpdir, config):
    output_dir = os.path.join(tmpdir, 'output')
    subprocess.check_call([
        'jenkins-jobs', 'test', os.path.join(tmpdir), '-o', output_dir])
    config_args = []
    if config is not None:
        conf_file = tmpdir.join('config.ini')
        conf_file.write(config)
        config_args = ['--conf', str(conf_file)]
    success = True
    try:
        output = subprocess.check_output(['jenkins-job-linter', output_dir]
                                         + config_args)
    except subprocess.CalledProcessError as exc:
        output = exc.output
        success = False
    return success, output.decode('utf-8')


def _jjb_subcommand_runner(tmpdir, config):
    config_args = []
    if config is not None:
        conf_file = tmpdir.join('config.ini')
        config = '\n'.join([JJB_CONFIG, config])
        conf_file.write(config)
        config_args = ['--conf', str(conf_file)]
    success = True
    try:
        output = subprocess.check_output([
            'jenkins-jobs'] + config_args + ['lint', os.path.join(tmpdir)])
    except subprocess.CalledProcessError as exc:
        output = exc.output
        success = False
    return success, output.decode('utf-8')


@pytest.fixture(params=['direct', 'jjb_subcommand'])
def runner(request):
    runner_funcs = {
        'direct': _direct_runner,
        'jjb_subcommand': _jjb_subcommand_runner,
    }
    return runner_funcs[request.param]


def test_integration(runner, tmpdir, integration_testcase):
    tmpdir.join('jobs.yaml').write(integration_testcase.jobs_yaml)
    success, output = runner(tmpdir, integration_testcase.config)
    assert integration_testcase.expected_output == output
    assert integration_testcase.expect_success == success


IntegrationTestcase = namedtuple(
    'IntegrationTestcase',
    ['test_name', 'jobs_yaml', 'expected_output', 'expect_success', 'config'])


def _parse_testcases(filename):
    names = set()
    with open(filename) as f:
        data = yaml.safe_load(f)
    for case_dict in data['cases']:
        name = case_dict['name']
        if name in names:
            raise Exception('Duplicate test name: {}'.format(name))
        names.add(name)
        yield IntegrationTestcase(name, case_dict['jobs.yaml'],
                                  case_dict['expected_output'],
                                  case_dict['expect_success'],
                                  case_dict.get('config', None))


def pytest_generate_tests(metafunc):
    test_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
    test_cases = _parse_testcases(os.path.join(test_dir, 'tests.yaml'))
    if 'integration_testcase' in metafunc.fixturenames:
        metafunc.parametrize('integration_testcase', test_cases,
                             ids=lambda testcase: testcase.test_name)
