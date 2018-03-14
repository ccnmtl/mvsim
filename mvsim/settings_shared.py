# Django settings for mvsim project.
import os.path
from ccnmtlsettings.shared import common
from courseaffils.columbia import CourseStringMapper

project = 'mvsim'
base = os.path.dirname(__file__)

locals().update(common(project=project, base=base))

INSTALLED_APPS += [  # noqa
    'courseaffils',
    'mvsim.main',
    'engine',
    'registration',
]

MIDDLEWARE_CLASSES += [  # noqa
    'djangohelpers.middleware.AuthRequirementMiddleware',
]

LOGOUT_REDIRECT_URL = LOGIN_REDIRECT_URL = '/'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True


DEFORM_TEMPLATE_OVERRIDES = os.path.join(os.path.dirname(__file__),
                                         "../deform_templates")

ACCOUNT_ACTIVATION_DAYS = 7

PROJECT_APPS = [
    'mvsim.main',
    'engine',
    # for some reason, this one is breaking with django 1.7
    #    'mvsim.graph',
]

DEFAULT_FROM_EMAIL = 'mvsim@mvsim.ccnmtl.columbia.edu'

ANONYMOUS_PATHS = (
    '/accounts/',
    '/static/',
    '/site_media/',
    '/docs/',
    '/admin/',
    '/registration/',
    '/favicon.ico',
    '/smoketest/',
)

COURSEAFFILS_COURSESTRING_MAPPER = CourseStringMapper

MVSIM_EVENTS_CSV = os.path.join(os.path.dirname(__file__), "../events.csv")

# For a production instance this should be changed to a /var/www-like
# directory served by Apache but for development it's convenient to
# just stuff these under the static media directory.

MVSIM_GRAPH_OUTPUT_DIRECTORY = os.path.join(os.path.dirname(__file__),
                                            "../media/graphs")
