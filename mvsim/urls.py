from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.conf import settings
from django.views.generic.simple import direct_to_template
import os.path
admin.autodiscover()
import staticmedia

site_media_root = os.path.join(os.path.dirname(__file__), "../media")
doc_root = os.path.join(os.path.dirname(__file__), "../docs", "_build", "html")

redirect_after_logout = getattr(settings, 'LOGOUT_REDIRECT_URL', None)

auth_urls = (r'^accounts/', include('django.contrib.auth.urls'))

logout_page = (r'^accounts/logout/$',
               'django.contrib.auth.views.logout',
               {'next_page': redirect_after_logout})

if hasattr(settings, 'WIND_BASE'):
    auth_urls = (r'^accounts/', include('djangowind.urls'))
    logout_page = (r'^accounts/logout/$',
                   'djangowind.views.logout',
                   {'next_page': redirect_after_logout})

urlpatterns = patterns(
    '',
    logout_page,
    auth_urls,
    (r'^registration/', include('registration.urls')),
    url(r'^impersonate/', include('impersonate.urls')),
    url(r'^$', 'mvsim.main.views.home', name='home'),
    url(r'^games/$', 'mvsim.main.views.games_index', name='games_index'),
    url(r'^games/new/$', 'mvsim.main.views.games_index', name='new_game'),

    url(r'^games/(?P<game_id>\d+)/$', 'mvsim.main.views.show_turn',
        name='game_show'),
    url(r'^games/(?P<game_id>\d+)/delete/$', 'mvsim.main.views.delete_game',
        name='game_delete'),
    url(r'^games/(?P<game_id>\d+)/edit/$', 'mvsim.main.views.edit_game',
        name='game_edit'),
    url(r'^games/(?P<game_id>\d+)/turn/$', 'mvsim.main.views.submit_turn'),
    url(r'^games/(?P<game_id>\d+)/game_over/$', 'mvsim.main.views.game_over',
        name='game_over'),

    url(r'^games/(?P<game_id>\d+)/history/$', 'mvsim.main.views.history',
        name='game_history'),

    url(r'^games/(?P<game_id>\d+)/turn/(?P<turn_number>\d+)/$',
        'mvsim.main.views.view_turn_history', name='game_turn_history'),

    url(r'^games/(?P<game_id>\d+)/graph/$', 'mvsim.graph.views.graph',
        name='game_graph'),
    url(r'^games/(?P<game_id>\d+)/graph_svg/$', 'mvsim.graph.views.graph_svg',
        name='game_graph_svg'),
    url(r'^games/(?P<game_id>\d+)/graph_download/$',
        'mvsim.graph.views.graph_download',
        name='game_graph_download'),

    url(r'^state/(?P<state_id>\d+)/$', 'mvsim.main.views.view_state',
        name="view_state"),
    url(r'^state/(?P<state_id>\d+)/clone/$', 'mvsim.main.views.clone_state',
        name="clone_state"),
    url(r'^state/(?P<state_id>\d+)/edit/$',
        'mvsim.main.views.edit_state',
        name="edit_state"),


    url(r'^course_sections/$',
        'mvsim.main.views.admin_course_sections',
        name="admin_course_sections"),
    url(r'^course_sections/(?P<section_id>\d+)/$',
        'mvsim.main.views.admin_course_section',
        name="admin_course_section"),
    url(r'^course_sections/(?P<section_id>\d+)/game_stats/$',
        'mvsim.main.views.course_section_game_stats',
        name="course_section_game_stats"),
    url(r'^course_sections/(?P<section_id>\d+)/associate_state/$',
        'mvsim.main.views.associate_state', name="associate_state"),

    (r'^admin/', include(admin.site.urls)),
    (r'^munin/', include('munin.urls')),
    (r'^smoketest/', include('smoketest.urls')),
    ('^stats/', direct_to_template, {'template': 'stats.html'}),
    (r'^static/(?P<path>.*)$',
     'django.views.static.serve',
     {'document_root': site_media_root}),
    (r'^site_media/(?P<path>.*)$',
     'django.views.static.serve',
     {'document_root': site_media_root}),
    (r'^uploads/(?P<path>.*)$',
     'django.views.static.serve',
     {'document_root': settings.MEDIA_ROOT}),
    (r'^docs/(?P<path>.*)$',
     'django.views.static.serve',
     {'document_root': doc_root}),
) + staticmedia.serve()
