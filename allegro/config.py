from pecan.hooks import TransactionHook, RequestViewerHook

# TODO: Make this a driver plugin point instead so we can pick and choose.
from allegro.models import music as models
#from allegro.models import sqlalchemy as models


# Server Specific Configurations
server = {
    'port': '8090',
    'host': '0.0.0.0'
}

# Pecan Application Configurations
app = {
    'root': 'allegro.controllers.root.RootController',
    'modules': ['allegro'],
    'default_renderer': 'json',
    'hooks': [
        TransactionHook(
            models.start,
            models.start_read_only,
            models.commit,
            models.rollback,
            models.clear
        ),
    ],
    'static_root': '%(confdir)s/public',
    'template_path': '%(confdir)s/allegro/templates',
    'debug': True,
    # Instead of this, add HTTP error reporters to controllers/errors.py
    #'errors': {
    #    404: '/error/404',
    #    '__force_dict__': True
    #}
}

logging = {
    'root': {'level': 'INFO', 'handlers': ['console']},
    'loggers': {
        'allegro': {'level': 'DEBUG', 'handlers': ['console']},
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

# NOTE: Can add 'interface' here and set to 'public'
# if the admin interface is unreachable. However, this
# means tenant visibility will be limited to those
# that allegro is a member of. The admin interface
# must be used in order to see all tenants, provided
# allegro has an admin role in at least one tenant
# (usually the service tenant).
identity = {
    'config': {
        'username': 'allegro',
        'password': 'password',
        'project_name': 'service',
        'auth_url': 'http://qos101.research.att.com:5000/v2.0',
    }
}

sqlalchemy = {
    'url': 'mysql+pymysql://allegro:password@127.0.0.1/allegro?charset=utf8',
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
