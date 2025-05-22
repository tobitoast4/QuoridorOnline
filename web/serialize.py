from rest_framework import serializers
from web import models


class GameUserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    class Meta:
        model = models.GameUser
        fields = ["id", "color", "username"]
        depth = 1

class GamePlayerSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    game_user = GameUserSerializer(required=False)
    # serialize only the UUID of the lobby
    lobby = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = models.GamePlayer
        fields = "__all__"
        depth = 1

class LobbySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    gameplayer_set = GamePlayerSerializer(many=True, required=False)
    created_by = GamePlayerSerializer(required=False)
    owner = GamePlayerSerializer(required=False)
    # created_by = serializers.PrimaryKeyRelatedField(queryset=models.GamePlayer.objects.all(), allow_null=True)
    # owner = serializers.PrimaryKeyRelatedField(queryset=models.GamePlayer.objects.all(), allow_null=True)
    class Meta:
        model = models.Lobby
        fields = "__all__"
        depth = 3