import json

from rest_framework import serializers
from web import models


class GameUserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    class Meta:
        model = models.GameUser
        fields = ["id", "color", "username"]
        depth = 1

class GamePlayerSerializer(serializers.ModelSerializer):
    game_user = GameUserSerializer(required=False)
    class Meta:
        model = models.GamePlayer
        fields = "__all__"
        depth = 1

    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)
    #     return representation["game_user"] if "game_user" in representation else None

class LobbySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    gameplayer_set = GamePlayerSerializer(many=True, required=False)
    created_by = GamePlayerSerializer(required=False)
    owner = GamePlayerSerializer(required=False)
    winner = GamePlayerSerializer(required=False)
    # created_by = serializers.PrimaryKeyRelatedField(queryset=models.GamePlayer.objects.all(), allow_null=True)
    # owner = serializers.PrimaryKeyRelatedField(queryset=models.GamePlayer.objects.all(), allow_null=True)
    class Meta:
        model = models.Lobby
        fields = "__all__"
        depth = 3

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.game:
            representation['game'] = json.loads(instance.game)
        return representation