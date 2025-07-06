from web.errors import QuoridorOnlineGameError
from web.quoridor.game import Game
from web.quoridor import deserialize
import random
from web import utils
import json
import os

from web import models


QUORIDOR_DATA_DIR = os.getenv("QUORIDOR_DATA_DIR", None)
DATA_DIR = None
if QUORIDOR_DATA_DIR is not None:
    if os.path.isdir(QUORIDOR_DATA_DIR):
        DATA_DIR = QUORIDOR_DATA_DIR
if DATA_DIR is None:  # either QUORIDOR_DATA_DIR is not set or its path is not valid
    PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(PROJECT_DIR, "data")  # this is the alternative data path, if QUORIDOR_DATA_DIR is not set

PLAYER_TIME_OUT_TIME = 2  # how long (in sec) is the player allowed to not poll until removed from the lobby

os.makedirs(DATA_DIR, exist_ok=True)


def create_new_lobby(lobby_owner):
    new_lobby = Lobby(lobby_owner)
    new_lobby.write_lobby()
    return new_lobby


def create_lobby_from_json(lobby_as_dict):
    new_lobby = Lobby(None)
    for key in lobby_as_dict:
        if key == "lobby_owner":
            new_lobby.__setattr__(key, deserialize.create_user_from_dict(lobby_as_dict[key]))
        elif key == "players":
            users = []
            for user_as_dict in lobby_as_dict["players"]:
                users.append(deserialize.create_user_from_dict(user_as_dict))
            new_lobby.__setattr__(key, users)
        elif key == "game":
            if lobby_as_dict["game"] is None:
                new_lobby.__setattr__(key, None)
            else:
                game = deserialize.create_game_from_json(lobby_as_dict["game"]["game_data"])
                new_lobby.__setattr__(key, game)
        else:
            new_lobby.__setattr__(key, lobby_as_dict[key])
    return new_lobby


def get_random_public_lobby():
    """Actually gets the first in the list"""
    lobbies = models.Lobby.objects.filter(is_private=False)
    if lobbies.count() >= 1:
        return lobbies.first()  # TODO: Return random
    raise QuoridorOnlineGameError("Could not find any public lobby :(<br/>"
                                  "Try again later or create your own one")

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
    for player in the_lobby.gameplayer_set.iterator():
        if player.game_user == the_user:
            # user is already in lobby, we only need to update the last_seen status
            player.last_seen = utils.get_current_time()
            player.save()
            return
    # if user is not in lobby, add them
    player = models.GamePlayer.objects.create(game_user=the_user, color=the_user.color, lobby=the_lobby)
    player.last_seen = utils.get_current_time()
    player.save()