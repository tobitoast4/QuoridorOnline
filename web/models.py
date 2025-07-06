from django.db import models
from django.contrib.auth.models import AbstractUser
from web import utils
from web.errors import QuoridorOnlineGameError
import uuid6, time


class GameUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid6.uuid8, editable=False)
    color = models.CharField(max_length=15, default=utils.get_random_color)
    is_guest = models.BooleanField(default=True)

class GamePlayer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid6.uuid8, editable=False)
    game_user = models.ForeignKey(GameUser, null=True, blank=True, on_delete=models.SET_NULL)
    lobby = models.ForeignKey('Lobby', null=True, blank=True, on_delete=models.CASCADE)
    color = models.CharField(max_length=15, default=utils.get_random_color)
    last_seen = models.IntegerField(default=time.time)

class Lobby(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid6.uuid8, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(GameUser, related_name='created_by', null=True, blank=True, on_delete=models.SET_NULL)
    owner = models.ForeignKey(GamePlayer, related_name='owner', null=True, blank=True, on_delete=models.SET_NULL)
    amount_of_walls_per_player = models.IntegerField(default=10)
    is_private = models.BooleanField(default=True)
    game = models.TextField(blank=True, null=True)

    def toggle_visibility(self):
        if self.is_private:
            self.is_private = False
        else:
            self.is_private = True
        self.save()

    def change_amount_of_walls_of_players(self, new_amount: int):
        if new_amount <= 0:
            raise QuoridorOnlineGameError("The amount of walls per player can not be lower than 1")
        elif new_amount > 99:
            raise QuoridorOnlineGameError("The amount of walls per player can not be higher than 99")
        else:
            self.amount_of_walls_per_player = new_amount
            self.save()

    def to_json(self):
        self_as_dict = vars(self).copy()
        self_as_dict["owner"] = self.owner.__json__()
        self_as_dict["players"] = [u.__json__() for u in self.players]
        if self.game is not None:
            self_as_dict["game"] = {
                "game_data": self.game.game_data
            }
        return self_as_dict
