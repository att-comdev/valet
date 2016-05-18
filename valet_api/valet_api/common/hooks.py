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

'''Hooks'''

from pecan.hooks import PecanHook

from valet_api.common.i18n import _
from valet_api.controllers import error

import webob


class NotFoundHook(PecanHook):
    '''Catchall 'not found' hook for API'''
    def on_error(self, state, exc):
        '''Redirects to app-specific not_found endpoint if 404 only'''
        if isinstance(exc, webob.exc.WSGIHTTPException):
            if exc.code == 404:
                message = _('The resource could not be found.')
                error('/errors/not_found', message)
