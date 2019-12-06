import django.views.static
import os.path

from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.views.generic import TemplateView
from mvsim.main.views import (
    home, history, view_turn_history, show_turn, delete_game, edit_game,
    submit_turn, game_over, games_index, view_state, clone_state,
    edit_state, admin_course_sections, admin_course_section,
    course_section_game_stats, associate_state,
)
from mvsim.graph.views import (
    graph, graph_svg, graph_download,
)


admin.autodiscover()

site_media_root = os.path.join(os.path.dirname(__file__), "../media")
doc_root = os.path.join(os.path.dirname(__file__), "../docs", "_build", "html")

auth_urls = url(r'^accounts/', include('django.contrib.auth.urls'))
if hasattr(settings, 'CAS_BASE'):
    auth_urls = url(r'^accounts/', include('djangowind.urls'))

urlpatterns = [
    auth_urls,
    url(r'^registration/', include('registration.urls')),
    url(r'^impersonate/', include('impersonate.urls')),
    url(r'^$', home, name='home'),
    url(r'^section/(?P<section_id>\d+)/games/$', games_index,
        name='games_index'),
    url(r'^section/(?P<section_id>\d+)/games/new/$', games_index,
        name='new_game'),

    url(r'^games/(?P<game_id>\d+)/$', show_turn, name='game_show'),
    url(r'^games/(?P<game_id>\d+)/delete/$', delete_game, name='game_delete'),
    url(r'^games/(?P<game_id>\d+)/edit/$', edit_game, name='game_edit'),
    url(r'^games/(?P<game_id>\d+)/turn/$', submit_turn),
    url(r'^games/(?P<game_id>\d+)/game_over/$', game_over, name='game_over'),

    url(r'^games/(?P<game_id>\d+)/history/$', history, name='game_history'),

    url(r'^games/(?P<game_id>\d+)/turn/(?P<turn_number>\d+)/$',
        view_turn_history, name='game_turn_history'),

    url(r'^games/(?P<game_id>\d+)/graph/$', graph, name='game_graph'),
    url(r'^games/(?P<game_id>\d+)/graph_svg/$',
        graph_svg, name='game_graph_svg'),
    url(r'^games/(?P<game_id>\d+)/graph_download/$', graph_download,
        name='game_graph_download'),

    url(r'^state/(?P<state_id>\d+)/$', view_state, name="view_state"),
    url(r'^state/(?P<state_id>\d+)/clone/$', clone_state, name="clone_state"),
    url(r'^state/(?P<state_id>\d+)/edit/$', edit_state, name="edit_state"),

    url(r'^course_sections/$', admin_course_sections,
        name="admin_course_sections"),
    url(r'^course_sections/(?P<section_id>\d+)/$', admin_course_section,
        name="admin_course_section"),
    url(r'^course_sections/(?P<section_id>\d+)/game_stats/$',
        course_section_game_stats, name="course_section_game_stats"),
    url(r'^course_sections/(?P<section_id>\d+)/associate_state/$',
        associate_state, name="associate_state"),

    url(r'^admin/', admin.site.urls),
    url(r'^smoketest/', include('smoketest.urls')),
    url(r'^stats/$', TemplateView.as_view(template_name="stats.html")),
    url(r'^stats/auth/$', TemplateView.as_view(
        template_name="auth_stats.html")),
    url(r'^static/(?P<path>.*)$', django.views.static.serve,
        {'document_root': site_media_root}),
    url(r'^site_media/(?P<path>.*)$', django.views.static.serve,
        {'document_root': site_media_root}),
    url(r'^uploads/(?P<path>.*)$', django.views.static.serve,
        {'document_root': settings.MEDIA_ROOT}),
    url(r'^docs/(?P<path>.*)$', django.views.static.serve,
        {'document_root': doc_root}),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
