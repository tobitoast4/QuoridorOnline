from errors import QuoridorOnlineGameError
import math


class Wall:
    def __init__(self, player_id, col_start, row_start, col_end, row_end, game_board):
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
        error_msg = f"Walls can not overlap"
        if col_start != col_end and row_start != row_end:
            raise QuoridorOnlineGameError(error_msg)
        if col_start == col_end and col_end % 1 != 0.5:
            raise QuoridorOnlineGameError(error_msg)
        if row_start == row_end and row_end % 1 != 0.5:
            raise QuoridorOnlineGameError(error_msg)
        self.player_id = player_id  # placed by this player
        self.col_start = col_start
        self.row_start = row_start
        self.col_end = col_end
        self.row_end = row_end
        self.game_board = game_board
        if game_board.is_new_wall_overlapping_old_walls(self):
            raise QuoridorOnlineGameError(error_msg)
        self.remove_links_between_fields()

    def remove_links_between_fields(self):
        if self.col_start == self.col_end:  # wall is vertical
            col_left = math.ceil(self.col_start)
            col_right = math.floor(self.col_start)
            field_top_left = self.game_board.getFieldByColAndRow(col_left, self.row_start)
            field_top_right = self.game_board.getFieldByColAndRow(col_right, self.row_start)
            field_top_left.remove_connection(field_top_right)
            field_bottom_left = self.game_board.getFieldByColAndRow(col_left, self.row_end)
            field_bottom_right = self.game_board.getFieldByColAndRow(col_right, self.row_end)
            field_bottom_left.remove_connection(field_bottom_right)
        elif self.row_start == self.row_end:
            row_top = math.floor(self.row_start)
            row_bottom = math.ceil(self.row_start)
            field_top_left = self.game_board.getFieldByColAndRow(self.col_start, row_top)
            field_bottom_left = self.game_board.getFieldByColAndRow(self.col_start, row_bottom)
            field_top_left.remove_connection(field_bottom_left)
            field_top_right = self.game_board.getFieldByColAndRow(self.col_end, row_top)
            field_bottom_right = self.game_board.getFieldByColAndRow(self.col_end, row_bottom)
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
        # new wall is placed horizontally
        if (other_wall.col_start + other_wall.col_end) / 2 == self.col_start and \
                other_wall.row_start == (self.row_start + self.row_end) / 2:
            return True
        # new wall is placed vertically
        if (other_wall.row_start + other_wall.row_end) / 2 == self.row_start and \
                other_wall.col_start == (self.col_start + self.col_end) / 2:
            return True

    def remove_wall_from_field(self):
        if self.col_start == self.col_end:  # wall is vertical
            col_left = math.floor(self.col_start)
            col_right = math.ceil(self.col_start)
            field_top_left = self.game_board.getFieldByColAndRow(col_left, self.row_start)
            field_top_right = self.game_board.getFieldByColAndRow(col_right, self.row_start)
            field_bottom_left = self.game_board.getFieldByColAndRow(col_left, self.row_end)
            field_bottom_right = self.game_board.getFieldByColAndRow(col_right, self.row_end)
            field_top_left.add_connection(field_top_right)
            field_bottom_left.add_connection(field_bottom_right)
        elif self.row_start == self.row_end:
            row_top = math.floor(self.row_start)
            row_bottom = math.ceil(self.row_start)
            field_top_left = self.game_board.getFieldByColAndRow(self.col_start, row_top)
            field_top_right = self.game_board.getFieldByColAndRow(self.col_end, row_top)
            field_bottom_left = self.game_board.getFieldByColAndRow(self.col_start, row_bottom)
            field_bottom_right = self.game_board.getFieldByColAndRow(self.col_end, row_bottom)
            field_top_left.add_connection(field_bottom_left)
            field_top_right.add_connection(field_bottom_right)
        self.game_board.walls.remove(self)

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
            "player_id": self.player_id,
            "start": {
                "col": self.col_start,
                "row": self.row_start,
            },
            "end": {
                "col": self.col_end,
                "row": self.row_end,
            },
        }
