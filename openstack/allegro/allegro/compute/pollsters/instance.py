#
# Copyright 2012 eNovance <licensing@enovance.com>
# Copyright 2012 Red Hat, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from allegro.compute import pollsters
from allegro.compute.pollsters import util
from allegro import sample


class InstancePollster(pollsters.BaseComputePollster):

    @staticmethod
    def get_samples(manager, cache, resources):
        for instance in resources:
            yield util.make_sample_from_instance(
                instance,
                name='instance',
                type=sample.TYPE_GAUGE,
                unit='instance',
                volume=1,
            )