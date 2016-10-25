# -*- encoding: utf-8 -*-
#
# Copyright (c) 2014-2016 AT&T
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.

'''Application'''

from pecan import make_app, deploy

from valet.api.common import identity, messaging
from valet.api.db import models
from config import register_conf, set_valet_conf


def setup_app(config):
    """ App Setup """
    identity.init_identity()
    messaging.init_messaging()
    models.init_model()
    app_conf = dict(config.app)

    return make_app(
        app_conf.pop('root'),
        logging=getattr(config, 'logging', {}), **app_conf)


# entry point for apache2
def load_app(config_file):
    register_conf()
    set_valet_conf('/etc/valet/valet.conf')
    return deploy(config_file)
