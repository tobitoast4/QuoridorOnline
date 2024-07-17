import time

from errors import QuoridorOnlineGameError
import quoridor.game_board as game_board
import quoridor.wall as wall
import user
import utils
import threading
import sys, random

STATE_PLACING_PLAYERS = -1
STATE_PLAYING = 0
STATE_PLAYER_DID_WIN = 2


class Game:
    def __init__(self, users: [user.User], amount_walls: int, next_lobby_id: str, skip_user_check=False):
        self.game_board = game_board.GameBoard(users, amount_walls, skip_user_check)
        self.state = STATE_PLACING_PLAYERS
        self.its_this_players_turn = 0
        self.turn = 0
        self.game_data = {
            "next_lobby_id": next_lobby_id,
            "initial_setup": self.game_board.__json__(initial=True),
            "game": []
        }
        self._append_game_data()

    def move_player(self, user_id, new_field_col, new_field_row):
        """Can be used to move a player."""
        if self.get_current_player().user.id != user_id:
            raise QuoridorOnlineGameError("It's not your turn currently")
        player = self._get_player_of_user(user_id)
        new_field = self.game_board.getFieldByColAndRow(new_field_col, new_field_row)
        if self.state == STATE_PLACING_PLAYERS:
            player.move_to_field(new_field, True)
            if self.its_this_players_turn == len(self.game_board.players)-1:  # last player placed his piece initially
                self.state = STATE_PLAYING
        else:
            result = player.move_to_field(new_field)
            if result is not None:
                self.state = STATE_PLAYER_DID_WIN
        self._next_players_turn()

    def place_wall(self, user_id, col_start, row_start, col_end, row_end, skip_user_check=False):
        """Can be used to place a wall."""
        if not skip_user_check:
            if self.get_current_player().user.id != user_id:
                raise QuoridorOnlineGameError("It's not your turn currently")
            if self.get_current_player().amount_walls_left <= 0:
                raise QuoridorOnlineGameError("You do not have any more walls left")
        new_wall = wall.Wall(user_id, col_start, row_start, col_end, row_end, self.game_board)
        # if creating a wall did not throw an exception, decrease the amount of walls the player has
        if not skip_user_check:
            self.get_current_player().amount_walls_left -= 1
            self._next_players_turn()

    def get_amount_of_moves(self):
        amount_of_walls = 0
        # calculate all horizontal walls
        for row_start in range(self.game_board.amount_fields-1):
            row_start += 0.5  # for the horizontal case, row_start and row_end is the same
            for col_start in range(self.game_board.amount_fields-1):
                try:  # if trying to place a wall does not throw an error, we know its a legal move
                    # for the horizontal case, col_end is equal to col_start+1
                    wall.Wall(None, col_start, row_start, col_start+1, row_start, self.game_board, place_wall=False)
                    amount_of_walls += 1
                except QuoridorOnlineGameError as e:
                    pass
        # calculate all vertical walls
        for col_start in range(self.game_board.amount_fields-1):
            col_start += 0.5  # for the horizontal case, row_start and row_end is the same
            for row_start in range(self.game_board.amount_fields-1):
                try:  # if trying to place a wall does not throw an error, we know its a legal move
                    # for the horizontal case, col_end is equal to col_start+1
                    wall.Wall(None, col_start, row_start, col_start, row_start+1, self.game_board, place_wall=False)
                    amount_of_walls += 1
                except QuoridorOnlineGameError as e:
                    pass
        return amount_of_walls

    def get_game_score(self):
        walls_0 = self.get_current_player().amount_walls_left
        way_0 = self.get_length_of_shortest_path_to_win(self.get_current_player())
        walls_e = self._get_next_player().amount_walls_left
        way_e = self.get_length_of_shortest_path_to_win(self._get_next_player())
        return walls_0 - way_0 - walls_e + way_e

    def get_length_of_shortest_path_to_win(self, player):
        path_finder = PathFinderDijkstra(player.field, self.game_board.fields)
        shortest_path = path_finder.get_shortest_path_to_win(player.win_option_fields)
        return shortest_path

    def get_current_player(self):
        return self.game_board.players[self.its_this_players_turn]

    def _get_next_player(self):
        next_turn = self.its_this_players_turn = 1
        if next_turn >= len(self.game_board.players):
            next_turn = 0
        return self.game_board.players[next_turn]

    def _next_players_turn(self):
        self.its_this_players_turn += 1
        if self.its_this_players_turn >= len(self.game_board.players):
            self.its_this_players_turn = 0
            self.turn += 1
        self._append_game_data()

    def _get_player_of_user(self, user_id):
        for player in self.game_board.players:
            if player.user.id == user_id:
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


