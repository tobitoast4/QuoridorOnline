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
        if str(self._get_current_player().gameplayer.game_user.id) != user_id:
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

    def move_player(self, user_id, lobby, new_field_col, new_field_row):
        """Can be used to move a player."""
        if str(self._get_current_player().gameplayer.game_user.id) != user_id:
            print(str(self._get_current_player().gameplayer.game_user.id), user_id)
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
            if result is not None:
                self.state = STATE_PLAYER_DID_WIN
                lobby.winner = player.gameplayer
                lobby.save()
        self._next_players_turn()

    def place_wall(self, user_id, col_start, row_start, col_end, row_end, skip_user_check=False):
        """Can be used to place a wall."""
        if not skip_user_check:
            if str(self._get_current_player().gameplayer.game_user.id) != user_id:
                raise QuoridorOnlineGameError("It's not your turn currently")
            if self._get_current_player().amount_walls_left <= 0:
                raise QuoridorOnlineGameError("You do not have any more walls left")
        player = self._get_player_of_user(user_id)
        # if player.gameplayer.has_surrendered:
        #     raise QuoridorOnlineGameError("You have surrendered already")
        new_wall = wall.Wall(user_id, col_start, row_start, col_end, row_end, self.game_board)
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
        player = self.game_board.players[self.its_this_players_turn]
        if player.gameplayer.has_surrendered:
            self._next_players_turn()  # skip this player, as he has surrendered
        self._append_game_data()

    def _get_player_of_user(self, user_id):
        for player in self.game_board.players:
            if str(player.gameplayer.game_user.id) == str(user_id):
                return player
        return None

    def _get_current_player(self):
        player = self.game_board.players[self.its_this_players_turn]
        if player.gameplayer.has_surrendered:
            self._next_players_turn()
            return self._get_current_player()
        return player

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
            if not player.gameplayer.has_surrendered:
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
