from oslo_config import cfg
from valet.api import config as api

CONF = cfg.CONF

ostro_cli_opts = [
    cfg.StrOpt('command',
               short='c',
               default='status',
               help='engine command.'),
]


engine_group = cfg.OptGroup(name='engine', title='Valet Engine conf')
engine_opts = [
    cfg.StrOpt('pid', default='/var/run/valet/ostro-daemon.pid'),
    cfg.StrOpt('mode', default='live',
               help='sim will let Ostro simulate datacenter, while live will let it handle a real datacenter'),
    cfg.StrOpt('sim_cfg_loc', default='/etc/valet/engine/ostro_sim.cfg'),
    cfg.StrOpt('keystone_tenant_url', default='http://controller:35357/v2.0/tokens'),
    cfg.StrOpt('keystone_project_url', default='http://controller:35357/v3/projects'),
    cfg.StrOpt('nova_url', default='http://controller:8774'),
    cfg.StrOpt('nova_host_resources_api', default='/os-hypervisors/detail'),
    cfg.StrOpt('nova_host_zones_api', default='/os-hosts'),
    cfg.StrOpt('nova_host_aggregates_api', default='/os-aggregates'),
    cfg.StrOpt('nova_flavors_api', default='/flavors/detail'),
    cfg.BoolOpt('network_control', default=False, help='whether network controller (i.e., Tegu) has been deployed'),
    cfg.StrOpt('network_control_url', default='http://network_control:29444/tegu/api'),
    cfg.StrOpt('ip', default='localhost'),
    cfg.IntOpt('priority', default=1, help='this instance priority (master=1)'),
    cfg.StrOpt('rpc_server_ip', default='localhost',
               help='Set RPC server ip and port if used. Otherwise, ignore these parameters'),
    cfg.StrOpt('rpc_server_port', default='8002'),
    cfg.StrOpt('logger_name', default='engine.log'),
    cfg.StrOpt('logging_level', default='debug'),
    cfg.StrOpt('logging_dir', default='/var/log/valet/'),
    cfg.StrOpt('max_main_log_size', default=5000000),
    cfg.IntOpt('max_log_size', default=1000000),
    cfg.IntOpt('max_num_of_logs', default=20),
    cfg.StrOpt('datacenter_name', default='bigsite',
               help='Inform the name of datacenter (region name), where Valet/Ostro is deployed.'),
    cfg.IntOpt('num_of_region_chars', default='3', help='number of chars that indicates the region code'),
    cfg.StrOpt('rack_code_list', default='r', help='rack indicator.'),
    cfg.ListOpt('node_code_list', default='a,c,u,f,o,p,s',
                help='indicates the node type. a: network, c KVM compute, u: ESXi compute, f: ?, o: operation, '
                     'p: power, s: storage.'),
    cfg.StrOpt('compute_trigger_time', default='1:00',
               help='trigger time or frequency for checking compute hosting server status (i.e., call Nova)'),
    cfg.IntOpt('compute_trigger_frequency', default=3600,
               help='trigger time or frequency for checking compute hosting server status (i.e., call Nova)'),
    cfg.StrOpt('topology_trigger_time', default='2:00',
               help='Set trigger time or frequency for checking datacenter topology (i.e., call AIC Formation)'),
    cfg.IntOpt('topology_trigger_frequency', default=3600,
               help='Set trigger time or frequency for checking datacenter topology (i.e., call AIC Formation)'),
    cfg.IntOpt('default_cpu_allocation_ratio', default=16, help='Set default overbooking ratios. '
                                                                'Note that each compute node can have its own ratios'),
    cfg.IntOpt('default_ram_allocation_ratio', default=1.5, help='Set default overbooking ratios. '
                                                                 'Note that each compute node can have its own ratios'),
    cfg.IntOpt('default_disk_allocation_ratio', default=1, help='Set default overbooking ratios. '
                                                                'Note that each compute node can have its own ratios'),
    cfg.IntOpt('static_cpu_standby_ratio', default=20, help='unused percentages of resources (i.e. standby) '
                                                            'that are set aside for applications workload spikes.'),
    cfg.IntOpt('static_mem_standby_ratio', default=20, help='unused percentages of resources (i.e. standby) '
                                                            'that are set aside for applications workload spikes.'),
    cfg.IntOpt('static_local_disk_standby_ratio', default=20, help='unused percentages of resources (i.e. standby) '
                                                                   'that are set aside for applications workload spikes.'),
]


def register_conf():
    api.register_conf()
    CONF.register_group(engine_group)
    CONF.register_opts(engine_opts, engine_group)
    CONF.register_cli_opts(ostro_cli_opts)
