from pecan import expose, response, request


def error_wrapper(func):
    def func_wrapper(self, **kwargs):
        kwargs = func(self, **kwargs)
        message = kwargs.get('message', 'undocumented error')
        status = kwargs.get('status', None)
        internalMessage = None
        if not status:
           status = response.status_code
           internalMessage = response.status
        return {
            "errors": [{
                "userMessage": message,
                "internalMessage": internalMessage,
                "code": status,
                "info": None,
            }]
        }
    return func_wrapper

class ErrorsController(object):

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
    def not_allowed(self, **kw):
        msg = kw.get(
            'error_message',
            'method not allowed'
        )
        response.status = 405
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
    @error_wrapper
    def unavailable(self, **kw):
        msg = kw.get(
            'error_message',
            'service unavailable',
        )
        response.status = 503
        return dict(message=msg)
