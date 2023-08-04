# Django settings for mvsim project.
import os.path
from ccnmtlsettings.shared import common
from courseaffils.columbia import CourseStringMapper

project = 'mvsim'
base = os.path.dirname(__file__)

locals().update(common(project=project, base=base))

CAS_SERVER_URL = 'https://cas.columbia.edu/cas/'
CAS_VERSION = '3'
CAS_ADMIN_REDIRECT = False

# Translate CUIT's CAS user attributes to the Django user model.
# https://cuit.columbia.edu/content/cas-3-ticket-validation-response
CAS_APPLY_ATTRIBUTES_TO_USER = True
CAS_RENAME_ATTRIBUTES = {
    'givenName': 'first_name',
    'lastName': 'last_name',
    'mail': 'email',
}

INSTALLED_APPS.remove('djangowind') # noqa

INSTALLED_APPS += [  # noqa
    'courseaffils',
    'mvsim.main',
    'engine',
    'django_registration',
    'django_cas_ng',
]

MIDDLEWARE += [  # noqa
    'djangohelpers.middleware.AuthRequirementMiddleware',
    'django_cas_ng.middleware.CASMiddleware',
]

LOGOUT_REDIRECT_URL = LOGIN_REDIRECT_URL = '/'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


DEFORM_TEMPLATE_OVERRIDES = os.path.join(os.path.dirname(__file__),
                                         "../deform_templates")

ACCOUNT_ACTIVATION_DAYS = 7

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'django_cas_ng.backends.CASBackend'
]

PROJECT_APPS = [
    'mvsim.main',
    'engine',
    # for some reason, this one is breaking with django 1.7
    #    'mvsim.graph',
]

TEMPLATES[0]['OPTIONS']['context_processors'].remove(
    'djangowind.context.context_processor')

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
