import os, sys, site

sys.path.append('/var/www/mvsim/mvsim/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'mvsim.settings_staging'

import django.core.handlers.wsgi
import django
django.setup()
application = django.core.handlers.wsgi.WSGIHandler()
