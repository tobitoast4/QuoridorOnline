from flask_login import UserMixin
import utils


class User(UserMixin):
    def __init__(self):
        self.id = utils.get_new_uuid()
        self.name = utils.get_player_guest_name()
        self.color = utils.get_random_color()

    def __str__(self):
        return f"{self.name} ({self.id})"

    def __json__(self):
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color
        }


def get_user_from_dict(json_dict):
    """Returns a user based on a dict.

    :param json_dict: The user as json dict.
                      E.g.: {'user_id': '3aac9193-ef2d-4c8e-b143-70c69f9e7b19', 'user_name': 'Guest-35e08f'}
    :return:
    """
    user = User()
    user.id = json_dict["user_id"]
    user.name = json_dict["user_name"]
    user.color = json_dict["user_color"]
    return user
