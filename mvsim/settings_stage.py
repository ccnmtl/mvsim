# flake8: noqa
from settings import *

DATABASE_ENGINE = 'postgresql_psycopg2'

TEMPLATE_DIRS = (
    "/usr/local/share/sandboxes/common/mvsim/mvsim/templates",
)

MEDIA_ROOT = '/usr/local/share/sandboxes/common/mvsim/uploads/'

DEBUG = True
TEMPLATE_DEBUG = DEBUG
