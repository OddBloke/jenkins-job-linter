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
"""Handle configuration for jenkins-job-linter."""
from configparser import ConfigParser
from typing import Any, Dict  # noqa

CONFIG_DEFAULTS = {
    'job_linter': {
        'disable_linters': [],
    },
    'job_linter:check_shebang': {
        'allow_default_shebang': True,
    },
}  # type: Dict[str, Dict[str, Any]]


def _filter_config(config: ConfigParser) -> ConfigParser:
    """
    Return a ConfigParser with only the job_linter section of the one passed.

    This creates a new ConfigParser and removes sections from that, so the one
    passed in remains unmodified.
    """
    filtered_config = ConfigParser()
    filtered_config.read_dict(CONFIG_DEFAULTS)
    filtered_config.read_dict(config)
    for section in filtered_config.sections():
        if not section.startswith('job_linter'):
            filtered_config.remove_section(section)
    return filtered_config
