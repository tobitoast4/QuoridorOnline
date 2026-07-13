from django.contrib import admin
from django.db import models as djmodels
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
    pass

@admin.register(models.GamePlayer)
class GamePlayerAdmin(AutoSearchAdmin):
    pass

@admin.register(models.Lobby)
class LobbyAdmin(AutoSearchAdmin):
    pass