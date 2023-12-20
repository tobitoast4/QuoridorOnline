
class Field:
    def __init__(self, col_num, row_num):
        self.col_num = col_num
        self.row_num = row_num
        self.neighbour_fields = []
        self.player = None

    def remove_connection(self, other_field: 'Field'):
        other_field.neighbour_fields.remove(self)
        self.neighbour_fields.remove(other_field)

    def __json__(self):
        return {
            "col_num": self.col_num,
            "row_num": self.row_num,
        }
