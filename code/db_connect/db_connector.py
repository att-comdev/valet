#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.0: Oct. 15, 2015
#
#################################################################################################################


import uuid, time, sys 
from cassandra.cqlengine import connection
from cassandra.cqlengine.management import sync_table
from db_helper import *


class DatabaseConnector:

    def __init__(self, _keyspace):
        self.keyspace = _keyspace  # 'ostro_v_2_0_0' or 'ostro_test'

        connection.setup(['127.0.0.1'], self.keyspace, protocol_version=3)

        # Create tables
        sync_table(Apps)
        #sync_table(Infras)

        self.status = "success"

    # Insert info into table, apps or infras, depending on insert_type
    def insert(self, _insert_type, _info):
        if _insert_type == 'app':
            app_list = _info
            for app in app_list:    # info is a list of app
                self._insert_app(app)
        elif _insert_type == "infrastructure":
            pass

    # Insert one application information using Object Mapper
    def _insert_app(self, _app):  
        application_id = _app['ID']
        application_name = _app['Name']
        application_status = _app['Status']
        vms = _app['VMs']
        volumes = _app['Volumes']
        vgroups = _app['VGroups']

        new_vms = {}
        new_volumes = {}
        new_vgroups = {}

        for vm_id, vm_info in vms.iteritems():
            new_vms[vm_id] = VM(name = vm_info['name'], \
                                status = vm_info['status'], \
                                uuid = vm_info['uuid'], \
                                affinity_group = vm_info['affinity_group'], \
                                availability_zone = vm_info['availability_zone'], \
                                diversity_groups = vm_info['diversity_groups'], \
                                cpu = vm_info['cpu'], \
                                mem = vm_info['mem'], \
                                local_volume = vm_info['lvol'], \
                                nw = vm_info['nw'], \
                                io = vm_info['io'], \
                                vol_links = vm_info['vol_links'], \
                                vm_links = vm_info['vm_links'], \
                                host = vm_info['host'])

        for vol_id, vol_info in volumes.iteritems():
            new_volumes[vol_id] = Volume(name = vol_info['name'], \
                                         status = vol_info['status'], \
                                         uuid = vol_info['uuid'], \
                                         affinity_group = vol_info['affinity_group'], \
                                         availability_zone = vol_info['availability_zone'], \
                                         diversity_groups = vol_info['diversity_groups'], \
                                         vol_class = vol_info['class'], \
                                         size = vol_info['size'], \
                                         io = vol_info['io'], \
                                         vm_links = vol_info['vm_links'], \
                                         host = vol_info['host'])

        for vg_id, vg_info in vgroups.iteritems():
            new_vgroups[vg_id] = VGroup(name = vg_info['name'], \
                                        affinity_group = vg_info['affinity_group'], \
                                        availability_zone = vg_info['availability_zone'], \
                                        diversity_groups = vg_info['diversity_groups'], \
                                        level = vg_info['level'], \
                                        cpu = vg_info['cpu'], \
                                        mem = vg_info['mem'], \
                                        local_volume = vg_info['lvol'], \
                                        volume = vg_info['vol'], \
                                        nw = vg_info['nw'], \
                                        io = vg_info['io'], \
                                        vol_links = vg_info['vol_links'], \
                                        vm_links = vg_info['vm_links'], \
                                        sub_vgroups = vg_info['subvgroups'], \
                                        vms= vg_info['vms'], \
                                        volumes= vg_info['volumes'])

        Apps.create(app_id = application_id, \
                    event_time = time.time(), \
                    status = application_status, \
                    app_name = application_name, \
                    app_info = AppInfo(vms = new_vms, \
                                       volumes = new_volumes, \
                                       vgroups = new_vgroups))


               
    # Query info in table apps or infrastructures depending on query_type
    def query(self, _query_type, _info):
        if _query_type == 'app':
            app_id = _info
            return self._query_app(app_id)
        elif _query_type == "infrastructure":
            pass

        return {}

    # Delete from table(s) depending on delete_type
    def delete(self, _delete_type, _info):
        if _delete_type == 'app':
            self._delete_app(_info)
        elif _delete_type == "infrastructure":
            pass
 
    # Query the app info. Only return the latest record
    def _query_app(self, _app_name):
        info = None
        try:
            if _app_name == "all":
                info = Apps.objects.all()
            else:
                info = Apps.objects.filter(app_name = _app_name)
            
            n = info.count()
            if n > 0:                       
                return app_info_to_json(info[n-1])
            else:
                return None
        except:
            e = sys.exc_info()[0]
            self.status = "DB app query error: " + e
            return None

    # Query application status
    def query_app_status(self, _app_name):
        try:
            info = Apps.objects.filter(app_name = _app_name)
            n = info.count()

            if n > 0:
                app = info[n-1]
                return app.app_info.status
            else:
                return None
        except:
            e = sys.exc_info()[0]
            self.status = "DB app status query error: " + e
            return None

    # Delete app info. Now only mark this app as 'deleted'. record is NOT deleted!
    def _delete_app(self, _app_name):
        info = Apps.objects.filter(app_name = _app_name)

        try:
            n = info.count()
            if n > 0:
                app = info[n-1]
                old_info = app.app_info
                new_app_info = AppInfo(status = 'deleted', \
                                       vm_list = old_info.vm_list, \
                                       pipes = old_info.pipes, \
                                       constraints = old_info.constraints, \
                                       event = old_info.event)
                app.update(app_info = new_app_info)
                return True
            else:
                self.status = "cannot find app to delete from DB"
                return False

        except:
            e = sys.exc_info()
            self.status = "DB app delete error: " + e
            return False

    # TODO: Update value of existing app (in Cassandra by read and write)
    def update_app(self, _app_name, _data):
        info = Apps.objects.filter(app_name = _app_name)

        try:
            n = info.count()
            if n > 0:   
                app = info[n-1]         # Only update the latest one
                old_info = app.app_info
                update_msg = self._parse_data(_data)

                new_app_info = AppInfo(status = 'active', \
                                       vm_list = old_info.vm_list, \
                                       pipes = old_info.pipes, \
                                       constraints = old_info.constraints, \
                                       event = old_info.event)
                app.update(app_info = new_app_info)
                return True

            else:
                self.status = "cannot find app to update in DB"
                return False
        except:
            e = sys.exc_info()
            self.status = "DB app update error: " + e
            return False

    # TODO: Parse input data to get information for updating table value
    def _parse_data(self, _data):
        return _data


if __name__ == '__main__':

    db = DatabaseConnector()

    db.insert_app("app1", "info")
    print db.query_app("app1")
    time.sleep(5)
    db.insert_app("app1", "info")
    print db.query_app("app1")


