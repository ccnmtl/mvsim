import os, sys, site

# enable the virtualenv
site.addsitedir('/var/www/mvsim/mvsim/ve/lib/python2.5/site-packages')

# paths we might need to pick up the project's settings
sys.path.append('/var/www/mvsim/mvsim/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'mvsim.settings_production'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
