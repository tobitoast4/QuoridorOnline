import user


class Player:
    def __init__(self, the_user: user.User):
        self.user = user
        self.field = None
        self.start_option_fields = []
        self.win_option_fields = []