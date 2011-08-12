from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
import os.path
admin.autodiscover()
import staticmedia

site_media_root = os.path.join(os.path.dirname(__file__),"media")

redirect_after_logout = getattr(settings, 'LOGOUT_REDIRECT_URL', None)
auth_urls = (r'^accounts/',include('django.contrib.auth.urls'))
logout_page = (r'^accounts/logout/$','django.contrib.auth.views.logout', {'next_page': redirect_after_logout})
if hasattr(settings,'WIND_BASE'):
    auth_urls = (r'^accounts/',include('djangowind.urls'))
    logout_page = (r'^accounts/logout/$','djangowind.views.logout', {'next_page': redirect_after_logout})

urlpatterns = patterns(
    '',
    auth_urls,
    logout_page,

    url(r'^$', 'main.views.home', name='home'),
    url(r'^games/$', 'main.views.games_index', name='games_index'),
    url(r'^games/new/$', 'main.views.games_index', name='new_game'),
    
    url(r'^games/(?P<game_id>\d+)/$', 'main.views.show_turn', name='game_show'),
    url(r'^games/(?P<game_id>\d+)/turn/$', 'main.views.submit_turn'),
    url(r'^games/(?P<game_id>\d+)/game_over/$', 'main.views.game_over', name='game_over'),

    url(r'^games/(?P<game_id>\d+)/graph/$', 'graph.views.graph'),
    
    url(r'^state/(?P<state_id>\d+)/$', 'main.views.view_state'),
        
    (r'^admin/', include(admin.site.urls)),
    (r'^munin/',include('munin.urls')),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': site_media_root}),
    (r'^uploads/(?P<path>.*)$','django.views.static.serve',{'document_root' : settings.MEDIA_ROOT}),
    ) + staticmedia.serve()

