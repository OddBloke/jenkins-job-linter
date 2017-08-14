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
from typing import Any, Dict, List, cast

from jenkins_job_linter.linters import LINTERS

GLOBAL_CONFIG_DEFAULTS = {
    'disable_linters': [],
    'only_run': None,
}  # type: Dict[str, Any]


class GetListConfigParser(ConfigParser):
    """A ConfigParser subclass that implements a getlist method."""

    def getlist(self, section: str, option: str,
                *args: Any, **kwargs: Any) -> List[str]:
        """Parse an option, splitting it by commas and stripping whitespace."""
        def commas_to_list(value: str) -> List[str]:
            if not value:
                return []
            return [item.strip() for item in value.split(',')]

        # These type shenanigans can be removed once
        # https://github.com/python/typeshed/pull/1542 is released
        ret = self._get_conv(  # type: ignore
            section, option, commas_to_list, *args, **kwargs)
        return cast(List[str], ret)


def _get_default_linter_configs() -> Dict[str, Dict[str, Any]]:
    return {'job_linter:{}'.format(name): linter.default_config
            for name, linter in LINTERS.items()}


def _filter_config(config: ConfigParser) -> GetListConfigParser:
    """
    Return a ConfigParser with only the job_linter section of the one passed.

    This creates a new ConfigParser and removes sections from that, so the one
    passed in remains unmodified.
    """
    filtered_config = GetListConfigParser(allow_no_value=True)
    filtered_config.read_dict({'job_linter': GLOBAL_CONFIG_DEFAULTS})
    filtered_config.read_dict(_get_default_linter_configs())
    filtered_config.read_dict(config)
    for section in filtered_config.sections():
        if not section.startswith('job_linter'):
            filtered_config.remove_section(section)
    return filtered_config
