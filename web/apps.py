import json
from pathlib import Path
from django.apps import AppConfig



class WebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web'

    def ready(self):
        pass
        from . import models
        from web.utils import create_lobby_from_json

        # return
        for datei in Path("old_games").iterdir():
            if datei.is_file():
                # try:
                    with open(datei, "r", encoding="utf-8") as f:
                        inhalt = f.read()

                    create_lobby_from_json(json.loads(inhalt))
                # except Exception as e:
                #     print(f"Fehler beim Verarbeiten der Datei {datei}: {e}")