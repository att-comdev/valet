# Copyright 2014 eNovance
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
import itertools

import allegro.agent.manager
import allegro.alarm.notifier.rest
import allegro.alarm.rpc
import allegro.alarm.service
import allegro.api
import allegro.api.app
import allegro.api.controllers.v2.alarms
import allegro.cmd.eventlet.polling
import allegro.collector
import allegro.compute.discovery
import allegro.compute.notifications
import allegro.compute.util
import allegro.compute.virt.inspector
import allegro.compute.virt.libvirt.inspector
import allegro.compute.virt.vmware.inspector
import allegro.compute.virt.xenapi.inspector
import allegro.coordination
import allegro.dispatcher
import allegro.dispatcher.file
import allegro.energy.kwapi
import allegro.event.converter
import allegro.hardware.discovery
import allegro.image.glance
import allegro.ipmi.notifications.ironic
import allegro.ipmi.platform.intel_node_manager
import allegro.ipmi.pollsters
import allegro.meter.notifications
import allegro.middleware
import allegro.network.notifications
import allegro.neutron_client
import allegro.notification
import allegro.nova_client
import allegro.objectstore.rgw
import allegro.objectstore.swift
import allegro.pipeline
import allegro.publisher.messaging
import allegro.publisher.utils
import allegro.sample
import allegro.service
import allegro.storage
import allegro.utils


def list_opts():
    return [
        ('DEFAULT',
         itertools.chain(allegro.agent.manager.OPTS,
                         allegro.api.app.OPTS,
                         allegro.cmd.eventlet.polling.CLI_OPTS,
                         allegro.compute.notifications.OPTS,
                         allegro.compute.util.OPTS,
                         allegro.compute.virt.inspector.OPTS,
                         allegro.compute.virt.libvirt.inspector.OPTS,
                         allegro.dispatcher.OPTS,
                         allegro.image.glance.OPTS,
                         allegro.ipmi.notifications.ironic.OPTS,
                         allegro.middleware.OPTS,
                         allegro.network.notifications.OPTS,
                         allegro.nova_client.OPTS,
                         allegro.objectstore.swift.OPTS,
                         allegro.pipeline.OPTS,
                         allegro.sample.OPTS,
                         allegro.service.OPTS,
                         allegro.storage.OLD_OPTS,
                         allegro.utils.OPTS,)),
        ('alarm',
         itertools.chain(allegro.alarm.notifier.rest.OPTS,
                         allegro.alarm.service.OPTS,
                         allegro.alarm.rpc.OPTS,
                         allegro.alarm.evaluator.gnocchi.OPTS,
                         allegro.api.controllers.v2.alarms.ALARM_API_OPTS)),
        ('api',
         itertools.chain(allegro.api.OPTS,
                         allegro.api.app.API_OPTS,
                         [allegro.service.API_OPT])),
        # deprecated path, new one is 'polling'
        ('central', allegro.agent.manager.OPTS),
        ('collector',
         itertools.chain(allegro.collector.OPTS,
                         [allegro.service.COLL_OPT])),
        ('compute', allegro.compute.discovery.OPTS),
        ('coordination', allegro.coordination.OPTS),
        ('database', allegro.storage.OPTS),
        ('dispatcher_file', allegro.dispatcher.file.OPTS),
        ('event', allegro.event.converter.OPTS),
        ('exchange_control', allegro.exchange_control.EXCHANGE_OPTS),
        ('hardware', allegro.hardware.discovery.OPTS),
        ('ipmi',
         itertools.chain(allegro.ipmi.platform.intel_node_manager.OPTS,
                         allegro.ipmi.pollsters.OPTS)),
        ('meter', allegro.meter.notifications.OPTS),
        ('notification',
         itertools.chain(allegro.notification.OPTS,
                         [allegro.service.NOTI_OPT])),
        ('polling', allegro.agent.manager.OPTS),
        ('publisher', allegro.publisher.utils.OPTS),
        ('publisher_notifier', allegro.publisher.messaging.NOTIFIER_OPTS),
        ('publisher_rpc', allegro.publisher.messaging.RPC_OPTS),
        ('rgw_admin_credentials', allegro.objectstore.rgw.CREDENTIAL_OPTS),
        ('service_credentials', allegro.service.CLI_OPTS),
        ('service_types',
         itertools.chain(allegro.energy.kwapi.SERVICE_OPTS,
                         allegro.image.glance.SERVICE_OPTS,
                         allegro.neutron_client.SERVICE_OPTS,
                         allegro.nova_client.SERVICE_OPTS,
                         allegro.objectstore.rgw.SERVICE_OPTS,
                         allegro.objectstore.swift.SERVICE_OPTS,)),
        ('vmware', allegro.compute.virt.vmware.inspector.OPTS),
        ('xenapi', allegro.compute.virt.xenapi.inspector.OPTS),
    ]
