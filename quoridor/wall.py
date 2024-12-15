from errors import QuoridorOnlineGameError
import math


class Wall:
    def __init__(self, player_id, col_start, row_start, col_end, row_end, game_board, place_wall=True):
        """Creates and places a wall on the given game_board, EXCEPT if place_wall is set to False.
           place_wall=False may be used to check if a wall can be placed at a certain location
           without actually placing it.

        Walls can be placed like this:
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
        if place_wall:
            self.remove_links_between_fields()
            game_board.walls.append(self)
        path_checker = PathChecker()
        if not path_checker.check_if_path_to_win_exists_for_all_players(self.game_board.players):
            self.remove_wall_from_field()
            raise QuoridorOnlineGameError("Wall could not be placed as it would block a player from winning")

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


class PathChecker:
    """Class that checks that a wall does not block any player
       completely off from winning.

       # TODO: PROBLEM THAT COULD OCCUR:
       # TODO: Use Dijkstra
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
            self.path_found = False
            self.fields_visited = []
            self._check_if_path_to_win_exists(player.field, player.win_option_fields)
            if self.path_found == False:  # after check_if_path_to_win_exists() this should be set
                return False              # to true if there is a path
        return True

    def _check_if_path_to_win_exists(self, field, fields_to_win):
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
            self._check_if_path_to_win_exists(neighbour_field, fields_to_win)
