# Django settings for mvsim project.
import os.path
import sys

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = ()

MANAGERS = ADMINS

ALLOWED_HOSTS = ['.ccnmtl.columbia.edu', 'localhost']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mvsim',
        'HOST': '',
        'PORT': 5432,
        'USER': '',
        'PASSWORD': '',
        'ATOMIC_REQUESTS': True,
    }
}

TIME_ZONE = 'America/New_York'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = False
MEDIA_ROOT = "/var/www/mvsim/uploads/"
MEDIA_URL = '/uploads/'
STATIC_URL = '/media/'
SECRET_KEY = ')ng#)ef_u@_^zvvu@dxm7ql-yb^_!a6%v3v^j3b(mp+)l+5%@h'
LOGOUT_REDIRECT_URL = LOGIN_REDIRECT_URL = '/'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.template.context_processors.debug',
    'django.template.context_processors.request',
    'django.template.context_processors.static',
    'djangowind.context.context_processor',
    'stagingcontext.staging_processor',
)

MIDDLEWARE_CLASSES = (
    'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    'django_statsd.middleware.GraphiteMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'waffle.middleware.WaffleMiddleware',
    'impersonate.middleware.ImpersonateMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'djangohelpers.middleware.AuthRequirementMiddleware',
)

ROOT_URLCONF = 'mvsim.urls'

TEMPLATE_DIRS = (
    "/var/www/mvsim/templates/",
    os.path.join(os.path.dirname(__file__), "templates"),
)

DEFORM_TEMPLATE_OVERRIDES = os.path.join(os.path.dirname(__file__),
                                         "../deform_templates")

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.flatpages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'djangowind',
    'courseaffils',
    'registration',
    'mvsim.main',
    'django_statsd',
    'smoketest',
    'debug_toolbar',
    'impersonate',
    'django_jenkins',
    'engine',
    'waffle',
    'django_markwhat',
    'storages',
    'compressor',
]

INTERNAL_IPS = ('127.0.0.1', )
DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
)

STATSD_CLIENT = 'statsd.client'
STATSD_PREFIX = 'mvsim'
STATSD_HOST = 'localhost'
STATSD_PORT = 8125

ACCOUNT_ACTIVATION_DAYS = 7

if 'test' in sys.argv or 'jenkins' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
            'HOST': '',
            'PORT': '',
            'USER': '',
            'PASSWORD': '',
            'ATOMIC_REQUESTS': True,
        }
    }
    STATSD_HOST = '127.0.0.1'

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

JENKINS_TASKS = (
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pyflakes',
)

PROJECT_APPS = [
    'mvsim.main',
    'engine',
    # for some reason, this one is breaking with django 1.7
    #    'mvsim.graph',
]

THUMBNAIL_SUBDIR = "thumbs"
EMAIL_SUBJECT_PREFIX = "[mvsim] "
EMAIL_HOST = 'localhost'
SERVER_EMAIL = "mvsim@ccnmtl.columbia.edu"
DEFAULT_FROM_EMAIL = 'mvsim@mvsim.ccnmtl.columbia.edu'

# put any static media here to override app served static media
STATICMEDIA_MOUNTS = (
    ('/static', 'sitemedia'),
)

STATIC_ROOT = "/tmp/mvsim/static"
STATICFILES_DIRS = ("media/",)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

COMPRESS_URL = "/media/"
COMPRESS_ROOT = "media/"

# WIND settings

AUTHENTICATION_BACKENDS = ('djangowind.auth.SAMLAuthBackend',
                           'django.contrib.auth.backends.ModelBackend', )
CAS_BASE = "https://cas.columbia.edu/"

WIND_PROFILE_HANDLERS = ['djangowind.auth.CDAPProfileHandler']
WIND_AFFIL_HANDLERS = ['djangowind.auth.AffilGroupMapper',
                       'djangowind.auth.StaffMapper',
                       'djangowind.auth.SuperuserMapper']
WIND_STAFF_MAPPER_GROUPS = ['tlc.cunix.local:columbia.edu']
WIND_SUPERUSER_MAPPER_GROUPS = ['anp8', 'jb2410', 'zm4',
                                'egr2107', 'sld2131',
                                'amm8', 'mar227', ]

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

from courseaffils.columbia import CourseStringMapper
COURSEAFFILS_COURSESTRING_MAPPER = CourseStringMapper

MVSIM_EVENTS_CSV = os.path.join(os.path.dirname(__file__), "../events.csv")

# For a production instance this should be changed to a /var/www-like
# directory served by Apache but for development it's convenient to
# just stuff these under the static media directory.

MVSIM_GRAPH_OUTPUT_DIRECTORY = os.path.join(os.path.dirname(__file__),
                                            "../media/graphs")
LOGIN_REDIRECT_URL = "/"
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')

SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_HTTPONLY = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}
