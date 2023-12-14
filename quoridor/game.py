from errors import QuoridorOnlineGameError
from player import *
from field import *


class GameBoard:
    def __init__(self, users: [user.User]):
        if len(users) < 2 or len(users) > 4:
            raise QuoridorOnlineGameError("Allowed amount of players are 2, 3 or 4.")
        self.amount_fields = 9
        self.fields = []
        self.players = [Player(the_user) for the_user in users]
        self.create_fields()
        self.set_players_start_and_win_fields()  # fields need to be created first

    def create_fields(self):
        # create fields
        for col in range(self.amount_fields):
            for row in range(self.amount_fields):
                self.fields.append(Field(col, row))
        # create links between fields
        for field in self.fields:
            field_on_top = self.getFieldByColAndRow(field.col_num - 1, field.row_num)
            if field_on_top is not None:
                field.neighbour_fields.append(field_on_top)
            field_on_bottom = self.getFieldByColAndRow(field.col_num + 1, field.row_num)
            if field_on_bottom is not None:
                field.neighbour_fields.append(field_on_bottom)
            field_left = self.getFieldByColAndRow(field.col_num, field.row_num - 1)
            if field_left is not None:
                field.neighbour_fields.append(field_left)
            field_right = self.getFieldByColAndRow(field.col_num, field.row_num + 1)
            if field_right is not None:
                field.neighbour_fields.append(field_right)

    def set_players_start_and_win_fields(self):
        for p in range(len(self.players)):
            player = self.players[p]
            if p == 0:  # first player
                player.start_option_fields = self.getFieldsByColOrRow(None, 0)
                player.win_option_fields = self.getFieldsByColOrRow(None, self.amount_fields-1)
            if p == 1:  # second player
                player.start_option_fields = self.getFieldsByColOrRow(None, self.amount_fields-1)
                player.win_option_fields = self.getFieldsByColOrRow(None, 0)
            if p == 2:  # third player
                player.start_option_fields = self.getFieldsByColOrRow(0, None)
                player.win_option_fields = self.getFieldsByColOrRow(self.amount_fields-1, None)
            if p == 3:  # fourth player
                player.start_option_fields = self.getFieldsByColOrRow(self.amount_fields-1, None)
                player.win_option_fields = self.getFieldsByColOrRow(0, None)

    def getFieldByColAndRow(self, col_num, row_num) -> Field:
        if not (col_num < 0 or row_num < 0 or col_num >= self.amount_fields or row_num >= self.amount_fields):
            for field in self.fields:
                if field.col_num == col_num and field.row_num == row_num:
                    return field
        return None

    def getFieldsByColOrRow(self, col_num, row_num):
        """Returns all fields in the specified column / row.
           Inputs can be col_num=k, row_num=None or col_num=None, row_num=k .
           Other inputs will return null.
        """
        if col_num < 0 or row_num < 0 or col_num >= self.amount_fields or row_num >= self.amount_fields:
            return None
        fields_to_return = []
        if col_num is None:
            for i in range(self.amount_fields):
                fields_to_return.append(self.getFieldByColAndRow(i, row_num))
        elif row_num is None:
            for i in range(self.amount_fields):
                fields_to_return.append(self.getFieldByColAndRow(col_num, i))
        else:
            return None
        return fields_to_return

    def print_fields(self):
        for row in range(self.amount_fields):
            for col in range(self.amount_fields):
                current_field = self.getFieldByColAndRow(col, row)
                field_right = self.getFieldByColAndRow(col + 1, row)
                if field_right in current_field.neighbour_fields:
                    print("0    ", end="")
                else:
                    print("0    ", end="")
            print()
            for col in range(self.amount_fields):
                current_field = self.getFieldByColAndRow(col, row)
                field_bottom = self.getFieldByColAndRow(col, row + 1)
                if field_bottom in current_field.neighbour_fields:
                    print("     ", end="")
                else:
                    print("     ", end="")
            print()


user1 = user.User()
user1.id = "id_player_1"
user1.name = "Red"

user2 = user.User()
user2.id = "id_player_2"
user2.name = "Green"

users = [user1, user2]

game_board = GameBoard(users)
game_board.print_fields()
