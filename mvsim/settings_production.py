# flake8: noqa
from settings_shared import *
from ccnmtlsettings.production import common
import os

project = 'mvsim'
base = os.path.dirname(__file__)

locals().update(
    common(
        project=project,
        base=base,
        STATIC_ROOT=STATIC_ROOT,
        INSTALLED_APPS=INSTALLED_APPS,
        cloudfront='d3l9lx77lf1ppr',
    ))

try:
    from local_settings import *
except ImportError:
    pass

MVSIM_GRAPH_OUTPUT_DIRECTORY = "/var/www/mvsim/uploads/graphs"
