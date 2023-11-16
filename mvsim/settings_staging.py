from django.conf import settings
from mvsim.settings_shared import *  # noqa: F403
from ctlsettings.staging import common
import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

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
    from mvsim.local_settings import *  # noqa: F403
except ImportError:
    pass

MVSIM_GRAPH_OUTPUT_DIRECTORY = "/var/www/mvsim/uploads/graphs"

if hasattr(settings, 'SENTRY_DSN'):
    sentry_sdk.init(
        dsn=SENTRY_DSN,  # noqa: F405
        integrations=[DjangoIntegration()],
        debug=True,
    )
