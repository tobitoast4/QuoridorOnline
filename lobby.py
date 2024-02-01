import user
from errors import QuoridorOnlineGameError
from quoridor.game import Game
from quoridor import deserialize
import random
import utils
import json

PLAYER_TIME_OUT_TIME = 1  # how long (in sec) is the player allowed to not poll until removed from the lobby


class LobbyManager:
    def __init__(self):
        self.lobbies = []

    def create_new_lobby(self, lobby_owner):
        new_lobby = Lobby(lobby_owner)
        self.lobbies.append(new_lobby)
        return new_lobby

    def get_lobby(self, lobby_id):
        for current_lobby in self.lobbies:
            if current_lobby.lobby_id == lobby_id:
                return current_lobby
        return None

    def get_random_public_lobby(self):
        lobby_list_copy = self.lobbies.copy()
        lobby_list_copy = [lobby for lobby in lobby_list_copy if not lobby.is_private and lobby.game is None]
        if len(lobby_list_copy) <= 0:
            raise QuoridorOnlineGameError("Could not find any public lobby :(<br/>"
                                          "Try again later or create your own one")
        else:
            return lobby_list_copy[random.randint(0, len(lobby_list_copy)-1)]

    def add_player_to_lobby(self, lobby_id, the_user):
        the_lobby = self.get_lobby(lobby_id)
        for p in range(len(the_lobby.players)):
            player = the_lobby.players[p]
            if player.id == the_user.id:
                # user is already in lobby, we only need to update the last_seen status
                the_lobby.players_last_seen[p] = utils.get_current_time()
                return
        # if user is not in lobby, add them
        the_lobby.players.append(the_user)
        the_lobby.players_last_seen.append(utils.get_current_time())

    def update_player_name_in_lobby(self, lobby_id, user_id, new_user_name):
        the_lobby = self.get_lobby(lobby_id)
        for p in range(len(the_lobby.players)):
            player = the_lobby.players[p]
            if player.id == user_id:
                player.name = new_user_name
                return

    def check_players_last_seen_time(self):
        try:
            for lobby in self.lobbies:
                is_lobby_owner_still_in_lobby = False
                for p in reversed(range(len(lobby.players))):
                    if lobby.lobby_owner.id == lobby.players[p].id:
                        is_lobby_owner_still_in_lobby = True
                    player_last_seen_time = lobby.players_last_seen[p]
                    if utils.get_current_time() - player_last_seen_time > PLAYER_TIME_OUT_TIME:
                        del lobby.players[p]
                        del lobby.players_last_seen[p]
                if not is_lobby_owner_still_in_lobby:
                    if len(lobby.players) > 0:
                        lobby.lobby_owner = lobby.players[0]
        except Exception as e:
            print(e)


class Lobby:
    def __init__(self, lobby_owner):
        self.lobby_id = utils.get_new_uuid()
        self.is_private = True
        self.time_created = utils.get_current_time()
        self.lobby_owner = lobby_owner
        self.amount_of_walls_per_player = 10
        self.players = []  # this is of type [user.User]
        self.players_last_seen = []  # this list contains the timestamp when the player was seen at last
                                     # the order corresponds to the order of self.players
        self.game = None

    def start_game(self):
        random.shuffle(self.players)
        self.game = Game(self.players, self.amount_of_walls_per_player)

    def change_visibility(self):
        if self.is_private:
            self.is_private = False
        else:
            self.is_private = True

    def change_amount_of_walls_of_players(self, new_amount: int):
        if new_amount <= 0:
            raise QuoridorOnlineGameError("The amount of walls per player can not be lower than 1")
        elif new_amount > 99:
            raise QuoridorOnlineGameError("The amount of walls per player can not be higher than 99")
        else:
            self.amount_of_walls_per_player = new_amount

    def to_json(self):
        self_as_dict = vars(self).copy()
        self_as_dict["lobby_owner"] = self.lobby_owner.__json__()
        self_as_dict["players"] = [u.__json__() for u in self.players]
        if self.game is not None:
            self_as_dict["game"] = {
                "game_data": self.game.game_data
            }
        return self_as_dict


def create_lobby_from_json(lobby_as_dict):
    game, users = deserialize.create_game_from_json(lobby_as_dict["game"]["game_data"])
    new_lobby = Lobby(None)
    for key in lobby_as_dict:
        if key == "lobby_owner":
            new_lobby.__setattr__(key, deserialize.create_user_from_dict(lobby_as_dict[key]))
        elif key == "players":
            new_lobby.__setattr__(key, users)
        elif key == "game":
            new_lobby.__setattr__(key, game)
        else:
            new_lobby.__setattr__(key, lobby_as_dict[key])
