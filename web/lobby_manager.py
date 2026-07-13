from django.db.models import Count

from web.errors import QuoridorOnlineGameError
from web.quoridor.game import Game
from web.quoridor import deserialize
import random
from web import utils
import json
import os

from web import models

PLAYER_TIME_OUT_TIME = 2  # how long (in sec) is the player allowed to not poll until removed from the lobby


def get_random_public_lobby():
    """Actually gets the first in the list"""
    lobbys = (
    models.Lobby.objects
        .filter(is_private=False, game=None)
        .annotate(player_count=Count("gameplayer"))
        .filter(player_count__gte=0)
    )
    if lobbys.count() >= 1:
        return lobbys.order_by("?").first()  # .order_by("?") returns random
    else:
        return None

def check_players_last_seen_time(lobby):  # TODO: Remove
    players_to_delete = []
    for player in lobby.gameplayer_set.iterator():
        if utils.get_current_time() - player.last_seen > PLAYER_TIME_OUT_TIME:
            players_to_delete.append(player)
    for player in players_to_delete:
        if lobby.owner == player:
            lobby.owner = None
        player.delete()
    if lobby.owner == None and lobby.gameplayer_set.count() > 0:
        lobby.owner = lobby.gameplayer_set.first()
    lobby.save()

def add_player_to_lobby(the_lobby, the_user):
    # if user is not in lobby, add them
    player = models.GamePlayer.objects.filter(game_user=the_user, lobby=the_lobby).first()
    if not player:
        player = models.GamePlayer.objects.create(game_user=the_user, color=the_user.color, lobby=the_lobby)
        player.last_seen = utils.get_current_time()
        player.save()
        if the_lobby.owner is None:
            the_lobby.owner = player
            the_lobby.save()

def add_ai_player_to_lobby(the_lobby):
    user = models.GameUser.objects.create(username=utils.get_player_guest_name(), color=utils.get_random_color())
    player = models.GamePlayer.objects.create(game_user=user, lobby=the_lobby, is_artificial=True)
    player.save()
    if the_lobby.owner is None:
        the_lobby.owner = player
        the_lobby.save()

def remove_player_from_lobby(the_lobby, the_user):
    # if user is in lobby, remove them
    player = models.GamePlayer.objects.filter(game_user=the_user, lobby=the_lobby).first()
    if player:
        player.delete()