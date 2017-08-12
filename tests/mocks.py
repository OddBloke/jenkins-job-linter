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
from configparser import ConfigParser
from unittest import mock

from jenkins_job_linter import _filter_config
from jenkins_job_linter.linters import Linter, LintResult

NAMES = ('linter-{}'.format(num) for num in itertools.count())


def create_linter_mock(check_result=LintResult.PASS, check_msg=None,
                       default_config=None, **kwargs):
    linter_mock = mock.create_autospec(Linter)
    linter_mock.return_value.check.return_value = check_result, check_msg
    linter_mock.default_config = default_config or {}
    return linter_mock, kwargs


def create_mock_for_class(cls, **kwargs):
    special_cases = {
        Linter: create_linter_mock,
    }
    if cls in special_cases:
        created_mock, kwargs = special_cases[cls](**kwargs)
    else:
        created_mock = mock.create_autospec(cls)
    for key, value in kwargs.items():
        setattr(created_mock, key, value)
    return created_mock


def get_config():
    return _filter_config(ConfigParser())


def mock_LINTERS(mocker, linter_mocks):
    linters = dict(zip(NAMES, linter_mocks))
    mocker.patch('jenkins_job_linter.LINTERS', linters)
    mocker.patch('jenkins_job_linter.config.LINTERS', linters)
    return linters
