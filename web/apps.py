import json
from pathlib import Path
from django.apps import AppConfig



class WebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web'

    def ready(self):
        pass
        # from . import models
