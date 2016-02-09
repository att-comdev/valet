#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
#################################################################################################################


import sys

sys.path.insert(0, '../app_manager')
from app_topology_base import VGroup, VM, Volume


def display_app_topology(_app_topology):
    print "===Input logical topology==="
    for sn in _app_topology.vms.keys():
        s = _app_topology.vms[sn]
        print "VM = ", s.name
        for dzk in s.diversity_groups.keys():
            dz = s.diversity_groups[dzk]
            print "    diversity = ", dzk + "::" + dz
        if s.affinity_group != None:
            print "    affinity = ", s.affinity_group.uuid + "::" + s.affinity_group.level
        print "    vcpus = ", s.vCPUs
        print "    mem = {} MB".format(s.mem) 
        print "    local volume = {} GB".format(s.local_volume_size)
        print "    total nw bw = {} Mbps, total io bw = {} Mbps".format(s.nw_bandwidth, s.io_bandwidth)
        print "    vCPU weight = ", s.vCPU_weight
        print "    mem weight = ", s.mem_weight
        print "    local volume weight = ", s.local_volume_weight
        print "    bandwidth weight = {}".format(s.bandwidth_weight)
        for vl in s.volume_list: 
            print "    volume = ", vl.node.name                        
            for dzk in vl.node.diversity_groups.keys():
                dz = vl.node.diversity_groups[dzk]    
                print "        diversity = ", dzk + "::" + dz 
            if vl.node.affinity_group != None:
                print "        affinity = ", vl.node.affinity_group.uuid + "::" + vl.node.affinity_group.level
            print "        volume class = ", vl.node.volume_class
            print "        volume size = {} GB".format(vl.node.volume_size)
            print "        total io bw = {} Mbps".format(vl.node.io_bandwidth)
            print "        volume weight = ", vl.node.volume_weight 
            print "        io bw weight = ", vl.node.bandwidth_weight                       
            print "        access type = ", vl.access_type
            print "        volume io bw = {} Mbps".format(vl.io_bandwidth)                 
        for l in s.vm_list:                                                                           
            print "    linked vm = ", l.node.name
            print "        bw = {} Mbps".format(l.nw_bandwidth)
    for vgk in _app_topology.vgroups.keys():
        _display_vgroups(_app_topology.vgroups[vgk])
    print "========================================="

def _display_vgroups(_vg):
    print "VGroup = ", _vg.name
    if isinstance(_vg, VGroup):
        print "    level = ", _vg.level
    for dzk in _vg.diversity_groups.keys():
        dz = _vg.diversity_groups[dzk]
        print "    diversity = ", dzk + "::" + dz
    if _vg.affinity_group != None:
        print "    affinity = ", _vg.affinity_group.uuid + "::" + _vg.affinity_group.level
    if isinstance(_vg, VM):
        print "    vcpus = ", _vg.vCPUs
        print "    mem = {} MB".format(_vg.mem) 
        print "    local volume = {} GB".format(_vg.local_volume_size)
        print "    total nw bw = {} Mbps, total io bw = {} Mbps".format(_vg.nw_bandwidth, _vg.io_bandwidth)
        print "    vCPU weight = ", _vg.vCPU_weight
        print "    mem weight = ", _vg.mem_weight
        print "    local volume weight = ", _vg.local_volume_weight
        print "    bandwidth weight = {}".format(_vg.bandwidth_weight)
        for l in _vg.vm_list:
            print "    linked group = ", l.node.name
            print "        bw = {} Mbps".format(l.nw_bandwidth)
        for l in _vg.volume_list:
            print "    linked group = ", l.node.name
            print "        io = {} Mbps".format(l.io_bandwidth)
    elif isinstance(_vg, Volume):
        print "    volume class = ", _vg.volume_class
        print "    volume = {} GB".format(_vg.volume_size)
        print "    total io bw = {} Mbps".format(_vg.io_bandwidth)
        print "    volume weight = ", _vg.volume_weight
        print "    io bw weight = ", _vg.bandwidth_weight
        for l in _vg.vm_list:
            print "    linked group = ", l.node.name
            print "        io = {} Mbps".format(l.io_bandwidth)
    elif isinstance(_vg, VGroup):
        print "    vcpus = ", _vg.vCPUs
        print "    mem = {} MB".format(_vg.mem) 
        print "    local volume = {} GB".format(_vg.local_volume_size)
        print "    volumes"
        for vol_class in _vg.volume_sizes.keys():
            print "      volume class = ", vol_class
            print "      size = {} GB".format(_vg.volume_sizes[vol_class])
        print "    total nw bw = {} Mbps, total io bw = {} Mbps".format(_vg.nw_bandwidth, _vg.io_bandwidth)
        print "    vCPU weight = ", _vg.vCPU_weight
        print "    mem weight = ", _vg.mem_weight
        print "    local volume weight = ", _vg.local_volume_weight
        print "    volume weight = ", _vg.volume_weight
        print "    bandwidth weight = {}".format(_vg.bandwidth_weight)
    if isinstance(_vg, VGroup):
        print "    links:"
        for l in _vg.vgroup_list:
            print "        name = ", l.node.name
            print "            nw bandwidth = {}, io bandwidth = {}".format(l.nw_bandwidth, l.io_bandwidth)
        for svg in _vg.subvgroup_list:
            print "---in subgroup {}---".format(svg.name)
            _display_vgroups(svg)
            print "---out subgroup {}---".format(svg.name)

