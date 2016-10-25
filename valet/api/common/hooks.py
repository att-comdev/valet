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

import json
import logging
from valet.api.common.i18n import _
from valet.api.v1.controllers import error

from pecan import conf
from pecan.hooks import PecanHook
import webob

LOG = logging.getLogger(__name__)


class MessageNotificationHook(PecanHook):
    '''Send API request/responses out as Oslo msg notifications.'''
    def after(self, state):
        LOG.info('sending notification')
        notifier = conf.messaging.notifier
        status_code = state.response.status_code
        status = webob.exc.status_map.get(status_code)

        if issubclass(status, webob.exc.HTTPOk):
            notifier_fn = notifier.info
        else:
            notifier_fn = notifier.error

        ctxt = {}  # Not using this just yet.

        request_path = state.request.path

        event_type_parts = ['api']
        api_version = state.request.path_info_pop()
        if api_version:
            event_type_parts.append(api_version)
        api_subject = state.request.path_info_pop()
        if api_subject:
            event_type_parts.append(api_subject)
        event_type = '.'.join(event_type_parts)

        request_method = state.request.method
        try:
            request_body = json.loads(state.request.body)
        except ValueError:
            request_body = None
        try:
            response_body = json.loads(state.response.body)
        except ValueError:
            response_body = state.response.body

        tenant_id = state.request.context.get('tenant_id', None)
        user_id = state.request.context.get('user_id', None)

        payload = {
            'context': {
                'tenant_id': tenant_id,
                'user_id': user_id,
            },
            'request': {
                'method': request_method,
                'path': request_path,
                'body': request_body,
            },
            'response': {
                'status_code': status_code,
                'body': response_body,
            }
        }
        notifier_fn(ctxt, event_type, payload)
        LOG.info('valet notification - sent')


class NotFoundHook(PecanHook):
    '''Catchall 'not found' hook for API'''
    def on_error(self, state, exc):
        '''Redirects to app-specific not_found endpoint if 404 only'''
        if isinstance(exc, webob.exc.WSGIHTTPException):
            if exc.code == 404:
                message = _('The resource could not be found.')
                error('/errors/not_found', message)
