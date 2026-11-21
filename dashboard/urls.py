from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    re_path(r'^lobbies/?$', views.lobbies, name='lobbies'),
    re_path(r'^delete_empty_lobbies/?$', views.delete_empty_lobbies, name='delete_empty_lobbies'),
]
