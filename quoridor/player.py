from errors import QuoridorOnlineGameError
import quoridor.field as field
import user


class Player:
    def __init__(self, the_user: user.User):
        self.user = the_user
        self.field = None
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
            if new_field not in self.field.neighbour_fields:
                raise QuoridorOnlineGameError("Field not allowed for this player.")
        if new_field in self.win_option_fields:
            return self  # THE PLAYER DID WIN! (Maybe return something different here?)
        if self.field is not None:
            self.field.player = None  # remove player from old field
        new_field.player = self
        self.field = new_field

    def __json__(self, initial=False):
        if initial:
            return {
                "user": self.user.__json__(),
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
            }
