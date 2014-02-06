# flake8: noqa
from settings_shared import *

TEMPLATE_DIRS = (
    "/var/www/mvsim/mvsim/mvsim/templates",
)

MEDIA_ROOT = '/var/www/mvsim/uploads/'
# put any static media here to override app served static media
STATICMEDIA_MOUNTS = (
    ('/sitemedia', '/var/www/mvsim/mvsim/sitemedia'),
)


DEBUG = False
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mvsim',
        'HOST': '',
        'PORT': 6432,
        'USER': '',
        'PASSWORD': '',
        }
}

if 'migrate' not in sys.argv:
    INSTALLED_APPS.append('raven.contrib.django.raven_compat')

try:
    from local_settings import *
except ImportError:
    pass

MVSIM_GRAPH_OUTPUT_DIRECTORY = "/var/www/mvsim/uploads/graphs"
