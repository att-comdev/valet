from pecan.hooks import TransactionHook

from valet.api.db import models
from valet.api.common.hooks import NotFoundHook, MessageNotificationHook


# Server Specific Configurations
server = {
    'port': '8090',
    'host': '0.0.0.0'
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

logging = {
    'root': {'level': 'DEBUG', 'handlers': ['console']},
    'loggers': {
        'api': {
            'level': 'DEBUG', 'handlers': ['console'], 'propagate': False
        },
        'api.models': {
            'level': 'INFO', 'handlers': ['console'], 'propagate': False
        },
        'pecan': {
            'level': 'DEBUG', 'handlers': ['console'], 'propagate': False
        },
        'py.warnings': {'handlers': ['console']},
        '__force_dict__': True
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'color'
        }
    },
    'formatters': {
        'simple': {
            'format': ('%(asctime)s %(levelname)-5.5s [%(name)s]'
                       '[%(threadName)s] %(message)s')
        },
        'color': {
            '()': 'pecan.log.ColorFormatter',
            'format': ('%(asctime)s [%(padded_color_levelname)s] [%(name)s]'
                       '[%(threadName)s] %(message)s'),
            '__force_dict__': True
        }
    }
}

ostro = {
    'tries': 10,
    'interval': 1,
}

messaging = {
    'config': {
        'transport_url': 'rabbit://openstack:Aa123456@controller:5672/',
    }
}

identity = {
    'config': {
        'username': 'demo',
        'password': 'Aa123456',
        'project_name': 'demo',
        'auth_url': 'http://controller:5000/v2.0',
    }
}

music = {
    'host': 'valet2',
    'hosts': 'valet1, valet2',
    'port': '8080',
    'keyspace': 'valet_test',
    'replication_factor': 3,
}
