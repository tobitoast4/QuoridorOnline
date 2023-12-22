from errors import QuoridorOnlineGameError
import quoridor.game_board as game_board
import quoridor.wall as wall
import user
import utils

STATE_PLACING_PLAYERS = -1
STATE_PLAYING = 0
STATE_PLAYER_DID_WIN = 2


class Game:
    def __init__(self, users: [user.User]):
        self.game_board = game_board.GameBoard(users)
        self.state = STATE_PLACING_PLAYERS
        self.its_this_players_turn = 0
        self.turn = 0
        self.game_data = {
            "initial_setup": self.game_board.__json__(initial=True),
            "game": []
        }
        self._append_game_data()

    def move_player(self, user_id, new_field_col, new_field_row):
        """Can be used to move a player."""
        if self._get_current_player().user.id != user_id:  # TODO: make this a decorator?
            raise QuoridorOnlineGameError("It's not your turn currently")
        player = self._get_player_of_user(user_id)
        new_field = self.game_board.getFieldByColAndRow(new_field_col, new_field_row)
        if self.state == STATE_PLACING_PLAYERS:
            player.move_to_field(new_field, True)
            if self.its_this_players_turn == len(self.game_board.players)-1:  # last player placed his piece initially
                self.state = STATE_PLAYING
        else:
            player.move_to_field(new_field)
        self._next_players_turn()

    def place_wall(self, user_id, col_start, row_start, col_end, row_end):
        """Can be used to place a wall."""
        if self._get_current_player().user.id != user_id:  # TODO: make this a decorator?
            raise QuoridorOnlineGameError("It's not your turn currently")
        new_wall = wall.Wall(col_start, row_start, col_end, row_end, self.game_board)
        self.game_board.walls.append(new_wall)
        self._next_players_turn()

    def get_current_game_data(self):
        """Can be used to query the current status of the game."""
        return self.game_data

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
