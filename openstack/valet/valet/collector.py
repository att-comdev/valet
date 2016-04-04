#
# Copyright 2012-2013 eNovance <licensing@enovance.com>
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

import socket

import msgpack
from oslo_config import cfg
from oslo_log import log
import oslo_messaging
from oslo_service import service as os_service
from oslo_utils import netutils
from oslo_utils import units

from valet import dispatcher
from valet import messaging
from valet.i18n import _, _LE
from valet import utils

OPTS = [
    cfg.StrOpt('udp_address',
               default='0.0.0.0',
               help='Address to which the UDP socket is bound. Set to '
               'an empty string to disable.'),
    cfg.IntOpt('udp_port',
               default=4952,
               min=1, max=65535,
               help='Port to which the UDP socket is bound.'),
    cfg.BoolOpt('requeue_sample_on_dispatcher_error',
                default=False,
                help='Requeue the sample on the collector sample queue '
                'when the collector fails to dispatch it. This is only valid '
                'if the sample come from the notifier publisher.'),
    cfg.BoolOpt('requeue_event_on_dispatcher_error',
                default=False,
                help='Requeue the event on the collector event queue '
                'when the collector fails to dispatch it.'),
    cfg.BoolOpt('enable_rpc',
                default=False,
                help='Enable the RPC functionality of collector. This '
                'functionality is now deprecated in favour of notifier '
                'publisher and queues.')
]

cfg.CONF.register_opts(OPTS, group="collector")
cfg.CONF.import_opt('metering_topic', 'valet.publisher.messaging',
                    group='publisher_rpc')
cfg.CONF.import_opt('metering_topic', 'valet.publisher.messaging',
                    group='publisher_notifier')
cfg.CONF.import_opt('event_topic', 'valet.publisher.messaging',
                    group='publisher_notifier')
cfg.CONF.import_opt('store_events', 'valet.notification',
                    group='notification')


LOG = log.getLogger(__name__)


class CollectorService(os_service.Service):
    """Listener for the collector service."""
    def start(self):
        """Bind the UDP socket and handle incoming data."""
        # ensure dispatcher is configured before starting other services
        self.dispatcher_manager = dispatcher.load_dispatcher_manager()
        self.rpc_server = None
        self.sample_listener = None
        self.event_listener = None
        super(CollectorService, self).start()

        if cfg.CONF.collector.udp_address:
            self.tg.add_thread(self.start_udp)

        transport = messaging.get_transport(optional=True)
        if transport:
            if cfg.CONF.collector.enable_rpc:
                LOG.warning('RPC collector is deprecated in favour of queues. '
                            'Please switch to notifier publisher.')
                self.rpc_server = messaging.get_rpc_server(
                    transport, cfg.CONF.publisher_rpc.metering_topic, self)

            sample_target = oslo_messaging.Target(
                topic=cfg.CONF.publisher_notifier.metering_topic)
            self.sample_listener = messaging.get_notification_listener(
                transport, [sample_target],
                [SampleEndpoint(self.dispatcher_manager)],
                allow_requeue=(cfg.CONF.collector.
                               requeue_sample_on_dispatcher_error))

            if cfg.CONF.notification.store_events:
                event_target = oslo_messaging.Target(
                    topic=cfg.CONF.publisher_notifier.event_topic)
                self.event_listener = messaging.get_notification_listener(
                    transport, [event_target],
                    [EventEndpoint(self.dispatcher_manager)],
                    allow_requeue=(cfg.CONF.collector.
                                   requeue_event_on_dispatcher_error))
                self.event_listener.start()

            if cfg.CONF.collector.enable_rpc:
                self.rpc_server.start()
            self.sample_listener.start()

            if not cfg.CONF.collector.udp_address:
                # Add a dummy thread to have wait() working
                self.tg.add_timer(604800, lambda: None)

    def start_udp(self):
        address_family = socket.AF_INET
        if netutils.is_valid_ipv6(cfg.CONF.collector.udp_address):
            address_family = socket.AF_INET6
        udp = socket.socket(address_family, socket.SOCK_DGRAM)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp.bind((cfg.CONF.collector.udp_address,
                  cfg.CONF.collector.udp_port))

        self.udp_run = True
        while self.udp_run:
            # NOTE(jd) Arbitrary limit of 64K because that ought to be
            # enough for anybody.
            data, source = udp.recvfrom(64 * units.Ki)
            try:
                sample = msgpack.loads(data, encoding='utf-8')
            except Exception:
                LOG.warn(_("UDP: Cannot decode data sent by %s"), source)
            else:
                try:
                    LOG.debug("UDP: Storing %s", sample)
                    self.dispatcher_manager.map_method('record_metering_data',
                                                       sample)
                except Exception:
                    LOG.exception(_("UDP: Unable to store meter"))

    def stop(self):
        self.udp_run = False
        if cfg.CONF.collector.enable_rpc and self.rpc_server:
            self.rpc_server.stop()
        if self.sample_listener:
            utils.kill_listeners([self.sample_listener])
        if self.event_listener:
            utils.kill_listeners([self.event_listener])
        super(CollectorService, self).stop()

    def record_metering_data(self, context, data):
        """RPC endpoint for messages we send to ourselves.

        When the notification messages are re-published through the
        RPC publisher, this method receives them for processing.
        """
        self.dispatcher_manager.map_method('record_metering_data', data=data)


class CollectorEndpoint(object):
    def __init__(self, dispatcher_manager, requeue_on_error):
        self.dispatcher_manager = dispatcher_manager
        self.requeue_on_error = requeue_on_error

    def sample(self, ctxt, publisher_id, event_type, payload, metadata):
        """RPC endpoint for notification messages

        When another service sends a notification over the message
        bus, this method receives it.
        """
        try:
            self.dispatcher_manager.map_method(self.method, payload)
        except Exception:
            if self.requeue_on_error:
                LOG.exception(_LE("Dispatcher failed to handle the %s, "
                                  "requeue it."), self.ep_type)
                return oslo_messaging.NotificationResult.REQUEUE
            raise


class SampleEndpoint(CollectorEndpoint):
    method = 'record_metering_data'
    ep_type = 'sample'

    def __init__(self, dispatcher_manager):
        super(SampleEndpoint, self).__init__(
            dispatcher_manager,
            cfg.CONF.collector.requeue_sample_on_dispatcher_error)


class EventEndpoint(CollectorEndpoint):
    method = 'record_events'
    ep_type = 'event'

    def __init__(self, dispatcher_manager):
        super(EventEndpoint, self).__init__(
            dispatcher_manager,
            cfg.CONF.collector.requeue_event_on_dispatcher_error)