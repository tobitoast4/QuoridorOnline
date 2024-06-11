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
        path_checker = PathChecker()
        if not path_checker.check_if_path_to_win_exists_for_all_players(self.game_board.players):
            new_wall.remove_wall_from_field()
            raise QuoridorOnlineGameError("Wall could not be placed as it would block a player from winning")
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

    def get_length_of_shortest_path_to_win(self):
        current_player = self.get_current_player()
        # shortest_path = sys.maxsize
        # for _ in range(3):
        #     path_finder = PathFinder()
        #     path_finder.start_find_length_of_shortest_path_to_win(current_player.field, current_player.win_option_fields)
        #     for my_thread in path_finder.running_threads:
        #         my_thread.join()
        #     shortest_path = min(path_finder.path_length, shortest_path)
        # path_finder = PathFinder2()
        # path_finder.start_find_length_of_shortest_path_to_win(current_player.field, current_player.win_option_fields)
        # for my_thread in path_finder.running_threads:
        #     my_thread.join()
        path_finder = PathFinderDijkstra(current_player.field, self.game_board.fields, self.game_board)
        shortest_path = path_finder.get_shortest_path_to_win(current_player.win_option_fields)
        return shortest_path

    def get_current_player(self):
        return self.game_board.players[self.its_this_players_turn]

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


class PathChecker:
    """Class that checks that a wall does not block any player
       completely off from winning.

       # TODO: PROBLEM THAT COULD OCCUR:
       A problem that could currently happen, is that there is a path,
       but check_if_path_to_win_exists_for_all_players() returns False.
       This could happen, if a field that need a way to win would contains
       is already visited by another recursion loop.
    """
    def __init__(self):
        self.path_found = None
        self.fields_visited = None

    def check_if_path_to_win_exists_for_all_players(self, players):
        for player in players:
            self.path_found = False
            self.fields_visited = []
            self._check_if_path_to_win_exists(player.field, player.win_option_fields)
            if self.path_found == False:  # after check_if_path_to_win_exists() this should be set
                return False              # to true if there is a path
        return True

    def _check_if_path_to_win_exists(self, field, fields_to_win):
        # Returns true if there is at least one path from field to one of
        # the fields in fields_to_win. Otherwise returns false.
        if field in self.fields_visited:
            return
        if field in fields_to_win:
            self.path_found = True
            return
        if self.path_found:
            return
        self.fields_visited.append(field)
        neighbour_fields = field.neighbour_fields
        for neighbour_field in neighbour_fields:
            self._check_if_path_to_win_exists(neighbour_field, fields_to_win)


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
    def __init__(self, start_field, other_fields, gameboard):
        self.gameboard = gameboard
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
        # self.print_fields(None)
        self.print_fields(field)
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
                if fields_path_length < shortest_path:
                    shortest_path = fields_path_length
                    the_field_with_shortest_path = field
        return the_field_with_shortest_path

    def get_shortest_path_to_win(self, fields_to_win):
        path_length = sys.maxsize
        for field in fields_to_win:
            current_path_length_to_field = self.cost_table[field]["path_length"]
            path_length = min(path_length, current_path_length_to_field)
        return path_length

    def print_fields(self, highlight_field):
        """Use this for debugging to print the game board"""
        for row in range(self.gameboard.amount_fields):
            for col in range(self.gameboard.amount_fields):
                current_field = self.gameboard.getFieldByColAndRow(col, row)
                field_right = self.gameboard.getFieldByColAndRow(col + 1, row)

                # if current_field in self.fields_visited:
                #     field_marker = "X"
                # elif current_field == highlight_field:
                #     field_marker = "?"
                # else:
                #     field_marker = "0"
                field_marker = self.cost_table[current_field]["path_length"]
                if field_marker > 99:
                    field_marker = "#"
                if current_field == highlight_field:
                    field_marker = "?"
                # if current_field.player is not None:
                #     field_marker = current_field.player.user.name[0]
                if field_right in current_field.neighbour_fields:
                    print(f"{str(field_marker).zfill(2)}---", end="")
                else:
                    print(f"{str(field_marker).zfill(2)}   ", end="")
            print()
            for col in range(self.gameboard.amount_fields):
                current_field = self.gameboard.getFieldByColAndRow(col, row)
                field_bottom = self.gameboard.getFieldByColAndRow(col, row + 1)
                if field_bottom in current_field.neighbour_fields:
                    print("|    ", end="")
                else:
                    print("     ", end="")
            print()
