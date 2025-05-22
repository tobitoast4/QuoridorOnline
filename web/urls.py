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
    path("start_game/<lobby_id>", views.start_game),
    path("game/<lobby_id>", views.game),
    path("get_game_data/<lobby_id>", views.get_game_data),
    path("game_move_player/<lobby_id>", views.game_move_player),
    path("game_place_wall/<lobby_id>", views.game_place_wall),

    path("change_lobby_visibility/<lobby_id>", views.change_lobby_visibility),
]
