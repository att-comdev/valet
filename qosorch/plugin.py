#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

'''
plugin.py

Author: Joe D'Andrea
Created: 8 August 2014
Contact: jdandrea@research.att.com
'''

import inspect
import os.path
import urllib2
import pickle
import simplejson

from oslo_config import cfg
from oslo_log import log as logging

from heat.common.i18n import _
from heat.common import exception
from heat.db import api as db_api

LOG = logging.getLogger(__name__)


class ReservationPlugin(object):
    '''
    Base QoS Reservation Plugin Class

    This class is expected to be instantiated by ATT::QoS::Reservation.
    The reservation instance must be set via set_reservation before usage.
    '''

    def __init__(self, reservation):
        '''Plugin initialization.'''

        self._access_type = None
        self._bandwidth = None
        self._iops = None
        self._latency = None
        self._reservation = reservation

    @property
    def reservation(self):
        ''' Gets reservation that this plugin is associated with.'''
        return self._reservation

    @property
    def opt_name_str(self):
        '''
        Heat Config Option name for reservation service endpoints.
        This is the Reservation service plugin name, lower-cased,
        with '_uri' appended.
        '''
        opt_name = self.service_name.lower() + '_uri'
        return opt_name

    @property
    def _api_endpoint(self):
        '''
        Returns the reservation plugin's API endpoint URI.
        '''
        try:
            opt = getattr(cfg.CONF, self.reservation.opt_group_str)
            endpoint = opt[self.opt_name_str]
            if endpoint:
                return endpoint
            else:
                raise
        except:
            raise exception.Error(_('Reservation Endpoint %s not defined '
                                    'in heat.conf.' % self.service_name))

    def _db_key(self, key):
        '''
        Generate a plugin-specific database key in the format
        key + '.' + plugin filename (without extension).
        If the key is None, the return value is also None.
        '''
        if not key:
            return None
        filename = inspect.getfile(self.__class__)
        db_key = key + '.' + os.path.splitext(os.path.basename(filename))[0]
        return db_key

    def db_get(self, key=None):
        '''
        Get plugin dictionary for the reservation's current action.
        Given an optional key, get the value for just that key.

        If no underlying dictionary exists, or the key is otherwise None,
        this method returns None.
        '''

        data = None
        try:
            #db_key = self._db_key(self.reservation.action)
            db_key = self._db_key('reservation_plugin')
            value = db_api.resource_data_get(self.reservation, db_key)
        except exception.NotFound:
            value = None
        finally:
            if type(value) is str or type(value) is unicode:
                data = pickle.loads(value)

        if data and key:
            return data.get(key, None)
        return data

    def db_set(self, data, update=False):
        '''
        Set plugin dictionary for the reservation's current action.

        data is an input dictionary. update specifies if the existing
        dictionary is to be replaced (default behavior) or updated/merged.

        input dictionary keys set to None are always deleted in the
        resultant dictionary.

        If data is None and update is False (default), any existing dictionary
        will be deleted. If update is True, no existing dictionary changes
        are made.

        The current, resultant dictionary is always returned.
        '''

        #db_key = self._db_key(self.reservation.action)
        db_key = self._db_key('reservation_plugin')
        if data:
            # Get a copy of the dict or create a new one.
            current_data = self.db_get()
            if current_data:
                new_data = current_data.copy()
            else:
                new_data = {}

            # Merge the two and get rid of all the None values.
            new_data.update(data)
            new_data = dict((key, val) for key, val
                            in new_data.iteritems() if val)

            # Save the new dict.
            value = pickle.dumps(new_data)
            db_api.resource_data_set(self.reservation, db_key, value, redact=True)

            data = new_data
        elif not update:
            try:
                db_api.resource_data_delete(self.reservation, db_key)
            except:
                pass

        return data

    # TODO: Add Get Attribute anonymous function - optional support by plugins
    # Multiple plugins per reservation can place data in the backing store. Access
    # by reservation plugin name.

    @property
    def access_type(self):
        '''
        Returns the reservation's access type.
        '''

        if self._access_type is not None:
            return self._access_type

        self._access_type = self.reservation.properties.get(self.reservation.ACCESS_TYPE)

        return self._access_type

    @property
    def bandwidth(self):
        '''
        Returns the reservation's normalized bandwidth dictionary (min and max bps).
        '''

        if self._bandwidth is not None:
            return self._bandwidth

        bw_map = self.reservation.properties.get(self.reservation.BANDWIDTH)
        bw_min = bw_map.get(self.reservation.MIN)
        bw_max = bw_map.get(self.reservation.MAX)
        #bw_tolerance = bw_map.get(self.reservation.TOLERANCE)
        bw_units = bw_map.get(self.reservation.UNITS)

        # Convert bandwidth to bits/sec. This is a pre-validated value.
        if bw_units == self.reservation.KBPS:
            bw_min *= 1000
            bw_max *= 1000
        elif bw_units == self.reservation.MBPS:
            bw_min *= 1000000
            bw_max *= 1000000
        elif bw_units == self.reservation.GBPS:
            bw_min *= 1000000000
            bw_max *= 1000000000
        elif bw_units == self.reservation.TBPS:
            bw_min *= 1000000000000
            bw_max *= 1000000000000

        self._bandwidth = {
            'min': bw_min,
            'max': bw_max,
            #'tolerance': bw_tolerance,
        }

        return self._bandwidth

    @property
    def iops(self):
        '''
        Returns an iops dictionary (min and max).
        '''

        if self._iops is not None:
            return self._iops

        iops_map = self.reservation.properties.get(self.reservation.IOPS)
        iops_min = iops_map.get(self.reservation.MIN)
        iops_max = iops_map.get(self.reservation.MAX)
        #iops_tolerance = iops_map.get(self.reservation.TOLERANCE)

        self._iops = {
            'min': iops_min,
            'max': iops_max,
            #'tolerance': iops_tolerance,
        }

        return self._iops

    @property
    def latency(self):
        '''
        Returns a latency dictionary in ms (min and max).
        '''

        if self._latency is not None:
            return self._latency

        latency_map = self.reservation.properties.get(self.reservation.LATENCY)
        latency_min = latency_map.get(self.reservation.MIN)
        latency_max = latency_map.get(self.reservation.MAX)
        #latency_tolerance = latency_map.get(self.reservation.TOLERANCE)

        self._latency = {
            'min': latency_min,
            'max': latency_max,
            #'tolerance': latency_tolerance,
        }

        return self._latency

    @property
    def cfg_uri(self):
        '''
        Plugins must override this with an API endpoint URI.
        '''
        raise exception.Error(_('Reservation plugins must provide an API endpoint.'))

    @property
    def service_name(self):
        '''
        Plugins must override this with a human readable service name.
        '''
        raise exception.Error(_('Reservation plugins must provide a service name.'))

    @property
    def expects_encoded_payload(self):
        '''
        Plugins may override this if they wish for the payload to not
        be encoded on its way to the API endpoint. Defaults to True.
        '''
        return True

    def call_api(self, payload=None, method='POST',
                 content_type='application/x-www-form-urlencoded'):
        '''Call the plugin service API, POSTing the specified payload'''

        # TODO: Will there ever be the potential for different endpoints
        # depending upon the phase and the request?
        # TODO: Support other REST calls as needed (e.g., GET, PUT, DELETE).
        uri = self._api_endpoint

        # Coerce the payload into a string if needed
        if type(payload) is dict:
            payload_string = simplejson.dumps(payload)
        else:
            payload_string = payload

        LOG.info(_('Posting %(service)s request: %(uri)s\n'
                   'Payload: %(payload)s' % {
            'service': self.service_name,
            'uri': uri,
            'payload': payload_string,
        }))

        try:
            request = urllib2.Request(uri, data=payload_string,
                                     headers={'Content-type': content_type})
            request.get_method = lambda: method
            response = urllib2.urlopen(request)
            output_string = response.read()

            # Turn the output into a dict if possible
            output = ''
            try:
                output = simplejson.loads(output_string)
            except simplejson.JSONDecodeError as exc:
                output = output_string

            # Set the request/response for this plugin in the backing store.
            self.db_set({
                'uri': uri,
                'request': payload,
                'status': response.code,
                'response': output,
            })

            LOG.info(_('%(name)s HTTP Status: %(status)d' % {
                'name': self.service_name,
                'status': response.code,
            }))

            # Normally a debug level log
            LOG.info(_('%(name)s Response: %(response)s' % {
                'name': self.service_name,
                'response': output_string,
            }))

            response.close()
        except urllib2.URLError as exc:
            message = None
            if hasattr(exc, 'reason'):
                message = _("Failed to reach %(uri)s. Reason: %(reason)s") % {
                    'uri': uri,
                    'reason': exc.reason,
                }
            elif hasattr(exc, 'code'):
                message = _("Request %(uri)s failed. Reason: %(code)s") % {
                    'uri': uri,
                    'code': exc.code,
                }
            if message:
                LOG.warning(_('%(service)s Failure: %(msg)s. Continuing.\n' % {
                    'service': self.service_name,
                    'msg': message,
                }))
            return None

        return output

    def find_resource(self, resource_id, resource_type=None):
        '''
        Return the resource object with the specified instance ID, or None
        if it cannot be found.
        '''

        for res in self.reservation.stack.itervalues():
            if res.resource_id == resource_id:
                if not(resource_type) or res.type() == resource_type:
                    return res
        return None

    # TODO: Parameters and response TBD.
    def register(self):
        '''
        Plugins may override this with a registration method.
        Not an abstract base class since register is not _required_.
        '''
        pass
