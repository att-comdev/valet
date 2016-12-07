from oslo_config import cfg
from pecan.hooks import TransactionHook
from valet.api.db import models
from valet.api.common.hooks import NotFoundHook, MessageNotificationHook


CONF = cfg.CONF

# Server Specific Configurations
server = {
    'port': CONF.server.port,
    'host': CONF.server.host
}

# Pecan Application Configurations
app = {
    'root': 'valet.api.v1.controllers.root.RootController',
    'modules': ['valet.api'],
    'default_renderer': 'json',
    'force_canonical': False,
    'debug': False,
    'hooks': [
        TransactionHook(
            models.start,
            models.start_read_only,
            models.commit,
            models.rollback,
            models.clear
        ),
        NotFoundHook(),
        MessageNotificationHook(),
    ],
}

ostro = {
    'tries': CONF.music.tries,
    'interval': CONF.music.interval,
}


messaging = {
    'config': {
        'transport_url': 'rabbit://' + CONF.messaging.username + ':' + CONF.messaging.password +
        '@' + CONF.messaging.host + ':' + str(CONF.messaging.port) + '/'
    }
}

identity = {
    'config': {
        'username': CONF.identity.username,
        'password': CONF.identity.password,
        'project_name': CONF.identity.project_name,
        'auth_url': CONF.identity.auth_url,
        'interface': CONF.identity.interface,
    }
}

music = {
    'host': CONF.music.host,
    'port': CONF.music.port,
    'keyspace': CONF.music.keyspace,
    'replication_factor': CONF.music.replication_factor,
}
