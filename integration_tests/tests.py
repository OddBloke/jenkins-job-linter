import inspect
import os
import subprocess
from collections import namedtuple

import yaml


def runner(tmpdir):
    output_dir = os.path.join(tmpdir, 'output')
    subprocess.check_call([
        'jenkins-jobs', 'test', os.path.join(tmpdir), '-o', output_dir])
    try:
        output = subprocess.check_output(['jenkins-job-linter', output_dir])
    except subprocess.CalledProcessError as exc:
        output = exc.output
    return output.decode('utf-8')


def test_integration(tmpdir, integration_testcase):
    tmpdir.join('jobs.yaml').write(integration_testcase.jobs_yaml)
    output = runner(tmpdir)
    assert integration_testcase.expected_output == output


IntegrationTestcase = namedtuple('IntegrationTestcase',
                                 ['test_name', 'jobs_yaml', 'expected_output'])


def _parse_testcases(filename):
    with open(filename) as f:
        data = yaml.safe_load(f)
    for case_dict in data['cases']:
        yield IntegrationTestcase(case_dict['name'], case_dict['jobs.yaml'],
                                  case_dict['expected_output'])


def pytest_generate_tests(metafunc):
    test_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
    test_cases = _parse_testcases(os.path.join(test_dir, 'tests.ini'))
    metafunc.parametrize('integration_testcase', test_cases)
