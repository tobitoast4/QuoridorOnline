from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^/?$', views.dashboard, name='dashboard'),
    re_path(r'^get_lobby/(?P<lobby_id>[^/]+)/?$', views.get_lobby, name='get_lobby'),
    re_path(r'^delete_empty_lobbies/?$', views.delete_empty_lobbies, name='delete_empty_lobbies'),
]
