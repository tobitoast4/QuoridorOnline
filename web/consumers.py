import json
import logging
import re
from django.contrib.auth import get_user_model
from django.utils.html import escape
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from web import lobby_manager, models, serialize, utils
from web.quoridor import deserialize as quoridor_deserialize
from web.quoridor import game as quoridor_game
from web.quoridor.artificial_player import move as ai_move
import asyncio

from html import escape

# TODO: Logger should be configured in settings.py and not here. This is just a temporary solution for now.
# TODO: Log on every message?
logger = logging.getLogger(__name__)
User = get_user_model()



def html_escape(text):
    return escape(str(text), quote=True)
    


class LobbyConsumer(AsyncWebsocketConsumer):

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
    
    @database_sync_to_async
    def get_lobby_data(self):
        the_lobby = models.Lobby.objects.get(id=self.lobby_id)
        serializer = serialize.LobbySerializer(the_lobby)
        return serializer.data

    async def connect(self):
        @database_sync_to_async
        def add_player_to_lobby():
            user = User.objects.get(pk=self.user_id)
            the_lobbys = models.Lobby.objects.filter(pk=self.lobby_id)
            if the_lobbys.count() == 1:
                the_lobby = the_lobbys.first()
                if the_lobby.game is None:  # game not started yet
                    lobby_manager.add_player_to_lobby(the_lobby, user)

        self.lobby_id = self.scope['url_route']['kwargs'].get('lobby_id')
        self.user = self.scope.get('user')
        self.room_group_name = f'lobby_{self.lobby_id}'
        
        # User-Info für Logging
        user_info = await self.get_user_info()
        self.user_id = user_info['user_id']
        self.user_name = user_info['username']

        # Zur Gruppe hinzufügen
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        try:
            await add_player_to_lobby()
            utils.add_online_user(self.user_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'lobby_state', 'message': await self.get_lobby_data()}
            )
        except Exception as e:
            await self.send_error(str(e))

        # Benachrichtige andere Spieler, dass jemand verbunden ist
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_connected',
                'user_id': user_info['user_id'],
                'username': user_info['username'],
            }
        )
        logger.info(f"Player {self.user_name} connected to lobby {self.lobby_id}")

    async def disconnect(self, close_code):
        @database_sync_to_async
        def remove_player_from_lobby():
            user = User.objects.get(pk=self.user_id)
            the_lobbys = models.Lobby.objects.filter(pk=self.lobby_id)
            if the_lobbys.count() == 1:
                the_lobby = the_lobbys.first()
                if the_lobby.game is None:  # game not started yet
                    lobby_manager.remove_player_from_lobby(the_lobby, user)

        await remove_player_from_lobby()
        utils.remove_online_user(self.user_id)
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'lobby_state', 'message': await self.get_lobby_data()}
        )
        logger.info(f"Player {self.user_name} disconnected from lobby {self.lobby_id}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            message_data = data.get('message')

            if message_type == 'start_game':
                await self.handle_start_game(message_data)
            elif message_type == 'change_lobby_visibility':
                await self.handle_change_lobby_visibility(message_data)
            elif message_type == 'change_amount_of_walls_per_player':
                await self.handle_change_amount_of_walls_per_player(message_data)
            elif message_type == 'rename_player':
                await self.handle_rename_player(message_data)
            elif message_type == 'change_color':
                await self.handle_change_color(message_data)
            elif message_type == 'lobby_state_request':
                await self.handle_lobby_state_request()
            # elif message_type == 'chat_message':
            #     await self.handle_chat_message(message_data)
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            await self.send_error("Invalid message")

    async def handle_start_game(self, data):
        @database_sync_to_async
        def process_start_game():
            the_lobby = models.Lobby.objects.get(pk=self.lobby_id)
            if self.user_id != str(the_lobby.owner.game_user.id):
                raise PermissionError("Only the lobby owner can start the game")
            # TODO: Shuffle players
            next_lobby = models.Lobby.objects.create(created_by=the_lobby.created_by, previous_lobby=the_lobby)
            new_game = quoridor_game.Game(the_lobby.gameplayer_set, the_lobby.amount_of_walls_per_player, next_lobby.id)
            the_lobby.game = json.dumps(new_game.game_data, cls=utils.UUIDEncoder)
            the_lobby.save()
        try:
            await process_start_game()
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'lobby_state', 'message': await self.get_lobby_data()}
            )
            logger.info(f"Player {self.user_name} started the game in lobby {self.lobby_id}")
        except Exception as e:
            await self.send_error(str(e))

    async def handle_change_lobby_visibility(self, data):
        @database_sync_to_async
        def process_change_lobby_visibility():
            the_lobby = models.Lobby.objects.get(id=self.lobby_id)
            if self.user_id != str(the_lobby.owner.game_user.id):
                raise PermissionError("Only the lobby owner can change the lobby visibility")
            the_lobby.toggle_visibility()
            if the_lobby.is_private:
                return "Lobby visibility successfully changed to: private"
            else:
                return "Lobby visibility successfully changed to: public"
        try:
            msg = await process_change_lobby_visibility()
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'lobby_state', 'message': await self.get_lobby_data()}
            )
        except Exception as e:
            await self.send_error(str(e))

    async def handle_change_amount_of_walls_per_player(self, data):
        @database_sync_to_async
        def process_change_amount_of_walls_per_player(new_amount):
            the_lobby = models.Lobby.objects.get(id=self.lobby_id)
            if self.user_id != str(the_lobby.owner.game_user.id):
                raise PermissionError("Only the lobby owner can change the amount of walls per player")
            if the_lobby.game is not None:
                raise PermissionError("You can not change the amount of walls per player when the game is already running")
            the_lobby.change_amount_of_walls_of_players(new_amount)
        try:
            await process_change_amount_of_walls_per_player( data.get("new_amount"))
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'lobby_state', 'message': await self.get_lobby_data()}
            )
        except Exception as e:
            await self.send_error(str(e))

    async def handle_rename_player(self, data):
        @database_sync_to_async
        def process_rename_player(new_name):
            if new_name == "":
                raise ValueError("User name can not be empty")
            if len(new_name) > 64:
                raise ValueError("User name is too long")
            if User.objects.filter(username=new_name).exists():
                raise ValueError("User name is already taken")
            if User.objects.filter(username=new_name).exists():
                raise ValueError("User name is already taken")
            if new_name != html_escape(new_name):  # XSS prevention
                raise ValueError("User name contains invalid characters")
            user = User.objects.get(pk=self.user_id)
            user.username = new_name
            user.save()
        try:
            await process_rename_player(data.get("new_name"))
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'lobby_state', 'message': await self.get_lobby_data()}
            )
        except Exception as e:
            await self.send_error(str(e))

    async def handle_change_color(self, data):
        @database_sync_to_async
        def process_change_color(new_color):
            if new_color not in utils.COLORS:
                raise ValueError("Invalid color")
            user = User.objects.get(pk=self.user_id)
            gameplayer = user.gameplayer_set.filter(lobby__id=self.lobby_id).first()
            gameplayer.color = new_color
            gameplayer.save()
            user.color = new_color
            user.save()
        try:
            await process_change_color(data.get("new_color"))
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'lobby_state', 'message': await self.get_lobby_data()}
            )
        except Exception as e:
            await self.send_error(str(e))

    async def handle_lobby_state_request(self): 
        try:
            await self.send(text_data=json.dumps({
                'type': 'lobby_state',
                'message': await self.get_lobby_data()
            }))
        except Exception as e:
            await self.send_error(str(e))

    async def send_error(self, error_message):
        """Sendet eine Fehlernachricht an den Client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message
        }))

    # Broadcast-Handler (werden von group_send aufgerufen)
    async def lobby_state(self, event):
        await self.send(text_data=json.dumps({
            'type': 'lobby_state',
            'message': event['message'],
        }))

    async def player_connected(self, event):
        # Required as we have group_send(... 'type': 'player_connected',
        await self.send(text_data=json.dumps({
            'type': 'player_connected',
            'user_id': event['user_id'],
            'username': event['username'],
        }))


class GameConsumer(AsyncWebsocketConsumer):

    @database_sync_to_async
    def get_user_info(self):
        if self.user and self.user.is_authenticated:
            user_id = str(self.user.id)
        else:
            user_id = self.scope["session"].get("anonymous_user_id")
        user = User.objects.get(pk=user_id)
        return {
            'color': user.color,  # TODO: Color should be fetched from the GamePlayer model, not the User model
            'username': user.username,
            'user_id': user_id
        }

    async def connect(self):
        self.lobby_id = self.scope['url_route']['kwargs'].get('lobby_id')
        self.user = self.scope.get('user')
        self.room_group_name = f'game_{self.lobby_id}'
        
        # User-Info für Logging
        user_info = await self.get_user_info()
        self.user_id = user_info['user_id']
        self.user_name = user_info['username']
        self.user_color = user_info['color']

        # Zur Gruppe hinzufügen
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        utils.add_online_user(self.user_id)

        # Benachrichtige andere Spieler, dass jemand verbunden ist
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_connected',
                'user_id': user_info['user_id'],
            }
        )
        asyncio.create_task(self.play_ai_player())  # start AI player moves if the real user connects
        logger.info(f"Player {self.user_name} connected to game {self.lobby_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        utils.remove_online_user(self.user_id)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_disconnected',
                'user_id': self.user_id
            }
        )
        logger.info(f"Player {self.user_name} disconnected from game {self.lobby_id}")

    async def receive(self, text_data):
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
            elif message_type == 'online_state_request':
                await self.handle_online_state_request()
            # elif message_type == 'chat_message':
            #     await self.handle_chat_message(message_data)
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            await self.send_error("Ungültige Nachricht")

    async def handle_game_move(self, data):
        @database_sync_to_async
        def process_move(col_num, row_num):
            try:
                the_lobby = models.Lobby.objects.get(id=self.lobby_id)
                the_game_json = json.loads(the_lobby.game)
                the_game = quoridor_deserialize.create_game_from_json(the_game_json)
                the_game.move_player(self.user_id, the_lobby, col_num, row_num)
                the_lobby.game = json.dumps(the_game.game_data, cls=utils.UUIDEncoder)
                the_lobby.save()
                serializer = serialize.LobbySerializer(the_lobby)
                return serializer.data
            except models.Lobby.DoesNotExist:
                raise ValueError(f"Lobby with id {self.lobby_id} does not exist.")
        try:
            lobby_data = await process_move(data.get("new_field_col_num"), data.get("new_field_row_num"))
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'game_state', 'message': lobby_data}
            )
            asyncio.create_task(self.play_ai_player())
        except Exception as e:
            await self.send_error(str(e))

    async def handle_place_wall(self, data):
        @database_sync_to_async
        def process_place_wall(col_start, row_start, col_end, row_end):
            try:
                the_lobby = models.Lobby.objects.get(id=self.lobby_id)
                the_game_json = json.loads(the_lobby.game)
                the_game = quoridor_deserialize.create_game_from_json(the_game_json)
                the_game.place_wall(self.user_id, col_start, row_start, col_end, row_end)
                the_lobby.game = json.dumps(the_game.game_data, cls=utils.UUIDEncoder)
                the_lobby.save()
                serializer = serialize.LobbySerializer(the_lobby)
                return serializer.data
            except models.Lobby.DoesNotExist:
                raise ValueError(f"Lobby with id {self.lobby_id} does not exist.")
        try:
            lobby_data = await process_place_wall(data.get("col_start"),
                                                  data.get("row_start"),
                                                  data.get("col_end"),
                                                  data.get("row_end"))
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'game_state', 'message': lobby_data}
            )
            asyncio.create_task(self.play_ai_player())
        except Exception as e:
            await self.send_error(str(e))

    async def handle_surrender(self, data):
        @database_sync_to_async
        def process_surrender():
            try:
                the_lobby = models.Lobby.objects.get(id=self.lobby_id)
                the_game_json = json.loads(the_lobby.game)
                the_game = quoridor_deserialize.create_game_from_json(the_game_json)
                the_game.surrender(self.user_id, the_lobby)
                the_lobby.game = json.dumps(the_game.game_data, cls=utils.UUIDEncoder)
                the_lobby.save()
                serializer = serialize.LobbySerializer(the_lobby)
                return serializer.data
            except models.Lobby.DoesNotExist:
                raise ValueError(f"Lobby with id {self.lobby_id} does not exist.")
        try:
            lobby_data = await process_surrender()
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'game_state', 'message': lobby_data}
            )
            asyncio.create_task(self.play_ai_player())
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

    async def handle_online_state_request(self): 
        @database_sync_to_async
        def get_online_user_ids():
            online_user_ids = utils.get_online_user_ids()
            the_lobby = models.Lobby.objects.get(id=self.lobby_id)
            players = the_lobby.gameplayer_set.all()
            user_ids_in_lobby = [str(p.game_user.id) for p in players]
            return list(set(online_user_ids) & set(user_ids_in_lobby))
            
        try:
            online_user_ids = await get_online_user_ids()
            await self.send(text_data=json.dumps({
                'type': 'online_state',
                'message': online_user_ids
            }))
        except Exception as e:
            await self.send_error(str(e))

    # async def handle_chat_message(self, data):
    #     """Verarbeitet Chat-Nachrichten."""
    #     chat_data = {
    #         'type': 'chat_message_broadcast',
    #         'user_id': self.user_id,
    #         'username': self.user_name,
    #         'message': data.get('message'),
    #     }
    #     await self.channel_layer.group_send(
    #         self.room_group_name,
    #         chat_data
    #     )

    async def play_ai_player(self):
        @database_sync_to_async
        def load_game_state():
            the_lobby = models.Lobby.objects.get(id=self.lobby_id)
            the_game_json = json.loads(the_lobby.game)
            the_game = quoridor_deserialize.create_game_from_json(the_game_json)
            return the_lobby, the_game, the_lobby.winner

        @database_sync_to_async
        def save_game_state(the_lobby, new_game):
            the_lobby.game = json.dumps(new_game.game_data, cls=utils.UUIDEncoder)
            the_lobby.save()
            serializer = serialize.LobbySerializer(the_lobby)
            return serializer.data

        def run_ai_move(the_lobby, the_game):
            move_generator = ai_move.MoveSimulator(the_lobby, the_game, depth=2, wall_range=5)
            return move_generator.play()

        try:
            the_lobby, the_game, winner = await load_game_state()
            if not winner and the_game.get_current_player().gameplayer.is_artificial:
                new_game = await asyncio.to_thread(run_ai_move, the_lobby, the_game)
                lobby_data = await save_game_state(the_lobby, new_game)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'game_state', 'message': lobby_data}
                )
                asyncio.create_task(self.play_ai_player())
        except Exception as e:
            await self.send_error(str(e))

    async def send_error(self, error_message):
        """Sendet eine Fehlernachricht an den Client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message
        }))

    async def game_state(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'message': event['message'],
        }))

    async def online_state(self, event):
        await self.send(text_data=json.dumps({
            'type': 'online_state',
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
            'user_id': event['user_id']
        }))

    async def player_disconnected(self, event):
        # Required as we have group_send(... 'type': 'player_disconnected',
        await self.send(text_data=json.dumps({
            'type': 'player_disconnected',
            'user_id': event['user_id']
        }))
