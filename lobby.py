from threading import Thread
import time
import utils
import json

PLAYER_TIME_OUT_TIME = 0.5  # how long (in sec) is the player allowed to not poll until removed from the lobby

LOBBY_STATE_IN_LOBBY = 0
LOBBY_STATE_IN_GAME = 1


class LobbyManager:
    def __init__(self):
        self.lobbies = []
        self.start_check_players_last_seen_time_task()

    def create_new_lobby(self,):
        new_lobby = Lobby()
        self.lobbies.append(new_lobby)
        return new_lobby

    def get_lobby(self, lobby_id):
        for current_lobby in self.lobbies:
            if current_lobby.lobby_id == lobby_id:
                return current_lobby
        return None

    def add_player_to_lobby(self, lobby_id, user):
        the_lobby = self.get_lobby(lobby_id)
        for p in range(len(the_lobby.players)):
            player = the_lobby.players[p]
            if player.id == user.id:
                # user is already in lobby, we only need to update the last_seen status
                the_lobby.players_last_seen[p] = utils.get_current_time()
                return
        # if user is not in lobby, add them
        the_lobby.players.append(user)
        the_lobby.players_last_seen.append(utils.get_current_time())

    def start_check_players_last_seen_time_task(self):
        thread = Thread(target=self.check_players_last_seen_time)
        thread.start()

    def check_players_last_seen_time(self):
        while True:
            for lobby in self.lobbies:
                for p in range(len(lobby.players)):
                    player_last_seen_time = lobby.players_last_seen[p]
                    if utils.get_current_time() - player_last_seen_time > PLAYER_TIME_OUT_TIME:
                        del lobby.players[p]
                        del lobby.players_last_seen[p]
            time.sleep(0.6)


class Lobby:
    def __init__(self):
        self.lobby_id = utils.get_new_uuid()
        self.time_created = utils.get_current_time()
        self.players = []
        self.players_last_seen = []  # this list contains the timestamp when the player was seen at last
                                     # the order corresponds to the order of self.players
        self.state = LOBBY_STATE_IN_LOBBY

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)


