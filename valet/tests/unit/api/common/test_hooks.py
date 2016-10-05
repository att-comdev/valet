'''
Created on Sep 29, 2016

@author: stack
'''

import mock
import valet.api.common.hooks as hooks
from valet.api.common.hooks import MessageNotificationHook
from valet.tests.unit.api.v1.api_base import ApiBase


class TestHooks(ApiBase):

    def setUp(self):
        super(TestHooks, self).setUp()

        self.message_notification_hook = MessageNotificationHook()

    @mock.patch.object(hooks, 'conf')
    @mock.patch.object(hooks, 'webob')
    def test_after(self, mock_bob, mock_conf):
        mock_bob.exc.status_map = {"test_status_code": State}
        mock_bob.exc.HTTPOk = State
        mock_conf.messaging.notifier.return_value = "notifier"
        self.message_notification_hook.after(State)

        self.validate_test(mock_conf.messaging.notifier.info.called)

        mock_bob.exc.HTTPOk = ApiBase
        self.message_notification_hook.after(State)
        self.validate_test(mock_conf.messaging.notifier.error.called)


class State(object):
    class response(object):
        status_code = "test_status_code"
        body = "test_body"

    class request(object):
        path = "test_path"
        method = "test_method"
        body = "test_req_body"
        context = {'tenant_id': 'test_tenant_id', 'user_id': 'test_user_id'}

        @classmethod
        def path_info_pop(cls):
            return None
