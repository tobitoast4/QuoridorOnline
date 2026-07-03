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
    lobbies = models.Lobby.objects.filter(is_private=False, game=None)
    if lobbies.count() >= 1:
        return lobbies.first()  # TODO: Return random
    else:
        return None

def check_players_last_seen_time(lobby):
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

def remove_player_from_lobby(the_lobby, the_user):
    # if user is in lobby, remove them
    player = models.GamePlayer.objects.filter(game_user=the_user, lobby=the_lobby).first()
    if player:
        player.delete()