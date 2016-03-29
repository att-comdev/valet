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

import valet.agent.manager
import valet.alarm.notifier.rest
import valet.alarm.rpc
import valet.alarm.service
import valet.api
import valet.api.app
import valet.api.controllers.v2.alarms
import valet.cmd.eventlet.polling
import valet.collector
import valet.compute.discovery
import valet.compute.notifications
import valet.compute.util
import valet.compute.virt.inspector
import valet.compute.virt.libvirt.inspector
import valet.compute.virt.vmware.inspector
import valet.compute.virt.xenapi.inspector
import valet.coordination
import valet.dispatcher
import valet.dispatcher.file
import valet.energy.kwapi
import valet.event.converter
import valet.hardware.discovery
import valet.image.glance
import valet.ipmi.notifications.ironic
import valet.ipmi.platform.intel_node_manager
import valet.ipmi.pollsters
import valet.meter.notifications
import valet.middleware
import valet.network.notifications
import valet.neutron_client
import valet.notification
import valet.nova_client
import valet.objectstore.rgw
import valet.objectstore.swift
import valet.pipeline
import valet.publisher.messaging
import valet.publisher.utils
import valet.sample
import valet.service
import valet.storage
import valet.utils


def list_opts():
    return [
        ('DEFAULT',
         itertools.chain(valet.agent.manager.OPTS,
                         valet.api.app.OPTS,
                         valet.cmd.eventlet.polling.CLI_OPTS,
                         valet.compute.notifications.OPTS,
                         valet.compute.util.OPTS,
                         valet.compute.virt.inspector.OPTS,
                         valet.compute.virt.libvirt.inspector.OPTS,
                         valet.dispatcher.OPTS,
                         valet.image.glance.OPTS,
                         valet.ipmi.notifications.ironic.OPTS,
                         valet.middleware.OPTS,
                         valet.network.notifications.OPTS,
                         valet.nova_client.OPTS,
                         valet.objectstore.swift.OPTS,
                         valet.pipeline.OPTS,
                         valet.sample.OPTS,
                         valet.service.OPTS,
                         valet.storage.OLD_OPTS,
                         valet.utils.OPTS,)),
        ('alarm',
         itertools.chain(valet.alarm.notifier.rest.OPTS,
                         valet.alarm.service.OPTS,
                         valet.alarm.rpc.OPTS,
                         valet.alarm.evaluator.gnocchi.OPTS,
                         valet.api.controllers.v2.alarms.ALARM_API_OPTS)),
        ('api',
         itertools.chain(valet.api.OPTS,
                         valet.api.app.API_OPTS,
                         [valet.service.API_OPT])),
        # deprecated path, new one is 'polling'
        ('central', valet.agent.manager.OPTS),
        ('collector',
         itertools.chain(valet.collector.OPTS,
                         [valet.service.COLL_OPT])),
        ('compute', valet.compute.discovery.OPTS),
        ('coordination', valet.coordination.OPTS),
        ('database', valet.storage.OPTS),
        ('dispatcher_file', valet.dispatcher.file.OPTS),
        ('event', valet.event.converter.OPTS),
        ('exchange_control', valet.exchange_control.EXCHANGE_OPTS),
        ('hardware', valet.hardware.discovery.OPTS),
        ('ipmi',
         itertools.chain(valet.ipmi.platform.intel_node_manager.OPTS,
                         valet.ipmi.pollsters.OPTS)),
        ('meter', valet.meter.notifications.OPTS),
        ('notification',
         itertools.chain(valet.notification.OPTS,
                         [valet.service.NOTI_OPT])),
        ('polling', valet.agent.manager.OPTS),
        ('publisher', valet.publisher.utils.OPTS),
        ('publisher_notifier', valet.publisher.messaging.NOTIFIER_OPTS),
        ('publisher_rpc', valet.publisher.messaging.RPC_OPTS),
        ('rgw_admin_credentials', valet.objectstore.rgw.CREDENTIAL_OPTS),
        ('service_credentials', valet.service.CLI_OPTS),
        ('service_types',
         itertools.chain(valet.energy.kwapi.SERVICE_OPTS,
                         valet.image.glance.SERVICE_OPTS,
                         valet.neutron_client.SERVICE_OPTS,
                         valet.nova_client.SERVICE_OPTS,
                         valet.objectstore.rgw.SERVICE_OPTS,
                         valet.objectstore.swift.SERVICE_OPTS,)),
        ('vmware', valet.compute.virt.vmware.inspector.OPTS),
        ('xenapi', valet.compute.virt.xenapi.inspector.OPTS),
    ]
