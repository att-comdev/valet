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

from pecan import conf, expose, redirect, request, response


def error_wrapper(func):
    '''Error decorator.'''
    def func_wrapper(self, **kwargs):
        # Call the controller method
        kwargs = func(self, **kwargs)

        # Prep the actual error
        # Modeled after Apple's error APIs at present.
        # TODO: Use OpenStack format?
        message = kwargs.get('message', 'Undocumented error')
        internalMessage = kwargs.get('internal', response.status)
        status = kwargs.get('status', response.status_code)
        info = kwargs.get('info', 'No remediation available')

        # TODO: Support multiple errors?
        return {
            "errors": [{
                "userMessage": message,
                "internalMessage": internalMessage,
                "code": status,
                "info": info,
            }]
        }
    return func_wrapper

# TODO: Pass in the rest of kwargs along with the message
class ErrorsController(object):
    '''Error handling controller'''
    @expose('json')
    @error_wrapper
    def schema(self, **kw):
        msg = str(request.validation_error)
        response.status = 400
        return dict(message=msg)

    @expose('json')
    @error_wrapper
    def invalid(self, **kw):
        msg = kw.get(
            'error_message',
            'invalid request'
        )
        response.status = 400
        return dict(message=msg)

    @expose('json')
    @error_wrapper
    def unauthorized(self, **kw):
        msg = kw.get(
            'error_message',
            'authorization required'
        )
        response.status = 401
        return dict(message=msg)

    @expose('json')
    @error_wrapper
    def forbidden(self, **kw):
        msg = kw.get(
            'error_message',
            'forbidden'
        )
        response.status = 403
        return dict(message=msg)

    @expose('json')
    @error_wrapper
    def not_found(self, **kw):
        msg = kw.get(
            'error_message',
            'resource was not found'
        )
        response.status = 404
        return dict(message=msg)

    @expose('json')
    @expose('json')
    @error_wrapper
    def not_allowed(self, **kw):
        msg = kw.get(
            'error_message',
            'method not allowed'
        )
        response.status = 405
        return dict(message=msg)

    @error_wrapper
    def conflict(self, **kw):
        msg = kw.get(
            'error_message',
            'conflict'
        )
        response.status = 409
        return dict(message=msg)

    @expose('json')
    @error_wrapper
    def server_error(self, **kw):
        msg = kw.get(
            'error_message',
            'server error',
        )
        response.status = 500
        return dict(message=msg)

    @expose('json')
    @error_wrapper
    def unavailable(self, **kw):
        msg = kw.get(
            'error_message',
            'service unavailable',
        )
        response.status = 503
        return dict(message=msg)
