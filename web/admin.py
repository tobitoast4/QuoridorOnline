from django.contrib import admin
from django.db import models as djmodels
from django.db.models import Count, Q
from web import models

# Register your models here.

class AutoSearchAdmin(admin.ModelAdmin):
    """Admin base that automatically enables search on text fields.

    It inspects the model for CharField/TextField and returns their names
    for `search_fields`. Override `search_fields` in subclasses to customize.
    """
    def get_search_fields(self, request):
        # collect concrete CharField/TextField names
        names = []
        for f in getattr(self.model, '_meta').get_fields():
            if isinstance(f, (djmodels.UUIDField)):
                names.append(str(f.name))
            if isinstance(f, (djmodels.CharField, djmodels.TextField)):
                names.append(f.name)
        return tuple(names) if names else super().get_search_fields(request)


@admin.register(models.GameUser)
class GameUserAdmin(AutoSearchAdmin):
    list_display = (
        "username",
        "email",
        "is_guest",
        "registered_time",
        "last_login",
        "games_played",
        "is_active",
        "is_staff",
    )
    list_filter = ("is_guest", "is_active", "is_staff")
    date_hierarchy = "date_joined"
    ordering = ("-date_joined",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _games_played=Count(
                "gameplayer__lobby",
                filter=Q(gameplayer__lobby__game__isnull=False),
                distinct=True,
            )
        )

    @admin.display(description="Registered time", ordering="date_joined")
    def registered_time(self, obj):
        return obj.date_joined

    @admin.display(description="Games played", ordering="_games_played")
    def games_played(self, obj):
        return obj._games_played

@admin.register(models.GamePlayer)
class GamePlayerAdmin(AutoSearchAdmin):
    pass

@admin.register(models.Lobby)
class LobbyAdmin(AutoSearchAdmin):
    pass
