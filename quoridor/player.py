from errors import QuoridorOnlineGameError
import quoridor.field as field
import user


class Player:
    def __init__(self, the_user: user.User):
        self.user = the_user
        self.field = None
        self.amount_walls_left = 10
        self.start_option_fields = []
        self.win_option_fields = []

    def move_to_field(self, new_field: field.Field, is_initial_move=False):
        """Moves the player to a new field while respecting their possible moves.

           Returns the player if move was a win. Else None.
        """
        if is_initial_move:
            if new_field not in self.start_option_fields:
                raise QuoridorOnlineGameError("Field not allowed for this player as initial move.")
        else:
            if new_field not in self.getMoveOptions():
                raise QuoridorOnlineGameError("Field not allowed for this player.")
        if self.field is not None:
            self.field.player = None  # remove player from old field
        new_field.player = self
        self.field = new_field
        if new_field in self.win_option_fields:
            return self  # THE PLAYER DID WIN! (Maybe return something different here?)

    def getMoveOptions(self):
        """Gets the move option fields for the player at their current position respecting other players.
           A player can jump over one other player but not over two.
           Two players can not share the same field and one can not kick another out of their field.
        """
        move_option_fields = []
        if self.field is None:
            return []
        for the_field in self.field.neighbour_fields:
            if the_field.player is None:
                move_option_fields.append(the_field)
            else:
                location_of_neighbour_field = self.field.getNeighbourFieldLocation(the_field)
                new_move_option_field = the_field.getNeighbourField(location_of_neighbour_field)
                if new_move_option_field is not None and new_move_option_field.player is None:
                    move_option_fields.append(new_move_option_field)
        return move_option_fields


    def __json__(self, initial=False):
        if initial:
            return {
                "user": self.user.__json__(),
                "amount_walls_left": self.amount_walls_left,
                "start_option_fields": [f.__json__() for f in self.start_option_fields],
                "win_option_fields": [f.__json__() for f in self.win_option_fields]
            }
        else:
            field_json = None
            if self.field is not None:
                field_json = self.field.__json__()
            return {
                "user": self.user.__json__(),
                "field": field_json,
                "amount_walls_left": self.amount_walls_left,
                "move_options": [f.__json__() for f in self.getMoveOptions()],
            }
