from collections import deque

from web.errors import QuoridorOnlineGameError
import web.quoridor.game_board as game_board
import web.quoridor.wall as wall
from web import utils

STATE_PLACING_PLAYERS = -1
STATE_PLAYING = 0
STATE_PLAYER_DID_WIN = 2  # TODO: Remove this state


class Game:
    def __init__(self, gameplayers, amount_walls: int, next_lobby_id: str, skip_user_check=False):
        self.game_board = game_board.GameBoard(gameplayers, amount_walls, skip_user_check)
        self.state = STATE_PLACING_PLAYERS
        self.its_this_players_turn = 0
        self.turn = 0
        self.game_data = {
            "next_lobby_id": next_lobby_id,
            "initial_setup": self.game_board.__json__(initial=True),
            "game": []
        }
        self._append_game_data()

    def surrender(self, user_id, lobby):
        """Can be used to surrender from the game."""
        if str(self.get_current_player().gameplayer.game_user.id) != user_id:
            raise QuoridorOnlineGameError("It's not your turn currently")
        player = self._get_player_of_user(user_id)
        # if player.gameplayer.has_surrendered:
        #     raise QuoridorOnlineGameError("You have surrendered already")
        player.remove_from_field()  # a surrendered player should not block other players
        player.gameplayer.has_surrendered = True
        player.gameplayer.save()
        # List of players who have not surrendered yet
        not_surrendered_players = [p for p in self.game_board.players if not p.gameplayer.has_surrendered]
        if len(not_surrendered_players) == 1:
            self.state = STATE_PLAYER_DID_WIN
            lobby.winner = not_surrendered_players[0].gameplayer
            lobby.save()
        self._next_players_turn()

    def move_player(self, user_id, lobby, new_field_col, new_field_row, set_winner=True):
        """Can be used to move a player."""
        if str(self.get_current_player().gameplayer.game_user.id) != str(user_id):
            raise QuoridorOnlineGameError("It's not your turn currently")
        player = self._get_player_of_user(user_id)
        # if player.gameplayer.has_surrendered:
        #     raise QuoridorOnlineGameError("You have surrendered already")
        new_field = self.game_board.getFieldByColAndRow(new_field_col, new_field_row)
        if self.state == STATE_PLACING_PLAYERS:
            player.move_to_field(new_field, True)
            if self.its_this_players_turn == len(self.game_board.players)-1:  # last player placed his piece initially
                self.state = STATE_PLAYING
        else:
            result = player.move_to_field(new_field)
            if result is not None and set_winner:
                self.state = STATE_PLAYER_DID_WIN
                lobby.winner = player.gameplayer
                lobby.save()
        self._next_players_turn()

    def place_wall(self, user_id, col_start, row_start, col_end, row_end, skip_user_check=False):
        """Can be used to place a wall."""
        if not skip_user_check:
            if str(self.get_current_player().gameplayer.game_user.id) != str(user_id):
                raise QuoridorOnlineGameError("It's not your turn currently")
            if self.get_current_player().amount_walls_left <= 0:
                raise QuoridorOnlineGameError("You do not have any more walls left")
        player = self._get_player_of_user(user_id)
        # if player.gameplayer.has_surrendered:
        #     raise QuoridorOnlineGameError("You have surrendered already")
        new_wall = wall.Wall(user_id, col_start, row_start, col_end, row_end, self.game_board)
        self.game_board.walls.append(new_wall)
        if not self.check_if_path_to_win_exists_for_all_players():
            new_wall.remove_wall_from_field()
            raise QuoridorOnlineGameError("Wall could not be placed as it would block a player from winning")
        # if creating a wall did not throw an exception, decrease the amount of walls the player has
        if not skip_user_check:
            self.get_current_player().amount_walls_left -= 1
            self._next_players_turn()

    def get_current_player(self):
        player = self.game_board.players[self.its_this_players_turn]
        # if player.gameplayer.has_surrendered:
        #     self._next_players_turn()
        #     return self.get_current_player()
        return player
    
    def get_other_players(self):
        current_player = self.get_current_player()
        other_players = []
        for p in self.game_board.players:
            if p != current_player:
                other_players.append(p)
        return other_players

    def _next_players_turn(self):
        self.its_this_players_turn += 1
        if self.its_this_players_turn >= len(self.game_board.players):
            self.its_this_players_turn = 0
            self.turn += 1
        player = self.game_board.players[self.its_this_players_turn]
        if player.gameplayer.has_surrendered:
            self._next_players_turn()  # skip this player, as he has surrendered
        self._append_game_data()

    def _get_player_of_user(self, user_id):
        for player in self.game_board.players:
            if str(player.gameplayer.game_user.id) == str(user_id):
                return player
        return None

    def _append_game_data(self):
        self.game_data["game"].append({
            "state": self.state,
            "its_this_players_turn": self.its_this_players_turn,
            "turn": self.turn,
            "time": utils.get_current_time(),
            "game_board": self.game_board.__json__(),
        })

    def check_if_path_to_win_exists_for_all_players(self):
        for player in self.game_board.players:
            if not player.gameplayer.has_surrendered:
                distance = self.shortest_distance(player)
                if distance < 0:  # after shortest_distance() this should be set
                    return False              # to true if there is a path
        return True

    def shortest_distance(self, player):
        fields_to_win = player.win_option_fields
        start = player.field 

        queue = deque([(start, 0)])
        visited = {start}

        while queue:
            field, distance = queue.popleft()
            if field in fields_to_win:
                return distance
            for neighbor in field.neighbour_fields:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, distance + 1))
        # no path
        return -1
    
    def fields_of_path_to_win(self, field, win_option_fields):
        """Return the shortest path (list of Field) from `field` to the
        nearest field in `win_option_fields` using BFS. Returns `None` if no
        path exists.
        """
        goals = set(win_option_fields)
        start = field

        queue = deque([start])
        prev = {start: None}

        while queue:
            cur = queue.popleft()
            if cur in goals:
                # reconstruct path from start -> cur
                path = []
                node = cur
                while node is not None:
                    path.append(node)
                    node = prev[node]
                path.reverse()
                return path
            for neighbor in cur.neighbour_fields:
                if neighbor not in prev:
                    prev[neighbor] = cur
                    queue.append(neighbor)
        return None
    