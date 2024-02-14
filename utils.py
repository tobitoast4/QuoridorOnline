import random
import time
import uuid

COLORS = ["red", "orange", "#FFE600", "#199A19", "blue", "#4A0080", "#EE81EE"]


def get_new_uuid():
    return str(uuid.uuid4())


def get_current_time():
    """Get the current time in seconds.

    :return: Time in seconds (float).
             E.g.: 1702510907.4896383
    """
    return time.time()


def get_player_guest_name():
    return f"Guest-{str(uuid.uuid4())[:6]}"


def get_random_color():
    # these are html colors (https://htmlcolorcodes.com/color-names/)
    # colors = ["red", "blue", "green", "black", "deepPink", "orangeRed"]
    return COLORS[random.randint(0, len(COLORS)-1)]
