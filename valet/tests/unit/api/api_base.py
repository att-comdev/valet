'''
Created on Sep 25, 2016

@author: stack
'''

import mock
import pecan
from valet.tests.base import Base


class ApiBase(Base):

    def __init__(self, *args, **kwds):
        super(ApiBase, self).__init__(*args, **kwds)
        pecan.conf.identity = mock.MagicMock()
        ApiBase.response = None

    @classmethod
    def mock_error(cls, url, msg=None, **kwargs):
        ApiBase.response = msg
