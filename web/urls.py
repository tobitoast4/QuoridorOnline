from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    re_path(r'^ads.txt', views.ads_txt, name='ads_txt'),
    re_path(r'^local/?$', views.local, name='local'),
    re_path(r'^how-to-play/?$', views.how_to_play, name='how_to_play'),
    re_path(r'^about/?$', views.about, name='about'),
    re_path(r'^privacy_policy/?$', views.privacy_policy, name='privacy_policy'),
    re_path(r'^lobby/?$', views.lobby, name='lobby'),
    re_path(r'^lobby/(?P<lobby_id>[^/]+)/?$', views.lobby, name='lobby_detail'),
    re_path(r'^get_random_lobby/?$', views.get_random_lobby, name='get_random_lobby'),
    re_path(r'^game/(?P<lobby_id>[^/]+)/?$', views.game, name='game'),
    re_path(r'^get_game_data/(?P<lobby_id>[^/]+)/?$', views.get_game_data, name='get_game_data'),
    re_path(r'^rename_player/?$', views.rename_player, name='rename_player'),
    re_path(r'^change_color/?$', views.change_color, name='change_color'),
    re_path(r'^logout/?$', views.logout_user, name='logout'),
    re_path(r'^account/?$', views.account, name='account'),
    re_path(r'^register/?$', views.register, name='register'),
    re_path(r'^login/?$', views.login, name='login'),
]
