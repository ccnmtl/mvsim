from django.conf import settings
from mvsim.settings_shared import *  # noqa: F403
from ctlsettings.staging import common, init_sentry
import os

project = 'mvsim'
base = os.path.dirname(__file__)

locals().update(
    common(
        project=project,
        base=base,
        STATIC_ROOT=STATIC_ROOT,  # noqa: F405
        INSTALLED_APPS=INSTALLED_APPS,  # noqa: F405
        s3prefix='ccnmtl',
        cloudfront='d3opx5c84brxu8',
    ))

try:
    from mvsim.local_settings import *  # noqa: F403 F401
except ImportError:
    pass

MVSIM_GRAPH_OUTPUT_DIRECTORY = "/var/www/mvsim/uploads/graphs"

if hasattr(settings, 'SENTRY_DSN'):
    init_sentry(SENTRY_DSN)  # noqa F405
