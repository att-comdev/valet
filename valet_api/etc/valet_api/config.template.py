from pecan.hooks import TransactionHook

from valet_api import models
from valet_api.common.hooks import NotFoundHook, MessageNotificationHook


# Server Specific Configurations
server = {
    'port': '8090',
    'host': '0.0.0.0'
}

# Pecan Application Configurations
app = {
    'root': 'valet_api.controllers.root.RootController',
    'modules': ['valet_api'],
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
    'root': {'level': 'INFO', 'handlers': ['console']},
    'loggers': {
        'valet_api': {
            'level': 'DEBUG', 'handlers': ['console'], 'propagate': False
        },
        'valet_api.models': {
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
        'transport_url': 'rabbit://username:password@127.0.0.1:5672/',
    }
}

identity = {
    'config': {
        'username': 'valet',
        'password': 'password',
        'project_name': 'service',
        'auth_url': 'http://controller:5000/v2.0',
    }
}

music = {
    'host': '127.0.0.1',
    'port': '8080',
    'keyspace': 'valet',
    'replication_factor': 3,
}
