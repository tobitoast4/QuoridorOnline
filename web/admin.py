from django.contrib import admin
from web import models

# Register your models here.

@admin.register(models.GameUser)
class GameUserAdmin(admin.ModelAdmin):
    pass

@admin.register(models.GamePlayer)
class GamePlayerAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Lobby)
class LobbyAdmin(admin.ModelAdmin):
    pass