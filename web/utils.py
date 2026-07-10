import logging
import random
from datetime import datetime
import time
import uuid
import json
import os
from pathlib import Path
from typing import Any, Dict

import redis
from django.contrib.auth import get_user_model
from django.db import transaction
import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

from web import models

logger = logging.getLogger(__name__)

REDIS_ONLINE_USERS_SET_KEY = "online_users"
REDIS_ONLINE_USERS_COUNT_HASH_KEY = "online_users_count"
COLORS = ["red", "orange", "#FFE600", "#199A19", "blue", "#4A0080", "#EE81EE"]


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)


def get_new_uuid():
    return str(uuid.uuid4())


def get_current_time():
    """Get the current time in seconds.

    :return: Time in seconds (float).
             E.g.: 1702510907.4896383
    """
    return time.time()


def get_redis_client():
    if not hasattr(get_redis_client, "_client"):
        redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379")
        get_redis_client._client = redis.from_url(redis_url, decode_responses=True)
    return get_redis_client._client


def add_online_user(user_id: str):
    try:
        client = get_redis_client()
        client.hincrby(REDIS_ONLINE_USERS_COUNT_HASH_KEY, user_id, 1)
        client.sadd(REDIS_ONLINE_USERS_SET_KEY, user_id)
    except redis.RedisError as e:
        logger.warning("Unable to add online user to Redis: %s", e)


def remove_online_user(user_id: str):
    try:
        client = get_redis_client()
        count = client.hincrby(REDIS_ONLINE_USERS_COUNT_HASH_KEY, user_id, -1)
        if count <= 0:
            client.hdel(REDIS_ONLINE_USERS_COUNT_HASH_KEY, user_id)
            client.srem(REDIS_ONLINE_USERS_SET_KEY, user_id)
    except redis.RedisError as e:
        logger.warning("Unable to remove online user from Redis: %s", e)


def get_online_user_ids():
    try:
        client = get_redis_client()
        return list(client.smembers(REDIS_ONLINE_USERS_SET_KEY))
    except redis.RedisError as e:
        logger.warning("Unable to read online user ids from Redis: %s", e)
        return []


def get_online_user_count():
    try:
        client = get_redis_client()
        return client.scard(REDIS_ONLINE_USERS_SET_KEY)
    except redis.RedisError as e:
        logger.warning("Unable to read online user count from Redis: %s", e)
        return 0

def get_player_guest_name():
    return f"Guest-{str(uuid.uuid4())[:6]}"


def get_random_color():
    # these are html colors (https://htmlcolorcodes.com/color-names/)
    # colors = ["red", "blue", "green", "black", "deepPink", "orangeRed"]
    return COLORS[random.randint(0, len(COLORS)-1)]


def delete_json_files_without_game():
    """Deletes all JSON files in the specified folder that do not contain a 'game' key."""
    # Ordner mit den JSON-Dateien
    folder = Path("/pfad/zum/ordner")

    for json_file in folder.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("game") is None:
                print(f"Lösche {json_file.name}")
                json_file.unlink()

                # Zugehörige .lock-Datei löschen
                lock_file = json_file.with_suffix(".json.lock")
                if lock_file.exists():
                    print(f"Lösche {lock_file.name}")
                    lock_file.unlink()

        except Exception as e:
            print(f"Fehler bei {json_file.name}: {e}")


def send_email(content):
    try:
        smtp = smtplib.SMTP('smtp.ionos.de', 587)
        smtp.connect('smtp.ionos.de', 587)
        smtp.starttls()
        smtp.ehlo()
        password = os.getenv("IONOS_PASSWORD")
        if password is None:
            return
        smtp.login("support@quoridoronline.com", password)
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "NEW LOBBY"
        msg['From'] = "support@quoridoronline.com"
        msg['To'] = "tobi83301@gmail.com"
        msg.attach(MIMEText(content, "plain"))
        smtp.send_message(msg)
    except Exception as e:
        logger.warning("Unable to send email: %s", e)
