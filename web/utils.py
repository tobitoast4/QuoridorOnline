import random
from datetime import datetime
import time
import uuid
import json
from pathlib import Path
from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.db import transaction

from web import models

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


#send email
import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
smtp = smtplib.SMTP('smtp.ionos.de', 587)

def send_email(content):
    name="Tobi" #You need to fill the name here
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