
class Wall:
    def __init__(self, field_to_attach, is_vertical, game_board):
        """This (x) is the field_to_attach:
        If wall is placed vertically:

            +-----+  #  +-----+
            |     |  #  |  x  |
            +-----+  #  +-----+
                     #                  (### is the wall)
            +-----+  #  +-----+
            |     |  #  |     |
            +-----+  #  +-----+

        If wall is placed horizontally:

            +-----+     +-----+
            |     |     |     |
            +-----+     +-----+
            ###################
            +-----+     +-----+
            |  x  |     |     |
            +-----+     +-----+

        """
        if is_vertical:
            self.field_top_right = field_to_attach
            self.field_bottom_left = game_board.getFieldByColAndRow(field_to_attach.col_num-1, field_to_attach.row_num+1)
            self.field_top_left = game_board.getFieldByColAndRow(field_to_attach.col_num-1, field_to_attach.row_num)
            self.field_bottom_right = game_board.getFieldByColAndRow(field_to_attach.col_num, field_to_attach.row_num+1)
        else:
            self.field_bottom_left = field_to_attach
            self.field_top_right = game_board.getFieldByColAndRow(field_to_attach.col_num+1, field_to_attach.row_num-1)
            self.field_top_left = game_board.getFieldByColAndRow(field_to_attach.col_num, field_to_attach.row_num-1)
            self.field_bottom_right = game_board.getFieldByColAndRow(field_to_attach.col_num+1, field_to_attach.row_num)
        self.is_vertical = is_vertical
        self.remove_links_between_fields()

    def remove_links_between_fields(self):
        if self.is_vertical:
            self.field_top_left.neighbour_fields.remove(self.field_top_right)
            self.field_top_right.neighbour_fields.remove(self.field_top_left)
            self.field_bottom_left.neighbour_fields.remove(self.field_bottom_right)
            self.field_bottom_right.neighbour_fields.remove(self.field_bottom_left)
        else:
            self.field_top_left.neighbour_fields.remove(self.field_bottom_left)
            self.field_bottom_left.neighbour_fields.remove(self.field_top_left)
            self.field_top_right.neighbour_fields.remove(self.field_bottom_right)
            self.field_bottom_right.neighbour_fields.remove(self.field_top_right)

    def is_wall_overlapping(self, other_wall):
        pass
