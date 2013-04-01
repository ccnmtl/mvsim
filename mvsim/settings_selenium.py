from settings_shared import *


# Running tests
#
# The tests rely on a checked in selenium_base.db located in
# mvsim/main/fixtures

# This base database was created like so:
# sqlite3 selenium.db
# ./manage.py syncdb --settings=mvsim.settings_selenium
# ./manage.py migrate --settings=mvsim.settings_selenium
# ./manage.py loaddata mvsim/main/fixtures/test_course.json \
# --settings=settings_selenium
# mv selenium.db mvsim/main/fixtures/selenum_base.db
#
# Run tests
# ./manage.py harvest --settings=mvsim.settings_selenium --debug-mode \
# --verbosity=2 --traceback

# Test Data
# mvsim/main/fixtures/test_course.json
#
# Test Course
# test_instructor/test
# admin/admin
# test_student_one/test
# test_student_two/test

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'selenium.db',
        'OPTIONS': {
            'timeout': 30,
        }
    }
}

LETTUCE_APPS = (
    'mvsim.main',
)

LETTUCE_SERVER_PORT = 8002
STATSD_HOST = '127.0.0.1'
BROWSER = 'Chrome'
