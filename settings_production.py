from settings_shared import *

TEMPLATE_DIRS = (
    "/var/www/mvsim/mvsim/templates",
)

MEDIA_ROOT = '/var/www/mvsim/uploads/'
# put any static media here to override app served static media
STATICMEDIA_MOUNTS = (
    ('/sitemedia', '/var/www/mvsim/mvsim/sitemedia'),	
)


DEBUG = False
TEMPLATE_DEBUG = DEBUG

try:
    from local_settings import *
except ImportError:
    pass

MVSIM_GRAPH_OUTPUT_DIRECTORY = "/var/www/mvsim/graphs")
