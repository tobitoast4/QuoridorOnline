
class Field:
    def __init__(self, col_num, row_num, game_board):
        self.col_num = col_num
        self.row_num = row_num
        self.game_board = game_board
        self.neighbour_fields = []
        self.player = None

    def remove_connection(self, other_field: 'Field'):
        other_field.neighbour_fields.remove(self)
        self.neighbour_fields.remove(other_field)

    def getNeighbourField(self, position):
        """Returns the neighbour of the actual field
           Position can be "right", "bottom", "left" or "top"
        """
        if position == "right":
            return self.game_board.getFieldByColAndRow(self.col_num + 1, self.row_num)
        elif position == "bottom":
            return self.game_board.getFieldByColAndRow(self.col_num, self.row_num + 1)
        elif position == "left":
            return self.game_board.getFieldByColAndRow(self.col_num - 1, self.row_num)
        elif position == "top":
            return self.game_board.getFieldByColAndRow(self.col_num, self.row_num - 1)
        else:
            return None

    def getNeighbourFieldLocation(self, field_to_check):
        """The inverse function of getNeighbourField()"""
        if field_to_check == self.game_board.getFieldByColAndRow(self.col_num + 1, self.row_num):
            return "right"
        elif field_to_check == self.game_board.getFieldByColAndRow(self.col_num, self.row_num + 1):
            return "bottom"
        elif field_to_check == self.game_board.getFieldByColAndRow(self.col_num - 1, self.row_num):
            return "left"
        elif field_to_check == self.game_board.getFieldByColAndRow(self.col_num, self.row_num - 1):
            return "top"
        else:
            return None

    def __json__(self):
        return {
            "col_num": self.col_num,
            "row_num": self.row_num,
        }
