from errors import QuoridorOnlineGameError
import math


class Wall:
    def __init__(self, col_start, row_start, col_end, row_end, game_board):
        """Walls can be placed like this:
        Wall is placed vertically:
                          ->  col_start=0.5, row_start=0, col_end=0.5, row_end=1
          field (0, 0)
            +-----+  #  +-----+
            |     |  #  |  x  |
            +-----+  #  +-----+
                     #                  (### is the wall)
            +-----+  #  +-----+
            |     |  #  |     |
            +-----+  #  +-----+ field (1, 1)

        Wall is placed horizontally:
                          ->  col_start=0, row_start=0.5, col_end=1, row_end=0.5
          field (0, 0)
            +-----+     +-----+
            |     |     |     |
            +-----+     +-----+
            ###################
            +-----+     +-----+
            |  x  |     |     |
            +-----+     +-----+
                            field (1, 1)
        """
        error_msg = f"This wall can not be placed (col_start={col_start}, row_start={row_start}, " \
                    f"col_end={col_end}, row_end={row_end})"
        if col_start != col_end and row_start != row_end:
            raise QuoridorOnlineGameError(error_msg)
        if col_start == col_end and col_end % 1 != 0.5:
            raise QuoridorOnlineGameError(error_msg)
        if row_start == row_end and row_end % 1 != 0.5:
            raise QuoridorOnlineGameError(error_msg)
        self.col_start = col_start
        self.row_start = row_start
        self.col_end = col_end
        self.row_end = row_end
        self.game_board = game_board
        if game_board.is_new_wall_overlapping_old_walls(self):
            error_msg = f"This wall can not be placed (col_start={col_start}, row_start={row_start}, " \
                        f"col_end={col_end}, row_end={row_end}) as it is overlapping with another wall"
            raise QuoridorOnlineGameError(error_msg)
        self.remove_links_between_fields()

    def remove_links_between_fields(self):
        if self.col_start == self.col_end:  # wall is vertical
            field_col_left = math.ceil(self.col_start)
            field_col_right = math.floor(self.col_start)
            field_top_left = self.game_board.getFieldByColAndRow(field_col_left, self.row_start)
            field_top_right = self.game_board.getFieldByColAndRow(field_col_right, self.row_start)
            field_top_left.remove_connection(field_top_right)
            field_bottom_left = self.game_board.getFieldByColAndRow(field_col_left, self.row_end)
            field_bottom_right = self.game_board.getFieldByColAndRow(field_col_right, self.row_end)
            field_bottom_left.remove_connection(field_bottom_right)
        elif self.row_start == self.row_end:
            field_row_top = math.floor(self.row_start)
            field_row_bottom = math.ceil(self.row_start)
            field_top_left = self.game_board.getFieldByColAndRow(self.col_start, field_row_top)
            field_bottom_left = self.game_board.getFieldByColAndRow(self.col_start, field_row_bottom)
            field_top_left.remove_connection(field_bottom_left)
            field_top_right = self.game_board.getFieldByColAndRow(self.col_end, field_row_top)
            field_bottom_right = self.game_board.getFieldByColAndRow(self.col_end, field_row_bottom)
            field_top_right.remove_connection(field_bottom_right)
        else:
            raise QuoridorOnlineGameError("Either col_start == col_end or col_start == col_end must be true")

    def is_overlapping_other_wall(self, other_wall: 'Wall'):
        # cases for same alignment (vertical / horizontal)
        if other_wall._is_wall_at_coordinates(self.col_start, self.row_start):
            return True
        if other_wall._is_wall_at_coordinates(self.col_end, self.row_end):
            return True
        # cases for different alignment
        if (other_wall.col_start + other_wall.col_end) / 2 == self.col_start and \
                other_wall.row_start == (self.row_start + self.row_end) / 2:
            return True

    def _is_wall_at_coordinates(self, col, row):
        """Checks if wall is at coordinates.:
        E.g. Wall is placed here:
                          ->  col_start=0.5, row_start=0, col_end=0.5, row_end=1
          field (0, 0)
            +-----+  #  +-----+
            |     |  #  |  x  |
            +-----+  #  +-----+
                     #                  (### is the wall)
            +-----+  #  +-----+
            |     |  #  |     |
            +-----+  #  +-----+ field (1, 1)

        col=0.5, row=0 returns True
        col=0.5, row=1 returns True
        """
        if col == self.col_start and row == self.row_start:
            return True
        if col == self.col_end and row == self.row_end:
            return True

    def __json__(self):
        return {
            "start": {
                "col": self.col_start,
                "row": self.row_start,
            },
            "end": {
                "col": self.col_end,
                "row": self.row_end,
            },
        }
