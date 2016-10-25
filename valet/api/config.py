from oslo_config import cfg

CONF = cfg.CONF

server_group = cfg.OptGroup(name='server', title='Valet API Server conf')
server_opts = [
    cfg.StrOpt('host', default='0.0.0.0'),
    cfg.StrOpt('port', default='8090'),
]


messaging_group = cfg.OptGroup(name='messaging', title='Valet Messaging conf')
messaging_opts = [
    cfg.StrOpt('username'),
    cfg.StrOpt('password'),
    cfg.StrOpt('host'),
    cfg.StrOpt('port', default='5672'),
]


ostro_group = cfg.OptGroup(name='ostro', title='Valet Engine conf')
ostro_opts = [
    cfg.IntOpt('tries', default=10),
    cfg.IntOpt('interval', default=1)
]


identity_group = cfg.OptGroup(name='identity', title='Valet identity conf')
identity_opts = [
    cfg.StrOpt('interface'),
    cfg.StrOpt('username'),
    cfg.StrOpt('password'),
    cfg.StrOpt('project_name'),
    cfg.StrOpt('auth_url', default='http://controller:5000/v2.0')
]


music_group = cfg.OptGroup(name='music', title='Valet Persistence conf')
music_opts = [
    cfg.StrOpt('host', default='0.0.0.0'),
    cfg.IntOpt('port', default=8080),
    cfg.StrOpt('keyspace', default='valet'),
    cfg.IntOpt('replication_factor', default=3),
    cfg.StrOpt('request_table', default='placement_requests'),
    cfg.StrOpt('response_table', default='placement_results'),
    cfg.StrOpt('event_table', default='oslo_messages'),
    cfg.StrOpt('resource_table', default='resource_status'),
    cfg.StrOpt('app_table', default='app'),
    cfg.StrOpt('resource_index_table', default='resource_log_index'),
    cfg.StrOpt('app_index_table', default='app_log_index'),
    cfg.StrOpt('uuid_table', default='uuid_map'),
    cfg.StrOpt('db_host', default='localhost')
    # cfg.ListOpt('db_hosts', default='valet1,valet2,valet3')
]


def set_valet_conf(file_name):
    CONF(default_config_files=[file_name])


def register_conf():
    CONF.register_group(server_group)
    CONF.register_opts(server_opts, server_group)
    CONF.register_group(music_group)
    CONF.register_opts(music_opts, music_group)
    CONF.register_group(identity_group)
    CONF.register_opts(identity_opts, identity_group)
    CONF.register_group(ostro_group)
    CONF.register_opts(ostro_opts, ostro_group)
    CONF.register_group(messaging_group)
    CONF.register_opts(messaging_opts, messaging_group)
