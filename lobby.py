import user
from errors import QuoridorOnlineGameError
from quoridor.game import Game
from quoridor import deserialize
import random
import utils
import json
import os
from filelock import FileLock


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
PLAYER_TIME_OUT_TIME = 2  # how long (in sec) is the player allowed to not poll until removed from the lobby


os.makedirs(DATA_DIR, exist_ok=True)


def create_new_lobby(lobby_owner):
    new_lobby = Lobby(lobby_owner)
    new_lobby.write_lobby()
    return new_lobby


def get_lobby(lobby_id):
    file_location = os.path.join(DATA_DIR, f"{lobby_id}.json")
    if os.path.isfile(file_location):
        with open(file_location) as f:
            try:
                lobby_as_dict = json.load(f)
            except:
                pass
            return create_lobby_from_json(lobby_as_dict)
    return None


def get_random_public_lobby():
    """Actually gets the first in the list"""
    for file in os.listdir(DATA_DIR):
        file_location = os.path.join(DATA_DIR, file)
        if os.path.isfile(file_location):
            with open(file_location) as f:
                try:
                    lobby_as_dict = json.load(f)
                except:
                    continue
                if lobby_as_dict["is_private"] == False and lobby_as_dict["game"] is None:
                    return create_lobby_from_json(lobby_as_dict)
    raise QuoridorOnlineGameError("Could not find any public lobby :(<br/>"
                                  "Try again later or create your own one")


def add_player_to_lobby(lobby_id, the_user):
    the_lobby = get_lobby(lobby_id)
    for p in range(len(the_lobby.players)):
        player = the_lobby.players[p]
        if player.id == the_user.id:
            # user is already in lobby, we only need to update the last_seen status
            the_lobby.players_last_seen[p] = utils.get_current_time()
            the_lobby.write_lobby()
            return
    # if user is not in lobby, add them
    the_lobby.players.append(the_user)
    the_lobby.players_last_seen.append(utils.get_current_time())
    the_lobby.write_lobby()


def update_player_name_in_lobby(lobby_id, user_id, new_user_name):
    the_lobby = get_lobby(lobby_id)
    for p in range(len(the_lobby.players)):
        player = the_lobby.players[p]
        if player.id == user_id:
            player.name = new_user_name
            break
    the_lobby.write_lobby()


def check_players_last_seen_time(lobby_id):
    try:
        the_lobby = get_lobby(lobby_id)
        is_lobby_owner_still_in_lobby = False
        for p in reversed(range(len(the_lobby.players))):
            if the_lobby.lobby_owner.id == the_lobby.players[p].id:
                is_lobby_owner_still_in_lobby = True
            player_last_seen_time = the_lobby.players_last_seen[p]
            if utils.get_current_time() - player_last_seen_time > PLAYER_TIME_OUT_TIME:
                del the_lobby.players[p]
                del the_lobby.players_last_seen[p]
        if not is_lobby_owner_still_in_lobby:
            if len(the_lobby.players) > 0:
                the_lobby.lobby_owner = the_lobby.players[0]
        the_lobby.write_lobby()
    except Exception as e:
        print(e)


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
        next_lobby = create_new_lobby(self.lobby_owner)  # creates a new lobby which will be used if players
                                                         # click 'Play again' after the current game
        self.game = Game(self.players, self.amount_of_walls_per_player, next_lobby.lobby_id)

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

    def write_lobby(self):
        lobby_id = self.lobby_id
        file_path = os.path.join(DATA_DIR, f"{lobby_id}.json")
        with FileLock(f"{file_path}.lock"):
            with open(file_path, "w") as f:
                json.dump(self.to_json(), f, indent=4)
