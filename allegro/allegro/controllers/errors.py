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

'''Errors'''

from allegro.i18n import _

from pecan import expose, request, response

# pylint: disable=R0201


def error_wrapper(func):
    '''Error decorator.'''
    def func_wrapper(self, **kwargs):
        '''Wrapper function for error decorator.'''
        # Call the controller method
        kwargs = func(self, **kwargs)

        # Prep the actual error
        # Modeled after Apple's error APIs at present.
        # TODO: Use OpenStack format?
        message = kwargs.get('message', _('Undocumented error'))
        internal_message = kwargs.get('internal', response.status)
        status = kwargs.get('status', response.status_code)
        info = kwargs.get('info', _('No remediation available'))

        # TODO: Support multiple errors?
        return {
            "errors": [{
                "userMessage": message,
                "internalMessage": internal_message,
                "code": status,
                "info": info,
            }]
        }
    return func_wrapper

# TODO: Pass in the rest of kwargs along with the message
class ErrorsController(object):
    '''
    Errors Controller
    /errors/{error_name}
    '''

    @expose('json')
    @error_wrapper
    def schema(self):
        '''400'''
        msg = str(request.validation_error)
        response.status = 400
        return dict(message=msg)

    @expose('json')
    @error_wrapper
    def invalid(self, **kw):
        '''400'''
        msg = kw.get(
            'error_message',
            _('invalid request')
        )
        response.status = 400
        return dict(message=msg)

    @expose()
    def unauthorized(self):
        '''401'''
        # Don't return any implementation details.
        response.status = 401
        response.content_type = 'text/plain'
        response.body = _('Authentication required')
        return response

    @expose('json')
    @error_wrapper
    def forbidden(self, **kw):
        '''403'''
        msg = kw.get(
            'error_message',
            _('forbidden')
        )
        response.status = 403
        return dict(message=msg)

    @expose('json')
    @error_wrapper
    def not_found(self, **kw):
        '''404'''
        msg = kw.get(
            'error_message',
            _('resource was not found')
        )
        response.status = 404
        return dict(message=msg)

    @expose('json')
    @error_wrapper
    def not_allowed(self, **kw):
        '''405'''
        msg = kw.get(
            'error_message',
            _('method not allowed')
        )
        kwargs = request.context.get('kwargs')
        allow = kwargs.get('allow', None)
        if allow:
            response.headers['Allow'] = allow
        response.status = 405
        return dict(message=msg)

    @expose('json')
    @error_wrapper
    def conflict(self, **kw):
        '''409'''
        msg = kw.get(
            'error_message',
            _('conflict')
        )
        response.status = 409
        return dict(message=msg)

    @expose('json')
    @error_wrapper
    def server_error(self, **kw):
        '''500'''
        msg = kw.get(
            'error_message',
            _('server error'),
        )
        response.status = 500
        return dict(message=msg)

    @expose('json')
    @error_wrapper
    def unavailable(self, **kw):
        '''503'''
        msg = kw.get(
            'error_message',
            _('service unavailable'),
        )
        response.status = 503
        return dict(message=msg)
