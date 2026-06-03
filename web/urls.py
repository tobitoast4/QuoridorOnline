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
    path("get_random_lobby", views.get_random_lobby),
    path("start_game/<lobby_id>", views.start_game),
    path("game/<lobby_id>", views.game),
    path("get_game_data/<lobby_id>", views.get_game_data),
    path("game_move_player/<lobby_id>", views.game_move_player),
    path("game_place_wall/<lobby_id>", views.game_place_wall),
    path("rename_player", views.rename_player),
    path("change_color", views.change_color),
    path("change_lobby_visibility/<lobby_id>", views.change_lobby_visibility),
    path("change_amount_of_walls_per_player/<lobby_id>", views.change_amount_of_walls_per_player),


    path("dashboard", views.dashboard),
    # path("get_lobby_json", views.get_lobby_json),

    
    path("logout", views.logout_user, name="logout"),
    path("login", views.login, name="login"),
]
