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
    'keyspace': 'valet_test'
}
