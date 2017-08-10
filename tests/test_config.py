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

from jenkins_job_linter import _filter_config


class TestFilterConfig:

    def test_filter_by_prefix(self, mocker):
        mocker.patch('jenkins_job_linter.config.CONFIG_DEFAULTS', {})
        config = configparser.ConfigParser()
        wont_filter = ['job_linter', 'job_linter:linter', 'job_linter-thing']
        will_filter = ['jenkins', 'jenkins_jobs', 'whatever-else']
        config.read_dict({k: {} for k in wont_filter + will_filter})
        filtered_config = _filter_config(config)
        assert set(wont_filter) == set(filtered_config.sections())
