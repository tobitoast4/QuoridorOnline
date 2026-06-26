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


def create_lobby_from_json(payload: Dict[str, Any]):
    """Create a lobby and its owner player from a JSON-like payload."""
    lobby_id = payload.get("lobby_id")
    owner_data = payload.get("lobby_owner") or {}
    owner_name = owner_data.get("name")
    owner_color = owner_data.get("color") or get_random_color()
    owner_id = owner_data.get("id")
    owner_uuid = uuid.UUID(owner_id) if owner_id else None
    lobby_uuid = uuid.UUID(lobby_id) if lobby_id else None
    game_data = payload.get("game")
    game_json = json.dumps(game_data, cls=UUIDEncoder) if game_data is not None else None
    players_data = payload.get("players", [])
    players_last_seen = payload.get("players_last_seen", [])
    created_at = payload.get("time_created")

    if owner_uuid is None and not owner_name:
        raise ValueError("lobby_owner.id or lobby_owner.name is required")

    user_model = get_user_model()
    player_records = {}

    for index, player_payload in enumerate(players_data):
        player_id = player_payload.get("id")
        player_name = player_payload.get("name")
        if not player_id:
            raise ValueError("Each player must include an 'id'")
        if not player_name:
            raise ValueError(f"Player {player_id} must include a 'name'")

        player_uuid = uuid.UUID(player_id)
        player_color = player_payload.get("color") or get_random_color()
        player_user = user_model.objects.filter(pk=player_uuid).first()

        player_usernames_count = user_model.objects.filter(username__startswith=player_name).count()
        if player_usernames_count > 0:
            player_name += str(player_usernames_count)

        if player_user is None:
            player_user = user_model.objects.create(
                id=player_uuid,
                username=player_name,
                email="",
                color=player_color,
                is_guest=True,
            )
        # else:
        #     player_user.username = player_name
        #     player_user.color = player_color
        #     player_user.save(update_fields=["username", "color"])

        last_seen = int(players_last_seen[index]) if index < len(players_last_seen) else int(time.time())
        player_records[player_uuid] = {
            "user": player_user,
            "color": player_color,
            "last_seen": last_seen,
        }

    if lobby_uuid:
        lobby = models.Lobby.objects.filter(pk=lobby_uuid).first()
        if lobby is None:
            lobby = models.Lobby.objects.create(
                id=lobby_uuid,
                created_by=None,
                amount_of_walls_per_player=payload.get("amount_of_walls_per_player", 10),
                is_private=payload.get("is_private", True),
                game=game_json,
                created_at=datetime.fromtimestamp(created_at) if created_at is not None else None,
            )
        else:
            return
    else:
        lobby = models.Lobby.objects.create(
            created_by=None,
            amount_of_walls_per_player=payload.get("amount_of_walls_per_player", 10),
            is_private=payload.get("is_private", True),
            game=game_json,
            created_at=datetime.fromtimestamp(created_at) if created_at is not None else None,
        )
    

    owner_user = None
    if owner_uuid in player_records:
        owner_user = player_records[owner_uuid]["user"]
    elif owner_uuid is not None:
        owner_user = user_model.objects.filter(pk=owner_uuid).first()
        
        owner_usernames_count = user_model.objects.filter(username__startswith=owner_name).count()
        if owner_usernames_count > 0:
            owner_name += str(owner_usernames_count)

    if owner_user is None:
        if not owner_name:
            raise ValueError("lobby_owner.name is required when the owner is not listed in players")
        owner_user = user_model.objects.create(
            id=owner_uuid,
            username=owner_name,
            email="",
            color=owner_color,
            is_guest=True,
        )
    # else:
    #     owner_user.username = owner_name or owner_user.username
    #     owner_user.color = owner_color
    #     owner_user.save(update_fields=["username", "color"])

    owner_player = None
    for player_uuid, record in player_records.items():
        gameplayer = models.GamePlayer.objects.filter(lobby=lobby, game_user=record["user"]).first()
        if gameplayer is None:
            gameplayer = models.GamePlayer.objects.create(
                game_user=record["user"],
                lobby=lobby,
                color=record["color"],
                last_seen=record["last_seen"],
            )
        else:
            gameplayer.color = record["color"]
            gameplayer.last_seen = record["last_seen"]
            gameplayer.save(update_fields=["color", "last_seen"])

        if player_uuid == owner_uuid:
            owner_player = gameplayer

    if owner_player is None:
        owner_player = models.GamePlayer.objects.filter(lobby=lobby, game_user=owner_user).first()
        if owner_player is None:
            owner_player = models.GamePlayer.objects.create(
                game_user=owner_user,
                lobby=lobby,
                color=owner_color,
                last_seen=int(time.time()),
            )

    lobby.created_by = owner_user
    lobby.owner = owner_player
    lobby.save(update_fields=["created_by", "owner"])
    return lobby


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


# #send email
# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# server = smtplib.SMTP('smtp.ionos.de', 587)
#
# name="Tobi" #You need to fill the name here
# server.connect('smtp.ionos.de', 587)
# server.starttls()
# server.ehlo()
# server.login("support@quoridoronline.com", "A16...")
# TOADDR = "tobi.zillmann@gmail.com"
# FromADDR = "support@quoridoronline.com"
# msg = MIMEMultipart('alternative')
# msg['Subject'] = "email subject here"
# msg['From'] = FromADDR
# msg['To'] = f"{TOADDR},support@quoridoronline.com"
# #The below is email body
# html = """\
#             <html>
#               <body>
#                 <p><span style="color: rgb(0,0,0);">Dear {0},</span></p>
#                <p>
#                   your email body
#                 </p>
#                 <p>Kind Regards,<br />
#                 Your name ....
#                 </p>
#                 </body>
#             </html>
#             """.format(name.split()[0])
# msg.attach(MIMEText(html, 'html'))
# server.sendmail(FromADDR, TOADDR, msg.as_string())