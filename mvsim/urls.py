import django.views.static
import os.path

from django.urls import include, path, re_path
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
from django_cas_ng import views as cas_views


admin.autodiscover()

site_media_root = os.path.join(os.path.dirname(__file__), "../media")
doc_root = os.path.join(os.path.dirname(__file__), "../docs", "_build", "html")

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('cas/login', cas_views.LoginView.as_view(),
         name='cas_ng_login'),
    path('cas/logout', cas_views.LogoutView.as_view(),
         name='cas_ng_logout'),
    path('registration/',
         include('django_registration.backends.activation.urls')),
    path('registration/', include('django.contrib.auth.urls')),
    path('impersonate/', include('impersonate.urls')),
    path('', home, name='home'),
    re_path(r'^section/(?P<section_id>\d+)/games/$', games_index,
            name='games_index'),
    re_path(r'^section/(?P<section_id>\d+)/games/new/$', games_index,
            name='new_game'),

    re_path(r'^games/(?P<game_id>\d+)/$', show_turn, name='game_show'),
    re_path(r'^games/(?P<game_id>\d+)/delete/$',
            delete_game, name='game_delete'),
    re_path(r'^games/(?P<game_id>\d+)/edit/$', edit_game, name='game_edit'),
    re_path(r'^games/(?P<game_id>\d+)/turn/$', submit_turn),
    re_path(r'^games/(?P<game_id>\d+)/game_over/$',
            game_over, name='game_over'),

    re_path(r'^games/(?P<game_id>\d+)/history/$',
            history, name='game_history'),

    re_path(r'^games/(?P<game_id>\d+)/turn/(?P<turn_number>\d+)/$',
            view_turn_history, name='game_turn_history'),

    re_path(r'^games/(?P<game_id>\d+)/graph/$', graph, name='game_graph'),
    re_path(r'^games/(?P<game_id>\d+)/graph_svg/$',
            graph_svg, name='game_graph_svg'),
    re_path(r'^games/(?P<game_id>\d+)/graph_download/$', graph_download,
            name='game_graph_download'),

    re_path(r'^state/(?P<state_id>\d+)/$', view_state, name="view_state"),
    re_path(r'^state/(?P<state_id>\d+)/clone/$',
            clone_state, name="clone_state"),
    re_path(r'^state/(?P<state_id>\d+)/edit/$', edit_state, name="edit_state"),

    path('course_sections/', admin_course_sections,
         name="admin_course_sections"),
    re_path(r'^course_sections/(?P<section_id>\d+)/$', admin_course_section,
            name="admin_course_section"),
    re_path(r'^course_sections/(?P<section_id>\d+)/game_stats/$',
            course_section_game_stats, name="course_section_game_stats"),
    re_path(r'^course_sections/(?P<section_id>\d+)/associate_state/$',
            associate_state, name="associate_state"),

    path('admin/', admin.site.urls),
    path('smoketest/', include('smoketest.urls')),
    path('stats/', TemplateView.as_view(template_name="stats.html")),
    re_path(r'^static/(?P<path>.*)$', django.views.static.serve,
            {'document_root': site_media_root}),
    re_path(r'^site_media/(?P<path>.*)$', django.views.static.serve,
            {'document_root': site_media_root}),
    re_path(r'^uploads/(?P<path>.*)$', django.views.static.serve,
            {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^docs/(?P<path>.*)$', django.views.static.serve,
            {'document_root': doc_root}),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
