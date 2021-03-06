#
# Copyright 2014-2017 AT&T Intellectual Property
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Plugin."""

import os

from tempest import config
from tempest.test_discover import plugins
from valet.tests.tempest import config as project_config

import valet


class ValetTempestPlugin(plugins.TempestPlugin):
    """Plugins for Valet Tempest Testing."""

    def load_tests(self):
        """Load tempest tests, return full test dir and base path."""
        base_path = os.path.split(os.path.dirname(
            os.path.abspath(valet.__file__)))[0]
        test_dir = "valet/tests/tempest"
        full_test_dir = os.path.join(base_path, test_dir)
        return full_test_dir, base_path

    def register_opts(self, conf):
        """Register opt groups in config."""
        config.register_opt_group(conf, project_config.service_available_group,
                                  project_config.ServiceAvailableGroup)

        config.register_opt_group(conf, project_config.placement_group,
                                  project_config.PlacementGroup)

        config.register_opt_group(conf, project_config.valet_group,
                                  project_config.opt_valet)

    def get_opt_lists(self):
        """Get Opt Lists."""
        pass
