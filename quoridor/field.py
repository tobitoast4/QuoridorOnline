
class Field:
    def __init__(self, col_num, row_num):
        self.col_num = col_num
        self.row_num = row_num
        self.neighbour_fields = []
        self.player = None

    def __json__(self):
        return {
            "col_num": self.col_num,
            "row_num": self.row_num,
        }
