import time
import uuid


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
