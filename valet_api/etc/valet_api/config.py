from pecan.hooks import TransactionHook, RequestViewerHook

from valet_api import models


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
    'hooks': [
        TransactionHook(
            models.start,
            models.start_read_only,
            models.commit,
            models.rollback,
            models.clear
        ),
    ],
    #'static_root': '%(confdir)s/public',
    'template_path': '%(confdir)s/valet_api/templates',
    'debug': False,
}

logging = {
    'root': {'level': 'INFO', 'handlers': ['console']},
    'loggers': {
        'valet_api': {'level': 'DEBUG', 'handlers': ['console']},
        'pecan': {'level': 'DEBUG', 'handlers': ['console']},
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

identity = {
    'config': {
        'username': 'valet',
        'password': 'password',
        'project_name': 'service',
        'auth_url': 'http://qos101.research.att.com:5000/v2.0',
    }
}

sqlalchemy = {
    'url': 'mysql+pymysql://valet:password@127.0.0.1/valet?charset=utf8',
    'echo':          True,
    'echo_pool':     True,
    'pool_recycle':  3600,
    'encoding':      'utf-8',
}

music = {
    'host': '127.0.0.1',
    'port': '8080',
    'keyspace': 'valet',
    'replication_factor': 3,
}