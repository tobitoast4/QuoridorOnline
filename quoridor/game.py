import utils
import game_board
import user

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
            "inital_setup": self.game_board.__json__(),
            "game": []
        }
        self.append_game_data()

    def move_player(self, the_user, new_field_col, new_field_row):
        player = self.get_player_of_user(the_user)
        new_field = self.game_board.getFieldByColAndRow(new_field_col, new_field_row)
        if self.state == STATE_PLACING_PLAYERS:
            player.move_to_field(new_field, True)
            if self.its_this_players_turn == len(self.game_board.players)-1:  # last player placed his piece initially
                self.state = STATE_PLAYING
        else:
            player.move_to_field(new_field)
        self.nextPlayersTurn()
        self.append_game_data()

    def nextPlayersTurn(self):
        self.its_this_players_turn += 1
        if self.its_this_players_turn >= len(self.game_board.players):
            self.its_this_players_turn = 0
            self.turn += 1

    def get_player_of_user(self, the_user):
        for player in self.game_board.players:
            if player.user.id == the_user.id:
                return player
        return None

    def append_game_data(self):
        self.game_data["game"].append({
            "state": self.state,
            "its_this_players_turn": self.its_this_players_turn,
            "turn": self.turn,
            "time": utils.get_current_time(),
            "game_board": self.game_board.__json__(),
        })



user1 = user.User()
user1.id = "id_player_1"
user1.name = "Red"

user2 = user.User()
user2.id = "id_player_2"
user2.name = "Green"

users = [user1, user2]

game = Game(users)

print(game.state)
game.move_player(user1, 4, 0)
print(game.state)
game.move_player(user2, 4, 8)
print(game.state)
game.move_player(user1, 4, 1)
print(game.state)

print(game.game_data)
