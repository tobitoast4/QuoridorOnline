from errors import QuoridorOnlineGameError
import quoridor.game_board as game_board
import quoridor.wall as wall
import user
import utils

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
        if self._get_current_player().user.id != user_id:
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
            if self._get_current_player().user.id != user_id:
                raise QuoridorOnlineGameError("It's not your turn currently")
            if self._get_current_player().amount_walls_left <= 0:
                raise QuoridorOnlineGameError("You do not have any more walls left")
        new_wall = wall.Wall(col_start, row_start, col_end, row_end, self.game_board)
        self.game_board.walls.append(new_wall)
        path_checker = PathChecker()
        if not path_checker.check_if_path_to_win_exists_for_all_players(self.game_board.players):
            new_wall.remove_wall_from_field()
            raise QuoridorOnlineGameError("Wall could not be placed as it would block a player from winning")
        # if creating a wall did not throw an exception, decrease the amount of walls the player has
        if not skip_user_check:
            self._get_current_player().amount_walls_left -= 1
            self._next_players_turn()

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

    def _get_current_player(self):
        return self.game_board.players[self.its_this_players_turn]

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
            self.check_if_path_to_win_exists(player.field, player.win_option_fields)
            if self.path_found == False:  # after check_if_path_to_win_exists() this should be set
                return False              # to true if there is a path
        return True

    def check_if_path_to_win_exists(self, field, fields_to_win):
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
            self.check_if_path_to_win_exists(neighbour_field, fields_to_win)
