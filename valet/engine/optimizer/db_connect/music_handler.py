#!/bin/python


import json
import operator
from valet.common.music import Music
from valet.engine.optimizer.db_connect.event import Event


def ensurekey(d, k):
    return d.setdefault(k, {})


# FIXME(GJ): make MUSIC as pluggable
class MusicHandler(object):

    def __init__(self, _config, _logger):
        self.config = _config
        self.logger = _logger

        self.music = Music(hosts=self.config.db_hosts, replication_factor=self.config.replication_factor)
        if self.config.db_hosts is not None and len(self.config.db_hosts) > 0:
            for dbh in self.config.db_hosts:
                self.logger.info("DB: music host = " + dbh)
        if self.config.replication_factor is not None:
            self.logger.info("DB: music replication factor = " + str(self.config.replication_factor))

    # FIXME(GJ): this may not need
    def init_db(self):
        try:
            self.music.create_keyspace(self.config.db_keyspace)
        except Exception as e:
            self.logger.error("DB: " + str(e))
            return False

        schema = {
            'stack_id': 'text',
            'request': 'text',
            'PRIMARY KEY': '(stack_id)'
        }
        try:
            self.music.create_table(self.config.db_keyspace, self.config.db_request_table, schema)
        except Exception as e:
            self.logger.error("DB: " + str(e))
            return False

        schema = {
            'stack_id': 'text',
            'placement': 'text',
            'PRIMARY KEY': '(stack_id)'
        }
        try:
            self.music.create_table(self.config.db_keyspace, self.config.db_response_table, schema)
        except Exception as e:
            self.logger.error("DB: " + str(e))
            return False

        schema = {
            'timestamp': 'text',
            'exchange': 'text',
            'method': 'text',
            'args': 'text',
            'PRIMARY KEY': '(timestamp)'
        }
        try:
            self.music.create_table(self.config.db_keyspace, self.config.db_event_table, schema)
        except Exception as e:
            self.logger.error("DB: " + str(e))
            return False

        schema = {
            'site_name': 'text',
            'resource': 'text',
            'PRIMARY KEY': '(site_name)'
        }
        try:
            self.music.create_table(self.config.db_keyspace, self.config.db_resource_table, schema)
        except Exception as e:
            self.logger.error("DB: " + str(e))
            return False

        schema = {
            'stack_id': 'text',
            'app': 'text',
            'PRIMARY KEY': '(stack_id)'
        }
        try:
            self.music.create_table(self.config.db_keyspace, self.config.db_app_table, schema)
        except Exception as e:
            self.logger.error("DB: " + str(e))
            return False

        schema = {
            'uuid': 'text',
            'h_uuid': 'text',
            's_uuid': 'text',
            'PRIMARY KEY': '(uuid)'
        }
        try:
            self.music.create_table(self.config.db_keyspace, self.config.db_uuid_table, schema)
        except Exception as e:
            self.logger.error("DB: " + str(e))
            return False

        return True

    # TODO(GJ): evaluate the delay
    def get_events(self):
        event_list = []

        events = {}
        try:
            events = self.music.read_all_rows(self.config.db_keyspace, self.config.db_event_table)
        except Exception as e:
            self.logger.error("DB:event: " + str(e))
            # FIXME(GJ): return None?
            return {}

        if len(events) > 0:
            for _, row in events.iteritems():
                event_id = row['timestamp']
                exchange = row['exchange']
                method = row['method']
                args_data = row['args']

                if exchange != "nova":
                    if self.delete_event(event_id) is False:
                        return None
                    self.logger.warn("DB: event exchange (" + exchange + ") is not supported")
                    continue

                if method != 'object_action' and method != 'build_and_run_instance':
                    if self.delete_event(event_id) is False:
                        return None
                    self.logger.warn("DB: event method (" + method + ") is not considered")
                    continue

                if len(args_data) == 0:
                    if self.delete_event(event_id) is False:
                        return None
                    self.logger.warn("DB: event does not have args")
                    continue

                try:
                    args = json.loads(args_data)
                except (ValueError, KeyError, TypeError):
                    self.logger.warn("DB: while decoding to JSON event = " + method + ":" + event_id)
                    continue

                if method == 'object_action':
                    if 'objinst' in args.keys():
                        objinst = args['objinst']
                        if 'nova_object.name' in objinst.keys():
                            nova_object_name = objinst['nova_object.name']
                            if nova_object_name == 'Instance':
                                if 'nova_object.changes' in objinst.keys() and \
                                   'nova_object.data' in objinst.keys():
                                    change_list = objinst['nova_object.changes']
                                    change_data = objinst['nova_object.data']
                                    if 'vm_state' in change_list and \
                                       'vm_state' in change_data.keys():
                                        if change_data['vm_state'] == 'deleted' or \
                                           change_data['vm_state'] == 'active':
                                            e = Event(event_id)
                                            e.exchange = exchange
                                            e.method = method
                                            e.args = args
                                            event_list.append(e)
                                        else:
                                            self.logger.warn("unknown vm_state = " + change_data["vm_state"])
                                            if 'uuid' in change_data.keys():
                                                self.logger.warn("    uuid = " + change_data['uuid'])
                                            if self.delete_event(event_id) is False:
                                                return None
                                    else:
                                        if self.delete_event(event_id) is False:
                                            return None
                                else:
                                    if self.delete_event(event_id) is False:
                                        return None
                            elif nova_object_name == 'ComputeNode':
                                if 'nova_object.changes' in objinst.keys() and \
                                   'nova_object.data' in objinst.keys():
                                    e = Event(event_id)
                                    e.exchange = exchange
                                    e.method = method
                                    e.args = args
                                    event_list.append(e)
                                else:
                                    if self.delete_event(event_id) is False:
                                        return None
                            else:
                                if self.delete_event(event_id) is False:
                                    return None
                        else:
                            if self.delete_event(event_id) is False:
                                return None
                    else:
                        if self.delete_event(event_id) is False:
                            return None

                elif method == 'build_and_run_instance':
                    if 'filter_properties' not in args.keys():
                        if self.delete_event(event_id) is False:
                            return None
                        continue
                    # NOTE(GJ): do not check the existance of scheduler_hints

                    if 'instance' not in args.keys():
                        if self.delete_event(event_id) is False:
                            return None
                        continue
                    else:
                        instance = args['instance']
                        if 'nova_object.data' not in instance.keys():
                            if self.delete_event(event_id) is False:
                                return None
                            continue

                    e = Event(event_id)
                    e.exchange = exchange
                    e.method = method
                    e.args = args
                    event_list.append(e)

        error_event_list = []
        for e in event_list:
            e.set_data()

            if e.method == "object_action":
                if e.object_name == 'Instance':
                    if e.uuid is None or e.uuid == "none" or \
                       e.host is None or e.host == "none" or \
                       e.vcpus == -1 or e.mem == -1:
                        error_event_list.append(e)
                        self.logger.warn("DB: data missing in instance object event")

                elif e.object_name == 'ComputeNode':
                    if e.host is None or e.host == "none":
                        error_event_list.append(e)
                        self.logger.warn("DB: data missing in compute object event")

            elif e.method == "build_and_run_instance":
                if e.uuid is None or e.uuid == "none":
                    error_event_list.append(e)
                    self.logger.warn("DB: data missing in build event")

        if len(error_event_list) > 0:
            event_list[:] = [e for e in event_list if e not in error_event_list]

        if len(event_list) > 0:
            event_list.sort(key=operator.attrgetter('event_id'))

        return event_list

    def delete_event(self, _event_id):
        try:
            self.music.delete_row_eventually(self.config.db_keyspace,
                                             self.config.db_event_table,
                                             'timestamp', _event_id)
        except Exception as e:
            self.logger.error("DB: while deleting event: " + str(e))
            return False

        return True

    def get_uuid(self, _uuid):
        h_uuid = "none"
        s_uuid = "none"

        row = {}
        try:
            row = self.music.read_row(self.config.db_keyspace, self.config.db_uuid_table, 'uuid', _uuid)
        except Exception as e:
            self.logger.error("DB: while reading uuid: " + str(e))
            return None

        if len(row) > 0:
            h_uuid = row[row.keys()[0]]['h_uuid']
            s_uuid = row[row.keys()[0]]['s_uuid']

        return h_uuid, s_uuid

    def put_uuid(self, _e):
        heat_resource_uuid = "none"
        heat_root_stack_id = "none"
        if _e.heat_resource_uuid is not None and _e.heat_resource_uuid != "none":
            heat_resource_uuid = _e.heat_resource_uuid
        else:
            heat_resource_uuid = _e.uuid
        if _e.heat_root_stack_id is not None and _e.heat_root_stack_id != "none":
            heat_root_stack_id = _e.heat_root_stack_id
        else:
            heat_root_stack_id = _e.uuid

        data = {
            'uuid': _e.uuid,
            'h_uuid': heat_resource_uuid,
            's_uuid': heat_root_stack_id
        }

        try:
            self.music.create_row(self.config.db_keyspace, self.config.db_uuid_table, data)
        except Exception as e:
            self.logger.error("DB: while inserting uuid: " + str(e))
            return False

        return True

    def delete_uuid(self, _k):
        try:
            self.music.delete_row_eventually(self.config.db_keyspace, self.config.db_uuid_table, 'uuid', _k)
        except Exception as e:
            self.logger.error("DB: while deleting uuid: " + str(e))
            return False

        return True

    def get_requests(self):
        request_list = []

        requests = {}
        try:
            requests = self.music.read_all_rows(self.config.db_keyspace, self.config.db_request_table)
        except Exception as e:
            self.logger.error("DB: while reading requests: " + str(e))
            # FIXME(GJ): return None?
            return {}

        if len(requests) > 0:
            self.logger.info("DB: placement request arrived")

            for _, row in requests.iteritems():
                self.logger.info("    request_id = " + row['stack_id'])

                r_list = json.loads(row['request'])
                for r in r_list:
                    request_list.append(r)

        return request_list

    def put_result(self, _result):
        for appk, app_placement in _result.iteritems():
            data = {
                'stack_id': appk,
                'placement': json.dumps(app_placement)
            }

            try:
                self.music.create_row(self.config.db_keyspace, self.config.db_response_table, data)
            except Exception as e:
                self.logger.error("DB: while putting placement result: " + str(e))
                return False

        for appk in _result.keys():
            try:
                self.music.delete_row_eventually(self.config.db_keyspace,
                                                 self.config.db_request_table,
                                                 'stack_id', appk)
            except Exception as e:
                self.logger.error("DB: while deleting handled request: " + str(e))
                return False

        return True

    def get_resource_status(self, _k):
        json_resource = {}

        row = {}
        try:
            row = self.music.read_row(self.config.db_keyspace, self.config.db_resource_table, 'site_name', _k, self.logger)
        except Exception as e:
            self.logger.error("DB: while reading resource status: " + str(e))
            return None

        if len(row) > 0:
            str_resource = row[row.keys()[0]]['resource']
            json_resource = json.loads(str_resource)

        return json_resource

    def update_resource_status(self, _k, _status):
        row = {}
        try:
            row = self.music.read_row(self.config.db_keyspace, self.config.db_resource_table, 'site_name', _k)
        except Exception as e:
            self.logger.error("DB: while reading resource status: " + str(e))
            return False

        json_resource = {}
        if len(row) > 0:
            str_resource = row[row.keys()[0]]['resource']
            json_resource = json.loads(str_resource)

            if 'flavors' in _status.keys():
                flavors = _status['flavors']
                for fk, f in flavors.iteritems():
                    if fk in ensurekey(json_resource, 'flavors').keys():
                        del json_resource['flavors'][fk]
                    json_resource['flavors'][fk] = f

            if 'logical_groups' in _status.keys():
                logical_groups = _status['logical_groups']
                for lgk, lg in logical_groups.iteritems():
                    if lgk in ensurekey(json_resource, 'logical_groups').keys():
                        del json_resource['logical_groups'][lgk]
                    json_resource['logical_groups'][lgk] = lg

            if 'hosts' in _status.keys():
                hosts = _status['hosts']
                for hk, h in hosts.iteritems():
                    if hk in ensurekey(json_resource, 'hosts').keys():
                        del json_resource['hosts'][hk]
                    json_resource['hosts'][hk] = h

            if 'host_groups' in _status.keys():
                host_groupss = _status['host_groups']
                for hgk, hg in host_groupss.iteritems():
                    if hgk in ensurekey(json_resource, 'host_groups').keys():
                        del json_resource['host_groups'][hgk]
                    json_resource['host_groups'][hgk] = hg

            if 'datacenter' in _status.keys():
                datacenter = _status['datacenter']
                del json_resource['datacenter']
                json_resource['datacenter'] = datacenter

            json_resource['timestamp'] = _status['timestamp']

            try:
                self.music.delete_row_eventually(self.config.db_keyspace,
                                                 self.config.db_resource_table,
                                                 'site_name', _k)
            except Exception as e:
                self.logger.error("DB: while deleting resource status: " + str(e))
                return False

        else:
            json_resource = _status

        data = {
            'site_name': _k,
            'resource': json.dumps(json_resource)
        }

        try:
            self.music.create_row(self.config.db_keyspace, self.config.db_resource_table, data)
        except Exception as e:
            self.logger.error("DB: " + str(e))
            return False

        self.logger.info("DB: resource status updated")

        return True

    def add_app(self, _k, _app_data):
        try:
            self.music.delete_row_eventually(self.config.db_keyspace, self.config.db_app_table, 'stack_id', _k)
        except Exception as e:
            self.logger.error("DB: while deleting app: " + str(e))
            return False

        if _app_data is not None:
            data = {
                'stack_id': _k,
                'app': json.dumps(_app_data)
            }

            try:
                self.music.create_row(self.config.db_keyspace, self.config.db_app_table, data)
            except Exception as e:
                self.logger.error("DB: while inserting app: " + str(e))
                return False

        return True

    def get_app_info(self, _s_uuid):
        json_app = {}

        row = {}
        try:
            row = self.music.read_row(self.config.db_keyspace, self.config.db_app_table, 'stack_id', _s_uuid)
        except Exception as e:
            self.logger.error("DB: while reading app info: " + str(e))
            return None

        if len(row) > 0:
            str_app = row[row.keys()[0]]['app']
            json_app = json.loads(str_app)

        return json_app

    # TODO(GY): get all other VMs related to this VM
    def get_vm_info(self, _s_uuid, _h_uuid, _host):
        updated = False
        json_app = {}

        vm_info = {}

        row = {}
        try:
            row = self.music.read_row(self.config.db_keyspace, self.config.db_app_table, 'stack_id', _s_uuid)
        except Exception as e:
            self.logger.error("DB: " + str(e))
            return None

        if len(row) > 0:
            str_app = row[row.keys()[0]]['app']
            json_app = json.loads(str_app)

            vms = json_app["VMs"]
            for vmk, vm in vms.iteritems():
                if vmk == _h_uuid:
                    if vm["status"] != "deleted":
                        if vm["host"] != _host:
                            vm["planned_host"] = vm["host"]
                            vm["host"] = _host
                            self.logger.warn("DB: conflicted placement decision from Ostro")
                            # TODO(GY): affinity, diversity, exclusivity validation check
                            updated = True
                    else:
                        vm["status"] = "scheduled"
                        self.logger.warn("DB: vm was deleted")
                        updated = True

                    vm_info = vm
                    break
            else:
                self.logger.error("DB: vm is missing from stack")

        else:
            self.logger.warn("DB: not found stack for update = " + _s_uuid)

        if updated is True:
            if self.add_app(_s_uuid, json_app) is False:
                return None

        return vm_info

    def update_vm_info(self, _s_uuid, _h_uuid):
        updated = False
        json_app = {}

        row = {}
        try:
            row = self.music.read_row(self.config.db_keyspace, self.config.db_app_table, 'stack_id', _s_uuid)
        except Exception as e:
            self.logger.error("DB: " + str(e))
            return False

        if len(row) > 0:
            str_app = row[row.keys()[0]]['app']
            json_app = json.loads(str_app)

            vms = json_app["VMs"]
            for vmk, vm in vms.iteritems():
                if vmk == _h_uuid:
                    if vm["status"] != "deleted":
                        vm["status"] = "deleted"
                        self.logger.warn("DB: deleted marked")
                        updated = True
                    else:
                        self.logger.warn("DB: vm was already deleted")

                    break
            else:
                self.logger.error("DB: vm is missing from stack")

        else:
            self.logger.warn("DB: not found stack for update = " + _s_uuid)

        if updated is True:
            if self.add_app(_s_uuid, json_app) is False:
                return False

        return True
