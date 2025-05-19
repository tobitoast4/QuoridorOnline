from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path("local", views.local),
    path("how-to-play", views.how_to_play),
    path("about", views.about),
    path("privacy_policy", views.privacy_policy),
    path("lobby", views.lobby),
    path("lobby/<lobby_id>", views.lobby),
    path("get_lobby/<lobby_id>", views.get_lobby),
]