def display_dc_topology(_topology): 
    print "===Physical topology==="
    print "Last updated time = ", _topology.current_timestamp

    print "datacenter = ", _topology.datacenter.name
    print "  last updated = ", _topology.datacenter.last_update
    print "  vCPUs = ", _topology.datacenter.vCPUs
    print "  avail vCPUs = ", _topology.datacenter.avail_vCPUs
    print "  mem = {} MB".format(_topology.datacenter.mem_cap)
    print "  avail mem = {} MB".format(_topology.datacenter.avail_mem_cap)
    print "  local disk = {} GB".format(_topology.datacenter.local_disk_cap)
    print "  avail local disk = {} GB".format(_topology.datacenter.avail_local_disk_cap)
    print "  storages"
    for shk in _topology.datacenter.storages.keys():
        sh = _topology.datacenter.storages[shk]
        print "    name = ", sh.name
        print "      status = ", sh.status
        #print "      disk = ", sh.disk.name
        print "      class = ", sh.storage_class
        print "      hosts = ", sh.host_list
        print "      cap = {} GB".format(sh.disk_cap)
        print "      avail cap = {} GB".format(sh.avail_disk_cap)

    for ss in _topology.datacenter.spine_switch_list:
        print "  cluster = ", ss.name
        print "  status = ", ss.status
        print "  last updated = ", ss.last_update
        for dcs in ss.switch_list:
            print "    datacenter = ", dcs.resource.name
            print "      outbound bw = {} Mbps".format(dcs.nw_bandwidth)
            print "      avail outbound bw = {} Mbps".format(dcs.avail_nw_bandwidth)
        for pss in ss.peer_switch_list:
            print "    peer = ", pss.resource.name
            print "      outbound bw = {} Mbps".format(pss.nw_bandwidth)
            print "      avail outbound bw = {} Mbps".format(pss.avail_nw_bandwidth)
        print "    vCPUs = ", ss.vCPUs
        print "    avail vCPUs = ", ss.avail_vCPUs
        print "    mem = {} MB".format(ss.mem_cap)
        print "    avail mem = {} MB".format(ss.avail_mem_cap)
        print "    local disk = {} GB".format(ss.local_disk_cap)
        print "    avail local disk = {} GB".format(ss.avail_local_disk_cap)
        print "    storages"
        for cshk in ss.storages.keys():
            csh = ss.storages[cshk]
            print "      name = ", csh.name
            print "        status = ", csh.status
            #print "      disk = ", csh.disk.name
            print "        class = ", csh.storage_class
            print "        hosts = ", csh.host_list
            print "        cap = {} GB".format(csh.disk_cap)
            print "        avail cap = {} GB".format(csh.avail_disk_cap)
        #for ios in ss.io_switch_list:
            #print "    io switch = ", ios.resource.name
            #print "      outbound bw = {} Mbps".format(ios.nw_bandwidth)
            #print "      avail outbound bw = {} Mbps".format(ios.avail_nw_bandwidth)

        if len(ss.leaf_switch_list) > 0:
            for s in ss.leaf_switch_list:
                print "    rack = ", s.name
                print "    status = ", s.status
                print "    last updated = ", s.last_update
                for ssl in s.spine_switch_list:
                    print "      spine switch = ", ssl.resource.name
                    print "        outbound bw = {} Mbps".format(ssl.nw_bandwidth)
                    print "        avail outbound bw = {} Mbps".format(ssl.avail_nw_bandwidth)
                for psl in s.peer_switch_list:
                    print "      peer = ", psl.resource.name
                    print "        outbound bw = {} Mbps".format(psl.nw_bandwidth)
                    print "        avail outbound bw = {} Mbps".format(psl.avail_nw_bandwidth)
                print "      vCPUs = ", s.vCPUs
                print "      avail vCPUs = ", s.avail_vCPUs
                print "      mem = {} MB".format(s.mem_cap)
                print "      avail mem = {} MB".format(s.avail_mem_cap)
                print "      local disk = {} GB".format(s.local_disk_cap)
                print "      avail local disk = {} GB".format(s.avail_local_disk_cap)
                print "      storages"
                for rshk in s.storages.keys():
                    rsh = s.storages[rshk]
                    print "        name = ", rsh.name
                    print "          status = ", rsh.status
                    #print "        disk = ", rsh.disk.name
                    print "          class = ", rsh.storage_class
                    print "          hosts = ", rsh.host_list
                    print "          cap = {} GB".format(rsh.disk_cap)
                    print "          avail cap = {} GB".format(rsh.avail_disk_cap)
                #for rios in s.io_switch_list:
                    #print "      io switch = ", rios.resource.name
                    #print "        outbound bw = {} Mbps".format(rios.nw_bandwidth)
                    #print "        avail outbound bw = {} Mbps".format(rios.avail_nw_bandwidth)

                for h in s.host_list:
                    print "      host = ", h.name
                    print "        last updated = ", h.last_update
                    print "        tag = ", h.tag
                    print "        status = ", h.status
                    print "        state = ", h.state
                    print "        zone = ", h.zone
                    print "        aggregate = ", h.aggregate
                    for lsl in h.leaf_switch_list:
                        print "        leaf switch = ",lsl.resource.name
                        print "          outbound bw = {} Mbps".format(lsl.nw_bandwidth)
                        print "          avail outbound bw = {} Mbps".format(lsl.avail_nw_bandwidth)
                    print "        vCPUs = ", h.vCPUs
                    print "        avail vCPUs = ", h.avail_vCPUs
                    print "        mem = {} MB".format(h.mem_cap)
                    print "        avail mem = {} MB".format(h.avail_mem_cap)
                    print "        local_disk = {} GB".format(h.local_disk_cap)
                    print "        avail local disk = {} GB".format(h.avail_local_disk_cap)
                    print "        storages"
                    for hshk in h.storages.keys():
                        hsh = h.storages[hshk]
                        print "          name = ", hsh.name
                        print "            status = ", hsh.status
                        #print "          disk = ", hsh.disk.name
                        print "            class = ", hsh.storage_class
                        print "            hosts = ", hsh.host_list
                        print "            cap = {} GB".format(hsh.disk_cap)
                        print "            avail cap = {} GB".format(hsh.avail_disk_cap)
                        print "            volume list"
                        for vol in hsh.volume_list:
                            print "            vol = {}".format(vol)
                    #for hios in h.io_switch_list:
                        #print "        io switch = ", hios.resource.name
                        #print "          outbound bw = {} Mbps".format(hios.nw_bandwidth)
                        #print "          avail outbound bw = {} Mbps".format(hios.avail_nw_bandwidth)
                    print "        vm list"
                    for vm in h.vm_list:
                        print "          vm = {}".format(vm)
                    print "        volume list"
                    for vol in h.volume_list:
                        print "          volume = {}".format(vol)
        else:
            for h in ss.host_list:
                print "    host = ", h.name
                print "      last updated = ", h.last_update
                print "      tag = ", h.tag
                print "      status = ", h.status
                print "      state = ", h.state
                print "      zone = ", h.zone
                print "      aggregate = ", h.aggregate
                for lsl in h.leaf_switch_list:
                    print "      leaf switch = ",lsl.resource.name
                    print "        outbound bw = {} Mbps".format(lsl.nw_bandwidth)
                    print "        avail outbound bw = {} Mbps".format(lsl.avail_nw_bandwidth)
                print "      vCPUs = ", h.vCPUs
                print "      avail vCPUs = ", h.avail_vCPUs
                print "      mem = {} MB".format(h.mem_cap)
                print "      avail mem = {} MB".format(h.avail_mem_cap)
                print "      local disk = {} GB".format(h.local_disk_cap)
                print "      avail local disk = {} GB".format(h.avail_local_disk_cap)
                print "      storages"
                for hshk in h.storages.keys():
                    hsh = h.storages[hshk]
                    print "        name = ", hsh.name
                    print "          status = ", hsh.status
                    #print "        disk = ", hsh.disk.name
                    print "          class = ", hsh.storage_class
                    print "          hosts = ", hsh.host_list
                    print "          cap = {} GB".format(hsh.disk_cap)
                    print "          avail cap = {} GB".format(hsh.avail_disk_cap)
                    print "          volume list"
                    for vol in hsh.volume_list:
                        print "            vol = {}".format(vol)
                #for hios in h.io_switch_list:
                    #print "      io switch = ", hios.resource.name
                    #print "        outbound bw = {} Mbps".format(hios.nw_bandwidth)
                    #print "        avail outbound bw = {} Mbps".format(hios.avail_nw_bandwidth)
                print "      vm list"
                for vm in h.vm_list:
                    print "        vm = {}".format(vm)
                print "      volume list"
                for vol in h.volume_list:
                    print "          volume = {}".format(vol)



