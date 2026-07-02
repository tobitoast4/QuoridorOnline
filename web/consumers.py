import json
import logging
from django.contrib.auth import get_user_model
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache

from web import models, serialize, utils
from web.quoridor import deserialize as quoridor_deserialize

logger = logging.getLogger(__name__)
User = get_user_model()

class GameConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer für Echtzeit-Spielkommunikation.
    Verbindet Spieler mit ihren Lobbies.
    """

    @database_sync_to_async
    def get_user_info(self):
        if self.user and self.user.is_authenticated:
            user_id = str(self.user.id)
        else:
            user_id = self.scope["session"].get("anonymous_user_id")
        user = User.objects.get(pk=user_id)
        return {
            'username': user.username,
            'user_id': user_id
        }

    async def connect(self):
        """WebSocket-Verbindung aufbau."""
        self.lobby_id = self.scope['url_route']['kwargs'].get('lobby_id')
        self.user = self.scope.get('user')
        self.room_group_name = f'game_{self.lobby_id}'
        
        # User-Info für Logging
        user_info = await self.get_user_info()
        self.user_id = user_info['user_id']

        # Zur Gruppe hinzufügen
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Benachrichtige andere Spieler, dass jemand verbunden ist
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_connected',
                'user_id': user_info['user_id'],
                'username': user_info['username'],
            }
        )
        logger.info(f"Player {user_info['username']} connected to lobby {self.lobby_id}")

    async def disconnect(self, close_code):
        """WebSocket-Verbindung trennen."""
        user_info = await self.get_user_info()
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"Player {user_info['username']} disconnected from lobby {self.lobby_id}")

    async def receive(self, text_data):
        """Empfängt Nachrichten vom Client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            message_data = data.get('message')

            if message_type == 'game_move':
                await self.handle_game_move(message_data)
            elif message_type == 'place_wall':
                await self.handle_place_wall(message_data)
            elif message_type == 'surrender':
                await self.handle_surrender(message_data)
            elif message_type == 'game_state_request':
                await self.handle_game_state_request()
            # elif message_type == 'chat_message':
            #     await self.handle_chat_message(message_data)
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            await self.send_error("Ungültige Nachricht")

    async def handle_game_move(self, data):
        @database_sync_to_async
        def process_move(user_id, col_num, row_num):
            try:
                the_lobby = models.Lobby.objects.get(id=self.lobby_id)
                the_game_json = json.loads(the_lobby.game)
                the_game = quoridor_deserialize.create_game_from_json(the_game_json)
                the_game.move_player(user_id, the_lobby, col_num, row_num)
                the_lobby.game = json.dumps(the_game.game_data, cls=utils.UUIDEncoder)
                the_lobby.save()
                serializer = serialize.LobbySerializer(the_lobby)
                return serializer.data
            except models.Lobby.DoesNotExist:
                raise ValueError(f"Lobby with id {self.lobby_id} does not exist.")
        try:
            lobby_data = await process_move(self.user_id, data.get("new_field_col_num"), data.get("new_field_row_num"))
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'game_state', 'message': lobby_data}
            )
        except Exception as e:
            await self.send_error(str(e))

    async def handle_place_wall(self, data):
        @database_sync_to_async
        def process_place_wall(user_id, col_start, row_start, col_end, row_end):
            try:
                the_lobby = models.Lobby.objects.get(id=self.lobby_id)
                the_game_json = json.loads(the_lobby.game)
                the_game = quoridor_deserialize.create_game_from_json(the_game_json)
                the_game.place_wall(user_id, col_start, row_start, col_end, row_end)
                the_lobby.game = json.dumps(the_game.game_data, cls=utils.UUIDEncoder)
                the_lobby.save()
                serializer = serialize.LobbySerializer(the_lobby)
                return serializer.data
            except models.Lobby.DoesNotExist:
                raise ValueError(f"Lobby with id {self.lobby_id} does not exist.")
        try:
            lobby_data = await process_place_wall(self.user_id, 
                                                  data.get("col_start"),
                                                  data.get("row_start"),
                                                  data.get("col_end"),
                                                  data.get("row_end"))
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'game_state', 'message': lobby_data}
            )
        except Exception as e:
            await self.send_error(str(e))

    async def handle_surrender(self, data):
        @database_sync_to_async
        def process_surrender(user_id):
            try:
                the_lobby = models.Lobby.objects.get(id=self.lobby_id)
                the_game_json = json.loads(the_lobby.game)
                the_game = quoridor_deserialize.create_game_from_json(the_game_json)
                the_game.surrender(user_id, the_lobby)
                the_lobby.game = json.dumps(the_game.game_data, cls=utils.UUIDEncoder)
                the_lobby.save()
                serializer = serialize.LobbySerializer(the_lobby)
                return serializer.data
            except models.Lobby.DoesNotExist:
                raise ValueError(f"Lobby with id {self.lobby_id} does not exist.")
        try:
            lobby_data = await process_surrender(self.user_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'game_state', 'message': lobby_data}
            )
        except Exception as e:
            await self.send_error(str(e))

    async def handle_game_state_request(self): 
        @database_sync_to_async
        def get_lobby_data():
            try:
                the_lobby = models.Lobby.objects.get(id=self.lobby_id)
                serializer = serialize.LobbySerializer(the_lobby)
                return serializer.data
            except models.Lobby.DoesNotExist:
                raise ValueError(f"Lobby with id {self.lobby_id} does not exist.")
            
        try:
            lobby_data = await get_lobby_data()
            await self.send(text_data=json.dumps({
                'type': 'game_state',
                'message': lobby_data
            }))
        except Exception as e:
            await self.send_error(str(e))

    # async def handle_chat_message(self, data):
    #     """Verarbeitet Chat-Nachrichten."""
    #     user_info = await self.get_user_info()
    #     chat_data = {
    #         'type': 'chat_message_broadcast',
    #         'user_id': user_info['user_id'],
    #         'username': user_info['username'],
    #         'message': data.get('message'),
    #     }
    #     await self.channel_layer.group_send(
    #         self.room_group_name,
    #         chat_data
    #     )

    async def send_error(self, error_message):
        """Sendet eine Fehlernachricht an den Client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message
        }))

    # Broadcast-Handler (werden von group_send aufgerufen)
    async def game_state(self, event):
        """Broadcast des aktuellen Spielstatus."""
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'message': event['message'],
        }))

    # async def chat_message_broadcast(self, event):
    #     """Broadcast einer Chat-Nachricht."""
    #     await self.send(text_data=json.dumps({
    #         'type': 'chat_message',
    #         'user_id': event['user_id'],
    #         'username': event['username'],
    #         'message': event['message'],
    #     }))

    async def player_connected(self, event):
        # Required as we have group_send(... 'type': 'player_connected',
        await self.send(text_data=json.dumps({
            'type': 'player_connected',
            'user_id': event['user_id'],
            'username': event['username'],
        }))