class PathFinder:
    """Class that finds the length of the shortest way to winning.

       # TODO: PROBLEM THAT COULD OCCUR:
       Same problem as for PathChecker
    """
    def __init__(self):
        self.path_length = sys.maxsize
        self.fields_visited = []
        self.running_threads = []

    def start_find_length_of_shortest_path_to_win(self, field, fields_to_win):
        self.find_length_of_shortest_path_to_win(field, fields_to_win, 0)

    def find_length_of_shortest_path_to_win(self, field, fields_to_win, current_path_length):
        # TODO: CURRENTLY THIS DOES NOT ALWAYS RETURN THE SHORTEST WAY!!!
        # But we accept this currently because is is a fastly running algorithm
        if field in self.fields_visited:
            return
        if field in fields_to_win:
            self.path_length = min(self.path_length, current_path_length)
            return
        self.fields_visited.append(field)
        neighbour_fields = field.neighbour_fields
        for neighbour_field in neighbour_fields:
            new_thread = threading.Thread(
                target=self.find_length_of_shortest_path_to_win,
                args=(neighbour_field, fields_to_win, current_path_length+1)
            )
            self.running_threads.append(new_thread)
            new_thread.start()


class PathFinder2:
    """Class that finds the length of the shortest way to winning.

       # TODO: PROBLEM THAT COULD OCCUR:
       Same problem as for PathChecker
    """
    def __init__(self):
        self.path_length = sys.maxsize
        self.running_threads = []

    def start_find_length_of_shortest_path_to_win(self, field, fields_to_win):
        self.find_length_of_shortest_path_to_win(field, fields_to_win, 0)

    def find_length_of_shortest_path_to_win(self, field, fields_to_win, current_path_length):
        # TODO: CURRENTLY THIS DOES NOT ALWAYS RETURN THE SHORTEST WAY!!!
        # But we accept this currently because is is a fastly running algorithm
        if current_path_length > 32:
            return
        if field in fields_to_win:
            self.path_length = min(self.path_length, current_path_length)
            return
        neighbour_fields = field.neighbour_fields
        for neighbour_field in neighbour_fields:
            new_thread = threading.Thread(
                target=self.find_length_of_shortest_path_to_win,
                args=(neighbour_field, fields_to_win, current_path_length+1)
            )
            self.running_threads.append(new_thread)
            new_thread.start()


class PathFinderDijkstra:
    """Class that finds the length of the shortest way to winning.
    """
    def __init__(self, start_field, other_fields):
        self.start_field = start_field
        self.other_fields = other_fields
        self.fields_visited = []
        self.cost_table = {}

        for field in other_fields:
            if field == start_field:
                self.add_or_update_node_to_cost_table(field, 0, field)
            else:
                self.add_or_update_node_to_cost_table(field, sys.maxsize, None)
        self.calculate_path_lengths(start_field)

    def calculate_path_lengths(self, field):
        neighbour_fields = field.neighbour_fields
        next_field = None
        for neighbour_field in neighbour_fields:
            current_path_length_to_field = self.cost_table[field]["path_length"]
            for neighbour_neighbour_field in neighbour_field.neighbour_fields:
                current_path_length_to_neighbour_field = self.cost_table[neighbour_neighbour_field]["path_length"]
                current_path_length_to_field = min(current_path_length_to_field, current_path_length_to_neighbour_field)
            if neighbour_field not in self.fields_visited:
                current_path_length_to_neighbour_field = self.cost_table[neighbour_field]["path_length"]
                self.add_or_update_node_to_cost_table(neighbour_field,
                     min(current_path_length_to_neighbour_field, current_path_length_to_field+1), field)
                next_field = neighbour_field
        if next_field is None:
            next_field = self.get_unvisited_field_with_shortest_path()
        self.fields_visited.append(field)
        if len(self.fields_visited) < len(self.other_fields):
            self.calculate_path_lengths(next_field)

    def add_or_update_node_to_cost_table(self, field, path_length, predecessor):
        self.cost_table[field] = {
            "path_length": path_length, "predecessor": predecessor
        }

    def get_unvisited_field_with_shortest_path(self):
        shortest_path = sys.maxsize
        the_field_with_shortest_path = None
        for field in self.cost_table:
            if field not in self.fields_visited:
                fields_path_length = self.cost_table[field]["path_length"]
                if fields_path_length <= shortest_path:
                    shortest_path = fields_path_length
                    the_field_with_shortest_path = field
        return the_field_with_shortest_path

    def get_shortest_path_to_win(self, fields_to_win):
        path_length = sys.maxsize
        for field in fields_to_win:
            current_path_length_to_field = self.cost_table[field]["path_length"]
            path_length = min(path_length, current_path_length_to_field)
        return path_length
