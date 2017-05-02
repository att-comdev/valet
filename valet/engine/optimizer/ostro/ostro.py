#!/bin/python

# Modified: Jan. 30, 2017


from oslo_config import cfg
import threading
import time
import traceback
from valet.engine.listener.listener_manager import ListenerManager
from valet.engine.optimizer.app_manager.app_handler import AppHandler
from valet.engine.optimizer.app_manager.app_topology_base import VM, Volume
from valet.engine.optimizer.db_connect.music_handler import MusicHandler
from valet.engine.optimizer.ostro.optimizer import Optimizer
from valet.engine.resource_manager.compute_manager import ComputeManager
from valet.engine.resource_manager.resource import Resource
from valet.engine.resource_manager.topology_manager import TopologyManager

CONF = cfg.CONF


class Ostro(object):

    def __init__(self, _config, _logger):
        self.config = _config
        self.logger = _logger

        self.db = MusicHandler(self.config, self.logger)
        if self.db.init_db() is False:
            self.logger.error("error while initializing MUSIC database")
        else:
            self.logger.debug("done init music")

        self.resource = Resource(self.db, self.config, self.logger)
        self.logger.debug("done init resource")

        self.app_handler = AppHandler(self.resource, self.db, self.config, self.logger)
        self.logger.debug("done init apphandler")

        self.optimizer = Optimizer(self.resource, self.logger)
        self.logger.debug("done init optimizer")

        self.data_lock = threading.Lock()
        self.thread_list = []

        self.topology = TopologyManager(1, "Topology", self.resource, self.data_lock, self.config, self.logger)
        self.logger.debug("done init topology")

        self.compute = ComputeManager(2, "Compute", self.resource, self.data_lock, self.config, self.logger)
        self.logger.debug("done init compute")

        self.listener = ListenerManager(3, "Listener", CONF)
        self.logger.debug("done init listener")

        self.status = "success"
        self.end_of_process = False

        self.batch_store_trigger = 10  # sec
        self.batch_events_count = 1

    '''
    def run_ostro(self):
        self.logger.info("start Ostro ......")

        self.topology.start()
        self.compute.start()
        self.listener.start()

        self.thread_list.append(self.topology)
        self.thread_list.append(self.compute)
        self.thread_list.append(self.listener)

        while self.end_of_process is False:
            request_list = self.db.get_requests()
            if request_list is None:
                break

            if len(request_list) > 0:
                if self.place_app(request_list) is False:
                    break
            else:
                event_list = self.db.get_events()
                if event_list is None:
                    break

                if len(event_list) > 0:
                    if self.handle_events(event_list) is False:
                        break
                else:
                    if self.resource.resource_updated is True and \
                       (time.time()-self.resource.curr_db_timestamp) >= self.batch_store_trigger:
                        if self.resource.store_topology_updates() is False:
                            break
                        self.resource.resource_updated = False
                    else:
                        time.sleep(0.1)

        self.topology.end_of_process = True
        self.compute.end_of_process = True

        for t in self.thread_list:
            t.join()

        self.logger.info("exit Ostro")
    '''

    def run_ostro(self):
        self.logger.info("start Ostro ......")

        self.topology.start()
        self.compute.start()
        self.listener.start()

        self.thread_list.append(self.topology)
        self.thread_list.append(self.compute)
        self.thread_list.append(self.listener)

        while self.end_of_process is False:
            time.sleep(0.1)

            request_list = self.db.get_requests()
            if request_list is None:
                break

            if len(request_list) > 0:
                if self.place_app(request_list) is False:
                    break
            else:
                event_list = self.db.get_events()
                if event_list is None:
                    break

                if len(event_list) > 0:
                    if self.handle_events(event_list) is False:
                        break
                else:
                    if self.resource.resource_updated is True and \
                       (time.time() - self.resource.curr_db_timestamp) >= self.batch_store_trigger:
                        if self.resource.store_topology_updates() is False:
                            break
                        self.resource.resource_updated = False

        self.topology.end_of_process = True
        self.compute.end_of_process = True

        for t in self.thread_list:
            t.join()

        self.logger.info("exit Ostro")

    def stop_ostro(self):
        self.end_of_process = True

        while len(self.thread_list) > 0:
            time.sleep(1)
            for t in self.thread_list:
                if not t.is_alive():
                    self.thread_list.remove(t)

    def bootstrap(self):
        self.logger.info("start bootstrap")

        try:
            resource_status = self.db.get_resource_status(self.resource.datacenter.name)
            if resource_status is None:
                self.logger.error("failed to read from table: " + self.config.db_resource_table)
                return False

            if len(resource_status) > 0:
                self.logger.info("bootstrap from DB")
                if not self.resource.bootstrap_from_db(resource_status):
                    self.logger.error("failed to parse bootstrap data!")

            self.logger.info("bootstrap from OpenStack")
            if not self._set_hosts():
                return False

            if not self._set_flavors():
                return False

            if not self._set_topology():
                return False

            self.resource.update_topology()

        except Exception:
            self.logger.critical("bootstrap failed: " + traceback.format_exc())

        self.logger.info("done bootstrap")

        return True

    def _set_topology(self):
        if not self.topology.set_topology():
            # self.status = "datacenter configuration error"
            self.logger.error("failed to read datacenter topology")
            return False

        self.logger.info("done topology bootstrap")
        return True

    def _set_hosts(self):
        if not self.compute.set_hosts():
            # self.status = "OpenStack (Nova) internal error"
            self.logger.error("failed to read hosts from OpenStack (Nova)")
            return False

        self.logger.info("done hosts & groups bootstrap")
        return True

    def _set_flavors(self):
        if not self.compute.set_flavors():
            # self.status = "OpenStack (Nova) internal error"
            self.logger.error("failed to read flavors from OpenStack (Nova)")
            return False

        self.logger.info("done flavors bootstrap")
        return True

    def place_app(self, _app_data):
        start_time = time.time()

        for req in _app_data:
            if req["action"] == "query":
                self.logger.info("start query")

                query_result = self._query(req)
                result = self._get_json_results("query", "ok", self.status, query_result)

                if self.db.put_result(result) is False:
                    return False

                self.logger.info("done query")
            else:
                self.logger.info("start app placement")

                result = None
                placement_map = self._place_app(req)

                if placement_map is None:
                    result = self._get_json_results("placement", "error", self.status, placement_map)
                else:
                    result = self._get_json_results("placement", "ok", "success", placement_map)

                if self.db.put_result(result) is False:
                    return False

                self.logger.info("done app placement")

        end_time = time.time()
        self.logger.info("EVAL: total decision delay of request = " + str(end_time - start_time) + " sec")

        return True

    def _query(self, _q):
        query_result = {}

        if "type" in _q.keys():
            if _q["type"] == "group_vms":
                if "parameters" in _q.keys():
                    params = _q["parameters"]
                    if "group_name" in params.keys():
                        self.data_lock.acquire()
                        vm_list = self._get_vms_from_logical_group(params["group_name"])
                        self.data_lock.release()
                        query_result[_q["stack_id"]] = vm_list
                    else:
                        self.status = "unknown paramenter in query"
                        self.logger.warn("unknown paramenter in query")
                        query_result[_q["stack_id"]] = None
                else:
                    self.status = "no paramenter in query"
                    self.logger.warn("no parameters in query")
                    query_result[_q["stack_id"]] = None
            elif _q["type"] == "all_groups":
                self.data_lock.acquire()
                query_result[_q["stack_id"]] = self._get_logical_groups()
                self.data_lock.release()
            else:
                self.status = "unknown query type"
                self.logger.warn("unknown query type")
                query_result[_q["stack_id"]] = None
        else:
            self.status = "unknown type in query"
            self.logger.warn("no type in query")
            query_result[_q["stack_id"]] = None

        return query_result

    def _get_vms_from_logical_group(self, _group_name):
        self.logger.debug("query to see vms of " + _group_name)

        vm_list = []

        vm_id_list = []
        for lgk, lg in self.resource.logical_groups.iteritems():
            if lg.group_type == "EX" or lg.group_type == "AFF" or lg.group_type == "DIV":
                lg_id = lgk.split(":")
                if lg_id[1] == _group_name:
                    self.logger.debug("found group in Ostro")
                    vm_id_list = lg.vm_list
                    break

        if len(vm_id_list) == 0:
            self.logger.debug("group does not exist in Ostro")

        for vm_id in vm_id_list:
            if vm_id[2] != "none":   # if physical_uuid != 'none'
                vm_list.append(vm_id[2])
            else:
                self.logger.warn("found pending vms in this group while query")

        return vm_list

    def _get_logical_groups(self):
        logical_groups = {}

        for lgk, lg in self.resource.logical_groups.iteritems():
            logical_groups[lgk] = lg.get_json_info()

        return logical_groups

    def _place_app(self, _app):
        ''' set application topology '''
        app_topology = self.app_handler.add_app(_app)
        if app_topology is None:
            self.status = self.app_handler.status
            self.logger.error("while register requested apps: " + self.app_handler.status)
            return None

        ''' check and set vm flavor information '''
        for _, vm in app_topology.vms.iteritems():
            if self._set_vm_flavor_information(vm) is False:
                self.status = "fail to set flavor information"
                self.logger.error(self.status)
                return None
        for _, vg in app_topology.vgroups.iteritems():
            if self._set_vm_flavor_information(vg) is False:
                self.status = "fail to set flavor information in a group"
                self.logger.error(self.status)
                return None

        self.data_lock.acquire()

        ''' set weights for optimization '''
        app_topology.set_weight()
        app_topology.set_optimization_priority()

        ''' perform search for optimal placement of app topology  '''
        placement_map = self.optimizer.place(app_topology)
        if placement_map is None:
            self.status = self.optimizer.status
            # self.logger.debug("error while optimizing app placement: " + self.status)
            self.data_lock.release()
            return None

        ''' update resource and app information '''
        if len(placement_map) > 0:
            self.resource.update_topology(store=False)

            self.app_handler.add_placement(placement_map, self.resource.current_timestamp)
            if len(app_topology.exclusion_list_map) > 0 and len(app_topology.planned_vm_map) > 0:
                for vk in app_topology.planned_vm_map.keys():
                    if vk in placement_map.keys():
                        del placement_map[vk]

        self.data_lock.release()

        return placement_map

    def _set_vm_flavor_information(self, _v):
        if isinstance(_v, VM):
            return self._set_vm_flavor_properties(_v)
        else:  # affinity group
            for _, sg in _v.subvgroups.iteritems():
                if self._set_vm_flavor_information(sg) is False:
                    return False
            return True

    def _set_vm_flavor_properties(self, _vm):
        flavor = self.resource.get_flavor(_vm.flavor)

        if flavor is None:
            self.logger.warn("does not exist flavor (" + _vm.flavor + ") and try to refetch")

            ''' reset flavor resource and try again '''
            if self._set_flavors() is False:
                return False

            self.resource.update_topology(store=False)

            flavor = self.resource.get_flavor(_vm.flavor)
            if flavor is None:
                return False

        _vm.vCPUs = flavor.vCPUs
        _vm.mem = flavor.mem_cap
        _vm.local_volume_size = flavor.disk_cap

        if len(flavor.extra_specs) > 0:
            extra_specs = {}
            for mk, mv in flavor.extra_specs.iteritems():
                extra_specs[mk] = mv
            _vm.extra_specs_list.append(extra_specs)

        return True

    def handle_events(self, _event_list):
        self.data_lock.acquire()

        resource_updated = False

        events_count = 0
        handled_event_list = []
        for e in _event_list:
            if e.host is not None and e.host != "none":
                if self._check_host(e.host) is False:
                    self.logger.warn("EVENT: host (" + e.host + ") related to this event not exists")
                    continue

            if e.method == "build_and_run_instance":         # VM is created (from stack)
                self.logger.debug("EVENT: got build_and_run for " + e.uuid)
                if self.db.put_uuid(e) is False:
                    self.data_lock.release()
                    return False

            elif e.method == "object_action":
                if e.object_name == 'Instance':              # VM became active or deleted
                    orch_id = self.db.get_uuid(e.uuid)       # h_uuid, stack_id
                    if orch_id is None:
                        self.data_lock.release()
                        return False

                    if e.vm_state == "active":
                        self.logger.debug("EVENT: got instance_active for " + e.uuid)
                        vm_info = self.app_handler.get_vm_info(orch_id[1], orch_id[0], e.host)
                        if vm_info is None:
                            self.logger.error("EVENT: error while getting app info from MUSIC")
                            self.data_lock.release()
                            return False

                        if len(vm_info) == 0:
                            '''
                            stack not found because vm is created by the other stack
                            '''
                            self.logger.warn("EVENT: no vm_info found in app placement record")
                            self._add_vm_to_host(e.uuid, orch_id[0], e.host, e.vcpus, e.mem, e.local_disk)
                        else:
                            if "planned_host" in vm_info.keys() and vm_info["planned_host"] != e.host:
                                '''
                                vm is activated in the different host
                                '''
                                self.logger.warn("EVENT: vm activated in the different host")
                                self._add_vm_to_host(e.uuid, orch_id[0], e.host, e.vcpus, e.mem, e.local_disk)

                                self._remove_vm_from_host(e.uuid, orch_id[0],
                                                          vm_info["planned_host"],
                                                          float(vm_info["cpus"]),
                                                          float(vm_info["mem"]),
                                                          float(vm_info["local_volume"]))

                                self._remove_vm_from_logical_groups(e.uuid, orch_id[0], vm_info["planned_host"])
                            else:
                                '''
                                found vm in the planned host,
                                possibly the vm deleted in the host while batch cleanup
                                '''
                                if self._check_h_uuid(orch_id[0], e.host) is False:
                                    self.logger.warn("EVENT: planned vm was deleted")
                                    if self._check_uuid(e.uuid, e.host) is True:
                                        self._update_h_uuid_in_host(orch_id[0], e.uuid, e.host)
                                        self._update_h_uuid_in_logical_groups(orch_id[0], e.uuid, e.host)
                                else:
                                    self.logger.debug("EVENT: vm activated as planned")
                                    self._update_uuid_in_host(orch_id[0], e.uuid, e.host)
                                    self._update_uuid_in_logical_groups(orch_id[0], e.uuid, e.host)

                        resource_updated = True

                    elif e.vm_state == "deleted":
                        self.logger.debug("EVENT: got instance_delete for " + e.uuid)

                        self._remove_vm_from_host(e.uuid, orch_id[0], e.host, e.vcpus, e.mem, e.local_disk)
                        self._remove_vm_from_logical_groups(e.uuid, orch_id[0], e.host)

                        if self.app_handler.update_vm_info(orch_id[1], orch_id[0]) is False:
                            self.logger.error("EVENT: error while updating app in MUSIC")
                            self.data_lock.release()
                            return False

                        resource_updated = True

                    else:
                        self.logger.warn("EVENT: unknown event vm_state = " + e.vm_state)

                elif e.object_name == 'ComputeNode':     # Host resource is updated
                    self.logger.debug("EVENT: got compute for " + e.host)
                    # NOTE: what if host is disabled?
                    if self.resource.update_host_resources(e.host, e.status,
                                                           e.vcpus, e.vcpus_used,
                                                           e.mem, e.free_mem,
                                                           e.local_disk, e.free_local_disk,
                                                           e.disk_available_least) is True:
                        self.resource.update_host_time(e.host)

                        resource_updated = True

                else:
                    self.logger.warn("EVENT: unknown object_name = " + e.object_name)
            else:
                self.logger.warn("EVENT: unknown method = " + e.method)

            events_count += 1
            handled_event_list.append(e)
            if events_count >= self.batch_events_count:
                break

        if resource_updated is True:
            self.resource.update_topology(store=False)

        for e in handled_event_list:
            if self.db.delete_event(e.event_id) is False:
                self.data_lock.release()
                return False
            if e.method == "object_action":
                if e.object_name == 'Instance':
                    if e.vm_state == "deleted":
                        if self.db.delete_uuid(e.uuid) is False:
                            self.data_lock.release()
                            return False

        self.data_lock.release()

        return True

    def _add_vm_to_host(self, _uuid, _h_uuid, _host_name, _vcpus, _mem, _local_disk):
        existing_vm = False
        if self._check_uuid(_uuid, _host_name) is True:
            existing_vm = True
        else:
            if self._check_h_uuid(_h_uuid, _host_name) is True:
                existing_vm = True

        if existing_vm is False:
            vm_id = None
            if _h_uuid is None:
                vm_id = ("none", "none", _uuid)
            else:
                vm_id = (_h_uuid, "none", _uuid)

            self.resource.add_vm_to_host(_host_name, vm_id, _vcpus, _mem, _local_disk)
            self.resource.update_host_time(_host_name)

    def _remove_vm_from_host(self, _uuid, _h_uuid, _host_name, _vcpus, _mem, _local_disk):
        if self._check_h_uuid(_h_uuid, _host_name) is True:
            self.resource.remove_vm_by_h_uuid_from_host(_host_name, _h_uuid, _vcpus, _mem, _local_disk)
            self.resource.update_host_time(_host_name)
        else:
            if self._check_uuid(_uuid, _host_name) is True:
                self.resource.remove_vm_by_uuid_from_host(_host_name, _uuid, _vcpus, _mem, _local_disk)
                self.resource.update_host_time(_host_name)
            else:
                self.logger.warn("vm (" + _uuid + ") is missing while removing")

    def _remove_vm_from_logical_groups(self, _uuid, _h_uuid, _host_name):
        host = self.resource.hosts[_host_name]
        if _h_uuid is not None and _h_uuid != "none":
            self.resource.remove_vm_by_h_uuid_from_logical_groups(host, _h_uuid)
        else:
            self.resource.remove_vm_by_uuid_from_logical_groups(host, _uuid)

    def _check_host(self, _host_name):
        exist = False

        for hk in self.resource.hosts.keys():
            if hk == _host_name:
                exist = True
                break

        return exist

    def _check_h_uuid(self, _h_uuid, _host_name):
        if _h_uuid is None or _h_uuid == "none":
            return False

        host = self.resource.hosts[_host_name]

        return host.exist_vm_by_h_uuid(_h_uuid)

    def _check_uuid(self, _uuid, _host_name):
        if _uuid is None or _uuid == "none":
            return False

        host = self.resource.hosts[_host_name]

        return host.exist_vm_by_uuid(_uuid)

    def _update_uuid_in_host(self, _h_uuid, _uuid, _host_name):
        host = self.resource.hosts[_host_name]
        if host.update_uuid(_h_uuid, _uuid) is True:
            self.resource.update_host_time(_host_name)
        else:
            self.logger.warn("fail to update uuid in host = " + host.name)

    def _update_h_uuid_in_host(self, _h_uuid, _uuid, _host_name):
        host = self.resource.hosts[_host_name]
        if host.update_h_uuid(_h_uuid, _uuid) is True:
            self.resource.update_host_time(_host_name)

    def _update_uuid_in_logical_groups(self, _h_uuid, _uuid, _host_name):
        host = self.resource.hosts[_host_name]

        self.resource.update_uuid_in_logical_groups(_h_uuid, _uuid, host)

    def _update_h_uuid_in_logical_groups(self, _h_uuid, _uuid, _host_name):
        host = self.resource.hosts[_host_name]

        self.resource.update_h_uuid_in_logical_groups(_h_uuid, _uuid, host)

    def _get_json_results(self, _request_type, _status_type, _status_message, _map):
        result = {}

        if _request_type == "query":
            for qk, qr in _map.iteritems():
                query_result = {}

                query_status = {}
                if qr is None:
                    query_status['type'] = "error"
                    query_status['message'] = _status_message
                else:
                    query_status['type'] = "ok"
                    query_status['message'] = "success"

                query_result['status'] = query_status
                if qr is not None:
                    query_result['resources'] = qr

                result[qk] = query_result

        else:
            if _status_type != "error":
                applications = {}
                for v in _map.keys():
                    if isinstance(v, VM) or isinstance(v, Volume):
                        resources = None
                        if v.app_uuid in applications.keys():
                            resources = applications[v.app_uuid]
                        else:
                            resources = {}
                            applications[v.app_uuid] = resources

                        host = _map[v]
                        resource_property = {"host": host}
                        properties = {"properties": resource_property}
                        resources[v.uuid] = properties

                for appk, app_resources in applications.iteritems():
                    app_result = {}
                    app_status = {}

                    app_status['type'] = _status_type
                    app_status['message'] = _status_message

                    app_result['status'] = app_status
                    app_result['resources'] = app_resources

                    result[appk] = app_result

                for appk, app in self.app_handler.apps.iteritems():
                    if app.request_type == "ping":
                        app_result = {}
                        app_status = {}

                        app_status['type'] = _status_type
                        app_status['message'] = "ping"

                        app_result['status'] = app_status
                        app_result['resources'] = {"ip": self.config.ip, "id": self.config.priority}

                        result[appk] = app_result

            else:
                for appk in self.app_handler.apps.keys():
                    app_result = {}
                    app_status = {}

                    app_status['type'] = _status_type
                    app_status['message'] = _status_message

                    app_result['status'] = app_status
                    app_result['resources'] = {}

                    result[appk] = app_result

        return result
